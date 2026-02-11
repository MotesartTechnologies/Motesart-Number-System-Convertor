import { useRef, useEffect, useMemo } from "react";

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
  
  // Major scale intervals: W W H W W W H (2,2,1,2,2,2,1 semitones)
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

  const styles = {
    container: {
      fontFamily: '"Segoe UI", Roboto, sans-serif',
      backgroundColor: printMode ? '#ffffff' : '#0a0a1a',
      color: printMode ? '#1f2937' : '#e5e7eb',
      padding: `${24 * zoom}px`,
      minHeight: '400px',
      transform: `scale(${zoom})`,
      transformOrigin: 'top left',
      width: zoom !== 1 ? `${100 / zoom}%` : '100%',
    },
    header: {
      marginBottom: `${24 * zoom}px`,
      borderBottom: `2px solid ${printMode ? '#d1d5db' : '#374151'}`,
      paddingBottom: `${16 * zoom}px`,
    },
    title: {
      fontSize: `${28 * zoom}px`,
      fontWeight: '700',
      color: printMode ? '#1f2937' : '#a78bfa',
      marginBottom: `${8 * zoom}px`,
    },
    artist: {
      fontSize: `${16 * zoom}px`,
      color: printMode ? '#6b7280' : '#9ca3af',
      marginBottom: `${8 * zoom}px`,
    },
    keyInfo: {
      fontSize: `${14 * zoom}px`,
      fontFamily: 'monospace',
      color: printMode ? '#b45309' : '#fbbf24',
      fontWeight: '600',
    },
    subtitle: {
      fontSize: `${11 * zoom}px`,
      color: printMode ? '#9ca3af' : '#6b7280',
      marginTop: `${8 * zoom}px`,
    },
    scaleRef: {
      backgroundColor: printMode ? '#f3f4f6' : '#1e1e2e',
      border: `1px solid ${printMode ? '#d1d5db' : '#374151'}`,
      borderRadius: `${8 * zoom}px`,
      padding: `${12 * zoom}px ${16 * zoom}px`,
      marginBottom: `${24 * zoom}px`,
    },
    scaleTitle: {
      fontSize: `${12 * zoom}px`,
      fontWeight: '600',
      color: printMode ? '#374151' : '#9ca3af',
      marginBottom: `${8 * zoom}px`,
    },
    scaleGrid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(4, 1fr)',
      gap: `${8 * zoom}px`,
      fontFamily: 'monospace',
      fontSize: `${13 * zoom}px`,
    },
    scaleItem: {
      color: printMode ? '#1f2937' : '#e5e7eb',
    },
    scaleNumber: {
      color: printMode ? '#b45309' : '#fbbf24',
      fontWeight: '700',
    },
    modifierLegend: {
      fontSize: `${11 * zoom}px`,
      color: printMode ? '#6b7280' : '#6b7280',
      marginTop: `${8 * zoom}px`,
    },
    section: {
      marginBottom: `${24 * zoom}px`,
    },
    sectionLabel: {
      fontSize: `${16 * zoom}px`,
      fontWeight: '700',
      color: printMode ? '#7c3aed' : '#a78bfa',
      marginBottom: `${12 * zoom}px`,
    },
    lineContainer: {
      marginBottom: `${16 * zoom}px`,
    },
    chordLine: {
      fontFamily: 'monospace',
      fontSize: `${18 * zoom}px`,
      fontWeight: '700',
      color: printMode ? '#b45309' : '#fbbf24',
      letterSpacing: '2px',
      marginBottom: `${4 * zoom}px`,
      whiteSpace: 'pre-wrap',
    },
    originalChordLine: {
      fontFamily: 'monospace',
      fontSize: `${12 * zoom}px`,
      color: printMode ? '#9ca3af' : '#6b7280',
      marginBottom: `${4 * zoom}px`,
      whiteSpace: 'pre-wrap',
    },
    lyricLine: {
      fontSize: `${15 * zoom}px`,
      color: printMode ? '#4b5563' : '#9ca3af',
      whiteSpace: 'pre-wrap',
    },
    progressionBox: {
      backgroundColor: printMode ? '#fef3c7' : 'rgba(251, 191, 36, 0.1)',
      border: `1px solid ${printMode ? '#fcd34d' : 'rgba(251, 191, 36, 0.3)'}`,
      borderRadius: `${6 * zoom}px`,
      padding: `${8 * zoom}px ${12 * zoom}px`,
      marginTop: `${8 * zoom}px`,
      fontFamily: 'monospace',
      fontSize: `${14 * zoom}px`,
    },
    progressionLabel: {
      fontSize: `${10 * zoom}px`,
      color: printMode ? '#92400e' : '#fbbf24',
      textTransform: 'uppercase',
      letterSpacing: '1px',
      marginBottom: `${4 * zoom}px`,
    },
    progressionChords: {
      color: printMode ? '#b45309' : '#fbbf24',
      fontWeight: '600',
    },
    legend: {
      marginTop: `${24 * zoom}px`,
      paddingTop: `${16 * zoom}px`,
      borderTop: `1px solid ${printMode ? '#e5e7eb' : '#374151'}`,
      fontSize: `${11 * zoom}px`,
      color: printMode ? '#6b7280' : '#6b7280',
    },
  };

  const sections = songData?.sections || [];
  const allChords = songData?.all_chords || songData?.chords || [];

  // If no sections but have chords, create a default section
  const displaySections = sections.length > 0 ? sections : 
    (allChords.length > 0 ? [{ name: 'Main', chords: allChords, lines: [] }] : []);

  if (!songData || displaySections.length === 0) {
    return (
      <div style={styles.container} ref={containerRef}>
        <div className="flex flex-col items-center justify-center h-64 text-slate-500">
          <p>No song data available for lead sheet view</p>
          <p className="text-sm mt-2">Use Manual Entry to add chords</p>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container} ref={containerRef} data-testid="lead-sheet-view">
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.title}>{songData.title || 'Untitled'}</div>
        {songData.artist && <div style={styles.artist}>{songData.artist}</div>}
        <div style={styles.keyInfo}>
          Key: {keySignature || 'C'} | 1 = {keySignature || 'C'} | Time: {timeSignature}
        </div>
        <div style={styles.subtitle}>
          Converted by Motesart Technologies — Motesart Number System v1.0
        </div>
      </div>

      {/* Scale Reference Box */}
      <div style={styles.scaleRef}>
        <div style={styles.scaleTitle}>Scale Reference:</div>
        <div style={styles.scaleGrid}>
          {[1, 2, 3, 4, 5, 6, 7].map(degree => (
            <div key={degree} style={styles.scaleItem}>
              <span style={styles.scaleNumber}>{degree}</span> = {scaleNotes[degree]}
            </div>
          ))}
          <div style={styles.scaleItem}>
            <span style={styles.scaleNumber}>½</span> = chromatic
          </div>
        </div>
        <div style={styles.modifierLegend}>
          m = minor | M = non-diatonic major | ⁷ = 7th | ° = dim | ⁺ = aug | sus = suspended | /X = bass note
        </div>
      </div>

      {/* Sections */}
      {displaySections.map((section, sIdx) => (
        <div key={sIdx} style={styles.section}>
          <div style={styles.sectionLabel}>[{section.name}]</div>
          
          {/* If section has lines with chords/lyrics */}
          {section.lines && section.lines.length > 0 ? (
            section.lines.map((line, lIdx) => (
              <div key={lIdx} style={styles.lineContainer}>
                {/* Chord line */}
                {(line.chords?.length > 0 || line.converted) && (
                  <>
                    <div style={styles.chordLine}>
                      {line.converted || line.chords?.map(c => c.symbol).join('   ') || ''}
                    </div>
                    {showOriginalChords && line.chords?.length > 0 && (
                      <div style={styles.originalChordLine}>
                        ({line.chords.map(c => c.original).join('   ')})
                      </div>
                    )}
                  </>
                )}
                {/* Lyric line */}
                {line.original && line.type === 'lyric_line' && (
                  <div style={styles.lyricLine}>{line.original}</div>
                )}
              </div>
            ))
          ) : (
            /* If section only has chords array */
            section.chords && section.chords.length > 0 && (
              <div style={styles.lineContainer}>
                <div style={styles.chordLine}>
                  {section.chords.map(c => c.symbol || c).join('   ')}
                </div>
                {showOriginalChords && (
                  <div style={styles.originalChordLine}>
                    ({section.chords.map(c => c.original || c).join('   ')})
                  </div>
                )}
              </div>
            )
          )}

          {/* Progression summary */}
          {section.progression && (
            <div style={styles.progressionBox}>
              <div style={styles.progressionLabel}>Progression</div>
              <div style={styles.progressionChords}>{section.progression}</div>
            </div>
          )}
        </div>
      ))}

      {/* Legend */}
      <div style={styles.legend}>
        Legend: 1-7 = scale degrees | ½ = chromatic (1½, 2½, 4½, 5½, 6½ only) | m = minor | 
        M = non-diatonic major | ⁷ ⁹ ¹¹ ¹³ = extensions | /X = bass note
      </div>
    </div>
  );
}

export default LeadSheetView;
