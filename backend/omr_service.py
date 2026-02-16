"""
Optical Music Recognition (OMR) Service for Motesart Converter
PERMANENT SOLUTION using MuseScore + music21 + Gemini AI fallback
"""

import os
import subprocess
import tempfile
import logging
import base64
import asyncio
import json
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Note to semitone mapping
NOTE_TO_SEMITONE = {
    'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3,
    'E': 4, 'Fb': 4, 'E#': 5, 'F': 5, 'F#': 6, 'Gb': 6, 
    'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 
    'B': 11, 'Cb': 11, 'B#': 0
}

# Major scale semitone positions
MAJOR_SCALE_SEMITONES = [0, 2, 4, 5, 7, 9, 11]  # 1, 2, 3, 4, 5, 6, 7

# Half-number mapping for chromatic notes
HALF_NUMBER_MAP = {
    1: "1½",   # Between 1 and 2 (C# in key of C)
    3: "2½",   # Between 2 and 3 (D# in key of C)
    6: "4½",   # Between 4 and 5 (F# in key of C)
    8: "5½",   # Between 5 and 6 (G# in key of C)
    10: "6½"   # Between 6 and 7 (A# in key of C)
}


def get_key_root_semitone(key_name: str) -> int:
    """Get the semitone value for a key root."""
    # Clean up key name (handle 'D-flat' -> 'Db', etc.)
    key_clean = key_name.replace('-flat', 'b').replace('-sharp', '#').replace(' major', '').replace(' minor', '').strip()
    
    # Handle common variations
    key_map = {
        'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3,
        'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8,
        'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11
    }
    return key_map.get(key_clean, 0)


def pitch_to_motesart(pitch_str: str, key_root: int) -> str:
    """
    Convert a pitch string (e.g., 'C4', 'Db5', 'F#3') to Motesart degree.
    Uses half-numbers for chromatic notes.
    """
    if not pitch_str:
        return "?"
    
    # Parse pitch name and octave
    match = re.match(r'^([A-Ga-g][#b]?)(-?\d)?$', pitch_str)
    if not match:
        return "?"
    
    note_name = match.group(1).capitalize()
    
    # Get semitone value
    semitone = NOTE_TO_SEMITONE.get(note_name)
    if semitone is None:
        return "?"
    
    # Calculate semitones from key root
    semitones_from_root = (semitone - key_root) % 12
    
    # Check if diatonic (in major scale)
    if semitones_from_root in MAJOR_SCALE_SEMITONES:
        degree = MAJOR_SCALE_SEMITONES.index(semitones_from_root) + 1
        return str(degree)
    
    # Chromatic - use half-number
    if semitones_from_root in HALF_NUMBER_MAP:
        return HALF_NUMBER_MAP[semitones_from_root]
    
    return "?"


def process_pdf_to_images(pdf_path: str) -> List[str]:
    """Convert PDF pages to images using pdf2image."""
    try:
        from pdf2image import convert_from_path
        
        logger.info(f"Converting PDF to images: {pdf_path}")
        images = convert_from_path(pdf_path, dpi=150, first_page=1, last_page=5)
        
        image_paths = []
        for i, img in enumerate(images):
            temp_path = tempfile.mktemp(suffix=f'_page{i+1}.png')
            img.save(temp_path, 'PNG')
            image_paths.append(temp_path)
            logger.info(f"Saved page {i+1} to {temp_path}")
        
        return image_paths
    except Exception as e:
        logger.error(f"PDF to image conversion failed: {e}")
        return []


