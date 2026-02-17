# Motesart Number System Converter - PRD

## Original Problem Statement
Build a multi-step "Motesart Number System Converter" app that supports:
- Traditional sheet music (staff notation)
- Sheet music with chords written above staff
- Chord charts / lead sheets (section labels + chord symbols only)
- Hymnals / SATB (multi-staff with SATB voicing)

## What's Been Implemented

### Phase 1.3 - January 16, 2026
- File Type Support: PDF, PNG, JPG, MIDI, MusicXML
- Chord Chart Parsing, Dual Authentication, Branded Exports

### Phase 1.4 - January 17, 2026
- Multi-User Avatar System with founder crown

### Phase 1.5 - February 11, 2026
- Text Converter Page (`/converter`) with 3-column layout
- Core Conversion Engine with Rules §3, §6, §7, §4c

### Phase 1.6 - February 11, 2026
- Bug Fixes: Explain AI, Chat Section, PDF/Image OCR, HEIC Support

### Phase 1.7 - February 11, 2026
- Complete Dashboard Reorganization with Manual Entry fallback
- Scrollable right column layout

### Phase 1.9 - February 16, 2026 (COMPLETED)
**Text Converter Bug Fixes:**

1. **Minor Chord Markers (Bug Fix)** ✅
   - ALL minor chords now get 'm' marker (diatonic or not)
   - `Am in C → 6m` (not just 6)
   - `Em in C → 3m`
   - `Fm in C → 4m` (non-diatonic)

2. **Slash Notation (Bug Fix)** ✅
   - Format: bass/chord (bass note first)
   - `G/B in G → 3/1` (not 1/3)
   - `C/E in C → 3/1`
   - `D/F# in D → 3/1`

3. **Half-Numbers (Bug Fix)** ✅
   - No sharp (♯) or flat (♭) symbols in output
   - C# → 1½, D#/Eb → 2½, F# → 4½, G#/Ab → 5½, A#/Bb → 6½

### Phase 3 - February 17, 2026 (COMPLETED)
**Rebuilt OMR Pipeline with Google Gemini Vision API:**

1. **Removed Old OMR Systems:**
   - Removed broken Audiveris, oemer, Tesseract implementations
   - Cleaned up failed OMR code

2. **New Gemini-based OMR Pipeline:**
   - Uses Google Gemini Vision API (gemini-2.5-flash) via Emergent LLM key
   - Converts PDF pages to high-resolution PNG (300 DPI)
   - Sends images with detailed prompt for note extraction
   - Parses structured JSON response with measures, notes, lyrics

3. **Motesart Conversion:**
   - Maps notes to numbers: C=1, D=2, E=3, F=4, G=5, A=6, B=7
   - Half-numbers for chromatic notes (1½, 2½, 4½, 5½, 6½)
   - Octave dots: • above for higher octaves, • below for lower octaves

4. **Display Format:**
   - Motesart numbers on one line with measure bars (|)
   - Lyrics aligned below (when extracted)
   - Legend explaining notation

5. **Supported File Types:**
   - Scanned PDF hymnals
   - Image uploads (PNG, JPG, JPEG, WebP)
   - HEIC conversion supported

## Application Routes
- `/` - Landing page
- `/login` - Login/Register page
- `/converter` - Text-based chord chart converter
- `/dashboard` - File upload with Manual Entry fallback
- `/learn` - Methodology explanation page

## API Endpoints

### Authentication
- `POST /api/auth/register` | `login` | `session` | `logout`
- `GET /api/auth/me`
- `PUT /api/auth/profile`
- `POST /api/auth/avatar` | `DELETE /api/auth/avatar`

### Text Conversion
- `POST /api/convert/text` - Convert chord chart text
- `GET /api/keys` - Available keys list

### File Upload & Manual Entry
- `POST /api/upload` - Upload file (PDF, PNG, JPG, HEIC, MIDI, MusicXML)
- `GET /api/conversions` - List user's conversions
- `GET /api/conversions/{id}` - Get single conversion
- `PUT /api/conversions/{id}/manual` - Update with manual entry data
- `DELETE /api/conversions/{id}` - Delete conversion
- `GET /api/conversions/{id}/file` - Get original file

