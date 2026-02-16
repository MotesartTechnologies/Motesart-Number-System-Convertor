import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Plus, Trash2, Play, Music } from "lucide-react";

const NOTES = ['C', 'D', 'E', 'F', 'G', 'A', 'B'];
const ACCIDENTALS = ['', '#', 'b'];
const OCTAVES = ['3', '4', '5', '6'];
const DURATIONS = [
  { value: '1', label: 'Whole' },
  { value: '0.5', label: 'Half' },
  { value: '0.25', label: 'Quarter' },
  { value: '0.125', label: 'Eighth' },
];

// Convert note name to MIDI number
const noteToMidi = (note, accidental, octave) => {
  const noteMap = { 'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11 };
  let midi = noteMap[note] + (parseInt(octave) + 1) * 12;
  if (accidental === '#') midi += 1;
  if (accidental === 'b') midi -= 1;
  return midi;
};

// Convert MIDI to Motesart degree
const midiToMotesart = (midi, keyRootMidi) => {
  const MAJOR_SCALE_SEMITONES = [0, 2, 4, 5, 7, 9, 11];
  const HALF_NUMBER_MAP = {
    1: "1½", 3: "2½", 6: "4½", 8: "5½", 10: "6½"
  };
  
  const semitones = (midi - keyRootMidi) % 12;
  const normalizedSemitones = semitones < 0 ? semitones + 12 : semitones;
  
  if (MAJOR_SCALE_SEMITONES.includes(normalizedSemitones)) {
    return String(MAJOR_SCALE_SEMITONES.indexOf(normalizedSemitones) + 1);
  }
  
  return HALF_NUMBER_MAP[normalizedSemitones] || '?';
};

// Get MIDI for key root
const getKeyRootMidi = (keyName) => {
  const keyMap = {
    'C': 60, 'C#': 61, 'Db': 61, 'D': 62, 'D#': 63, 'Eb': 63,
    'E': 64, 'F': 65, 'F#': 66, 'Gb': 66, 'G': 67, 'G#': 68,
    'Ab': 68, 'A': 69, 'A#': 70, 'Bb': 70, 'B': 71
  };
  return keyMap[keyName] || 60;
};

export function ManualNoteEntry({ 
  keySignature = 'C',
  onNotesChange,
  initialNotes = []
}) {
  const [notes, setNotes] = useState(initialNotes);
  const [currentNote, setCurrentNote] = useState('C');
  const [currentAccidental, setCurrentAccidental] = useState('');
  const [currentOctave, setCurrentOctave] = useState('4');
  const [currentDuration, setCurrentDuration] = useState('0.25');
  const [currentLyric, setCurrentLyric] = useState('');
  
  const keyRootMidi = getKeyRootMidi(keySignature);
  
  // Add a note
  const addNote = () => {
    const midi = noteToMidi(currentNote, currentAccidental, currentOctave);
    const motesart = midiToMotesart(midi, keyRootMidi);
    
    const newNote = {
      id: Date.now(),
      pitch: `${currentNote}${currentAccidental}${currentOctave}`,
      pitch_name: `${currentNote}${currentAccidental}`,
      midi,
      motesart,
      duration: parseFloat(currentDuration),
      duration_type: currentDuration === '1' ? 'whole' : 
                     currentDuration === '0.5' ? 'half' :
                     currentDuration === '0.25' ? 'quarter' : 'eighth',
      lyric: currentLyric,
    };
    
    const updatedNotes = [...notes, newNote];
    setNotes(updatedNotes);
    setCurrentLyric('');
    
    if (onNotesChange) {
      onNotesChange(updatedNotes);
    }
  };
  
  // Remove a note
  const removeNote = (id) => {
    const updatedNotes = notes.filter(n => n.id !== id);
    setNotes(updatedNotes);
    if (onNotesChange) {
      onNotesChange(updatedNotes);
    }
  };
  
  // Clear all notes
  const clearNotes = () => {
    setNotes([]);
    if (onNotesChange) {
      onNotesChange([]);
    }
  };

  return (
    <div className="space-y-4 p-4 bg-slate-900/50 rounded-lg border border-slate-700">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
          <Music className="w-4 h-4 text-amber-400" />
          Manual Note Entry
        </h3>
        <span className="text-xs text-slate-400">
          Key: 1 = {keySignature}
        </span>
      </div>
      
      {/* Note input controls */}
      <div className="grid grid-cols-5 gap-2">
        <div>
          <Label className="text-xs text-slate-400">Note</Label>
          <Select value={currentNote} onValueChange={setCurrentNote}>
            <SelectTrigger className="h-8 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {NOTES.map(n => (
                <SelectItem key={n} value={n}>{n}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        
        <div>
          <Label className="text-xs text-slate-400">Accidental</Label>
          <Select value={currentAccidental} onValueChange={setCurrentAccidental}>
            <SelectTrigger className="h-8 text-xs">
              <SelectValue placeholder="♮" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">♮ Natural</SelectItem>
              <SelectItem value="#">♯ Sharp</SelectItem>
              <SelectItem value="b">♭ Flat</SelectItem>
            </SelectContent>
          </Select>
        </div>
        
        <div>
          <Label className="text-xs text-slate-400">Octave</Label>
          <Select value={currentOctave} onValueChange={setCurrentOctave}>
            <SelectTrigger className="h-8 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {OCTAVES.map(o => (
                <SelectItem key={o} value={o}>{o}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        
        <div>
          <Label className="text-xs text-slate-400">Duration</Label>
          <Select value={currentDuration} onValueChange={setCurrentDuration}>
            <SelectTrigger className="h-8 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {DURATIONS.map(d => (
                <SelectItem key={d.value} value={d.value}>{d.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        
        <div>
          <Label className="text-xs text-slate-400">Lyric</Label>
          <Input 
            value={currentLyric}
            onChange={(e) => setCurrentLyric(e.target.value)}
            placeholder="word"
            className="h-8 text-xs"
          />
        </div>
      </div>
      
      {/* Add button */}
      <div className="flex gap-2">
        <Button 
          onClick={addNote} 
          size="sm" 
          className="bg-amber-600 hover:bg-amber-500"
        >
          <Plus className="w-3 h-3 mr-1" />
          Add Note
        </Button>
        <Button 
          onClick={clearNotes} 
          size="sm" 
          variant="outline"
          className="border-slate-600"
        >
          <Trash2 className="w-3 h-3 mr-1" />
          Clear All
        </Button>
      </div>
      
      {/* Notes display */}
      {notes.length > 0 && (
        <div className="mt-4">
          <div className="text-xs text-slate-400 mb-2">
            Added Notes ({notes.length}):
          </div>
          <div className="flex flex-wrap gap-2">
            {notes.map(note => (
              <div 
                key={note.id}
                className="flex items-center gap-1 px-2 py-1 bg-slate-800 rounded text-xs border border-slate-700"
              >
                <span className="text-amber-400 font-mono font-bold">
                  {note.motesart}
                </span>
                <span className="text-slate-400">
                  ({note.pitch})
                </span>
                {note.lyric && (
                  <span className="text-slate-500 italic">
                    "{note.lyric}"
                  </span>
                )}
                <button
                  onClick={() => removeNote(note.id)}
                  className="ml-1 text-red-400 hover:text-red-300"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Preview of Motesart sequence */}
      {notes.length > 0 && (
        <div className="mt-3 p-2 bg-slate-800/50 rounded border border-amber-400/30">
          <div className="text-xs text-slate-400 mb-1">Motesart Sequence:</div>
          <div className="font-mono text-lg text-amber-400 font-bold tracking-wider">
            {notes.map(n => n.motesart).join('  ')}
          </div>
          {notes.some(n => n.lyric) && (
            <div className="text-xs text-slate-500 mt-1">
              {notes.map(n => n.lyric || '').join(' ')}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default ManualNoteEntry;
