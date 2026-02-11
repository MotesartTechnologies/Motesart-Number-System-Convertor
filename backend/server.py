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
    Convert semitones from root to scale degree and whether it's chromatic.
    Returns (degree_number, is_chromatic, half_number_symbol)
    """
    semitones = semitones % 12
    
    # Check if it's a diatonic scale degree
    if semitones in MAJOR_SCALE_SEMITONES:
        degree = MAJOR_SCALE_SEMITONES.index(semitones) + 1
        return (degree, False, str(degree))
    
    # Chromatic - use half-numbers
    half_symbol = HALF_NUMBER_MAP.get(semitones)
    if half_symbol:
        base_degree = int(half_symbol[0])
        return (base_degree, True, half_symbol)
    
    # Fallback for edge cases
    return (0, True, f"?{semitones}")

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
    Uses BASS FIRST, CHORD SECOND for slash chords per methodology.
    """
    if not chord_str or chord_str.strip() == '':
        return None
    
    chord_str = chord_str.strip()
    
    # Handle slash chords (bass/chord or chord/bass in input)
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
    
    # Convert root to Motesart number
    root_number = get_note_number(root_semitone + 60, key_root)
    
    # Determine chord quality
    quality = ""
    extensions = []
    
    # Check for minor
    if quality_str.startswith('m') and not quality_str.startswith('maj'):
        quality = "m"
        quality_str = quality_str[1:]
    elif quality_str.startswith('min'):
        quality = "m"
        quality_str = quality_str[3:]
    
    # Check for diminished
    if 'dim' in quality_str or '°' in quality_str or 'o' in quality_str.lower():
        quality = "°"
        quality_str = re.sub(r'dim|°|o', '', quality_str, flags=re.IGNORECASE)
    
    # Check for augmented
    if 'aug' in quality_str or '+' in quality_str:
        quality = "⁺"
        quality_str = re.sub(r'aug|\+', '', quality_str, flags=re.IGNORECASE)
    
    # Check for suspended
    if 'sus2' in quality_str:
        quality = "sus²"
        quality_str = quality_str.replace('sus2', '')
    elif 'sus4' in quality_str or 'sus' in quality_str:
        quality = "sus⁴"
        quality_str = re.sub(r'sus4?', '', quality_str)
    
    # Check for 7th
    if 'maj7' in quality_str.lower() or 'M7' in quality_str or 'Δ7' in quality_str:
        quality += "M⁷"
        quality_str = re.sub(r'maj7|M7|Δ7', '', quality_str, flags=re.IGNORECASE)
    elif '7' in quality_str and 'm' in quality:
        quality = "m⁷"
        quality_str = quality_str.replace('7', '')
    elif '7' in quality_str:
        quality += "⁷"
        quality_str = quality_str.replace('7', '')
    
    # Check for extensions (2⁹, 4¹¹, 6¹³)
    if '9' in quality_str:
        extensions.append("⁹")
        quality_str = quality_str.replace('9', '')
    if '11' in quality_str:
        extensions.append("¹¹")
        quality_str = quality_str.replace('11', '')
    if '13' in quality_str:
        extensions.append("¹³")
        quality_str = quality_str.replace('13', '')
    
    # Build Motesart symbol
    symbol = root_number + quality
    if extensions:
        symbol += "".join(extensions)
    
    # Handle slash bass (BASS FIRST, CHORD SECOND per methodology)
    bass_number = None
    if bass_note:
        bass_root = re.match(r'^([A-G][#b]?)', bass_note)
        if bass_root:
            bass_semitone = CHORD_ROOT_MAP.get(bass_root.group(1), 0)
            bass_number = get_note_number(bass_semitone + 60, key_root)
            # Format: bass/chord (e.g., 1/5 = 1 in bass, 5-chord above)
            symbol = f"{bass_number}/{root_number}{quality}"
    
    return {
        "original": chord_str,
        "symbol": symbol,
        "root": root_number,
        "quality": quality,
        "bass": bass_number,
        "extensions": extensions
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

# ==================== EXPORT (BRANDED MOTESART TEMPLATE) ====================

# Motesart Legend for exports (ASCII-safe version for PDF)
MOTESART_LEGEND = "Symbol Legend: 1/2 = chromatic step up | /X = bass first (slash) | m = minor | M = non-diatonic major | + = augmented | o = diminished | sus2/sus4 = suspensions | 9 11 13 = extensions"
MOTESART_LEGEND_RICH = "½ = chromatic step up | /X = bass first (slash) | m = minor | M = non-diatonic major | ⁺ = augmented | ° = diminished | sus²/sus⁴ = suspensions | 2⁹ / 4¹¹ / 6¹³ = extensions"

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
        # Generate branded PDF (using ASCII-safe characters)
        from fpdf import FPDF
        
        # Helper to make strings PDF-safe
        def pdf_safe(s):
            if not s:
                return ""
            return s.replace("—", "-").replace("½", "1/2").replace("⁺", "+").replace("°", "o").replace("²", "2").replace("⁴", "4").replace("⁹", "9").replace("¹¹", "11").replace("¹³", "13")
        
        pdf = FPDF()
        pdf.add_page()
        
        # Header with branding
        pdf.set_font("Helvetica", "B", 18)
        pdf.cell(0, 12, "Motesart Number Conversion", ln=True, align="C")
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 6, branded_header, ln=True, align="C")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(5)
        
        # Title and Key
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, pdf_safe(f"{title} - {key_sig}"), ln=True, align="C")
        
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 8, f"Time: {time_sig} | Tempo: {tempo} BPM | Type: {CONTENT_TYPES.get(content_type, content_type)}", ln=True, align="C")
        pdf.ln(8)
        
        # Sections & Progressions
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 10, "Sections & Progressions", ln=True)
        pdf.set_font("Courier", "", 11)
        
        for section in conversion.get("sections", []):
            section_name = section.get("name", "Section")
            progression = pdf_safe(section.get("progression", ""))
            chords = section.get("chords", [])
            
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 8, f"{section_name}:", ln=True)
            
            pdf.set_font("Courier", "", 11)
            if chords:
                chord_symbols = " | ".join([pdf_safe(c.get("symbol", "")) for c in chords[:12]])
                pdf.multi_cell(0, 6, chord_symbols)
            elif progression:
                pdf.cell(0, 6, progression, ln=True)
            pdf.ln(3)
        
        # All Chords summary
        all_chords = conversion.get("chords", [])
        if all_chords:
            pdf.ln(5)
            pdf.set_font("Helvetica", "B", 13)
            pdf.cell(0, 10, "All Chords", ln=True)
            pdf.set_font("Courier", "", 10)
            chord_line = " | ".join([pdf_safe(c.get("symbol", "")) for c in all_chords[:30]])
            pdf.multi_cell(0, 6, chord_line)
        
        # Progressions Detected
        progressions = conversion.get("progressions", [])
        if progressions:
            pdf.ln(5)
            pdf.set_font("Helvetica", "B", 13)
            pdf.cell(0, 10, "Progressions Detected", ln=True)
            pdf.set_font("Helvetica", "", 11)
            for prog in progressions:
                prog_name = pdf_safe(prog.get('name', ''))
                prog_desc = pdf_safe(prog.get('description', ''))
                pdf.cell(0, 7, f"- {prog_name}: {prog_desc}", ln=True)
        
        # Footer Legend (ASCII-safe)
        pdf.ln(10)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(80, 80, 80)
        pdf.multi_cell(0, 5, MOTESART_LEGEND)
        
        pdf_output = io.BytesIO()
        pdf.output(pdf_output)
        pdf_output.seek(0)
        
        return StreamingResponse(
            pdf_output,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename_base}_motesart.pdf"}
        )
    
    else:
        # Generate Text/Markdown with branded template (can use rich characters)
        lines = [
            branded_header_rich,
            "=" * len(branded_header),
            "",
            f"# {title}",
            f"**Key:** {key_sig}",
            f"**Time:** {time_sig} | **Tempo:** {tempo} BPM",
            f"**Type:** {CONTENT_TYPES.get(content_type, content_type)}",
            "",
            "## Sections & Progressions"
        ]
        
        for section in conversion.get("sections", []):
            section_name = section.get("name", "Section")
            progression = section.get("progression", "")
            chords = section.get("chords", [])
            
            lines.append(f"\n### {section_name}")
            if chords:
                chord_str = " | ".join([c.get("symbol", "") for c in chords])
                lines.append(chord_str)
            elif progression:
                lines.append(progression)
        
        # All chords
        all_chords = conversion.get("chords", [])
        if all_chords:
            lines.extend(["", "## All Chords"])
            chord_line = " | ".join([c.get("symbol", "") for c in all_chords])
            lines.append(chord_line)
        
        # Progressions
        progressions = conversion.get("progressions", [])
        if progressions:
            lines.extend(["", "## Progressions Detected"])
            for prog in progressions:
                lines.append(f"- {prog.get('name')}: {prog.get('description', '')}")
        
        # Footer legend (rich version for text)
        lines.extend(["", "---", MOTESART_LEGEND_RICH])
        
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
        "https://music2numbers.preview.emergentagent.com",
        "https://*.emergentagent.com",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
