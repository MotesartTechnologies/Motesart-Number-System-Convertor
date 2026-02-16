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
import re

# Import OMR service
from omr_service import (
    process_sheet_music_omr,
    extract_notes_for_staff_view,
    pitch_to_motesart,
    get_key_root_semitone,
    analyze_sheet_music_image
)

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

# ==================== CONSTANTS ====================

# Motesart Logo URL
MOTESART_LOGO_URL = "https://customer-assets.emergentagent.com/job_music-to-numbers/artifacts/eqmmw6fl_2316F097-7806-4D1F-AB36-BB5FF560800D.png"

# Content types for detection
CONTENT_TYPES = {
    "chord_chart": "Chord Chart / Lead Sheet",
    "traditional": "Traditional Sheet Music",
    "hymnal": "Hymnal / SATB",
    "lead_sheet": "Lead Sheet with Chords"
}

# Conversion statuses
STATUS_UPLOADED = "uploaded"
STATUS_CONVERTING_OCR = "converting_ocr"
STATUS_CONVERTING_MOTESART = "converting_motesart"
STATUS_COMPLETED = "completed"
STATUS_ERROR = "error"

# ==================== MODELS ====================

class User(BaseModel):
    user_id: str
    email: str
    name: str
    username: Optional[str] = None  # Display username (e.g., "Motesart" for founder)
    picture: Optional[str] = None  # Google profile picture
    avatar_url: Optional[str] = None  # Custom uploaded avatar
    is_founder: bool = False  # Special flag for Motesart founder account
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UpdateProfileRequest(BaseModel):
    username: Optional[str] = None
    name: Optional[str] = None

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
    content_type: Optional[str] = None  # chord_chart, traditional, hymnal, lead_sheet
    status: str  # uploaded, converting_ocr, converting_motesart, completed, error
    status_message: Optional[str] = None
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

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    conversion_id: str
    message: str
    history: List[ChatMessage] = []

class EmailLoginRequest(BaseModel):
    email: str
    password: str

class EmailRegisterRequest(BaseModel):
    name: str
    email: str
    password: str

# ==================== AVATAR HELPERS ====================

# Motesart founder special avatar
MOTESART_FOUNDER_AVATAR = "https://customer-assets.emergentagent.com/job_music-to-numbers/artifacts/eqmmw6fl_2316F097-7806-4D1F-AB36-BB5FF560800D.png"
MOTESART_FOUNDER_EMAIL = "motesartproductions@gmail.com"  # Update this to actual founder email

def generate_avatar_url(name: str, user_id: str) -> str:
    """
    Generate a unique default avatar for a user based on their initials.
    Uses DiceBear Avatars API for consistent, unique avatars.
    """
    # Get initials (up to 2 characters)
    initials = "".join([word[0].upper() for word in name.split()[:2]]) if name else "U"
    
    # Use DiceBear initials avatar with user_id as seed for uniqueness
    # This ensures each user gets a unique, consistent avatar
    return f"https://api.dicebear.com/7.x/initials/svg?seed={user_id}&chars=2&backgroundColor=6366f1,8b5cf6,06b6d4&textColor=ffffff"

def get_display_avatar(user_doc: dict) -> str:
    """Get the appropriate avatar URL for a user"""
    # Priority: custom avatar_url > Google picture > generated default
    if user_doc.get("avatar_url"):
        return user_doc["avatar_url"]
    if user_doc.get("picture"):
        return user_doc["picture"]
    # Generate default based on name and user_id
    return generate_avatar_url(user_doc.get("name", "User"), user_doc.get("user_id", "default"))

def get_display_name(user_doc: dict) -> str:
    """Get the appropriate display name for a user"""
    # Use username if set, otherwise name
    if user_doc.get("username"):
        return user_doc["username"]
    return user_doc.get("name", "User")

def check_is_founder(email: str) -> bool:
    """Check if the email belongs to the Motesart founder"""
    return email.lower() == MOTESART_FOUNDER_EMAIL.lower()

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
    
    # Check if this is the founder
    is_founder = check_is_founder(data["email"])
    
    if existing_user:
        user_id = existing_user["user_id"]
        # Update user info but preserve custom avatar and username
        update_data = {
            "name": data["name"],
            "picture": data.get("picture"),
            "is_founder": is_founder
        }
        # Set founder-specific fields if this is the founder
        if is_founder and not existing_user.get("username"):
            update_data["username"] = "Motesart"
            update_data["avatar_url"] = MOTESART_FOUNDER_AVATAR
        
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": update_data}
        )
    else:
        # Generate unique avatar for new user
        default_avatar = generate_avatar_url(data["name"], user_id)
        
        new_user_data = {
            "user_id": user_id,
            "email": data["email"],
            "name": data["name"],
            "picture": data.get("picture"),
            "avatar_url": MOTESART_FOUNDER_AVATAR if is_founder else default_avatar,
            "username": "Motesart" if is_founder else None,
            "is_founder": is_founder,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(new_user_data)
    
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
    # Add computed fields
    user_doc["computed_avatar"] = get_display_avatar(user_doc)
    user_doc["display_name"] = get_display_name(user_doc)
    return user_doc

@api_router.get("/auth/me")
async def get_me(user: User = Depends(get_current_user)):
    """Get current authenticated user with avatar info"""
    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0, "password_hash": 0})
    if user_doc:
        # Add computed avatar and display name
        user_doc["computed_avatar"] = get_display_avatar(user_doc)
        user_doc["display_name"] = get_display_name(user_doc)
    return user_doc

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
    
    # Check if this is the founder
    is_founder = check_is_founder(req.email)
    
    # Generate unique avatar for new user
    default_avatar = generate_avatar_url(req.name, user_id)
    
    await db.users.insert_one({
        "user_id": user_id,
        "email": req.email,
        "name": req.name,
        "username": "Motesart" if is_founder else None,
        "avatar_url": MOTESART_FOUNDER_AVATAR if is_founder else default_avatar,
        "is_founder": is_founder,
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
    # Add computed fields
    user_doc["computed_avatar"] = get_display_avatar(user_doc)
    user_doc["display_name"] = get_display_name(user_doc)
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
    # Add computed fields
    user_doc["computed_avatar"] = get_display_avatar(user_doc)
    user_doc["display_name"] = get_display_name(user_doc)
    return user_doc

@api_router.put("/auth/profile")
async def update_profile(req: UpdateProfileRequest, user: User = Depends(get_current_user)):
    """Update user profile (username, name)"""
    update_data = {}
    
    if req.username is not None:
        # Prevent non-founders from using "Motesart" username
        if req.username.lower() == "motesart" and not user.is_founder:
            raise HTTPException(status_code=400, detail="This username is reserved")
        update_data["username"] = req.username
    
    if req.name is not None:
        update_data["name"] = req.name
    
    if update_data:
        await db.users.update_one(
            {"user_id": user.user_id},
            {"$set": update_data}
        )
    
    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0, "password_hash": 0})
    user_doc["computed_avatar"] = get_display_avatar(user_doc)
    user_doc["display_name"] = get_display_name(user_doc)
    return user_doc

@api_router.post("/auth/avatar")
async def upload_avatar(file: UploadFile = File(...), user: User = Depends(get_current_user)):
    """Upload a custom avatar image"""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:  # 5MB limit
        raise HTTPException(status_code=400, detail="Image must be less than 5MB")
    
    import base64
    # Store as base64 data URL for simplicity
    # In production, you'd upload to S3/cloud storage
    extension = file.filename.split(".")[-1].lower() if file.filename else "png"
    content_type = f"image/{extension}" if extension in ["png", "jpg", "jpeg", "gif", "webp"] else "image/png"
    avatar_data_url = f"data:{content_type};base64,{base64.b64encode(content).decode()}"
    
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$set": {"avatar_url": avatar_data_url}}
    )
    
    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0, "password_hash": 0})
    user_doc["computed_avatar"] = get_display_avatar(user_doc)
    user_doc["display_name"] = get_display_name(user_doc)
    return user_doc

