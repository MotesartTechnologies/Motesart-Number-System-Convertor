import { useState, useEffect, useCallback, useRef } from "react";
import { useNavigate, Link } from "react-router-dom";
import {
  Music,
  Upload,
  FileMusic,
  Sparkles,
  Download,
  Settings,
  Trash2,
  RefreshCw,
  Info,
  AlertCircle,
  CheckCircle,
  Loader2,
  Eye,
  FileImage,
  FileText,
  Clock,
  Printer,
  BookOpen,
  Send,
  MessageSquare,
  ChevronDown,
  ChevronUp,
  Edit3,
  Key,
  Keyboard,
  ZoomIn,
  ZoomOut,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Navbar } from "@/components/Navbar";
import { MotesartPreview } from "@/components/MotesartPreview";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Motesart Logo URL
const MOTESART_LOGO = "https://customer-assets.emergentagent.com/job_music-to-numbers/artifacts/eqmmw6fl_2316F097-7806-4D1F-AB36-BB5FF560800D.png";

// Content type labels
const CONTENT_TYPES = {
  chord_chart: "Chord Chart / Lead Sheet",
  traditional: "Traditional Sheet Music",
  hymnal: "Hymnal / SATB",
  lead_sheet: "Lead Sheet with Chords"
};

// Available keys for manual selection
const AVAILABLE_KEYS = [
  { value: "C", label: "C" },
  { value: "C#", label: "C# / Db" },
  { value: "D", label: "D" },
  { value: "Eb", label: "Eb / D#" },
  { value: "E", label: "E" },
  { value: "F", label: "F" },
  { value: "F#", label: "F# / Gb" },
  { value: "G", label: "G" },
  { value: "Ab", label: "Ab / G#" },
  { value: "A", label: "A" },
  { value: "Bb", label: "Bb / A#" },
  { value: "B", label: "B" },
];

// Status labels and colors
const STATUS_CONFIG = {
  uploaded: {
    label: "Uploaded",
    sublabel: "Use Manual Entry to convert",
    color: "yellow",
    icon: Clock
  },
  converting_ocr: {
    label: "Converting",
    sublabel: "Reading sheet music...",
    color: "blue",
    icon: Loader2
  },
  converting_motesart: {
    label: "Converting",
    sublabel: "Generating numbers...",
    color: "blue",
    icon: Loader2
  },
  processing: {
    label: "Processing",
    sublabel: "Converting to Motesart...",
    color: "blue",
    icon: Loader2
  },
  completed: {
    label: "Converted",
    sublabel: "Ready to view",
    color: "green",
    icon: CheckCircle
  },
  error: {
    label: "Error",
    sublabel: "Conversion failed",
    color: "red",
    icon: AlertCircle
  }
};

