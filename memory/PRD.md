# Motesart Number System Converter - PRD

## Original Problem Statement
Build a multi-step "Motesart Number System Converter" app that supports:
- Traditional sheet music (staff notation)
- Sheet music with chords written above staff
- Chord charts / lead sheets (section labels + chord symbols only)
- Hymnals / SATB (multi-staff with SATB voicing)

## What's Been Implemented

### Phase 1.3 - January 16, 2026
- **File Type Support**: PDF, PNG, JPG, MIDI, MusicXML
- **Chord Chart Parsing**: Parse chord symbols from text
- **Dual Authentication**: Google OAuth + Email/Password
- **Branded Exports**: PDF, CSV, Text with Motesart branding

### Phase 1.4 - January 17, 2026
- **Multi-User Avatar System**: Unique DiceBear avatars, custom upload, founder crown
- **Founder Account**: Special Motesart logo avatar and crown icon

### Phase 1.5 - February 11, 2026
- **Text Converter Page** (`/converter`): 3-column layout, auto key detection, color-coded output
- **Core Conversion Engine**: Rules §3 (half-numbers), §6 (chord quality), §7 (inversions), §4c (extensions)

### Phase 1.6 - February 11, 2026 (CURRENT)
**4 Critical Bug Fixes:**

1. **BUG 1: Explain AI Button** ✅
   - `/api/explain` endpoint with GPT-5.2 integration
   - Returns plain-English explanation using Motesart terminology
   - Shows loading spinner while generating
   - Error message if no chords detected

2. **BUG 2: Chat Section Added** ✅
   - New "Chat with AI" panel on File Upload page
   - Message bubbles: user (purple, right), AI (dark blue, left)
   - Suggested questions: "What key is this in?", "Explain the progression", "How do I transpose this?"
   - Auto-scroll to newest message
   - "Thinking..." animation while AI responds

3. **BUG 3: PDF/Image OCR** ✅
   - `extract_text_from_pdf()` using PyMuPDF for text extraction
   - `extract_text_from_image()` using pytesseract for OCR
   - Falls back gracefully if no chords detected
   - Status message: "Could not detect chords - try Text Converter"

4. **BUG 4: HEIC Support** ✅
   - Added `.heic` and `.heif` to supported formats
   - `convert_heic_to_png()` using pillow-heif
   - Upload box updated: "Supported: PDF, PNG, JPG, HEIC, MusicXML, MIDI"

## Application Routes
- `/` - Landing page
- `/login` - Login/Register page
- `/converter` - Text-based chord chart converter
- `/dashboard` - File upload converter (PDF, HEIC, MIDI, MusicXML)
- `/upload` - Alias for dashboard
- `/learn` - Methodology explanation page

## API Endpoints

### Authentication
- `POST /api/auth/register` - Email registration
- `POST /api/auth/login` - Email login
- `POST /api/auth/session` - Google OAuth session
- `GET /api/auth/me` - Current user with avatar
- `POST /api/auth/logout` - Clear session
- `PUT /api/auth/profile` - Update profile
- `POST /api/auth/avatar` - Upload avatar
- `DELETE /api/auth/avatar` - Reset avatar

### Text Conversion
- `POST /api/convert/text` - Convert chord chart text
- `GET /api/keys` - Available keys list

### File Upload & Conversion
- `POST /api/upload` - Upload file (PDF, PNG, JPG, HEIC, MIDI, MusicXML)
- `GET /api/conversions` - List user's conversions
- `GET /api/conversions/{id}` - Get single conversion
- `DELETE /api/conversions/{id}` - Delete conversion
- `GET /api/conversions/{id}/file` - Get original file

### AI Interaction
- `POST /api/explain` - Generate AI explanation for progression
- `POST /api/chat` - Chat with AI about uploaded music

### Export
- `GET /api/export/{id}?format=pdf|csv|text` - Export with branding

## Technical Dependencies

### Backend (Python)
- FastAPI, Pydantic, MongoDB (motor)
- mido (MIDI), music21 (MusicXML)
- fpdf2 (PDF export)
- **PyMuPDF** (PDF text extraction)
- **pytesseract** (OCR for images)
- **pillow-heif** (HEIC conversion)
- emergentintegrations (GPT-5.2 via Emergent LLM Key)

### System Dependencies
- **tesseract-ocr** (for pytesseract OCR)

### Frontend (React)
- React Router, Tailwind CSS, Shadcn/UI
- lucide-react icons
- axios for API calls

## Database Schema

### users collection
```json
{
  "user_id": "user_xxxxx",
  "email": "string",
  "name": "string",
  "username": "string",
  "avatar_url": "string",
  "is_founder": "boolean",
  "password_hash": "string",
  "created_at": "datetime"
}
```

### conversions collection
```json
{
  "conversion_id": "conv_xxxxx",
  "user_id": "user_xxxxx",
  "filename": "string",
  "file_type": "string (pdf|png|jpg|heic|midi|xml)",
  "status": "string (processing|uploaded|completed|error)",
  "key_signature": "string",
  "key_name": "string",
  "chords": [],
  "sections": [],
  "extraction_method": "string (ocr|pdf_text|midi|musicxml)",
  "file_data": "base64 string",
  "created_at": "datetime"
}
```

## Test Credentials
- Regular user: `testuser@example.com` / `test123456`
- Founder user: `motesartproductions@gmail.com` / `founder123456`

## Test Reports
- `/app/test_reports/iteration_5.json` - Avatar system (100% pass)
- `/app/test_reports/iteration_6.json` - Text converter (100% pass)
- `/app/test_reports/iteration_7.json` - Bug fixes (100% pass)

## Prioritized Backlog

### P0 (Complete)
- [x] Multi-user avatar system
- [x] Text-based chord chart converter
- [x] Explain AI button functionality
- [x] Chat section on File Upload page
- [x] PDF/image OCR extraction
- [x] HEIC file support

### P1 (Next)
- [ ] Improve OCR accuracy with music-specific training
- [ ] Add visual indicator when HEIC is being converted
- [ ] Save chat history per conversion

### P2 (Phase 2)
- [ ] Full OMR integration (Audiveris) for staff notation
- [ ] Hymnal SATB analysis
- [ ] Airtable integration
- [ ] Leaderboard page

### P3 (Future)
- [ ] Roman numeral side-by-side view
- [ ] Real-time playback
- [ ] Collaborative features
