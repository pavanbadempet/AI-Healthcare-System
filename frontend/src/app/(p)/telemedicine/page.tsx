"use client";

import { useState, useEffect } from "react";
import { getAppointments, bookAppointment, getDoctors, type Appointment } from "@/lib/api";
import { useAuthStore } from "@/lib/auth";
import { motion } from "framer-motion";
import { Video, Calendar, Clock, Stethoscope, FileText, CheckCircle2, ShieldAlert, Lock, Activity, Phone, MonitorSmartphone } from "lucide-react";

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
      const aptDate = new Date(`${dateStr}T${timeStr}:00`);
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
      <div className="w-full bg-[var(--bg-secondary)] border-b border-[var(--border)] px-4 py-1.5 flex justify-between items-center text-[11px] font-mono tracking-widest text-[var(--text-dim)] uppercase" role="status" aria-label="Telemedicine security status">
        <div className="flex gap-4">
          <span className="flex items-center gap-1.5 text-[var(--success)]"><Lock size={10} aria-hidden="true" /> SESSION PRIVACY CONTROLS ACTIVE</span>
          <span>PROTOCOL: WEBRTC TRANSPORT</span>
        </div>
        <div className="flex gap-4">
          <span>SERVER: CARE-VIDEO-US-EAST</span>
          <span>LATENCY: 8ms</span>
        </div>
      </div>

      <div className="p-6 md:p-8 max-w-[1800px] mx-auto space-y-6">
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }} className="flex flex-col md:flex-row md:items-end justify-between gap-4 pb-6 border-b border-[var(--border)]">
          <div>
            <h1 className="text-3xl font-semibold text-[var(--text-primary)] mb-1 tracking-tight flex items-center gap-3">
              Secure Telemedicine <span className="text-[11px] bg-[var(--bg-card)] border border-[var(--border)] px-2 py-1 rounded text-[var(--success)] uppercase tracking-widest align-middle">ACCESS CONTROLLED</span>
            </h1>
            <p className="text-[var(--text-secondary)] text-sm font-mono mt-1">Private video consultations and remote monitoring.</p>
          </div>
          
          <div className="flex gap-3">
            <button className="btn btn-primary text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-2" aria-label="Join active telemedicine call">
              <Phone size={14} aria-hidden="true" /> Join Active Call
            </button>
          </div>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Scheduling Form */}
          <div className="lg:col-span-1">
            <div className="panel p-6 h-full">
              <div className="flex items-center gap-2 mb-6 pb-4 border-b border-[var(--border)]">
                <Calendar size={18} className="text-[var(--accent)]" aria-hidden="true" />
                <h2 className="section-title">Schedule Encounter</h2>
              </div>
              
              <form onSubmit={handleBook} className="space-y-5">
                <div>
                  <label className="section-label mb-1.5 block" htmlFor="tele-doctor">Attending Physician</label>
                  <select 
                    id="tele-doctor"
                    value={selectedDoctor}
                    onChange={(e) => setSelectedDoctor(e.target.value)}
                    className="input-clinical"
                    required
                    aria-label="Select attending physician"
                  >
                    <option value="">-- SELECT SPECIALIST --</option>
                    {doctors.map(d => (
                      <option key={d.id} value={d.id}>DR. {d.name.toUpperCase()} ({d.specialization.toUpperCase()})</option>
                    ))}
                  </select>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="section-label mb-1.5 block" htmlFor="tele-date">Date</label>
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
                    <label className="section-label mb-1.5 block" htmlFor="tele-time">Time</label>
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
                  <label className="section-label mb-1.5 block" htmlFor="tele-notes">Clinical Notes / Reason</label>
                  <textarea 
                    id="tele-notes"
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="Brief description of symptoms or follow-up reason..."
                    className="input-clinical h-24 resize-none"
                    aria-label="Clinical notes for appointment"
                  />
                </div>

                <button 
                  type="submit" 
                  disabled={booking}
                  className="w-full py-2.5 bg-[var(--text-primary)] text-[var(--bg-primary)] text-xs font-bold uppercase tracking-widest hover:opacity-90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed mt-4"
                  aria-label={booking ? "Processing appointment" : "Confirm appointment booking"}
                >
                  {booking ? "PROCESSING..." : "CONFIRM APPOINTMENT"}
                </button>
              </form>
            </div>
          </div>

          {/* Appointments List */}
          <div className="lg:col-span-2">
            <div className="panel h-full flex flex-col">
              <div className="panel-header flex justify-between items-center">
                <h2 className="section-title flex items-center gap-2">
                  <Activity size={18} className="text-[var(--success)]" aria-hidden="true" /> Active Encounters
                </h2>
                <span className="text-[11px] bg-[var(--bg-card)] px-2 py-1 rounded text-[var(--text-dim)] font-mono border border-[var(--border)]">
                  {activeAppts.length} PENDING
                </span>
              </div>
              
              <div className="flex-1 overflow-auto p-0" role="list" aria-label="Active telemedicine encounters">
                {loading ? (
                  <div className="p-6 space-y-4 animate-pulse">
                    {[1,2,3].map(i => <div key={i} className="h-20 bg-[var(--bg-card)] rounded border border-[var(--border)]" />)}
                  </div>
                ) : activeAppts.length > 0 ? (
                  <div className="divide-y divide-[var(--border)]">
                    {activeAppts.map(apt => {
                      const d = new Date(apt.appointment_date);
                      return (
                        <div key={apt.id} className="p-5 hover:bg-[var(--bg-card)] transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-4 group" role="listitem">
                          <div className="flex items-start gap-4">
                            <div className="w-12 h-12 bg-[var(--accent-muted)] border border-[var(--accent-border)] rounded flex flex-col items-center justify-center text-[var(--accent)] shrink-0">
                              <span className="text-xs font-bold">{d.getDate()}</span>
                              <span className="text-[11px] font-mono uppercase">{d.toLocaleString('default', { month: 'short' })}</span>
                            </div>
                            <div>
                              <h3 className="text-[13px] font-bold text-[var(--text-primary)] uppercase tracking-wider mb-0.5">DR. {apt.doctor?.name.toUpperCase() || 'UNKNOWN'}</h3>
                              <p className="mono-meta mb-1">{apt.doctor?.specialization.toUpperCase() || 'SPECIALIST'} | ENCOUNTER #{apt.id}</p>
                              <div className="flex items-center gap-3 text-[11px] text-[var(--text-secondary)] font-mono">
                                <span className="flex items-center gap-1"><Clock size={12} className="text-[var(--accent)]" aria-hidden="true" /> {d.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                                <span className="flex items-center gap-1 text-[var(--success)]"><CheckCircle2 size={12} aria-hidden="true" /> CONFIRMED</span>
                              </div>
                            </div>
                          </div>
                          
                          <div className="flex items-center gap-3">
                            <button className="btn btn-secondary text-[11px] font-bold uppercase tracking-widest flex items-center gap-2" aria-label={`View intake for encounter ${apt.id}`}>
                              <FileText size={14} aria-hidden="true" /> Intake
                            </button>
                            <button className="px-4 py-2 bg-[var(--success-muted)] border border-[var(--success-border)] text-[var(--success)] text-[11px] font-bold uppercase tracking-widest rounded hover:bg-[var(--success)] hover:text-[var(--bg-primary)] transition-colors flex items-center gap-2" aria-label={`Join video call for encounter ${apt.id}`}>
                              <Video size={14} aria-hidden="true" /> Join
                            </button>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                ) : (
                  <div className="h-[300px] flex flex-col items-center justify-center text-[var(--text-dim)]">
                    <MonitorSmartphone size={48} className="mb-4 opacity-20" aria-hidden="true" />
                    <p className="text-xs font-mono uppercase tracking-widest">No active telemedicine encounters scheduled.</p>
                  </div>
                )}
              </div>
              
              {/* Past Appointments Section */}
              <div className="border-t border-[var(--border)] bg-[var(--bg-primary)]">
                <div className="px-6 py-3 border-b border-[var(--border)]">
                  <h3 className="section-label">Encounter History</h3>
                </div>
                <div className="divide-y divide-[var(--border-subtle)] max-h-[200px] overflow-auto">
                  {pastAppts.length > 0 ? (
                    pastAppts.map(apt => (
                      <div key={apt.id} className="px-6 py-3 flex justify-between items-center">
                        <div className="flex items-center gap-3">
                          <span className="w-1.5 h-1.5 rounded-full bg-[var(--border-focus)]" aria-hidden="true"></span>
                          <span className="text-[11px] font-mono text-[var(--text-secondary)]">{new Date(apt.appointment_date).toLocaleDateString()}</span>
                          <span className="text-xs font-bold text-[var(--text-primary)]">DR. {apt.doctor?.name.toUpperCase()}</span>
                        </div>
                        <span className="section-label bg-[var(--bg-card)] px-2 py-0.5 rounded border border-[var(--border)]">COMPLETED</span>
                      </div>
                    ))
                  ) : (
                    <div className="px-6 py-4 section-label">NO ENCOUNTER HISTORY FOUND.</div>
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
