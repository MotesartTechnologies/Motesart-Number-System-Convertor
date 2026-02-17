import { useState, useRef, useCallback } from "react";
import {
  ZoomIn,
  ZoomOut,
  Music,
  FileText,
  Eye,
  Printer,
  Download,
  Copy,
  Image,
  RefreshCw,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { StaffNotationView } from "./StaffNotationView";
import { LeadSheetView } from "./LeadSheetView";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export function MotesartPreview({
  songData,
  conversionId,
  keySignature,
  timeSignature = "4/4",
  isStaffNotation = false,
  omrNotes = [],
  omrMeasures = [],
  omrLyrics = [],
  omrDisplay = null,
  onExport,
  onOMRProcessed,
  onShowOriginal,
  fileType,
}) {
  const [viewMode, setViewMode] = useState(isStaffNotation ? "staff" : "leadsheet");
  const [zoom, setZoom] = useState(1);
  const [showOriginalChords, setShowOriginalChords] = useState(false);
  const [printMode, setPrintMode] = useState(false);
  const [isProcessingOMR, setIsProcessingOMR] = useState(false);
  const [showOriginalFile, setShowOriginalFile] = useState(false);
  
  const staffCanvasRef = useRef(null);
  const leadSheetRef = useRef(null);

  // Zoom controls
  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.25, 2));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.25, 0.5));
  
  // Toggle original file view
  const handleShowOriginal = () => {
    if (onShowOriginal) {
      onShowOriginal();
    } else {
      setShowOriginalFile(!showOriginalFile);
    }
  };

  // Store canvas reference for export
  const handleCanvasReady = useCallback((canvas) => {
    staffCanvasRef.current = canvas;
  }, []);

  // Process OMR for sheet music
  const handleProcessOMR = async () => {
    if (!conversionId) {
      toast.error("No conversion selected");
      return;
    }
    
    setIsProcessingOMR(true);
    toast.info("Processing sheet music with OMR...", { duration: 5000 });
    
    try {
      const response = await fetch(
        `${BACKEND_URL}/api/conversions/${conversionId}/omr`,
        {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ key_override: keySignature }),
        }
      );
      
      if (response.ok) {
        const result = await response.json();
        
        if (result.omr_success) {
          toast.success(`OMR complete! Extracted ${result.omr_notes?.length || 0} notes.`);
          // Switch to staff view
          setViewMode("staff");
          // Notify parent to refresh conversion data
          if (onOMRProcessed) {
            onOMRProcessed(result);
          }
        } else {
          toast.warning(result.omr_error || "OMR could not extract notes. Try Manual Entry.");
        }
      } else {
        throw new Error("OMR processing failed");
      }
    } catch (error) {
      console.error("OMR error:", error);
      toast.error("OMR processing failed: " + error.message);
    } finally {
      setIsProcessingOMR(false);
    }
  };

  // Export as PDF
  const handleExportPDF = async () => {
    try {
      if (conversionId) {
        // Use backend export
        const response = await fetch(
          `${BACKEND_URL}/api/export/${conversionId}?format=pdf`,
          { credentials: "include" }
        );
        if (response.ok) {
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = `${songData?.title || 'motesart'}_conversion.pdf`;
          a.click();
          window.URL.revokeObjectURL(url);
          toast.success("PDF downloaded!");
        }
      }
      if (onExport) onExport("pdf");
    } catch (error) {
      toast.error("Export failed");
    }
  };

  // Export as PNG (staff view)
  const handleExportPNG = () => {
    if (viewMode === "staff" && staffCanvasRef.current) {
      const canvas = staffCanvasRef.current;
      const link = document.createElement("a");
      link.download = `${songData?.title || 'motesart'}_staff.png`;
      link.href = canvas.toDataURL("image/png");
      link.click();
      toast.success("PNG downloaded!");
    } else {
      toast.info("PNG export is available for Staff View only");
    }
  };

  // Copy text version
  const handleCopyText = async () => {
    if (!songData) return;
    
    let text = `${songData.title || 'Untitled'}\n`;
    text += `1 = ${keySignature || 'C'} | Time: ${timeSignature}\n`;
    text += `Converted by Motesart Technologies\n\n`;
    
    const sections = songData.sections || [];
    for (const section of sections) {
      text += `[${section.name}]\n`;
      if (section.chords) {
        text += section.chords.map(c => c.symbol || c).join('  ') + '\n';
      }
      if (section.progression) {
        text += `Progression: ${section.progression}\n`;
      }
      text += '\n';
    }
    
    text += '\nLegend: m=minor, M=non-diatonic major, ½=chromatic, ⁷⁹¹¹¹³=extensions\n';
    
    try {
      await navigator.clipboard.writeText(text);
      toast.success("Copied to clipboard!");
    } catch (error) {
      toast.error("Copy failed");
    }
  };

  // Print
  const handlePrint = () => {
    setPrintMode(true);
    setTimeout(() => {
      window.print();
      setPrintMode(false);
    }, 500);
  };

  return (
    <div 
      className="flex flex-col h-full"
      data-testid="motesart-preview"
    >
      {/* Toolbar */}
      <div 
        className="flex flex-wrap items-center gap-2 p-3 border-b border-slate-700 bg-slate-900/50"
        data-testid="preview-toolbar"
      >
        {/* View Toggle */}
        <div className="flex rounded-lg border border-slate-700 overflow-hidden">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setViewMode("staff")}
            className={`rounded-none px-3 ${viewMode === "staff" ? "bg-neon-indigo/20 text-neon-indigo" : ""}`}
            data-testid="staff-view-btn"
          >
            <Music className="w-4 h-4 mr-1" />
            Staff View
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setViewMode("leadsheet")}
            className={`rounded-none px-3 ${viewMode === "leadsheet" ? "bg-neon-indigo/20 text-neon-indigo" : ""}`}
            data-testid="leadsheet-view-btn"
          >
            <FileText className="w-4 h-4 mr-1" />
            Lead Sheet
          </Button>
        </div>

        <div className="h-6 w-px bg-slate-700" />

        {/* Zoom Controls */}
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleZoomOut}
            disabled={zoom <= 0.5}
            className="h-8 w-8 p-0"
          >
            <ZoomOut className="w-4 h-4" />
          </Button>
          <span className="text-xs text-slate-400 w-12 text-center">
            {Math.round(zoom * 100)}%
          </span>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleZoomIn}
            disabled={zoom >= 2}
            className="h-8 w-8 p-0"
          >
            <ZoomIn className="w-4 h-4" />
          </Button>
        </div>

        <div className="h-6 w-px bg-slate-700" />

        {/* Toggles */}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setShowOriginalChords(!showOriginalChords)}
          className={showOriginalChords ? "bg-slate-700" : ""}
          title="Show original chord letters alongside Motesart numbers"
        >
          <Eye className="w-4 h-4 mr-1" />
          Show Chords
        </Button>
        
        {/* View Original File */}
        {conversionId && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleShowOriginal}
            className={showOriginalFile ? "bg-neon-purple/20 text-neon-purple" : ""}
            title="View original uploaded file"
          >
            <Image className="w-4 h-4 mr-1" />
            Original
          </Button>
        )}

        <Button
          variant="ghost"
          size="sm"
          onClick={() => setPrintMode(!printMode)}
          className={printMode ? "bg-slate-700" : ""}
          title="Switch to print mode (light background)"
        >
          <Printer className="w-4 h-4 mr-1" />
          Print Mode
        </Button>

        {/* OMR Process Button */}
        {viewMode === "staff" && conversionId && omrNotes.length === 0 && (
          <Button
            variant="default"
            size="sm"
            onClick={handleProcessOMR}
            disabled={isProcessingOMR}
            className="bg-amber-600 hover:bg-amber-500"
            title="Extract notes from sheet music using OMR"
          >
            {isProcessingOMR ? (
              <>
                <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4 mr-1" />
                Process OMR
              </>
            )}
          </Button>
        )}

        <div className="flex-1" />

        {/* Export Buttons */}
        <Button
          variant="outline"
          size="sm"
          onClick={handleExportPDF}
          className="border-slate-700"
        >
          <Download className="w-4 h-4 mr-1" />
          PDF
        </Button>
        {viewMode === "staff" && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleExportPNG}
            className="border-slate-700"
          >
            <Image className="w-4 h-4 mr-1" />
            PNG
          </Button>
        )}
        <Button
          variant="outline"
          size="sm"
          onClick={handleCopyText}
          className="border-slate-700"
        >
          <Copy className="w-4 h-4 mr-1" />
          Copy
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={handlePrint}
          className="border-slate-700"
        >
          <Printer className="w-4 h-4" />
        </Button>
      </div>

      {/* Original File Preview (collapsible) */}
      {showOriginalFile && conversionId && (
        <div className="border-b border-slate-700 p-4 bg-slate-900/50">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-slate-300">Original File</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowOriginalFile(false)}
              className="h-6 px-2 text-xs"
            >
              Close
            </Button>
          </div>
          <div className="aspect-video max-h-[300px] rounded-lg bg-slate-800/50 border border-slate-700 overflow-hidden">
            {fileType === "pdf" ? (
              <iframe
                src={`${BACKEND_URL}/api/conversions/${conversionId}/file`}
                className="w-full h-full"
                title="Original PDF"
              />
            ) : (
              <img
                src={`${BACKEND_URL}/api/conversions/${conversionId}/file`}
                alt="Original Sheet Music"
                className="w-full h-full object-contain"
              />
            )}
          </div>
        </div>
      )}

      {/* Preview Area */}
      <div 
        className={`flex-1 overflow-auto p-4 ${printMode ? "bg-white" : "bg-[#0a0a1a]"}`}
        style={{ minHeight: '400px' }}
      >
        {viewMode === "staff" ? (
          <StaffNotationView
            songData={songData}
            keySignature={keySignature}
            timeSignature={timeSignature}
            printMode={printMode}
            showOriginalChords={showOriginalChords}
            zoom={zoom}
            omrNotes={omrNotes}
            omrMeasures={omrMeasures}
            omrLyrics={omrLyrics}
            omrDisplay={omrDisplay}
            omrPages={songData?.omr_pages || []}
            totalPages={songData?.total_pages || 1}
            failedPages={songData?.failed_pages || []}
            isProcessing={isProcessingOMR}
            onProcessOMR={conversionId ? handleProcessOMR : null}
            onCanvasReady={handleCanvasReady}
          />
        ) : (
          <LeadSheetView
            songData={songData}
            keySignature={keySignature}
            timeSignature={timeSignature}
            printMode={printMode}
            showOriginalChords={showOriginalChords}
            zoom={zoom}
          />
        )}
      </div>
    </div>
  );
}

export default MotesartPreview;