@api_router.delete("/auth/avatar")
async def delete_avatar(user: User = Depends(get_current_user)):
    """Remove custom avatar and revert to default"""
    # Generate a new default avatar
    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    default_avatar = generate_avatar_url(user_doc.get("name", "User"), user.user_id)
    
    # Don't allow founder to delete their special avatar
    if user.is_founder:
        default_avatar = MOTESART_FOUNDER_AVATAR
    
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$set": {"avatar_url": default_avatar}}
    )
    
    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0, "password_hash": 0})
    user_doc["computed_avatar"] = get_display_avatar(user_doc)
    user_doc["display_name"] = get_display_name(user_doc)
    return user_doc

# ==================== MOTESART CONVERSION LOGIC ====================

# Scale degree mapping (semitones from root)
MAJOR_SCALE_SEMITONES = [0, 2, 4, 5, 7, 9, 11]  # 1, 2, 3, 4, 5, 6, 7
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
FLAT_NAMES = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']

# All key names for auto-detect and selection
ALL_KEYS = ['C', 'C#', 'Db', 'D', 'D#', 'Eb', 'E', 'F', 'F#', 'Gb', 'G', 'G#', 'Ab', 'A', 'A#', 'Bb', 'B']

# Chord symbol to root mapping (for chord chart parsing)
CHORD_ROOT_MAP = {
    'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'Fb': 4,
    'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 
    'Bb': 10, 'B': 11, 'Cb': 11
}

# Diatonic chord qualities in major key (by scale degree)
# 1=major, 2=minor, 3=minor, 4=major, 5=major, 6=minor, 7=diminished
DIATONIC_QUALITIES = {
    1: 'major', 2: 'minor', 3: 'minor', 4: 'major', 
    5: 'major', 6: 'minor', 7: 'diminished'
}

# Rule §3: Half-numbers - ONLY these are valid (no 3½ or 7½)
# Semitone offsets 1,3,6,8,10 map to degrees 1,2,4,5,6 with ½ symbol
HALF_NUMBER_MAP = {
    1: "1½",   # Between 1 and 2 (C# in key of C)
    3: "2½",   # Between 2 and 3 (D# in key of C)
    6: "4½",   # Between 4 and 5 (F# in key of C)
    8: "5½",   # Between 5 and 6 (G# in key of C)
    10: "6½",  # Between 6 and 7 (A# in key of C)
}

def get_note_number(pitch: int, key_root: int) -> str:
    """
    Convert MIDI pitch to Motesart number relative to key.
    Rule §3: Only valid half-numbers are 1½, 2½, 4½, 5½, 6½ (never 3½ or 7½)
    """
    semitones_from_root = (pitch - key_root) % 12
    
    # Check if it's a scale degree
    if semitones_from_root in MAJOR_SCALE_SEMITONES:
        return str(MAJOR_SCALE_SEMITONES.index(semitones_from_root) + 1)
    
    # Half-numbers for chromatic tones (Rule §3)
    return HALF_NUMBER_MAP.get(semitones_from_root, f"?{semitones_from_root}")

def semitone_to_degree(semitones: int) -> tuple:
    """
    Convert semitones from root to scale degree using ONLY half-numbers.
    The Motesart Number System NEVER uses sharp (♯) or flat (♭) symbols.
    
    Valid half-numbers: 1½, 2½, 4½, 5½, 6½
    NEVER 3½ or 7½ (these are natural half-steps)
    
    Returns (base_degree, is_chromatic, display_symbol)
    """
    semitones = semitones % 12
    
    # Check if it's a diatonic scale degree
    if semitones in MAJOR_SCALE_SEMITONES:
        degree = MAJOR_SCALE_SEMITONES.index(semitones) + 1
        return (degree, False, str(degree))
    
    # Chromatic notes use half-numbers ONLY - no flats or sharps
    # Map: semitone -> (base_degree, display)
    half_number_map = {
        1: (1, "1½"),   # Between 1 and 2
        3: (2, "2½"),   # Between 2 and 3
        6: (4, "4½"),   # Between 4 and 5
        8: (5, "5½"),   # Between 5 and 6
        10: (6, "6½"),  # Between 6 and 7
    }
    
    if semitones in half_number_map:
        base_degree, symbol = half_number_map[semitones]
        return (base_degree, True, symbol)
    
    # Fallback (should never reach in 12-tone system)
    return (1, True, "?")

def semitone_to_melodic_number(semitones: int) -> str:
    """
    Convert semitones from root to Motesart melodic number.
    Rule §3: Only valid half-numbers are 1½, 2½, 4½, 5½, 6½ (never 3½ or 7½)
    
    The Motesart Number System NEVER uses sharp (♯) or flat (♭) symbols.
    """
    semitones = semitones % 12
    
    # Check if it's a diatonic scale degree
    if semitones in MAJOR_SCALE_SEMITONES:
        return str(MAJOR_SCALE_SEMITONES.index(semitones) + 1)
    
    # Half-numbers for chromatic tones (Rule §3)
    return HALF_NUMBER_MAP.get(semitones, "?")

def is_diatonic_chord(root_semitones: int, quality: str, key_root: int) -> bool:
    """
    Rule §6: Check if a chord is diatonic to the key.
    Used to determine if we need 'M' marker for major chords.
    """
    semitones_from_key = (root_semitones - key_root) % 12
    
    # Get the scale degree
    if semitones_from_key not in MAJOR_SCALE_SEMITONES:
        return False  # Root is chromatic, so chord is non-diatonic
    
    degree = MAJOR_SCALE_SEMITONES.index(semitones_from_key) + 1
    expected_quality = DIATONIC_QUALITIES.get(degree)
    
    # Normalize quality for comparison
    quality_lower = quality.lower()
    if quality_lower in ['m', 'min', 'minor', '-']:
        actual = 'minor'
    elif quality_lower in ['dim', 'o', '°', 'diminished']:
        actual = 'diminished'
    elif quality_lower in ['aug', '+', '⁺', 'augmented']:
        actual = 'augmented'
    else:
        actual = 'major'
    
    return actual == expected_quality

