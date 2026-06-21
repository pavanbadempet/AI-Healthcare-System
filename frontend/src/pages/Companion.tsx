import { useState, useRef, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Smile, Sun, Cloud, Heart, Activity, FileText, ClipboardList,
  Send, Moon, Pill, ThermometerSun, TrendingUp, ChevronRight,
  Sparkles, Calendar, BarChart3, MessageCircleHeart, PlusCircle,
  Check, X, AlertTriangle, Loader2,
} from 'lucide-react';
import TopNav from '@/components/layout/TopNav';

/* ─────────────────────────────────────────────────
   TYPE DEFINITIONS
   ───────────────────────────────────────────────── */
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
  role: 'user' | 'cara';
  text: string;
  timestamp: Date;
}

/* ─────────────────────────────────────────────────
   CONSTANTS
   ───────────────────────────────────────────────── */
const SEVERITY_COLORS: Record<Severity, { bar: string; bg: string; text: string; border: string; dot: string }> = {
  mild:     { bar: '#34d399', bg: 'rgba(52,211,153,0.15)', text: '#6ee7b7', border: 'rgba(52,211,153,0.4)', dot: '#34d399' },
  moderate: { bar: '#fbbf24', bg: 'rgba(251,191,36,0.15)', text: '#fcd34d', border: 'rgba(251,191,36,0.4)', dot: '#fbbf24' },
  severe:   { bar: '#f87171', bg: 'rgba(248,113,113,0.15)', text: '#fca5a5', border: 'rgba(248,113,113,0.4)', dot: '#f87171' },
};

const SYMPTOM_LIST = [
  'Joint Pain', 'Fatigue', 'Headache', 'Nausea', 'Shortness of Breath',
  'Muscle Ache', 'Dizziness', 'Chest Tightness', 'Swelling', 'Insomnia',
  'Brain Fog', 'Stomach Pain', 'Back Pain', 'Anxiety', 'Palpitations',
];

const DAY_LABELS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

const COMPANION_RESPONSES: Record<string, string[]> = {
  greeting: [
    "Hey there! 🌸 I'm Cara, your health companion. How are you feeling today?",
    "Welcome back! ☀️ Remember, it's completely okay to have tough days. I'm right here with you.",
    "Hi friend! 🌷 I noticed you haven't logged in a while. No pressure — whenever you're ready, I'm here.",
  ],
  mild: [
    "I'm glad it's a mild day! 💚 Keep doing those small things that help — stretching, hydration, rest. You're doing great!",
    "A mild day is still worth celebrating! 🎉 Remember, progress isn't always linear, and gentle days matter too.",
    "That's wonderful to hear! 🌿 Your body is telling you it's managing well. Keep listening to it.",
  ],
  moderate: [
    "I hear you — moderate days can be draining. 💛 Have you tried a warm compress or some gentle movement today?",
    "Moderate flares are your body asking for extra care. 🧸 Maybe take a shorter walk and stay extra hydrated?",
    "Hang in there. 💛 Moderate doesn't mean you're failing — it means you're honest about how you feel.",
  ],
  severe: [
    "I'm so sorry you're going through this. ❤️ Please remember this flare won't last forever. Can you rest and reach out to your doctor?",
    "Severe days are hard. 💗 You are incredibly brave for showing up. Please be extra gentle with yourself today.",
    "I wish I could take this pain away. ❤️‍🩹 If symptoms persist, please consider contacting your healthcare provider. You deserve proper support.",
  ],
  general: [
    "That's a really important observation. I've noted it in your log! 📝",
    "Thank you for sharing that with me. Tracking these patterns helps your doctor help you better. 💜",
    "I appreciate you being so open. Remember — no question or feeling is too small to mention. 🌻",
  ],
  sleep: [
    "Sleep is such a crucial part of recovery! 😴 Even small improvements in sleep quality can reduce flare severity.",
    "If you're having trouble sleeping, try dimming screens an hour before bed and keeping the room cool. 🌙",
  ],
  medication: [
    "Great job staying on top of your meds! 💊 Consistency really makes a difference over time.",
    "If you missed a dose, don't worry — just take it when you remember and get back on track. No judgment here! 💪",
  ],
};

