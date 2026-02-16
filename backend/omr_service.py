"""
Optical Music Recognition (OMR) Service for Motesart Converter
Uses Gemini AI for image-based OMR and music21 for MusicXML parsing
"""

import os
import tempfile
import logging
import base64
import asyncio
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Major scale semitone intervals from root
MAJOR_SCALE_SEMITONES = [0, 2, 4, 5, 7, 9, 11]

# Note name to semitone mapping
NOTE_TO_SEMITONE = {
    'C': 0, 'C#': 1, 'D-': 1, 'Db': 1,
    'D': 2, 'D#': 3, 'E-': 3, 'Eb': 3,
    'E': 4, 'E#': 5, 'F-': 4, 'Fb': 4,
    'F': 5, 'F#': 6, 'G-': 6, 'Gb': 6,
    'G': 7, 'G#': 8, 'A-': 8, 'Ab': 8,
    'A': 9, 'A#': 10, 'B-': 10, 'Bb': 10,
    'B': 11, 'B#': 0, 'C-': 11, 'Cb': 11
}

# Half-number map for chromatic notes
HALF_NUMBER_MAP = {
    1: "1½",   # Between 1 and 2
    3: "2½",   # Between 2 and 3
    6: "4½",   # Between 4 and 5
    8: "5½",   # Between 5 and 6
    10: "6½",  # Between 6 and 7
}

# Key signature to root note mapping (number of sharps/flats)
KEY_SIGNATURE_MAP = {
    # Sharps
    0: 'C',
    1: 'G',
    2: 'D', 
    3: 'A',
    4: 'E',
    5: 'B',
    6: 'F#',
    7: 'C#',
    # Flats (negative)
    -1: 'F',
    -2: 'Bb',
    -3: 'Eb',
    -4: 'Ab',
    -5: 'Db',
    -6: 'Gb',
    -7: 'Cb',
}


def get_key_root_semitone(key_name: str) -> int:
    """Get the semitone value for a key root note."""
    # Handle various key name formats
    key_name = key_name.replace(' major', '').replace(' minor', '').strip()
    
    # Try direct lookup
    if key_name in NOTE_TO_SEMITONE:
        return NOTE_TO_SEMITONE[key_name]
    
    # Handle music21 key format (e.g., "D- major")
    if key_name.endswith('-'):
        flat_key = key_name[:-1] + 'b'
        if flat_key in NOTE_TO_SEMITONE:
            return NOTE_TO_SEMITONE[flat_key]
    
    # Default to C
    logger.warning(f"Unknown key: {key_name}, defaulting to C")
    return 0


def pitch_to_motesart(pitch_name: str, key_root_semitone: int) -> str:
    """
    Convert a pitch name to its Motesart degree number.
    
    Args:
        pitch_name: The pitch name (e.g., 'C4', 'F#5', 'Bb3')
        key_root_semitone: The semitone value of the key root
        
    Returns:
        Motesart degree string (e.g., '1', '4', '6½')
    """
    # Extract note name (without octave)
    note_name = ''.join(c for c in pitch_name if not c.isdigit())
    
    # Handle music21 pitch format
    note_name = note_name.replace('-', 'b')  # D- -> Db
    
    # Get semitone of this note
    note_semitone = NOTE_TO_SEMITONE.get(note_name, 0)
    
    # Calculate semitones from key root
    semitones_from_root = (note_semitone - key_root_semitone) % 12
    
    # Check if diatonic
    if semitones_from_root in MAJOR_SCALE_SEMITONES:
        degree = MAJOR_SCALE_SEMITONES.index(semitones_from_root) + 1
        return str(degree)
    
    # Chromatic - use half-number
    if semitones_from_root in HALF_NUMBER_MAP:
        return HALF_NUMBER_MAP[semitones_from_root]
    
    return "?"


