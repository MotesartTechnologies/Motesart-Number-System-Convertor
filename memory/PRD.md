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

### Phase 1.8 - February 11, 2026 (CURRENT)
**Visual Preview Implementation:**

1. **Lead Sheet View (Format B)** ✅
   - Title in purple/violet
   - Key signature "1 = Ab" in amber/gold
   - Section labels [Verse], [Chorus] in purple
   - Chord numbers in gold above lyrics
   - Scale Reference box with all 7 degrees
   - Progression summary boxes per section
   - Legend at bottom

2. **Manual Entry Live Preview** ✅
   - Debounced 500ms live preview as user types
   - Key and Time signature selectors
   - Section detection ([Verse], [Chorus])
   - Instant Motesart conversion display
   - "Apply to Preview" button to confirm

3. **Export Matches Visual Preview** ✅
   - PDF export with Lead Sheet format
   - Text export with sections and lyrics
   - Scale reference box in exports
   - Progression summaries included

4. **Basic Staff View (Phase 1)** ✅
   - 5-line staff with treble clef
   - Chord numbers above staff
   - Note positions on staff lines
   - Section labels rendered
   - Bar lines and double bar at end

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

### P1 (Next)
- [ ] Try Audiveris or music21 for improved OMR
- [ ] Enhanced Staff View with rhythmic notation
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
