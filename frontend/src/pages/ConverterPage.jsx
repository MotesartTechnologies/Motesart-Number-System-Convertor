import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  Music,
  Sparkles,
  Copy,
  Check,
  RefreshCw,
  Trash2,
  Settings,
  ChevronDown,
  FileText,
  Info,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
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
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Example chord charts for demonstration
const EXAMPLE_CHARTS = {
  simple: `[Verse]
G    D    Em   C
Amazing grace how sweet the sound
G    D    G
That saved a wretch like me

[Chorus]
G    D    Em   C
I once was lost but now I'm found
G    D    G
Was blind but now I see`,

  pop: `[Intro]
C  G  Am  F

[Verse 1]
C              G
When I was young  
Am             F
I never needed anyone
C              G        Am   F
And making love was just for fun

[Chorus]
C        G        Am      F
All by myself, don't wanna be
C        G        Am   F
All by myself anymore`,

  jazz: `[Intro]
Cmaj7  Dm7  G7  Cmaj7

[Verse]
Dm7      G7       Cmaj7    Am7
Fly me to the moon
Dm7      G7       C        A7
Let me play among the stars
Dm7      G7       Em7      Am7
Let me see what spring is like
Dm7      G7       Cmaj7
On Jupiter and Mars`,
};

// Available keys
const KEYS = [
  { value: "auto", label: "Auto-detect" },
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

const TIME_SIGNATURES = ["4/4", "3/4", "6/8", "2/4", "12/8"];

export default function ConverterPage({ user }) {
  const navigate = useNavigate();
  const [inputText, setInputText] = useState("");
  const [selectedKey, setSelectedKey] = useState("auto");
  const [timeSignature, setTimeSignature] = useState("4/4");
  const [isConverting, setIsConverting] = useState(false);
  const [conversionResult, setConversionResult] = useState(null);
  const [copied, setCopied] = useState(false);
  
  // Settings - half-numbers are ALWAYS on (removed as toggle)
  const [settings, setSettings] = useState({
    octaveMarkings: false,
    romanNumerals: false,
  });

  // Load example
  const loadExample = (exampleKey) => {
    setInputText(EXAMPLE_CHARTS[exampleKey]);
    setConversionResult(null);
  };

  // Convert chord chart
  const handleConvert = async () => {
    if (!inputText.trim()) {
      toast.error("Please enter a chord chart to convert");
      return;
    }

    setIsConverting(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/convert/text`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          text: inputText,
          key: selectedKey === "auto" ? null : selectedKey,
          time_signature: timeSignature,
          show_half_numbers: settings.showHalfNumbers,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Conversion failed");
      }

      const result = await response.json();
      setConversionResult(result);
      toast.success(`Converted ${result.chord_count} chords`);
    } catch (error) {
      toast.error(error.message || "Conversion failed");
    } finally {
      setIsConverting(false);
    }
  };

  // Clear all
  const handleClear = () => {
    setInputText("");
    setConversionResult(null);
    setSelectedKey("auto");
  };

  // Copy to clipboard
  const handleCopy = async () => {
    if (!conversionResult) return;

    // Build plain text output
    let output = `1 = ${conversionResult.key_name}\n\n`;
    
    for (const section of conversionResult.sections) {
      output += `[${section.name}]\n`;
      for (const line of section.lines) {
        output += `${line.converted}\n`;
      }
      output += "\n";
    }

    try {
      await navigator.clipboard.writeText(output);
      setCopied(true);
      toast.success("Copied to clipboard");
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      toast.error("Failed to copy");
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

  // Render a converted line with color coding
  const renderConvertedLine = (line) => {
    if (line.type === "empty") return null;
    
    if (line.type === "lyric_line" || line.chords.length === 0) {
      return (
        <div className="text-slate-400 font-light">
          {line.original}
        </div>
      );
    }

    // Line with chords - color the chord symbols
    const parts = [];
    let lastIndex = 0;
    const text = line.converted;
    
    // Find all chord symbols in the converted text
    const chordSymbols = line.chords.map(c => c.symbol);
    
    for (const chord of line.chords) {
      const symbol = chord.symbol;
      const idx = text.indexOf(symbol, lastIndex);
      
      if (idx > lastIndex) {
        // Text before the chord
        parts.push(
          <span key={`text-${lastIndex}`} className="text-slate-400">
            {text.slice(lastIndex, idx)}
          </span>
        );
      }
      
      if (idx >= 0) {
        // The chord symbol - golden/yellow color
        parts.push(
          <span 
            key={`chord-${idx}`} 
            className="font-mono font-semibold text-amber-400"
            title={`Original: ${chord.original}`}
          >
            {symbol}
          </span>
        );
        lastIndex = idx + symbol.length;
      }
    }
    
    // Remaining text
    if (lastIndex < text.length) {
      parts.push(
        <span key={`text-end`} className="text-slate-400">
          {text.slice(lastIndex)}
        </span>
      );
    }

    return <div className="leading-relaxed">{parts}</div>;
  };

  return (
    <div className="min-h-screen bg-sonic-void" data-testid="converter-page">
      <Navbar user={user} onLogout={handleLogout} />

      {/* Main Content - 3 Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 p-4 h-[calc(100vh-4rem)]">
        {/* Left Column - Input Panel */}
        <div className="lg:col-span-4 space-y-4 overflow-hidden flex flex-col">
          <Card className="bg-slate-900/50 border-slate-800 flex-1 flex flex-col">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-heading flex items-center gap-2">
                <FileText className="w-4 h-4 text-neon-indigo" />
                Input Chord Chart
              </CardTitle>
              <p className="text-xs text-slate-500 mt-1">
                Paste your chord chart below. Supports chords-over-lyrics, inline [chords], or plain sequences.
              </p>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col space-y-4">
              {/* Key and Time Signature Selectors */}
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label className="text-xs text-slate-400">Key</Label>
                  <Select value={selectedKey} onValueChange={setSelectedKey}>
                    <SelectTrigger 
                      className="bg-slate-950/50 border-slate-700"
                      data-testid="key-selector"
                    >
                      <SelectValue placeholder="Select key" />
                    </SelectTrigger>
                    <SelectContent>
                      {KEYS.map((key) => (
                        <SelectItem key={key.value} value={key.value}>
                          {key.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs text-slate-400">Time Signature</Label>
                  <Select value={timeSignature} onValueChange={setTimeSignature}>
                    <SelectTrigger 
                      className="bg-slate-950/50 border-slate-700"
                      data-testid="time-signature-selector"
                    >
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {TIME_SIGNATURES.map((ts) => (
                        <SelectItem key={ts} value={ts}>
                          {ts}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Textarea */}
              <Textarea
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder={`Paste your chord chart here...

Example:
[Verse]
G    D    Em   C
Amazing grace how sweet
G    D    G
That saved a wretch like me`}
                className="flex-1 min-h-[300px] bg-slate-950/50 border-slate-700 font-mono text-sm resize-none"
                data-testid="chord-input"
              />

              {/* Action Buttons */}
              <div className="flex gap-2">
                <Button
                  onClick={handleConvert}
                  disabled={isConverting || !inputText.trim()}
                  className="flex-1 bg-neon-indigo hover:bg-indigo-500"
                  data-testid="convert-btn"
                >
                  {isConverting ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Converting...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4 mr-2" />
                      Convert
                    </>
                  )}
                </Button>
                <Button
                  variant="outline"
                  onClick={handleClear}
                  className="border-slate-700 hover:bg-slate-800"
                  data-testid="clear-btn"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>

              {/* Example Loaders */}
              <div className="pt-2 border-t border-slate-800">
                <Label className="text-xs text-slate-500 mb-2 block">Load Example:</Label>
                <div className="flex gap-2 flex-wrap">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => loadExample("simple")}
                    className="text-xs text-slate-400 hover:text-white"
                  >
                    Simple Hymn
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => loadExample("pop")}
                    className="text-xs text-slate-400 hover:text-white"
                  >
                    Pop Song
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => loadExample("jazz")}
                    className="text-xs text-slate-400 hover:text-white"
                  >
                    Jazz Standard
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Center Column - Output Panel */}
        <div className="lg:col-span-5 space-y-4 overflow-hidden flex flex-col">
          <Card className="bg-slate-900/50 border-slate-800 flex-1 overflow-hidden flex flex-col">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base font-heading flex items-center gap-2">
                  <Music className="w-4 h-4 text-neon-cyan" />
                  Motesart Numbers
                </CardTitle>
                {conversionResult && (
                  <div className="flex items-center gap-3">
                    <span className="text-lg font-mono font-bold text-neon-indigo">
                      {conversionResult.key}
                    </span>
                    <span className="text-xs text-slate-500 bg-slate-800 px-2 py-1 rounded">
                      {conversionResult.chord_count} chords
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleCopy}
                      className="h-8"
                      data-testid="copy-btn"
                    >
                      {copied ? (
                        <Check className="w-4 h-4 text-green-400" />
                      ) : (
                        <Copy className="w-4 h-4" />
                      )}
                    </Button>
                  </div>
                )}
              </div>
            </CardHeader>
            <CardContent className="flex-1 overflow-hidden p-0">
              <ScrollArea className="h-full px-4 pb-4">
                {!conversionResult ? (
                  <div className="flex flex-col items-center justify-center h-64 text-center">
                    <Music className="w-12 h-12 text-slate-700 mb-4" />
                    <p className="text-slate-400">
                      Enter a chord chart and click Convert
                    </p>
                    <p className="text-sm text-slate-600 mt-2">
                      The Motesart numbers will appear here
                    </p>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {/* Key Display */}
                    <div className="p-4 rounded-xl bg-gradient-to-r from-neon-indigo/10 to-neon-purple/10 border border-neon-indigo/30">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-xs text-slate-400">Key</p>
                          <p className="text-2xl font-mono font-bold text-neon-indigo">
                            {conversionResult.key}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-xs text-slate-400">Time</p>
                          <p className="text-lg font-mono text-slate-300">
                            {timeSignature}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Sections */}
                    {conversionResult.sections.map((section, sIdx) => (
                      <div
                        key={sIdx}
                        className="space-y-2"
                        data-testid={`section-${sIdx}`}
                      >
                        {/* Section Header */}
                        <div className="flex items-center gap-2">
                          <span className="font-heading font-semibold text-purple-400">
                            [{section.name}]
                          </span>
                          {section.progression && (
                            <span className="text-xs text-slate-500 font-mono">
                              {section.progression}
                            </span>
                          )}
                        </div>

                        {/* Section Lines */}
                        <div className="pl-4 space-y-1 font-mono text-sm">
                          {section.lines.map((line, lIdx) => (
                            <div key={lIdx}>
                              {renderConvertedLine(line)}
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}

                    {/* Symbol Legend */}
                    <div className="p-3 rounded-lg bg-slate-800/30 border border-slate-700/50 mt-6">
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
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </div>

        {/* Right Column - Settings */}
        <div className="lg:col-span-3 space-y-4 overflow-hidden flex flex-col">
          {/* Settings Panel */}
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
                  Octave markings
                </Label>
                <Switch
                  id="octave-markers"
                  checked={settings.octaveMarkings}
                  onCheckedChange={(checked) =>
                    setSettings({ ...settings, octaveMarkings: checked })
                  }
                  data-testid="toggle-octave-markers"
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="roman-numerals" className="text-sm text-slate-300">
                  Roman numerals side-by-side
                </Label>
                <Switch
                  id="roman-numerals"
                  checked={settings.romanNumerals}
                  onCheckedChange={(checked) =>
                    setSettings({ ...settings, romanNumerals: checked })
                  }
                  data-testid="toggle-roman-numerals"
                />
              </div>
            </CardContent>
          </Card>

          {/* Info Panel */}
          <Card className="bg-slate-900/50 border-slate-800 flex-1">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-heading flex items-center gap-2">
                <Info className="w-4 h-4 text-slate-400" />
                Conversion Rules
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[300px]">
                <div className="space-y-4 text-sm">
                  <div>
                    <h4 className="font-semibold text-slate-200 mb-1">§3 Half-Numbers</h4>
                    <p className="text-slate-400 text-xs">
                      Valid: 1½, 2½, 4½, 5½, 6½<br />
                      Never use 3½ or 7½ (natural half-steps)
                    </p>
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-200 mb-1">§6 Chord Quality</h4>
                    <p className="text-slate-400 text-xs">
                      • Minor: always marked with 'm'<br />
                      • Major: 'M' only if non-diatonic<br />
                      • Diatonic major: no modifier
                    </p>
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-200 mb-1">§7 Inversions</h4>
                    <p className="text-slate-400 text-xs">
                      Format: chord/bass<br />
                      Example: G/B → 1/3 (1-chord with 3 in bass)
                    </p>
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-200 mb-1">§4c Extensions</h4>
                    <p className="text-slate-400 text-xs">
                      Superscripts: 7→⁷, 9→⁹, 11→¹¹, 13→¹³<br />
                      Maj7: M⁷, Min7: m⁷, Dom7: ⁷
                    </p>
                  </div>
                  <div className="pt-2 border-t border-slate-700">
                    <h4 className="font-semibold text-slate-200 mb-1">Supported Formats</h4>
                    <p className="text-slate-400 text-xs">
                      1. Chords-over-lyrics (Ultimate Guitar)<br />
                      2. Inline [chord] within lyrics<br />
                      3. Plain chord sequences
                    </p>
                  </div>
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
