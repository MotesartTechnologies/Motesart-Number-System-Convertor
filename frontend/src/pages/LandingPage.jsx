import { Music, Sparkles, FileMusic, Download, ArrowRight, Waves } from "lucide-react";
import { Button } from "@/components/ui/button";

const HERO_BG = "https://images.unsplash.com/photo-1759771963975-8a4885446f1f?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDF8MHwxfHNlYXJjaHwxfHxhYnN0cmFjdCUyMG5lb24lMjBzb3VuZCUyMHdhdmVzJTIwZGFyayUyMGJhY2tncm91bmR8ZW58MHx8fHwxNzY4NTQyMTYzfDA&ixlib=rb-4.1.0&q=85";
const FEATURE_IMG_1 = "https://images.unsplash.com/photo-1762281429507-a0384348f4b1?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDF8MHwxfHNlYXJjaHwyfHxhYnN0cmFjdCUyMG5lb24lMjBzb3VuZCUyMHdhdmVzJTIwZGFyayUyMGJhY2tncm91bmR8ZW58MHx8fHwxNzY4NTQyMTYzfDA&ixlib=rb-4.1.0&q=85";
const FEATURE_IMG_2 = "https://images.unsplash.com/photo-1714123710240-974b15c86409?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1ODB8MHwxfHNlYXJjaHwxfHxtdXNpY2lhbiUyMHByb2R1Y2luZyUyMG11c2ljJTIwaW4lMjBkYXJrJTIwc3R1ZGlvfGVufDB8fHx8MTc2ODU0MjE2NXww&ixlib=rb-4.1.0&q=85";

const handleLogin = () => {
  // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
  const redirectUrl = window.location.origin + '/dashboard';
  window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
};

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-sonic-void text-white">
      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center overflow-hidden">
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
        <div className="relative z-10 w-full max-w-7xl mx-auto px-6 py-20">
          <nav className="flex items-center justify-between mb-20">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-neon-indigo/20 border border-neon-indigo/50 flex items-center justify-center">
                <Music className="w-5 h-5 text-neon-indigo" />
              </div>
              <span className="font-heading font-semibold text-xl tracking-tight">Motesart</span>
            </div>
            <Button
              onClick={handleLogin}
              className="bg-white/10 hover:bg-white/20 text-white border border-white/20 rounded-full px-6"
              data-testid="nav-login-btn"
            >
              Sign In
            </Button>
          </nav>

          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div className="space-y-8 animate-slide-in-up">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-neon-indigo/20 border border-neon-indigo/30">
                <Sparkles className="w-4 h-4 text-neon-indigo" />
                <span className="text-sm text-slate-300">AI-Powered Music Analysis</span>
              </div>

              <h1 className="font-heading text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight leading-none">
                Music in
                <span className="block text-transparent bg-clip-text bg-gradient-to-r from-neon-indigo to-neon-cyan">
                  Numbers
                </span>
              </h1>

              <p className="text-lg text-slate-400 max-w-lg leading-relaxed">
                Transform any MIDI or MusicXML file into the Motesart Number System. 
                Visualize chords, detect progressions, and understand music theory like never before.
              </p>

              <div className="flex flex-wrap gap-4">
                <Button
                  onClick={handleLogin}
                  className="bg-neon-indigo hover:bg-indigo-500 text-white rounded-full px-8 py-6 text-lg font-medium glow-primary"
                  data-testid="hero-get-started-btn"
                >
                  Get Started Free
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
                <Button
                  variant="outline"
                  className="border-slate-700 hover:bg-slate-800 text-slate-300 rounded-full px-8 py-6 text-lg"
                  data-testid="hero-learn-more-btn"
                >
                  Learn More
                </Button>
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

        {/* Decorative elements */}
        <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-sonic-void to-transparent" />
      </section>

      {/* Features Section */}
      <section className="py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="font-heading text-4xl font-bold mb-4">How It Works</h2>
            <p className="text-slate-400 max-w-2xl mx-auto">
              Upload your music files and get instant conversion to the Motesart Number System
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="group relative p-6 bg-slate-900/50 border border-white/5 hover:border-neon-indigo/50 rounded-2xl transition-all duration-500 card-hover">
              <div className="w-12 h-12 rounded-xl bg-neon-indigo/20 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <FileMusic className="w-6 h-6 text-neon-indigo" />
              </div>
              <h3 className="font-heading text-xl font-semibold mb-2">Upload Music</h3>
              <p className="text-slate-400 text-sm leading-relaxed">
                Drag and drop MIDI or MusicXML files. We support exports from any DAW, notation software, or keyboard.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="group relative p-6 bg-slate-900/50 border border-white/5 hover:border-neon-cyan/50 rounded-2xl transition-all duration-500 card-hover">
              <div className="w-12 h-12 rounded-xl bg-neon-cyan/20 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <Waves className="w-6 h-6 text-neon-cyan" />
              </div>
              <h3 className="font-heading text-xl font-semibold mb-2">Auto-Analyze</h3>
              <p className="text-slate-400 text-sm leading-relaxed">
                Key detection, chord recognition, and progression analysis happen automatically with AI assistance.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="group relative p-6 bg-slate-900/50 border border-white/5 hover:border-neon-purple/50 rounded-2xl transition-all duration-500 card-hover">
              <div className="w-12 h-12 rounded-xl bg-neon-purple/20 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <Download className="w-6 h-6 text-neon-purple" />
              </div>
              <h3 className="font-heading text-xl font-semibold mb-2">Export & Share</h3>
              <p className="text-slate-400 text-sm leading-relaxed">
                Export to PDF, CSV for Airtable, or plain text. Perfect for lessons, practice, and study.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Visual Section */}
      <section className="py-24 px-6 bg-slate-900/30">
        <div className="max-w-7xl mx-auto grid lg:grid-cols-2 gap-16 items-center">
          <div className="space-y-6">
            <h2 className="font-heading text-4xl font-bold">
              See Music
              <span className="text-neon-cyan"> Differently</span>
            </h2>
            <p className="text-slate-400 leading-relaxed">
              The Motesart Number System replaces traditional note names with numbers relative to the key. 
              This universal approach works in any key, making transposition instant and chord patterns obvious.
            </p>
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
              src={FEATURE_IMG_1}
              alt="Sound wave visualization"
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
              <h2 className="font-heading text-4xl font-bold mb-4">
                Ready to Transform Your Music?
              </h2>
              <p className="text-slate-400 mb-8 max-w-xl mx-auto">
                Join musicians and teachers using the Motesart Number System for faster learning and deeper understanding.
              </p>
              <Button
                onClick={handleLogin}
                className="bg-neon-indigo hover:bg-indigo-500 text-white rounded-full px-10 py-6 text-lg font-medium glow-primary"
                data-testid="cta-get-started-btn"
              >
                Start Converting Now
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
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
