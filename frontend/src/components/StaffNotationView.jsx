import { useRef, useEffect, useState } from "react";
import { Button } from "../components/ui/button";
import { Loader2, RefreshCw, ZoomIn, ZoomOut } from "lucide-react";

// Staff configuration
const STAFF_CONFIG = {
  lineSpacing: 10,
  noteSize: 14,
  measureWidth: 140,
  staffMarginTop: 80,
  leftMargin: 60,
  rightMargin: 30,
  systemSpacing: 120,
  beatsPerMeasure: 4,
  colors: {
    staffLines: '#555555',
    numbers: '#fbbf24',
    lyrics: '#9ca3af',
    barLines: '#666666',
    background: '#0a0a1a',
    backgroundPrint: '#ffffff',
    textPrint: '#1f2937',
    title: '#a78bfa',
  }
};

// MIDI pitch to staff position (relative to middle C = 60)
const midiToStaffPosition = (midi) => {
  // Middle C (60) = position 0 (middle of staff)
  // Each step up/down = 1 position
  const c4 = 60;
  const noteInOctave = midi % 12;
  const octave = Math.floor(midi / 12) - 4; // Octave relative to C4
  
  // Note positions within octave (C D E F G A B)
  const notePositions = [0, 1, 1, 2, 2, 3, 4, 4, 5, 5, 6, 6]; // Accounting for sharps/flats
  const basePosition = notePositions[noteInOctave];
  
  return basePosition + (octave * 7);
};

// Staff position to Y coordinate
const staffPositionToY = (position, staffTopY, lineSpacing) => {
  // Position 0 = middle C (one ledger line below staff)
  // Position 5 = G4 (2nd line from bottom)
  // Position -2 = A3
  const middleLine = staffTopY + (lineSpacing * 2); // Middle line of staff (B4)
  return middleLine - (position * (lineSpacing / 2));
};