### AI Interaction
- `POST /api/explain` - Generate AI explanation
- `POST /api/chat` - Chat with AI about music

### Export
- `GET /api/export/{id}?format=pdf|csv|text` - Export with visual preview match

## Conversion Rules

### Rule §3: Half-Numbers (CRITICAL)
The Motesart Number System **NEVER** uses sharp (♯) or flat (♭) symbols in output.
All chromatic notes use half-numbers moving UPWARD only:
- **Valid:** 1½, 2½, 4½, 5½, 6½
- **NEVER:** 3½ or 7½ (these are natural half-steps)

Chromatic note mapping (any key):
- Degree + 1 semitone → half-number (e.g., C# in C = 1½)
- All 12 chromatic notes map to: 1, 1½, 2, 2½, 3, 4, 4½, 5, 5½, 6, 6½, 7

### Rule §6: Chord Quality
- **Minor chords:** ALWAYS marked with 'm'
  - Am in key of C → 6m
  - Em in key of G → 6m
  - Fm in key of C → 4m
- **Diatonic major chords:** NO quality marker
  - C in key of C → 1
  - F in key of C → 4
- **Non-diatonic major:** marked with 'M'
  - E major in key of C → 3M (explicit like "Emaj")
- **Chromatic root (half-number):** No 'M' marker needed
  - C# (1½) doesn't need 'M' - the half-number already shows non-diatonic
- **Diminished:** marked with '°'
- **Augmented:** marked with '⁺'

### Rule §7: Inversions
- Format: bass/chord (bass note first, chord second)
  - G/B in G → 3/1 (B is 3, G chord is 1)
  - C/E in C → 3/1 (E is 3, C chord is 1)

### Rule §4c: Extensions
- Superscripts: 7→⁷, 9→⁹, 11→¹¹, 13→¹³

### Settings
- "Show half-numbers" toggle **REMOVED** - half-numbers are always on
- Kept: "Show octave markings", "Roman numerals side-by-side"

## Test Credentials
- Regular user: `test@example.com` / `Test123!`
- Founder user: `motesartproductions@gmail.com` / (via Google Auth)

## Test Reports
- `/app/test_reports/iteration_10.json` - Phase 1 Bug Fixes & Phase 3 OMR (100% pass)
- Test file: `/app/backend/tests/test_phase1_bug_fixes.py`

## Prioritized Backlog

### P0 (Complete)
- [x] Lead Sheet View (Format B) rendering
- [x] Manual Entry with live preview
- [x] Export matches visual preview
- [x] Chromatic note handling with half-numbers (no sharps/flats)
- [x] Slash notation (bass/chord format)
- [x] Minor chord markers (ALL minors get 'm')
- [x] Gemini-based OMR for image analysis
- [x] Staff View with Motesart numbers on notes

### P1 (In Progress)
- [ ] Toolbar functionality (Zoom, Print mode)
- [ ] Multi-page PDF processing for OMR
- [ ] Lyrics extraction and display under notes

### P2 (Future)
- [ ] Hymnal SATB analysis
- [ ] Airtable integration
- [ ] Leaderboard page
- [ ] Export as MusicXML with Motesart

## Files of Reference
- `/app/backend/server.py` - Backend with all endpoints
- `/app/backend/omr_service.py` - Gemini-based OMR service
- `/app/frontend/src/pages/Dashboard.jsx` - File upload dashboard with live preview
- `/app/frontend/src/pages/ConverterPage.jsx` - Text converter
- `/app/frontend/src/components/LeadSheetView.jsx` - Lead sheet format display
- `/app/frontend/src/components/StaffNotationView.jsx` - Staff notation canvas with OMR notes
- `/app/frontend/src/components/MotesartPreview.jsx` - Preview container with toolbar
- `/app/frontend/src/components/Navbar.jsx` - Navigation

## Known Issues
- **OMR Accuracy:** Gemini-based OMR provides reasonable note extraction but may not capture every note perfectly. For critical accuracy, use Manual Entry.
- **PDF Multi-page:** Currently only processes first page of PDF files.
- **Lyrics:** Gemini extracts lyrics but they're not yet rendered under the staff.
