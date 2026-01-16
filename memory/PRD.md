# Motesart Number System Converter - PRD

## Original Problem Statement
Build a multi-step "Motesart Number System Converter" app that:
- Ingests sheet music (PDF, images) and music files (MIDI, MusicXML)
- Detects key, notes, chords, and structure
- Renders Motesart numbers with explanations in a clean dashboard
- Sheet-music-first approach with PDF/image as primary input

## User Personas
1. **Music Students** - Learning music theory through the number system
2. **Music Teachers** - Creating lesson materials and demonstrating concepts
3. **Musicians** - Analyzing songs and understanding chord progressions

## Core Requirements
- Upload sheet music (PDF, image) and music files (MIDI, MusicXML)
- Auto-detect key signature (1 = tonic)
- Convert notes to Motesart numbers (1-7, half-numbers)
- Detect chords and progressions (2-5-1, 1-6-4-5)
- AI-powered explanations via GPT-5.2
- Export to PDF, CSV, Print

## What's Been Implemented

### Phase 1 MVP - January 16, 2026
- MIDI and MusicXML parsing
- Key detection and note-to-number conversion
- Basic chord and progression detection
- Google OAuth authentication
- Export to PDF/Text/CSV
- Dark analytics theme dashboard

### Phase 1.1 Updates - January 16, 2026
- **Navigation**: Added persistent navbar (Home | Converter | Learn)
- **Home Page**: Updated hero "See Your Sheet Music in Numbers" with sheet-music-first messaging
- **Learn Page**: Full methodology documentation with:
  - "What is Motesart Methodology?" explanations
  - Key mappings for all major keys (1=C through 1=Eb)
  - Common progressions (2-5-1, 1-6-4-5, etc.) with song examples
  - Half-numbers reference (1½, 2½, 4½, 5½, 6½)
  - Symbol quick reference (m, M, 7, /, °, +, sus)
- **Auth Flow**: Added email registration alongside Google OAuth
- **Upload Section**: Sheet-music-first wording ("Upload Sheet Music")
- **Recent Files**: Enhanced display with Title, Type, Key, Date columns

## Prioritized Backlog

### P0 (Critical) - Done
- [x] File upload and conversion (MIDI/MusicXML)
- [x] Key detection
- [x] Note-to-number mapping
- [x] Basic chord detection
- [x] User authentication (Google + Email)
- [x] Export functionality
- [x] Navigation and Learn page

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
1. Add OMR support for PDF/image sheet music
2. Integrate with Airtable for T.A.M.i data logging
3. Add key change detection within pieces
4. Build piano roll visualization