export function StaffNotationView({ 
  songData, 
  keySignature, 
  timeSignature = "4/4",
  printMode = false,
  showOriginalChords = false,
  zoom = 1,
  omrNotes = [],
  omrMeasures = [],
  omrLyrics = [],
  isProcessing = false,
  onProcessOMR = null,
}) {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    if (!canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    const bgColor = printMode ? STAFF_CONFIG.colors.backgroundPrint : STAFF_CONFIG.colors.background;
    const textColor = printMode ? STAFF_CONFIG.colors.textPrint : '#ffffff';
    const numberColor = printMode ? '#b45309' : STAFF_CONFIG.colors.numbers;
    const lyricColor = printMode ? '#4b5563' : STAFF_CONFIG.colors.lyrics;
    const lineColor = printMode ? '#374151' : STAFF_CONFIG.colors.staffLines;
    const titleColor = printMode ? '#7c3aed' : STAFF_CONFIG.colors.title;

    // Use OMR notes if available, otherwise fall back to chord-based notes
    const notes = omrNotes.length > 0 ? omrNotes : (songData?.notes || []);
    const measures = omrMeasures.length > 0 ? omrMeasures : (songData?.measures || []);
    const title = songData?.title || 'Untitled';
    
    // Calculate canvas dimensions
    const measuresPerLine = 4;
    const totalMeasures = measures.length || Math.ceil(notes.length / 4) || 4;
    const numSystems = Math.ceil(totalMeasures / measuresPerLine);
    
    const canvasWidth = 800 * zoom;
    const canvasHeight = Math.max(400, (numSystems * STAFF_CONFIG.systemSpacing + 150)) * zoom;
    
    canvas.width = canvasWidth;
    canvas.height = canvasHeight;
    
    ctx.scale(zoom, zoom);

    // Clear background
    ctx.fillStyle = bgColor;
    ctx.fillRect(0, 0, canvasWidth / zoom, canvasHeight / zoom);

    // Draw header
    ctx.fillStyle = titleColor;
    ctx.font = 'bold 24px Georgia, serif';
    ctx.fillText(title, STAFF_CONFIG.leftMargin, 35);

    // Key and time signature
    ctx.fillStyle = numberColor;
    ctx.font = 'bold 16px monospace';
    ctx.fillText(`1 = ${keySignature || 'C'}`, STAFF_CONFIG.leftMargin, 58);
    
    ctx.fillStyle = textColor;
    ctx.font = '14px monospace';
    ctx.fillText(`Time: ${timeSignature}`, STAFF_CONFIG.leftMargin + 100, 58);

    // Branding
    ctx.fillStyle = lyricColor;
    ctx.font = '10px sans-serif';
    ctx.fillText('Converted by Motesart Technologies', STAFF_CONFIG.leftMargin, 75);

    // If no notes, show placeholder
    if (notes.length === 0 && measures.length === 0) {
      ctx.fillStyle = lyricColor;
      ctx.font = '14px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('No notes detected. Click "Process OMR" to extract notes from sheet music.', canvasWidth / (2 * zoom), 150);
      ctx.textAlign = 'left';
      return;
    }

    // Draw systems (groups of staff lines)
    let noteIndex = 0;
    let measureIndex = 0;
    
    for (let sys = 0; sys < numSystems; sys++) {
      const staffTopY = STAFF_CONFIG.staffMarginTop + (sys * STAFF_CONFIG.systemSpacing);
      
      // Draw 5 staff lines
      ctx.strokeStyle = lineColor;
      ctx.lineWidth = 1;
      for (let line = 0; line < 5; line++) {
        const lineY = staffTopY + (line * STAFF_CONFIG.lineSpacing);
        ctx.beginPath();
        ctx.moveTo(STAFF_CONFIG.leftMargin, lineY);
        ctx.lineTo(canvasWidth / zoom - STAFF_CONFIG.rightMargin, lineY);
        ctx.stroke();
      }

      // Draw treble clef
      ctx.fillStyle = lineColor;
      ctx.font = '42px serif';
      ctx.fillText('𝄞', STAFF_CONFIG.leftMargin + 2, staffTopY + 32);

      // Calculate measure positions for this system
      const measureStartX = STAFF_CONFIG.leftMargin + 45;
      const availableWidth = canvasWidth / zoom - STAFF_CONFIG.rightMargin - measureStartX;
      const measureWidth = availableWidth / measuresPerLine;

      // Draw measures for this system
      for (let m = 0; m < measuresPerLine && measureIndex < totalMeasures; m++) {
        const measureX = measureStartX + (m * measureWidth);
        
        // Draw bar line
        if (m > 0) {
          ctx.strokeStyle = STAFF_CONFIG.colors.barLines;
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(measureX, staffTopY);
          ctx.lineTo(measureX, staffTopY + STAFF_CONFIG.lineSpacing * 4);
          ctx.stroke();
        }

        // Get notes for this measure
        const measureData = measures[measureIndex];
        const measureNotes = measureData?.notes || [];
        
        // If no measure data, try to distribute notes evenly
        const notesToDraw = measureNotes.length > 0 ? measureNotes : 
          notes.slice(noteIndex, noteIndex + 4);
        
        // Draw notes in this measure
        const notesInMeasure = notesToDraw.length || 4;
        const noteSpacing = measureWidth / (notesInMeasure + 1);
        
        for (let n = 0; n < notesToDraw.length; n++) {
          const note = notesToDraw[n];
          const noteX = measureX + noteSpacing * (n + 1);
          
          // Calculate Y position based on pitch
          let noteY;
          if (note.midi) {
            const staffPos = midiToStaffPosition(note.midi);
            noteY = staffPositionToY(staffPos, staffTopY, STAFF_CONFIG.lineSpacing);
          } else {
            // Default to middle of staff
            noteY = staffTopY + STAFF_CONFIG.lineSpacing * 2;
          }
          
          // Draw note head (filled oval)
          ctx.beginPath();
          ctx.ellipse(noteX, noteY, 8, 6, 0, 0, Math.PI * 2);
          ctx.fillStyle = numberColor;
          ctx.fill();
          ctx.strokeStyle = printMode ? '#000' : '#fff';
          ctx.lineWidth = 1;
          ctx.stroke();
          
          // Draw Motesart number on note
          const motesartNum = note.motesart || '?';
          ctx.fillStyle = printMode ? '#fff' : '#0a0a1a';
          ctx.font = 'bold 9px monospace';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText(motesartNum, noteX, noteY);
          ctx.textAlign = 'left';
          ctx.textBaseline = 'alphabetic';
          
          // Draw stem
          const stemDirection = noteY < staffTopY + STAFF_CONFIG.lineSpacing * 2 ? 1 : -1;
          ctx.strokeStyle = numberColor;
          ctx.lineWidth = 1.5;
          ctx.beginPath();
          ctx.moveTo(noteX + (stemDirection > 0 ? 7 : -7), noteY);
          ctx.lineTo(noteX + (stemDirection > 0 ? 7 : -7), noteY + (stemDirection * 30));
          ctx.stroke();
          
          // Draw ledger lines if needed
          const staffBottom = staffTopY + STAFF_CONFIG.lineSpacing * 4;
          if (noteY > staffBottom) {
            ctx.strokeStyle = lineColor;
            ctx.lineWidth = 1;
            for (let ly = staffBottom + STAFF_CONFIG.lineSpacing; ly <= noteY + 2; ly += STAFF_CONFIG.lineSpacing) {
              ctx.beginPath();
              ctx.moveTo(noteX - 10, ly);
              ctx.lineTo(noteX + 10, ly);
              ctx.stroke();
            }
          }
          if (noteY < staffTopY) {
            ctx.strokeStyle = lineColor;
            ctx.lineWidth = 1;
            for (let ly = staffTopY - STAFF_CONFIG.lineSpacing; ly >= noteY - 2; ly -= STAFF_CONFIG.lineSpacing) {
              ctx.beginPath();
              ctx.moveTo(noteX - 10, ly);
              ctx.lineTo(noteX + 10, ly);
              ctx.stroke();
            }
          }
          
          // Draw lyric below staff if available
          if (note.lyric) {
            ctx.fillStyle = lyricColor;
            ctx.font = '11px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(note.lyric, noteX, staffTopY + STAFF_CONFIG.lineSpacing * 5 + 15);
            ctx.textAlign = 'left';
          }
          
          noteIndex++;
        }
        
        measureIndex++;
      }

      // Final bar line for system
      const systemEndX = measureStartX + (Math.min(measuresPerLine, totalMeasures - (sys * measuresPerLine)) * measureWidth);
      ctx.strokeStyle = STAFF_CONFIG.colors.barLines;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(systemEndX, staffTopY);
      ctx.lineTo(systemEndX, staffTopY + STAFF_CONFIG.lineSpacing * 4);
      ctx.stroke();
      
      // Double bar at end of piece
      if (measureIndex >= totalMeasures) {
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(systemEndX + 4, staffTopY);
        ctx.lineTo(systemEndX + 4, staffTopY + STAFF_CONFIG.lineSpacing * 4);
        ctx.stroke();
      }
    }

    // Draw legend at bottom
    const legendY = STAFF_CONFIG.staffMarginTop + (numSystems * STAFF_CONFIG.systemSpacing) + 20;
    ctx.fillStyle = lyricColor;
    ctx.font = '10px sans-serif';
    ctx.fillText(
      'Numbers on note heads = Motesart scale degrees | Half-numbers (1½, 2½, etc.) = chromatic notes',
      STAFF_CONFIG.leftMargin,
      legendY
    );

  }, [songData, keySignature, timeSignature, printMode, showOriginalChords, zoom, omrNotes, omrMeasures]);

  // Show processing state or trigger button
  if (isProcessing) {
    return (
      <div 
        className="flex flex-col items-center justify-center h-64 bg-slate-900/50 rounded-lg"
        data-testid="staff-notation-view"
      >
        <Loader2 className="w-8 h-8 animate-spin text-amber-400 mb-3" />
        <p className="text-slate-400">Processing sheet music with OMR...</p>
        <p className="text-xs text-slate-500 mt-1">Extracting notes, detecting key signature...</p>
      </div>
    );
  }

  return (
    <div ref={containerRef} className="relative" data-testid="staff-notation-view">
      {/* OMR Process Button */}
      {onProcessOMR && omrNotes.length === 0 && (
        <div className="absolute top-2 right-2 z-10">
          <Button
            onClick={onProcessOMR}
            size="sm"
            className="bg-amber-600 hover:bg-amber-500 text-white"
          >
            <RefreshCw className="w-4 h-4 mr-1" />
            Process OMR
          </Button>
        </div>
      )}
      
      <div className="overflow-auto max-h-[600px]">
        <canvas 
          ref={canvasRef} 
          className="block mx-auto"
          style={{ maxWidth: '100%', height: 'auto' }}
        />
      </div>
    </div>
  );
}

export default StaffNotationView;
