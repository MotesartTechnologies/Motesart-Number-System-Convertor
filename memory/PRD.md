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

### Phase 3 - February 16, 2026 (COMPLETED)
**Gemini-based OMR Implementation:**

1. **Gemini AI Integration** ✅
   - Uses Gemini 2.5 Flash via Emergent LLM Key
   - Analyzes sheet music images to extract notes
   - Detects key signature, time signature, title

2. **Note Extraction** ✅
   - Extracts individual notes with pitch, duration
   - Converts pitches to Motesart degrees
   - Handles chromatic notes with half-numbers

3. **Staff View Rendering** ✅
   - Canvas-based staff notation display
   - Motesart numbers rendered on note heads
   - Key and time signature displayed
   - Title from metadata shown

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
- **Diatonic chords:** NO quality marker (even for minor/diminished)
  - Am in key of C → 6 (not 6m)
  - Em in key of G → 6 (not 6m)
- **Non-diatonic minor:** marked with 'm'
  - Fm in key of C → 4m
- **Non-diatonic major:** marked with 'M'
  - A major in key of C → 6M
- **Chromatic root (half-number):** No 'M' marker needed
  - C# (1½) doesn't need 'M' - the half-number already shows non-diatonic

### Rule §7: Inversions
- Format: chord/bass (G/B → 1/3)

### Rule §4c: Extensions
- Superscripts: 7→⁷, 9→⁹, 11→¹¹, 13→¹³

### Settings
- "Show half-numbers" toggle **REMOVED** - half-numbers are always on
- Kept: "Show octave markings", "Roman numerals side-by-side"

## Test Credentials
- Regular user: `testuser@example.com` / `test123456`
- Founder user: `motesartproductions@gmail.com` / `founder123456`

## Test Reports
- `/app/test_reports/iteration_9.json` - Lead Sheet View & Live Preview (100%)

## Prioritized Backlog

### P0 (Complete)
- [x] Lead Sheet View (Format B) rendering
- [x] Manual Entry with live preview
- [x] Export matches visual preview
- [x] Basic Staff View (Phase 1)
- [x] Chromatic note handling with half-numbers (no sharps/flats)
- [x] Slash notation (inversions) working
- [x] Quality markers fixed (diatonic = no marker)

### P1 (In Progress - Phase 2)
- [x] OMR infrastructure created (oemer, music21, omr_service.py)
- [x] File upload saves to disk for large files
- [x] OMR endpoint `/api/conversions/{id}/omr` created
- [x] Manual Note Entry component for Staff View
- [ ] Audiveris deep learning OMR (requires specialized models)
- [ ] Enhanced Staff View with rhythmic notation

### P2 (Phase 2 - Deferred)
- [ ] Full Audiveris integration for accurate note extraction
- [ ] Per-note rendering on staff with correct positions
- [ ] Hymnal SATB analysis
- [ ] Airtable integration
- [ ] Leaderboard page

## Files of Reference
- `/app/backend/server.py` - Backend with all endpoints
- `/app/frontend/src/pages/Dashboard.jsx` - File upload dashboard with live preview
- `/app/frontend/src/pages/ConverterPage.jsx` - Text converter
- `/app/frontend/src/components/LeadSheetView.jsx` - Lead sheet format display
- `/app/frontend/src/components/StaffNotationView.jsx` - Staff notation canvas
- `/app/frontend/src/components/MotesartPreview.jsx` - Preview container with toolbar
- `/app/frontend/src/components/Navbar.jsx` - Navigation

## Known Issues
- **OMR Pipeline:** Optical Music Recognition for PDF/images still unreliable. Current implementation uses pytesseract which works for chord chart text but not for traditional sheet music notation.
- **Workaround:** Manual Entry provides reliable chord input and live preview functionality.
