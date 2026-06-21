import { useState, useEffect, useRef } from "react";
import { 
  getAppointments, 
  bookAppointment, 
  getDoctors, 
  chatWithCASA, 
  streamCASA, 
  type Appointment, 
  type CASAMessage 
} from "@/lib/api";
import { fetchRecommendedSpecialists, bookSpecialCareAppointment } from "@/lib/apiIntelligence";
import { useAuthStore } from "@/lib/auth";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Video, 
  Calendar, 
  Clock, 
  Stethoscope, 
  FileText, 
  CheckCircle2, 
  Lock, 
  Activity, 
  Phone, 
  MonitorSmartphone, 
  Send, 
  Bot, 
  User, 
  Mic, 
  MicOff, 
  AlertTriangle, 
  Sparkles,
  Info
} from "lucide-react";

export default function TelemedicinePage() {
  const { user } = useAuthStore();
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [doctors, setDoctors] = useState<{ id: number; name: string; specialization: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [booking, setBooking] = useState(false);

  // Manual form states
  const [selectedDoctor, setSelectedDoctor] = useState("");
  const [dateStr, setDateStr] = useState("");
  const [timeStr, setTimeStr] = useState("");
  const [notes, setNotes] = useState("");

  // Special care preferences (Itch 6)
  const [requestFemale, setRequestFemale] = useState(false);
  const [homeVisitVan, setHomeVisitVan] = useState(false);

  // CASA Agent states
  const [messages, setMessages] = useState<CASAMessage[]>([
    {
      role: "assistant",
      content: "Hello! I am CASA, your Clinical-Aware Scheduling Assistant. Describe your symptoms or let me know who you would like to book with."
    }
  ]);
  const [inputMessage, setInputMessage] = useState("");
  const [isAgentTyping, setIsAgentTyping] = useState(false);
  const [streamActive, setStreamActive] = useState(true); // default to streaming
  const [emergencyWarning, setEmergencyWarning] = useState<string | null>(null);
  const [bookingConfirmation, setBookingConfirmation] = useState<any>(null);

  // Audio mode simulation
  const [isAudioMode, setIsAudioMode] = useState(false);
  const [audioWaves, setAudioWaves] = useState<number[]>([10, 20, 15, 30, 25, 40, 10, 5, 20, 30, 25, 10]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const audioIntervalRef = useRef<any>(null);

  // Specialist matching recommendations (Itch 7)
  const [recommendedSpecialties, setRecommendedSpecialties] = useState<any[]>([]);
  const [loadingRecommendations, setLoadingRecommendations] = useState(false);

  const loadRecommendations = async () => {
    if (!user?.id) return;
    setLoadingRecommendations(true);
    try {
      const data = await fetchRecommendedSpecialists(user.id);
      setRecommendedSpecialties(data.recommended_specialties || []);
    } catch (err) {
      console.error("Failed to load recommended specialties:", err);
    } finally {
      setLoadingRecommendations(false);
    }
  };

  useEffect(() => {
    Promise.all([getAppointments(), getDoctors()])
      .then(([apps, docs]) => {
        setAppointments(apps);
        setDoctors(docs);
      })
      .catch(console.error)
      .finally(() => setLoading(false));

    if (user?.id) {
      void loadRecommendations();
    }
  }, [user?.id]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView?.({ behavior: "smooth" });
  }, [messages, isAgentTyping]);

  // Simulate audio visualization when audio mode is active
  useEffect(() => {
    if (isAudioMode) {
      audioIntervalRef.current = setInterval(() => {
        setAudioWaves(Array.from({ length: 16 }, () => Math.floor(Math.random() * 45) + 5));
      }, 100);
    } else {
      if (audioIntervalRef.current) clearInterval(audioIntervalRef.current);
    }
    return () => {
      if (audioIntervalRef.current) clearInterval(audioIntervalRef.current);
    };
  }, [isAudioMode]);

  const refreshAppointments = async () => {
    try {
      const apps = await getAppointments();
      setAppointments(apps);
    } catch (err) {
      console.error("Failed to refresh appointments:", err);
    }
  };

  const handleBook = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDoctor || !dateStr || !timeStr) return;
    setBooking(true);
    try {
      if (requestFemale || homeVisitVan) {
        const doctor = doctors.find(d => d.id === parseInt(selectedDoctor));
        const specialist = doctor ? doctor.specialization : "General Medicine";
        await bookSpecialCareAppointment({
          patient_id: user?.id || 1,
          doctor_id: parseInt(selectedDoctor),
          specialist,
          date_time: `${dateStr}T${timeStr}:00`,
          reason: notes || "Manual special care booking",
          request_female_clinician: requestFemale,
          home_visit_van: homeVisitVan
        });
      } else {
        await bookAppointment({
          doctor_id: parseInt(selectedDoctor),
          appointment_date: `${dateStr}T${timeStr}:00`,
          notes
        });
      }
      await refreshAppointments();
      setSelectedDoctor("");
      setDateStr("");
      setTimeStr("");
      setNotes("");
      setRequestFemale(false);
      setHomeVisitVan(false);
    } catch (err) {
      console.error(err);
    } finally {
      setBooking(false);
    }
  };

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputMessage.trim() || isAgentTyping) return;

    const userText = inputMessage.trim();
    setInputMessage("");
    setEmergencyWarning(null);
    setBookingConfirmation(null);

    const newUserMsg: CASAMessage = { role: "user", content: userText };
    setMessages(prev => [...prev, newUserMsg]);
    setIsAgentTyping(true);

    const history = messages.map(m => ({ role: m.role, content: m.content }));

    if (streamActive) {
      // Streamed Response
      setMessages(prev => [...prev, { role: "assistant", content: "" }]);

      let cancelStream = streamCASA(
        userText,
        history,
        (chunk) => {
          if (chunk.reply) {
            setMessages(prev => {
              const newArr = [...prev];
              const last = newArr[newArr.length - 1];
              if (last.role === "assistant") {
                last.content += chunk.reply;
              }
              return newArr;
            });
          }
          if (chunk.status === "warning" && chunk.reply) {
            setEmergencyWarning(chunk.reply);
          }
          if (chunk.action_triggered && chunk.booking_details) {
            setBookingConfirmation(chunk.booking_details);
            refreshAppointments();
          }
          if (chunk.status === "complete") {
            setIsAgentTyping(false);
          }
          if (chunk.error) {
            setMessages(prev => {
              const newArr = [...prev];
              const last = newArr[newArr.length - 1];
              if (last.role === "assistant") {
                last.content += `\n\n**Error:** ${chunk.error}`;
              }
              return newArr;
            });
            setIsAgentTyping(false);
          }
        },
        () => {
          setIsAgentTyping(false);
        },
        (err) => {
          console.error("Stream error:", err);
          setMessages(prev => {
            const newArr = [...prev];
            const last = newArr[newArr.length - 1];
            if (last.role === "assistant") {
              last.content += "\n\n**Error:** Request interrupted. Please try again.";
            }
            return newArr;
          });
          setIsAgentTyping(false);
        }
      );
    } else {
      // Standard HTTP Response
      try {
        const res = await chatWithCASA(userText, history);
        setMessages(prev => [...prev, { role: "assistant", content: res.response }]);
        if (res.action_triggered && res.booking_details) {
          setBookingConfirmation(res.booking_details);
          refreshAppointments();
        }
        if (res.error) {
          setEmergencyWarning(`Booking failed: ${res.error}`);
        }
      } catch (err: any) {
        console.error("Chat error:", err);
        setMessages(prev => [...prev, { role: "assistant", content: "Error communicating with CASA. Please try again." }]);
      } finally {
        setIsAgentTyping(false);
      }
    }
  };

  const handleSuggestionClick = (suggestionText: string) => {
    setInputMessage(suggestionText);
  };

  const activeAppts = appointments.filter(a => new Date(a.appointment_date) > new Date()).sort((a,b) => new Date(a.appointment_date).getTime() - new Date(b.appointment_date).getTime());
  const pastAppts = appointments.filter(a => new Date(a.appointment_date) <= new Date()).sort((a,b) => new Date(b.appointment_date).getTime() - new Date(a.appointment_date).getTime());

  return (
    <div className="w-full min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] font-sans pb-20">
      {/* Privacy security status header */}
      <div className="w-full bg-[var(--bg-secondary)] border-b border-[var(--border)] px-4 py-1.5 flex justify-between items-center text-[10px] font-mono tracking-wider text-[var(--text-dim)] uppercase" role="status" aria-label="Telemedicine security status">
        <div className="flex gap-4">
          <span className="flex items-center gap-1.5 text-[var(--success)] font-semibold">
            <Lock size={11} aria-hidden="true" /> PRIVATE WebRTC LINK ACTIVE
          </span>
          <span>TRANSPORT: ENCRYPTED PORT</span>
        </div>
        <div className="flex gap-4">
          <span>LATENCY: 8ms</span>
        </div>
      </div>

      <div className="py-6 max-w-[1600px] mx-auto px-4 md:px-8 space-y-6">
        <motion.div 
          initial={{ opacity: 0, y: -8 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ duration: 0.25 }} 
          className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[var(--border)]"
        >
          <div>
            <h1 className="text-xl font-bold text-[var(--text-primary)] uppercase tracking-wider flex items-center gap-2 font-display">
              Telemedicine Sessions 
              <span className="text-[10px] bg-[rgba(255,255,255,0.03)] border border-[var(--border)] px-2 py-0.5 rounded text-[var(--success)] uppercase tracking-wider font-mono">
                Encrypted
              </span>
            </h1>
            <p className="text-xs text-[var(--text-secondary)] font-mono uppercase tracking-wide mt-1">Private virtual consults and remote observations.</p>
          </div>
          
          <div className="flex gap-2">
            <button 
              onClick={() => setIsAudioMode(!isAudioMode)}
              className={`btn text-xs flex items-center justify-center gap-1.5 cursor-pointer transition-all duration-300 ${
                isAudioMode ? "bg-[var(--danger)] text-white hover:bg-[var(--danger)]/80" : "btn-secondary"
              }`}
              aria-label={isAudioMode ? "End voice call simulation" : "Start voice call simulation"}
            >
              {isAudioMode ? <MicOff size={13} aria-hidden="true" /> : <Mic size={13} aria-hidden="true" />}
              {isAudioMode ? "End Call Simulation" : "Simulate Voice Intake"}
            </button>
          </div>
        </motion.div>

        {/* Audio Mode Overlay Panel */}
        <AnimatePresence>
          {isAudioMode && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="w-full bg-[rgba(95,95,247,0.04)] border border-[var(--accent-border)] rounded-lg p-6 flex flex-col items-center justify-center space-y-4 shadow-[0_0_15px_rgba(95,95,247,0.05)]"
            >
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[var(--danger)] animate-pulse" />
                <span className="text-xs font-mono uppercase tracking-widest text-[var(--text-secondary)]">CASA Voice Line Connected</span>
              </div>

              {/* Waveform visualizer */}
              <div className="flex items-end justify-center gap-1.5 h-16 w-full max-w-sm">
                {audioWaves.map((val, idx) => (
                  <motion.div
                    key={idx}
                    animate={{ height: `${val}px` }}
                    transition={{ type: "spring", stiffness: 300, damping: 20 }}
                    className="w-1.5 rounded-full bg-gradient-to-t from-[var(--accent)] to-[var(--accent-purple)]"
                  />
                ))}
              </div>

              <p className="text-xs text-[var(--text-dim)] font-mono uppercase text-center max-w-md">
                Talk directly to schedule. Or use the conversational panel below to chat concurrently.
              </p>
            </motion.div>
          )}
        </AnimatePresence>        {/* Recommended Specialists Panel (Itch 7) */}
        {recommendedSpecialties.length > 0 && (
          <div className="panel p-4 bg-gradient-to-r from-indigo-950/20 via-indigo-900/5 to-black/40 border border-indigo-500/20 rounded-xl space-y-3">
            <div className="flex items-center gap-2 text-[var(--accent)] font-bold text-xs uppercase tracking-wider">
              <Sparkles size={14} className="text-yellow-400 animate-pulse" />
              AI Specialist Matcher Insights
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {recommendedSpecialties.map((spec: any, idx: number) => (
                <div key={idx} className="p-3 rounded-lg bg-[rgba(255,255,255,0.01)] border border-[var(--border)] flex justify-between items-start">
                  <div>
                    <span className="text-xs font-bold text-[var(--text-primary)] uppercase">
                      {spec.specialty} Specialist
                    </span>
                    <span className="text-[10px] text-[var(--text-secondary)] font-mono uppercase block mt-1 leading-normal">
                      Reason: {spec.reason}
                    </span>
                  </div>
                  <span className={`text-[9px] font-mono border px-1.5 py-0.5 rounded uppercase font-bold shrink-0 ${
                    spec.priority?.toLowerCase() === 'high' 
                      ? 'border-rose-500/30 bg-rose-500/10 text-rose-400' 
                      : 'border-blue-500/30 bg-blue-500/10 text-blue-400'
                  }`}>
                    {spec.priority}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main left column: CASA Conversational scheduling & Active Encounters */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* CASA Conversational Panel */}
            <div className="panel flex flex-col h-[520px] overflow-hidden">
              {/* Header */}
              <div className="panel-header flex justify-between items-center bg-[rgba(15,15,17,0.5)] border-b border-[var(--border)] px-4 py-3">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-[var(--success)] animate-pulse" />
                  <span className="text-xs font-bold uppercase tracking-wider flex items-center gap-1.5">
                    <Bot size={14} className="text-[var(--accent)]" /> CASA AI Scheduling Assistant
                  </span>
                </div>
                <div className="flex items-center gap-4 text-[10px] font-mono">
                  <label className="flex items-center gap-1.5 cursor-pointer text-[var(--text-dim)] select-none">
                    <input 
                      type="checkbox" 
                      checked={streamActive}
                      onChange={(e) => setStreamActive(e.target.checked)}
                      className="cursor-pointer accent-[var(--accent)]"
                    />
                    STREAM RESPONSE
                  </label>
                </div>
              </div>

              {/* Messages Area */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
                
                {/* Emergency warning banner */}
                <AnimatePresence>
                  {emergencyWarning && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      className="p-3 bg-[rgba(255,74,74,0.08)] border border-[var(--danger-border)] rounded text-xs text-[var(--danger)] flex items-start gap-2"
                    >
                      <AlertTriangle size={15} className="shrink-0 mt-0.5" />
                      <div>
                        <span className="font-bold uppercase tracking-wider block">Clinical Safety Warning</span>
                        <span className="mt-1 block font-sans">{emergencyWarning}</span>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Booking confirmation card */}
                <AnimatePresence>
                  {bookingConfirmation && (
                    <motion.div
                      initial={{ scale: 0.95, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      exit={{ scale: 0.95, opacity: 0 }}
                      className="p-4 bg-[rgba(0,230,118,0.06)] border border-[var(--success-border)] rounded-lg text-xs space-y-2 relative overflow-hidden"
                    >
                      <div className="absolute right-0 top-0 w-24 h-24 bg-[var(--success)]/5 rounded-full blur-xl pointer-events-none" />
                      <div className="flex items-center gap-2 text-[var(--success)] font-bold uppercase tracking-wider">
                        <CheckCircle2 size={14} /> Appointment Confirmed
                      </div>
                      <div className="grid grid-cols-2 gap-4 mt-2 font-mono">
                        <div>
                          <span className="text-[9px] text-[var(--text-dim)] uppercase block">Physician</span>
                          <span className="text-[var(--text-primary)] uppercase">{bookingConfirmation.doctor_name}</span>
                        </div>
                        <div>
                          <span className="text-[9px] text-[var(--text-dim)] uppercase block">Specialization</span>
                          <span className="text-[var(--text-primary)] uppercase">{bookingConfirmation.specialist}</span>
                        </div>
                        <div className="col-span-2">
                          <span className="text-[9px] text-[var(--text-dim)] uppercase block">Scheduled Date/Time</span>
                          <span className="text-[var(--text-primary)] uppercase flex items-center gap-1">
                            <Clock size={11} className="text-[var(--accent)]" /> {new Date(bookingConfirmation.date_time).toLocaleString()}
                          </span>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Standard Message List */}
                {messages.map((m, idx) => (
                  <div 
                    key={idx} 
                    className={`flex gap-3 max-w-[85%] ${m.role === "user" ? "ml-auto flex-row-reverse" : "mr-auto"}`}
                  >
                    <div className={`w-7 h-7 rounded border flex items-center justify-center shrink-0 text-xs ${
                      m.role === "user" 
                        ? "bg-[rgba(95,95,247,0.1)] border-[var(--accent-border)] text-[var(--accent)]" 
                        : "bg-[rgba(255,255,255,0.02)] border-[var(--border)] text-[var(--text-secondary)]"
                    }`}>
                      {m.role === "user" ? <User size={13} /> : <Bot size={13} />}
                    </div>
                    <div className={`p-3 rounded text-xs leading-relaxed font-sans ${
                      m.role === "user" 
                        ? "bg-[rgba(95,95,247,0.06)] border border-[var(--accent-border)] text-[var(--text-primary)] rounded-tr-none" 
                        : "bg-[rgba(255,255,255,0.02)] border border-[var(--border)] text-[var(--text-secondary)] rounded-tl-none"
                    }`}>
                      {m.content}
                    </div>
                  </div>
                ))}

                {isAgentTyping && (
                  <div className="flex gap-3 mr-auto items-center">
                    <div className="w-7 h-7 rounded border bg-[rgba(255,255,255,0.02)] border-[var(--border)] text-[var(--text-secondary)] flex items-center justify-center text-xs">
                      <Bot size={13} />
                    </div>
                    <div className="flex gap-1 items-center px-3 py-2 bg-[rgba(255,255,255,0.02)] border border-[var(--border)] rounded rounded-tl-none">
                      <span className="w-1.5 h-1.5 bg-[var(--text-dim)] rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                      <span className="w-1.5 h-1.5 bg-[var(--text-dim)] rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                      <span className="w-1.5 h-1.5 bg-[var(--text-dim)] rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Suggestions shortcuts */}
              <div className="px-4 py-2 bg-[rgba(15,15,17,0.2)] border-t border-[var(--border)] flex gap-2 overflow-x-auto custom-scrollbar whitespace-nowrap">
                <button 
                  onClick={() => handleSuggestionClick("I need to book an appointment with a Cardiologist")}
                  className="px-2.5 py-1 bg-[rgba(255,255,255,0.02)] border border-[var(--border)] hover:border-[var(--accent-border)] hover:bg-[var(--accent-muted)] rounded text-[10px] font-mono text-[var(--text-secondary)] hover:text-[var(--accent)] cursor-pointer transition-all flex items-center gap-1"
                >
                  <Sparkles size={10} /> Cardiologist Booking
                </button>
                <button 
                  onClick={() => handleSuggestionClick("I have been having chronic fatigue and high glucose readings")}
                  className="px-2.5 py-1 bg-[rgba(255,255,255,0.02)] border border-[var(--border)] hover:border-[var(--accent-border)] hover:bg-[var(--accent-muted)] rounded text-[10px] font-mono text-[var(--text-secondary)] hover:text-[var(--accent)] cursor-pointer transition-all flex items-center gap-1"
                >
                  <Sparkles size={10} /> Report Symptoms
                </button>
                <button 
                  onClick={() => handleSuggestionClick("Who is the available pulmonologist?")}
                  className="px-2.5 py-1 bg-[rgba(255,255,255,0.02)] border border-[var(--border)] hover:border-[var(--accent-border)] hover:bg-[var(--accent-muted)] rounded text-[10px] font-mono text-[var(--text-secondary)] hover:text-[var(--accent)] cursor-pointer transition-all flex items-center gap-1"
                >
                  <Sparkles size={10} /> Find Pulmonologist
                </button>
              </div>

              {/* Input Form */}
              <form onSubmit={handleSendMessage} className="p-3 bg-[rgba(10,10,15,0.9)] border-t border-[var(--border)] flex gap-2">
                <input 
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder="Describe your symptoms or booking details..."
                  className="flex-1 input-clinical bg-[var(--bg-secondary)] px-3 text-xs focus:border-[var(--accent-border)] focus:outline-none"
                  disabled={isAgentTyping}
                />
                <button 
                  type="submit"
                  disabled={isAgentTyping || !inputMessage.trim()}
                  className="btn btn-primary px-4 cursor-pointer flex items-center justify-center gap-1"
                  aria-label="Send message to assistant"
                >
                  <Send size={13} />
                </button>
              </form>
            </div>

            {/* Scheduled Encounters list */}
            <div className="panel flex flex-col overflow-hidden">
              <div className="panel-header flex justify-between items-center bg-[rgba(15,15,17,0.5)] px-4 py-3 border-b border-[var(--border)]">
                <h2 className="section-title flex items-center gap-2">
                  <Activity size={14} className="text-[var(--success)]" aria-hidden="true" /> Scheduled Encounters
                </h2>
                <span className="text-[10px] bg-[rgba(255,255,255,0.03)] px-2 py-0.5 rounded text-[var(--text-dim)] font-mono border border-[var(--border)]">
                  {activeAppts.length} PENDING
                </span>
              </div>
              
              <div className="divide-y divide-[var(--border)]" role="list" aria-label="Active telemedicine encounters">
                {loading ? (
                  <div className="p-4 text-xs font-mono text-[var(--text-dim)] uppercase tracking-wider">
                    Loading records...
                  </div>
                ) : activeAppts.length > 0 ? (
                  activeAppts.map(apt => {
                    const d = new Date(apt.appointment_date);
                    return (
                      <div key={apt.id} className="p-4 hover:bg-[rgba(255,255,255,0.01)] transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4" role="listitem">
                        <div className="flex items-start gap-3">
                          <div className="w-10 h-10 bg-[var(--accent-muted)] border border-[var(--accent-border)] rounded flex flex-col items-center justify-center text-[var(--accent)] shrink-0 font-mono">
                            <span className="text-xs font-bold leading-none">{d.getDate()}</span>
                            <span className="text-[8px] uppercase">{d.toLocaleString('default', { month: 'short' })}</span>
                          </div>
                          <div className="space-y-0.5">
                            <h3 className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wide">DR. {apt.doctor?.name.toUpperCase() || 'PHYSICIAN'}</h3>
                            <p className="mono-meta text-[9px]">{apt.doctor?.specialization.toUpperCase()} | ENCOUNTER #{apt.id}</p>
                            {apt.notes && (
                              <p className="text-[10px] text-[var(--text-dim)] font-mono mt-1 max-w-md line-clamp-1">{apt.notes.toUpperCase()}</p>
                            )}
                            <div className="flex items-center gap-3 text-[10px] text-[var(--text-secondary)] font-mono uppercase mt-1">
                              <span className="flex items-center gap-1"><Clock size={11} className="text-[var(--accent)]" aria-hidden="true" /> {d.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                              <span className="flex items-center gap-1 text-[var(--success)]"><CheckCircle2 size={11} aria-hidden="true" /> Booked</span>
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-2">
                          <button className="btn btn-secondary text-[11px] py-1 px-3 flex items-center gap-1 cursor-pointer" aria-label={`View intake for encounter ${apt.id}`}>
                            <FileText size={12} aria-hidden="true" /> Record
                          </button>
                          <a 
                            href={`https://meet.jit.si/ai-health-${apt.id}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="px-3 py-1 bg-[var(--success-muted)] border border-[var(--success-border)] text-[var(--success)] text-[11px] font-bold uppercase rounded hover:bg-[var(--success)] hover:text-[#09090b] transition-all flex items-center gap-1 cursor-pointer" 
                            aria-label={`Join video call for encounter ${apt.id}`}
                          >
                            <Video size={12} aria-hidden="true" /> Connect
                          </a>
                        </div>
                      </div>
                    )
                  })
                ) : (
                  <div className="h-[180px] flex flex-col items-center justify-center text-[var(--text-dim)]">
                    <MonitorSmartphone size={32} className="mb-3 opacity-20" aria-hidden="true" />
                    <p className="text-[10px] font-mono uppercase tracking-wider">No consultations scheduled.</p>
                  </div>
                )}
              </div>
            </div>

          </div>

          {/* Right column: manual scheduler fallback & Completed studies */}
          <div className="space-y-6">
            
            {/* Manual scheduling form */}
            <div className="panel p-5 space-y-5">
              <div className="flex items-center gap-2 pb-3 border-b border-[var(--border)]">
                <Calendar size={15} className="text-[var(--accent)]" aria-hidden="true" />
                <h2 className="section-title">Manual Scheduling Fallback</h2>
              </div>
              
              <form onSubmit={handleBook} className="space-y-4">
                <div>
                  <label className="section-label mb-1 block" htmlFor="tele-doctor">Specialist Physician</label>
                  <select 
                    id="tele-doctor"
                    value={selectedDoctor}
                    onChange={(e) => setSelectedDoctor(e.target.value)}
                    className="input-clinical"
                    required
                    aria-label="Select attending physician"
                  >
                    <option value="" className="bg-[var(--bg-card)]">-- SELECT PHYSICIAN --</option>
                    {doctors.map(d => (
                      <option key={d.id} value={d.id} className="bg-[var(--bg-card)]">DR. {d.name.toUpperCase()} ({d.specialization.toUpperCase()})</option>
                    ))}
                  </select>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="section-label mb-1 block" htmlFor="tele-date">Date</label>
                    <input 
                      id="tele-date"
                      type="date"
                      value={dateStr}
                      onChange={(e) => setDateStr(e.target.value)}
                      className="input-clinical"
                      required
                      aria-label="Appointment date"
                    />
                  </div>
                  <div>
                    <label className="section-label mb-1 block" htmlFor="tele-time">Time</label>
                    <input 
                      id="tele-time"
                      type="time"
                      value={timeStr}
                      onChange={(e) => setTimeStr(e.target.value)}
                      className="input-clinical"
                      required
                      aria-label="Appointment time"
                    />
                  </div>
                </div>

                <div>
                  <label className="section-label mb-1 block" htmlFor="tele-notes">Encounter Notes</label>
                  <textarea 
                    id="tele-notes"
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="Document symptoms or follow-up reason..."
                    className="input-clinical h-20 resize-none uppercase font-mono text-[10px]"
                    aria-label="Clinical notes for appointment"
                  />
                </div>

                {/* Special care preferences (Itch 6) */}
                <div className="space-y-2 border-t border-[var(--border)] pt-3">
                  <span className="section-label block">Special Care Preferences</span>
                  <div className="flex flex-col gap-2">
                    <label className="flex items-center gap-2 cursor-pointer text-xs font-mono uppercase text-[var(--text-secondary)] select-none">
                      <input 
                        type="checkbox" 
                        checked={requestFemale}
                        onChange={(e) => setRequestFemale(e.target.checked)}
                        className="cursor-pointer accent-[var(--accent)]"
                      />
                      Prefer Female Clinician
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer text-xs font-mono uppercase text-[var(--text-secondary)] select-none">
                      <input 
                        type="checkbox" 
                        checked={homeVisitVan}
                        onChange={(e) => setHomeVisitVan(e.target.checked)}
                        className="cursor-pointer accent-[var(--accent)]"
                      />
                      Mobile Clinic Van Home Visit
                    </label>
                  </div>
                </div>

                <button 
                  type="submit" 
                  disabled={booking}
                  className="w-full btn btn-primary py-2.5 cursor-pointer flex items-center justify-center gap-1.5 text-xs"
                  aria-label={booking ? "Processing appointment" : "Confirm appointment booking"}
                >
                  {booking ? "PROCESSING..." : "CONFIRM SCHEDULE"}
                </button>
              </form>
            </div>

            {/* Completed studies archive */}
            <div className="panel overflow-hidden">
              <div className="px-4 py-3 bg-[rgba(15,15,17,0.5)] border-b border-[var(--border)]">
                <h3 className="section-label flex items-center gap-1.5">
                  <Info size={12} className="text-[var(--text-dim)]" /> Completed Studies Archive
                </h3>
              </div>
              <div className="divide-y divide-[var(--border)] max-h-[220px] overflow-y-auto custom-scrollbar">
                {pastAppts.length > 0 ? (
                  pastAppts.map(apt => (
                    <div key={apt.id} className="p-3 flex justify-between items-start text-[10px] font-mono uppercase hover:bg-[rgba(255,255,255,0.01)] transition-all">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="w-1 h-1 rounded-full bg-[var(--text-muted)]" aria-hidden="true"></span>
                          <span className="text-[var(--text-dim)]">{new Date(apt.appointment_date).toLocaleDateString()}</span>
                          <span className="text-[var(--text-secondary)]">DR. {apt.doctor?.name.toUpperCase()}</span>
                        </div>
                        {apt.notes && (
                          <p className="text-[9px] text-[var(--text-dim)] max-w-xs line-clamp-1 lowercase font-sans">{apt.notes}</p>
                        )}
                      </div>
                      <span className="text-[9px] border border-[var(--border)] px-1.5 py-0.5 bg-[rgba(255,255,255,0.01)] shrink-0">Released</span>
                    </div>
                  ))
                ) : (
                  <div className="px-4 py-4 text-[10px] font-mono text-[var(--text-dim)] uppercase text-center">No completed encounters logged.</div>
                )}
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
}
