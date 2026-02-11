import { useRef, useEffect, useState } from "react";

// Staff configuration
const STAFF_CONFIG = {
  lineSpacing: 12,
  noteSize: 18,
  chordSize: 16,
  lyricSize: 14,
  measureWidth: 180,
  staffMarginTop: 60,
  staffMarginBottom: 50,
  measuresPerLine: 4,
  systemHeight: 160,
  leftMargin: 40,
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
// Degree 1 = middle of staff, going up and down from there
const degreeToStaffPosition = (degree, octave = 0) => {
  // Base positions: 1=0, 2=1, 3=2, 4=3, 5=4, 6=5, 7=6
  const basePosition = degree - 1;
  return basePosition + (octave * 7);
};

// Convert staff position to Y coordinate
const staffPositionToY = (position, staffTopY) => {
  // Position 0 (degree 1) = bottom line of staff
  // Each position moves up half a line spacing
  const staffMiddle = staffTopY + (STAFF_CONFIG.lineSpacing * 2);
  return staffMiddle - (position * (STAFF_CONFIG.lineSpacing / 2));
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

    // Calculate dimensions
    const measures = songData.measures || [];
    const sections = songData.sections || [];
    
    // If we have sections instead of measures, convert to measures
    let allMeasures = measures;
    if (allMeasures.length === 0 && sections.length > 0) {
      allMeasures = [];
      sections.forEach(section => {
        // Add section marker
        allMeasures.push({ sectionLabel: section.name, isSection: true });
        // Add chords from section
        if (section.chords) {
          section.chords.forEach((chord, idx) => {
            allMeasures.push({
              chord: chord.symbol,
              originalChord: chord.original,
              notes: [{ degree: parseInt(chord.root) || 1, display: chord.symbol }]
            });
          });
        }
      });
    }

    // If still no measures, create placeholder
    if (allMeasures.length === 0) {
      allMeasures = [{ chord: "1", notes: [{ degree: 1, display: "1" }], lyric: "No data" }];
    }

    const measuresPerLine = STAFF_CONFIG.measuresPerLine;
    const systems = Math.ceil(allMeasures.length / measuresPerLine);
    
    const canvasWidth = 800 * zoom;
    const canvasHeight = (systems * STAFF_CONFIG.systemHeight + 120) * zoom;
    
    canvas.width = canvasWidth;
    canvas.height = canvasHeight;
    
    // Scale context
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

    // Draw "Converted by Motesart Technologies" subtitle
    ctx.fillStyle = lyricColor;
    ctx.font = '11px sans-serif';
    ctx.fillText('Converted by Motesart Technologies — Motesart Number System v1.0', STAFF_CONFIG.leftMargin, 78);

    let y = 100;
    let measureIndex = 0;

    for (let sys = 0; sys < systems; sys++) {
      const staffTopY = y;
      
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

      // Draw treble clef symbol (simplified)
      ctx.fillStyle = lineColor;
      ctx.font = '48px serif';
      ctx.fillText('𝄞', STAFF_CONFIG.leftMargin + 5, staffTopY + 38);

      // Calculate measure positions
      const measureStartX = STAFF_CONFIG.leftMargin + 50;
      const availableWidth = 800 - STAFF_CONFIG.rightMargin - measureStartX;
      const measureWidth = availableWidth / measuresPerLine;

      // Draw measures for this system
      const startMeasure = sys * measuresPerLine;
      const endMeasure = Math.min(startMeasure + measuresPerLine, allMeasures.length);

      for (let m = startMeasure; m < endMeasure; m++) {
        const mx = measureStartX + (m - startMeasure) * measureWidth;
        const measure = allMeasures[m];

        if (!measure) continue;

        // Draw bar line at start of measure
        if (m > startMeasure || sys > 0) {
          ctx.strokeStyle = STAFF_CONFIG.colors.barLines;
          ctx.lineWidth = 1.5;
          ctx.beginPath();
          ctx.moveTo(mx, staffTopY);
          ctx.lineTo(mx, staffTopY + STAFF_CONFIG.lineSpacing * 4);
          ctx.stroke();
        }

        // Section label
        if (measure.isSection && measure.sectionLabel) {
          ctx.fillStyle = chordColor;
          ctx.font = 'bold 14px sans-serif';
          ctx.fillText(`[${measure.sectionLabel}]`, mx + 5, staffTopY - 25);
          continue;
        }

        // Draw chord number above staff
        if (measure.chord) {
          ctx.fillStyle = chordColor;
          ctx.font = 'bold 16px monospace';
          const chordText = measure.chord;
          ctx.fillText(chordText, mx + 10, staffTopY - 10);
          
          // Show original chord if enabled
          if (showOriginalChords && measure.originalChord) {
            ctx.fillStyle = lyricColor;
            ctx.font = '12px monospace';
            ctx.fillText(`(${measure.originalChord})`, mx + 10, staffTopY - 25);
          }
        }

        // Draw note numbers on staff
        if (measure.notes && measure.notes.length > 0) {
          const noteSpacing = (measureWidth - 20) / Math.max(measure.notes.length, 1);
          
          measure.notes.forEach((note, ni) => {
            const noteX = mx + 15 + ni * noteSpacing;
            const degree = note.degree || 1;
            const staffPos = degreeToStaffPosition(degree);
            const noteY = staffPositionToY(staffPos, staffTopY);

            // Draw the number
            ctx.fillStyle = numberColor;
            ctx.font = 'bold 20px monospace';
            const displayText = note.display || degree.toString();
            ctx.fillText(displayText, noteX, noteY + 6);

            // Draw ledger lines if needed
            if (staffPos < 0 || staffPos > 8) {
              ctx.strokeStyle = lineColor;
              ctx.lineWidth = 1;
              // Below staff
              if (staffPos < 0) {
                for (let l = -2; l >= staffPos; l -= 2) {
                  const ledgerY = staffPositionToY(l, staffTopY);
                  ctx.beginPath();
                  ctx.moveTo(noteX - 5, ledgerY);
                  ctx.lineTo(noteX + 20, ledgerY);
                  ctx.stroke();
                }
              }
              // Above staff
              if (staffPos > 8) {
                for (let l = 10; l <= staffPos; l += 2) {
                  const ledgerY = staffPositionToY(l, staffTopY);
                  ctx.beginPath();
                  ctx.moveTo(noteX - 5, ledgerY);
                  ctx.lineTo(noteX + 20, ledgerY);
                  ctx.stroke();
                }
              }
            }
          });
        }

        // Draw lyrics below staff
        if (measure.lyric) {
          ctx.fillStyle = lyricColor;
          ctx.font = '13px sans-serif';
          ctx.fillText(measure.lyric, mx + 8, staffTopY + STAFF_CONFIG.lineSpacing * 4 + 25);
        }
      }

      // Final bar line (double bar at end)
      const lastX = measureStartX + (endMeasure - startMeasure) * measureWidth;
      ctx.strokeStyle = STAFF_CONFIG.colors.barLines;
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(lastX, staffTopY);
      ctx.lineTo(lastX, staffTopY + STAFF_CONFIG.lineSpacing * 4);
      ctx.stroke();

      if (sys === systems - 1) {
        // Double bar at the very end
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
      'Legend: 1-7 = scale degrees | ½ = chromatic | m = minor | M = non-diatonic major | ⁷ ⁹ ¹¹ ¹³ = extensions | /X = bass note',
      STAFF_CONFIG.leftMargin,
      legendY
    );

    if (onCanvasReady) {
      onCanvasReady(canvas);
    }

  }, [songData, keySignature, timeSignature, printMode, showOriginalChords, zoom, onCanvasReady]);

  if (!songData) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-500">
        No song data available for staff notation view
      </div>
    );
  }

  return (
    <div ref={containerRef} className="overflow-auto">
      <canvas 
        ref={canvasRef} 
        className="block mx-auto"
        style={{ maxWidth: '100%', height: 'auto' }}
      />
    </div>
  );
}

export default StaffNotationView;
