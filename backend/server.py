from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Request, Response, Depends
from fastapi.responses import FileResponse, StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import httpx
import io
import json
import tempfile

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

class User(BaseModel):
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SessionData(BaseModel):
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ConversionCreate(BaseModel):
    filename: str
    file_type: str

class Conversion(BaseModel):
    conversion_id: str
    user_id: str
    filename: str
    file_type: str
    status: str  # processing, completed, error
    key_signature: Optional[str] = None
    time_signature: Optional[str] = None
    tempo: Optional[int] = None
    notes: List[Dict[str, Any]] = []
    chords: List[Dict[str, Any]] = []
    progressions: List[Dict[str, Any]] = []
    sections: List[Dict[str, Any]] = []
    raw_data: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ExplainRequest(BaseModel):
    conversion_id: str
    section_index: Optional[int] = None
    context: Optional[str] = None

class EmailLoginRequest(BaseModel):
    email: str
    password: str

class EmailRegisterRequest(BaseModel):
    name: str
    email: str
    password: str

# ==================== AUTH HELPERS ====================

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    import bcrypt
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    import bcrypt
    return bcrypt.checkpw(password.encode(), hashed.encode())

async def get_current_user(request: Request) -> User:
    """Extract user from session token (cookie or header)"""
    session_token = request.cookies.get("session_token")
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.split(" ")[1]
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session_doc = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session_doc:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    expires_at = session_doc["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")
    
    user_doc = await db.users.find_one({"user_id": session_doc["user_id"]}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="User not found")
    
    return User(**user_doc)

# ==================== AUTH ENDPOINTS ====================

