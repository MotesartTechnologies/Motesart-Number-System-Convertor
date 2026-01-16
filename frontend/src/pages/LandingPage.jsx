import { Link } from "react-router-dom";
import { Sparkles, FileMusic, Download, ArrowRight, Waves, BookOpen, ChevronRight, FileImage } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Navbar } from "@/components/Navbar";

const HERO_BG = "https://images.unsplash.com/photo-1759771963975-8a4885446f1f?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDF8MHwxfHNlYXJjaHwxfHxhYnN0cmFjdCUyMG5lb24lMjBzb3VuZCUyMHdhdmVzJTIwZGFyayUyMGJhY2tncm91bmR8ZW58MHx8fHwxNzY4NTQyMTYzfDA&ixlib=rb-4.1.0&q=85";
const FEATURE_IMG = "https://images.unsplash.com/photo-1714123710240-974b15c86409?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1ODB8MHwxfHNlYXJjaHwxfHxtdXNpY2lhbiUyMHByb2R1Y2luZyUyMG11c2ljJTIwaW4lMjBkYXJrJTIwc3R1ZGlvfGVufDB8fHx8MTc2ODU0MjE2NXww&ixlib=rb-4.1.0&q=85";

// Motesart Logo URL (C → 1 concept)
const MOTESART_LOGO = "https://customer-assets.emergentagent.com/job_music-to-numbers/artifacts/eqmmw6fl_2316F097-7806-4D1F-AB36-BB5FF560800D.png";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-sonic-void text-white">
      <Navbar />

      {/* Hero Section */}
      <section className="relative min-h-[85vh] flex items-center overflow-hidden">
        {/* Background */}
        <div className="absolute inset-0">
          <img
            src={HERO_BG}
            alt="Abstract neon sound waves"
            className="w-full h-full object-cover opacity-40"
          />
          <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/20 via-purple-500/10 to-sonic-void" />
          <div className="absolute inset-0 bg-gradient-to-t from-sonic-void via-transparent to-transparent" />
        </div>

        {/* Content */}
        <div className="relative z-10 w-full max-w-7xl mx-auto px-6 py-16">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div className="space-y-8 animate-slide-in-up">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-neon-indigo/20 border border-neon-indigo/30">
                <Sparkles className="w-4 h-4 text-neon-indigo" />
                <span className="text-sm text-slate-300">AI-Powered Music Analysis</span>
              </div>

              <h1 className="font-heading text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight leading-none">
                See Your Sheet Music in
                <span className="block text-transparent bg-clip-text bg-gradient-to-r from-neon-indigo to-neon-cyan">
                  Numbers
                </span>
              </h1>

              <p className="text-lg text-slate-400 max-w-lg leading-relaxed">
                Upload your sheet music and see it instantly in the Motesart Number System. 
                Visualize chords, detect progressions, and transpose to any key in seconds.
              </p>

              <div className="flex flex-wrap gap-4">
                <Link to="/converter">
                  <Button
                    className="bg-neon-indigo hover:bg-indigo-500 text-white rounded-full px-8 py-6 text-lg font-medium glow-primary"
                    data-testid="hero-upload-btn"
                  >
                    <FileImage className="w-5 h-5 mr-2" />
                    Upload Sheet Music
                  </Button>
                </Link>
                <Link to="/learn">
                  <Button
                    variant="outline"
                    className="border-slate-700 hover:bg-slate-800 text-slate-300 rounded-full px-8 py-6 text-lg"
                    data-testid="hero-learn-btn"
                  >
                    Learn More
                  </Button>
                </Link>
              </div>

              <div className="flex items-center gap-8 pt-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-white">1 = C</div>
                  <div className="text-sm text-slate-500">Any Key</div>
                </div>
                <div className="w-px h-10 bg-slate-700" />
                <div className="text-center">
                  <div className="text-2xl font-bold text-neon-cyan font-mono">2-5-1</div>
                  <div className="text-sm text-slate-500">Progressions</div>
                </div>
                <div className="w-px h-10 bg-slate-700" />
                <div className="text-center">
                  <div className="text-2xl font-bold text-neon-purple font-mono">1½</div>
                  <div className="text-sm text-slate-500">Half Numbers</div>
                </div>
              </div>
            </div>

            {/* Demo Preview Card */}
            <div className="hidden lg:block">
              <div className="glass-panel rounded-2xl p-6 space-y-4 animate-fade-in" style={{ animationDelay: '0.3s' }}>
                <div className="flex items-center justify-between mb-4">
                  <span className="text-sm text-slate-400">Preview</span>
                  <span className="text-sm font-mono text-neon-indigo">1 = Eb</span>
                </div>
                
                <div className="space-y-3">
                  <div className="flex items-center gap-3 p-3 rounded-lg bg-slate-800/50">
                    <span className="text-slate-500 text-sm w-12">M1</span>
                    <div className="flex gap-2 font-mono text-lg">
                      <span className="text-neon-cyan">1</span>
                      <span className="text-white">-</span>
                      <span className="text-neon-cyan">5</span>
                      <span className="text-white">-</span>
                      <span className="text-neon-cyan">6</span>
                      <span className="text-white">-</span>
                      <span className="text-neon-cyan">4</span>
                    </div>
                    <span className="ml-auto text-xs text-neon-indigo px-2 py-1 rounded bg-neon-indigo/20">1-5-6-4</span>
                  </div>
                  <div className="flex items-center gap-3 p-3 rounded-lg bg-slate-800/50">
                    <span className="text-slate-500 text-sm w-12">M2</span>
                    <div className="flex gap-2 font-mono text-lg">
                      <span className="text-neon-purple">2m7</span>
                      <span className="text-white">-</span>
                      <span className="text-neon-purple">5<sup>7</sup></span>
                      <span className="text-white">-</span>
                      <span className="text-neon-purple">1M7</span>
                    </div>
                    <span className="ml-auto text-xs text-green-400 px-2 py-1 rounded bg-green-400/20">2-5-1</span>
                  </div>
                  <div className="flex items-center gap-3 p-3 rounded-lg bg-slate-800/50">
                    <span className="text-slate-500 text-sm w-12">M3</span>
                    <div className="flex gap-2 font-mono text-lg">
                      <span className="text-neon-cyan">1</span>
                      <span className="text-slate-500">/</span>
                      <span className="text-neon-pink">3</span>
                      <span className="text-white">-</span>
                      <span className="text-neon-cyan">4</span>
                      <span className="text-white">-</span>
                      <span className="text-orange-400">2½</span>
                    </div>
                    <span className="ml-auto text-xs text-orange-400 px-2 py-1 rounded bg-orange-400/20">passing</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-sonic-void to-transparent" />
      </section>

      {/* Learn More - Short Answers */}
      <section className="py-24 px-6 bg-slate-900/30">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="font-heading text-3xl sm:text-4xl font-bold mb-4">Learn More</h2>
            <p className="text-slate-400">Quick answers about the Motesart methodology</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {/* What is Motesart */}
            <Card className="bg-slate-900/50 border-slate-800 hover:border-neon-indigo/50 transition-colors card-hover">
              <CardContent className="pt-6">
                <div className="w-12 h-12 rounded-xl bg-neon-indigo/20 flex items-center justify-center mb-4">
                  <BookOpen className="w-6 h-6 text-neon-indigo" />
                </div>
                <h3 className="font-heading text-xl font-semibold mb-3">What is Motesart Methodology?</h3>
                <p className="text-slate-400 text-sm leading-relaxed">
                  A numbers-first music language: each note becomes a scale degree (1–7) so you can 
                  hear, play, and transpose faster than with letters alone.
                </p>
              </CardContent>
            </Card>

            {/* How we convert */}
            <Card className="bg-slate-900/50 border-slate-800 hover:border-neon-cyan/50 transition-colors card-hover">
              <CardContent className="pt-6">
                <div className="w-12 h-12 rounded-xl bg-neon-cyan/20 flex items-center justify-center mb-4">
                  <Waves className="w-6 h-6 text-neon-cyan" />
                </div>
                <h3 className="font-heading text-xl font-semibold mb-3">How do we convert your music?</h3>
                <p className="text-slate-400 text-sm leading-relaxed">
                  We read the key, chords, and notes from your sheet music, then translate every pitch 
                  into a number and every chord into its function (1–6–4–5, 2–5–1, etc.).
                </p>
              </CardContent>
            </Card>

            {/* Symbols */}
            <Card className="bg-slate-900/50 border-slate-800 hover:border-neon-purple/50 transition-colors card-hover">
              <CardContent className="pt-6">
                <div className="w-12 h-12 rounded-xl bg-neon-purple/20 flex items-center justify-center mb-4">
                  <span className="font-mono text-lg text-neon-purple">½</span>
                </div>
                <h3 className="font-heading text-xl font-semibold mb-3">What do the symbols mean?</h3>
                <p className="text-slate-400 text-sm leading-relaxed">
                  <span className="font-mono text-neon-cyan">½</span> = chromatic up, 
                  <span className="font-mono text-neon-pink"> /3</span> = 3rd in the bass, 
                  <span className="font-mono text-slate-300"> m</span> = minor, 
                  <span className="font-mono text-slate-300"> M</span> = non-diatonic major, 
                  <span className="font-mono text-neon-purple"> 7</span> = seventh chords.
                </p>
              </CardContent>
            </Card>
          </div>

          <div className="text-center mt-8">
            <Link to="/learn" className="inline-flex items-center gap-2 text-neon-indigo hover:text-indigo-400 transition-colors">
              View Motesart Key
              <ChevronRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="font-heading text-3xl sm:text-4xl font-bold mb-4">How It Works</h2>
            <p className="text-slate-400 max-w-2xl mx-auto">
              Three simple steps to transform your sheet music into numbers
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="relative group p-6 bg-slate-900/50 border border-white/5 hover:border-neon-indigo/50 rounded-2xl transition-all duration-500 card-hover">
              <div className="absolute -top-3 -left-3 w-8 h-8 rounded-full bg-neon-indigo flex items-center justify-center font-bold text-sm">1</div>
              <div className="w-12 h-12 rounded-xl bg-neon-indigo/20 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <FileImage className="w-6 h-6 text-neon-indigo" />
              </div>
              <h3 className="font-heading text-xl font-semibold mb-2">Upload Sheet Music</h3>
              <p className="text-slate-400 text-sm leading-relaxed">
                Drag and drop your sheet music (PDF or image). Also supports MusicXML and MIDI from DAWs and notation software.
              </p>
            </div>

            <div className="relative group p-6 bg-slate-900/50 border border-white/5 hover:border-neon-cyan/50 rounded-2xl transition-all duration-500 card-hover">
              <div className="absolute -top-3 -left-3 w-8 h-8 rounded-full bg-neon-cyan flex items-center justify-center font-bold text-sm text-slate-900">2</div>
              <div className="w-12 h-12 rounded-xl bg-neon-cyan/20 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <Waves className="w-6 h-6 text-neon-cyan" />
              </div>
              <h3 className="font-heading text-xl font-semibold mb-2">Auto-Analyze</h3>
              <p className="text-slate-400 text-sm leading-relaxed">
                Key detection, chord recognition, and progression analysis happen automatically with AI assistance.
              </p>
            </div>

            <div className="relative group p-6 bg-slate-900/50 border border-white/5 hover:border-neon-purple/50 rounded-2xl transition-all duration-500 card-hover">
              <div className="absolute -top-3 -left-3 w-8 h-8 rounded-full bg-neon-purple flex items-center justify-center font-bold text-sm">3</div>
              <div className="w-12 h-12 rounded-xl bg-neon-purple/20 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <Download className="w-6 h-6 text-neon-purple" />
              </div>
              <h3 className="font-heading text-xl font-semibold mb-2">Export & Share</h3>
              <p className="text-slate-400 text-sm leading-relaxed">
                Export to PDF, CSV for Airtable, or print. Perfect for lessons, practice, and study with students, bands, and choirs.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* See Music Differently */}
      <section className="py-24 px-6 bg-slate-900/30">
        <div className="max-w-7xl mx-auto grid lg:grid-cols-2 gap-16 items-center">
          <div className="space-y-6">
            <h2 className="font-heading text-3xl sm:text-4xl font-bold">
              See Music
              <span className="text-neon-cyan"> Differently</span>
            </h2>
            <p className="text-slate-400 leading-relaxed">
              Same music. New language. Traditional notation on the left; Motesart numbers on the right.
              The universal number system makes patterns obvious and transposition instant.
            </p>
            
            {/* Side by side comparison */}
            <div className="grid grid-cols-2 gap-4 p-4 rounded-xl bg-slate-800/30 border border-slate-700">
              <div className="text-center">
                <div className="text-xs text-slate-500 uppercase tracking-wider mb-3">Traditional</div>
                <div className="font-mono text-lg text-slate-300 space-y-1">
                  <div>C - G - Am - F</div>
                  <div className="text-sm text-slate-500">Key of C</div>
                </div>
              </div>
              <div className="text-center border-l border-slate-700">
                <div className="text-xs text-slate-500 uppercase tracking-wider mb-3">Motesart</div>
                <div className="font-mono text-lg space-y-1">
                  <div>
                    <span className="text-neon-cyan">1</span>
                    <span className="text-slate-500"> - </span>
                    <span className="text-neon-cyan">5</span>
                    <span className="text-slate-500"> - </span>
                    <span className="text-neon-purple">6m</span>
                    <span className="text-slate-500"> - </span>
                    <span className="text-neon-cyan">4</span>
                  </div>
                  <div className="text-sm text-neon-indigo">1 = C</div>
                </div>
              </div>
            </div>

            <ul className="space-y-3">
              <li className="flex items-center gap-3 text-slate-300">
                <span className="w-6 h-6 rounded-full bg-neon-indigo/20 flex items-center justify-center text-xs text-neon-indigo">1</span>
                Numbers 1-7 represent major scale degrees
              </li>
              <li className="flex items-center gap-3 text-slate-300">
                <span className="w-6 h-6 rounded-full bg-neon-cyan/20 flex items-center justify-center text-xs text-neon-cyan font-mono">½</span>
                Half-numbers (1½, 2½, etc.) for chromatic tones
              </li>
              <li className="flex items-center gap-3 text-slate-300">
                <span className="w-6 h-6 rounded-full bg-neon-purple/20 flex items-center justify-center text-xs text-neon-purple">/</span>
                Slash notation shows bass inversions (1/3, 5/7)
              </li>
            </ul>
          </div>
          <div className="relative">
            <img
              src={FEATURE_IMG}
              alt="Musician in studio"
              className="rounded-2xl w-full object-cover aspect-video"
            />
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-t from-sonic-void/80 to-transparent" />
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <div className="glass-panel rounded-3xl p-12 relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-neon-indigo/10 to-neon-purple/10" />
            <div className="relative z-10">
              <h2 className="font-heading text-3xl sm:text-4xl font-bold mb-4">
                Ready to Transform Your Music?
              </h2>
              <p className="text-slate-400 mb-8 max-w-xl mx-auto">
                Join musicians and teachers using the Motesart Number System for faster learning and deeper understanding.
              </p>
              <Link to="/converter">
                <Button
                  className="bg-neon-indigo hover:bg-indigo-500 text-white rounded-full px-10 py-6 text-lg font-medium glow-primary"
                  data-testid="cta-upload-btn"
                >
                  Upload Sheet Music
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-slate-800">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-neon-indigo/20 border border-neon-indigo/50 flex items-center justify-center">
              <Music className="w-4 h-4 text-neon-indigo" />
            </div>
            <span className="font-heading font-semibold">Motesart Converter</span>
          </div>
          <p className="text-sm text-slate-500">
            Built for musicians, by musicians. Part of the T.A.M.i ecosystem.
          </p>
        </div>
      </footer>
    </div>
  );
}
