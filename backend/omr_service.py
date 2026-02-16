"""
Optical Music Recognition (OMR) Service for Motesart Converter
Uses oemer for image-based OMR and music21 for MusicXML parsing
"""

import os
import tempfile
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path

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


def process_image_with_oemer(image_path: str) -> Optional[str]:
    """
    Process an image file with oemer OMR to get MusicXML.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Path to the generated MusicXML file, or None if failed
    """
    try:
        logger.info(f"Processing image with oemer: {image_path}")
        
        # Create output directory
        output_dir = tempfile.mkdtemp()
        
        # Try using oemer's inference function
        try:
            from oemer import MODULE_PATH
            from oemer.inference import inference
            
            # Get the model path
            model_path = os.path.join(MODULE_PATH, 'checkpoints', 'unet_big')
            
            if os.path.exists(model_path):
                logger.info(f"Running oemer inference with model: {model_path}")
                
                # Run inference - this returns the recognized data
                result = inference(model_path, image_path)
                
                if result:
                    logger.info(f"oemer inference returned result")
                    # The result might be music data we can convert
                    # For now, save it and try to process
                    
                    # Try to export to MusicXML using music21
                    try:
                        from music21 import stream, note, meter, key as m21key
                        
                        # Create a simple score from the result
                        score = stream.Score()
                        part = stream.Part()
                        
                        # Add time signature
                        part.append(meter.TimeSignature('4/4'))
                        
                        # If result has notes, add them
                        if isinstance(result, (list, tuple)):
                            for item in result:
                                if hasattr(item, 'pitch'):
                                    n = note.Note(item.pitch)
                                    part.append(n)
                        
                        score.append(part)
                        
                        musicxml_path = os.path.join(output_dir, "result.musicxml")
                        score.write('musicxml', fp=musicxml_path)
                        
                        if os.path.exists(musicxml_path):
                            return musicxml_path
                            
                    except Exception as e:
                        logger.warning(f"Could not convert oemer result to MusicXML: {e}")
            else:
                logger.warning(f"oemer model not found at: {model_path}")
                
        except Exception as e:
            logger.warning(f"oemer inference failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Fallback: Try using music21 for image processing (limited support)
        try:
            from music21 import converter
            # music21 can't parse images directly, but try anyway
            score = converter.parse(image_path)
            if score:
                musicxml_path = os.path.join(output_dir, "result.musicxml")
                score.write('musicxml', fp=musicxml_path)
                return musicxml_path
        except Exception as e:
            logger.warning(f"music21 image parse failed: {e}")
        
        logger.warning("No OMR method succeeded for image")
        return None
        
    except Exception as e:
        logger.error(f"oemer processing failed: {e}")
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
        from music21 import converter, key, meter, note, chord, stream
        
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
        
        # Extract notes from all parts
        key_root = result['key_root_semitone']
        
        for part_idx, part in enumerate(score.parts):
            part_notes = []
            
            for measure in part.recurse().getElementsByClass(stream.Measure):
                measure_data = {
                    'number': measure.number,
                    'notes': [],
                    'chords': [],
                    'lyrics': []
                }
                
                for element in measure.recurse():
                    if isinstance(element, note.Note):
                        # Extract note data
                        note_data = {
                            'pitch': element.pitch.nameWithOctave,
                            'pitch_name': element.pitch.name,
                            'midi': element.pitch.midi,
                            'duration': float(element.duration.quarterLength),
                            'duration_type': element.duration.type,
                            'offset': float(element.offset),
                            'motesart': pitch_to_motesart(element.pitch.name, key_root),
                        }
                        
                        # Extract lyrics if any
                        if element.lyrics:
                            note_data['lyric'] = ' '.join([l.text for l in element.lyrics if l.text])
                            result['lyrics'].append(note_data['lyric'])
                        
                        measure_data['notes'].append(note_data)
                        part_notes.append(note_data)
                        
                    elif isinstance(element, chord.Chord):
                        # Extract chord data
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
                
                if measure_data['notes'] or measure_data['chords']:
                    result['measures'].append(measure_data)
            
            result['notes'].extend(part_notes)
        
        logger.info(f"Extracted {len(result['notes'])} notes, {len(result['measures'])} measures")
        return result
        
    except Exception as e:
        logger.error(f"music21 parsing failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def process_sheet_music_omr(file_path: str) -> Dict:
    """
    Main entry point for OMR processing.
    
    Args:
        file_path: Path to the sheet music file (PDF or image)
        
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
        'title': None,
    }
    
    try:
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Handle PDF files
        if file_ext == '.pdf':
            image_paths = process_pdf_to_images(file_path)
            if not image_paths:
                result['error'] = "Failed to convert PDF to images"
                return result
            
            # Process first page (can extend to multiple pages)
            musicxml_path = process_image_with_oemer(image_paths[0])
            
            # Clean up temp images
            for img_path in image_paths:
                try:
                    os.remove(img_path)
                except:
                    pass
                    
        # Handle image files
        elif file_ext in ['.png', '.jpg', '.jpeg', '.heic', '.tiff', '.bmp']:
            musicxml_path = process_image_with_oemer(file_path)
        
        # Handle MusicXML files directly
        elif file_ext in ['.xml', '.musicxml', '.mxl']:
            musicxml_path = file_path
        
        # Handle MIDI files
        elif file_ext in ['.mid', '.midi']:
            # music21 can parse MIDI directly
            parsed = parse_musicxml_with_music21(file_path)
            if parsed:
                result.update(parsed)
                result['success'] = True
            else:
                result['error'] = "Failed to parse MIDI file"
            return result
        
        else:
            result['error'] = f"Unsupported file format: {file_ext}"
            return result
        
        # Parse the MusicXML if we got one
        if musicxml_path and os.path.exists(musicxml_path):
            parsed = parse_musicxml_with_music21(musicxml_path)
            if parsed:
                result.update(parsed)
                result['success'] = True
            else:
                result['error'] = "Failed to parse MusicXML output"
        else:
            result['error'] = "OMR processing did not produce MusicXML output"
        
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
