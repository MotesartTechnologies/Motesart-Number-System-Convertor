# Motesart Number System Converter - PRD

## Original Problem Statement
Build a multi-step "Motesart Number System Converter" app that:
- Ingests common music files (MIDI, MusicXML)
- Detects key, notes, chords, and structure
- Renders Motesart numbers with explanations in a clean dashboard

## User Personas
1. **Music Students** - Learning music theory through the number system
2. **Music Teachers** - Creating lesson materials and demonstrating concepts
3. **Musicians** - Analyzing songs and understanding chord progressions

## Core Requirements
- Upload MIDI and MusicXML files
- Auto-detect key signature (1 = tonic)
- Convert notes to Motesart numbers (1-7, half-numbers)
- Detect chords and progressions (2-5-1, 1-6-4-5)
- AI-powered explanations via GPT-5.2
- Export to PDF, Text, CSV

## What's Been Implemented (Phase 1 MVP) - January 16, 2026

### Authentication
- Emergent-managed Google OAuth integration
- Session-based authentication with httpOnly cookies
- Protected dashboard route

### Backend (FastAPI)
- File upload endpoint (MIDI/MusicXML)
- MIDI parser using mido library
- MusicXML parser using music21 library
- Key detection algorithm
- Note-to-number conversion (Motesart rules)
- Chord detection (Major, minor, 7ths, etc.)
- Progression recognition (2-5-1, 1-6-4-5, etc.)
- AI explanation endpoint (OpenAI GPT-5.2 via Emergent)
- Export endpoints (PDF, Text, CSV)

### Frontend (React)
- Dark analytics theme with neon accents
- Landing page with hero, features, CTA sections
- Dashboard with 3-column Bento Grid layout:
  - Left: Upload zone + Recent files
  - Center: Motesart view + Progressions strip
  - Right: AI Explain panel + Settings + Export
- File drag-and-drop upload
- Conversion history management
- Settings toggles (half-numbers, octave markers, roman numerals)

## Prioritized Backlog

### P0 (Critical) - Done
- [x] File upload and conversion
- [x] Key detection
- [x] Note-to-number mapping
- [x] Basic chord detection
- [x] User authentication
- [x] Export functionality

### P1 (Phase 2)
- [ ] Image/PDF OMR support (Optical Music Recognition)
- [ ] Key change detection mid-piece
- [ ] Piano roll visualization
- [ ] Airtable integration for T.A.M.i dashboard

### P2 (Future)
- [ ] Roman numeral side-by-side view
- [ ] Rhythm grid visualization
- [ ] Real-time playback with number highlighting
- [ ] Collaborative features (share conversions)

## Next Action Items
1. Add image/PDF support via external OMR API
2. Integrate with Airtable for T.A.M.i data logging
3. Add more sophisticated key change detection
4. Build piano roll visualization