def parse_chord_symbol(chord_str: str, key_root: int) -> Dict:
    """
    Parse a chord symbol (like "Am7", "G/B", "Cmaj7") into Motesart notation.
    
    Rule §6: Chord Quality Inference
    - Minor chords: ALWAYS mark with 'm' (e.g., Am → 6m, Em → 3m)
    - Diminished chords: ALWAYS mark with '°'
    - Major chords: Add 'M' ONLY if non-diatonic
    - Diatonic major chords: no modifier
    
    Rule §7: Inversions - bass/chord format
    - G/B in key of G → 3/1 (bass first, chord second)
    
    Rule §4c: Extensions with superscripts
    - 7→⁷, 9→⁹, 11→¹¹, 13→¹³
    """
    if not chord_str or chord_str.strip() == '':
        return None
    
    chord_str = chord_str.strip()
    original_chord = chord_str
    
    # Handle slash chords - Rule §7: chord/bass format
    bass_note = None
    if '/' in chord_str:
        parts = chord_str.split('/')
        chord_str = parts[0]
        bass_note = parts[1] if len(parts) > 1 else None
    
    # Extract root note
    root_match = re.match(r'^([A-G][#b]?)', chord_str)
    if not root_match:
        return None
    
    root_name = root_match.group(1)
    root_semitone = CHORD_ROOT_MAP.get(root_name, 0)
    quality_str = chord_str[len(root_name):]
    original_quality = quality_str
    
    # Check if this is a "plain note" (no explicit quality modifiers)
    # Plain notes (like "C", "F#", "Bb") should just show the number without quality inference
    is_plain_note = quality_str.strip() == "" and bass_note is None
    
    # Check if this is an EXPLICIT major chord (like "Cmaj", "GM", "Amaj")
    # These should get 'M' marker if non-diatonic, unlike plain notes
    is_explicit_major = False
    
    # Determine the actual chord quality from input
    is_minor = False
    is_diminished = False
    is_augmented = False
    is_sus2 = False
    is_sus4 = False
    has_7 = False
    has_maj7 = False
    has_9 = False
    has_11 = False
    has_13 = False
    
    # Check for explicit major FIRST (before minor check, since 'maj' starts with 'm')
    if quality_str.lower().startswith('maj') and not quality_str.lower().startswith('maj7'):
        is_explicit_major = True
        quality_str = re.sub(r'^maj', '', quality_str, flags=re.IGNORECASE)
    elif quality_str == 'M' or quality_str.startswith('M') and not quality_str.startswith('M7'):
        is_explicit_major = True
        if quality_str == 'M':
            quality_str = ''
        elif quality_str.startswith('M'):
            quality_str = quality_str[1:]
    
    # Check for minor (after explicit major check)
    if quality_str.startswith('m') and not quality_str.startswith('maj'):
        is_minor = True
        quality_str = quality_str[1:]
    elif quality_str.startswith('min'):
        is_minor = True
        quality_str = quality_str[3:]
    elif quality_str.startswith('-'):
        is_minor = True
        quality_str = quality_str[1:]
    
    # Check for diminished
    if 'dim' in quality_str.lower() or '°' in quality_str or quality_str.lower() == 'o':
        is_diminished = True
        quality_str = re.sub(r'dim|°|o', '', quality_str, flags=re.IGNORECASE)
    
    # Check for augmented
    if 'aug' in quality_str.lower() or '+' in quality_str or '⁺' in quality_str:
        is_augmented = True
        quality_str = re.sub(r'aug|\+|⁺', '', quality_str, flags=re.IGNORECASE)
    
    # Check for suspended
    if 'sus2' in quality_str.lower():
        is_sus2 = True
        quality_str = re.sub(r'sus2', '', quality_str, flags=re.IGNORECASE)
    elif 'sus4' in quality_str.lower() or 'sus' in quality_str.lower():
        is_sus4 = True
        quality_str = re.sub(r'sus4?', '', quality_str, flags=re.IGNORECASE)
    
    # Check for 7th variations - order matters!
    if 'maj7' in quality_str.lower() or 'M7' in quality_str or 'Δ7' in quality_str or 'Δ' in quality_str:
        has_maj7 = True
        quality_str = re.sub(r'maj7|M7|Δ7|Δ', '', quality_str, flags=re.IGNORECASE)
    elif '7' in quality_str:
        has_7 = True
        quality_str = quality_str.replace('7', '')
    
    # Check for extensions
    if '13' in quality_str:
        has_13 = True
        quality_str = quality_str.replace('13', '')
    if '11' in quality_str:
        has_11 = True
        quality_str = quality_str.replace('11', '')
    if '9' in quality_str:
        has_9 = True
        quality_str = quality_str.replace('9', '')
    
    # Convert root to Motesart number
    root_degree, root_chromatic, root_number = semitone_to_degree(root_semitone - key_root)
    
    # Determine the quality string for Motesart notation
    # Rule §6: Quality Inference - UPDATED INTERPRETATION
    # - Plain notes (just root, no quality): NO quality marker (e.g., "D" → "2", not "2M")
    # - Explicit major (e.g., "Gmaj", "AM"): Gets 'M' if non-diatonic
    # - Diatonic chords: NO quality marker (even for minor/diminished)
    # - Non-diatonic chords: show quality marker (m, M, °, ⁺, etc.)
    # - Half-number roots: already indicate non-diatonic, add quality only if explicit
    
    quality_symbol = ""
    
    # If it's a plain note (no explicit quality), just use the root number
    if is_plain_note:
        # No quality marker for plain notes - just the number
        pass
    else:
        # Check if the chord is diatonic (root on diatonic scale degree with expected quality)
        actual_quality = 'major'
        if is_minor:
            actual_quality = 'minor'
        elif is_diminished:
            actual_quality = 'diminished'
        elif is_augmented:
            actual_quality = 'augmented'
        elif is_sus2 or is_sus4:
            actual_quality = 'suspended'
        
        # Diatonic check
        is_chord_diatonic = False
        if not root_chromatic:  # Only check for diatonic scale degrees
            is_chord_diatonic = is_diatonic_chord(root_semitone, actual_quality, key_root)
        
        # Apply quality markers based on chord type
        # Rule §6: Quality Inference - CORRECTED
        # - Minor chords: ALWAYS mark with 'm' (diatonic or not)
        # - Diminished: ALWAYS mark with '°'
        # - Augmented: ALWAYS mark with '⁺'
        # - Major chords: Add 'M' ONLY if non-diatonic (not on half-number root)
        # - Diatonic major chords: no modifier
        
        if is_minor:
            # ALL minor chords get 'm' marker - ALWAYS
            quality_symbol = "m"
        elif is_diminished:
            quality_symbol = "°"  # Always show diminished marker
        elif is_augmented:
            quality_symbol = "⁺"  # Augmented is never diatonic
        elif is_sus2:
            quality_symbol = "sus²"  # Suspended chords always marked
        elif is_sus4:
            quality_symbol = "sus⁴"  # Suspended chords always marked
        elif is_explicit_major:
            # Explicit major (e.g., "Gmaj", "AM") - show 'M' if non-diatonic
            if root_chromatic:
                quality_symbol = ""  # Half-number already shows non-diatonic
            elif not is_chord_diatonic:
                quality_symbol = "M"
        else:
            # Implied major chord (e.g., just "G" with other context)
            # Diatonic major: no marker; Non-diatonic major: 'M'
            if root_chromatic:
                quality_symbol = ""  # Half-number already shows non-diatonic
            elif not is_chord_diatonic:
                quality_symbol = "M"
    
    # Build extension string with superscripts (Rule §4c)
    extension_str = ""
    if has_maj7:
        if is_minor:
            extension_str = "M⁷"  # mM7 chord
        else:
            extension_str = "M⁷"
    elif has_7:
        if is_minor:
            quality_symbol = "m"  # Already set, but be explicit
            extension_str = "⁷"
        elif is_diminished:
            extension_str = "⁷"  # dim7
        else:
            extension_str = "⁷"  # dominant 7
    
    if has_9:
        extension_str += "⁹"
    if has_11:
        extension_str += "¹¹"
    if has_13:
        extension_str += "¹³"
    
    # Build the final symbol
    symbol = root_number + quality_symbol + extension_str
    
    # Handle slash bass note - Rule §7: bass/chord format
    bass_number = None
    if bass_note:
        bass_match = re.match(r'^([A-G][#b]?)', bass_note)
        if bass_match:
            bass_root = bass_match.group(1)
            bass_semitone = CHORD_ROOT_MAP.get(bass_root, 0)
            _, _, bass_number = semitone_to_degree(bass_semitone - key_root)
            # Rule §7: Format as bass/chord (e.g., G/B in key of G → 3/1)
            # Bass note comes first, then the chord
            symbol = f"{bass_number}/{symbol}"
    
    return {
        "original": original_chord,
        "symbol": symbol,
        "root": root_number,
        "quality": quality_symbol,
        "bass": bass_number,
        "extensions": extension_str,
        "is_minor": is_minor,
        "is_diminished": is_diminished,
        "is_augmented": is_augmented,
        "is_diatonic": is_diatonic_chord(root_semitone, 'minor' if is_minor else 'major', key_root)
    }

def auto_detect_key(chords: List[str]) -> tuple:
    """
    Auto-detect the key from a list of chord symbols.
    Returns (key_root, key_name)
    """
    if not chords:
        return (0, "C")
    
    # Count chord roots
    root_counts = {}
    minor_counts = {}
    
    for chord in chords:
        root_match = re.match(r'^([A-G][#b]?)', chord)
        if root_match:
            root = root_match.group(1)
            root_counts[root] = root_counts.get(root, 0) + 1
            
            # Check if minor
            rest = chord[len(root):]
            if rest.startswith('m') and not rest.startswith('maj'):
                minor_counts[root] = minor_counts.get(root, 0) + 1
    
    if not root_counts:
        return (0, "C")
    
    # Most common root is likely the key (especially if major)
    # Give preference to major chords that appear frequently
    best_key = None
    best_score = -1
    
    for root, count in root_counts.items():
        # Major chords get higher weight for key detection
        minor_count = minor_counts.get(root, 0)
        major_count = count - minor_count
        score = major_count * 2 + minor_count
        
        if score > best_score:
            best_score = score
            best_key = root
    
    if best_key:
        key_root = CHORD_ROOT_MAP.get(best_key, 0)
        return (key_root, best_key)
    
    return (0, "C")

