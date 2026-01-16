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

## Methodology Rules

### Extensions (Section 5)
- Extensions do NOT introduce new numbers
- Written as superscripts: 2⁹, 4¹¹, 6¹³
- Think in 2, 4, 6 relative to scale

### Inversions (Section 7) - BASS FIRST, CHORD SECOND
- 1/3 = 1 in bass, 3-chord above
- 1/5 = 1 in bass, 5-chord above
- 1/7 = 1 in bass, 7-chord above

### Symbol Legend
- m → minor chord
- M → major chord (non-diatonic only)
- ⁺ → augmented chord
- ° → diminished chord
- ø⁷ → half-diminished 7th
- sus² → suspended 2
- sus⁴ → suspended 4
- ⁷ → seventh chord
- /X → bass note (slash notation)
- ½ → chromatic step up

## Status Flow
1. `uploaded` - File stored (PDF/images wait for OMR)
2. `converting_ocr` - Reading sheet music (Phase 2)
3. `converting_motesart` - Generating numbers
4. `completed` - Ready to view
5. `error` - Conversion failed

## Branded Template
All outputs include:
- Header: "Converted by Motesart Technologies — Motesart Number System v1.0"
- Logo: C → 1 concept image
- Song title and key signature
- Sections with progressions
- Symbol legend footer

## What's Been Implemented

### Phase 1.3 - January 16, 2026
- **File Type Support**: PDF, PNG, JPG, MIDI, MusicXML
- **Chord Chart Parsing**: Parse chord symbols from text
- **Status Flow**: uploaded → converting → completed → error
- **Branded Template**: Logo, header, sections, legend footer
- **Export Formats**: PDF, CSV, Text with branding
- **Dual Authentication**: Google OAuth + Email/Password

### Phase 1.4 - January 17, 2026 (Current)
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
- **UI Avatar Integration** ✅
  - Navbar displays user avatar with initials fallback
  - Crown icon for founder only
  - User dropdown shows avatar, display name, email
  - `computed_avatar` and `display_name` in all auth responses

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

## API Endpoints

### Authentication
- `POST /api/auth/register` - Email registration (returns avatar fields)
- `POST /api/auth/login` - Email login (returns avatar fields)
- `POST /api/auth/session` - Google OAuth session exchange
- `GET /api/auth/me` - Get current user with avatar
- `POST /api/auth/logout` - Clear session
- `PUT /api/auth/profile` - Update username/name
- `POST /api/auth/avatar` - Upload custom avatar
- `DELETE /api/auth/avatar` - Revert to default avatar

### Conversions
- `POST /api/upload` - Upload and convert file
- `GET /api/conversions` - List user's conversions
- `GET /api/conversions/{id}` - Get single conversion
- `DELETE /api/conversions/{id}` - Delete conversion
- `GET /api/conversions/{id}/file` - Get original file (for PDF/image display)

### Export
- `GET /api/export/{id}?format=pdf|csv|text` - Export with branding

### AI
- `POST /api/explain` - Generate AI explanation (GPT-5.2 via Emergent LLM Key)

## Test Credentials
- Regular user: `testuser@example.com` / `test123456`
- Founder user: `motesartproductions@gmail.com` / `founder123456`

## Prioritized Backlog

### P0 (Immediate - This Session)
- [x] Multi-user avatar system with unique icons
- [x] Founder special handling (crown, Motesart avatar)
- [ ] Clean up state on re-login (ensure selectedConversion resets)

### P1 (Phase 2)
- [ ] OMR integration (Audiveris/ScanScore) for PDF/image conversion
- [ ] Hymnal SATB analysis for bass line chord detection
- [ ] Airtable integration for T.A.M.i dashboard
- [ ] Leaderboard page with user avatars and rankings

### P2 (Future)
- [ ] Roman numeral side-by-side view
- [ ] Real-time playback
- [ ] Collaborative features
- [ ] Multiple avatar style options (DiceBear styles)

## Technical Notes

### Avatar Generation
Using DiceBear Initials API for unique avatars:
```
https://api.dicebear.com/7.x/initials/svg?seed={user_id}&chars=2&backgroundColor=6366f1,8b5cf6,06b6d4&textColor=ffffff
```

### Founder Detection
Email-based detection in `check_is_founder()`:
```python
MOTESART_FOUNDER_EMAIL = "motesartproductions@gmail.com"
```

### CORS Configuration
Fixed CORS to allow localhost:3000 with credentials:
```python
allow_origins=["http://localhost:3000", "https://music2numbers.preview.emergentagent.com"]
```

## Next Action Items
1. Address state reset issue on re-login (P1)
2. Plan Phase 2 OMR integration
3. Design leaderboard page with user avatars
