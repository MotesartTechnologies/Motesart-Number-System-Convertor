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
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Navbar } from "@/components/Navbar";
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

// Status labels and colors
const STATUS_CONFIG = {
  uploaded: {
    label: "Uploaded",
    sublabel: "Could not detect chords - try Text Converter",
    color: "yellow",
    icon: Clock
  },
  converting_ocr: {
    label: "Converting",
    sublabel: "Step 1 of 2: Reading sheet music...",
    color: "blue",
    icon: Loader2
  },
  converting_motesart: {
    label: "Converting",
    sublabel: "Step 2 of 2: Generating numbers...",
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
  const [settings, setSettings] = useState({
    showHalfNumbers: true,
    showOctaveMarkers: false,
    showRomanNumerals: false,
  });
  
  // Chat state
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState("");
  const [isSendingChat, setIsSendingChat] = useState(false);
  const chatScrollRef = useRef(null);

  // Scroll chat to bottom when new messages arrive
  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight;
    }
  }, [chatMessages]);

  // Reset chat when conversion changes
  useEffect(() => {
    setChatMessages([]);
    setExplanation("");
  }, [selectedConversion?.conversion_id]);

  // Fetch conversions - always refresh on mount
  const fetchConversions = useCallback(async (selectFirst = false) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/conversions`, {
        credentials: "include",
      });
      if (response.ok) {
        const data = await response.json();
        setConversions(data);
        // Select first conversion if requested or if none selected yet
        if (selectFirst && data.length > 0) {
          setSelectedConversion(data[0]);
        }
      }
    } catch (error) {
      console.error("Failed to fetch conversions:", error);
    }
  }, []);

  // Fetch on mount - always refresh
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
    // Clear the old explanation and chat when uploading new file
    setExplanation("");
    setChatMessages([]);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${BACKEND_URL}/api/upload`, {
        method: "POST",
        credentials: "include",
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Upload failed");
      }

      const conversion = await response.json();
      
      // Show appropriate message based on status
      if (conversion.status === "completed") {
        toast.success("File converted successfully!");
      } else if (conversion.status === "uploaded") {
        toast.success("File uploaded! OMR conversion coming in Phase 2.");
      } else {
        toast.success("File uploaded and processing...");
      }
      
      // Select the new conversion immediately
      setSelectedConversion(conversion);
      // Refresh the list
      fetchConversions(false);
    } catch (error) {
      toast.error(error.message || "Failed to upload file");
    } finally {
      setIsUploading(false);
    }
  };

  // Handle drag and drop
  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files[0];
    handleUpload(file);
  };

  // Handle file input
  const handleFileInput = (e) => {
    const file = e.target.files[0];
    handleUpload(file);
  };

  // Delete conversion
  const handleDelete = async (conversionId) => {
    try {
      const response = await fetch(
        `${BACKEND_URL}/api/conversions/${conversionId}`,
        {
          method: "DELETE",
          credentials: "include",
        }
      );

      if (response.ok) {
        toast.success("Conversion deleted");
        if (selectedConversion?.conversion_id === conversionId) {
          setSelectedConversion(null);
        }
        fetchConversions();
      }
    } catch (error) {
      toast.error("Failed to delete conversion");
    }
  };

  // Get explanation
  const handleExplain = async (sectionIndex = null) => {
    if (!selectedConversion) {
      toast.error("Upload and convert a file first to get an AI explanation");
      return;
    }
    
    // Check if there are any chords to explain
    if (!selectedConversion.chords?.length && !selectedConversion.sections?.length) {
      toast.error("No chords detected in this file. Try the Text Converter for manual input.");
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

  // Handle chat message
  const handleSendChat = async () => {
    if (!chatInput.trim() || !selectedConversion) return;
    
    const userMessage = chatInput.trim();
    setChatInput("");
    
    // Add user message to chat
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
          history: chatMessages.slice(-10) // Send last 10 messages for context
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
        content: "I'm having trouble responding right now. Please try again.",
        timestamp: new Date().toISOString()
      };
      setChatMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsSendingChat(false);
    }
  };

  // Handle chat input key press
  const handleChatKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendChat();
    }
  };

  // Export conversion
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

  // Print
  const handlePrint = () => {
    window.print();
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

  // Get status badge with proper styling based on STATUS_CONFIG
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

  // Get status detail text
  const getStatusDetail = (status) => {
    const config = STATUS_CONFIG[status];
    return config ? config.sublabel : "";
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

  return (
    <div className="min-h-screen bg-sonic-void" data-testid="converter-page">
      <Navbar user={user} onLogout={handleLogout} />

      {/* Main Content - 3 Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 p-4 h-[calc(100vh-4rem)]">
        {/* Left Column - Upload & Files */}
        <div className="lg:col-span-3 space-y-4 overflow-hidden flex flex-col">
          {/* Upload Card */}
          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-heading flex items-center gap-2">
                <FileImage className="w-4 h-4 text-neon-indigo" />
                Upload Sheet Music
              </CardTitle>
              <p className="text-xs text-slate-500 mt-1">
                Drag & drop your sheet music (PDF or image). Optional: MusicXML or MIDI.
              </p>
            </CardHeader>
            <CardContent>
              <div
                className={`upload-zone rounded-xl p-6 text-center cursor-pointer ${
                  isDragOver ? "drag-over" : ""
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
                  accept=".pdf,.png,.jpg,.jpeg,.mid,.midi,.xml,.musicxml,.mxl"
                  onChange={handleFileInput}
                  className="hidden"
                  data-testid="file-input"
                />
                {isUploading ? (
                  <Loader2 className="w-8 h-8 mx-auto text-neon-indigo animate-spin" />
                ) : (
                  <Upload className="w-8 h-8 mx-auto text-slate-500 mb-2" />
                )}
                <p className="text-sm text-slate-400 mt-2">
                  {isUploading ? "Converting..." : "Drop sheet music here"}
                </p>
              </div>
              <p className="text-xs text-slate-600 mt-3 text-center">
                Supported: PDF, PNG, JPG, HEIC, MusicXML, MIDI
              </p>
            </CardContent>
          </Card>

          {/* Recent Files */}
          <Card className="bg-slate-900/50 border-slate-800 flex-1 overflow-hidden flex flex-col">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base font-heading">Recent Files</CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={fetchConversions}
                  className="h-8 w-8 p-0"
                  data-testid="refresh-files-btn"
                >
                  <RefreshCw className="w-4 h-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="flex-1 overflow-hidden p-0">
              <ScrollArea className="h-full px-4 pb-4">
                {conversions.length === 0 ? (
                  <p className="text-sm text-slate-500 text-center py-8">
                    No files yet. Upload sheet music to get started.
                  </p>
                ) : (
                  <div className="space-y-2">
                    {conversions.map((conv) => (
                      <div
                        key={conv.conversion_id}
                        className={`file-item p-3 rounded-lg cursor-pointer group ${
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
                                <span className="text-xs font-mono text-neon-indigo">
                                  {conv.key_signature}
                                </span>
                              )}
                              <span className="text-xs text-slate-500 uppercase">
                                {conv.file_type}
                              </span>
                              {getStatusBadge(conv.status)}
                            </div>
                            <div className="flex items-center gap-1 mt-1 text-xs text-slate-600">
                              <Clock className="w-3 h-3" />
                              {formatDate(conv.created_at)}
                            </div>
                          </div>
                          <div className="flex items-center gap-1">
                            {(conv.status === "processing" || conv.status === "converting_ocr" || conv.status === "converting_motesart") && (
                              <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
                            )}
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDelete(conv.conversion_id);
                              }}
                              data-testid={`delete-file-${conv.conversion_id}`}
                            >
                              <Trash2 className="w-3 h-3 text-red-400" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </div>

        {/* Center Column - Motesart Numbers */}
        <div className="lg:col-span-6 space-y-4 overflow-hidden flex flex-col">
          {/* Sheet Music Viewer (for uploaded PDF/images not yet converted) */}
          {selectedConversion?.is_sheet_music && selectedConversion?.status === "uploaded" && (
            <Card className="bg-slate-900/50 border-slate-800 border-yellow-500/30">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base font-heading flex items-center gap-2">
                    <FileImage className="w-4 h-4 text-neon-pink" />
                    Original Sheet Music
                  </CardTitle>
                  <div className="text-right">
                    <span className="text-xs px-2 py-1 rounded bg-yellow-500/20 text-yellow-400 border border-yellow-500/30">
                      Status: Uploaded
                    </span>
                    <p className="text-xs text-slate-500 mt-1">
                      OMR conversion coming in Phase 2
                    </p>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="aspect-[4/3] rounded-lg bg-slate-800/50 border border-slate-700 flex items-center justify-center overflow-hidden">
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
                      className="max-w-full max-h-full object-contain"
                    />
                  )}
                </div>
                <p className="text-xs text-slate-500 mt-3 text-center">
                  Your file is uploaded and saved. OMR conversion to Motesart numbers coming in Phase 2.
                </p>
              </CardContent>
            </Card>
          )}

          {/* Numbers View - Branded Motesart Template */}
          <Card className="bg-slate-900/50 border-slate-800 flex-1 overflow-hidden flex flex-col">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base font-heading flex items-center gap-2">
                  <Eye className="w-4 h-4 text-neon-cyan" />
                  Motesart View
                </CardTitle>
                {selectedConversion && selectedConversion.status === "completed" && (
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-mono text-neon-indigo">
                      {selectedConversion.key_signature}
                    </span>
                    <span className="text-xs text-slate-500">
                      {selectedConversion.time_signature} | {selectedConversion.tempo} BPM
                    </span>
                    {getStatusBadge(selectedConversion.status)}
                  </div>
                )}
              </div>
            </CardHeader>
            <CardContent className="flex-1 overflow-hidden p-0">
              <ScrollArea className="h-full px-4 pb-4">
                {!selectedConversion ? (
                  <div className="flex flex-col items-center justify-center h-64 text-center">
                    <FileMusic className="w-12 h-12 text-slate-700 mb-4" />
                    <p className="text-slate-400">Upload sheet music to see the Motesart numbers</p>
                    <p className="text-sm text-slate-600 mt-2">
                      Supports: Traditional scores, Chord charts, Hymnals, Lead sheets
                    </p>
                  </div>
                ) : selectedConversion.status === "uploaded" ? (
                  <div className="flex flex-col items-center justify-center h-64 text-center">
                    <FileImage className="w-12 h-12 text-yellow-500/50 mb-4" />
                    <p className="text-slate-400">Original file stored</p>
                    <p className="text-sm text-slate-600 mt-2">
                      OMR conversion coming in Phase 2
                    </p>
                  </div>
                ) : selectedConversion.status === "processing" || selectedConversion.status === "converting_ocr" || selectedConversion.status === "converting_motesart" ? (
                  <div className="flex flex-col items-center justify-center h-64">
                    <Loader2 className="w-8 h-8 text-neon-indigo animate-spin mb-4" />
                    <p className="text-slate-400">{getStatusDetail(selectedConversion.status)}</p>
                  </div>
                ) : selectedConversion.status === "completed" ? (
                  <div className="space-y-4">
                    {/* Branded Header */}
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
                        <p className="font-mono text-lg text-neon-indigo">{selectedConversion.key_signature}</p>
                        <p className="text-xs text-slate-500">
                          {CONTENT_TYPES[selectedConversion.content_type] || "Music File"}
                        </p>
                      </div>
                    </div>

                    {/* Sections with chords/progressions */}
                    {selectedConversion.sections?.map((section, sIdx) => (
                      <div
                        key={sIdx}
                        className="p-4 rounded-xl bg-slate-800/30 border border-slate-700/50"
                        data-testid={`section-${sIdx}`}
                      >
                        <div className="flex items-center justify-between mb-3">
                          <span className="text-sm font-heading font-semibold text-slate-200">
                            {section.name}
                          </span>
                          {section.start_measure && (
                            <span className="text-xs text-slate-500">
                              Measures {section.start_measure}-{section.end_measure}
                            </span>
                          )}
                        </div>

                        {/* Chord progression line */}
                        {section.progression && (
                          <div className="mb-3 p-2 rounded bg-neon-indigo/10 border border-neon-indigo/20">
                            <span className="font-mono text-neon-cyan">{section.progression}</span>
                          </div>
                        )}

                        {/* Individual chords in section */}
                        {section.chords?.length > 0 && (
                          <div className="flex flex-wrap gap-2">
                            {section.chords.map((chord, cIdx) => (
                              <span
                                key={cIdx}
                                className="font-mono text-sm px-3 py-1.5 rounded-lg bg-neon-indigo/10 border border-neon-indigo/30 text-neon-indigo"
                              >
                                {chord.symbol}
                              </span>
                            ))}
                          </div>
                        )}

                        {/* Notes in measure grid (for traditional/MIDI) */}
                        {!section.chords?.length && selectedConversion.notes?.length > 0 && (
                          <div className="measure-grid rounded-lg overflow-hidden">
                            {Array.from({ length: 4 }).map((_, mIdx) => {
                              const measureNum = (section.start_measure || 1) + mIdx;
                              const measureNotes = selectedConversion.notes?.filter(
                                (n) => Math.floor(n.beat / 4) + 1 === measureNum
                              );
                              const measureChords = selectedConversion.chords?.filter(
                                (c) => c.measure === measureNum
                              );

                              return (
                                <div key={mIdx} className="measure-cell">
                                  <div className="text-xs text-slate-600 mb-1">M{measureNum}</div>
                                  {measureChords?.length > 0 && (
                                    <div className="flex flex-wrap gap-1 mb-2">
                                      {measureChords.map((chord, cIdx) => (
                                        <span
                                          key={cIdx}
                                          className="motesart-chord text-sm px-2 py-0.5 rounded bg-neon-indigo/20"
                                        >
                                          {chord.symbol}
                                        </span>
                                      ))}
                                    </div>
                                  )}
                                  <div className="flex flex-wrap gap-1">
                                    {measureNotes?.slice(0, 8).map((note, nIdx) => (
                                      <span
                                        key={nIdx}
                                        className="motesart-number"
                                        title={`Pitch: ${note.pitch}, Beat: ${note.beat?.toFixed(2)}`}
                                      >
                                        {note.motesart_number}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    ))}

                    {/* All Chords Summary */}
                    {selectedConversion.chords?.length > 0 && (
                      <div className="p-4 rounded-xl bg-slate-800/30 border border-slate-700/50">
                        <h4 className="text-sm font-heading font-medium text-slate-300 mb-3">
                          All Chords
                        </h4>
                        <div className="flex flex-wrap gap-2">
                          {selectedConversion.chords.map((chord, idx) => (
                            <span
                              key={idx}
                              className="font-mono text-sm px-3 py-1.5 rounded-lg bg-neon-indigo/10 border border-neon-indigo/30 text-neon-indigo"
                            >
                              {chord.symbol}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Symbol Legend Footer */}
                    <div className="p-3 rounded-lg bg-slate-800/20 border border-slate-700/30">
                      <p className="text-xs text-slate-500 leading-relaxed">
                        <span className="font-semibold text-slate-400">Legend:</span>{" "}
                        <span className="font-mono text-neon-pink">½</span> = chromatic step up |{" "}
                        <span className="font-mono text-neon-cyan">/X</span> = bass first (slash) |{" "}
                        <span className="font-mono">m</span> = minor |{" "}
                        <span className="font-mono">M</span> = non-diatonic major |{" "}
                        <span className="font-mono text-green-400">⁺</span> = augmented |{" "}
                        <span className="font-mono text-orange-400">°</span> = diminished |{" "}
                        <span className="font-mono text-neon-purple">2⁹ 4¹¹ 6¹³</span> = extensions
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center h-64 text-center">
                    <AlertCircle className="w-12 h-12 text-red-500/50 mb-4" />
                    <p className="text-slate-400">Conversion failed</p>
                    <p className="text-sm text-red-400 mt-2">
                      {selectedConversion.error_message || "Please try uploading again"}
                    </p>
                  </div>
                )}
              </ScrollArea>
            </CardContent>
          </Card>

          {/* Progressions Strip */}
          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader className="pb-2">
              <CardTitle className="text-base font-heading">Progressions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2 overflow-x-auto scrollbar-hide pb-2">
                {!selectedConversion ? (
                  <span className="text-sm text-slate-500">No progressions detected</span>
                ) : selectedConversion.sections?.length > 0 ? (
                  selectedConversion.sections.map((section, idx) => (
                    <button
                      key={idx}
                      className="progression-chip whitespace-nowrap"
                      onClick={() => handleExplain(idx)}
                      data-testid={`progression-${idx}`}
                    >
                      {section.name}: {section.progression}
                    </button>
                  ))
                ) : (
                  <span className="text-sm text-slate-500">Upload a file to detect progressions</span>
                )}
                {selectedConversion?.progressions?.map((prog, idx) => (
                  <span
                    key={`prog-${idx}`}
                    className="px-3 py-1.5 rounded-full text-sm font-mono bg-green-500/20 border border-green-500/50 text-green-300"
                  >
                    {prog.name}
                  </span>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column - Chat, Explain & Settings */}
        <div className="lg:col-span-3 space-y-4 overflow-hidden flex flex-col">
          {/* Chat Panel */}
          <Card className="glass-panel border-neon-purple/20 flex-1 min-h-[300px] overflow-hidden flex flex-col">
            <CardHeader className="pb-2">
              <CardTitle className="text-base font-heading flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-neon-purple" />
                Chat with AI
              </CardTitle>
              <p className="text-xs text-slate-500">Ask questions about this music</p>
            </CardHeader>
            <CardContent className="flex-1 overflow-hidden flex flex-col p-0">
              {/* Chat Messages */}
              <div 
                ref={chatScrollRef}
                className="flex-1 overflow-y-auto px-4 py-2 space-y-3"
              >
                {chatMessages.length === 0 ? (
                  <div className="text-center py-6">
                    <MessageSquare className="w-8 h-8 text-slate-600 mx-auto mb-3" />
                    <p className="text-sm text-slate-500">
                      {selectedConversion 
                        ? "Ask me about the key, progressions, or how to play this piece!"
                        : "Upload a file first to start chatting"}
                    </p>
                    {selectedConversion && (
                      <div className="mt-3 flex flex-wrap gap-1 justify-center">
                        {["What key is this in?", "Explain the progression", "How do I transpose this?"].map((q, i) => (
                          <Button 
                            key={i}
                            variant="ghost" 
                            size="sm"
                            className="text-xs text-slate-400 hover:text-white"
                            onClick={() => {
                              setChatInput(q);
                              setTimeout(() => handleSendChat(), 100);
                            }}
                          >
                            {q}
                          </Button>
                        ))}
                      </div>
                    )}
                  </div>
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
                      <span className="flex items-center gap-2">
                        <Loader2 className="w-3 h-3 animate-spin" />
                        Thinking...
                      </span>
                    </div>
                  </div>
                )}
              </div>
              
              {/* Chat Input */}
              <div className="p-3 border-t border-slate-700/50">
                <div className="flex gap-2">
                  <Input
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyPress={handleChatKeyPress}
                    placeholder={selectedConversion ? "Ask about this music..." : "Upload a file first"}
                    disabled={!selectedConversion || isSendingChat}
                    className="flex-1 bg-slate-900/50 border-slate-700 text-sm"
                    data-testid="chat-input"
                  />
                  <Button
                    onClick={handleSendChat}
                    disabled={!selectedConversion || !chatInput.trim() || isSendingChat}
                    size="sm"
                    className="bg-neon-purple hover:bg-purple-500"
                    data-testid="chat-send-btn"
                  >
                    <Send className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Explain Panel */}
          <Card className="glass-panel border-neon-indigo/20 explain-panel">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base font-heading flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-neon-indigo" />
                  Quick Explain
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
                    <RefreshCw className="w-4 h-4" />
                  )}
                </Button>
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              {explanation ? (
                <div className="prose prose-sm prose-invert max-w-none">
                  <p className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">
                    {explanation}
                  </p>
                </div>
              ) : (
                <p className="text-xs text-slate-500 text-center py-2">
                  {selectedConversion 
                    ? selectedConversion.chords?.length || selectedConversion.sections?.length
                      ? "Click the refresh button for an AI explanation of this piece"
                      : "No chords detected. Try the Text Converter for manual input."
                    : "Upload and convert a file first"}
                </p>
              )}
            </CardContent>
          </Card>

          {/* Settings */}
          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-heading flex items-center gap-2">
                <Settings className="w-4 h-4 text-slate-400" />
                Settings
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <Label htmlFor="half-numbers" className="text-sm text-slate-300">
                  Show half-numbers
                </Label>
                <Switch
                  id="half-numbers"
                  checked={settings.showHalfNumbers}
                  onCheckedChange={(checked) =>
                    setSettings({ ...settings, showHalfNumbers: checked })
                  }
                  data-testid="toggle-half-numbers"
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="octave-markers" className="text-sm text-slate-300">
                  Octave markers
                </Label>
                <Switch
                  id="octave-markers"
                  checked={settings.showOctaveMarkers}
                  onCheckedChange={(checked) =>
                    setSettings({ ...settings, showOctaveMarkers: checked })
                  }
                  data-testid="toggle-octave-markers"
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="roman-numerals" className="text-sm text-slate-300">
                  Roman numerals
                </Label>
                <Switch
                  id="roman-numerals"
                  checked={settings.showRomanNumerals}
                  onCheckedChange={(checked) =>
                    setSettings({ ...settings, showRomanNumerals: checked })
                  }
                  data-testid="toggle-roman-numerals"
                />
              </div>
            </CardContent>
          </Card>

          {/* Export & Share */}
          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-heading flex items-center gap-2">
                <Download className="w-4 h-4 text-slate-400" />
                Export & Share
              </CardTitle>
              <p className="text-xs text-slate-500 mt-1">
                Perfect for lessons, practice, and study
              </p>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleExport("pdf")}
                  disabled={!selectedConversion}
                  className="border-slate-700 hover:bg-slate-800"
                  data-testid="export-pdf-btn"
                >
                  PDF
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleExport("csv")}
                  disabled={!selectedConversion}
                  className="border-slate-700 hover:bg-slate-800"
                  data-testid="export-csv-btn"
                >
                  CSV
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handlePrint}
                  disabled={!selectedConversion}
                  className="border-slate-700 hover:bg-slate-800"
                  data-testid="print-btn"
                >
                  <Printer className="w-3 h-3 mr-1" />
                  Print
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