def convert_chord_chart_text(text: str, key_override: str = None) -> Dict:
    """
    Convert a chord chart text to Motesart notation.
    
    Supports three input formats:
    1. Chords-over-lyrics (Ultimate Guitar style)
    2. Inline chords [G] within lyrics
    3. Plain chord sequences (G Am C D)
    
    Half-numbers (1½, 2½, 4½, 5½, 6½) are ALWAYS used for chromatic notes.
    The Motesart Number System NEVER uses sharp (♯) or flat (♭) symbols.
    
    Returns structured data with sections, converted chords, and metadata.
    """
    if not text or not text.strip():
        return {"error": "No input text provided", "sections": [], "chords": []}
    
    lines = text.strip().split('\n')
    
    # First pass: extract all chords to detect key
    # Note: Don't use \b at end because #/b are not word characters
    # Order matters: 'maj7' before 'maj' before 'm', '13' before '11' before '1', etc.
    # Use negative lookbehind to avoid matching chords within words
    chord_pattern = re.compile(r'(?<![a-z])([A-G][#b]?(?:maj7|maj|min|m|M7|M|dim|aug|sus[24]?|add|13|11|9|7)*(?:/[A-G][#b]?)?)(?![a-z])', re.IGNORECASE)
    all_chords_raw = chord_pattern.findall(text)
    
    # Detect or use override key
    if key_override and key_override in CHORD_ROOT_MAP:
        key_root = CHORD_ROOT_MAP[key_override]
        key_name = key_override
    else:
        key_root, key_name = auto_detect_key(all_chords_raw)
    
    # Section headers pattern
    section_pattern = re.compile(
        r'^\s*\[?\s*(Intro|Verse|Pre[\-\s]?Chorus|Chorus|Bridge|Interlude|Refrain|Outro|Tag|Vamp|Hook|Instrumental|Solo|Ending|Coda)\s*\d*\s*\]?\s*:?\s*$',
        re.IGNORECASE
    )
    
    sections = []
    current_section = {"name": "Intro", "lines": [], "chords": []}
    all_converted_chords = []
    chord_count = 0
    
    for line in lines:
        original_line = line
        line_stripped = line.strip()
        
        if not line_stripped:
            continue
        
        # Check for section header
        section_match = section_pattern.match(line_stripped)
        if section_match:
            # Save previous section if it has content
            if current_section["chords"] or current_section["lines"]:
                sections.append(current_section)
            
            current_section = {
                "name": section_match.group(1).strip().title(),
                "lines": [],
                "chords": []
            }
            continue
        
        # Check for key/tempo/time metadata
        key_match = re.match(r'^Key:\s*([A-G][#b]?)', line_stripped, re.IGNORECASE)
        if key_match and not key_override:
            key_name = key_match.group(1)
            key_root = CHORD_ROOT_MAP.get(key_name, 0)
            continue
        
        if re.match(r'^(Tempo|Time|BPM):', line_stripped, re.IGNORECASE):
            continue
        
        # Process chords in the line
        line_chords = []
        chord_positions = []  # Store (start, end, parsed) tuples
        
        # Find all chord positions and convert them
        for match in chord_pattern.finditer(line_stripped):
            chord_str = match.group(1)
            parsed = parse_chord_symbol(chord_str, key_root)
            if parsed:
                line_chords.append(parsed)
                all_converted_chords.append(parsed)
                chord_count += 1
                chord_positions.append((match.start(), match.end(), parsed))
        
        # Build the converted line with Motesart symbols
        if line_chords:
            # Replace chords by position (in reverse order to preserve indices)
            result_chars = list(line_stripped)
            for start, end, parsed in reversed(chord_positions):
                symbol = parsed["symbol"]
                # Replace characters from start to end with the symbol
                result_chars[start:end] = list(symbol)
            result_line = ''.join(result_chars)
            
            current_section["lines"].append({
                "original": line_stripped,
                "converted": result_line,
                "chords": line_chords,
                "type": "chord_line"
            })
            current_section["chords"].extend(line_chords)
        else:
            # Line without chords (lyrics or other text)
            current_section["lines"].append({
                "original": line_stripped,
                "converted": line_stripped,
                "chords": [],
                "type": "lyric_line" if len(line_stripped) > 3 else "empty"
            })
    
    # Add the last section
    if current_section["chords"] or current_section["lines"]:
        sections.append(current_section)
    
    # Build progressions for each section
    for section in sections:
        if section["chords"]:
            # Get unique chord symbols in order (up to 8)
            seen = []
            for c in section["chords"]:
                if c["symbol"] not in seen:
                    seen.append(c["symbol"])
            section["progression"] = " - ".join(seen[:8])
        else:
            section["progression"] = ""
    
    return {
        "key": f"1 = {key_name}",
        "key_name": key_name,
        "key_root": key_root,
        "chord_count": chord_count,
        "sections": sections,
        "all_chords": all_converted_chords
    }

class ChordChartConvertRequest(BaseModel):
    text: str
    key: Optional[str] = None
    time_signature: Optional[str] = "4/4"

@api_router.post("/convert/text")
async def convert_chord_chart(req: ChordChartConvertRequest, user: User = Depends(get_current_user)):
    """
    Convert a chord chart text to Motesart notation.
    
    Half-numbers (1½, 2½, 4½, 5½, 6½) are ALWAYS used for chromatic notes.
    The Motesart Number System NEVER uses sharp or flat symbols.
    
    Supports:
    - Chords-over-lyrics format
    - Inline [chord] format
    - Plain chord sequences
    """
    result = convert_chord_chart_text(
        req.text,
        key_override=req.key if req.key and req.key != "auto" else None
    )
    
    return result

@api_router.get("/keys")
async def get_available_keys():
    """Get list of available keys for the converter"""
    return {
        "keys": [
            {"value": "auto", "label": "Auto-detect"},
            {"value": "C", "label": "C"},
            {"value": "C#", "label": "C# / Db"},
            {"value": "D", "label": "D"},
            {"value": "Eb", "label": "Eb / D#"},
            {"value": "E", "label": "E"},
            {"value": "F", "label": "F"},
            {"value": "F#", "label": "F# / Gb"},
            {"value": "G", "label": "G"},
            {"value": "Ab", "label": "Ab / G#"},
            {"value": "A", "label": "A"},
            {"value": "Bb", "label": "Bb / A#"},
            {"value": "B", "label": "B"},
        ]
    }

def parse_chord_chart_text(text: str) -> Dict:
    """
    Parse chord chart text (like from Send Me chord chart) into structured data.
    Detects sections (Intro, Verse, Chorus, Bridge) and chord progressions.
    """
    lines = text.strip().split('\n')
    
    sections = []
    current_section = None
    chords_in_section = []
    
    # Detect key from first line or chord chart header
    key_match = re.search(r'Key:\s*([A-G][#b]?)', text, re.IGNORECASE)
    key_name = key_match.group(1) if key_match else "C"
    key_root = CHORD_ROOT_MAP.get(key_name, 0)
    
    # Detect tempo
    tempo_match = re.search(r'Tempo:\s*(\d+)', text, re.IGNORECASE)
    tempo = int(tempo_match.group(1)) if tempo_match else 120
    
    # Detect time signature
    time_match = re.search(r'Time:\s*(\d+/\d+)', text, re.IGNORECASE)
    time_sig = time_match.group(1) if time_match else "4/4"
    
    # Detect title
    title_match = re.search(r'Title:\s*(.+)', text, re.IGNORECASE)
    title = title_match.group(1).strip() if title_match else None
    
    # Section headers to detect
    section_patterns = [
        r'\*\*?(Intro|Verse|Pre\s*Chorus|Chorus|Bridge|Interlude|Refrain|Outro|Tag|Vamp)\s*\d*\*?\*?',
        r'^(Intro|Verse|Pre\s*Chorus|Chorus|Bridge|Interlude|Refrain|Outro|Tag|Vamp)\s*\d*\s*$'
    ]
    
    # Chord pattern (matches most chord symbols)
    chord_pattern = re.compile(r'\b([A-G][#b]?(?:m|min|maj|M|dim|aug|sus[24]?|add)?[2-9]?(?:/[A-G][#b]?)?)\b')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check for section header
        section_found = False
        for pattern in section_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                # Save previous section
                if current_section and chords_in_section:
                    sections.append({
                        "name": current_section,
                        "chords": chords_in_section,
                        "progression": "-".join([c["symbol"] for c in chords_in_section[:8]])
                    })
                
                current_section = match.group(1).strip()
                chords_in_section = []
                section_found = True
                break
        
        if section_found:
            continue
        
        # Extract chords from line
        chord_matches = chord_pattern.findall(line)
        for chord_str in chord_matches:
            parsed = parse_chord_symbol(chord_str, key_root)
            if parsed:
                chords_in_section.append(parsed)
    
    # Save last section
    if current_section and chords_in_section:
        sections.append({
            "name": current_section,
            "chords": chords_in_section,
            "progression": "-".join([c["symbol"] for c in chords_in_section[:8]])
        })
    
    # If no sections found, create one from all chords
    if not sections:
        all_chords = []
        for match in chord_pattern.findall(text):
            parsed = parse_chord_symbol(match, key_root)
            if parsed:
                all_chords.append(parsed)
        if all_chords:
            sections.append({
                "name": "Main",
                "chords": all_chords,
                "progression": "-".join([c["symbol"] for c in all_chords[:8]])
            })
    
    return {
        "title": title,
        "key_signature": f"1 = {key_name}",
        "key_root": key_root,
        "key_name": key_name,
        "tempo": tempo,
        "time_signature": time_sig,
        "sections": sections,
        "content_type": "chord_chart"
    }

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

