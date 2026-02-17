"""
Optical Music Recognition (OMR) Service for Motesart Converter
Using Google Gemini Vision API for sheet music analysis
Supports multi-page PDFs with lyrics alignment
"""

import os
import json
import base64
import tempfile
import logging
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    """
    pitch = pitch.strip().replace('-', 'b') if pitch else 'C'
    base_note = pitch[0].upper() if pitch else 'C'
    accidental = pitch[1:] if len(pitch) > 1 else ''
    
    semitone = NOTE_TO_SEMITONE.get(pitch.upper(), NOTE_TO_SEMITONE.get(base_note, 0))
    semitones_from_root = (semitone - key_root) % 12
    
    if semitones_from_root in MAJOR_SCALE_SEMITONES:
        degree = MAJOR_SCALE_SEMITONES.index(semitones_from_root) + 1
        motesart_num = str(degree)
        accidental_symbol = ''
    elif semitones_from_root in HALF_NUMBER_MAP:
        motesart_num = HALF_NUMBER_MAP[semitones_from_root]
        accidental_symbol = ''
    else:
        motesart_num = NOTE_TO_NUMBER.get(base_note, '?')
        if '#' in accidental:
            accidental_symbol = '♯'
        elif 'b' in accidental:
            accidental_symbol = '♭'
        else:
            accidental_symbol = ''
    
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


def convert_pdf_to_images(pdf_path: str, dpi: int = 300) -> List[Dict]:
    """
    Convert ALL PDF pages to high-resolution PNG images.
    
    Args:
        pdf_path: Path to the PDF file
        dpi: Resolution (default 300 DPI for high quality)
        
    Returns:
        List of dicts with 'page_number', 'image_path', 'success'
    """
    try:
        from pdf2image import convert_from_path
        
        logger.info(f"Converting PDF to images at {dpi} DPI: {pdf_path}")
        
        # Convert ALL pages
        images = convert_from_path(pdf_path, dpi=dpi)
        
        pages = []
        for i, img in enumerate(images):
            try:
                temp_path = tempfile.mktemp(suffix=f'_page{i+1}.png')
                img.save(temp_path, 'PNG')
                pages.append({
                    'page_number': i + 1,
                    'image_path': temp_path,
                    'success': True,
                    'error': None
                })
                logger.info(f"Saved page {i+1} to {temp_path}")
            except Exception as e:
                pages.append({
                    'page_number': i + 1,
                    'image_path': None,
                    'success': False,
                    'error': str(e)
                })
                logger.error(f"Failed to save page {i+1}: {e}")
        
        logger.info(f"Converted {len(pages)} pages from PDF")
        return pages
        
    except Exception as e:
        logger.error(f"PDF to image conversion failed: {e}")
        return []


def extract_text_from_pdf(pdf_path: str) -> List[Dict]:
    """
    Extract selectable text from PDF pages for lyrics fallback.
    """
    try:
        import fitz  # PyMuPDF
        
        doc = fitz.open(pdf_path)
        pages_text = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            pages_text.append({
                'page_number': page_num + 1,
                'text': text,
                'words': text.split()
            })
        
        doc.close()
        return pages_text
        
    except Exception as e:
        logger.warning(f"Could not extract text from PDF: {e}")
        return []


async def analyze_sheet_music_with_gemini(image_path: str, user_api_key: str = None) -> Dict:
    """
    Send sheet music image to Google Gemini Vision API for analysis.
    
    Args:
        image_path: Path to the image file
        user_api_key: Optional user-provided Gemini API key
        
    Returns:
        Parsed JSON response with notes, lyrics, key, time signature
    """
    try:
        # Use user's API key if provided, otherwise use Emergent LLM key
        api_key = user_api_key or os.environ.get('EMERGENT_LLM_KEY')
        
        if not api_key:
            return {
                'success': False,
                'error': 'No API key configured. Please add your Gemini API key in settings.',
                'error_type': 'NO_API_KEY'
            }
        
        logger.info(f"Analyzing sheet music with Gemini: {image_path}")
        
        # Determine MIME type
        ext = os.path.splitext(image_path)[1].lower()
        mime_type = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.webp': 'image/webp'
        }.get(ext, 'image/png')
        
        # Use emergent integrations
        from emergentintegrations.llm.chat import LlmChat, UserMessage, FileContentWithMimeType
        
        chat = LlmChat(
            api_key=api_key,
            session_id=f"omr_{os.path.basename(image_path)}",
            system_message="""You are an expert music notation analyst. 