function getCaraResponse(input: string, severity?: Severity): string {
  const lower = input.toLowerCase();
  if (severity) {
    const responses = COMPANION_RESPONSES[severity];
    return responses[Math.floor(Math.random() * responses.length)];
  }
  if (lower.includes('sleep') || lower.includes('tired') || lower.includes('insomnia')) {
    return COMPANION_RESPONSES.sleep[Math.floor(Math.random() * COMPANION_RESPONSES.sleep.length)];
  }
  if (lower.includes('medicine') || lower.includes('pill') || lower.includes('medication') || lower.includes('med')) {
    return COMPANION_RESPONSES.medication[Math.floor(Math.random() * COMPANION_RESPONSES.medication.length)];
  }
  if (lower.includes('pain') || lower.includes('hurt') || lower.includes('ache') || lower.includes('sore')) {
    return COMPANION_RESPONSES.severe[Math.floor(Math.random() * COMPANION_RESPONSES.severe.length)];
  }
  if (lower.includes('good') || lower.includes('better') || lower.includes('great') || lower.includes('fine')) {
    return COMPANION_RESPONSES.mild[Math.floor(Math.random() * COMPANION_RESPONSES.mild.length)];
  }
  return COMPANION_RESPONSES.general[Math.floor(Math.random() * COMPANION_RESPONSES.general.length)];
}

/* ─────────────────────────────────────────────────
   SEED DATA GENERATOR — last 7 days of demo entries
   ───────────────────────────────────────────────── */
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

/* ─────────────────────────────────────────────────
   FLOATING CLOUD CARD COMPONENT
   ───────────────────────────────────────────────── */
function CloudCard({
  icon: Icon, label, value, delay, onClick, active,
}: {
  icon: React.ElementType; label: string; value: string; delay: number; onClick?: () => void; active?: boolean;
}) {
  return (
    <motion.button
      onClick={onClick}
      initial={{ y: 20, opacity: 0 }}
      animate={{ y: [0, -8, 0], opacity: 1 }}
      transition={{ y: { repeat: Infinity, duration: 4 + delay, ease: 'easeInOut' }, opacity: { duration: 0.6, delay: delay * 0.15 } }}
      className="group relative cursor-pointer"
      style={{ animationDelay: `${delay * 200}ms` }}
    >
      <div
        className={`relative rounded-3xl px-6 py-5 transition-all duration-300
          ${active
            ? 'bg-white/20 border-2 border-white/40 shadow-[0_0_30px_rgba(255,255,255,0.2)]'
            : 'bg-white/10 border border-white/20 hover:bg-white/15 hover:border-white/30 hover:shadow-[0_0_20px_rgba(255,255,255,0.1)]'
          }
          backdrop-blur-xl`}
      >
        <div className="flex items-center gap-3 mb-2">
          <div className={`p-2 rounded-xl ${active ? 'bg-white/25' : 'bg-white/10 group-hover:bg-white/15'} transition-colors`}>
            <Icon className="w-5 h-5 text-white/90" />
          </div>
          <span className="text-sm font-semibold text-white/90 tracking-wide">{label}</span>
        </div>
        <p className="text-xs text-white/60 pl-1">{value}</p>
        {active && (
          <motion.div
            layoutId="cloud-indicator"
            className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-8 h-1 rounded-full bg-white/60"
          />
        )}
      </div>
    </motion.button>
  );
}

/* ─────────────────────────────────────────────────
   WEEKLY FLARE BAR CHART
   ───────────────────────────────────────────────── */