@api_router.post("/auth/session")
async def create_session(request: Request, response: Response):
    """Exchange session_id for session_token"""
    body = await request.json()
    session_id = body.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    
    async with httpx.AsyncClient() as client_http:
        resp = await client_http.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id}
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid session_id")
        data = resp.json()
    
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    existing_user = await db.users.find_one({"email": data["email"]}, {"_id": 0})
    
    if existing_user:
        user_id = existing_user["user_id"]
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"name": data["name"], "picture": data.get("picture")}}
        )
    else:
        await db.users.insert_one({
            "user_id": user_id,
            "email": data["email"],
            "name": data["name"],
            "picture": data.get("picture"),
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    session_token = data.get("session_token") or f"st_{uuid.uuid4().hex}"
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    await db.user_sessions.delete_many({"user_id": user_id})
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 60 * 60
    )
    
    user_doc = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    return user_doc

@api_router.get("/auth/me")
async def get_me(user: User = Depends(get_current_user)):
    """Get current authenticated user"""
    return user.model_dump()

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    """Logout user and clear session"""
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_many({"session_token": session_token})
    
    response.delete_cookie(key="session_token", path="/", secure=True, samesite="none")
    return {"message": "Logged out successfully"}

@api_router.post("/auth/register")
async def register_email(req: EmailRegisterRequest, response: Response):
    """Register with email and password"""
    # Check if email already exists
    existing_user = await db.users.find_one({"email": req.email}, {"_id": 0})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    hashed_pw = hash_password(req.password)
    
    await db.users.insert_one({
        "user_id": user_id,
        "email": req.email,
        "name": req.name,
        "password_hash": hashed_pw,
        "auth_type": "email",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Create session
    session_token = f"st_{uuid.uuid4().hex}"
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 60 * 60
    )
    
    user_doc = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
    return user_doc

@api_router.post("/auth/login")
async def login_email(req: EmailLoginRequest, response: Response):
    """Login with email and password"""
    user_doc = await db.users.find_one({"email": req.email}, {"_id": 0})
    
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Check if this is an email-auth user
    if not user_doc.get("password_hash"):
        raise HTTPException(status_code=401, detail="Please use Google login for this account")
    
    if not verify_password(req.password, user_doc["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create session
    session_token = f"st_{uuid.uuid4().hex}"
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    await db.user_sessions.delete_many({"user_id": user_doc["user_id"]})
    await db.user_sessions.insert_one({
        "user_id": user_doc["user_id"],
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 60 * 60
    )
    
    # Remove password_hash from response
    user_doc.pop("password_hash", None)
    return user_doc

# ==================== MOTESART CONVERSION LOGIC ====================

# Scale degree mapping (semitones from root)
MAJOR_SCALE_SEMITONES = [0, 2, 4, 5, 7, 9, 11]  # 1, 2, 3, 4, 5, 6, 7
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
FLAT_NAMES = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']

def get_note_number(pitch: int, key_root: int) -> str:
    """Convert MIDI pitch to Motesart number relative to key"""
    semitones_from_root = (pitch - key_root) % 12
    
    # Check if it's a scale degree
    if semitones_from_root in MAJOR_SCALE_SEMITONES:
        return str(MAJOR_SCALE_SEMITONES.index(semitones_from_root) + 1)
    
    # Half-numbers for chromatic tones
    # No 3½ (between 3-4 is natural half step) or 7½ (between 7-1 is natural half step)
    half_number_map = {
        1: "1½",   # Between 1 and 2
        3: "2½",   # Between 2 and 3
        6: "4½",   # Between 4 and 5
        8: "5½",   # Between 5 and 6
        10: "6½",  # Between 6 and 7
    }
    
    return half_number_map.get(semitones_from_root, f"?{semitones_from_root}")

def detect_key_from_notes(notes: List[Dict]) -> tuple:
    """Detect key from note frequency analysis"""
    if not notes:
        return 0, "C"  # Default to C major
    
    pitch_classes = [n.get("pitch", 60) % 12 for n in notes]
    pitch_counts = {}
    for pc in pitch_classes:
        pitch_counts[pc] = pitch_counts.get(pc, 0) + 1
    
    # Try each possible key and score how well notes fit the major scale
    best_key = 0
    best_score = -1
    
    for root in range(12):
        scale_pcs = [(root + s) % 12 for s in MAJOR_SCALE_SEMITONES]
        score = sum(pitch_counts.get(pc, 0) for pc in scale_pcs)
        if score > best_score:
            best_score = score
            best_key = root
    
    key_name = NOTE_NAMES[best_key]
    return best_key, key_name

def detect_chord(pitches: List[int], key_root: int) -> Dict:
    """
    Detect chord type from simultaneous pitches using Motesart methodology.
    
    NEW METHODOLOGY (from THE MOTESART NUMBER SYSTEM 1pg Methodology.docx):
    - Section 5: Extensions use superscripts (2⁹, 4¹¹, 6¹³)
    - Section 7: Slash notation is BASS FIRST, CHORD SECOND (e.g., 1/3 = 1 in bass, 3-chord above)
    
    Symbol Legend:
    - m → minor chord
    - M → major chord (non-diatonic only)
    - ⁺ → augmented chord
    - ° → diminished chord
    - sus² → suspended 2
    - sus⁴ → suspended 4
    - ⁷ → seventh chord
    - ⁹ ¹¹ ¹³ → extensions (with base numbers 2⁹, 4¹¹, 6¹³)
    - /X → bass note (slash notation, bass first)
    - ½ → chromatic step up
    """
    if len(pitches) < 2:
        return None
    
    pitches = sorted(set(pitches))
    bass = pitches[0]  # Lowest note is bass
    
    # Try to identify root by analyzing intervals
    # For now, assume root is the bass note unless we detect an inversion pattern
    root = bass
    
    intervals = [(p - root) % 12 for p in pitches]
    intervals = sorted(set(intervals))
    
    # Chord quality detection with extensions
    chord_type = "unknown"
    extensions = []
    
    # Basic triads
    if set([0, 4, 7]).issubset(set(intervals)):
        chord_type = "Major"
    elif set([0, 3, 7]).issubset(set(intervals)):
        chord_type = "minor"
    elif intervals == [0, 3, 6] or set([0, 3, 6]).issubset(set(intervals)):
        chord_type = "dim"
    elif intervals == [0, 4, 8] or set([0, 4, 8]).issubset(set(intervals)):
        chord_type = "aug"
    elif set([0, 2, 7]).issubset(set(intervals)):
        chord_type = "sus²"
    elif set([0, 5, 7]).issubset(set(intervals)):
        chord_type = "sus⁴"
    
    # Seventh chords
    if 11 in intervals:  # Major 7th
        chord_type = "M⁷" if chord_type == "Major" else chord_type + "M⁷"
    elif 10 in intervals:  # Minor 7th (dominant or minor)
        if chord_type == "Major":
            chord_type = "⁷"  # Dominant 7
        elif chord_type == "minor":
            chord_type = "m⁷"
        elif chord_type == "dim":
            chord_type = "ø⁷"  # Half-diminished
    elif 9 in intervals and chord_type == "dim":
        chord_type = "°⁷"  # Fully diminished
    
    # Extensions (Section 5 methodology: 2⁹, 4¹¹, 6¹³)
    # These show upper-structure color without introducing new numbers
    if 2 in intervals or 14 in intervals:  # 9th (2 an octave up)
        extensions.append("⁹")
    if 5 in intervals and chord_type not in ["sus⁴"]:  # 11th (4 an octave up)
        # Only mark as extension if not a sus4 chord
        if 14 in intervals or 2 in intervals:  # Only if 9th is present
            extensions.append("¹¹")
    if 9 in intervals and "⁷" in chord_type:  # 13th (6 an octave up)
        extensions.append("¹³")
    
    root_number = get_note_number(root, key_root)
    bass_number = get_note_number(bass, key_root)
    
    # Build symbol
    symbol = root_number
    if chord_type == "minor":
        symbol += "m"
    elif chord_type == "dim":
        symbol += "°"
    elif chord_type == "aug":
        symbol += "⁺"
    elif chord_type not in ["Major", "unknown"]:
        symbol += chord_type
    
    # Add extensions
    if extensions:
        symbol += "".join(extensions)
    
    # Section 7: Slash notation - BASS FIRST, CHORD SECOND
    # Format: bass/chord (e.g., 1/3 = 1 in bass, 3-chord above)
    # This is different from traditional notation!
    chord_above = None
    if bass_number != root_number:
        # The symbol represents the chord, bass_number is what's in the bass
        # New format: bass/chord
        chord_above = symbol
        symbol = f"{bass_number}/{root_number}"
        if chord_type not in ["Major", "unknown"]:
            # Add chord quality to the chord part
            symbol = f"{bass_number}/{root_number}"
            if chord_type == "minor":
                symbol += "m"
            elif chord_type == "dim":
                symbol += "°"
            elif chord_type == "aug":
                symbol += "⁺"
    
    return {
        "symbol": symbol,
        "root": root_number,
        "type": chord_type,
        "bass": bass_number,
        "chord_above": chord_above,
        "extensions": extensions,
        "pitches": pitches,
        "methodology_note": "Bass-first slash notation (Section 7): X/Y = X in bass, Y-chord above"
    }

def detect_progressions(chords: List[Dict]) -> List[Dict]:
    """Detect common chord progressions"""
    if len(chords) < 2:
        return []
    
    progressions = []
    roots = [c.get("root", "1") for c in chords if c]
    
    # Common patterns to detect
    patterns = {
        "2-5-1": ["2", "5", "1"],
        "1-6-4-5": ["1", "6", "4", "5"],
        "1-4-5-1": ["1", "4", "5", "1"],
        "1-5-6-4": ["1", "5", "6", "4"],
        "6-4-1-5": ["6", "4", "1", "5"],
        "4-5-1": ["4", "5", "1"],
    }
    
    for name, pattern in patterns.items():
        for i in range(len(roots) - len(pattern) + 1):
            window = roots[i:i + len(pattern)]
            # Clean roots for comparison (remove 'm', '7', etc.)
            clean_window = [r.replace("m", "").replace("7", "").split("/")[0] for r in window]
            if clean_window == pattern:
                progressions.append({
                    "name": name,
                    "start_index": i,
                    "end_index": i + len(pattern),
                    "description": f"Functional progression: {name}"
                })
    
    return progressions

def parse_midi_file(content: bytes) -> Dict:
    """Parse MIDI file and extract musical information"""
    import mido
    
    midi = mido.MidiFile(file=io.BytesIO(content))
    
    notes = []
    tempo = 120
    time_signature = "4/4"
    
    ticks_per_beat = midi.ticks_per_beat
    current_time = 0
    active_notes = {}
    
    for track in midi.tracks:
        current_time = 0
        for msg in track:
            current_time += msg.time
            
            if msg.type == 'set_tempo':
                tempo = int(60000000 / msg.tempo)
            elif msg.type == 'time_signature':
                time_signature = f"{msg.numerator}/{msg.denominator}"
            elif msg.type == 'note_on' and msg.velocity > 0:
                active_notes[(msg.channel, msg.note)] = {
                    "pitch": msg.note,
                    "start_time": current_time,
                    "velocity": msg.velocity
                }
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                key = (msg.channel, msg.note)
                if key in active_notes:
                    note = active_notes.pop(key)
                    note["end_time"] = current_time
                    note["duration"] = current_time - note["start_time"]
                    note["beat"] = note["start_time"] / ticks_per_beat
                    notes.append(note)
    
    return {
        "notes": notes,
        "tempo": tempo,
        "time_signature": time_signature,
        "ticks_per_beat": ticks_per_beat
    }

def parse_musicxml_file(content: bytes) -> Dict:
    """Parse MusicXML file and extract musical information"""
    from music21 import converter, key as m21key, meter, tempo as m21tempo
    
    with tempfile.NamedTemporaryFile(suffix='.xml', delete=False) as f:
        f.write(content)
        temp_path = f.name
    
    try:
        score = converter.parse(temp_path)
        
        # Extract key
        key_sig = score.analyze('key')
        key_name = key_sig.tonic.name if key_sig else "C"
        mode = key_sig.mode if key_sig else "major"
        
        # Extract time signature
        ts = score.recurse().getElementsByClass(meter.TimeSignature)
        time_sig = f"{ts[0].numerator}/{ts[0].denominator}" if ts else "4/4"
        
        # Extract tempo
        tempos = score.recurse().getElementsByClass(m21tempo.MetronomeMark)
        bpm = int(tempos[0].number) if tempos else 120
        
        # Extract notes
        notes = []
        for element in score.recurse().notes:
            if hasattr(element, 'pitch'):
                notes.append({
                    "pitch": element.pitch.midi,
                    "name": element.pitch.nameWithOctave,
                    "beat": float(element.offset),
                    "duration": float(element.quarterLength),
                    "octave": element.pitch.octave
                })
            elif hasattr(element, 'pitches'):  # Chord
                for p in element.pitches:
                    notes.append({
                        "pitch": p.midi,
                        "name": p.nameWithOctave,
                        "beat": float(element.offset),
                        "duration": float(element.quarterLength),
                        "octave": p.octave
                    })
        
        return {
            "notes": notes,
            "key": f"{key_name} {mode}",
            "time_signature": time_sig,
            "tempo": bpm
        }
    finally:
        os.unlink(temp_path)

def convert_to_motesart(parsed_data: Dict) -> Dict:
    """Convert parsed music data to Motesart number system"""
    notes = parsed_data.get("notes", [])
    
    # Detect key
    key_root, key_name = detect_key_from_notes(notes)
    
    # Convert notes to Motesart numbers
    motesart_notes = []
    for note in notes:
        pitch = note.get("pitch", 60)
        number = get_note_number(pitch, key_root)
        
        motesart_notes.append({
            **note,
            "motesart_number": number,
            "key_root": key_root
        })
    
    # Group notes by beat for chord detection
    beat_groups = {}
    for note in motesart_notes:
        beat = round(note.get("beat", 0) * 4) / 4  # Quantize to sixteenth notes
        if beat not in beat_groups:
            beat_groups[beat] = []
        beat_groups[beat].append(note)
    
    # Detect chords
    chords = []
    for beat in sorted(beat_groups.keys()):
        group = beat_groups[beat]
        if len(group) >= 2:
            pitches = [n["pitch"] for n in group]
            chord = detect_chord(pitches, key_root)
            if chord:
                chord["beat"] = beat
                chord["measure"] = int(beat / 4) + 1
                chords.append(chord)
    
    # Detect progressions
    progressions = detect_progressions(chords)
    
    # Create sections based on measure groups
    sections = []
    if motesart_notes:
        max_beat = max(n.get("beat", 0) for n in motesart_notes)
        measures = int(max_beat / 4) + 1
        
        # Group into 4-bar sections
        for i in range(0, measures, 4):
            section_chords = [c for c in chords if i <= c.get("measure", 1) - 1 < i + 4]
            chord_roots = [c["root"] for c in section_chords if c]
            
            sections.append({
                "name": f"Section {i // 4 + 1}",
                "start_measure": i + 1,
                "end_measure": min(i + 4, measures),
                "progression": "-".join(chord_roots[:4]) if chord_roots else "N/A"
            })
    
    return {
        "key_signature": f"1 = {key_name}",
        "key_root": key_root,
        "key_name": key_name,
        "time_signature": parsed_data.get("time_signature", "4/4"),
        "tempo": parsed_data.get("tempo", 120),
        "notes": motesart_notes,
        "chords": chords,
        "progressions": progressions,
        "sections": sections
    }

# ==================== FILE UPLOAD & CONVERSION ====================

# Supported file types
SUPPORTED_MUSIC_FILES = ["mid", "midi", "xml", "musicxml", "mxl"]
SUPPORTED_SHEET_MUSIC = ["pdf", "png", "jpg", "jpeg"]
ALL_SUPPORTED = SUPPORTED_MUSIC_FILES + SUPPORTED_SHEET_MUSIC

@api_router.post("/upload")
async def upload_file(file: UploadFile = File(...), user: User = Depends(get_current_user)):
    """
    Upload and convert a music file.
    
    Sheet-music first approach:
    - Primary: PDF, PNG, JPG (sheet music images)
    - Secondary: MusicXML, MIDI (digital music files)
    
    For PDF/images: stores file and marks as "uploaded" (OMR processing in Phase 2)
    For MIDI/MusicXML: immediate conversion to Motesart numbers
    """
    filename = file.filename or "unknown"
    extension = filename.split(".")[-1].lower()
    
    if extension not in ALL_SUPPORTED:
        raise HTTPException(
            status_code=400, 
            detail="Unsupported file type. Please upload sheet music (PDF, PNG, JPG) or music files (MusicXML, MIDI)."
        )
    
    content = await file.read()
    file_size = len(content)
    
    conversion_id = f"conv_{uuid.uuid4().hex[:12]}"
    
    # Determine file category
    is_sheet_music = extension in SUPPORTED_SHEET_MUSIC
    initial_status = "uploaded" if is_sheet_music else "processing"
    
    # Save initial conversion record
    conversion_doc = {
        "conversion_id": conversion_id,
        "user_id": user.user_id,
        "filename": filename,
        "file_type": extension,
        "file_size": file_size,
        "is_sheet_music": is_sheet_music,
        "status": initial_status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # For sheet music (PDF/images), store the file content for later OMR processing
    if is_sheet_music:
        import base64
        conversion_doc["file_data"] = base64.b64encode(content).decode('utf-8')
        conversion_doc["status_message"] = "Uploaded – waiting for conversion (OMR coming in Phase 2)"
    
    await db.conversions.insert_one(conversion_doc)
    
    # For MIDI/MusicXML, process immediately
    if not is_sheet_music:
        try:
            # Parse file based on type
            if extension in ["mid", "midi"]:
                parsed_data = parse_midi_file(content)
            else:
                parsed_data = parse_musicxml_file(content)
            
            # Convert to Motesart
            motesart_data = convert_to_motesart(parsed_data)
            
            # Update conversion record with results
            await db.conversions.update_one(
                {"conversion_id": conversion_id},
                {"$set": {
                    "status": "completed",
                    "key_signature": motesart_data["key_signature"],
                    "time_signature": motesart_data["time_signature"],
                    "tempo": motesart_data["tempo"],
                    "notes": motesart_data["notes"],
                    "chords": motesart_data["chords"],
                    "progressions": motesart_data["progressions"],
                    "sections": motesart_data["sections"],
                    "raw_data": {"key_root": motesart_data["key_root"], "key_name": motesart_data["key_name"]},
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
        except Exception as e:
            logger.error(f"Conversion error: {str(e)}")
            await db.conversions.update_one(
                {"conversion_id": conversion_id},
                {"$set": {
                    "status": "error", 
                    "error_message": str(e),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")
    
    # Return the conversion record (without file_data for response size)
    conversion_doc = await db.conversions.find_one(
        {"conversion_id": conversion_id}, 
        {"_id": 0, "file_data": 0}
    )
    return conversion_doc

@api_router.get("/conversions/{conversion_id}/file")
async def get_conversion_file(conversion_id: str, user: User = Depends(get_current_user)):
    """Get the original uploaded file for a conversion (for sheet music display)"""
    conversion = await db.conversions.find_one(
        {"conversion_id": conversion_id, "user_id": user.user_id},
        {"_id": 0}
    )
    if not conversion:
        raise HTTPException(status_code=404, detail="Conversion not found")
    
    if not conversion.get("file_data"):
        raise HTTPException(status_code=404, detail="No file data available")
    
    import base64
    file_data = base64.b64decode(conversion["file_data"])
    file_type = conversion.get("file_type", "pdf")
    
    media_types = {
        "pdf": "application/pdf",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg"
    }
    
    return StreamingResponse(
        io.BytesIO(file_data),
        media_type=media_types.get(file_type, "application/octet-stream"),
        headers={"Content-Disposition": f"inline; filename={conversion.get('filename', 'file')}"}
    )

@api_router.get("/conversions")
async def get_conversions(user: User = Depends(get_current_user)):
    """Get user's conversion history"""
    conversions = await db.conversions.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return conversions

@api_router.get("/conversions/{conversion_id}")
async def get_conversion(conversion_id: str, user: User = Depends(get_current_user)):
    """Get a specific conversion"""
    conversion = await db.conversions.find_one(
        {"conversion_id": conversion_id, "user_id": user.user_id},
        {"_id": 0}
    )
    if not conversion:
        raise HTTPException(status_code=404, detail="Conversion not found")
    return conversion

@api_router.delete("/conversions/{conversion_id}")
async def delete_conversion(conversion_id: str, user: User = Depends(get_current_user)):
    """Delete a conversion"""
    result = await db.conversions.delete_one({
        "conversion_id": conversion_id,
        "user_id": user.user_id
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conversion not found")
    return {"message": "Conversion deleted"}

# ==================== AI EXPLANATIONS ====================

@api_router.post("/explain")
async def explain_section(req: ExplainRequest, user: User = Depends(get_current_user)):
    """Generate AI explanation for a conversion section"""
    conversion = await db.conversions.find_one(
        {"conversion_id": req.conversion_id, "user_id": user.user_id},
        {"_id": 0}
    )
    if not conversion:
        raise HTTPException(status_code=404, detail="Conversion not found")
    
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        api_key = os.environ.get("EMERGENT_LLM_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="LLM API key not configured")
        
        # Build context
        key_sig = conversion.get("key_signature", "1 = C")
        chords = conversion.get("chords", [])[:10]
        sections = conversion.get("sections", [])
        progressions = conversion.get("progressions", [])
        
        section_context = ""
        if req.section_index is not None and req.section_index < len(sections):
            section = sections[req.section_index]
            section_context = f"Current section: {section.get('name')} (measures {section.get('start_measure')}-{section.get('end_measure')}), progression: {section.get('progression')}"
        
        prompt = f"""You are a music theory expert explaining the Motesart Number System.

Key: {key_sig}
Chords detected: {json.dumps(chords[:5], indent=2)}
Progressions found: {json.dumps(progressions, indent=2)}
{section_context}
{f"User question: {req.context}" if req.context else ""}

Explain what the user is seeing in plain, student-friendly language. Focus on:
1. What the numbers mean in this key
2. The chord progression and its function (e.g., 2-5-1 resolution)
3. Any chromatic tones (half-numbers like 2½) and their role
4. Inversion notation (e.g., 1/3 means 1 chord with 3 in bass)

Keep the explanation concise (2-3 paragraphs) and educational."""

        chat = LlmChat(
            api_key=api_key,
            session_id=f"explain_{req.conversion_id}",
            system_message="You are a helpful music theory teacher specializing in the Motesart Number System."
        ).with_model("openai", "gpt-5.2")
        
        response = await chat.send_message(UserMessage(text=prompt))
        
        return {"explanation": response}
        
    except ImportError:
        return {"explanation": f"Key: {conversion.get('key_signature', 'Unknown')}. This piece uses the Motesart Number System where 1 represents the tonic note. Chords and progressions are shown as numbers relative to the key."}
    except Exception as e:
        logger.error(f"Explain error: {str(e)}")
        return {"explanation": f"Key: {conversion.get('key_signature', 'Unknown')}. Unable to generate detailed explanation at this time."}

# ==================== EXPORT ====================

@api_router.get("/export/{conversion_id}")
async def export_conversion(
    conversion_id: str, 
    format: str = "text",
    user: User = Depends(get_current_user)
):
    """Export conversion to PDF, CSV, or Text"""
    conversion = await db.conversions.find_one(
        {"conversion_id": conversion_id, "user_id": user.user_id},
        {"_id": 0}
    )
    if not conversion:
        raise HTTPException(status_code=404, detail="Conversion not found")
    
    filename_base = conversion.get("filename", "export").rsplit(".", 1)[0]
    
    if format == "csv":
        # Generate CSV
        import csv
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(["Filename", conversion.get("filename")])
        writer.writerow(["Key", conversion.get("key_signature")])
        writer.writerow(["Time Signature", conversion.get("time_signature")])
        writer.writerow(["Tempo", conversion.get("tempo")])
        writer.writerow([])
        
        # Notes
        writer.writerow(["Beat", "Pitch", "Motesart Number", "Duration"])
        for note in conversion.get("notes", []):
            writer.writerow([
                note.get("beat", 0),
                note.get("pitch", 0),
                note.get("motesart_number", ""),
                note.get("duration", 0)
            ])
        
        writer.writerow([])
        writer.writerow(["Chords"])
        writer.writerow(["Beat", "Symbol", "Type", "Root"])
        for chord in conversion.get("chords", []):
            writer.writerow([
                chord.get("beat", 0),
                chord.get("symbol", ""),
                chord.get("type", ""),
                chord.get("root", "")
            ])
        
        content = output.getvalue()
        return StreamingResponse(
            io.BytesIO(content.encode()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename_base}_motesart.csv"}
        )
    
    elif format == "pdf":
        # Generate PDF
        from fpdf import FPDF
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "Motesart Number Conversion", ln=True, align="C")
        
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 8, f"File: {conversion.get('filename')}", ln=True)
        pdf.cell(0, 8, f"Key: {conversion.get('key_signature')}", ln=True)
        pdf.cell(0, 8, f"Time: {conversion.get('time_signature')} | Tempo: {conversion.get('tempo')} BPM", ln=True)
        pdf.ln(5)
        
        # Sections
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Sections & Progressions", ln=True)
        pdf.set_font("Helvetica", "", 11)
        for section in conversion.get("sections", []):
            pdf.cell(0, 7, f"{section.get('name')}: {section.get('progression')}", ln=True)
        
        pdf.ln(5)
        
        # Chords
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Chords", ln=True)
        pdf.set_font("Courier", "", 10)
        
        chords = conversion.get("chords", [])
        chord_line = " | ".join([c.get("symbol", "") for c in chords[:20]])
        pdf.multi_cell(0, 6, chord_line)
        
        pdf_output = io.BytesIO()
        pdf.output(pdf_output)
        pdf_output.seek(0)
        
        return StreamingResponse(
            pdf_output,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename_base}_motesart.pdf"}
        )
    
    else:
        # Generate Text/Markdown
        lines = [
            f"# Motesart Number Conversion",
            f"**File:** {conversion.get('filename')}",
            f"**Key:** {conversion.get('key_signature')}",
            f"**Time:** {conversion.get('time_signature')} | **Tempo:** {conversion.get('tempo')} BPM",
            "",
            "## Sections & Progressions"
        ]
        
        for section in conversion.get("sections", []):
            lines.append(f"- {section.get('name')}: {section.get('progression')}")
        
        lines.extend(["", "## Chords"])
        chords = conversion.get("chords", [])
        chord_line = " | ".join([c.get("symbol", "") for c in chords])
        lines.append(chord_line)
        
        lines.extend(["", "## Progressions Detected"])
        for prog in conversion.get("progressions", []):
            lines.append(f"- {prog.get('name')}: {prog.get('description')}")
        
        content = "\n".join(lines)
        return StreamingResponse(
            io.BytesIO(content.encode()),
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename={filename_base}_motesart.txt"}
        )

# ==================== HEALTH CHECK ====================

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
