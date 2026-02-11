import { useRef, useEffect } from "react";

// Staff configuration
const STAFF_CONFIG = {
  lineSpacing: 12,
  noteSize: 18,
  chordSize: 16,
  lyricSize: 14,
  measureWidth: 160,
  staffMarginTop: 60,
  staffMarginBottom: 60,
  measuresPerLine: 4,
  systemHeight: 180,
  leftMargin: 50,
  rightMargin: 30,
  colors: {
    staffLines: '#555555',
    numbers: '#fbbf24',
    chords: '#a78bfa',
    lyrics: '#9ca3af',
    barLines: '#666666',
    background: '#0a0a1a',
    backgroundPrint: '#ffffff',
    textPrint: '#000000',
  }
};

// Map scale degree to staff position (line/space from bottom)
const degreeToStaffPosition = (degree, octave = 0) => {
  // Map degrees 1-7 to staff positions
  // Degree 1 sits on the bottom line, going up
  const basePosition = degree - 1;
  return basePosition + (octave * 7);
};

// Convert staff position to Y coordinate
const staffPositionToY = (position, staffTopY) => {
  const staffBottom = staffTopY + (STAFF_CONFIG.lineSpacing * 4);
  return staffBottom - (position * (STAFF_CONFIG.lineSpacing / 2));
};

