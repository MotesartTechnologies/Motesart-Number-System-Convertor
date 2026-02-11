import { useRef, useMemo } from "react";

// Get scale notes for a given key
const getScaleNotes = (key) => {
  const noteOrder = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
  const flatOrder = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B'];
  
  // Use flats for flat keys
  const useFlats = ['F', 'Bb', 'Eb', 'Ab', 'Db', 'Gb'].includes(key);
  const notes = useFlats ? flatOrder : noteOrder;
  
  // Find the key index
  let keyIndex = noteOrder.indexOf(key);
  if (keyIndex === -1) keyIndex = flatOrder.indexOf(key);
  if (keyIndex === -1) keyIndex = 0;
  
  // Major scale intervals: W W H W W W H
  const intervals = [0, 2, 4, 5, 7, 9, 11];
  
  const scaleNotes = {};
  intervals.forEach((interval, degree) => {
    const noteIndex = (keyIndex + interval) % 12;
    scaleNotes[degree + 1] = notes[noteIndex];
  });
  
  return scaleNotes;
};

export function LeadSheetView({ 
  songData, 
  keySignature,
  timeSignature = "4/4",
  printMode = false,
  showOriginalChords = false,
  zoom = 1 
}) {
  const containerRef = useRef(null);
  const scaleNotes = useMemo(() => getScaleNotes(keySignature || 'C'), [keySignature]);

  // Color scheme
  const colors = {
    bg: printMode ? '#ffffff' : '#0a0a1a',
    text: printMode ? '#1f2937' : '#e5e7eb',
    title: printMode ? '#7c3aed' : '#a78bfa',
    artist: printMode ? '#6b7280' : '#9ca3af',
    keyInfo: printMode ? '#b45309' : '#fbbf24',
    subtitle: printMode ? '#9ca3af' : '#6b7280',
    sectionLabel: printMode ? '#7c3aed' : '#a78bfa',
    chordNumber: printMode ? '#b45309' : '#fbbf24',
    lyric: printMode ? '#4b5563' : '#9ca3af',
    originalChord: printMode ? '#9ca3af' : '#6b7280',
    border: printMode ? '#d1d5db' : '#374151',
    cardBg: printMode ? '#f3f4f6' : '#1e1e2e',
    progressionBg: printMode ? '#fef3c7' : 'rgba(251, 191, 36, 0.1)',
    progressionBorder: printMode ? '#fcd34d' : 'rgba(251, 191, 36, 0.3)',
  };

  const sections = songData?.sections || [];
  const allChords = songData?.all_chords || songData?.chords || [];

  // If no sections but have chords, create a default section
  const displaySections = sections.length > 0 ? sections : 
    (allChords.length > 0 ? [{ name: 'Main', chords: allChords, lines: [] }] : []);

  if (!songData || displaySections.length === 0) {
    return (
      <div 
        ref={containerRef}
        className="flex flex-col items-center justify-center h-64"
        style={{ backgroundColor: colors.bg, color: colors.text }}
        data-testid="lead-sheet-view"
      >
        <p className="text-slate-500">No song data available for lead sheet view</p>
        <p className="text-sm mt-2 text-slate-600">Use Manual Entry to add chords</p>
      </div>
    );
  }

  // Format chord number for display with proper spacing
  const formatChordNumber = (chord) => {
    if (typeof chord === 'string') return chord;
    return chord?.symbol || chord?.root || '?';
  };

  // Render a line with chord-over-lyric alignment
  const renderChordLyricLine = (line, lineIdx) => {
    const chords = line.chords || [];
    const hasConvertedLine = line.converted && line.type === 'chord_line';
    const hasLyrics = line.type === 'lyric_line' && line.original;

    if (hasConvertedLine) {
      // This is a chord line - display the converted numbers
      return (
        <div key={lineIdx} style={{ marginBottom: `${12 * zoom}px` }}>
          <div 
            style={{
              fontFamily: 'monospace',
              fontSize: `${20 * zoom}px`,
              fontWeight: '700',
              color: colors.chordNumber,
              letterSpacing: '0.15em',
              lineHeight: 1.5,
            }}
          >
            {line.converted}
          </div>
          {showOriginalChords && chords.length > 0 && (
            <div 
              style={{
                fontFamily: 'monospace',
                fontSize: `${12 * zoom}px`,
                color: colors.originalChord,
                marginTop: `${2 * zoom}px`,
              }}
            >
              ({chords.map(c => c.original).join('   ')})
            </div>
          )}
        </div>
      );
    }

    if (hasLyrics) {
      // This is a lyric line
      return (
        <div 
          key={lineIdx}
          style={{
            fontSize: `${16 * zoom}px`,
            color: colors.lyric,
            lineHeight: 1.6,
            marginBottom: `${8 * zoom}px`,
          }}
        >
          {line.original}
        </div>
      );
    }

    return null;
  };

  // Render section chords in a grid if no lines
  const renderSectionChords = (chords) => {
    if (!chords || chords.length === 0) return null;

    return (
      <div style={{ marginBottom: `${16 * zoom}px` }}>
        <div 
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: `${16 * zoom}px`,
            fontFamily: 'monospace',
            fontSize: `${22 * zoom}px`,
            fontWeight: '700',
            color: colors.chordNumber,
          }}
        >
          {chords.map((chord, idx) => (
            <span 
              key={idx}
              style={{
                minWidth: `${40 * zoom}px`,
                textAlign: 'center',
              }}
            >
              {formatChordNumber(chord)}
            </span>
          ))}
        </div>
        {showOriginalChords && (
          <div 
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: `${16 * zoom}px`,
              fontFamily: 'monospace',
              fontSize: `${12 * zoom}px`,
              color: colors.originalChord,
              marginTop: `${4 * zoom}px`,
            }}
          >
            {chords.map((chord, idx) => (
              <span 
                key={idx}
                style={{
                  minWidth: `${40 * zoom}px`,
                  textAlign: 'center',
                }}
              >
                {chord?.original || ''}
              </span>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div 
      ref={containerRef} 
      data-testid="lead-sheet-view"
      style={{
        fontFamily: '"Segoe UI", Roboto, sans-serif',
        backgroundColor: colors.bg,
        color: colors.text,
        padding: `${24 * zoom}px`,
        minHeight: '400px',
        transform: `scale(${zoom})`,
        transformOrigin: 'top left',
        width: zoom !== 1 ? `${100 / zoom}%` : '100%',
      }}
    >
      {/* Header */}
      <div 
        style={{
          marginBottom: `${24 * zoom}px`,
          borderBottom: `2px solid ${colors.border}`,
          paddingBottom: `${16 * zoom}px`,
        }}
      >
        <div 
          style={{
            fontSize: `${28 * zoom}px`,
            fontWeight: '700',
            color: colors.title,
            marginBottom: `${8 * zoom}px`,
          }}
        >
          {songData.title || 'Untitled'}
        </div>
        {songData.artist && (
          <div 
            style={{
              fontSize: `${16 * zoom}px`,
              color: colors.artist,
              marginBottom: `${8 * zoom}px`,
            }}
          >
            {songData.artist}
          </div>
        )}
        <div 
          style={{
            fontSize: `${16 * zoom}px`,
            fontFamily: 'monospace',
            color: colors.keyInfo,
            fontWeight: '600',
          }}
        >
          1 = {keySignature || 'C'} | Time: {timeSignature}
        </div>
        <div 
          style={{
            fontSize: `${11 * zoom}px`,
            color: colors.subtitle,
            marginTop: `${8 * zoom}px`,
          }}
        >
          Converted by Motesart Technologies — Motesart Number System v1.0
        </div>
      </div>

      {/* Scale Reference Box */}
      <div 
        style={{
          backgroundColor: colors.cardBg,
          border: `1px solid ${colors.border}`,
          borderRadius: `${8 * zoom}px`,
          padding: `${12 * zoom}px ${16 * zoom}px`,
          marginBottom: `${24 * zoom}px`,
        }}
      >
        <div 
          style={{
            fontSize: `${12 * zoom}px`,
            fontWeight: '600',
            color: colors.subtitle,
            marginBottom: `${8 * zoom}px`,
          }}
        >
          Scale Reference:
        </div>
        <div 
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: `${8 * zoom}px`,
            fontFamily: 'monospace',
            fontSize: `${13 * zoom}px`,
          }}
        >
          {[1, 2, 3, 4, 5, 6, 7].map(degree => (
            <div key={degree} style={{ color: colors.text }}>
              <span style={{ color: colors.chordNumber, fontWeight: '700' }}>{degree}</span> = {scaleNotes[degree]}
            </div>
          ))}
          <div style={{ color: colors.text }}>
            <span style={{ color: colors.chordNumber, fontWeight: '700' }}>½</span> = chromatic
          </div>
        </div>
        <div 
          style={{
            fontSize: `${11 * zoom}px`,
            color: colors.subtitle,
            marginTop: `${8 * zoom}px`,
          }}
        >
          m = minor | M = non-diatonic major | ⁷ = 7th | ° = dim | ⁺ = aug | sus = suspended | /X = bass note
        </div>
      </div>

      {/* Sections */}
      {displaySections.map((section, sIdx) => (
        <div 
          key={sIdx} 
          style={{ marginBottom: `${28 * zoom}px` }}
          data-testid={`section-${section.name?.toLowerCase()?.replace(/\s+/g, '-') || sIdx}`}
        >
          {/* Section Label */}
          <div 
            style={{
              fontSize: `${18 * zoom}px`,
              fontWeight: '700',
              color: colors.sectionLabel,
              marginBottom: `${12 * zoom}px`,
            }}
          >
            [{section.name}]
          </div>
          
          {/* Lines with chords/lyrics */}
          {section.lines && section.lines.length > 0 ? (
            section.lines.map((line, lIdx) => renderChordLyricLine(line, lIdx))
          ) : (
            // Fallback: render chords array directly
            renderSectionChords(section.chords)
          )}

          {/* Progression summary box */}
          {section.progression && (
            <div 
              style={{
                backgroundColor: colors.progressionBg,
                border: `1px solid ${colors.progressionBorder}`,
                borderRadius: `${6 * zoom}px`,
                padding: `${8 * zoom}px ${12 * zoom}px`,
                marginTop: `${12 * zoom}px`,
              }}
            >
              <div 
                style={{
                  fontSize: `${10 * zoom}px`,
                  color: colors.keyInfo,
                  textTransform: 'uppercase',
                  letterSpacing: '1px',
                  marginBottom: `${4 * zoom}px`,
                }}
              >
                Progression
              </div>
              <div 
                style={{
                  fontFamily: 'monospace',
                  fontSize: `${14 * zoom}px`,
                  fontWeight: '600',
                  color: colors.chordNumber,
                }}
              >
                {section.progression}
              </div>
            </div>
          )}
        </div>
      ))}

      {/* Legend */}
      <div 
        style={{
          marginTop: `${24 * zoom}px`,
          paddingTop: `${16 * zoom}px`,
          borderTop: `1px solid ${colors.border}`,
          fontSize: `${11 * zoom}px`,
          color: colors.subtitle,
        }}
      >
        Legend: 1-7 = scale degrees | ½ = chromatic (1½, 2½, 4½, 5½, 6½ only) | m = minor | 
        M = non-diatonic major | ⁷ ⁹ ¹¹ ¹³ = extensions | /X = bass note
      </div>
    </div>
  );
}

export default LeadSheetView;
