import { Link } from "react-router-dom";
import { 
  Music, Hash, Slash, ArrowUpRight, ChevronRight, 
  Piano, BookOpen, HelpCircle, ArrowRight 
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Navbar } from "@/components/Navbar";

// Major scale mappings for different keys
const KEY_MAPPINGS = {
  "C": ["C", "D", "E", "F", "G", "A", "B"],
  "D": ["D", "E", "F#", "G", "A", "B", "C#"],
  "E": ["E", "F#", "G#", "A", "B", "C#", "D#"],
  "F": ["F", "G", "A", "Bb", "C", "D", "E"],
  "G": ["G", "A", "B", "C", "D", "E", "F#"],
  "A": ["A", "B", "C#", "D", "E", "F#", "G#"],
  "Bb": ["Bb", "C", "D", "Eb", "F", "G", "A"],
  "Eb": ["Eb", "F", "G", "Ab", "Bb", "C", "D"],
};

const PROGRESSIONS = [
  { roman: "I–vi–IV–V", motesart: "1–6–4–5", name: "Pop Progression", example: "Let It Be, No Woman No Cry" },
  { roman: "ii–V–I", motesart: "2–5–1", name: "Jazz Turnaround", example: "Most jazz standards" },
  { roman: "I–IV–V–I", motesart: "1–4–5–1", name: "Blues/Rock", example: "Johnny B. Goode, La Bamba" },
  { roman: "vi–IV–I–V", motesart: "6–4–1–5", name: "Axis Progression", example: "Someone Like You, Despacito" },
  { roman: "I–V–vi–IV", motesart: "1–5–6–4", name: "Four Chords", example: "With or Without You" },
  { roman: "vii–iii–vi", motesart: "7–3–6", name: "Circle of 5ths", example: "Fly Me to the Moon" },
];

const HALF_NUMBERS = [
  { symbol: "1½", meaning: "Raised 1st (between 1 and 2)", example: "Blues note, tension" },
  { symbol: "2½", meaning: "Raised 2nd / minor 3rd", example: "Minor key feel" },
  { symbol: "4½", meaning: "Raised 4th (tritone)", example: "Blues note, lydian" },
  { symbol: "5½", meaning: "Raised 5th / minor 6th", example: "Augmented feel" },
  { symbol: "6½", meaning: "Raised 6th / minor 7th", example: "Dominant 7th chord" },
];

// Extensions (Section 5) - These don't introduce new numbers
const EXTENSIONS = [
  { symbol: "2⁹", meaning: "2 as a 9th extension", example: "Upper-structure color" },
  { symbol: "4¹¹", meaning: "4 as an 11th extension", example: "Sus4 tension" },
  { symbol: "6¹³", meaning: "6 as a 13th extension", example: "Rich jazz voicing" },
];

// Updated symbol legend per methodology document
const SYMBOL_LEGEND = [
  { symbol: "m", meaning: "Minor chord", color: "neon-cyan" },
  { symbol: "M", meaning: "Non-diatonic major", color: "neon-indigo" },
  { symbol: "⁺", meaning: "Augmented chord", color: "green-400" },
  { symbol: "°", meaning: "Diminished chord", color: "orange-400" },
  { symbol: "ø⁷", meaning: "Half-diminished 7th", color: "orange-400" },
  { symbol: "sus²", meaning: "Suspended 2nd", color: "yellow-400" },
  { symbol: "sus⁴", meaning: "Suspended 4th", color: "yellow-400" },
  { symbol: "⁷", meaning: "Seventh chord", color: "neon-purple" },
  { symbol: "/X", meaning: "Bass note (X in bass)", color: "neon-pink" },
  { symbol: "½", meaning: "Chromatic step up", color: "neon-cyan" },
  { symbol: "² ³", meaning: "Inversion markers (optional)", color: "slate-300" },
];