def detect_key_from_chords(chords: List[str]) -> tuple:
    """Detect key from a list of chord symbols"""
    if not chords:
        return 0, "C"
    
    # Count chord roots
    root_counts = {}
    for chord in chords:
        root_match = re.match(r'^([A-G][#b]?)', chord)
        if root_match:
            root = root_match.group(1)
            root_counts[root] = root_counts.get(root, 0) + 1
    
    # Most common root is likely the key (or its relative)
    if root_counts:
        key_name = max(root_counts, key=root_counts.get)
        key_root = CHORD_ROOT_MAP.get(key_name, 0)
        return key_root, key_name
    
    return 0, "C"

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
SUPPORTED_SHEET_MUSIC = ["pdf", "png", "jpg", "jpeg", "heic", "heif"]
ALL_SUPPORTED = SUPPORTED_MUSIC_FILES + SUPPORTED_SHEET_MUSIC

async def convert_heic_to_png(content: bytes) -> bytes:
    """Convert HEIC/HEIF image to PNG format"""
    try:
        from PIL import Image
        from pillow_heif import register_heif_opener
        register_heif_opener()
        
        img = Image.open(io.BytesIO(content))
        output = io.BytesIO()
        img.convert('RGB').save(output, format='PNG')
        output.seek(0)
        return output.read()
    except ImportError:
        logger.warning("pillow-heif not installed, storing HEIC as-is")
        return content
    except Exception as e:
        logger.error(f"HEIC conversion error: {e}")
        return content

async def extract_text_from_image(content: bytes, filename: str) -> dict:
    """
    Extract text/chords from sheet music images using OCR.
    Returns detected chords, key, and sections.
    """
    try:
        # Try using Google Cloud Vision or pytesseract for OCR
        import pytesseract
        from PIL import Image
        
        img = Image.open(io.BytesIO(content))
        text = pytesseract.image_to_string(img)
        
        if text.strip():
            # Parse the extracted text for chord symbols
            chord_pattern = re.compile(r'(?<![a-z])([A-G][#b]?(?:maj7|maj|min|m|M7|M|dim|aug|sus[24]?|add|13|11|9|7)*(?:/[A-G][#b]?)?)(?![a-z])', re.IGNORECASE)
            chords_raw = chord_pattern.findall(text)
            
            if chords_raw:
                # Detect key from chords
                key_root, key_name = auto_detect_key(chords_raw)
                
                # Parse chords into Motesart notation
                parsed_chords = []
                for chord in chords_raw:
                    parsed = parse_chord_symbol(chord, key_root)
                    if parsed:
                        parsed_chords.append(parsed)
                
                return {
                    "success": True,
                    "method": "ocr",
                    "raw_text": text[:500],
                    "key_signature": f"1 = {key_name}",
                    "key_root": key_root,
                    "key_name": key_name,
                    "chords": parsed_chords,
                    "sections": [{
                        "name": "Main",
                        "chords": parsed_chords,
                        "progression": " - ".join([c["symbol"] for c in parsed_chords[:8]])
                    }]
                }
        
        return {"success": False, "error": "No chords detected in image"}
        
    except ImportError:
        return {"success": False, "error": "OCR not available - pytesseract not installed"}
    except Exception as e:
        logger.error(f"Image OCR error: {e}")
        return {"success": False, "error": str(e)}

async def extract_text_from_pdf(content: bytes, filename: str) -> dict:
    """
    Extract text/chords from PDF files.
    Tries text extraction first, then falls back to OCR on images.
    """
    try:
        import fitz  # PyMuPDF
        
        doc = fitz.open(stream=content, filetype="pdf")
        full_text = ""
        
        for page in doc:
            full_text += page.get_text()
        
        if full_text.strip():
            # Parse the extracted text for chord symbols
            chord_pattern = re.compile(r'(?<![a-z])([A-G][#b]?(?:maj7|maj|min|m|M7|M|dim|aug|sus[24]?|add|13|11|9|7)*(?:/[A-G][#b]?)?)(?![a-z])', re.IGNORECASE)
            chords_raw = chord_pattern.findall(full_text)
            
            if chords_raw:
                # Detect key from chords
                key_root, key_name = auto_detect_key(chords_raw)
                
                # Parse chords into Motesart notation
                parsed_chords = []
                for chord in chords_raw:
                    parsed = parse_chord_symbol(chord, key_root)
                    if parsed:
                        parsed_chords.append(parsed)
                
                return {
                    "success": True,
                    "method": "pdf_text",
                    "raw_text": full_text[:500],
                    "key_signature": f"1 = {key_name}",
                    "key_root": key_root,
                    "key_name": key_name,
                    "chords": parsed_chords,
                    "sections": [{
                        "name": "Main",
                        "chords": parsed_chords,
                        "progression": " - ".join([c["symbol"] for c in parsed_chords[:8]])
                    }]
                }
        
        # If no text found, try OCR on first page
        if doc.page_count > 0:
            page = doc[0]
            pix = page.get_pixmap()
            img_data = pix.tobytes()
            return await extract_text_from_image(img_data, filename)
        
        return {"success": False, "error": "No chords detected in PDF"}
        
    except ImportError:
        return {"success": False, "error": "PDF extraction not available - PyMuPDF not installed"}
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        return {"success": False, "error": str(e)}

