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

### Phase 3.1 - February 17, 2026 (COMPLETED)
**Enhanced OMR with Lyrics Alignment & Multi-page Support:**

1. **Lyrics Alignment:**
   - Motesart numbers displayed on one line
   - Lyrics/words aligned directly below corresponding numbers
   - Format: | 1  1  5  5 | with lyrics below each note
   - Uses measure bars (|) to separate measures

2. **Multi-page PDF Support:**
   - Processes ALL pages in uploaded PDFs
   - Converts each page to 300 DPI PNG
   - Sends each page to Gemini individually
   - Combines all pages into continuous output
   - Shows page count and failed page warnings

3. **Error Handling:**
   - Clear error messages for failed pages
   - "API credits exhausted" message for quota issues
   - "Could not read page X" for individual page failures
   - Graceful degradation - continues processing other pages

4. **Accuracy Verification:**
   - Original file preview toggle
   - Side-by-side comparison of original and conversion
   - Text output expandable section for verification

5. **Export Options:**
   - "Copy Text" button for clipboard export
   - Text output shows numbers and lyrics aligned
   - PDF and PNG export buttons in toolbar

6. **API Key Management:**
   - Users can add their own Gemini API key
   - Falls back to Emergent LLM key if no user key
   - API key status shown (masked)
   - Endpoints: GET/PUT /api/auth/api-keys

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
- [ ] API Key Management UI - frontend for users to enter their own Gemini API key
- [ ] Visual Staff Notation (Format A) - render Motesart numbers on top of original sheet music image

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
- **Visual Staff View:** Current StaffNotationView shows text-based output. Full visual rendering (numbers on image) is planned.
- **API Key UI:** Backend endpoint exists but frontend UI for API key management is not yet implemented.

## Changelog

### February 17, 2026 - Priority 1 Critical Bug Fix (COMPLETED)
**Fixed: Gemini OMR Pipeline Not Triggering on File Upload**

The application was showing "No Chords Detected" errors because the upload endpoint was not correctly calling the Gemini OMR pipeline. This recurring issue has been permanently resolved.

**Changes Made:**
1. Deleted old `extract_text_from_image()` function (lines 1640-1690)
2. Deleted old `extract_text_from_pdf()` function (lines 1692-1750)
3. Verified `/api/upload` endpoint correctly calls `process_sheet_music_omr()` from `omr_service.py`
4. Removed all instances of "No chords detected" error messages from backend

**Verification:**
- Backend logs now show: `Step 1: File uploaded` → `Step 2: Calling Gemini Vision API` → `Step 3: Gemini response received` → `Step 4: OMR successful` → `Step 5: Motesart conversion complete`
- Upload returns `status: "completed"` with `omr_success: True` and extracted notes
- 100% test pass rate (11/11 backend tests)

**Test Report:** `/app/test_reports/iteration_11.json`
