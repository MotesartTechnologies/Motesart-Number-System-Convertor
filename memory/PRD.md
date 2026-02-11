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

### Phase 1.7 - February 11, 2026 (CURRENT)
**Complete Dashboard Reorganization:**

1. **Motesart Conversion Display Panel** ✅
   - Prominent 65% width on right column
   - Key signature in large amber text (e.g., "1 = G")
   - Section headers [Verse], [Chorus] in purple
   - Chord badges with symbols in gold/amber
   - Symbol legend at bottom
   - Motesart branding header

2. **Manual Entry Fallback** ✅
   - "Manual Entry" button in header
   - Key selector dropdown (12 keys: C through B)
   - Chord symbols textarea input
   - "Convert to Motesart Numbers" button
   - Updates conversion in database via PUT endpoint
   - Appears automatically when OCR fails

3. **Scrollable Right Column** ✅
   - `max-h-[calc(100vh-5rem)]` with `overflow-y-auto`
   - All panels accessible via scroll
   - No content cut off at bottom

4. **New 2-Column Layout** ✅
   - Left column (35%): Upload, Recent Files, Settings
   - Right column (65%): Conversion, AI Chat, Export
   - Dark theme `#0a0a1a` background
   - Cards `#12122a` with `rounded-xl`

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
- `PUT /api/conversions/{id}/manual` - **NEW** Update with manual entry data
- `DELETE /api/conversions/{id}` - Delete conversion
- `GET /api/conversions/{id}/file` - Get original file

### AI Interaction
- `POST /api/explain` - Generate AI explanation
- `POST /api/chat` - Chat with AI about music

### Export
- `GET /api/export/{id}?format=pdf|csv|text`

## Conversion Rules

### Rule §3: Half-Numbers
- Valid: 1½, 2½, 4½, 5½, 6½ (NEVER 3½ or 7½)
- Chromatic chord roots use ♭/♯ notation

### Rule §6: Chord Quality
- Minor: ALWAYS marked with 'm'
- Major: 'M' ONLY if non-diatonic
- Diatonic major: no modifier

### Rule §7: Inversions
- Format: chord/bass (G/B → 1/3)

### Rule §4c: Extensions
- Superscripts: 7→⁷, 9→⁹, 11→¹¹, 13→¹³

## Test Credentials
- Regular user: `testuser@example.com` / `test123456`
- Founder user: `motesartproductions@gmail.com` / `founder123456`

## Test Reports
- `/app/test_reports/iteration_5.json` - Avatar system (100%)
- `/app/test_reports/iteration_6.json` - Text converter (100%)
- `/app/test_reports/iteration_7.json` - Bug fixes (100%)
- `/app/test_reports/iteration_8.json` - Dashboard reorganization (100%)

## Prioritized Backlog

### P0 (Complete)
- [x] Multi-user avatar system
- [x] Text-based chord chart converter
- [x] Explain AI button
- [x] Chat section on File Upload page
- [x] HEIC file support
- [x] Dashboard reorganization with Manual Entry
- [x] Prominent Motesart Conversion display
- [x] Scrollable right column

### P1 (Next)
- [ ] Improve OCR accuracy with music-specific preprocessing
- [ ] Save chat history per conversion
- [ ] "Detect Key from Image" using image analysis

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
- `/app/frontend/src/pages/Dashboard.jsx` - File upload dashboard
- `/app/frontend/src/pages/ConverterPage.jsx` - Text converter
- `/app/frontend/src/components/Navbar.jsx` - Navigation
- `/app/backend/tests/test_dashboard_reorganization.py` - Dashboard tests
