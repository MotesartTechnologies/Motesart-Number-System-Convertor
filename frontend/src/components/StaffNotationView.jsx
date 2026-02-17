import { useRef, useEffect, useState } from "react";
import { Button } from "../components/ui/button";
import { Loader2, RefreshCw } from "lucide-react";

// Staff configuration
const STAFF_CONFIG = {
  lineSpacing: 10,
  noteSize: 14,
  measureWidth: 140,
  staffMarginTop: 100,
  leftMargin: 60,
  rightMargin: 30,
  systemSpacing: 140,
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
  const notePositions = [0, 0, 1, 1, 2, 3, 3, 4, 4, 5, 5, 6];
  const noteInOctave = midi % 12;
  const octave = Math.floor(midi / 12) - 4;
  const basePosition = notePositions[noteInOctave];
  return basePosition + (octave * 7);
};

// Staff position to Y coordinate
const staffPositionToY = (position, staffTopY, lineSpacing) => {
  const middleLine = staffTopY + (lineSpacing * 2);
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
  omrDisplay = null,
  isProcessing = false,
  onProcessOMR = null,
  onCanvasReady = null,
}) {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    if (!canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    // Colors based on print mode
    const bgColor = printMode ? STAFF_CONFIG.colors.backgroundPrint : STAFF_CONFIG.colors.background;
    const textColor = printMode ? STAFF_CONFIG.colors.textPrint : '#ffffff';
    const numberColor = printMode ? '#b45309' : STAFF_CONFIG.colors.numbers;
    const lyricColor = printMode ? '#4b5563' : STAFF_CONFIG.colors.lyrics;
    const lineColor = printMode ? '#374151' : STAFF_CONFIG.colors.staffLines;
    const titleColor = printMode ? '#7c3aed' : STAFF_CONFIG.colors.title;

    const notes = omrNotes.length > 0 ? omrNotes : (songData?.notes || []);
    const measures = omrMeasures.length > 0 ? omrMeasures : (songData?.measures || []);
    const title = songData?.title || 'Untitled';
    
    // Calculate canvas dimensions based on content
    const measuresPerLine = 4;
    const totalMeasures = measures.length || Math.ceil(notes.length / 4) || 4;
    const numSystems = Math.ceil(totalMeasures / measuresPerLine);
    
    const canvasWidth = 800 * zoom;
    const canvasHeight = Math.max(500, (numSystems * STAFF_CONFIG.systemSpacing + 180)) * zoom;
    
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

    // If no notes, show placeholder message
    if (notes.length === 0 && measures.length === 0) {
      ctx.fillStyle = lyricColor;
      ctx.font = '14px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('No notes detected. Click "Process OMR" to extract notes from sheet music.', canvasWidth / (2 * zoom), 180);
      ctx.textAlign = 'left';
      
      if (onCanvasReady) onCanvasReady(canvas);
      return;
    }

    // Draw Motesart output with numbers on top and lyrics below
    let yOffset = STAFF_CONFIG.staffMarginTop;
    const xStart = STAFF_CONFIG.leftMargin;
    const noteSpacing = 45;
    
    // Draw each measure
    let x = xStart;
    let measureNum = 0;
    
    for (const measure of measures) {
      const measureNotes = measure.notes || [];
      
      // Check if we need to wrap to next line
      const measureWidth = measureNotes.length * noteSpacing + 30;
      if (x + measureWidth > (canvasWidth / zoom) - STAFF_CONFIG.rightMargin) {
        x = xStart;
        yOffset += STAFF_CONFIG.systemSpacing;
      }
      
      // Draw measure number
      ctx.fillStyle = lyricColor;
      ctx.font = '10px sans-serif';
      ctx.fillText(`${measureNum + 1}`, x, yOffset - 15);
      
      // Draw notes in this measure
      for (const note of measureNotes) {
        const motesart = note.motesart || note.number || '?';
        const lyric = note.lyric || '';
        const dotsAbove = note.dots_above || '';
        const dotsBelow = note.dots_below || '';
        
        // Draw dots above (for higher octaves)
        if (dotsAbove) {
          ctx.fillStyle = numberColor;
          ctx.font = '10px monospace';
          ctx.textAlign = 'center';
          ctx.fillText(dotsAbove, x + 15, yOffset - 5);
        }
        
        // Draw Motesart number
        ctx.fillStyle = numberColor;
        ctx.font = 'bold 20px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(motesart, x + 15, yOffset + 15);
        
        // Draw dots below (for lower octaves)
        if (dotsBelow) {
          ctx.fillStyle = numberColor;
          ctx.font = '10px monospace';
          ctx.textAlign = 'center';
          ctx.fillText(dotsBelow, x + 15, yOffset + 30);
        }
        
        // Draw lyric below
        if (lyric) {
          ctx.fillStyle = lyricColor;
          ctx.font = '12px sans-serif';
          ctx.textAlign = 'center';
          ctx.fillText(lyric, x + 15, yOffset + 50);
        }
        
        x += noteSpacing;
      }
      
      // Draw bar line after measure
      ctx.strokeStyle = STAFF_CONFIG.colors.barLines;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(x + 5, yOffset - 20);
      ctx.lineTo(x + 5, yOffset + 55);
      ctx.stroke();
      
      x += 20;
      measureNum++;
    }
    
    // If we have notes but no measures, distribute them
    if (measures.length === 0 && notes.length > 0) {
      x = xStart;
      let noteCount = 0;
      
      for (const note of notes) {
        // Wrap every 8 notes or when line is full
        if (noteCount > 0 && noteCount % 8 === 0) {
          // Draw bar line
          ctx.strokeStyle = STAFF_CONFIG.colors.barLines;
          ctx.lineWidth = 2;
          ctx.beginPath();
          ctx.moveTo(x + 5, yOffset - 20);
          ctx.lineTo(x + 5, yOffset + 55);
          ctx.stroke();
          
          x += 20;
        }
        
        if (x + noteSpacing > (canvasWidth / zoom) - STAFF_CONFIG.rightMargin) {
          x = xStart;
          yOffset += STAFF_CONFIG.systemSpacing;
        }
        
        const motesart = note.motesart || '?';
        const lyric = note.lyric || '';
        const dotsAbove = note.dots_above || '';
        const dotsBelow = note.dots_below || '';
        
        // Draw dots above
        if (dotsAbove) {
          ctx.fillStyle = numberColor;
          ctx.font = '10px monospace';
          ctx.textAlign = 'center';
          ctx.fillText(dotsAbove, x + 15, yOffset - 5);
        }
        
        // Draw Motesart number
        ctx.fillStyle = numberColor;
        ctx.font = 'bold 20px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(motesart, x + 15, yOffset + 15);
        
        // Draw dots below
        if (dotsBelow) {
          ctx.fillStyle = numberColor;
          ctx.font = '10px monospace';
          ctx.textAlign = 'center';
          ctx.fillText(dotsBelow, x + 15, yOffset + 30);
        }
        
        // Draw lyric
        if (lyric) {
          ctx.fillStyle = lyricColor;
          ctx.font = '12px sans-serif';
          ctx.textAlign = 'center';
          ctx.fillText(lyric, x + 15, yOffset + 50);
        }
        
        x += noteSpacing;
        noteCount++;
      }
    }

    // Draw legend
    const legendY = canvasHeight / zoom - 30;
    ctx.fillStyle = lyricColor;
    ctx.font = '11px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('Numbers = Motesart scale degrees | • above = higher octave | • below = lower octave | ½ = chromatic notes', STAFF_CONFIG.leftMargin, legendY);

    // Notify parent that canvas is ready
    if (onCanvasReady) {
      onCanvasReady(canvas);
    }

  }, [songData, keySignature, timeSignature, printMode, showOriginalChords, zoom, omrNotes, omrMeasures, omrLyrics, onCanvasReady]);

  return (
    <div ref={containerRef} className="relative w-full" data-testid="staff-notation-view">
      {isProcessing && (
        <div className="absolute inset-0 bg-slate-900/80 flex items-center justify-center z-10 rounded-lg">
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="w-8 h-8 text-amber-500 animate-spin" />
            <p className="text-sm text-slate-300">Processing sheet music with Gemini AI...</p>
          </div>
        </div>
      )}
      
      <div className="overflow-auto">
        <canvas 
          ref={canvasRef}
          className="mx-auto rounded-lg"
          style={{ 
            maxWidth: '100%',
            height: 'auto',
          }}
        />
      </div>
      
      {/* Process OMR Button - shown when no notes */}
      {omrNotes.length === 0 && onProcessOMR && !isProcessing && (
        <div className="mt-4 text-center">
          <Button
            onClick={onProcessOMR}
            className="bg-amber-600 hover:bg-amber-500 text-white"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Process OMR with Gemini AI
          </Button>
          <p className="text-xs text-slate-500 mt-2">
            Extracts notes and lyrics from scanned sheet music using Google Gemini Vision API
          </p>
        </div>
      )}
    </div>
  );
}

export default StaffNotationView;
