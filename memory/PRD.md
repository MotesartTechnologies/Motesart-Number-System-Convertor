# Motesart Number System Converter - PRD

## Original Problem Statement
Build a multi-step "Motesart Number System Converter" app that supports:
- Traditional sheet music (staff notation)
- Sheet music with chords written above staff
- Chord charts / lead sheets (section labels + chord symbols only)
- Hymnals / SATB (multi-staff with SATB voicing)

## Source of Truth
`THE-MOTESART-NUMBER-SYSTEM-1pg-Methedology.docx`

## User Personas
1. **Music Students** - Learning music theory through the number system
2. **Music Teachers** - Creating lesson materials
3. **Church Musicians** - Converting hymnals and chord charts
4. **Worship Leaders** - Converting lead sheets like "Send Me"

## Core Conversion Rules (IMPLEMENTED)

### Rule §3: Half-Numbers
- **For melodic notes**: Valid are 1½, 2½, 4½, 5½, 6½ (NEVER 3½ or 7½)
- **For chord roots**: Use flat/sharp notation (♭2, ♭3, ♯4, ♯5, ♭7)

### Rule §6: Chord Quality Inference
- **Minor chords**: ALWAYS marked with 'm' (Em → 6m, Am → 2m)
- **Major chords**: Add 'M' ONLY if non-diatonic (F in G → ♭7M)
- **Diatonic major**: No modifier (G in G → 1, C in G → 4)
- **Diminished**: '°' symbol
- **Augmented**: '⁺' symbol

### Rule §7: Inversions - chord/bass Format
- Slash chords: chord/bass (NOT bass/chord)
- G/B in key of G → 1/3 (1-chord with 3 in bass)
- D/F# in key of G → 5/7 (5-chord with 7 in bass)

### Rule §4c: Extensions with Superscripts
- 7→⁷, 9→⁹, 11→¹¹, 13→¹³
- Maj7: M⁷, Min7: m⁷, Dom7: ⁷

## Symbol Legend
- m → minor chord
- M → major chord (non-diatonic only)
- ⁺ → augmented chord
- ° → diminished chord
- ø⁷ → half-diminished 7th
- sus² → suspended 2
- sus⁴ → suspended 4
- ⁷ → seventh chord
- /X → bass note (slash notation)
- ♭X / ♯X → chromatic chord roots

## What's Been Implemented

### Phase 1.3 - January 16, 2026
- **File Type Support**: PDF, PNG, JPG, MIDI, MusicXML
- **Chord Chart Parsing**: Parse chord symbols from text
- **Status Flow**: uploaded → converting → completed → error
- **Branded Template**: Logo, header, sections, legend footer
- **Export Formats**: PDF, CSV, Text with branding
- **Dual Authentication**: Google OAuth + Email/Password

### Phase 1.4 - January 17, 2026
- **Multi-User Avatar System** ✅
  - Unique DiceBear avatars for each user (based on user_id seed)
  - Custom avatar upload with base64 storage
  - Avatar deletion reverts to DiceBear default
  - Profile update endpoint for username/name changes
- **Founder Account Special Handling** ✅
  - Detection by email (motesartproductions@gmail.com)
  - Automatic `is_founder=true` flag
  - Username automatically set to "Motesart"
  - Special Motesart logo avatar
  - Golden crown icon in UI

