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

### Phase 1.4 - January 16, 2026 (CURRENT)
- **P0 Bug Fixes Completed:**
  - ✅ PDF export Unicode fix - Now uses DejaVu font for full Unicode support (½, ⁺, °, ⁹, ¹¹, ¹³)
  - ✅ Dashboard state reset - Properly clears when switching files or uploading new files
  - ✅ Phase 2 messaging - Clear UI communication that OMR is not yet active
  - ✅ CORS fix - Allows credentials-based requests from frontend
  - ✅ Logo integration - Motesart logo in navbar, login page, and empty dashboard state

### Phase 1.3 - January 16, 2026
- **File Type Support**: PDF, PNG, JPG, MIDI, MusicXML
- **Chord Chart Parsing**: Parse chord symbols from text
- **Status Flow**: uploaded → converting → completed → error
- **Branded Template**: Logo, header, sections, legend footer
- **Export Formats**: PDF, CSV, Text with branding
- **Authentication**: Google OAuth and email/password

## Testing Status
- All 17 backend tests passing
- All frontend features verified working
- Test credentials: test@test.com / test123

## Prioritized Backlog

### P0 (Phase 2 - Next Priority)
- [ ] OMR integration (Audiveris/ScanScore) for PDF/image conversion
- [ ] Real-time processing status updates via WebSocket

### P1 (Future)
- [ ] Enhanced AI Explain Panel with richer context
- [ ] Hymnal SATB analysis for bass line chord detection
- [ ] Airtable integration for T.A.M.i dashboard
- [ ] Key-change detection within a piece

### P2 (Backlog)
- [ ] Roman numeral side-by-side view
- [ ] Real-time playback
- [ ] Collaborative features
- [ ] Refactor server.py into modules (auth.py, conversion.py, parsers.py)
- [ ] Refactor Dashboard.jsx into smaller components

## Next Action Items
1. Implement OMR service for PDF/image to MusicXML conversion (Phase 2)
2. Add chord chart text extraction from PDF
3. Set up Airtable schema for T.A.M.i sync

## Technical Stack
- **Backend**: FastAPI, MongoDB (motor), Pydantic
- **Frontend**: React, Tailwind CSS, Shadcn/UI
- **Music Processing**: mido (MIDI), music21 (MusicXML)
- **Authentication**: JWT (email), Emergent Google OAuth
- **PDF Generation**: fpdf2 with DejaVu Unicode font
- **AI**: OpenAI GPT-5.2 via Emergent LLM Key