export default function Dashboard({ user }) {
  const navigate = useNavigate();
  const [conversions, setConversions] = useState([]);
  const [selectedConversion, setSelectedConversion] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const [explanation, setExplanation] = useState("");
  const [isExplaining, setIsExplaining] = useState(false);
  const [showOriginalPreview, setShowOriginalPreview] = useState(false);
  
  // Manual Entry state
  const [showManualEntry, setShowManualEntry] = useState(false);
  const [manualChords, setManualChords] = useState("");
  const [manualKey, setManualKey] = useState("C");
  const [isConvertingManual, setIsConvertingManual] = useState(false);
  const [manualConversionResult, setManualConversionResult] = useState(null);
  
  // Chat state
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState("");
  const [isSendingChat, setIsSendingChat] = useState(false);
  const chatScrollRef = useRef(null);

  // Scroll chat to bottom
  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight;
    }
  }, [chatMessages]);

  // Reset chat and manual entry when conversion changes
  useEffect(() => {
    setChatMessages([]);
    setExplanation("");
    setManualConversionResult(null);
    setManualChords("");
    setShowManualEntry(false);
  }, [selectedConversion?.conversion_id]);

  // Fetch conversions
  const fetchConversions = useCallback(async (selectFirst = false) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/conversions`, {
        credentials: "include",
      });
      if (response.ok) {
        const data = await response.json();
        setConversions(data);
        if (selectFirst && data.length > 0) {
          setSelectedConversion(data[0]);
        }
      }
    } catch (error) {
      console.error("Failed to fetch conversions:", error);
    }
  }, []);

  useEffect(() => {
    fetchConversions(true);
  }, [fetchConversions]);

  // Handle file upload
  const handleUpload = async (file) => {
    if (!file) return;

    const validTypes = [".mid", ".midi", ".xml", ".musicxml", ".mxl", ".pdf", ".png", ".jpg", ".jpeg", ".heic", ".heif"];
    const extension = "." + file.name.split(".").pop().toLowerCase();

    if (!validTypes.includes(extension)) {
      toast.error("Unsupported file type. Please upload sheet music (PDF, PNG, JPG, HEIC) or MusicXML/MIDI files.");
      return;
    }

    setIsUploading(true);
    setExplanation("");
    setChatMessages([]);
    setManualConversionResult(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${BACKEND_URL}/api/upload`, {
        method: "POST",
        credentials: "include",
        body: formData,
      });

      if (response.ok) {
        const newConversion = await response.json();
        setSelectedConversion(newConversion);
        await fetchConversions();
        
        if (newConversion.status === "completed" && newConversion.chords?.length > 0) {
          toast.success("File converted successfully!");
        } else if (newConversion.status === "uploaded") {
          toast.info("File uploaded. Use Manual Entry to convert chords.");
          setShowManualEntry(true);
        } else {
          toast.success("File uploaded and processing...");
        }
      } else {
        const error = await response.json();
        toast.error(error.detail || "Upload failed");
      }
    } catch (error) {
      toast.error("Upload failed: " + error.message);
    } finally {
      setIsUploading(false);
    }
  };

  // Handle manual chord conversion
  const handleManualConvert = async () => {
    if (!manualChords.trim()) {
      toast.error("Please enter some chord symbols");
      return;
    }

    setIsConvertingManual(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/convert/text`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: manualChords,
          key: manualKey,
          time_signature: "4/4",
          show_half_numbers: true,
        }),
      });

      if (response.ok) {
        const result = await response.json();
        setManualConversionResult(result);
        toast.success(`Converted ${result.chord_count} chords!`);
        
        // If we have a selected conversion, update it with the manual result
        if (selectedConversion) {
          await updateConversionWithManualData(result);
        }
      } else {
        throw new Error("Conversion failed");
      }
    } catch (error) {
      toast.error("Conversion failed: " + error.message);
    } finally {
      setIsConvertingManual(false);
    }
  };

  // Update conversion in database with manual entry data
  const updateConversionWithManualData = async (result) => {
    if (!selectedConversion) return;
    
    try {
      // Update the conversion via API
      const response = await fetch(`${BACKEND_URL}/api/conversions/${selectedConversion.conversion_id}/manual`, {
        method: "PUT",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          key_signature: result.key,
          key_name: result.key_name,
          chords: result.all_chords,
          sections: result.sections,
        }),
      });

      if (response.ok) {
        const updatedConversion = await response.json();
        setSelectedConversion(updatedConversion);
        await fetchConversions();
      }
    } catch (error) {
      console.error("Failed to update conversion:", error);
    }
  };

  // Drag and drop handlers
  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleUpload(file);
  };

  const handleFileInput = (e) => {
    const file = e.target.files?.[0];
    if (file) handleUpload(file);
  };

  // Delete conversion
  const handleDelete = async (conversionId) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/conversions/${conversionId}`, {
        method: "DELETE",
        credentials: "include",
      });
      if (response.ok) {
        if (selectedConversion?.conversion_id === conversionId) {
          setSelectedConversion(null);
        }
        await fetchConversions();
        toast.success("File deleted");
      }
    } catch (error) {
      toast.error("Delete failed");
    }
  };

  // Get explanation
  const handleExplain = async (sectionIndex = null) => {
    if (!selectedConversion) {
      toast.error("Upload a file first");
      return;
    }
    
    const hasChords = selectedConversion.chords?.length > 0 || 
                      selectedConversion.sections?.some(s => s.chords?.length > 0) ||
                      manualConversionResult?.all_chords?.length > 0;

    if (!hasChords) {
      toast.error("No chords to explain. Use Manual Entry to add chords first.");
      return;
    }

    setIsExplaining(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/explain`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          conversion_id: selectedConversion.conversion_id,
          section_index: sectionIndex,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setExplanation(data.explanation);
        toast.success("Explanation generated!");
      } else {
        throw new Error("Failed to generate explanation");
      }
    } catch (error) {
      toast.error("Failed to generate explanation");
      setExplanation("Unable to generate explanation. Please try again.");
    } finally {
      setIsExplaining(false);
    }
  };

  // Handle chat
  const handleSendChat = async () => {
    if (!chatInput.trim() || !selectedConversion) return;
    
    const userMessage = chatInput.trim();
    setChatInput("");
    
    const newUserMsg = {
      role: "user",
      content: userMessage,
      timestamp: new Date().toISOString()
    };
    setChatMessages(prev => [...prev, newUserMsg]);
    
    setIsSendingChat(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/chat`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          conversion_id: selectedConversion.conversion_id,
          message: userMessage,
          history: chatMessages.slice(-10)
        }),
      });

      if (response.ok) {
        const data = await response.json();
        const assistantMsg = {
          role: "assistant",
          content: data.response,
          timestamp: data.timestamp || new Date().toISOString()
        };
        setChatMessages(prev => [...prev, assistantMsg]);
      } else {
        throw new Error("Failed to get response");
      }
    } catch (error) {
      const errorMsg = {
        role: "assistant",
        content: "I'm having trouble responding. Please try again.",
        timestamp: new Date().toISOString()
      };
      setChatMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsSendingChat(false);
    }
  };

  const handleChatKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendChat();
    }
  };

  // Export
  const handleExport = async (format) => {
    if (!selectedConversion) return;

    try {
      const response = await fetch(
        `${BACKEND_URL}/api/export/${selectedConversion.conversion_id}?format=${format}`,
        { credentials: "include" }
      );

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${selectedConversion.filename.split(".")[0]}_motesart.${format === "text" ? "txt" : format}`;
        a.click();
        window.URL.revokeObjectURL(url);
        toast.success(`Exported as ${format.toUpperCase()}`);
      }
    } catch (error) {
      toast.error("Export failed");
    }
  };

  // Logout
  const handleLogout = async () => {
    try {
      await fetch(`${BACKEND_URL}/api/auth/logout`, {
        method: "POST",
        credentials: "include",
      });
      navigate("/", { replace: true });
    } catch (error) {
      console.error("Logout error:", error);
    }
  };

  // Get file type icon
  const getFileIcon = (fileType) => {
    if (["pdf", "png", "jpg", "jpeg", "heic", "heif"].includes(fileType)) {
      return <FileImage className="w-4 h-4 text-neon-pink" />;
    }
    if (["mid", "midi"].includes(fileType)) {
      return <Music className="w-4 h-4 text-neon-purple" />;
    }
    return <FileText className="w-4 h-4 text-neon-cyan" />;
  };

  // Get status badge
  const getStatusBadge = (status) => {
    const config = STATUS_CONFIG[status] || STATUS_CONFIG.processing;
    const colorClasses = {
      yellow: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
      blue: "bg-blue-500/20 text-blue-400 border-blue-500/30",
      green: "bg-green-500/20 text-green-400 border-green-500/30",
      red: "bg-red-500/20 text-red-400 border-red-500/30"
    };
    
    return (
      <span className={`text-xs px-2 py-0.5 rounded border ${colorClasses[config.color]}`}>
        {config.label}
      </span>
    );
  };

  // Format date
  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Render Motesart conversion content
  const renderMotesartContent = () => {
    // Use manual conversion result if available, otherwise use conversion data
    const conversionData = manualConversionResult || selectedConversion;
    const sections = conversionData?.sections || [];
    const allChords = manualConversionResult?.all_chords || selectedConversion?.chords || [];
    const keySignature = manualConversionResult?.key || selectedConversion?.key_signature || "1 = C";

    if (!selectedConversion) {
      return (
        <div className="flex flex-col items-center justify-center h-full text-center py-12">
          <FileMusic className="w-16 h-16 text-slate-700 mb-4" />
          <p className="text-slate-400 text-lg">Upload sheet music to see Motesart numbers</p>
          <p className="text-sm text-slate-600 mt-2">
            Supports: PDF, PNG, JPG, HEIC, MusicXML, MIDI
          </p>
        </div>
      );
    }

    const hasConversionData = sections.length > 0 || allChords.length > 0;
    const isProcessing = selectedConversion.status === "processing" || 
                         selectedConversion.status === "converting_ocr" || 
                         selectedConversion.status === "converting_motesart";

    if (isProcessing) {
      return (
        <div className="flex flex-col items-center justify-center h-full">
          <Loader2 className="w-12 h-12 text-neon-indigo animate-spin mb-4" />
          <p className="text-slate-400">{STATUS_CONFIG[selectedConversion.status]?.sublabel}</p>
        </div>
      );
    }

    if (!hasConversionData) {
      return (
        <div className="flex flex-col items-center justify-center h-full text-center py-8">
          <AlertCircle className="w-12 h-12 text-yellow-500/50 mb-4" />
          <p className="text-slate-300 font-medium mb-2">No Chords Detected</p>
          <p className="text-sm text-slate-500 max-w-md">
            Could not automatically detect chords from this file. Use Manual Entry below to type the chord symbols (like G, C, Am, D7) and see the Motesart conversion.
          </p>
          <Button 
            onClick={() => setShowManualEntry(true)}
            className="mt-4 bg-neon-indigo hover:bg-indigo-500"
          >
            <Edit3 className="w-4 h-4 mr-2" />
            Open Manual Entry
          </Button>
        </div>
      );
    }

    // Render the actual conversion
    return (
      <div className="space-y-4">
        {/* Key and metadata header */}
        <div className="flex items-center justify-between p-4 rounded-xl bg-gradient-to-r from-neon-indigo/10 to-neon-purple/10 border border-neon-indigo/30">
          <div className="flex items-center gap-3">
            <img src={MOTESART_LOGO} alt="Motesart" className="w-10 h-10 rounded" />
            <div>
              <p className="text-xs text-slate-400">Converted by Motesart Technologies</p>
              <p className="font-heading font-semibold">
                {selectedConversion.title || selectedConversion.filename?.split('.')[0]}
              </p>
            </div>
          </div>
          <div className="text-right">
            <p className="font-mono text-2xl font-bold text-amber-400">{keySignature}</p>
            <p className="text-xs text-slate-500">
              {selectedConversion.time_signature || "4/4"} | {selectedConversion.tempo || 120} BPM
            </p>
          </div>
        </div>

        {/* Sections with progressions */}
        {sections.map((section, sIdx) => (
          <div
            key={sIdx}
            className="p-4 rounded-xl bg-slate-800/30 border border-slate-700/50"
            data-testid={`section-${sIdx}`}
          >
            {/* Section header */}
            <div className="flex items-center justify-between mb-3">
              <span className="font-heading font-semibold text-purple-400 text-lg">
                [{section.name}]
              </span>
              {section.progression && (
                <span className="text-sm font-mono text-slate-500">
                  {section.progression}
                </span>
              )}
            </div>

            {/* Chord display */}
            {section.chords?.length > 0 && (
              <div className="font-mono text-xl space-y-2">
                <div className="flex flex-wrap gap-2">
                  {section.chords.map((chord, cIdx) => (
                    <span 
                      key={cIdx}
                      className="text-amber-400 font-bold px-2 py-1 bg-amber-400/10 rounded"
                      title={`Original: ${chord.original}`}
                    >
                      {chord.symbol}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Lines with converted chords */}
            {section.lines?.map((line, lIdx) => (
              <div key={lIdx} className="mt-2">
                {line.type === "chord_line" || line.chords?.length > 0 ? (
                  <div className="font-mono">
                    <div className="text-amber-400 font-bold text-lg">
                      {line.converted}
                    </div>
                  </div>
                ) : (
                  <div className="text-slate-500 text-sm">
                    {line.original}
                  </div>
                )}
              </div>
            ))}
          </div>
        ))}

        {/* All chords summary if no sections */}
        {sections.length === 0 && allChords.length > 0 && (
          <div className="p-4 rounded-xl bg-slate-800/30 border border-slate-700/50">
            <p className="text-sm text-slate-400 mb-3">All Detected Chords:</p>
            <div className="font-mono text-xl flex flex-wrap gap-2">
              {allChords.map((chord, idx) => (
                <span 
                  key={idx}
                  className="text-amber-400 font-bold px-2 py-1 bg-amber-400/10 rounded"
                  title={`Original: ${chord.original}`}
                >
                  {chord.symbol}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Symbol Legend */}
        <div className="p-3 rounded-lg bg-slate-900/50 border border-slate-700/50">
          <p className="text-xs text-slate-500 leading-relaxed">
            <span className="font-semibold text-slate-400">Legend:</span>{" "}
            <span className="font-mono text-amber-400">1-7</span> = scale degrees |{" "}
            <span className="font-mono text-amber-400">½</span> = chromatic (1½, 2½, 4½, 5½, 6½) |{" "}
            <span className="font-mono">m</span> = minor |{" "}
            <span className="font-mono">M</span> = non-diatonic major |{" "}
            <span className="font-mono text-amber-400">⁷ ⁹ ¹¹ ¹³</span> = extensions |{" "}
            <span className="font-mono">/X</span> = bass note
          </p>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-[#0a0a1a]" data-testid="dashboard-page">
      <Navbar user={user} onLogout={handleLogout} />

      {/* Main Content - New 2-Column Layout */}
      <div className="flex flex-col lg:flex-row gap-4 p-4 min-h-[calc(100vh-4rem)]">
        {/* LEFT COLUMN - Upload & Files (40% on desktop) */}
        <div className="lg:w-[35%] space-y-4 flex-shrink-0">
          {/* Upload Card */}
          <Card className="bg-[#12122a] border-[#2a2a4a] rounded-xl">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-heading flex items-center gap-2">
                <Upload className="w-4 h-4 text-neon-indigo" />
                Upload Sheet Music
              </CardTitle>
              <p className="text-xs text-slate-500 mt-1">
                Drop sheet music (PDF/image) or MIDI/MusicXML
              </p>
            </CardHeader>
            <CardContent>
              <div
                className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
                  isDragOver ? "border-neon-indigo bg-neon-indigo/10" : "border-slate-700 hover:border-slate-600"
                } ${isUploading ? "opacity-50 pointer-events-none" : ""}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => document.getElementById("file-input").click()}
                data-testid="upload-zone"
              >
                <input
                  id="file-input"
                  type="file"
                  accept=".pdf,.png,.jpg,.jpeg,.heic,.heif,.mid,.midi,.xml,.musicxml,.mxl"
                  onChange={handleFileInput}
                  className="hidden"
                  data-testid="file-input"
                />
                {isUploading ? (
                  <Loader2 className="w-10 h-10 mx-auto text-neon-indigo animate-spin" />
                ) : (
                  <FileImage className="w-10 h-10 mx-auto text-slate-500 mb-2" />
                )}
                <p className="text-sm text-slate-400 mt-2">
                  {isUploading ? "Uploading & Converting..." : "Drop sheet music here or click to browse"}
                </p>
                <p className="text-xs text-slate-600 mt-2">
                  PDF, PNG, JPG, HEIC, MusicXML, MIDI
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Recent Files */}
          <Card className="bg-[#12122a] border-[#2a2a4a] rounded-xl flex-1 overflow-hidden">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base font-heading">Recent Files</CardTitle>
                <Button variant="ghost" size="sm" onClick={() => fetchConversions()} className="h-8 w-8 p-0">
                  <RefreshCw className="w-4 h-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="p-0 max-h-[300px] overflow-y-auto">
              <div className="px-4 pb-4">
                {conversions.length === 0 ? (
                  <p className="text-sm text-slate-500 text-center py-6">
                    No files yet. Upload to get started.
                  </p>
                ) : (
                  <div className="space-y-2">
                    {conversions.map((conv) => (
                      <div
                        key={conv.conversion_id}
                        className={`p-3 rounded-lg cursor-pointer transition-all ${
                          selectedConversion?.conversion_id === conv.conversion_id
                            ? "bg-neon-indigo/10 border border-neon-indigo/30"
                            : "hover:bg-slate-800/50 border border-transparent"
                        }`}
                        onClick={() => setSelectedConversion(conv)}
                        data-testid={`file-item-${conv.conversion_id}`}
                      >
                        <div className="flex items-start gap-3">
                          {getFileIcon(conv.file_type)}
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium truncate">{conv.filename}</p>
                            <div className="flex items-center flex-wrap gap-2 mt-1">
                              {conv.key_signature && (
                                <span className="text-xs font-mono text-amber-400">
                                  {conv.key_signature}
                                </span>
                              )}
                              {getStatusBadge(conv.status)}
                            </div>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 w-6 p-0 opacity-50 hover:opacity-100"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDelete(conv.conversion_id);
                            }}
                          >
                            <Trash2 className="w-3 h-3 text-red-400" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Settings */}
          <Card className="bg-[#12122a] border-[#2a2a4a] rounded-xl">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-heading flex items-center gap-2">
                <Settings className="w-4 h-4 text-slate-400" />
                Display Settings
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between">
                <Label className="text-xs text-slate-400">Show half-numbers (½)</Label>
                <Switch defaultChecked />
              </div>
              <div className="flex items-center justify-between">
                <Label className="text-xs text-slate-400">Show original preview</Label>
                <Switch 
                  checked={showOriginalPreview} 
                  onCheckedChange={setShowOriginalPreview}
                />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* RIGHT COLUMN - Motesart Conversion (60% on desktop) */}
        <div className="lg:w-[65%] space-y-4 overflow-y-auto max-h-[calc(100vh-5rem)] pb-10">
          {/* MAIN: Motesart Conversion Panel */}
          <Card className="bg-[#12122a] border-[#2a2a4a] rounded-xl">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg font-heading flex items-center gap-2">
                  <Music className="w-5 h-5 text-amber-400" />
                  Motesart Conversion
                </CardTitle>
                {selectedConversion && (
                  <div className="flex items-center gap-2">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => setShowManualEntry(!showManualEntry)}
                      className="text-xs"
                    >
                      <Edit3 className="w-3 h-3 mr-1" />
                      Manual Entry
                    </Button>
                    {getStatusBadge(selectedConversion.status)}
                  </div>
                )}
              </div>
            </CardHeader>
            <CardContent className="min-h-[300px]">
              {renderMotesartContent()}
            </CardContent>
          </Card>

          {/* Manual Entry Panel (Collapsible) */}
          {showManualEntry && (
            <Card className="bg-[#12122a] border-neon-indigo/30 rounded-xl">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base font-heading flex items-center gap-2">
                    <Keyboard className="w-4 h-4 text-neon-indigo" />
                    Manual Chord Entry
                  </CardTitle>
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    onClick={() => setShowManualEntry(false)}
                    className="h-8 w-8 p-0"
                  >
                    <ChevronUp className="w-4 h-4" />
                  </Button>
                </div>
                <p className="text-xs text-slate-500">
                  Type chord symbols (G, Am, D7, C/E) and select the key to convert
                </p>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-3">
                  <div className="flex-1">
                    <Label className="text-xs text-slate-400 mb-1 block">Key</Label>
                    <Select value={manualKey} onValueChange={setManualKey}>
                      <SelectTrigger className="bg-slate-900/50 border-slate-700">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {AVAILABLE_KEYS.map((key) => (
                          <SelectItem key={key.value} value={key.value}>
                            {key.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div>
                  <Label className="text-xs text-slate-400 mb-1 block">Chord Symbols</Label>
                  <Textarea
                    value={manualChords}
                    onChange={(e) => setManualChords(e.target.value)}
                    placeholder="Enter chords like: G  D  Em  C  or  [Verse] G D C G  [Chorus] C G Am F"
                    className="bg-slate-900/50 border-slate-700 font-mono min-h-[100px]"
                  />
                </div>
                <Button 
                  onClick={handleManualConvert}
                  disabled={isConvertingManual || !manualChords.trim()}
                  className="w-full bg-neon-indigo hover:bg-indigo-500"
                >
                  {isConvertingManual ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Converting...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4 mr-2" />
                      Convert to Motesart Numbers
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Original Sheet Music Preview (Collapsible) */}
          {showOriginalPreview && selectedConversion?.is_sheet_music && (
            <Card className="bg-[#12122a] border-[#2a2a4a] rounded-xl">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base font-heading flex items-center gap-2">
                    <FileImage className="w-4 h-4 text-slate-400" />
                    Original Sheet Music
                  </CardTitle>
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    onClick={() => setShowOriginalPreview(false)}
                    className="h-8 w-8 p-0"
                  >
                    <ChevronUp className="w-4 h-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="aspect-[4/3] rounded-lg bg-slate-800/50 border border-slate-700 overflow-hidden">
                  {selectedConversion.file_type === "pdf" ? (
                    <iframe
                      src={`${BACKEND_URL}/api/conversions/${selectedConversion.conversion_id}/file`}
                      className="w-full h-full"
                      title="Sheet Music PDF"
                    />
                  ) : (
                    <img
                      src={`${BACKEND_URL}/api/conversions/${selectedConversion.conversion_id}/file`}
                      alt="Sheet Music"
                      className="w-full h-full object-contain"
                    />
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* AI Explain & Chat Panel */}
          <Card className="bg-[#12122a] border-[#2a2a4a] rounded-xl">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base font-heading flex items-center gap-2">
                  <MessageSquare className="w-4 h-4 text-neon-purple" />
                  AI Analysis & Chat
                </CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleExplain()}
                  disabled={!selectedConversion || isExplaining}
                  className="h-8"
                  data-testid="explain-btn"
                >
                  {isExplaining ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4 mr-1" />
                      Explain
                    </>
                  )}
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* AI Explanation */}
              {explanation && (
                <div className="p-4 rounded-lg bg-neon-indigo/10 border border-neon-indigo/20">
                  <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">
                    {explanation}
                  </p>
                </div>
              )}

              {/* Chat Messages */}
              <div 
                ref={chatScrollRef}
                className="max-h-[200px] overflow-y-auto space-y-3"
              >
                {chatMessages.length === 0 && !explanation ? (
                  <p className="text-sm text-slate-500 text-center py-4">
                    {selectedConversion 
                      ? "Click 'Explain' for AI analysis or ask a question below"
                      : "Upload a file to get AI analysis"}
                  </p>
                ) : (
                  chatMessages.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                    >
                      <div
                        className={`max-w-[85%] px-3 py-2 rounded-xl text-sm ${
                          msg.role === "user"
                            ? "bg-neon-purple/30 text-white rounded-br-sm"
                            : "bg-slate-800 text-slate-200 rounded-bl-sm"
                        }`}
                      >
                        <p className="whitespace-pre-wrap">{msg.content}</p>
                      </div>
                    </div>
                  ))
                )}
                {isSendingChat && (
                  <div className="flex justify-start">
                    <div className="bg-slate-800 text-slate-400 px-3 py-2 rounded-xl rounded-bl-sm text-sm">
                      <Loader2 className="w-4 h-4 animate-spin" />
                    </div>
                  </div>
                )}
              </div>

              {/* Chat Input */}
              <div className="flex gap-2">
                <Input
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyPress={handleChatKeyPress}
                  placeholder={selectedConversion ? "Ask about this music..." : "Upload a file first"}
                  disabled={!selectedConversion || isSendingChat}
                  className="flex-1 bg-slate-900/50 border-slate-700"
                  data-testid="chat-input"
                />
                <Button
                  onClick={handleSendChat}
                  disabled={!selectedConversion || !chatInput.trim() || isSendingChat}
                  size="sm"
                  className="bg-neon-purple hover:bg-purple-500"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Export Panel */}
          <Card className="bg-[#12122a] border-[#2a2a4a] rounded-xl">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-heading flex items-center gap-2">
                <Download className="w-4 h-4 text-slate-400" />
                Export & Share
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleExport("pdf")}
                  disabled={!selectedConversion}
                  className="flex-1"
                >
                  <Download className="w-4 h-4 mr-2" />
                  PDF
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleExport("csv")}
                  disabled={!selectedConversion}
                  className="flex-1"
                >
                  <Download className="w-4 h-4 mr-2" />
                  CSV
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleExport("text")}
                  disabled={!selectedConversion}
                  className="flex-1"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Text
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