export default function LearnPage() {
  return (
    <div className="min-h-screen bg-sonic-void">
      <Navbar />
      
      <div className="max-w-6xl mx-auto px-6 py-12">
        {/* Hero */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-neon-indigo/20 border border-neon-indigo/30 mb-6">
            <BookOpen className="w-4 h-4 text-neon-indigo" />
            <span className="text-sm text-slate-300">Learn the System</span>
          </div>
          <h1 className="font-heading text-4xl sm:text-5xl font-bold mb-4">
            The Motesart
            <span className="text-neon-cyan"> Number System</span>
          </h1>
          <p className="text-lg text-slate-400 max-w-2xl mx-auto">
            A numbers-first music language: each note becomes a scale degree (1–7) 
            so you can hear, play, and transpose faster than with letters alone.
          </p>
        </div>

        {/* What is Motesart */}
        <section className="mb-16">
          <h2 className="font-heading text-2xl font-bold mb-6 flex items-center gap-2">
            <HelpCircle className="w-6 h-6 text-neon-indigo" />
            What is Motesart Methodology?
          </h2>
          <div className="grid md:grid-cols-3 gap-6">
            <Card className="bg-slate-900/50 border-slate-800">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Hash className="w-5 h-5 text-neon-cyan" />
                  Numbers Replace Letters
                </CardTitle>
              </CardHeader>
              <CardContent className="text-slate-400 text-sm">
                Instead of C-D-E-F-G-A-B, use <span className="font-mono text-neon-cyan">1-2-3-4-5-6-7</span>. 
                The number represents the scale degree relative to your key.
              </CardContent>
            </Card>
            <Card className="bg-slate-900/50 border-slate-800">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Music className="w-5 h-5 text-neon-purple" />
                  Transpose Instantly
                </CardTitle>
              </CardHeader>
              <CardContent className="text-slate-400 text-sm">
                A <span className="font-mono text-neon-purple">2-5-1</span> progression is the same in ANY key. 
                Just change what "1" equals and all numbers follow.
              </CardContent>
            </Card>
            <Card className="bg-slate-900/50 border-slate-800">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Piano className="w-5 h-5 text-neon-pink" />
                  See Patterns Clearly
                </CardTitle>
              </CardHeader>
              <CardContent className="text-slate-400 text-sm">
                Chord progressions become obvious. <span className="font-mono text-neon-pink">1-6-4-5</span> is 
                the "pop progression" used in thousands of songs.
              </CardContent>
            </Card>
          </div>
        </section>

        {/* Any Key Section */}
        <section className="mb-16">
          <h2 className="font-heading text-2xl font-bold mb-6 flex items-center gap-2">
            <Piano className="w-6 h-6 text-neon-cyan" />
            Any Key: 1 = Your Tonic
          </h2>
          <p className="text-slate-400 mb-6">
            Choose a key (1 = X) and see its 1–7 mapping. The major scale follows W-W-H-W-W-W-H.
          </p>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(KEY_MAPPINGS).map(([key, notes]) => (
              <Card key={key} className="bg-slate-900/50 border-slate-800 hover:border-neon-cyan/50 transition-colors">
                <CardHeader className="pb-2">
                  <CardTitle className="text-base font-mono">
                    1 = {key}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex justify-between text-xs">
                    {notes.map((note, idx) => (
                      <div key={idx} className="text-center">
                        <div className="font-mono text-neon-cyan mb-1">{idx + 1}</div>
                        <div className="text-slate-500">{note}</div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        {/* Progressions */}
        <section className="mb-16">
          <h2 className="font-heading text-2xl font-bold mb-6 flex items-center gap-2">
            <ArrowUpRight className="w-6 h-6 text-neon-purple" />
            Common Progressions
          </h2>
          <p className="text-slate-400 mb-6">
            Progressions in Roman numerals translated to Motesart numbers. Same pattern, any key.
          </p>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {PROGRESSIONS.map((prog, idx) => (
              <Card key={idx} className="bg-slate-900/50 border-slate-800 hover:border-neon-purple/50 transition-colors">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs text-slate-500 font-mono">{prog.roman}</span>
                    <ChevronRight className="w-4 h-4 text-slate-600" />
                    <span className="font-mono text-neon-purple font-medium">{prog.motesart}</span>
                  </div>
                  <div className="text-sm font-medium text-slate-200 mb-1">{prog.name}</div>
                  <div className="text-xs text-slate-500">{prog.example}</div>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        {/* Half Numbers */}
        <section className="mb-16">
          <h2 className="font-heading text-2xl font-bold mb-6 flex items-center gap-2">
            <Slash className="w-6 h-6 text-neon-pink" />
            Half Numbers (Chromatic Tones)
          </h2>
          <p className="text-slate-400 mb-6">
            Chromatic tones are written as half-numbers (1½, 2½, etc.) — always moving upward. 
            No 3½ or 7½ because 3→4 and 7→1 are already natural half steps.
          </p>
          <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-4">
            {HALF_NUMBERS.map((item, idx) => (
              <Card key={idx} className="bg-slate-900/50 border-slate-800">
                <CardContent className="pt-6">
                  <div className="font-mono text-2xl text-neon-pink mb-2">{item.symbol}</div>
                  <div className="text-sm text-slate-300 mb-1">{item.meaning}</div>
                  <div className="text-xs text-slate-500">{item.example}</div>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        {/* Extensions (Section 5 of Methodology) */}
        <section className="mb-16">
          <h2 className="font-heading text-2xl font-bold mb-6 flex items-center gap-2">
            <span className="text-neon-purple font-mono">⁹</span>
            Extensions & Tensions (Section 5)
          </h2>
          <p className="text-slate-400 mb-6">
            Extensions <strong className="text-slate-200">do not introduce new numbers</strong>. They are written as 
            superscripts to show upper-structure color. You still think in 2, 4, 6 relative to the scale.
          </p>
          <div className="grid sm:grid-cols-3 gap-4">
            {EXTENSIONS.map((item, idx) => (
              <Card key={idx} className="bg-slate-900/50 border-slate-800 border-neon-purple/30">
                <CardContent className="pt-6">
                  <div className="font-mono text-3xl text-neon-purple mb-2">{item.symbol}</div>
                  <div className="text-sm text-slate-300 mb-1">{item.meaning}</div>
                  <div className="text-xs text-slate-500">{item.example}</div>
                </CardContent>
              </Card>
            ))}
          </div>
          <p className="text-xs text-slate-500 mt-4">
            Example: 2⁹ means "2 functioning as the 9th of the chord (extension tension)"
          </p>
        </section>

        {/* Inversions (Section 7 of Methodology) */}
        <section className="mb-16">
          <h2 className="font-heading text-2xl font-bold mb-6 flex items-center gap-2">
            <Slash className="w-6 h-6 text-neon-cyan" />
            Inversions & Slash Rule (Section 7)
          </h2>
          <p className="text-slate-400 mb-6">
            Slash notation is: <strong className="text-neon-cyan">BASS FIRST, CHORD SECOND</strong>. 
            The format X/Y means X in the bass with a Y-chord above.
          </p>
          <div className="grid sm:grid-cols-3 gap-4 mb-6">
            <Card className="bg-slate-900/50 border-slate-800">
              <CardContent className="pt-6">
                <div className="font-mono text-2xl text-neon-cyan mb-2">1/3</div>
                <div className="text-sm text-slate-300">1 in the bass, 3-chord above</div>
              </CardContent>
            </Card>
            <Card className="bg-slate-900/50 border-slate-800">
              <CardContent className="pt-6">
                <div className="font-mono text-2xl text-neon-cyan mb-2">1/5</div>
                <div className="text-sm text-slate-300">1 in the bass, 5-chord above</div>
              </CardContent>
            </Card>
            <Card className="bg-slate-900/50 border-slate-800">
              <CardContent className="pt-6">
                <div className="font-mono text-2xl text-neon-cyan mb-2">1/7</div>
                <div className="text-sm text-slate-300">1 in the bass, 7-chord above</div>
              </CardContent>
            </Card>
          </div>
          <Card className="bg-slate-800/30 border-slate-700">
            <CardContent className="pt-4">
              <p className="text-sm text-slate-400">
                <strong className="text-slate-200">Optional Teaching Markers:</strong> Superscripts ² and ³ describe 
                the voicing of the chord (second/third inversion), not the bass function.
              </p>
              <p className="text-xs text-slate-500 mt-2">
                Example: 1/3² = 1 in the bass, 3-chord in second inversion
              </p>
            </CardContent>
          </Card>
        </section>

        {/* Symbols Quick Reference */}
        <section className="mb-16">
          <h2 className="font-heading text-2xl font-bold mb-6">Symbol Quick Reference</h2>
          <Card className="bg-slate-900/50 border-slate-800">
            <CardContent className="pt-6">
              <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
                {SYMBOL_LEGEND.map((item, idx) => (
                  <div key={idx}>
                    <div className={`font-mono text-lg text-${item.color} mb-1`}>{item.symbol}</div>
                    <div className="text-sm text-slate-400">{item.meaning}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </section>
                  <div className="font-mono text-lg text-neon-indigo mb-1">M</div>
                  <div className="text-sm text-slate-400">Non-diatonic major</div>
                </div>
                <div>
                  <div className="font-mono text-lg text-neon-purple mb-1">7</div>
                  <div className="text-sm text-slate-400">Seventh chord (5⁷ = dominant 7)</div>
                </div>
                <div>
                  <div className="font-mono text-lg text-neon-pink mb-1">/3</div>
                  <div className="text-sm text-slate-400">Bass inversion (1/3 = 1 chord, 3 in bass)</div>
                </div>
                <div>
                  <div className="font-mono text-lg text-orange-400 mb-1">°</div>
                  <div className="text-sm text-slate-400">Diminished chord</div>
                </div>
                <div>
                  <div className="font-mono text-lg text-green-400 mb-1">+</div>
                  <div className="text-sm text-slate-400">Augmented chord</div>
                </div>
                <div>
                  <div className="font-mono text-lg text-yellow-400 mb-1">sus2/sus4</div>
                  <div className="text-sm text-slate-400">Suspended chords</div>
                </div>
                <div>
                  <div className="font-mono text-lg text-slate-300 mb-1">↑ ↓</div>
                  <div className="text-sm text-slate-400">Octave markers (optional)</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </section>

        {/* CTA */}
        <section className="text-center">
          <Card className="bg-gradient-to-br from-neon-indigo/10 to-neon-purple/10 border-neon-indigo/30">
            <CardContent className="py-12">
              <h3 className="font-heading text-2xl font-bold mb-4">Ready to Convert Your Music?</h3>
              <p className="text-slate-400 mb-6 max-w-lg mx-auto">
                Upload your sheet music and see it transformed into the Motesart Number System instantly.
              </p>
              <Link to="/converter">
                <Button className="bg-neon-indigo hover:bg-indigo-500 text-white rounded-full px-8 py-6 text-lg glow-primary">
                  Go to Converter
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              </Link>
            </CardContent>
          </Card>
        </section>
      </div>
    </div>
  );
}
