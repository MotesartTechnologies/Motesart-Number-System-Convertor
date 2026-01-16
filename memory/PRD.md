# Motesart Number System Converter - PRD

## Original Problem Statement
Build a multi-step "Motesart Number System Converter" app that:
- Ingests sheet music (PDF, images) and music files (MIDI, MusicXML)
- Detects key, notes, chords, and structure
- Renders Motesart numbers with explanations in a clean dashboard
- Sheet-music-first approach with PDF/image as primary input

## Source of Truth
`THE-MOTESART-NUMBER-SYSTEM-1pg-Methedology.docx` - Latest methodology document

## User Personas
1. **Music Students** - Learning music theory through the number system
2. **Music Teachers** - Creating lesson materials and demonstrating concepts
3. **Musicians** - Analyzing songs and understanding chord progressions

## Core Methodology Rules

### Extensions (Section 5)
- Extensions do NOT introduce new numbers
- Written as superscripts: 2⁹, 4¹¹, 6¹³
- Think in 2, 4, 6 relative to scale; superscripts show upper-structure color

### Inversions (Section 7) - NEW SLASH RULE
- Format: BASS FIRST, CHORD SECOND
- 1/3 = 1 in bass, 3-chord above
- 1/5 = 1 in bass, 5-chord above
- 1/7 = 1 in bass, 7-chord above
- Optional: ² ³ superscripts for inversion markers (teaching use)

### Symbol Legend
- m → minor chord
- M → major chord (non-diatonic only)
- ⁺ → augmented chord
- ° → diminished chord
- ø⁷ → half-diminished 7th
- sus² → suspended 2
- sus⁴ → suspended 4
- ⁷ → seventh chord
- ⁹ ¹¹ ¹³ → extensions
- /X → bass note (slash notation)
- ½ → chromatic step up

## What's Been Implemented

### Phase 1 MVP - January 16, 2026
- MIDI and MusicXML parsing with key detection
- Note-to-number conversion with half-numbers
- Chord and progression detection
- Google OAuth + Email authentication
- Export to PDF/Text/CSV
- Dark analytics theme dashboard

### Phase 1.1 Updates - January 16, 2026
- Navigation: Home | Converter | Learn
- Learn page with full methodology documentation
- Email registration alongside Google Auth
- Sheet-music-first upload wording

### Phase 1.2 Updates - January 16, 2026 (Current)
- **Methodology Update**: Extensions (2⁹, 4¹¹, 6¹³) and Inversions (BASS FIRST slash rule)
- **PDF/Image Upload Fix**: Files now store and appear in Recent Files
- **Sheet Music Viewer**: Original file displayed for PDF/image uploads
- **Status Badges**: Uploaded | Processing | Converted | Error
- **New API**: /api/conversions/{id}/file for file retrieval

## Prioritized Backlog

### P0 (Critical) - Done ✓
- [x] File upload and conversion (MIDI/MusicXML)
- [x] PDF/Image upload and storage
- [x] Key detection and note-to-number mapping
- [x] Chord detection with new methodology
- [x] User authentication (Google + Email)
- [x] Export functionality
- [x] Navigation and Learn page

### P1 (Phase 2)
- [ ] OMR integration for PDF/image → MusicXML conversion
- [ ] Key change detection mid-piece
- [ ] Piano roll visualization
- [ ] Airtable integration for T.A.M.i dashboard

### P2 (Future)
- [ ] Roman numeral side-by-side view
- [ ] Real-time playback with number highlighting
- [ ] Collaborative features (share conversions)

## Next Action Items
1. Integrate OMR service (Audiveris/ScanScore) for PDF/image conversion
2. Set up Airtable schema (Users, Conversions, Pieces)
3. Add key change detection within pieces
4. Build piano roll visualization