export function StaffNotationView({ 
  songData, 
  keySignature, 
  timeSignature = "4/4",
  printMode = false,
  showOriginalChords = false,
  zoom = 1,
  onCanvasReady 
}) {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    if (!canvasRef.current || !songData) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    const bgColor = printMode ? STAFF_CONFIG.colors.backgroundPrint : STAFF_CONFIG.colors.background;
    const textColor = printMode ? STAFF_CONFIG.colors.textPrint : '#ffffff';
    const numberColor = printMode ? '#b45309' : STAFF_CONFIG.colors.numbers;
    const chordColor = printMode ? '#7c3aed' : STAFF_CONFIG.colors.chords;
    const lyricColor = printMode ? '#4b5563' : STAFF_CONFIG.colors.lyrics;
    const lineColor = printMode ? '#374151' : STAFF_CONFIG.colors.staffLines;

    // Build measures from sections
    const sections = songData.sections || [];
    const allChords = songData.all_chords || [];
    
    // Create a flat list of items to render
    let renderItems = [];
    
    if (sections.length > 0) {
      sections.forEach((section, sIdx) => {
        // Add section header
        renderItems.push({ type: 'section', name: section.name });
        
        // Add lines from section (if available)
        const lines = section.lines || [];
        if (lines.length > 0) {
          lines.forEach(line => {
            if (line.type === 'chord_line' && line.chords?.length > 0) {
              line.chords.forEach(chord => {
                renderItems.push({
                  type: 'chord',
                  symbol: chord.symbol || chord,
                  original: chord.original || '',
                  root: parseInt((chord.symbol || chord).replace(/[^\d]/g, '')) || 1
                });
              });
            } else if (line.type === 'lyric_line' && line.original) {
              renderItems.push({ type: 'lyric', text: line.original });
            }
          });
        } else if (section.chords?.length > 0) {
          // Fallback to chords array
          section.chords.forEach(chord => {
            renderItems.push({
              type: 'chord',
              symbol: chord.symbol || chord,
              original: chord.original || '',
              root: parseInt((chord.symbol || chord).replace(/[^\d]/g, '')) || 1
            });
          });
        }
      });
    } else if (allChords.length > 0) {
      // No sections, just render all chords
      allChords.forEach(chord => {
        renderItems.push({
          type: 'chord',
          symbol: chord.symbol || chord,
          original: chord.original || '',
          root: parseInt((chord.symbol || chord).replace(/[^\d]/g, '')) || 1
        });
      });
    }

    // If nothing to render, show placeholder
    if (renderItems.length === 0) {
      renderItems = [{ type: 'chord', symbol: '1', original: 'C', root: 1 }];
    }

    // Group items into systems (staff lines)
    const chordsOnly = renderItems.filter(i => i.type === 'chord');
    const measuresPerLine = STAFF_CONFIG.measuresPerLine;
    const systems = Math.ceil(chordsOnly.length / measuresPerLine);
    const totalSystems = Math.max(systems, 2);

    const canvasWidth = 800 * zoom;
    const canvasHeight = (totalSystems * STAFF_CONFIG.systemHeight + 140) * zoom;
    
    canvas.width = canvasWidth;
    canvas.height = canvasHeight;
    
    ctx.scale(zoom, zoom);

    // Clear background
    ctx.fillStyle = bgColor;
    ctx.fillRect(0, 0, canvasWidth / zoom, canvasHeight / zoom);

    // Draw header
    ctx.fillStyle = chordColor;
    ctx.font = 'bold 22px Georgia, serif';
    ctx.fillText(songData.title || 'Untitled', STAFF_CONFIG.leftMargin, 35);

    // Key and time signature
    ctx.fillStyle = numberColor;
    ctx.font = 'bold 16px monospace';
    ctx.fillText(`1 = ${keySignature || 'C'}`, STAFF_CONFIG.leftMargin, 58);
    
    ctx.fillStyle = textColor;
    ctx.font = '14px monospace';
    ctx.fillText(`Time: ${timeSignature}`, STAFF_CONFIG.leftMargin + 100, 58);

    // Branding subtitle
    ctx.fillStyle = lyricColor;
    ctx.font = '11px sans-serif';
    ctx.fillText('Converted by Motesart Technologies', STAFF_CONFIG.leftMargin, 78);

    let y = 110;
    let chordIndex = 0;
    let currentSection = null;

    // Track which items we're on
    let itemIdx = 0;

    for (let sys = 0; sys < totalSystems && chordIndex < chordsOnly.length; sys++) {
      const staffTopY = y;
      
      // Check for section header at this position
      while (itemIdx < renderItems.length && renderItems[itemIdx].type !== 'chord') {
        const item = renderItems[itemIdx];
        if (item.type === 'section') {
          currentSection = item.name;
          // Draw section label above staff
          ctx.fillStyle = chordColor;
          ctx.font = 'bold 14px sans-serif';
          ctx.fillText(`[${item.name}]`, STAFF_CONFIG.leftMargin, staffTopY - 15);
        }
        itemIdx++;
      }

      // Draw 5 staff lines
      ctx.strokeStyle = lineColor;
      ctx.lineWidth = 1;
      for (let line = 0; line < 5; line++) {
        const lineY = staffTopY + line * STAFF_CONFIG.lineSpacing;
        ctx.beginPath();
        ctx.moveTo(STAFF_CONFIG.leftMargin, lineY);
        ctx.lineTo(800 - STAFF_CONFIG.rightMargin, lineY);
        ctx.stroke();
      }

      // Draw treble clef
      ctx.fillStyle = lineColor;
      ctx.font = '48px serif';
      ctx.fillText('𝄞', STAFF_CONFIG.leftMargin + 5, staffTopY + 38);

      // Calculate measure positions
      const measureStartX = STAFF_CONFIG.leftMargin + 55;
      const availableWidth = 800 - STAFF_CONFIG.rightMargin - measureStartX - 10;
      const measureWidth = availableWidth / measuresPerLine;

      // Draw measures for this system
      const startChordIdx = chordIndex;
      const endChordIdx = Math.min(startChordIdx + measuresPerLine, chordsOnly.length);

      for (let m = startChordIdx; m < endChordIdx; m++) {
        const mx = measureStartX + (m - startChordIdx) * measureWidth;
        const chord = chordsOnly[m];

        // Draw bar line at start of measure (except first)
        if (m > startChordIdx) {
          ctx.strokeStyle = STAFF_CONFIG.colors.barLines;
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(mx, staffTopY);
          ctx.lineTo(mx, staffTopY + STAFF_CONFIG.lineSpacing * 4);
          ctx.stroke();
        }

        // Draw chord number ABOVE the staff
        ctx.fillStyle = numberColor;
        ctx.font = 'bold 18px monospace';
        ctx.fillText(chord.symbol, mx + 15, staffTopY - 5);

        // Show original chord if enabled
        if (showOriginalChords && chord.original) {
          ctx.fillStyle = lyricColor;
          ctx.font = '11px monospace';
          ctx.fillText(`(${chord.original})`, mx + 15, staffTopY - 20);
        }

        // Draw a simple note position on the staff based on root
        const degree = chord.root || 1;
        const staffPos = degreeToStaffPosition(degree);
        const noteY = staffPositionToY(staffPos, staffTopY);

        // Draw a small circle to represent note position
        ctx.beginPath();
        ctx.arc(mx + measureWidth / 2, noteY, 6, 0, Math.PI * 2);
        ctx.fillStyle = numberColor;
        ctx.fill();

        // Draw the number inside/next to the note
        ctx.fillStyle = printMode ? '#ffffff' : '#0a0a1a';
        ctx.font = 'bold 10px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(degree.toString(), mx + measureWidth / 2, noteY + 4);
        ctx.textAlign = 'left';

        // Draw ledger lines if needed
        if (staffPos < 0) {
          ctx.strokeStyle = lineColor;
          ctx.lineWidth = 1;
          for (let l = -2; l >= staffPos; l -= 2) {
            const ledgerY = staffPositionToY(l, staffTopY);
            ctx.beginPath();
            ctx.moveTo(mx + measureWidth / 2 - 10, ledgerY);
            ctx.lineTo(mx + measureWidth / 2 + 10, ledgerY);
            ctx.stroke();
          }
        }
        if (staffPos > 8) {
          ctx.strokeStyle = lineColor;
          ctx.lineWidth = 1;
          for (let l = 10; l <= staffPos; l += 2) {
            const ledgerY = staffPositionToY(l, staffTopY);
            ctx.beginPath();
            ctx.moveTo(mx + measureWidth / 2 - 10, ledgerY);
            ctx.lineTo(mx + measureWidth / 2 + 10, ledgerY);
            ctx.stroke();
          }
        }

        chordIndex++;
        itemIdx++;
      }

      // Final bar line
      const lastX = measureStartX + (endChordIdx - startChordIdx) * measureWidth;
      ctx.strokeStyle = STAFF_CONFIG.colors.barLines;
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(lastX, staffTopY);
      ctx.lineTo(lastX, staffTopY + STAFF_CONFIG.lineSpacing * 4);
      ctx.stroke();

      // Double bar at the end of the piece
      if (chordIndex >= chordsOnly.length) {
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(lastX + 4, staffTopY);
        ctx.lineTo(lastX + 4, staffTopY + STAFF_CONFIG.lineSpacing * 4);
        ctx.stroke();
      }

      y += STAFF_CONFIG.systemHeight;
    }

    // Draw legend at bottom
    const legendY = y + 10;
    ctx.fillStyle = lyricColor;
    ctx.font = '11px sans-serif';
    ctx.fillText(
      'Legend: 1-7 = scale degrees | Numbers shown on staff positions | m = minor | M = non-diatonic major',
      STAFF_CONFIG.leftMargin,
      legendY
    );

    if (onCanvasReady) {
      onCanvasReady(canvas);
    }

  }, [songData, keySignature, timeSignature, printMode, showOriginalChords, zoom, onCanvasReady]);

  if (!songData) {
    return (
      <div 
        className="flex flex-col items-center justify-center h-64 text-slate-500"
        data-testid="staff-notation-view"
      >
        <p>No song data available for staff notation view</p>
        <p className="text-sm mt-2">Upload sheet music or use Manual Entry</p>
      </div>
    );
  }

  return (
    <div ref={containerRef} className="overflow-auto" data-testid="staff-notation-view">
      <canvas 
        ref={canvasRef} 
        className="block mx-auto"
        style={{ maxWidth: '100%', height: 'auto' }}
      />
    </div>
  );
}

export default StaffNotationView;
