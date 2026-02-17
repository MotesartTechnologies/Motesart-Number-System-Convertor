import { useRef, useEffect, useState } from "react";
import { Button } from "../components/ui/button";
import { Loader2, RefreshCw, Download, Copy, Check, AlertCircle } from "lucide-react";
import { toast } from "sonner";

// Staff configuration
const STAFF_CONFIG = {
  noteWidth: 50,
  lineHeight: 70,
  measurePadding: 15,
  colors: {
    numbers: '#fbbf24',
    lyrics: '#9ca3af',
    barLines: '#555555',
    background: '#0a0a1a',
    backgroundPrint: '#ffffff',
    title: '#a78bfa',
    pageLabel: '#6366f1',
    error: '#ef4444',
  }
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
  omrPages = [],
  totalPages = 1,
  failedPages = [],
  isProcessing = false,
  onProcessOMR = null,
  onCanvasReady = null,
  onExportPDF = null,
}) {
  const canvasRef = useRef(null);
  const [copied, setCopied] = useState(false);

  // Generate text output for clipboard
  const generateTextOutput = () => {
    if (!omrDisplay) return '';
    
    const lines = [];
    const numberLines = omrDisplay.number_lines || [];
    const lyricLines = omrDisplay.lyric_lines || [];
    
    for (let i = 0; i < numberLines.length; i++) {
      lines.push(numberLines[i]);
      if (lyricLines[i]) {
        lines.push(lyricLines[i]);
      }
      lines.push(''); // Empty line between rows
    }
    
    return lines.join('\n');
  };

  // Copy to clipboard handler
  const handleCopyToClipboard = async () => {
    const text = generateTextOutput();
    if (!text) {
      toast.error("No content to copy");
      return;
    }
    
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      toast.success("Copied to clipboard!");
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      toast.error("Failed to copy");
    }
  };

  useEffect(() => {
    if (!canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    const bgColor = printMode ? STAFF_CONFIG.colors.backgroundPrint : STAFF_CONFIG.colors.background;
    const textColor = printMode ? '#1f2937' : '#ffffff';
    const numberColor = printMode ? '#b45309' : STAFF_CONFIG.colors.numbers;
    const lyricColor = printMode ? '#4b5563' : STAFF_CONFIG.colors.lyrics;
    const titleColor = printMode ? '#7c3aed' : STAFF_CONFIG.colors.title;
    const barColor = printMode ? '#374151' : STAFF_CONFIG.colors.barLines;

    const title = songData?.title || 'Untitled';
    const measures = omrMeasures.length > 0 ? omrMeasures : (songData?.measures || []);
    const notes = omrNotes.length > 0 ? omrNotes : (songData?.notes || []);
    
    // Calculate canvas dimensions
    const notesPerLine = 16;
    const totalNotes = notes.length || measures.reduce((sum, m) => sum + (m.notes?.length || 0), 0);
    const numLines = Math.max(1, Math.ceil(totalNotes / notesPerLine));
    
    const canvasWidth = Math.max(800, notesPerLine * STAFF_CONFIG.noteWidth + 100) * zoom;
    const canvasHeight = Math.max(400, (numLines * STAFF_CONFIG.lineHeight * 2 + 200)) * zoom;
    
    canvas.width = canvasWidth;
    canvas.height = canvasHeight;
    
    ctx.scale(zoom, zoom);

    // Clear background
    ctx.fillStyle = bgColor;
    ctx.fillRect(0, 0, canvasWidth / zoom, canvasHeight / zoom);

    // Draw header
    ctx.fillStyle = titleColor;
    ctx.font = 'bold 24px Georgia, serif';
    ctx.fillText(title, 40, 40);

    // Key and time signature
    ctx.fillStyle = numberColor;
    ctx.font = 'bold 16px monospace';
    ctx.fillText(`1 = ${keySignature || 'C'}`, 40, 65);
    
    ctx.fillStyle = textColor;
    ctx.font = '14px monospace';
    ctx.fillText(`Time: ${timeSignature}`, 150, 65);

    // Page info if multi-page
    if (totalPages > 1) {
      ctx.fillStyle = STAFF_CONFIG.colors.pageLabel;
      ctx.font = '12px sans-serif';
      ctx.fillText(`Pages: ${totalPages - failedPages.length}/${totalPages} processed`, 280, 65);
    }

    // Branding
    ctx.fillStyle = lyricColor;
    ctx.font = '10px sans-serif';
    ctx.fillText('Converted by Motesart Technologies', 40, 85);

    // Show failed pages warning
    if (failedPages.length > 0) {
      ctx.fillStyle = STAFF_CONFIG.colors.error;
      ctx.font = '12px sans-serif';
      ctx.fillText(`⚠ Could not read page(s): ${failedPages.join(', ')}. Try higher quality scans.`, 40, 105);
    }

    // If no notes, show placeholder
    if (notes.length === 0 && measures.length === 0) {
      ctx.fillStyle = lyricColor;
      ctx.font = '14px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('No notes detected. Click "Process OMR" to extract notes from sheet music.', canvasWidth / (2 * zoom), 180);
      ctx.textAlign = 'left';
      
      if (onCanvasReady) onCanvasReady(canvas);
      return;
    }

    // Draw aligned output: numbers on top, lyrics below
    let yOffset = failedPages.length > 0 ? 140 : 120;
    let xOffset = 40;
    const noteWidth = STAFF_CONFIG.noteWidth;
    const lineHeight = STAFF_CONFIG.lineHeight;
    let noteCount = 0;
    let measureCount = 0;
    
    // Draw measure by measure
    const allMeasures = measures.length > 0 ? measures : [{notes: notes}];
    
    for (const measure of allMeasures) {
      const measureNotes = measure.notes || [];
      
      // Draw measure start bar
      ctx.strokeStyle = barColor;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(xOffset, yOffset);
      ctx.lineTo(xOffset, yOffset + lineHeight);
      ctx.stroke();
      xOffset += 10;
      
      for (const note of measureNotes) {
        // Check if we need to wrap to next line
        if (xOffset + noteWidth > (canvasWidth / zoom) - 40) {
          xOffset = 40;
          yOffset += lineHeight * 1.5;
          
          // Draw measure continuation bar
          ctx.strokeStyle = barColor;
          ctx.lineWidth = 2;
          ctx.beginPath();
          ctx.moveTo(xOffset, yOffset);
          ctx.lineTo(xOffset, yOffset + lineHeight);
          ctx.stroke();
          xOffset += 10;
        }
        
        const motesart = note.motesart || note.number || '-';
        const lyric = note.lyric || '';
        const dotsAbove = note.dots_above || '';
        const dotsBelow = note.dots_below || '';
        
        const centerX = xOffset + noteWidth / 2;
        
        // Draw dots above (higher octave)
        if (dotsAbove) {
          ctx.fillStyle = numberColor;
          ctx.font = '12px monospace';
          ctx.textAlign = 'center';
          ctx.fillText(dotsAbove, centerX, yOffset + 5);
        }
        
        // Draw Motesart number
        ctx.fillStyle = numberColor;
        ctx.font = 'bold 24px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(motesart, centerX, yOffset + 30);
        
        // Draw dots below (lower octave)
        if (dotsBelow) {
          ctx.fillStyle = numberColor;
          ctx.font = '12px monospace';
          ctx.textAlign = 'center';
          ctx.fillText(dotsBelow, centerX, yOffset + 45);
        }
        
        // Draw lyric below - aligned directly under the number
        if (lyric && lyric !== '-') {
          ctx.fillStyle = lyricColor;
          ctx.font = '14px sans-serif';
          ctx.textAlign = 'center';
          ctx.fillText(lyric, centerX, yOffset + lineHeight - 5);
        }
        
        xOffset += noteWidth;
        noteCount++;
      }
      
      // Draw measure end bar
      ctx.strokeStyle = barColor;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(xOffset + 5, yOffset);
      ctx.lineTo(xOffset + 5, yOffset + lineHeight);
      ctx.stroke();
      xOffset += STAFF_CONFIG.measurePadding;
      measureCount++;
    }

    // Draw legend
    const legendY = canvasHeight / zoom - 35;
    ctx.fillStyle = lyricColor;
    ctx.font = '11px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('Legend: Numbers = Motesart scale degrees | • = octave indicators | ½ = chromatic notes', 40, legendY);
    ctx.fillText('Format: | 1  2  3  4 | = one measure with notes | Lyrics aligned below each number', 40, legendY + 15);

    if (onCanvasReady) {
      onCanvasReady(canvas);
    }

  }, [songData, keySignature, timeSignature, printMode, showOriginalChords, zoom, omrNotes, omrMeasures, omrLyrics, omrDisplay, totalPages, failedPages, onCanvasReady]);

  return (
    <div className="relative w-full" data-testid="staff-notation-view">
      {isProcessing && (
        <div className="absolute inset-0 bg-slate-900/80 flex items-center justify-center z-10 rounded-lg">
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="w-8 h-8 text-amber-500 animate-spin" />
            <p className="text-sm text-slate-300">Processing sheet music with Gemini AI...</p>
            <p className="text-xs text-slate-500">This may take a moment for multi-page PDFs</p>
          </div>
        </div>
      )}
      
      {/* Action buttons */}
      {omrNotes.length > 0 && (
        <div className="flex gap-2 mb-3 justify-end">
          <Button
            variant="outline"
            size="sm"
            onClick={handleCopyToClipboard}
            className="border-slate-700 text-xs"
          >
            {copied ? (
              <>
                <Check className="w-3 h-3 mr-1 text-green-500" />
                Copied!
              </>
            ) : (
              <>
                <Copy className="w-3 h-3 mr-1" />
                Copy Text
              </>
            )}
          </Button>
        </div>
      )}
      
      <div className="overflow-auto border border-slate-800 rounded-lg">
        <canvas 
          ref={canvasRef}
          className="mx-auto"
          style={{ 
            maxWidth: '100%',
            height: 'auto',
          }}
        />
      </div>
      
      {/* Failed pages warning */}
      {failedPages.length > 0 && (
        <div className="mt-3 p-3 bg-red-900/20 border border-red-800 rounded-lg flex items-start gap-2">
          <AlertCircle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm text-red-300 font-medium">Some pages could not be read</p>
            <p className="text-xs text-red-400 mt-1">
              Pages {failedPages.join(', ')} failed. Try uploading higher quality scans.
            </p>
          </div>
        </div>
      )}
      
      {/* Process OMR Button */}
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
            Extracts notes and lyrics from scanned sheet music
          </p>
        </div>
      )}
      
      {/* Text output preview (collapsible) */}
      {omrDisplay && omrDisplay.number_lines?.length > 0 && (
        <details className="mt-4 border border-slate-700 rounded-lg">
          <summary className="p-3 cursor-pointer text-sm text-slate-300 hover:bg-slate-800/50">
            📝 View Text Output (click to expand)
          </summary>
          <pre className="p-4 text-xs font-mono text-slate-400 bg-slate-900 overflow-x-auto whitespace-pre">
{omrDisplay.number_lines.map((numLine, i) => (
  `${numLine}\n${omrDisplay.lyric_lines[i] || ''}\n\n`
)).join('')}
          </pre>
        </details>
      )}
    </div>
  );
}

export default StaffNotationView;
