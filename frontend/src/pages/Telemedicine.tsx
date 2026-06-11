
import { useState, useEffect } from "react";
import { getAppointments, bookAppointment, getDoctors, type Appointment } from "@/lib/api";
import { useAuthStore } from "@/lib/auth";
import { motion } from "framer-motion";
import { Video, Calendar, Clock, Stethoscope, FileText, CheckCircle2, Lock, Activity, Phone, MonitorSmartphone } from "lucide-react";

export default function TelemedicinePage() {
  const { user } = useAuthStore();
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [doctors, setDoctors] = useState<{ id: number; name: string; specialization: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [booking, setBooking] = useState(false);

  const [selectedDoctor, setSelectedDoctor] = useState("");
  const [dateStr, setDateStr] = useState("");
  const [timeStr, setTimeStr] = useState("");
  const [notes, setNotes] = useState("");

  useEffect(() => {
    Promise.all([getAppointments(), getDoctors()])
      .then(([apps, docs]) => {
        setAppointments(apps);
        setDoctors(docs);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleBook = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDoctor || !dateStr || !timeStr) return;
    setBooking(true);
    try {
      await bookAppointment({
        doctor_id: parseInt(selectedDoctor),
        appointment_date: `${dateStr}T${timeStr}:00`,
        notes
      });
      const apps = await getAppointments();
      setAppointments(apps);
      setSelectedDoctor("");
      setDateStr("");
      setTimeStr("");
      setNotes("");
    } catch (err) {
      console.error(err);
    } finally {
      setBooking(false);
    }
  };

  const activeAppts = appointments.filter(a => new Date(a.appointment_date) > new Date()).sort((a,b) => new Date(a.appointment_date).getTime() - new Date(b.appointment_date).getTime());
  const pastAppts = appointments.filter(a => new Date(a.appointment_date) <= new Date()).sort((a,b) => new Date(b.appointment_date).getTime() - new Date(a.appointment_date).getTime());

  return (
    <div className="w-full min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] font-sans selection:bg-[var(--accent)] selection:text-white pb-20">
      {/* Privacy status header */}
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

      <div className="py-6 max-w-[1600px] mx-auto space-y-6">
        <motion.div 
          initial={{ opacity: 0, y: -8 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ duration: 0.25 }} 
          className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[var(--border)]"
        >
          <div>
            <h1 className="text-xl font-bold text-[var(--text-primary)] uppercase tracking-wider flex items-center gap-2">
              Telemedicine Sessions 
              <span className="text-[10px] bg-[rgba(255,255,255,0.03)] border border-[var(--border)] px-2 py-0.5 rounded text-[var(--success)] uppercase tracking-wider font-mono">
                Encrypted
              </span>
            </h1>
            <p className="text-xs text-[var(--text-secondary)] font-mono uppercase tracking-wide mt-1">Private virtual consults and remote observations.</p>
          </div>
          
          <div className="flex gap-2">
            <button className="btn btn-primary text-xs flex items-center justify-center gap-1.5 cursor-pointer" aria-label="Join active telemedicine call">
              <Phone size={13} aria-hidden="true" /> Join Active Call
            </button>
          </div>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Scheduling Form */}
          <div className="lg:col-span-1">
            <div className="panel p-5 h-full space-y-5">
              <div className="flex items-center gap-2 pb-3 border-b border-[var(--border)]">
                <Calendar size={15} className="text-[var(--accent)]" aria-hidden="true" />
                <h2 className="section-title">Schedule Consult</h2>
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
                    className="input-clinical h-24 resize-none uppercase font-mono"
                    aria-label="Clinical notes for appointment"
                  />
                </div>

                <button 
                  type="submit" 
                  disabled={booking}
                  className="w-full btn btn-primary py-2.5 cursor-pointer flex items-center justify-center gap-1.5"
                  aria-label={booking ? "Processing appointment" : "Confirm appointment booking"}
                >
                  {booking ? "PROCESSING..." : "CONFIRM SCHEDULE"}
                </button>
              </form>
            </div>
          </div>

          {/* Appointments List */}
          <div className="lg:col-span-2">
            <div className="panel h-full flex flex-col justify-between overflow-hidden">
              <div className="panel-header flex justify-between items-center bg-[rgba(15,15,17,0.5)]">
                <h2 className="section-title flex items-center gap-2">
                  <Activity size={14} className="text-[var(--success)]" aria-hidden="true" /> Scheduled Encounters
                </h2>
                <span className="text-[10px] bg-[rgba(255,255,255,0.03)] px-2 py-0.5 rounded text-[var(--text-dim)] font-mono border border-[var(--border)]">
                  {activeAppts.length} PENDING
                </span>
              </div>
              
              <div className="flex-1 overflow-auto divide-y divide-[var(--border)]" role="list" aria-label="Active telemedicine encounters">
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
                            <div className="flex items-center gap-3 text-[10px] text-[var(--text-secondary)] font-mono uppercase">
                              <span className="flex items-center gap-1"><Clock size={11} className="text-[var(--accent)]" aria-hidden="true" /> {d.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                              <span className="flex items-center gap-1 text-[var(--success)]"><CheckCircle2 size={11} aria-hidden="true" /> Booked</span>
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-2">
                          <button className="btn btn-secondary text-[11px] py-1 px-3 flex items-center gap-1 cursor-pointer" aria-label={`View intake for encounter ${apt.id}`}>
                            <FileText size={12} aria-hidden="true" /> Record
                          </button>
                          <button className="px-3 py-1 bg-[var(--success-muted)] border border-[var(--success-border)] text-[var(--success)] text-[11px] font-bold uppercase rounded hover:bg-[var(--success)] hover:text-[#09090b] transition-all flex items-center gap-1 cursor-pointer" aria-label={`Join video call for encounter ${apt.id}`}>
                            <Video size={12} aria-hidden="true" /> Connect
                          </button>
                        </div>
                      </div>
                    )
                  })
                ) : (
                  <div className="h-[240px] flex flex-col items-center justify-center text-[var(--text-dim)]">
                    <MonitorSmartphone size={36} className="mb-3 opacity-20" aria-hidden="true" />
                    <p className="text-[10px] font-mono uppercase tracking-wider">No consultations scheduled.</p>
                  </div>
                )}
              </div>
              
              {/* Past Appointments Section */}
              <div className="border-t border-[var(--border)] bg-[rgba(15,15,17,0.5)]">
                <div className="px-4 py-2.5 border-b border-[var(--border)]">
                  <h3 className="section-label">Completed Studies</h3>
                </div>
                <div className="divide-y divide-[var(--border-subtle)] max-h-[140px] overflow-auto">
                  {pastAppts.length > 0 ? (
                    pastAppts.map(apt => (
                      <div key={apt.id} className="px-4 py-2 flex justify-between items-center text-[10px] font-mono uppercase">
                        <div className="flex items-center gap-2">
                          <span className="w-1 h-1 rounded-full bg-[var(--text-muted)]" aria-hidden="true"></span>
                          <span className="text-[var(--text-dim)]">{new Date(apt.appointment_date).toLocaleDateString()}</span>
                          <span className="text-[var(--text-secondary)]">DR. {apt.doctor?.name.toUpperCase()}</span>
                        </div>
                        <span className="section-label border border-[var(--border)] px-1.5 py-0.5 bg-[rgba(255,255,255,0.01)]">Released</span>
                      </div>
                    ))
                  ) : (
                    <div className="px-4 py-3 text-[10px] font-mono text-[var(--text-dim)] uppercase">No completed encounters logged.</div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
