import { useState, useRef, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Smile, Sun, Heart, Activity, FileText, ClipboardList,
  Send, Moon, Pill, TrendingUp, ChevronRight,
  Sparkles, Calendar, BarChart3, MessageCircle, PlusCircle,
  Check, X, AlertTriangle, Loader2, Info
} from 'lucide-react';
import TopNav from '@/components/layout/TopNav';
import { useAuthStore } from '@/lib/auth';

type Severity = 'mild' | 'moderate' | 'severe';

interface SymptomEntry {
  id: string;
  date: string;
  symptom: string;
  severity: Severity;
  sleepHours: number;
  tookMeds: boolean;
  notes: string;
}

interface ChatMessage {
  id: string;
  role: 'user' | 'system';
  text: string;
  timestamp: Date;
}

const SEVERITY_COLORS: Record<Severity, { bar: string; bg: string; text: string; border: string; dot: string }> = {
  mild:     { bar: 'var(--success)', bg: 'var(--success-muted)', text: 'var(--success)', border: 'var(--success-border)', dot: 'var(--success)' },
  moderate: { bar: 'var(--warning)', bg: 'var(--warning-muted)', text: 'var(--warning)', border: 'var(--warning-border)', dot: 'var(--warning)' },
  severe:   { bar: 'var(--danger)', bg: 'var(--danger-muted)', text: 'var(--danger)', border: 'var(--danger-border)', dot: 'var(--danger)' },
};

const SYMPTOM_LIST = [
  'Joint Pain', 'Fatigue', 'Headache', 'Nausea', 'Shortness of Breath',
  'Muscle Ache', 'Dizziness', 'Chest Tightness', 'Swelling', 'Insomnia',
  'Brain Fog', 'Stomach Pain', 'Back Pain', 'Anxiety', 'Palpitations',
];

const COMPANION_RESPONSES: Record<string, string[]> = {
  greeting: [
    "Patient simulator initialized. Log clinical symptom trends or query simulated compliance statistics.",
  ],
  mild: [
    "Simulation log saved. Severity classified as Mild. Continuous monitoring is recommended.",
  ],
  moderate: [
    "Simulation log saved. Severity classified as Moderate. Advice clinician consult if status degrades.",
  ],
  severe: [
    "Simulation log saved. Severity classified as Severe. Alert flag raised. Medical emergency review suggested.",
  ],
  general: [
    "Record updated in patient self-reporting ledger.",
  ]
};

function getSimulatedResponse(input: string, severity?: Severity): string {
  const lower = input.toLowerCase();
  if (severity) {
    const responses = COMPANION_RESPONSES[severity];
    return responses[Math.floor(Math.random() * responses.length)];
  }
  return COMPANION_RESPONSES.general[0];
}

function generateSeedData(): SymptomEntry[] {
  const entries: SymptomEntry[] = [];
  const severities: Severity[] = ['mild', 'moderate', 'severe', 'mild', 'moderate', 'mild', 'moderate'];
  const symptoms = ['Joint Pain', 'Fatigue', 'Headache', 'Muscle Ache', 'Back Pain', 'Brain Fog', 'Nausea'];
  for (let i = 6; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    entries.push({
      id: `seed-${i}`,
      date: d.toISOString().split('T')[0],
      symptom: symptoms[6 - i],
      severity: severities[6 - i],
      sleepHours: 4 + Math.floor(Math.random() * 5),
      tookMeds: Math.random() > 0.3,
      notes: '',
    });
  }
  return entries;
}