async def analyze_with_gemini(image_path: str, key_hint: str = None) -> Dict:
    """
    Use Gemini AI to analyze sheet music image and extract note information.
    
    Args:
        image_path: Path to the image file
        key_hint: Optional hint about the key signature
        
    Returns:
        Dictionary with extracted musical data
    """
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage, FileContentWithMimeType
        import json
        import re
        
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            logger.error("EMERGENT_LLM_KEY not found in environment")
            return {'success': False, 'error': 'API key not configured'}
        
        logger.info(f"Analyzing image with Gemini: {image_path}")
        
        # Determine MIME type
        ext = os.path.splitext(image_path)[1].lower()
        mime_map = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.webp': 'image/webp',
        }
        mime_type = mime_map.get(ext, 'image/png')
        
        # Create the chat instance with Gemini
        chat = LlmChat(
            api_key=api_key,
            session_id=f"omr_{os.path.basename(image_path)}",
            system_message="""You are an expert music notation analyst. 
Your task is to analyze sheet music images and extract detailed note information.
You MUST respond with valid JSON only - no markdown, no explanations, just pure JSON."""
        ).with_model("gemini", "gemini-2.5-flash")
        
        # Create image content
        image_content = FileContentWithMimeType(
            file_path=image_path,
            mime_type=mime_type
        )
        
        # Build the prompt
        key_context = f"The key signature appears to be {key_hint}." if key_hint else ""
        
        prompt = f"""Analyze this sheet music image carefully and extract ALL musical information.
{key_context}

Return a JSON object with this EXACT structure:
{{
    "key_signature": "the detected key (e.g., 'Db major', 'G major', 'C major')",
    "key_fifths": number of sharps (positive) or flats (negative) in the key signature,
    "time_signature": "4/4" or detected time signature,
    "title": "title if visible, or null",
    "tempo": tempo marking if visible or null,
    "notes": [
        {{
            "pitch": "note name with octave (e.g., 'C4', 'Db5', 'F#3')",
            "duration": "quarter", "half", "whole", "eighth", or "sixteenth",
            "measure": measure number (1-based),
            "beat": beat position in measure (1-based),
            "lyric": "any lyrics under this note or null"
        }}
    ],
    "chords": [
        {{
            "symbol": "chord symbol if any (e.g., 'Db', 'Fm7', 'Bbm')",
            "measure": measure number,
            "beat": beat position
        }}
    ],
    "lyrics_lines": ["array of lyric text lines if present"]
}}

IMPORTANT:
1. Extract EVERY visible note from the staff, not just a summary
2. Use proper enharmonic spelling based on the key (use flats for flat keys, sharps for sharp keys)
3. For a 5-flat key signature (Db major), notes should be: Db, Eb, F, Gb, Ab, Bb, C
4. Include all parts/voices if there are multiple staves
5. Return ONLY the JSON object, no other text"""

        # Send message with image
        message = UserMessage(
            text=prompt,
            file_contents=[image_content]
        )
        
        response = await chat.send_message(message)
        logger.info(f"Gemini response length: {len(response)}")
        
        # Parse the JSON response
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(response)
            
            logger.info(f"Parsed {len(data.get('notes', []))} notes from Gemini response")
            
            # Process notes to add Motesart numbers
            key_name = data.get('key_signature', 'C major').replace(' major', '').replace(' minor', '')
            key_root = get_key_root_semitone(key_name)
            
            for note in data.get('notes', []):
                pitch = note.get('pitch', '')
                note['motesart'] = pitch_to_motesart(pitch, key_root)
            
            # Process chords similarly
            for chord in data.get('chords', []):
                symbol = chord.get('symbol', '')
                if symbol:
                    # Get chord root
                    root_match = re.match(r'^([A-G][#b]?)', symbol)
                    if root_match:
                        chord['motesart'] = pitch_to_motesart(root_match.group(1), key_root)
            
            data['success'] = True
            data['key_root_semitone'] = key_root
            data['analysis_method'] = 'gemini'
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            logger.error(f"Response was: {response[:500]}")
            return {
                'success': False,
                'error': f'Invalid JSON response from Gemini: {str(e)}',
                'raw_response': response[:1000]
            }
            
    except Exception as e:
        logger.error(f"Gemini analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }


def analyze_with_gemini_sync(image_path: str, key_hint: str = None) -> Dict:
    """Synchronous wrapper for analyze_with_gemini."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(analyze_with_gemini(image_path, key_hint))


def process_image_with_oemer(image_path: str) -> Optional[str]:
    """
    Process an image file with OMR to get MusicXML.
    Currently falls back to OCR-based chord extraction since full OMR models are not available.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Path to the generated MusicXML file, or None if failed
    """
    try:
        logger.info(f"Processing image for music recognition: {image_path}")
        
        # Create output directory
        output_dir = tempfile.mkdtemp()
        
        # Since full OMR models aren't available, use OCR to extract text/chords
        # This won't get individual notes but can extract chord symbols and lyrics
        
        try:
            import pytesseract
            from PIL import Image
            import cv2
            import numpy as np
            
            # Load and preprocess image
            img = cv2.imread(image_path)
            if img is None:
                pil_img = Image.open(image_path)
                img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Apply thresholding to improve OCR
            _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            
            # Run OCR
            text = pytesseract.image_to_string(binary)
            logger.info(f"OCR extracted text length: {len(text)}")
            
            if text.strip():
                # Try to extract chord symbols from the text
                import re
                chord_pattern = r'[A-G][#b]?(?:m|M|maj|min|dim|aug|sus|add|7|9|11|13)*(?:/[A-G][#b]?)?'
                chords = re.findall(chord_pattern, text)
                
                if chords:
                    logger.info(f"Extracted {len(chords)} chord symbols from image")
                    
                    # Create a simple MusicXML with the chords
                    from music21 import stream, harmony, meter
                    
                    score = stream.Score()
                    part = stream.Part()
                    part.append(meter.TimeSignature('4/4'))
                    
                    for chord_str in chords[:20]:  # Limit to first 20
                        try:
                            h = harmony.ChordSymbol(chord_str)
                            part.append(h)
                        except:
                            pass
                    
                    score.append(part)
                    
                    musicxml_path = os.path.join(output_dir, "result.musicxml")
                    score.write('musicxml', fp=musicxml_path)
                    
                    if os.path.exists(musicxml_path):
                        logger.info(f"Created MusicXML with {len(chords)} chord symbols")
                        return musicxml_path
                        
        except Exception as e:
            logger.warning(f"OCR-based extraction failed: {e}")
        
        logger.warning("No OMR/OCR method succeeded for image")
        return None
        
    except Exception as e:
        logger.error(f"Image processing failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def process_pdf_to_images(pdf_path: str) -> List[str]:
    """
    Convert PDF pages to images for OMR processing.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of image file paths
    """
    try:
        from pdf2image import convert_from_path
        
        logger.info(f"Converting PDF to images: {pdf_path}")
        
        # Convert PDF to images
        images = convert_from_path(pdf_path, dpi=300)
        
        # Save images to temp files
        image_paths = []
        for i, image in enumerate(images):
            temp_path = tempfile.mktemp(suffix=f'_page{i+1}.png')
            image.save(temp_path, 'PNG')
            image_paths.append(temp_path)
            logger.info(f"Saved page {i+1} to {temp_path}")
        
        return image_paths
        
    except Exception as e:
        logger.error(f"PDF to image conversion failed: {e}")
        return []


def parse_musicxml_with_music21(musicxml_path: str) -> Dict:
    """
    Parse MusicXML file using music21 library.
    
    Args:
        musicxml_path: Path to the MusicXML file
        
    Returns:
        Dictionary with extracted musical data
    """
    try:
        from music21 import converter, key, meter, note, chord, stream, harmony
        
        logger.info(f"Parsing MusicXML with music21: {musicxml_path}")
        
        # Parse the file
        score = converter.parse(musicxml_path)
        
        result = {
            'key_signature': None,
            'key_name': None,
            'key_root_semitone': 0,
            'time_signature': '4/4',
            'measures': [],
            'notes': [],
            'chords': [],  # For chord symbols
            'lyrics': [],
            'title': None,
            'composer': None,
        }
        
        # Extract metadata
        if score.metadata:
            result['title'] = score.metadata.title or 'Untitled'
            result['composer'] = score.metadata.composer
        
        # Detect key signature
        detected_key = score.analyze('key')
        if detected_key:
            result['key_signature'] = str(detected_key)
            result['key_name'] = detected_key.tonic.name
            result['key_root_semitone'] = get_key_root_semitone(detected_key.tonic.name)
            logger.info(f"Detected key: {result['key_signature']}")
        
        # Get time signature
        time_sigs = score.recurse().getElementsByClass(meter.TimeSignature)
        if time_sigs:
            result['time_signature'] = str(time_sigs[0])
        
        # Extract notes AND chord symbols from all parts
        key_root = result['key_root_semitone']
        
        for part_idx, part in enumerate(score.parts):
            for measure in part.recurse().getElementsByClass(stream.Measure):
                measure_data = {
                    'number': measure.number,
                    'notes': [],
                    'chords': [],
                    'harmony': [],
                    'lyrics': []
                }
                
                for element in measure.recurse():
                    # Handle individual notes
                    if isinstance(element, note.Note):
                        note_data = {
                            'pitch': element.pitch.nameWithOctave,
                            'pitch_name': element.pitch.name,
                            'midi': element.pitch.midi,
                            'duration': float(element.duration.quarterLength),
                            'duration_type': element.duration.type,
                            'offset': float(element.offset),
                            'motesart': pitch_to_motesart(element.pitch.name, key_root),
                        }
                        
                        if element.lyrics:
                            note_data['lyric'] = ' '.join([l.text for l in element.lyrics if l.text])
                            result['lyrics'].append(note_data['lyric'])
                        
                        measure_data['notes'].append(note_data)
                        result['notes'].append(note_data)
                    
                    # Handle chord symbols (harmony)
                    elif isinstance(element, harmony.ChordSymbol):
                        chord_data = {
                            'symbol': element.figure,
                            'root': element.root().name if element.root() else '',
                            'bass': element.bass().name if element.bass() else '',
                            'kind': element.chordKind if hasattr(element, 'chordKind') else '',
                            'offset': float(element.offset),
                        }
                        
                        # Convert root to Motesart
                        if chord_data['root']:
                            chord_data['motesart'] = pitch_to_motesart(chord_data['root'], key_root)
                        
                        measure_data['harmony'].append(chord_data)
                        result['chords'].append(chord_data)
                        
                        # Also create a "note" entry for the chord root for staff display
                        if chord_data['root']:
                            # Get MIDI for root (assume octave 4)
                            root_midi = NOTE_TO_SEMITONE.get(chord_data['root'].replace('-', 'b'), 0) + 60
                            result['notes'].append({
                                'pitch': chord_data['root'] + '4',
                                'pitch_name': chord_data['root'],
                                'midi': root_midi,
                                'duration': 1.0,
                                'duration_type': 'quarter',
                                'offset': chord_data['offset'],
                                'motesart': chord_data.get('motesart', '?'),
                                'is_chord_root': True,
                                'chord_symbol': chord_data['symbol'],
                            })
                        
                    # Handle actual chords (multiple notes)
                    elif isinstance(element, chord.Chord):
                        chord_notes = []
                        for p in element.pitches:
                            chord_notes.append({
                                'pitch': p.nameWithOctave,
                                'pitch_name': p.name,
                                'midi': p.midi,
                                'motesart': pitch_to_motesart(p.name, key_root),
                            })
                        
                        measure_data['chords'].append({
                            'notes': chord_notes,
                            'duration': float(element.duration.quarterLength),
                            'duration_type': element.duration.type,
                            'offset': float(element.offset),
                        })
                        
                        # Add each note in the chord to the notes list
                        for cn in chord_notes:
                            result['notes'].append({
                                'pitch': cn['pitch'],
                                'pitch_name': cn['pitch_name'],
                                'midi': cn['midi'],
                                'duration': float(element.duration.quarterLength),
                                'duration_type': element.duration.type,
                                'offset': float(element.offset),
                                'motesart': cn['motesart'],
                            })
                
                if measure_data['notes'] or measure_data['chords'] or measure_data['harmony']:
                    result['measures'].append(measure_data)
        
        logger.info(f"Extracted {len(result['notes'])} notes, {len(result['chords'])} chord symbols, {len(result['measures'])} measures")
        return result
        
    except Exception as e:
        logger.error(f"music21 parsing failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def process_sheet_music_omr(file_path: str, use_gemini: bool = True) -> Dict:
    """
    Main entry point for OMR processing.
    Uses Gemini AI as the primary method for image analysis.
    
    Args:
        file_path: Path to the sheet music file (PDF or image)
        use_gemini: If True, use Gemini AI for image analysis (default)
        
    Returns:
        Dictionary with extracted and converted musical data
    """
    logger.info(f"Starting OMR processing for: {file_path}")
    
    result = {
        'success': False,
        'error': None,
        'key_signature': None,
        'key_name': None,
        'time_signature': '4/4',
        'notes': [],
        'measures': [],
        'lyrics': [],
        'chords': [],
        'title': None,
        'analysis_method': None,
    }
    
    try:
        file_ext = os.path.splitext(file_path)[1].lower()
        image_path = None
        temp_images = []
        
        # Handle PDF files - convert to image first
        if file_ext == '.pdf':
            image_paths = process_pdf_to_images(file_path)
            if not image_paths:
                result['error'] = "Failed to convert PDF to images"
                return result
            image_path = image_paths[0]  # Use first page
            temp_images = image_paths
            
        # Handle image files
        elif file_ext in ['.png', '.jpg', '.jpeg', '.webp']:
            image_path = file_path
            
        # Handle HEIC files - convert to PNG first
        elif file_ext == '.heic':
            try:
                from PIL import Image
                import pillow_heif
                pillow_heif.register_heif_opener()
                
                heic_img = Image.open(file_path)
                temp_png = tempfile.mktemp(suffix='.png')
                heic_img.save(temp_png, 'PNG')
                image_path = temp_png
                temp_images.append(temp_png)
            except Exception as e:
                logger.error(f"HEIC conversion failed: {e}")
                result['error'] = f"Could not convert HEIC file: {e}"
                return result
        
        # Handle MusicXML files directly
        elif file_ext in ['.xml', '.musicxml', '.mxl']:
            parsed = parse_musicxml_with_music21(file_path)
            if parsed:
                result.update(parsed)
                result['success'] = True
                result['analysis_method'] = 'musicxml'
            else:
                result['error'] = "Failed to parse MusicXML file"
            return result
        
        # Handle MIDI files
        elif file_ext in ['.mid', '.midi']:
            parsed = parse_musicxml_with_music21(file_path)
            if parsed:
                result.update(parsed)
                result['success'] = True
                result['analysis_method'] = 'midi'
            else:
                result['error'] = "Failed to parse MIDI file"
            return result
        
        else:
            result['error'] = f"Unsupported file format: {file_ext}"
            return result
        
        # Now process the image with Gemini AI
        if image_path and use_gemini:
            logger.info(f"Using Gemini AI for OMR analysis: {image_path}")
            gemini_result = analyze_with_gemini_sync(image_path)
            
            if gemini_result.get('success'):
                # Update result with Gemini data
                result['success'] = True
                result['analysis_method'] = 'gemini'
                result['key_signature'] = gemini_result.get('key_signature')
                result['key_name'] = gemini_result.get('key_signature', 'C').replace(' major', '').replace(' minor', '')
                result['key_root_semitone'] = gemini_result.get('key_root_semitone', 0)
                result['time_signature'] = gemini_result.get('time_signature', '4/4')
                result['title'] = gemini_result.get('title')
                result['notes'] = gemini_result.get('notes', [])
                result['chords'] = gemini_result.get('chords', [])
                result['lyrics'] = gemini_result.get('lyrics_lines', [])
                
                # Add MIDI values for notes if not present
                for note in result['notes']:
                    if 'midi' not in note:
                        pitch = note.get('pitch', 'C4')
                        note_name = ''.join(c for c in pitch if not c.isdigit()).replace('-', 'b')
                        octave = int(''.join(c for c in pitch if c.isdigit()) or '4')
                        semitone = NOTE_TO_SEMITONE.get(note_name, 0)
                        note['midi'] = semitone + (octave + 1) * 12
                
                logger.info(f"Gemini extracted {len(result['notes'])} notes")
            else:
                # Gemini failed, fall back to traditional method
                logger.warning(f"Gemini analysis failed: {gemini_result.get('error')}")
                result['error'] = gemini_result.get('error')
                
                # Try fallback OCR method
                if image_path:
                    musicxml_path = process_image_with_oemer(image_path)
                    if musicxml_path and os.path.exists(musicxml_path):
                        parsed = parse_musicxml_with_music21(musicxml_path)
                        if parsed:
                            result.update(parsed)
                            result['success'] = True
                            result['analysis_method'] = 'ocr_fallback'
        
        # Clean up temp images
        for temp_path in temp_images:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                pass
        
        return result
        
    except Exception as e:
        logger.error(f"OMR processing error: {e}")
        import traceback
        traceback.print_exc()
        result['error'] = str(e)
        return result


def extract_notes_for_staff_view(omr_result: Dict) -> List[Dict]:
    """
    Format OMR results for the Staff View component.
    
    Args:
        omr_result: Result from process_sheet_music_omr
        
    Returns:
        List of note data formatted for rendering
    """
    if not omr_result.get('success') or not omr_result.get('notes'):
        return []
    
    staff_notes = []
    for note_data in omr_result['notes']:
        staff_notes.append({
            'pitch': note_data.get('pitch', ''),
            'midi': note_data.get('midi', 60),
            'motesart': note_data.get('motesart', '?'),
            'duration': note_data.get('duration', 1),
            'duration_type': note_data.get('duration_type', 'quarter'),
            'lyric': note_data.get('lyric', ''),
        })
    
    return staff_notes


# Alternative approach: Direct image analysis without full OMR
def analyze_sheet_music_image(image_path: str, key_override: str = None) -> Dict:
    """
    Analyze a sheet music image using computer vision techniques.
    This is a fallback when full OMR is not available.
    
    Args:
        image_path: Path to the image file (PNG, JPG, etc. - NOT PDF)
        key_override: Optional key signature override
        
    Returns:
        Dictionary with analysis results
    """
    try:
        import cv2
        import numpy as np
        from PIL import Image
        
        logger.info(f"Analyzing sheet music image: {image_path}")
        
        # Check if it's a PDF - if so, convert first
        if image_path.lower().endswith('.pdf'):
            logger.info("Converting PDF to image for analysis")
            image_paths = process_pdf_to_images(image_path)
            if image_paths:
                image_path = image_paths[0]  # Use first page
            else:
                return {
                    'success': False,
                    'error': 'Could not convert PDF to image',
                    'analysis_type': 'image_analysis'
                }
        
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            # Try with PIL for formats like HEIC
            try:
                pil_img = Image.open(image_path)
                img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            except Exception as e:
                logger.error(f"Could not load image: {e}")
                return {
                    'success': False,
                    'error': f'Could not load image: {e}',
                    'analysis_type': 'image_analysis'
                }
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape
        
        # Detect staff lines using horizontal line detection
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (width // 10, 1))
        detect_horizontal = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, horizontal_kernel)
        _, thresh = cv2.threshold(detect_horizontal, 30, 255, cv2.THRESH_BINARY)
        
        # Find contours for staff lines
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        staff_lines = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w > width * 0.5:  # Long horizontal line
                staff_lines.append(y)
        
        staff_lines.sort()
        
        # Try to detect key signature from flats/sharps at the beginning
        # This is a simplified detection
        detected_key = key_override or 'C'
        
        result = {
            'success': True,
            'image_size': {'width': width, 'height': height},
            'staff_lines_detected': len(staff_lines),
            'staff_line_positions': staff_lines[:20],  # First 20 lines
            'key_signature': detected_key,
            'analysis_type': 'image_analysis',
            'notes': [],  # Placeholder - full note detection requires more sophisticated OMR
        }
        
        logger.info(f"Detected {len(staff_lines)} potential staff lines")
        return result
        
    except Exception as e:
        logger.error(f"Image analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e),
            'analysis_type': 'image_analysis'
        }


if __name__ == "__main__":
    # Test the module
    import sys
    if len(sys.argv) > 1:
        result = process_sheet_music_omr(sys.argv[1])
        print("OMR Result:", result)
    else:
        print("Usage: python omr_service.py <path_to_sheet_music>")