def process_with_musescore(file_path: str, output_dir: str) -> Optional[str]:
    """
    Convert PDF/image to MusicXML using MuseScore CLI.
    This is the primary OMR method.
    """
    try:
        output_path = os.path.join(output_dir, "converted.musicxml")
        
        logger.info(f"Processing with MuseScore: {file_path}")
        
        # MuseScore command for conversion
        result = subprocess.run([
            'musescore3',
            '--export-to', output_path,
            file_path
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0:
            logger.warning(f"MuseScore conversion warning: {result.stderr}")
        
        if os.path.exists(output_path):
            logger.info(f"MuseScore conversion successful: {output_path}")
            return output_path
        
        return None
        
    except subprocess.TimeoutExpired:
        logger.error("MuseScore conversion timed out")
        return None
    except Exception as e:
        logger.error(f"MuseScore processing failed: {e}")
        return None


def parse_musicxml_with_music21(musicxml_path: str) -> Optional[Dict]:
    """
    Parse MusicXML file using music21 and extract all musical data.
    """
    try:
        import music21
        
        logger.info(f"Parsing MusicXML with music21: {musicxml_path}")
        
        # Parse the score
        score = music21.converter.parse(musicxml_path)
        
        # Analyze key signature
        key_analysis = score.analyze('key')
        key_name = key_analysis.tonic.name.replace('-', 'b') if key_analysis else 'C'
        key_root = get_key_root_semitone(key_name)
        
        logger.info(f"Detected key: {key_name} (root semitone: {key_root})")
        
        # Extract time signature
        time_sig = None
        for ts in score.flatten().getElementsByClass('TimeSignature'):
            time_sig = f"{ts.numerator}/{ts.denominator}"
            break
        
        # Extract title if available
        title = None
        if score.metadata:
            title = score.metadata.title
        
        # Extract all notes
        notes_data = []
        for element in score.flatten().notesAndRests:
            if isinstance(element, music21.note.Note):
                pitch_name = element.pitch.name.replace('-', 'b')
                octave = element.pitch.octave
                pitch_str = f"{pitch_name}{octave}" if octave else pitch_name
                
                # Get Motesart degree
                motesart = pitch_to_motesart(pitch_name, key_root)
                
                # Get duration type
                duration_type = element.duration.type
                
                # Get lyric if any
                lyric = None
                if element.lyric:
                    lyric = element.lyric
                
                notes_data.append({
                    'pitch': pitch_str,
                    'pitch_name': pitch_name,
                    'midi': element.pitch.midi,
                    'motesart': motesart,
                    'duration': element.quarterLength,
                    'duration_type': duration_type,
                    'measure': element.measureNumber,
                    'beat': element.beat if hasattr(element, 'beat') else 1,
                    'lyric': lyric
                })
            elif isinstance(element, music21.note.Rest):
                notes_data.append({
                    'pitch': 'rest',
                    'pitch_name': 'rest',
                    'midi': None,
                    'motesart': '-',
                    'duration': element.quarterLength,
                    'duration_type': element.duration.type,
                    'measure': element.measureNumber,
                    'beat': element.beat if hasattr(element, 'beat') else 1,
                    'lyric': None
                })
        
        # Extract lyrics from all parts
        lyrics_lines = []
        for part in score.parts:
            for note in part.flatten().notes:
                if note.lyric:
                    lyrics_lines.append(note.lyric)
        
        # Extract chords if present
        chords_data = []
        for chord in score.flatten().getElementsByClass('ChordSymbol'):
            chords_data.append({
                'symbol': chord.figure,
                'measure': chord.measureNumber,
                'beat': chord.beat if hasattr(chord, 'beat') else 1
            })
        
        return {
            'key_signature': key_name,
            'key_name': key_name,
            'key_root_semitone': key_root,
            'time_signature': time_sig or '4/4',
            'title': title,
            'notes': notes_data,
            'chords': chords_data,
            'lyrics': lyrics_lines,
            'note_count': len([n for n in notes_data if n['pitch'] != 'rest'])
        }
        
    except Exception as e:
        logger.error(f"music21 parsing failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def analyze_with_gemini(image_path: str, key_hint: str = None) -> Dict:
    """
    Use Gemini AI to analyze sheet music image and extract note information.
    Fallback when MuseScore fails.
    """
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage, FileContentWithMimeType
        
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            logger.error("EMERGENT_LLM_KEY not found")
            return {'success': False, 'error': 'API key not configured'}
        
        logger.info(f"Analyzing image with Gemini: {image_path}")
        
        # Determine MIME type
        ext = os.path.splitext(image_path)[1].lower()
        mime_map = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp'}
        mime_type = mime_map.get(ext, 'image/png')
        
        # Create chat instance
        chat = LlmChat(
            api_key=api_key,
            session_id=f"omr_{os.path.basename(image_path)}",
            system_message="""You are an expert music notation analyst. 
Your task is to analyze sheet music images and extract detailed note information.
You MUST respond with valid JSON only - no markdown, no explanations, just pure JSON."""
        ).with_model("gemini", "gemini-2.5-flash")
        
        # Create image content
        image_content = FileContentWithMimeType(file_path=image_path, mime_type=mime_type)
        
        key_context = f"The key signature appears to be {key_hint}." if key_hint else ""
        
        prompt = f"""Analyze this sheet music image carefully and extract ALL musical information.
{key_context}

Return a JSON object with this EXACT structure:
{{
    "key_signature": "the detected key (e.g., 'Db', 'G', 'C')",
    "key_fifths": number of sharps (positive) or flats (negative),
    "time_signature": "4/4" or detected time signature,
    "title": "title if visible, or null",
    "notes": [
        {{
            "pitch": "note name with octave (e.g., 'C4', 'Db5')",
            "duration": "quarter", "half", "whole", "eighth", or "sixteenth",
            "measure": measure number (1-based),
            "beat": beat position in measure (1-based),
            "lyric": "any lyrics under this note or null"
        }}
    ],
    "chords": [
        {{
            "symbol": "chord symbol if any (e.g., 'Db', 'Fm7')",
            "measure": measure number,
            "beat": beat position
        }}
    ],
    "lyrics_lines": ["array of lyric text lines if present"]
}}

IMPORTANT:
1. Extract EVERY visible note from the staff
2. Use proper enharmonic spelling based on key (flats for flat keys)
3. For 5-flat key (Db major): Db, Eb, F, Gb, Ab, Bb, C
4. Return ONLY the JSON object"""

        message = UserMessage(text=prompt, file_contents=[image_content])
        response = await chat.send_message(message)
        
        logger.info(f"Gemini response length: {len(response)}")
        
        # Parse JSON response
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            data = json.loads(json_match.group()) if json_match else json.loads(response)
            
            # Process notes to add Motesart numbers
            key_name = data.get('key_signature', 'C').replace(' major', '').replace(' minor', '')
            key_root = get_key_root_semitone(key_name)
            
            for note in data.get('notes', []):
                pitch = note.get('pitch', '')
                note['motesart'] = pitch_to_motesart(pitch, key_root)
                # Add MIDI value
                note_name = ''.join(c for c in pitch if not c.isdigit()).replace('-', 'b')
                octave = int(''.join(c for c in pitch if c.isdigit()) or '4')
                semitone = NOTE_TO_SEMITONE.get(note_name, 0)
                note['midi'] = semitone + (octave + 1) * 12
            
            data['success'] = True
            data['key_root_semitone'] = key_root
            data['analysis_method'] = 'gemini'
            data['key_name'] = key_name
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini JSON: {e}")
            return {'success': False, 'error': f'Invalid JSON: {str(e)}'}
            
    except Exception as e:
        logger.error(f"Gemini analysis failed: {e}")
        return {'success': False, 'error': str(e)}


def analyze_with_gemini_sync(image_path: str, key_hint: str = None) -> Dict:
    """Synchronous wrapper for analyze_with_gemini."""
    import nest_asyncio
    nest_asyncio.apply()
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(analyze_with_gemini(image_path, key_hint))


def process_sheet_music_omr(file_path: str) -> Dict:
    """
    Main OMR processing function.
    Uses a 3-tier approach:
    1. MuseScore + music21 (best for PDF/MusicXML)
    2. Gemini AI (best for images)
    3. Fallback with helpful error message
    """
    logger.info(f"Starting OMR processing for: {file_path}")
    
    result = {
        'success': False,
        'error': None,
        'key_signature': None,
        'key_name': None,
        'key_root_semitone': 0,
        'time_signature': '4/4',
        'notes': [],
        'chords': [],
        'lyrics': [],
        'title': None,
        'analysis_method': None,
    }
    
    try:
        file_ext = os.path.splitext(file_path)[1].lower()
        temp_files = []
        
        # === TIER 1: Direct MusicXML/MIDI parsing ===
        if file_ext in ['.xml', '.musicxml', '.mxl', '.mid', '.midi']:
            logger.info("Using direct music21 parsing")
            parsed = parse_musicxml_with_music21(file_path)
            if parsed:
                result.update(parsed)
                result['success'] = True
                result['analysis_method'] = 'music21_direct'
                return result
        
        # === TIER 2: MuseScore conversion for PDF ===
        if file_ext == '.pdf':
            logger.info("Attempting MuseScore conversion for PDF")
            with tempfile.TemporaryDirectory() as temp_dir:
                musicxml_path = process_with_musescore(file_path, temp_dir)
                if musicxml_path:
                    parsed = parse_musicxml_with_music21(musicxml_path)
                    if parsed:
                        result.update(parsed)
                        result['success'] = True
                        result['analysis_method'] = 'musescore'
                        return result
            
            # MuseScore failed, convert PDF to images for Gemini
            logger.info("MuseScore failed, converting PDF to images for Gemini")
            image_paths = process_pdf_to_images(file_path)
            if image_paths:
                temp_files.extend(image_paths)
                file_path = image_paths[0]  # Use first page
                file_ext = '.png'
        
        # === TIER 3: Gemini AI for images ===
        if file_ext in ['.png', '.jpg', '.jpeg', '.webp', '.heic']:
            logger.info("Using Gemini AI for image analysis")
            
            # Handle HEIC conversion
            if file_ext == '.heic':
                try:
                    from PIL import Image
                    import pillow_heif
                    pillow_heif.register_heif_opener()
                    
                    heic_img = Image.open(file_path)
                    temp_png = tempfile.mktemp(suffix='.png')
                    heic_img.save(temp_png, 'PNG')
                    file_path = temp_png
                    temp_files.append(temp_png)
                except Exception as e:
                    logger.error(f"HEIC conversion failed: {e}")
                    result['error'] = f"Could not convert HEIC: {e}"
                    return result
            
            gemini_result = analyze_with_gemini_sync(file_path)
            
            if gemini_result.get('success'):
                result['success'] = True
                result['analysis_method'] = 'gemini'
                result['key_signature'] = gemini_result.get('key_signature')
                result['key_name'] = gemini_result.get('key_name')
                result['key_root_semitone'] = gemini_result.get('key_root_semitone', 0)
                result['time_signature'] = gemini_result.get('time_signature', '4/4')
                result['title'] = gemini_result.get('title')
                result['notes'] = gemini_result.get('notes', [])
                result['chords'] = gemini_result.get('chords', [])
                result['lyrics'] = gemini_result.get('lyrics_lines', [])
            else:
                result['error'] = gemini_result.get('error', 'Gemini analysis failed')
        
        # Clean up temp files
        for temp_path in temp_files:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                pass
        
        # If nothing worked, provide helpful fallback message
        if not result['success'] and not result['error']:
            result['error'] = 'Unable to process this file. Please use Manual Entry or Text Converter.'
        
        return result
        
    except Exception as e:
        logger.error(f"OMR processing error: {e}")
        import traceback
        traceback.print_exc()
        result['error'] = str(e)
        return result


def format_staff_view_data(omr_data: Dict) -> Dict:
    """Format OMR results for the Staff View component."""
    if not omr_data or not omr_data.get('success'):
        return {'success': False, 'error': omr_data.get('error', 'No data')}
    
    # Group notes by measure
    measures = {}
    for note in omr_data.get('notes', []):
        measure_num = note.get('measure', 1)
        if measure_num not in measures:
            measures[measure_num] = []
        measures[measure_num].append(note)
    
    return {
        'success': True,
        'key': omr_data.get('key_name', 'C'),
        'time_signature': omr_data.get('time_signature', '4/4'),
        'title': omr_data.get('title'),
        'measures': [{'number': k, 'notes': v} for k, v in sorted(measures.items())],
        'total_notes': len(omr_data.get('notes', [])),
        'analysis_method': omr_data.get('analysis_method')
    }


# Command-line testing
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = process_sheet_music_omr(sys.argv[1])
        print(json.dumps(result, indent=2, default=str))
    else:
        print("Usage: python omr_service.py <path_to_sheet_music>")