Your task is to analyze hymnal sheet music images and extract detailed note information.
You MUST respond with valid JSON only - no markdown, no explanations, just pure JSON."""
        ).with_model("gemini", "gemini-2.5-flash")
        
        image_content = FileContentWithMimeType(
            file_path=image_path,
            mime_type=mime_type
        )
        
        # Enhanced prompt for better lyrics extraction
        prompt = """Read this hymnal sheet music image carefully. Extract:
1. Every single music note (pitch like C, D, E, F, G, A, B with # or b for sharps/flats)
2. The octave number for each note (middle C = C4)
3. ALL lyrics/words - each syllable should be aligned to its corresponding note
4. The key signature
5. The time signature
6. Song title if visible

Return structured JSON with this EXACT format:
{
    "key_signature": "C major",
    "time_signature": "4/4",
    "title": "Song Title",
    "measures": [
        {
            "number": 1,
            "notes": [
                {"pitch": "C", "octave": 4, "duration": "quarter", "lyric": "My"},
                {"pitch": "C", "octave": 4, "duration": "quarter", "lyric": "thanks"},
                {"pitch": "G", "octave": 4, "duration": "quarter", "lyric": "to"},
                {"pitch": "G", "octave": 4, "duration": "quarter", "lyric": "Him"}
            ]
        }
    ]
}

CRITICAL INSTRUCTIONS:
1. Extract EVERY note visible on the staff - do not skip any
2. For EACH note, include the lyric syllable directly below it
3. If a note has no lyric, use null for lyric
4. If a note is held (no new syllable), use "-" for lyric
5. Group notes by measure (separated by bar lines)
6. Return ONLY valid JSON"""

        message = UserMessage(text=prompt, file_contents=[image_content])
        
        try:
            response = await chat.send_message(message)
            logger.info(f"Gemini response length: {len(response)}")
        except Exception as e:
            error_str = str(e)
            if '429' in error_str or 'quota' in error_str.lower():
                return {
                    'success': False,
                    'error': 'API credits exhausted. Please try again later or add your own Gemini API key.',
                    'error_type': 'QUOTA_EXCEEDED'
                }
            raise
        
        # Parse JSON from response
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(response)
            
            data['success'] = True
            data['analysis_method'] = 'gemini-2.5-flash'
            
            logger.info(f"Extracted {len(data.get('measures', []))} measures")
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            return {
                'success': False,
                'error': f'Could not parse music data from image. Try uploading a higher quality scan.',
                'error_type': 'PARSE_ERROR',
                'raw_response': response[:500]
            }
            
    except Exception as e:
        logger.error(f"Gemini analysis failed: {e}")
        error_str = str(e)
        
        if '429' in error_str or 'quota' in error_str.lower():
            return {
                'success': False,
                'error': 'API credits exhausted. Please try again later.',
                'error_type': 'QUOTA_EXCEEDED'
            }
        
        return {
            'success': False,
            'error': f'Could not read this page. Try uploading a higher quality scan.',
            'error_type': 'ANALYSIS_ERROR'
        }


def analyze_sheet_music_with_gemini_sync(image_path: str, user_api_key: str = None) -> Dict:
    """Synchronous wrapper for Gemini analysis."""
    import asyncio
    import nest_asyncio
    nest_asyncio.apply()
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(analyze_sheet_music_with_gemini(image_path, user_api_key))


def convert_to_motesart_format(gemini_data: Dict, key_override: str = None) -> Dict:
    """
    Convert Gemini output to Motesart format with aligned lyrics.
    """
    if not gemini_data.get('success'):
        return gemini_data
    
    key_sig = key_override or gemini_data.get('key_signature', 'C major')
    key_name = key_sig.replace(' major', '').replace(' minor', '').strip()
    key_root = get_key_root_semitone(key_name)
    
    formatted_measures = []
    all_notes = []
    all_lyrics = []
    
    for measure in gemini_data.get('measures', []):
        measure_notes = []
        measure_lyrics = []
        
        for note in measure.get('notes', []):
            pitch = note.get('pitch', 'C')
            octave = note.get('octave', 4)
            lyric = note.get('lyric') or ''
            duration = note.get('duration', 'quarter')
            
            # Handle rest notes
            if pitch.lower() == 'rest' or not pitch:
                measure_notes.append({
                    'pitch': 'rest',
                    'octave': None,
                    'motesart': '-',
                    'number': '-',
                    'accidental': '',
                    'dots_above': '',
                    'dots_below': '',
                    'duration': duration,
                    'lyric': lyric
                })
                measure_lyrics.append(lyric or '-')
                continue
            
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
            
            measure_lyrics.append(lyric or '-')
        
        formatted_measures.append({
            'number': measure.get('number', len(formatted_measures) + 1),
            'notes': measure_notes,
            'lyrics': measure_lyrics
        })
        
        all_notes.extend(measure_notes)
        all_lyrics.extend(measure_lyrics)
    
    # Create aligned display lines
    number_lines = []
    lyric_lines = []
    
    current_number_line = '|'
    current_lyric_line = '|'
    
    for measure in formatted_measures:
        for note in measure['notes']:
            display = note['motesart']
            lyric = note['lyric'] or '-'
            
            # Pad to align - use the longer of the two
            max_len = max(len(display), len(lyric), 3)
            current_number_line += f" {display.center(max_len)}"
            current_lyric_line += f" {lyric.center(max_len)}"
        
        current_number_line += ' |'
        current_lyric_line += ' |'
        
        # Start new line after 4 measures
        if len(current_number_line) > 60:
            number_lines.append(current_number_line)
            lyric_lines.append(current_lyric_line)
            current_number_line = '|'
            current_lyric_line = '|'
    
    # Add remaining content
    if current_number_line != '|':
        number_lines.append(current_number_line)
        lyric_lines.append(current_lyric_line)
    
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
            'number_lines': number_lines,
            'lyric_lines': lyric_lines,
            'combined': list(zip(number_lines, lyric_lines))
        },
        'analysis_method': gemini_data.get('analysis_method', 'gemini-2.5-flash')
    }


def process_sheet_music_omr(file_path: str, key_override: str = None, user_api_key: str = None) -> Dict:
    """
    Main OMR processing function with MULTI-PAGE PDF support.
    """
    logger.info(f"Starting OMR processing: {file_path}")
    
    result = {
        'success': False,
        'error': None,
        'error_type': None,
        'key_signature': None,
        'key_name': None,
        'time_signature': '4/4',
        'title': None,
        'pages': [],
        'measures': [],
        'all_notes': [],
        'all_lyrics': [],
        'display': None,
        'analysis_method': None,
        'total_pages': 0,
        'successful_pages': 0,
        'failed_pages': []
    }
    
    try:
        file_ext = os.path.splitext(file_path)[1].lower()
        temp_images = []
        pages_to_process = []
        
        # Convert PDF to images (ALL pages)
        if file_ext == '.pdf':
            logger.info("Converting multi-page PDF...")
            pdf_pages = convert_pdf_to_images(file_path, dpi=300)
            
            if not pdf_pages:
                result['error'] = "Failed to convert PDF to images"
                result['error_type'] = 'PDF_CONVERSION_ERROR'
                return result
            
            result['total_pages'] = len(pdf_pages)
            pages_to_process = pdf_pages
            temp_images = [p['image_path'] for p in pdf_pages if p['image_path']]
            
            # Also try to extract text for lyrics fallback
            pdf_text = extract_text_from_pdf(file_path)
            
        # Handle single image
        elif file_ext in ['.png', '.jpg', '.jpeg', '.webp']:
            pages_to_process = [{
                'page_number': 1,
                'image_path': file_path,
                'success': True,
                'error': None
            }]
            result['total_pages'] = 1
            
        # Handle HEIC
        elif file_ext in ['.heic', '.heif']:
            try:
                from PIL import Image
                import pillow_heif
                pillow_heif.register_heif_opener()
                
                heic_img = Image.open(file_path)
                temp_png = tempfile.mktemp(suffix='.png')
                heic_img.save(temp_png, 'PNG')
                pages_to_process = [{
                    'page_number': 1,
                    'image_path': temp_png,
                    'success': True,
                    'error': None
                }]
                temp_images.append(temp_png)
                result['total_pages'] = 1
            except Exception as e:
                result['error'] = f"Could not convert HEIC: {e}"
                result['error_type'] = 'HEIC_CONVERSION_ERROR'
                return result
        else:
            result['error'] = f"Unsupported file format: {file_ext}"
            result['error_type'] = 'UNSUPPORTED_FORMAT'
            return result
        
        # Process EACH page with Gemini
        all_measures = []
        all_notes_combined = []
        all_lyrics_combined = []
        page_results = []
        
        for page_info in pages_to_process:
            page_num = page_info['page_number']
            
            if not page_info['success'] or not page_info['image_path']:
                page_results.append({
                    'page_number': page_num,
                    'success': False,
                    'error': page_info.get('error', 'Page conversion failed'),
                    'measures': [],
                    'notes': []
                })
                result['failed_pages'].append(page_num)
                continue
            
            logger.info(f"Processing page {page_num}/{result['total_pages']}...")
            
            # Analyze with Gemini
            gemini_result = analyze_sheet_music_with_gemini_sync(
                page_info['image_path'],
                user_api_key
            )
            
            if gemini_result.get('success'):
                # Convert to Motesart format
                motesart_result = convert_to_motesart_format(gemini_result, key_override)
                
                if motesart_result.get('success'):
                    # Get key and time from first successful page
                    if not result['key_signature']:
                        result['key_signature'] = motesart_result.get('key_signature')
                        result['key_name'] = motesart_result.get('key_name')
                        result['time_signature'] = motesart_result.get('time_signature')
                        result['title'] = motesart_result.get('title')
                    
                    page_measures = motesart_result.get('measures', [])
                    page_notes = motesart_result.get('all_notes', [])
                    page_lyrics = motesart_result.get('all_lyrics', [])
                    
                    page_results.append({
                        'page_number': page_num,
                        'success': True,
                        'measures': page_measures,
                        'notes': page_notes,
                        'lyrics': page_lyrics,
                        'display': motesart_result.get('display'),
                        'image_path': page_info['image_path']
                    })
                    
                    all_measures.extend(page_measures)
                    all_notes_combined.extend(page_notes)
                    all_lyrics_combined.extend(page_lyrics)
                    result['successful_pages'] += 1
                else:
                    page_results.append({
                        'page_number': page_num,
                        'success': False,
                        'error': motesart_result.get('error', 'Conversion failed'),
                        'measures': [],
                        'notes': []
                    })
                    result['failed_pages'].append(page_num)
            else:
                page_results.append({
                    'page_number': page_num,
                    'success': False,
                    'error': gemini_result.get('error', f'Could not read page {page_num}'),
                    'error_type': gemini_result.get('error_type'),
                    'measures': [],
                    'notes': []
                })
                result['failed_pages'].append(page_num)
                
                # Check if quota exceeded - stop processing more pages
                if gemini_result.get('error_type') == 'QUOTA_EXCEEDED':
                    result['error'] = gemini_result.get('error')
                    result['error_type'] = 'QUOTA_EXCEEDED'
                    break
        
        # Combine all page results
        result['pages'] = page_results
        result['measures'] = all_measures
        result['all_notes'] = all_notes_combined
        result['all_lyrics'] = all_lyrics_combined
        
        # Create combined display
        if all_measures:
            result['success'] = True
            result['analysis_method'] = 'gemini-2.5-flash'
            
            # Rebuild display from all measures
            number_lines = []
            lyric_lines = []
            current_number = '|'
            current_lyric = '|'
            
            for i, measure in enumerate(all_measures):
                for note in measure.get('notes', []):
                    display = note.get('motesart', '-')
                    lyric = note.get('lyric') or '-'
                    max_len = max(len(display), len(lyric), 3)
                    current_number += f" {display.center(max_len)}"
                    current_lyric += f" {lyric.center(max_len)}"
                
                current_number += ' |'
                current_lyric += ' |'
                
                # New line every 4 measures
                if (i + 1) % 4 == 0:
                    number_lines.append(current_number)
                    lyric_lines.append(current_lyric)
                    current_number = '|'
                    current_lyric = '|'
            
            if current_number != '|':
                number_lines.append(current_number)
                lyric_lines.append(current_lyric)
            
            result['display'] = {
                'number_lines': number_lines,
                'lyric_lines': lyric_lines,
                'combined': list(zip(number_lines, lyric_lines))
            }
        
        # Clean up temp files
        for temp_path in temp_images:
            try:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                pass
        
        return result
        
    except Exception as e:
        logger.error(f"OMR processing error: {e}")
        import traceback
        traceback.print_exc()
        result['error'] = str(e)
        result['error_type'] = 'PROCESSING_ERROR'
        return result


def extract_notes_for_staff_view(omr_data: Dict) -> List[Dict]:
    """Extract notes from OMR data for staff view rendering."""
    if not omr_data:
        return []
    
    notes = omr_data.get('all_notes', [])
    if not notes:
        for measure in omr_data.get('measures', []):
            notes.extend(measure.get('notes', []))
    
    return notes


def pitch_to_motesart(pitch: str, key_root: int) -> str:
    """Simple pitch to Motesart number conversion."""
    if not pitch:
        return "?"
    
    match = re.match(r'^([A-Ga-g][#b]?)(-?\d)?$', pitch)
    if not match:
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
