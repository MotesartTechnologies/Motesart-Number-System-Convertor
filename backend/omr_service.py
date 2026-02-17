"""
Optical Music Recognition (OMR) Service for Motesart Converter
Using Google Gemini Vision API for sheet music analysis
"""

import os
import json
import base64
import tempfile
import logging
import re
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gemini API Key
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# Note to Motesart number mapping
NOTE_TO_NUMBER = {
    'C': '1', 'D': '2', 'E': '3', 'F': '4', 'G': '5', 'A': '6', 'B': '7'
}

# Semitone mapping for key transposition
NOTE_TO_SEMITONE = {
    'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3,
    'E': 4, 'Fb': 4, 'E#': 5, 'F': 5, 'F#': 6, 'Gb': 6,
    'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10,
    'B': 11, 'Cb': 11, 'B#': 0
}

# Major scale intervals (semitones from root)
MAJOR_SCALE_SEMITONES = [0, 2, 4, 5, 7, 9, 11]

# Half-number mapping for chromatic notes
HALF_NUMBER_MAP = {
    1: "1½", 3: "2½", 6: "4½", 8: "5½", 10: "6½"
}


def get_key_root_semitone(key_name: str) -> int:
    """Get the semitone value for a key root."""
    key_clean = key_name.replace('-flat', 'b').replace('-sharp', '#').replace(' major', '').replace(' minor', '').strip()
    return NOTE_TO_SEMITONE.get(key_clean, 0)


def note_to_motesart(pitch: str, octave: int, key_root: int = 0) -> Dict:
    """
    Convert a note pitch to Motesart number with octave indicators.
    
    Args:
        pitch: Note name (e.g., 'C', 'D#', 'Bb')
        octave: Octave number (e.g., 4)
        key_root: Semitone of key root for transposition
        
    Returns:
        Dict with 'number', 'accidental', 'octave_dots' fields
    """
    # Clean up pitch name
    pitch = pitch.strip().replace('-', 'b')
    
    # Extract base note and accidental
    base_note = pitch[0].upper() if pitch else 'C'
    accidental = pitch[1:] if len(pitch) > 1 else ''
    
    # Get semitone value
    semitone = NOTE_TO_SEMITONE.get(pitch.upper(), NOTE_TO_SEMITONE.get(base_note, 0))
    
    # Calculate semitones from key root
    semitones_from_root = (semitone - key_root) % 12
    
    # Determine the Motesart number
    if semitones_from_root in MAJOR_SCALE_SEMITONES:
        degree = MAJOR_SCALE_SEMITONES.index(semitones_from_root) + 1
        motesart_num = str(degree)
        accidental_symbol = ''
    elif semitones_from_root in HALF_NUMBER_MAP:
        motesart_num = HALF_NUMBER_MAP[semitones_from_root]
        accidental_symbol = ''
    else:
        # Fallback to simple note number
        motesart_num = NOTE_TO_NUMBER.get(base_note, '?')
        if '#' in accidental:
            accidental_symbol = '♯'
        elif 'b' in accidental:
            accidental_symbol = '♭'
        else:
            accidental_symbol = ''
    
    # Calculate octave dots (middle octave = 4, reference)
    reference_octave = 4
    octave_diff = (octave or 4) - reference_octave
    
    dots_above = '•' * octave_diff if octave_diff > 0 else ''
    dots_below = '•' * abs(octave_diff) if octave_diff < 0 else ''
    
    return {
        'number': motesart_num,
        'accidental': accidental_symbol,
        'dots_above': dots_above,
        'dots_below': dots_below,
        'display': f"{dots_above}{accidental_symbol}{motesart_num}{dots_below}".strip()
    }


def convert_pdf_to_images(pdf_path: str, dpi: int = 300) -> List[str]:
    """
    Convert PDF pages to high-resolution PNG images.
    
    Args:
        pdf_path: Path to the PDF file
        dpi: Resolution (default 300 DPI for high quality)
        
    Returns:
        List of paths to generated PNG images
    """
    try:
        from pdf2image import convert_from_path
        
        logger.info(f"Converting PDF to images at {dpi} DPI: {pdf_path}")
        
        # Convert PDF to images
        images = convert_from_path(pdf_path, dpi=dpi)
        
        image_paths = []
        for i, img in enumerate(images):
            # Save to temp file
            temp_path = tempfile.mktemp(suffix=f'_page{i+1}.png')
            img.save(temp_path, 'PNG')
            image_paths.append(temp_path)
            logger.info(f"Saved page {i+1} to {temp_path}")
        
        return image_paths
        
    except Exception as e:
        logger.error(f"PDF to image conversion failed: {e}")
        return []


def image_to_base64(image_path: str) -> str:
    """Convert image file to base64 string."""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