### Phase 1.5 - February 11, 2026 (CURRENT)
- **Text Converter Page** ✅
  - New /converter route for text-based chord chart conversion
  - 3-column layout: Input Panel (left), Output Panel (center), Settings (right)
  - Auto key detection from chord patterns
  - Manual key selection (Auto-detect, C through B)
  - Time signature selector
  - Color-coded output:
    - Section headers [Verse], [Chorus]: purple (#a78bfa)
    - Chord numbers: gold/amber (#fbbf24)
    - Lyrics: gray (#9ca3af)
  - Settings toggles: half-numbers, octave markers, roman numerals
  - Copy to clipboard functionality
  - Example loaders (Simple Hymn, Pop Song, Jazz Standard)
  - Conversion Rules reference panel

- **Core Conversion Engine** ✅
  - Rule §3 Half-Numbers: ♭/♯ notation for chromatic chord roots
  - Rule §6 Chord Quality: 'm' always for minor, 'M' only for non-diatonic major
  - Rule §7 Inversions: chord/bass format (G/B → 1/3)
  - Rule §4c Extensions: Superscripts (Cmaj7 → 1M⁷, Dm7 → 2m⁷)
  - Smart regex: Avoids detecting chords within words (Amazing ≠ Am)

## Application Routes
- `/` - Landing page
- `/login` - Login/Register page
- `/converter` - **NEW** Text-based chord chart converter
- `/dashboard` - File upload converter (MIDI, MusicXML, etc.)
- `/upload` - Alias for dashboard
- `/learn` - Methodology explanation page

## API Endpoints

### Authentication
- `POST /api/auth/register` - Email registration
- `POST /api/auth/login` - Email login
- `POST /api/auth/session` - Google OAuth session exchange
- `GET /api/auth/me` - Get current user with avatar
- `POST /api/auth/logout` - Clear session
- `PUT /api/auth/profile` - Update username/name
- `POST /api/auth/avatar` - Upload custom avatar
- `DELETE /api/auth/avatar` - Revert to default avatar

### Text Conversion (NEW)
- `POST /api/convert/text` - Convert chord chart text to Motesart numbers
  - Params: `text`, `key` (optional), `time_signature`, `show_half_numbers`
  - Returns: `key`, `chord_count`, `sections[]` with converted lines
- `GET /api/keys` - Get list of available keys

### File Conversions
- `POST /api/upload` - Upload and convert file (MIDI, MusicXML)
- `GET /api/conversions` - List user's conversions
- `GET /api/conversions/{id}` - Get single conversion
- `DELETE /api/conversions/{id}` - Delete conversion
- `GET /api/conversions/{id}/file` - Get original file

### Export
- `GET /api/export/{id}?format=pdf|csv|text` - Export with branding

### AI
- `POST /api/explain` - Generate AI explanation (GPT-5.2 via Emergent LLM Key)

## Database Schema

### users collection
```json
{
  "user_id": "user_xxxxx",
  "email": "string",
  "name": "string",
  "username": "string (optional, e.g., 'Motesart')",
  "picture": "string (Google profile picture)",
  "avatar_url": "string (custom or DiceBear URL)",
  "is_founder": "boolean",
  "password_hash": "string (for email auth)",
  "auth_type": "string ('email' or null for Google)",
  "created_at": "datetime"
}
```

### conversions collection
```json
{
  "conversion_id": "conv_xxxxx",
  "user_id": "user_xxxxx",
  "filename": "string",
  "file_type": "string",
  "status": "string",
  "key_signature": "string",
  "chords": [],
  "sections": [],
  "created_at": "datetime"
}
```

## Test Credentials
- Regular user: `testuser@example.com` / `test123456`
- Founder user: `motesartproductions@gmail.com` / `founder123456`

## Test Reports
- `/app/test_reports/iteration_5.json` - Avatar system tests (100% pass)
- `/app/test_reports/iteration_6.json` - Converter tests (100% pass)
- `/app/tests/test_motesart_converter.py` - Conversion rule tests

## Prioritized Backlog

### P0 (Complete)
- [x] Multi-user avatar system with unique icons
- [x] Founder special handling (crown, Motesart avatar)
- [x] Text-based chord chart converter with exact rules

### P1 (Next)
- [ ] Clean up state on re-login (ensure selectedConversion resets)
- [ ] Save text conversions to database
- [ ] Export converted text to PDF/CSV

### P2 (Phase 2)
- [ ] OMR integration (Audiveris/ScanScore) for PDF/image conversion
- [ ] Hymnal SATB analysis for bass line chord detection
- [ ] Airtable integration for T.A.M.i dashboard
- [ ] Leaderboard page with user avatars and rankings

### P3 (Future)
- [ ] Roman numeral side-by-side view (toggle in settings)
- [ ] Real-time playback
- [ ] Collaborative features
- [ ] Multiple avatar style options (DiceBear styles)

## Technical Notes

### Chord Pattern Regex
```python
# Avoids matching chords within words using negative lookahead/lookbehind
r'(?<![a-z])([A-G][#b]?(?:maj7|maj|min|m|M7|M|dim|aug|sus[24]?|add|13|11|9|7)*(?:/[A-G][#b]?)?)(?![a-z])'
```

### Diatonic Chord Detection
```python
DIATONIC_QUALITIES = {
    1: 'major', 2: 'minor', 3: 'minor', 4: 'major', 
    5: 'major', 6: 'minor', 7: 'diminished'
}
```

### Avatar Generation
Using DiceBear Initials API for unique avatars:
```
https://api.dicebear.com/7.x/initials/svg?seed={user_id}&chars=2&backgroundColor=6366f1,8b5cf6,06b6d4&textColor=ffffff
```

### Founder Detection
Email-based detection: `motesartproductions@gmail.com`

### CORS Configuration
```python
allow_origins=["http://localhost:3000", "https://music2numbers.preview.emergentagent.com"]
```

## Files of Reference
- `/app/backend/server.py` - All backend logic (conversion engine, auth, API endpoints)
- `/app/frontend/src/pages/ConverterPage.jsx` - Text converter UI
- `/app/frontend/src/pages/Dashboard.jsx` - File upload UI
- `/app/frontend/src/components/Navbar.jsx` - Navigation with avatar/crown
- `/app/frontend/src/App.js` - Router configuration