function FlareChart({ entries }: { entries: SymptomEntry[] }) {
  const last7 = useMemo(() => {
    const days: (SymptomEntry | null)[] = [];
    for (let i = 6; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      const key = d.toISOString().split('T')[0];
      const entry = entries.find(e => e.date === key);
      days.push(entry || null);
    }
    return days;
  }, [entries]);

  const severityHeight: Record<Severity, number> = { mild: 35, moderate: 65, severe: 100 };

  return (
    <div className="rounded-3xl p-6 bg-white/[0.06] border border-white/10 backdrop-blur-xl">
      <div className="flex items-center gap-2 mb-5">
        <BarChart3 className="w-5 h-5 text-orange-300" />
        <h3 className="text-white/90 font-semibold text-lg">Weekly Flare Tracker</h3>
      </div>
      <div className="flex items-end justify-between gap-2 h-32">
        {last7.map((entry, i) => {
          const today = new Date();
          today.setDate(today.getDate() - (6 - i));
          const dayLabel = DAY_LABELS[today.getDay()];
          const sev = entry?.severity || null;
          const height = sev ? severityHeight[sev] : 8;
          const color = sev ? SEVERITY_COLORS[sev].bar : '#4b5563';

          return (
            <div key={i} className="flex flex-col items-center gap-2 flex-1">
              <motion.div
                initial={{ height: 0 }}
                animate={{ height: `${height}%` }}
                transition={{ duration: 0.8, delay: i * 0.08, ease: 'easeOut' }}
                className="w-full max-w-[36px] rounded-xl relative overflow-hidden"
                style={{ backgroundColor: `${color}30` }}
              >
                <motion.div
                  initial={{ height: 0 }}
                  animate={{ height: '100%' }}
                  transition={{ duration: 0.6, delay: i * 0.08 + 0.3 }}
                  className="absolute bottom-0 w-full rounded-xl"
                  style={{ backgroundColor: color }}
                />
              </motion.div>
              <span className="text-[11px] text-white/50 font-medium">{dayLabel}</span>
            </div>
          );
        })}
      </div>
      {/* Legend */}
      <div className="flex gap-4 mt-4 justify-center">
        {(['mild', 'moderate', 'severe'] as Severity[]).map(s => (
          <div key={s} className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: SEVERITY_COLORS[s].dot }} />
            <span className="text-[11px] text-white/50 capitalize">{s}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────
   CHECK-IN FORM
   ───────────────────────────────────────────────── */
function CheckInForm({
  onSubmit,
  onCancel,
}: {
  onSubmit: (entry: Omit<SymptomEntry, 'id'>) => void;
  onCancel: () => void;
}) {
  const [symptom, setSymptom] = useState(SYMPTOM_LIST[0]);
  const [severity, setSeverity] = useState<Severity>('mild');
  const [sleepHours, setSleepHours] = useState(7);
  const [tookMeds, setTookMeds] = useState(true);
  const [notes, setNotes] = useState('');

  const handleSubmit = () => {
    onSubmit({
      date: new Date().toISOString().split('T')[0],
      symptom,
      severity,
      sleepHours,
      tookMeds,
      notes,
    });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="rounded-3xl p-6 bg-white/[0.06] border border-white/10 backdrop-blur-xl"
    >
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-2">
          <ClipboardList className="w-5 h-5 text-orange-300" />
          <h3 className="text-white/90 font-semibold text-lg">Daily Check-In</h3>
        </div>
        <button onClick={onCancel} className="p-1.5 rounded-xl hover:bg-white/10 transition-colors">
          <X className="w-4 h-4 text-white/50" />
        </button>
      </div>

      {/* Symptom Selection */}
      <div className="mb-4">
        <label className="text-sm text-white/60 mb-2 block font-medium">What's bothering you?</label>
        <div className="flex flex-wrap gap-2">
          {SYMPTOM_LIST.map(s => (
            <button
              key={s}
              onClick={() => setSymptom(s)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200
                ${symptom === s
                  ? 'bg-orange-500/30 border border-orange-400/50 text-orange-200'
                  : 'bg-white/5 border border-white/10 text-white/50 hover:bg-white/10 hover:text-white/70'
                }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Severity */}
      <div className="mb-4">
        <label className="text-sm text-white/60 mb-2 block font-medium">How severe?</label>
        <div className="flex gap-2">
          {(['mild', 'moderate', 'severe'] as Severity[]).map(s => (
            <button
              key={s}
              onClick={() => setSeverity(s)}
              className={`flex-1 py-2.5 rounded-2xl text-sm font-semibold capitalize transition-all duration-200 border
                ${severity === s
                  ? `border-transparent text-black`
                  : 'border-white/10 text-white/50 hover:bg-white/5'
                }`}
              style={severity === s ? { backgroundColor: SEVERITY_COLORS[s].bar } : undefined}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Sleep */}
      <div className="mb-4">
        <label className="text-sm text-white/60 mb-2 block font-medium">
          <Moon className="w-3.5 h-3.5 inline mr-1.5 -mt-0.5" />
          Sleep last night: <span className="text-white/80">{sleepHours}h</span>
        </label>
        <input
          type="range"
          min={0}
          max={12}
          step={0.5}
          value={sleepHours}
          onChange={e => setSleepHours(parseFloat(e.target.value))}
          className="w-full accent-orange-400"
        />
        <div className="flex justify-between text-[10px] text-white/30 mt-1">
          <span>0h</span><span>6h</span><span>12h</span>
        </div>
      </div>

      {/* Medication */}
      <div className="mb-5">
        <label className="text-sm text-white/60 mb-2 block font-medium">
          <Pill className="w-3.5 h-3.5 inline mr-1.5 -mt-0.5" />
          Did you take your medication today?
        </label>
        <div className="flex gap-2">
          <button
            onClick={() => setTookMeds(true)}
            className={`flex-1 py-2 rounded-2xl text-sm font-medium transition-all border
              ${tookMeds
                ? 'bg-emerald-500/20 border-emerald-400/40 text-emerald-300'
                : 'border-white/10 text-white/40 hover:bg-white/5'
              }`}
          >
            <Check className="w-4 h-4 inline mr-1 -mt-0.5" /> Yes
          </button>
          <button
            onClick={() => setTookMeds(false)}
            className={`flex-1 py-2 rounded-2xl text-sm font-medium transition-all border
              ${!tookMeds
                ? 'bg-red-500/20 border-red-400/40 text-red-300'
                : 'border-white/10 text-white/40 hover:bg-white/5'
              }`}
          >
            <X className="w-4 h-4 inline mr-1 -mt-0.5" /> Missed
          </button>
        </div>
      </div>

      {/* Notes */}
      <div className="mb-5">
        <label className="text-sm text-white/60 mb-2 block font-medium">Any additional notes? (optional)</label>
        <textarea
          value={notes}
          onChange={e => setNotes(e.target.value)}
          placeholder="How are you really feeling today..."
          rows={2}
          className="w-full rounded-2xl bg-white/5 border border-white/10 px-4 py-3 text-sm text-white/80
            placeholder:text-white/25 focus:outline-none focus:border-orange-400/40 focus:ring-1 focus:ring-orange-400/20
            resize-none transition-colors"
        />
      </div>

      <button
        onClick={handleSubmit}
        className="w-full py-3 rounded-2xl font-semibold text-sm transition-all duration-300
          bg-gradient-to-r from-orange-500 to-rose-500 text-white
          hover:from-orange-400 hover:to-rose-400 hover:shadow-[0_0_30px_rgba(251,146,60,0.3)]
          active:scale-[0.98]"
      >
        <Sparkles className="w-4 h-4 inline mr-2 -mt-0.5" />
        Log Check-In
      </button>
    </motion.div>
  );
}

/* ─────────────────────────────────────────────────
   COMPANION CHAT
   ───────────────────────────────────────────────── */
function CompanionChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'cara',
      text: COMPANION_RESPONSES.greeting[Math.floor(Math.random() * COMPANION_RESPONSES.greeting.length)],
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, isTyping]);

  const sendMessage = () => {
    if (!input.trim()) return;
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      text: input.trim(),
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    // Simulate Cara's thoughtful response
    setTimeout(() => {
      const response: ChatMessage = {
        id: `cara-${Date.now()}`,
        role: 'cara',
        text: getCaraResponse(userMsg.text),
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, response]);
      setIsTyping(false);
    }, 800 + Math.random() * 1200);
  };

  return (
    <div className="rounded-3xl bg-white/[0.06] border border-white/10 backdrop-blur-xl flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-white/10 flex items-center gap-3">
        <div className="relative">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-orange-400 to-rose-400 flex items-center justify-center">
            <Smile className="w-5 h-5 text-white" />
          </div>
          <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-400 rounded-full border-2 border-[#0a0a1a]" />
        </div>
        <div>
          <h3 className="text-white/90 font-semibold text-sm">Cara</h3>
          <p className="text-[11px] text-emerald-400/80">Online • Here for you</p>
        </div>
        <div className="ml-auto">
          <MessageCircleHeart className="w-5 h-5 text-orange-300/50" />
        </div>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-3 min-h-0" style={{ maxHeight: '340px' }}>
        <AnimatePresence>
          {messages.map(msg => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[85%] px-4 py-3 text-sm leading-relaxed
                  ${msg.role === 'user'
                    ? 'bg-orange-500/20 border border-orange-400/30 text-white/90 rounded-2xl rounded-tr-md'
                    : 'bg-white/[0.07] border border-white/10 text-white/80 rounded-2xl rounded-tl-md'
                  }`}
              >
                {msg.text}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        {isTyping && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-start">
            <div className="bg-white/[0.07] border border-white/10 rounded-2xl rounded-tl-md px-4 py-3 flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-white/30 animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-2 h-2 rounded-full bg-white/30 animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-2 h-2 rounded-full bg-white/30 animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </motion.div>
        )}
      </div>

      {/* Input */}
      <div className="px-4 py-3 border-t border-white/10">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && sendMessage()}
            placeholder="Tell Cara how you're feeling..."
            className="flex-1 bg-white/5 border border-white/10 rounded-2xl px-4 py-2.5 text-sm text-white/80
              placeholder:text-white/25 focus:outline-none focus:border-orange-400/40 transition-colors"
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim()}
            className="p-2.5 rounded-2xl bg-gradient-to-br from-orange-500 to-rose-500 text-white
              hover:from-orange-400 hover:to-rose-400 disabled:opacity-30 disabled:cursor-not-allowed
              transition-all active:scale-95"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────
   BIOMETRICS MINI CARD
   ───────────────────────────────────────────────── */
function BiometricsMini({ entries }: { entries: SymptomEntry[] }) {
  const avgSleep = entries.length > 0
    ? (entries.reduce((s, e) => s + e.sleepHours, 0) / entries.length).toFixed(1)
    : '—';
  const medCompliance = entries.length > 0
    ? Math.round((entries.filter(e => e.tookMeds).length / entries.length) * 100)
    : 0;
  const topSymptom = entries.length > 0
    ? entries.reduce<Record<string, number>>((acc, e) => { acc[e.symptom] = (acc[e.symptom] || 0) + 1; return acc; }, {})
    : {};
  const mostCommon = Object.entries(topSymptom).sort((a, b) => b[1] - a[1])[0]?.[0] || '—';

  return (
    <div className="rounded-3xl p-6 bg-white/[0.06] border border-white/10 backdrop-blur-xl">
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp className="w-5 h-5 text-orange-300" />
        <h3 className="text-white/90 font-semibold text-lg">Health Snapshot</h3>
      </div>
      <div className="grid grid-cols-3 gap-3">
        <div className="rounded-2xl bg-white/[0.05] border border-white/10 p-4 text-center">
          <Moon className="w-5 h-5 text-blue-300 mx-auto mb-1" />
          <div className="text-xl font-bold text-white/90">{avgSleep}h</div>
          <div className="text-[11px] text-white/40 mt-0.5">Avg Sleep</div>
        </div>
        <div className="rounded-2xl bg-white/[0.05] border border-white/10 p-4 text-center">
          <Pill className="w-5 h-5 text-emerald-300 mx-auto mb-1" />
          <div className="text-xl font-bold text-white/90">{medCompliance}%</div>
          <div className="text-[11px] text-white/40 mt-0.5">Med Compliance</div>
        </div>
        <div className="rounded-2xl bg-white/[0.05] border border-white/10 p-4 text-center">
          <AlertTriangle className="w-5 h-5 text-orange-300 mx-auto mb-1" />
          <div className="text-sm font-bold text-white/90 mt-0.5">{mostCommon}</div>
          <div className="text-[11px] text-white/40 mt-0.5">Top Symptom</div>
        </div>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────
   RECENT LOGS LIST
   ───────────────────────────────────────────────── */
function RecentLogs({ entries }: { entries: SymptomEntry[] }) {
  const recent = entries.slice(-5).reverse();
  return (
    <div className="rounded-3xl p-6 bg-white/[0.06] border border-white/10 backdrop-blur-xl">
      <div className="flex items-center gap-2 mb-4">
        <Calendar className="w-5 h-5 text-orange-300" />
        <h3 className="text-white/90 font-semibold text-lg">Recent Entries</h3>
      </div>
      {recent.length === 0 ? (
        <p className="text-sm text-white/40 text-center py-4">No entries yet. Try logging a check-in!</p>
      ) : (
        <div className="space-y-2">
          {recent.map(entry => (
            <div
              key={entry.id}
              className="flex items-center gap-3 rounded-2xl p-3 bg-white/[0.03] border border-white/[0.06] hover:bg-white/[0.06] transition-colors"
            >
              <div
                className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                style={{ backgroundColor: SEVERITY_COLORS[entry.severity].dot }}
              />
              <div className="flex-1 min-w-0">
                <div className="text-sm text-white/80 font-medium">{entry.symptom}</div>
                <div className="text-[11px] text-white/40">{entry.date} • {entry.sleepHours}h sleep • {entry.tookMeds ? 'Took meds' : 'Missed meds'}</div>
              </div>
              <span
                className="text-[11px] font-semibold px-2.5 py-1 rounded-full capitalize"
                style={{
                  backgroundColor: SEVERITY_COLORS[entry.severity].bg,
                  color: SEVERITY_COLORS[entry.severity].text,
                  border: `1px solid ${SEVERITY_COLORS[entry.severity].border}`,
                }}
              >
                {entry.severity}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ─────────────────────────────────────────────────
   DISCLAIMER BANNER
   ───────────────────────────────────────────────── */
function Disclaimer() {
  return (
    <div className="rounded-2xl p-4 bg-amber-500/[0.06] border border-amber-500/20 flex items-start gap-3">
      <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
      <p className="text-xs text-amber-200/70 leading-relaxed">
        <strong className="text-amber-300">Medical Disclaimer:</strong> Cara is an AI wellness companion and does not provide medical diagnoses,
        treatment recommendations, or emergency care. Always consult a qualified healthcare professional for medical advice,
        diagnosis, or treatment. If you are experiencing a medical emergency, please call your local emergency services immediately.
      </p>
    </div>
  );
}

/* ═══════════════════════════════════════════════════
   MAIN PAGE COMPONENT
   ═══════════════════════════════════════════════════ */
export default function Companion() {
  const [entries, setEntries] = useState<SymptomEntry[]>(generateSeedData);
  const [showCheckIn, setShowCheckIn] = useState(false);
  const [activeSection, setActiveSection] = useState<string>('daily');

  const handleCheckIn = (data: Omit<SymptomEntry, 'id'>) => {
    const newEntry: SymptomEntry = { ...data, id: `entry-${Date.now()}` };
    setEntries(prev => [...prev, newEntry]);
    setShowCheckIn(false);
  };

  return (
    <div className="min-h-screen bg-[#0a0a1a]">
      <TopNav />

      {/* ── SUNSET SKY HERO ── */}
      <div
        className="relative overflow-hidden"
        style={{
          background: 'linear-gradient(180deg, #1a0a2e 0%, #2d1b4e 15%, #5c2d82 30%, #c06040 50%, #e88d50 65%, #f4a460 78%, #f8c07c 88%, #fde8c8 100%)',
          minHeight: '340px',
        }}
      >
        {/* Animated clouds */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          {[...Array(6)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute rounded-full blur-3xl opacity-20"
              style={{
                width: `${200 + i * 80}px`,
                height: `${60 + i * 20}px`,
                background: 'white',
                top: `${10 + i * 12}%`,
                left: `${-10 + i * 18}%`,
              }}
              animate={{
                x: [0, 40, 0],
                opacity: [0.15, 0.25, 0.15],
              }}
              transition={{
                duration: 8 + i * 2,
                repeat: Infinity,
                ease: 'easeInOut',
                delay: i * 1.5,
              }}
            />
          ))}
        </div>

        {/* Hero content */}
        <div className="relative z-10 max-w-7xl mx-auto px-4 pt-24 pb-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center mb-8"
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 border border-white/20 backdrop-blur-sm mb-4">
              <Sun className="w-4 h-4 text-amber-200" />
              <span className="text-xs font-medium text-white/80">Your Personal Health Companion</span>
            </div>
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-3" style={{ fontFamily: "'Inter', sans-serif", textShadow: '0 2px 20px rgba(0,0,0,0.3)' }}>
              Good {new Date().getHours() < 12 ? 'Morning' : new Date().getHours() < 18 ? 'Afternoon' : 'Evening'} ☀️
            </h1>
            <p className="text-white/60 text-lg max-w-md mx-auto">
              How are you feeling today? Let's track your wellness together.
            </p>
          </motion.div>

          {/* Cloud cards row */}
          <div className="flex flex-wrap justify-center gap-4">
            <CloudCard
              icon={ClipboardList}
              label="Daily Log"
              value="Track symptoms & mood"
              delay={0}
              active={activeSection === 'daily'}
              onClick={() => { setActiveSection('daily'); setShowCheckIn(true); }}
            />
            <CloudCard
              icon={Activity}
              label="Biometrics"
              value="Sleep, meds & vitals"
              delay={1}
              active={activeSection === 'bio'}
              onClick={() => setActiveSection('bio')}
            />
            <CloudCard
              icon={FileText}
              label="Doctor Notes"
              value="SOAP note summaries"
              delay={2}
              active={activeSection === 'notes'}
              onClick={() => setActiveSection('notes')}
            />
            <CloudCard
              icon={Heart}
              label="Health History"
              value="Past conditions & trends"
              delay={3}
              active={activeSection === 'history'}
              onClick={() => setActiveSection('history')}
            />
          </div>
        </div>

        {/* Bottom gradient fade to dark */}
        <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-[#0a0a1a] to-transparent" />
      </div>

      {/* ── MAIN CONTENT ── */}
      <div className="max-w-7xl mx-auto px-4 -mt-8 pb-16 relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

          {/* LEFT COLUMN — Chart, Check-in, Biometrics, Logs */}
          <div className="lg:col-span-7 space-y-6">
            {/* Check-in or Prompt */}
            <AnimatePresence mode="wait">
              {showCheckIn ? (
                <CheckInForm
                  key="checkin"
                  onSubmit={handleCheckIn}
                  onCancel={() => setShowCheckIn(false)}
                />
              ) : (
                <motion.button
                  key="prompt"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  onClick={() => setShowCheckIn(true)}
                  className="w-full rounded-3xl p-5 bg-gradient-to-r from-orange-500/10 to-rose-500/10 border border-orange-400/20
                    hover:border-orange-400/40 hover:shadow-[0_0_30px_rgba(251,146,60,0.1)] transition-all duration-300 text-left
                    flex items-center gap-4 group"
                >
                  <div className="p-3 rounded-2xl bg-orange-500/20 group-hover:bg-orange-500/30 transition-colors">
                    <PlusCircle className="w-6 h-6 text-orange-300" />
                  </div>
                  <div>
                    <div className="text-white/80 font-semibold text-sm">Log Today's Check-In</div>
                    <div className="text-white/40 text-xs mt-0.5">Track your symptoms, sleep, and medications</div>
                  </div>
                  <ChevronRight className="w-5 h-5 text-white/30 ml-auto group-hover:text-orange-300 transition-colors" />
                </motion.button>
              )}
            </AnimatePresence>

            <FlareChart entries={entries} />
            <BiometricsMini entries={entries} />
            <RecentLogs entries={entries} />
          </div>

          {/* RIGHT COLUMN — Companion Chat */}
          <div className="lg:col-span-5 space-y-6">
            <CompanionChat />
            <Disclaimer />
          </div>
        </div>
      </div>
    </div>
  );
}
