import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  Music,
  Upload,
  FileMusic,
  Sparkles,
  Download,
  Settings,
  LogOut,
  Trash2,
  RefreshCw,
  ChevronRight,
  Info,
  AlertCircle,
  CheckCircle,
  Loader2,
  Eye,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

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

  // Fetch conversions
  const fetchConversions = useCallback(async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/conversions`, {
        credentials: "include",
      });
      if (response.ok) {
        const data = await response.json();
        setConversions(data);
        if (data.length > 0 && !selectedConversion) {
          setSelectedConversion(data[0]);
        }
      }
    } catch (error) {
      console.error("Failed to fetch conversions:", error);
    }
  }, [selectedConversion]);

  useEffect(() => {
    fetchConversions();
  }, [fetchConversions]);

  // Handle file upload
  const handleUpload = async (file) => {
    if (!file) return;

    const validTypes = [".mid", ".midi", ".xml", ".musicxml", ".mxl"];
    const extension = "." + file.name.split(".").pop().toLowerCase();

    if (!validTypes.includes(extension)) {
      toast.error("Unsupported file type. Please upload MIDI or MusicXML files.");
      return;
    }

    setIsUploading(true);

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
      toast.success("File converted successfully!");
      setSelectedConversion(conversion);
      fetchConversions();
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
    if (!selectedConversion) return;

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
      }
    } catch (error) {
      toast.error("Failed to generate explanation");
    } finally {
      setIsExplaining(false);
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

  return (
    <div className="min-h-screen bg-sonic-void" data-testid="dashboard">
      {/* Top Bar */}
      <header className="h-16 border-b border-slate-800 px-6 flex items-center justify-between bg-sonic-surface/50 backdrop-blur-lg sticky top-0 z-40">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-neon-indigo/20 border border-neon-indigo/50 flex items-center justify-center">
            <Music className="w-4 h-4 text-neon-indigo" />
          </div>
          <span className="font-heading font-semibold text-lg">Motesart Converter</span>
        </div>

        {selectedConversion && (
          <div className="hidden md:flex items-center gap-2 text-sm">
            <span className="text-slate-400">{selectedConversion.filename}</span>
            <span className="text-slate-600">–</span>
            <span className="font-mono text-neon-indigo">{selectedConversion.key_signature}</span>
          </div>
        )}

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="gap-2" data-testid="user-menu-btn">
              <Avatar className="w-8 h-8">
                <AvatarImage src={user?.picture} />
                <AvatarFallback className="bg-neon-indigo/20 text-neon-indigo text-sm">
                  {user?.name?.[0] || "M"}
                </AvatarFallback>
              </Avatar>
              <span className="hidden sm:inline text-sm text-slate-300">{user?.name}</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuItem className="text-slate-400">
              {user?.email}
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleLogout} data-testid="logout-btn">
              <LogOut className="w-4 h-4 mr-2" />
              Sign Out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </header>

      {/* Main Content - 3 Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 p-4 h-[calc(100vh-4rem)]">
        {/* Left Column - Upload & Files */}
        <div className="lg:col-span-3 space-y-4 overflow-hidden flex flex-col">
          {/* Upload Card */}
          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-heading flex items-center gap-2">
                <Upload className="w-4 h-4 text-neon-indigo" />
                Upload Music
              </CardTitle>
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
                  accept=".mid,.midi,.xml,.musicxml,.mxl"
                  onChange={handleFileInput}
                  className="hidden"
                  data-testid="file-input"
                />
                {isUploading ? (
                  <Loader2 className="w-8 h-8 mx-auto text-neon-indigo animate-spin" />
                ) : (
                  <FileMusic className="w-8 h-8 mx-auto text-slate-500 mb-2" />
                )}
                <p className="text-sm text-slate-400 mt-2">
                  {isUploading ? "Converting..." : "Drop MIDI or MusicXML file"}
                </p>
                <p className="text-xs text-slate-600 mt-1">.mid, .midi, .xml, .musicxml</p>
              </div>
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
                    No files yet. Upload one to get started.
                  </p>
                ) : (
                  <div className="space-y-2">
                    {conversions.map((conv) => (
                      <div
                        key={conv.conversion_id}
                        className={`file-item p-3 rounded-lg cursor-pointer flex items-center gap-3 ${
                          selectedConversion?.conversion_id === conv.conversion_id
                            ? "bg-neon-indigo/10 border border-neon-indigo/30"
                            : "hover:bg-slate-800/50"
                        }`}
                        onClick={() => setSelectedConversion(conv)}
                        data-testid={`file-item-${conv.conversion_id}`}
                      >
                        <FileMusic className="w-4 h-4 text-slate-400 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{conv.filename}</p>
                          <p className="text-xs text-slate-500 font-mono">
                            {conv.key_signature || "Processing..."}
                          </p>
                        </div>
                        {conv.status === "processing" && (
                          <Loader2 className="w-4 h-4 text-yellow-400 animate-spin" />
                        )}
                        {conv.status === "completed" && (
                          <CheckCircle className="w-4 h-4 text-green-400" />
                        )}
                        {conv.status === "error" && (
                          <AlertCircle className="w-4 h-4 text-red-400" />
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(conv.conversion_id);
                          }}
                          data-testid={`delete-file-${conv.conversion_id}`}
                        >
                          <Trash2 className="w-4 h-4 text-red-400" />
                        </Button>
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
          {/* Numbers View */}
          <Card className="bg-slate-900/50 border-slate-800 flex-1 overflow-hidden flex flex-col">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base font-heading flex items-center gap-2">
                  <Eye className="w-4 h-4 text-neon-cyan" />
                  Motesart View
                </CardTitle>
                {selectedConversion && (
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-slate-400">
                      {selectedConversion.time_signature} | {selectedConversion.tempo} BPM
                    </span>
                  </div>
                )}
              </div>
            </CardHeader>
            <CardContent className="flex-1 overflow-hidden p-0">
              <ScrollArea className="h-full px-4 pb-4">
                {!selectedConversion ? (
                  <div className="flex flex-col items-center justify-center h-64 text-center">
                    <Music className="w-12 h-12 text-slate-700 mb-4" />
                    <p className="text-slate-400">Upload a file to see the Motesart numbers</p>
                  </div>
                ) : selectedConversion.status === "processing" ? (
                  <div className="flex flex-col items-center justify-center h-64">
                    <Loader2 className="w-8 h-8 text-neon-indigo animate-spin mb-4" />
                    <p className="text-slate-400">Converting...</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {/* Sections with measures */}
                    {selectedConversion.sections?.map((section, sIdx) => (
                      <div
                        key={sIdx}
                        className="p-4 rounded-xl bg-slate-800/30 border border-slate-700/50"
                        data-testid={`section-${sIdx}`}
                      >
                        <div className="flex items-center justify-between mb-3">
                          <span className="text-sm font-medium text-slate-300">
                            {section.name}
                          </span>
                          <span className="text-xs text-slate-500">
                            Measures {section.start_measure}-{section.end_measure}
                          </span>
                        </div>

                        {/* Notes in measure grid */}
                        <div className="measure-grid rounded-lg overflow-hidden">
                          {Array.from({ length: 4 }).map((_, mIdx) => {
                            const measureNum = section.start_measure + mIdx;
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
                      </div>
                    ))}

                    {/* All Chords Summary */}
                    {selectedConversion.chords?.length > 0 && (
                      <div className="p-4 rounded-xl bg-slate-800/30 border border-slate-700/50">
                        <h4 className="text-sm font-medium text-slate-300 mb-3">
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

        {/* Right Column - Explain & Settings */}
        <div className="lg:col-span-3 space-y-4 overflow-hidden flex flex-col">
          {/* Explain Panel */}
          <Card className="glass-panel border-neon-indigo/20 flex-1 overflow-hidden flex flex-col explain-panel">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base font-heading flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-neon-purple" />
                  Explain
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
            <CardContent className="flex-1 overflow-hidden p-0">
              <ScrollArea className="h-full px-4 pb-4">
                {explanation ? (
                  <div className="prose prose-sm prose-invert max-w-none">
                    <p className="text-slate-300 leading-relaxed whitespace-pre-wrap">
                      {explanation}
                    </p>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Info className="w-8 h-8 text-slate-600 mx-auto mb-3" />
                    <p className="text-sm text-slate-500">
                      Click a progression chip or the refresh button to get an AI explanation.
                    </p>
                  </div>
                )}
              </ScrollArea>
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

          {/* Export */}
          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-heading flex items-center gap-2">
                <Download className="w-4 h-4 text-slate-400" />
                Export
              </CardTitle>
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
                  onClick={() => handleExport("text")}
                  disabled={!selectedConversion}
                  className="border-slate-700 hover:bg-slate-800"
                  data-testid="export-text-btn"
                >
                  Text
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
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