async def analyze_sheet_music_with_gemini(image_path: str) -> Dict:
    """
    Send sheet music image to Google Gemini Vision API for analysis.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Parsed JSON response with notes, lyrics, key, time signature
    """
    try:
        import google.generativeai as genai
        
        if not GEMINI_API_KEY:
            logger.error("GEMINI_API_KEY not configured")
            return {'success': False, 'error': 'Gemini API key not configured'}
        
        # Configure the API
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Use gemini-2.0-flash model
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        logger.info(f"Analyzing sheet music with Gemini: {image_path}")
        
        # Read and encode the image
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Determine MIME type
        ext = os.path.splitext(image_path)[1].lower()
        mime_type = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.webp': 'image/webp'
        }.get(ext, 'image/png')
        
        # Create the prompt
        prompt = """Read this hymnal sheet music image. Extract every single music note (pitch and octave), all lyrics/words aligned to their notes, the key signature, and time signature.

Return the result as structured JSON with this EXACT format:
{
    "key_signature": "C major" or detected key,
    "time_signature": "4/4" or detected time signature,
    "title": "song title if visible",
    "measures": [
        {
            "number": 1,
            "notes": [
                {
                    "pitch": "C",
                    "octave": 4,
                    "duration": "quarter",
                    "lyric": "word or syllable under this note"
                }
            ]
        }
    ]
}

IMPORTANT:
1. Extract EVERY note you can see on the staff
2. For each note, include the pitch (C, D, E, F, G, A, B with # or b if sharped/flatted)
3. Include the octave number (middle C = C4)
4. Align lyrics to the notes they belong to
5. Group notes by measure
6. Return ONLY valid JSON, no other text"""

        # Create image part for the API
        image_part = {
            'mime_type': mime_type,
            'data': image_data
        }
        
        # Generate content
        response = model.generate_content([prompt, image_part])
        
        # Get the response text
        response_text = response.text
        logger.info(f"Gemini response length: {len(response_text)}")
        
        # Parse JSON from response
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(response_text)
            
            data['success'] = True
            data['analysis_method'] = 'gemini-2.0-flash'
            
            logger.info(f"Extracted {len(data.get('measures', []))} measures")
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            logger.error(f"Response was: {response_text[:500]}")
            return {
                'success': False,
                'error': f'Invalid JSON response: {str(e)}',
                'raw_response': response_text[:1000]
            }
            
    except Exception as e:
        logger.error(f"Gemini analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }


def analyze_sheet_music_with_gemini_sync(image_path: str) -> Dict:
    """Synchronous wrapper for Gemini analysis."""
    import asyncio
    import nest_asyncio
    nest_asyncio.apply()
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(analyze_sheet_music_with_gemini(image_path))


def convert_to_motesart_format(gemini_data: Dict, key_override: str = None) -> Dict:
    """
    Convert Gemini output to Motesart format with numbers and aligned lyrics.
    
    Args:
        gemini_data: Parsed response from Gemini
        key_override: Optional key to use instead of detected key
        
    Returns:
        Formatted data for display
    """
    if not gemini_data.get('success'):
        return gemini_data
    
    # Get key signature
    key_sig = key_override or gemini_data.get('key_signature', 'C major')
    key_name = key_sig.replace(' major', '').replace(' minor', '').strip()
    key_root = get_key_root_semitone(key_name)
    
    # Process each measure
    formatted_measures = []
    all_notes = []
    all_lyrics = []
    
    for measure in gemini_data.get('measures', []):
        measure_notes = []
        measure_lyrics = []
        
        for note in measure.get('notes', []):
            pitch = note.get('pitch', 'C')
            octave = note.get('octave', 4)
            lyric = note.get('lyric', '')
            duration = note.get('duration', 'quarter')
            
            # Convert to Motesart
            motesart = note_to_motesart(pitch, octave, key_root)
            
            measure_notes.append({
                'pitch': pitch,
                'octave': octave,
                'motesart': motesart['display'],
                'number': motesart['number'],
                'accidental': motesart['accidental'],
                'dots_above': motesart['dots_above'],
                'dots_below': motesart['dots_below'],
                'duration': duration,
                'lyric': lyric
            })
            
            measure_lyrics.append(lyric or '')
        
        formatted_measures.append({
            'number': measure.get('number', len(formatted_measures) + 1),
            'notes': measure_notes,
            'lyrics': measure_lyrics
        })
        
        all_notes.extend(measure_notes)
        all_lyrics.extend(measure_lyrics)
    
    # Create display lines (numbers on top, lyrics below)
    number_line = ''
    lyric_line = ''
    
    for i, measure in enumerate(formatted_measures):
        if i > 0:
            number_line += ' | '
            lyric_line += ' | '
        
        for note in measure['notes']:
            display = note['motesart']
            lyric = note['lyric'] or '-'
            
            # Pad to align
            max_len = max(len(display), len(lyric))
            number_line += display.center(max_len + 1)
            lyric_line += lyric.center(max_len + 1)
    
    return {
        'success': True,
        'key_signature': key_sig,
        'key_name': key_name,
        'key_root_semitone': key_root,
        'time_signature': gemini_data.get('time_signature', '4/4'),
        'title': gemini_data.get('title'),
        'measures': formatted_measures,
        'all_notes': all_notes,
        'all_lyrics': all_lyrics,
        'display': {
            'number_line': number_line.strip(),
            'lyric_line': lyric_line.strip()
        },
        'analysis_method': gemini_data.get('analysis_method', 'gemini-2.0-flash')
    }


def process_sheet_music_omr(file_path: str, key_override: str = None) -> Dict:
    """
    Main OMR processing function using Google Gemini Vision API.
    
    Args:
        file_path: Path to PDF or image file
        key_override: Optional key to use for conversion
        
    Returns:
        Processed Motesart data
    """
    logger.info(f"Starting OMR processing with Gemini: {file_path}")
    
    result = {
        'success': False,
        'error': None,
        'key_signature': None,
        'key_name': None,
        'time_signature': '4/4',
        'measures': [],
        'all_notes': [],
        'all_lyrics': [],
        'display': None,
        'analysis_method': None,
    }
    
    try:
        file_ext = os.path.splitext(file_path)[1].lower()
        temp_images = []
        image_path = file_path
        
        # Convert PDF to images
        if file_ext == '.pdf':
            logger.info("Converting PDF to high-resolution images...")
            image_paths = convert_pdf_to_images(file_path, dpi=300)
            
            if not image_paths:
                result['error'] = "Failed to convert PDF to images"
                return result
            
            # Process first page (can extend to multiple pages)
            image_path = image_paths[0]
            temp_images = image_paths
        
        # Handle HEIC conversion
        elif file_ext in ['.heic', '.heif']:
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
                result['error'] = f"Could not convert HEIC: {e}"
                return result
        
        # Ensure it's an image format Gemini accepts
        if file_ext not in ['.png', '.jpg', '.jpeg', '.webp', '.pdf', '.heic', '.heif']:
            result['error'] = f"Unsupported file format: {file_ext}"
            return result
        
        # Analyze with Gemini
        logger.info(f"Sending image to Gemini Vision API: {image_path}")
        gemini_result = analyze_sheet_music_with_gemini_sync(image_path)
        
        if gemini_result.get('success'):
            # Convert to Motesart format
            motesart_result = convert_to_motesart_format(gemini_result, key_override)
            result.update(motesart_result)
        else:
            result['error'] = gemini_result.get('error', 'Gemini analysis failed')
            if gemini_result.get('raw_response'):
                result['raw_response'] = gemini_result['raw_response']
        
        # Clean up temp files
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


def extract_notes_for_staff_view(omr_data: Dict) -> List[Dict]:
    """Extract notes from OMR data for staff view rendering."""
    if not omr_data:
        return []
    
    notes = omr_data.get('all_notes', [])
    if not notes:
        # Try to extract from measures
        for measure in omr_data.get('measures', []):
            notes.extend(measure.get('notes', []))
    
    return notes


def get_key_root_semitone(key_name: str) -> int:
    """Get the semitone value for a key root."""
    key_clean = key_name.replace('-flat', 'b').replace('-sharp', '#').replace(' major', '').replace(' minor', '').strip()
    return NOTE_TO_SEMITONE.get(key_clean, 0)


def pitch_to_motesart(pitch: str, key_root: int) -> str:
    """Simple pitch to Motesart number conversion."""
    if not pitch:
        return "?"
    
    # Extract note name
    match = re.match(r'^([A-Ga-g][#b]?)(-?\d)?$', pitch)
    if not match:
        # Try just the note name
        note_name = pitch[0].upper() if pitch else 'C'
    else:
        note_name = match.group(1).capitalize()
    
    semitone = NOTE_TO_SEMITONE.get(note_name, 0)
    semitones_from_root = (semitone - key_root) % 12
    
    if semitones_from_root in MAJOR_SCALE_SEMITONES:
        degree = MAJOR_SCALE_SEMITONES.index(semitones_from_root) + 1
        return str(degree)
    
    if semitones_from_root in HALF_NUMBER_MAP:
        return HALF_NUMBER_MAP[semitones_from_root]
    
    return "?"


def analyze_sheet_music_image(image_path: str, key_override: str = None) -> Dict:
    """Backward compatibility wrapper."""
    return process_sheet_music_omr(image_path, key_override)


# Command-line testing
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = process_sheet_music_omr(sys.argv[1])
        print(json.dumps(result, indent=2, default=str))
    else:
        print("Usage: python omr_service.py <path_to_sheet_music>")