export default function Companion() {
  const [entries, setEntries] = useState<SymptomEntry[]>(generateSeedData);
  const [showCheckIn, setShowCheckIn] = useState(false);
  const [activeSection, setActiveSection] = useState<string>('daily');
  const [messages, setMessages] = useState<ChatMessage[]>([
    { id: '1', role: 'system', text: COMPANION_RESPONSES.greeting[0], timestamp: new Date() }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  
  // Check-In Form state
  const [symptom, setSymptom] = useState(SYMPTOM_LIST[0]);
  const [severity, setSeverity] = useState<Severity>('mild');
  const [sleepHours, setSleepHours] = useState(8);
  const [tookMeds, setTookMeds] = useState(true);
  const [notes, setNotes] = useState('');

  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleSubmitLog = (e: React.FormEvent) => {
    e.preventDefault();
    const newEntry: SymptomEntry = {
      id: `entry-${Date.now()}`,
      date: new Date().toISOString().split('T')[0],
      symptom,
      severity,
      sleepHours,
      tookMeds,
      notes,
    };
    setEntries(prev => [...prev, newEntry]);
    setShowCheckIn(false);
    
    // Simulate system response
    setIsTyping(true);
    setTimeout(() => {
      setMessages(prev => [...prev, {
        id: `msg-${Date.now()}`,
        role: 'system',
        text: getSimulatedResponse('', severity),
        timestamp: new Date()
      }]);
      setIsTyping(false);
    }, 800);
  };

  const handleSendChat = () => {
    if (!input.trim()) return;
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      text: input,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    setTimeout(() => {
      setMessages(prev => [...prev, {
        id: `bot-${Date.now()}`,
        role: 'system',
        text: getSimulatedResponse(input),
        timestamp: new Date()
      }]);
      setIsTyping(false);
    }, 800);
  };

  // Computations
  const avgSleep = useMemo(() => {
    return entries.length > 0
      ? (entries.reduce((s, e) => s + e.sleepHours, 0) / entries.length).toFixed(1)
      : '—';
  }, [entries]);

  const medCompliance = useMemo(() => {
    return entries.length > 0
      ? Math.round((entries.filter(e => e.tookMeds).length / entries.length) * 100)
      : 0;
  }, [entries]);

  const mostCommonSymptom = useMemo(() => {
    if (entries.length === 0) return '—';
    const topSymptom = entries.reduce<Record<string, number>>((acc, e) => {
      acc[e.symptom] = (acc[e.symptom] || 0) + 1;
      return acc;
    }, {});
    return Object.entries(topSymptom).sort((a, b) => b[1] - a[1])[0]?.[0] || '—';
  }, [entries]);

  return (
    <div className="w-full space-y-6 pb-12 selection:bg-[var(--accent)] selection:text-white relative">
      <header className="space-y-1.5 border-l-2 border-[var(--accent)] pl-4">
        <h1 className="text-xl font-bold text-[var(--text-primary)] uppercase tracking-wider">Patient Self-Reporting Simulation</h1>
        <p className="text-[var(--text-dim)] text-xs font-mono tracking-wide max-w-xl uppercase">
          Simulate and audit home-based patient portal logging feeds, symptom diaries, and medication compliance logs.
        </p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column: Logging & Metrics */}
        <div className="lg:col-span-7 space-y-6">
          
          {/* Simulation Controls Card */}
          <div className="glass-card rounded-2xl p-5 border border-white/[0.04]">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-sm font-bold text-[var(--text-primary)] uppercase tracking-wide flex items-center gap-2">
                <ClipboardList size={14} className="text-[var(--accent)]" />
                Simulate Patient Log Entry
              </h2>
              <button 
                onClick={() => setShowCheckIn(!showCheckIn)}
                className="btn btn-secondary text-xs uppercase tracking-wider"
              >
                {showCheckIn ? "Hide Portal Panel" : "Open Log Form"}
              </button>
            </div>

            {showCheckIn && (
              <form onSubmit={handleSubmitLog} className="space-y-4 pt-3 border-t border-white/[0.04]">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="section-label mb-1 block">Reported Symptom</label>
                    <select 
                      value={symptom}
                      onChange={e => setSymptom(e.target.value)}
                      className="w-full bg-[#0a0a0f] border border-zinc-800 rounded-xl p-2.5 text-xs text-[var(--text-primary)] focus:border-[var(--accent)] focus:outline-none"
                    >
                      {SYMPTOM_LIST.map(s => (
                        <option key={s} value={s}>{s}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="section-label mb-1 block">Severity Classification</label>
                    <div className="flex gap-2">
                      {(['mild', 'moderate', 'severe'] as Severity[]).map(s => (
                        <button
                          type="button"
                          key={s}
                          onClick={() => setSeverity(s)}
                          className={`flex-1 py-2 rounded-xl text-xs font-bold capitalize border transition-all ${
                            severity === s
                              ? 'bg-[var(--accent-muted)] border-[var(--accent-border)] text-[var(--accent)]'
                              : 'bg-transparent border-zinc-800 text-[var(--text-secondary)] hover:border-zinc-700'
                          }`}
                        >
                          {s}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="section-label mb-1 block">Sleep Duration: {sleepHours} Hours</label>
                    <input 
                      type="range"
                      min={0}
                      max={12}
                      step={0.5}
                      value={sleepHours}
                      onChange={e => setSleepHours(parseFloat(e.target.value))}
                      className="w-full accent-[var(--accent)]"
                    />
                  </div>

                  <div>
                    <label className="section-label mb-1 block">Medication Taken</label>
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => setTookMeds(true)}
                        className={`flex-1 py-2 rounded-xl text-xs font-bold border transition-all ${
                          tookMeds
                            ? 'bg-[var(--success-muted)] border-[var(--success-border)] text-[var(--success)]'
                            : 'bg-transparent border-zinc-800 text-[var(--text-secondary)]'
                        }`}
                      >
                        Yes, Compliant
                      </button>
                      <button
                        type="button"
                        onClick={() => setTookMeds(false)}
                        className={`flex-1 py-2 rounded-xl text-xs font-bold border transition-all ${
                          !tookMeds
                            ? 'bg-[var(--danger-muted)] border-[var(--danger-border)] text-[var(--danger)]'
                            : 'bg-transparent border-zinc-800 text-[var(--text-secondary)]'
                        }`}
                      >
                        No, Missed
                      </button>
                    </div>
                  </div>
                </div>

                <div>
                  <label className="section-label mb-1 block">Patient Notes</label>
                  <textarea 
                    value={notes}
                    onChange={e => setNotes(e.target.value)}
                    placeholder="Patient notes..."
                    rows={2}
                    className="w-full bg-[#0a0a0f] border border-zinc-800 rounded-xl p-3 text-xs text-[var(--text-primary)] focus:border-[var(--accent)] focus:outline-none resize-none"
                  />
                </div>

                <button type="submit" className="w-full btn btn-primary text-xs uppercase tracking-wider py-2.5">
                  Submit Log Entry to EMR
                </button>
              </form>
            )}
          </div>

          {/* Health Snapshot Vitals */}
          <div className="grid grid-cols-3 gap-4">
            <div className="glass-card rounded-2xl p-4 border border-white/[0.04] text-center">
              <Moon size={16} className="text-[var(--accent-blue)] mx-auto mb-1.5" />
              <div className="text-xl font-bold text-[var(--text-primary)] font-mono">{avgSleep}h</div>
              <div className="text-[9px] text-[var(--text-dim)] font-mono uppercase tracking-wide mt-0.5">Average Sleep</div>
            </div>
            <div className="glass-card rounded-2xl p-4 border border-white/[0.04] text-center">
              <Pill size={16} className="text-[var(--success)] mx-auto mb-1.5" />
              <div className="text-xl font-bold text-[var(--text-primary)] font-mono">{medCompliance}%</div>
              <div className="text-[9px] text-[var(--text-dim)] font-mono uppercase tracking-wide mt-0.5">Med Compliance</div>
            </div>
            <div className="glass-card rounded-2xl p-4 border border-white/[0.04] text-center">
              <AlertTriangle size={16} className="text-[var(--warning)] mx-auto mb-1.5" />
              <div className="text-xs font-bold text-[var(--text-primary)] truncate mt-1">{mostCommonSymptom}</div>
              <div className="text-[9px] text-[var(--text-dim)] font-mono uppercase tracking-wide mt-1">Top Symptom</div>
            </div>
          </div>

          {/* Recent Log Entries */}
          <div className="glass-card rounded-2xl p-5 border border-white/[0.04]">
            <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--text-primary)] mb-4 flex items-center gap-1.5">
              <Calendar size={13} className="text-[var(--accent)]" />
              Inbound Portal Logs
            </h3>
            <div className="space-y-3">
              {entries.slice(-5).reverse().map(entry => (
                <div 
                  key={entry.id}
                  className="flex items-center gap-3 rounded-xl p-3 bg-white/[0.01] border border-white/[0.03] hover:border-white/[0.06] transition-colors"
                >
                  <span 
                    className="w-2.5 h-2.5 rounded-full shrink-0" 
                    style={{ backgroundColor: SEVERITY_COLORS[entry.severity].dot }}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wide">{entry.symptom}</div>
                    <div className="text-[9px] text-[var(--text-dim)] font-mono uppercase mt-0.5">
                      Logged: {entry.date} • {entry.sleepHours}h Sleep • {entry.tookMeds ? "Compliant" : "Missed"}
                    </div>
                  </div>
                  <span 
                    className="px-2 py-0.5 rounded-full text-[9px] font-mono font-bold border uppercase"
                    style={{
                      backgroundColor: SEVERITY_COLORS[entry.severity].bg,
                      color: SEVERITY_COLORS[entry.severity].text,
                      borderColor: SEVERITY_COLORS[entry.severity].border
                    }}
                  >
                    {entry.severity}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Portal Message Simulator */}
        <div className="lg:col-span-5 space-y-6">
          <div className="glass-card rounded-2xl border border-white/[0.04] flex flex-col h-[400px]">
            <div className="panel-header bg-[rgba(15,15,17,0.5)] border-b border-[var(--border)] px-4 py-3 flex justify-between items-center">
              <div>
                <h3 className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider">Patient Engagement Sync</h3>
                <p className="text-[8px] text-[var(--success)] font-mono uppercase tracking-wider mt-0.5 flex items-center gap-1">
                  <span className="w-1 h-1 rounded-full bg-[var(--success)] animate-pulse" />
                  Simulator Mode Active
                </p>
              </div>
            </div>

            {/* Chat History */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3" style={{ maxHeight: '280px' }}>
              {messages.map(msg => (
                <div 
                  key={msg.id}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div 
                    className={`max-w-[85%] px-3 py-2 text-xs rounded-xl border ${
                      msg.role === 'user'
                        ? 'bg-[var(--accent-muted)] border-[var(--accent-border)] text-[var(--text-primary)]'
                        : 'bg-white/[0.02] border-white/[0.04] text-[var(--text-secondary)]'
                    }`}
                  >
                    {msg.text}
                  </div>
                </div>
              ))}
              {isTyping && (
                <div className="flex justify-start">
                  <div className="bg-white/[0.02] border border-white/[0.04] rounded-xl px-3 py-2 flex items-center gap-1">
                    <Loader2 size={10} className="animate-spin text-[var(--accent)]" />
                    <span className="text-[9px] font-mono text-[var(--text-dim)] uppercase">Generating log response...</span>
                  </div>
                </div>
              )}
              <div ref={scrollRef} />
            </div>

            {/* Chat Input */}
            <div className="p-3 border-t border-white/[0.04] bg-black/20">
              <div className="flex gap-2">
                <input 
                  type="text" 
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => { if(e.key === 'Enter') handleSendChat(); }}
                  placeholder="Simulate medical compliance inquiry..."
                  className="flex-1 bg-black/40 border border-zinc-800/80 rounded-lg px-3 py-1.5 text-xs text-[var(--text-primary)] placeholder-[var(--text-dim)] focus:outline-none focus:border-[var(--accent)]"
                />
                <button 
                  onClick={handleSendChat}
                  disabled={!input.trim()}
                  className="p-2 bg-[var(--accent)] text-white hover:bg-[var(--accent-hover)] rounded-lg disabled:opacity-30 transition-colors cursor-pointer"
                >
                  <Send size={12} />
                </button>
              </div>
            </div>
          </div>

          {/* Medical Disclaimer Panel */}
          <div className="rounded-xl p-4 bg-zinc-950/40 border border-zinc-800/60 flex items-start gap-3">
            <Info className="w-5 h-5 text-[var(--accent)] shrink-0 mt-0.5" />
            <p className="text-[10px] text-[var(--text-secondary)] font-mono uppercase tracking-wide leading-relaxed">
              <strong className="text-[var(--text-primary)] font-bold block mb-0.5">Clinical Simulator Notice</strong> 
              This portal simulates patients self-reporting diagnostics and treatment compliance. Always consult clinical practitioners for real diagnosis, treatment audits, or emergency medical review.
            </p>
          </div>
        </div>

      </div>
    </div>
  );
}