@api_router.post("/upload")
async def upload_file(file: UploadFile = File(...), user: User = Depends(get_current_user)):
    """
    Upload and convert a music file.
    
    Sheet-music first approach:
    - Primary: PDF, PNG, JPG, HEIC (sheet music images)
    - Secondary: MusicXML, MIDI (digital music files)
    
    For PDF/images: attempts OCR extraction, stores file for later OMR if needed
    For MIDI/MusicXML: immediate conversion to Motesart numbers
    """
    filename = file.filename or "unknown"
    extension = filename.split(".")[-1].lower()
    
    if extension not in ALL_SUPPORTED:
        raise HTTPException(
            status_code=400, 
            detail="Unsupported file type. Please upload sheet music (PDF, PNG, JPG, HEIC) or music files (MusicXML, MIDI)."
        )
    
    content = await file.read()
    original_file_size = len(content)
    
    # Convert HEIC to PNG if needed
    original_extension = extension
    if extension in ["heic", "heif"]:
        content = await convert_heic_to_png(content)
        extension = "png"  # Treat as PNG after conversion
    
    # Get actual file size after any conversion
    file_size = len(content)
    
    conversion_id = f"conv_{uuid.uuid4().hex[:12]}"
    
    # Determine file category
    is_sheet_music = original_extension in SUPPORTED_SHEET_MUSIC
    initial_status = "processing"
    
    # Save initial conversion record
    conversion_doc = {
        "conversion_id": conversion_id,
        "user_id": user.user_id,
        "filename": filename,
        "file_type": original_extension,
        "file_size": file_size,
        "is_sheet_music": is_sheet_music,
        "status": initial_status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Store file content - for large files, save to disk instead of MongoDB
    import base64
    UPLOAD_DIR = Path("/app/uploads")
    UPLOAD_DIR.mkdir(exist_ok=True)
    
    # Save file to disk
    file_path = UPLOAD_DIR / f"{conversion_id}.{extension}"
    with open(file_path, 'wb') as f:
        f.write(content)
    conversion_doc["file_path"] = str(file_path)
    
    # Only store small files (<10MB) in MongoDB for quick access
    if file_size < 10 * 1024 * 1024:
        conversion_doc["file_data"] = base64.b64encode(content).decode('utf-8')
    
    await db.conversions.insert_one(conversion_doc)
    
    # Process the file
    try:
        if is_sheet_music:
            # Try to extract chords from PDF/images
            if original_extension == "pdf":
                extraction_result = await extract_text_from_pdf(content, filename)
            else:
                extraction_result = await extract_text_from_image(content, filename)
            
            if extraction_result.get("success"):
                # Successfully extracted chords
                await db.conversions.update_one(
                    {"conversion_id": conversion_id},
                    {"$set": {
                        "status": "completed",
                        "key_signature": extraction_result["key_signature"],
                        "key_name": extraction_result.get("key_name", "C"),
                        "key_root": extraction_result.get("key_root", 0),
                        "chords": extraction_result["chords"],
                        "sections": extraction_result["sections"],
                        "content_type": "chord_chart",
                        "time_signature": "4/4",
                        "tempo": 120,
                        "extraction_method": extraction_result.get("method", "ocr"),
                        "raw_text": extraction_result.get("raw_text", ""),
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
            else:
                # Could not extract chords - mark as uploaded for manual/Phase 2 OMR
                await db.conversions.update_one(
                    {"conversion_id": conversion_id},
                    {"$set": {
                        "status": "uploaded",
                        "status_message": extraction_result.get("error", "Could not detect chords. Try the Text Converter for manual input."),
                        "key_signature": "1 = C",
                        "time_signature": "4/4",
                        "tempo": 120,
                        "chords": [],
                        "sections": [],
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
        else:
            # For MIDI/MusicXML, process immediately
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
    
    import base64
    file_data = None
    
    # Try to get file from disk first (for large files)
    if conversion.get("file_path") and os.path.exists(conversion["file_path"]):
        with open(conversion["file_path"], 'rb') as f:
            file_data = f.read()
    # Fall back to base64-encoded data in DB
    elif conversion.get("file_data"):
        file_data = base64.b64decode(conversion["file_data"])
    
    if not file_data:
        raise HTTPException(status_code=404, detail="No file data available")
    
    file_type = conversion.get("file_type", "pdf")
    
    media_types = {
        "pdf": "application/pdf",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "heic": "image/heic",
        "webp": "image/webp"
    }
    
    return StreamingResponse(
        io.BytesIO(file_data),
        media_type=media_types.get(file_type, "application/octet-stream"),
        headers={"Content-Disposition": f"inline; filename={conversion.get('filename', 'file')}"}
    )
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
        {"_id": 0, "file_data": 0}
    )
    if not conversion:
        raise HTTPException(status_code=404, detail="Conversion not found")
    return conversion

class ManualConversionUpdate(BaseModel):
    key_signature: str
    key_name: str
    chords: List[Dict] = []
    sections: List[Dict] = []

@api_router.put("/conversions/{conversion_id}/manual")
async def update_conversion_manual(
    conversion_id: str,
    update: ManualConversionUpdate,
    user: User = Depends(get_current_user)
):
    """Update a conversion with manually entered chord data"""
    conversion = await db.conversions.find_one(
        {"conversion_id": conversion_id, "user_id": user.user_id},
        {"_id": 0}
    )
    if not conversion:
        raise HTTPException(status_code=404, detail="Conversion not found")
    
    await db.conversions.update_one(
        {"conversion_id": conversion_id},
        {"$set": {
            "status": "completed",
            "key_signature": update.key_signature,
            "key_name": update.key_name,
            "chords": update.chords,
            "sections": update.sections,
            "manual_entry": True,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    updated = await db.conversions.find_one(
        {"conversion_id": conversion_id},
        {"_id": 0, "file_data": 0}
    )
    return updated


class OMRProcessRequest(BaseModel):
    key_override: Optional[str] = None


@api_router.post("/conversions/{conversion_id}/omr")
async def process_conversion_omr(
    conversion_id: str,
    request: OMRProcessRequest = None,
    user: User = Depends(get_current_user)
):
    """
    Process a conversion with full OMR (Optical Music Recognition).
    Extracts individual notes from sheet music images/PDFs.
    
    Uses oemer for image-based OMR and music21 for parsing.
    """
    conversion = await db.conversions.find_one(
        {"conversion_id": conversion_id, "user_id": user.user_id},
        {"_id": 0}
    )
    if not conversion:
        raise HTTPException(status_code=404, detail="Conversion not found")
    
    # Check for file data - either in MongoDB or on disk
    has_file = conversion.get("file_data") or (
        conversion.get("file_path") and os.path.exists(conversion["file_path"])
    )
    if not has_file:
        raise HTTPException(status_code=400, detail="No file data available for OMR processing")
    
    # Update status to processing
    await db.conversions.update_one(
        {"conversion_id": conversion_id},
        {"$set": {
            "status": "processing_omr",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    try:
        import base64
        file_type = conversion.get("file_type", "pdf")
        
        # Get file data - try MongoDB first, then disk
        if conversion.get("file_data"):
            file_data = base64.b64decode(conversion["file_data"])
        elif conversion.get("file_path") and os.path.exists(conversion["file_path"]):
            with open(conversion["file_path"], 'rb') as f:
                file_data = f.read()
        else:
            raise HTTPException(status_code=400, detail="No file data available for OMR processing")
        
        # Save to temp file for OMR processing
        temp_suffix = f".{file_type}"
        if file_type in ["heic", "heif"]:
            temp_suffix = ".png"  # Already converted
            
        with tempfile.NamedTemporaryFile(suffix=temp_suffix, delete=False) as tmp:
            tmp.write(file_data)
            temp_path = tmp.name
        
        logger.info(f"Processing OMR for {conversion_id}, file type: {file_type}")
        
        # Run OMR processing
        omr_result = process_sheet_music_omr(temp_path)
        
        # Clean up temp file
        try:
            os.remove(temp_path)
        except:
            pass
        
        if omr_result.get("success"):
            # Extract notes for staff view
            staff_notes = extract_notes_for_staff_view(omr_result)
            
            # Apply key override if provided
            key_name = omr_result.get("key_name", "C")
            if request and request.key_override:
                key_name = request.key_override
                # Recalculate Motesart degrees with new key
                key_root = get_key_root_semitone(key_name)
                for note in staff_notes:
                    note["motesart"] = pitch_to_motesart(note["pitch"], key_root)
            
            # Update conversion with OMR results
            update_data = {
                "status": "completed",
                "omr_processed": True,
                "omr_success": True,
                "key_signature": f"1 = {key_name}",
                "key_name": key_name,
                "key_root": get_key_root_semitone(key_name),
                "time_signature": omr_result.get("time_signature", "4/4"),
                "title": omr_result.get("title") or conversion.get("filename", "").split(".")[0],
                "omr_notes": staff_notes,
                "omr_measures": omr_result.get("measures", []),
                "omr_lyrics": omr_result.get("lyrics", []),
                "content_type": "traditional",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            await db.conversions.update_one(
                {"conversion_id": conversion_id},
                {"$set": update_data}
            )
            
            logger.info(f"OMR completed for {conversion_id}: {len(staff_notes)} notes extracted")
            
        else:
            # OMR failed - try image analysis fallback
            logger.warning(f"OMR failed for {conversion_id}: {omr_result.get('error')}")
            
            # Try basic image analysis
            with tempfile.NamedTemporaryFile(suffix=temp_suffix, delete=False) as tmp:
                tmp.write(file_data)
                temp_path = tmp.name
            
            analysis_result = analyze_sheet_music_image(
                temp_path, 
                key_override=request.key_override if request else None
            )
            
            try:
                os.remove(temp_path)
            except:
                pass
            
            await db.conversions.update_one(
                {"conversion_id": conversion_id},
                {"$set": {
                    "status": "uploaded",
                    "omr_processed": True,
                    "omr_success": False,
                    "omr_error": omr_result.get("error", "OMR processing failed"),
                    "image_analysis": analysis_result,
                    "status_message": "OMR could not extract notes. Use Manual Entry to add chords.",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
        
    except Exception as e:
        logger.error(f"OMR processing error: {e}")
        import traceback
        traceback.print_exc()
        
        await db.conversions.update_one(
            {"conversion_id": conversion_id},
            {"$set": {
                "status": "error",
                "omr_processed": True,
                "omr_success": False,
                "omr_error": str(e),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
    
    # Return updated conversion
    updated = await db.conversions.find_one(
        {"conversion_id": conversion_id},
        {"_id": 0, "file_data": 0}
    )
    return updated

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

@api_router.post("/chat")
async def chat_with_music(req: ChatRequest, user: User = Depends(get_current_user)):
    """
    Chat with AI about the uploaded music file.
    Supports questions about key, progressions, transposition, and Motesart notation.
    """
    conversion = await db.conversions.find_one(
        {"conversion_id": req.conversion_id, "user_id": user.user_id},
        {"_id": 0, "file_data": 0}
    )
    if not conversion:
        raise HTTPException(status_code=404, detail="Conversion not found")
    
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        api_key = os.environ.get("EMERGENT_LLM_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="LLM API key not configured")
        
        # Build context about the music
        key_sig = conversion.get("key_signature", "1 = C")
        key_name = conversion.get("key_name") or conversion.get("raw_data", {}).get("key_name", "C")
        chords = conversion.get("chords", [])
        sections = conversion.get("sections", [])
        filename = conversion.get("filename", "Unknown")
        
        # Build progression summary
        progressions_text = ""
        for section in sections[:5]:
            if section.get("progression"):
                progressions_text += f"- {section.get('name', 'Section')}: {section.get('progression')}\n"
        
        # Build chord symbols list
        chord_symbols = [c.get("symbol", "") for c in chords[:20] if c.get("symbol")]
        
        system_message = f"""You are a helpful music theory expert specializing in the Motesart Number System.

You are helping a user understand their uploaded music file: "{filename}"

Current music context:
- Key: {key_sig} (the note {key_name} is represented as 1)
- Detected chords (in Motesart notation): {', '.join(chord_symbols[:15]) if chord_symbols else 'None detected'}
- Sections and progressions:
{progressions_text if progressions_text else 'No sections detected'}

Motesart Number System rules you must use:
- Numbers 1-7 represent scale degrees
- Half-numbers (1½, 2½, 4½, 5½, 6½) represent chromatic tones - NEVER use 3½ or 7½
- 'm' always marks minor chords (e.g., 2m, 6m)
- 'M' marks non-diatonic major chords only
- Slash notation (like 1/3) means chord/bass - the chord with a different bass note
- Extensions use superscripts: ⁷, ⁹, ¹¹, ¹³

When answering questions:
- Always use Motesart numbers, not letter names (say "1" not "C" when in key of C)
- Explain progressions in terms of their function (tonic, subdominant, dominant)
- Keep responses concise but educational
- If asked about transposition, explain how the numbers would stay the same but the key signature would change"""

        # Build conversation history
        history_text = ""
        for msg in req.history[-10:]:  # Last 10 messages for context
            role = "User" if msg.role == "user" else "Assistant"
            history_text += f"{role}: {msg.content}\n"
        
        prompt = f"""Previous conversation:
{history_text}

User's new question: {req.message}"""

        chat = LlmChat(
            api_key=api_key,
            session_id=f"chat_{req.conversion_id}_{user.user_id}",
            system_message=system_message
        ).with_model("openai", "gpt-5.2")
        
        response = await chat.send_message(UserMessage(text=prompt))
        
        return {
            "response": response,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except ImportError:
        # Fallback response if LLM not available
        return {
            "response": f"I can see this file is in the key of {conversion.get('key_signature', '1 = C')}. To get detailed analysis, please ensure the AI service is configured. You can use the Text Converter for manual chord input and conversion.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return {
            "response": f"I'm having trouble processing your request. The file appears to be in {conversion.get('key_signature', 'an unknown key')}. Please try again or use the Text Converter for manual input.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

# ==================== EXPORT (BRANDED MOTESART TEMPLATE) ====================

# Motesart Legend for exports (ASCII-safe version for PDF)
MOTESART_LEGEND = "Half-numbers (1 1/2, 2 1/2, 4 1/2, 5 1/2, 6 1/2) represent chromatic notes. No 3 1/2 or 7 1/2 (natural half-steps). | /X = bass first | m = minor | M = non-diatonic major | + = augmented | o = diminished | sus2/sus4 = suspensions | 7 9 11 13 = extensions"
MOTESART_LEGEND_RICH = "Half-numbers (1½, 2½, 4½, 5½, 6½) represent chromatic notes. No 3½ or 7½ (natural half-steps). | /X = bass first | m = minor | M = non-diatonic major | ⁺ = augmented | ° = diminished | sus²/sus⁴ = suspensions | ⁷ ⁹ ¹¹ ¹³ = extensions"

@api_router.get("/export/{conversion_id}")
async def export_conversion(
    conversion_id: str, 
    format: str = "text",
    user: User = Depends(get_current_user)
):
    """
    Export conversion to PDF, CSV, or Text with branded Motesart template.
    
    Template includes:
    - Header with Motesart branding
    - Song title and key
    - Sections with progressions
    - Symbol legend footer
    """
    conversion = await db.conversions.find_one(
        {"conversion_id": conversion_id, "user_id": user.user_id},
        {"_id": 0}
    )
    if not conversion:
        raise HTTPException(status_code=404, detail="Conversion not found")
    
    filename_base = conversion.get("filename", "export").rsplit(".", 1)[0]
    title = conversion.get("title") or filename_base
    key_sig = conversion.get("key_signature", "1 = C")
    time_sig = conversion.get("time_signature", "4/4")
    tempo = conversion.get("tempo", 120)
    content_type = conversion.get("content_type", "traditional")
    
    # Branded header (ASCII-safe for PDF)
    branded_header = "Converted by Motesart Technologies - Motesart Number System v1.0"
    branded_header_rich = "Converted by Motesart Technologies — Motesart Number System v1.0"
    
    if format == "csv":
        # Generate CSV with branded header
        import csv
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Branded header
        writer.writerow([branded_header])
        writer.writerow([])
        writer.writerow(["Title", title])
        writer.writerow(["Key", key_sig])
        writer.writerow(["Time Signature", time_sig])
        writer.writerow(["Tempo", f"{tempo} BPM"])
        writer.writerow(["Content Type", CONTENT_TYPES.get(content_type, content_type)])
        writer.writerow([])
        
        # Sections & Progressions
        writer.writerow(["Section", "Progression", "Chords"])
        for section in conversion.get("sections", []):
            chords_str = " | ".join([c.get("symbol", "") for c in section.get("chords", [])])
            writer.writerow([
                section.get("name", ""),
                section.get("progression", ""),
                chords_str
            ])
        
        writer.writerow([])
        
        # Notes (if available)
        notes = conversion.get("notes", [])
        if notes:
            writer.writerow(["Beat", "Pitch", "Motesart Number", "Duration"])
            for note in notes:
                writer.writerow([
                    note.get("beat", 0),
                    note.get("pitch", 0),
                    note.get("motesart_number", ""),
                    note.get("duration", 0)
                ])
        
        writer.writerow([])
        writer.writerow([MOTESART_LEGEND])
        
        content = output.getvalue()
        return StreamingResponse(
            io.BytesIO(content.encode()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename_base}_motesart.csv"}
        )
    
    elif format == "pdf":
        # Generate branded PDF that matches the Lead Sheet View visual preview
        from fpdf import FPDF
        
        # Helper to make strings PDF-safe (ASCII-only for fpdf compatibility)
        def pdf_safe(s):
            if not s:
                return ""
            # Replace Unicode characters with ASCII equivalents
            replacements = {
                "—": "-", "–": "-",
                "½": "1/2",
                "⁺": "+",
                "°": "o",
                "²": "2", "⁴": "4", "⁷": "7", "⁹": "9",
                "¹¹": "11", "¹³": "13",
                "♭": "b", "♯": "#", "♮": "",
                "♩": "", "♪": "", "♫": "", "♬": "",
            }
            for old, new in replacements.items():
                s = s.replace(old, new)
            # Remove any remaining non-ASCII characters
            return s.encode('ascii', 'ignore').decode('ascii')
        
        # Extract key name from key_sig (e.g., "1 = Ab" -> "Ab")
        key_name = key_sig.replace("1 = ", "") if "1 = " in key_sig else key_sig
        
        # Build scale reference for the key
        note_order = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        flat_order = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']
        use_flats = key_name in ['F', 'Bb', 'Eb', 'Ab', 'Db', 'Gb']
        notes = flat_order if use_flats else note_order
        
        key_idx = 0
        if key_name in note_order:
            key_idx = note_order.index(key_name)
        elif key_name in flat_order:
            key_idx = flat_order.index(key_name)
        
        intervals = [0, 2, 4, 5, 7, 9, 11]
        scale_ref = {}
        for i, interval in enumerate(intervals):
            scale_ref[i + 1] = notes[(key_idx + interval) % 12]
        
        pdf = FPDF()
        pdf.add_page()
        
        # Header with title (matches Lead Sheet View)
        pdf.set_font("Helvetica", "B", 20)
        pdf.set_text_color(127, 58, 237)  # Purple for title
        pdf.cell(0, 12, pdf_safe(title), ln=True, align="L")
        
        # Key signature line (amber color would be nice but PDF is B&W)
        pdf.set_font("Courier", "B", 14)
        pdf.set_text_color(180, 83, 9)  # Amber-ish
        pdf.cell(0, 8, f"1 = {key_name}  |  Time: {time_sig}", ln=True, align="L")
        
        # Branding subtitle
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 6, branded_header, ln=True, align="L")
        pdf.set_text_color(0, 0, 0)
        
        # Separator line
        pdf.ln(3)
        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
        # Scale Reference Box
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Helvetica", "B", 10)
        y_start = pdf.get_y()
        pdf.cell(0, 6, "Scale Reference:", ln=True)
        pdf.set_font("Courier", "", 10)
        
        # Display scale degrees in grid format
        scale_line = "  ".join([f"{i}={scale_ref[i]}" for i in range(1, 8)])
        pdf.cell(0, 6, scale_line + "  1/2=chromatic", ln=True)
        
        # Modifier legend
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, "m=minor | M=non-diatonic major | 7=7th | o=dim | +=aug | sus=suspended | /X=bass note", ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(5)
        
        # Sections with chords and lyrics (matches Lead Sheet format)
        sections = conversion.get("sections", [])
        for section in sections:
            section_name = section.get("name", "Section")
            
            # Section label in purple
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(127, 58, 237)
            pdf.cell(0, 8, f"[{section_name}]", ln=True)
            pdf.set_text_color(0, 0, 0)
            
            # If section has lines (chord_line / lyric_line), display them
            lines = section.get("lines", [])
            if lines:
                for line in lines:
                    line_type = line.get("type", "")
                    if line_type == "chord_line" and line.get("converted"):
                        # Chord numbers in bold amber
                        pdf.set_font("Courier", "B", 14)
                        pdf.set_text_color(180, 83, 9)
                        pdf.cell(0, 7, pdf_safe(line.get("converted", "")), ln=True)
                    elif line_type == "lyric_line" and line.get("original"):
                        # Lyrics in gray
                        pdf.set_font("Helvetica", "", 11)
                        pdf.set_text_color(75, 85, 99)
                        pdf.cell(0, 6, pdf_safe(line.get("original", "")), ln=True)
                pdf.set_text_color(0, 0, 0)
            else:
                # Fallback: just show chords
                chords = section.get("chords", [])
                if chords:
                    pdf.set_font("Courier", "B", 14)
                    pdf.set_text_color(180, 83, 9)
                    chord_str = "   ".join([pdf_safe(c.get("symbol", "")) for c in chords[:12]])
                    pdf.cell(0, 7, chord_str, ln=True)
                    pdf.set_text_color(0, 0, 0)
            
            # Progression summary
            progression = section.get("progression", "")
            if progression:
                pdf.set_font("Helvetica", "I", 9)
                pdf.set_text_color(100, 100, 100)
                pdf.cell(0, 5, f"Progression: {pdf_safe(progression)}", ln=True)
                pdf.set_text_color(0, 0, 0)
            
            pdf.ln(4)
        
        # Footer Legend
        pdf.ln(8)
        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(3)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(100, 100, 100)
        pdf.multi_cell(0, 4, "Legend: 1-7 = scale degrees | 1/2 = chromatic (only 1 1/2, 2 1/2, 4 1/2, 5 1/2, 6 1/2) | m = minor | M = non-diatonic major | 7 9 11 13 = extensions | /X = bass note")
        
        # fpdf.output() returns bytes when dest='S'
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        pdf_output = io.BytesIO(pdf_bytes)
        pdf_output.seek(0)
        
        return StreamingResponse(
            pdf_output,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename_base}_motesart.pdf"}
        )
    
    else:
        # Generate Text/Markdown with branded template that matches Lead Sheet View
        key_name = key_sig.replace("1 = ", "") if "1 = " in key_sig else key_sig
        
        # Build scale reference for the key
        note_order = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        flat_order = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']
        use_flats = key_name in ['F', 'Bb', 'Eb', 'Ab', 'Db', 'Gb']
        notes = flat_order if use_flats else note_order
        
        key_idx = 0
        if key_name in note_order:
            key_idx = note_order.index(key_name)
        elif key_name in flat_order:
            key_idx = flat_order.index(key_name)
        
        intervals = [0, 2, 4, 5, 7, 9, 11]
        scale_ref = {}
        for i, interval in enumerate(intervals):
            scale_ref[i + 1] = notes[(key_idx + interval) % 12]
        
        lines = [
            f"# {title}",
            f"1 = {key_name}  |  Time: {time_sig}",
            branded_header_rich,
            "",
            "─" * 50,
            "",
            "## Scale Reference:",
            "  ".join([f"{i}={scale_ref[i]}" for i in range(1, 8)]) + "  ½=chromatic",
            "m=minor | M=non-diatonic major | ⁷=7th | °=dim | ⁺=aug | sus=suspended | /X=bass",
            "",
        ]
        
        # Sections with chords and lyrics
        for section in conversion.get("sections", []):
            section_name = section.get("name", "Section")
            lines.append(f"[{section_name}]")
            
            # If section has lines, display them
            section_lines = section.get("lines", [])
            if section_lines:
                for line in section_lines:
                    line_type = line.get("type", "")
                    if line_type == "chord_line" and line.get("converted"):
                        lines.append(line.get("converted", ""))
                    elif line_type == "lyric_line" and line.get("original"):
                        lines.append(line.get("original", ""))
            else:
                # Fallback: just show chords
                chords = section.get("chords", [])
                if chords:
                    lines.append("   ".join([c.get("symbol", "") for c in chords]))
            
            # Progression summary
            progression = section.get("progression", "")
            if progression:
                lines.append(f"Progression: {progression}")
            
            lines.append("")
        
        # Footer legend
        lines.extend([
            "─" * 50,
            MOTESART_LEGEND_RICH
        ])
        
        content = "\n".join(lines)
        return StreamingResponse(
            io.BytesIO(content.encode('utf-8')),
            media_type="text/plain; charset=utf-8",
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
    allow_origins=[
        "http://localhost:3000",
        "https://motesart-converter.preview.emergentagent.com",
        "https://*.emergentagent.com",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
