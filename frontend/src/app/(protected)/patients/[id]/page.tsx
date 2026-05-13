"use client";

import { useEffect, useState } from "react";
import { useAuthStore } from "@/lib/auth";
import { Activity, Thermometer, Droplets, HeartPulse, Stethoscope, ChevronLeft, Download, ShieldAlert, FileDigit, BrainCircuit } from "lucide-react";
import Link from "next/link";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

export default function PatientEMRView({ params }: { params: { id: string } }) {
  const { user } = useAuthStore();
  const [mounted, setMounted] = useState(false);
  const [vitals, setVitals] = useState<{ time: string; hr: number; bp: number; o2: number }[]>([]);

  useEffect(() => {
    setMounted(true);
    // Simulate real-time FHIR vitals stream
    const initVitals = Array.from({ length: 20 }, (_, i) => ({
      time: `-${20 - i}m`,
      hr: 75 + Math.sin(i) * 5 + Math.random() * 2,
      bp: 120 + Math.cos(i) * 10,
      o2: 98 - (Math.random() > 0.8 ? 1 : 0)
    }));
    setVitals(initVitals);

    const interval = setInterval(() => {
      setVitals(prev => {
        const next = [...prev.slice(1)];
        const last = prev[prev.length - 1];
        next.push({
          time: 'NOW',
          hr: last.hr + (Math.random() - 0.5) * 2,
          bp: last.bp + (Math.random() - 0.5) * 2,
          o2: 98 - (Math.random() > 0.9 ? 1 : 0)
        });
        return next;
      });
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  if (!mounted) return null;

  const mrn = `MRN-${(parseInt(params.id) * 1024 + 100000).toString().substring(0,6)}`;

  return (
    <div className="w-full min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] font-sans selection:bg-[var(--accent)] selection:text-white pb-20">
      {/* Top Status Bar */}
      <div className="w-full bg-[var(--danger-muted)] border-b border-[var(--danger-border)] px-4 py-1.5 flex justify-between items-center text-[11px] font-bold font-mono tracking-widest text-[var(--danger)] uppercase" role="alert" aria-label="Critical patient alert">
        <div className="flex gap-4">
          <span className="flex items-center gap-1.5"><AlertPulse /> CRITICAL PRIORITY LEVEL 1</span>
          <span>ICU-A BED 04</span>
        </div>
        <div className="flex gap-4">
          <span>CODE STATUS: FULL CODE</span>
          <span>ALLERGIES: PENICILLIN</span>
        </div>
      </div>

      <div className="p-6 md:p-8 max-w-[1800px] mx-auto space-y-6">
        {/* Header */}
        <header className="flex flex-col md:flex-row md:items-start justify-between gap-6 pb-6 border-b border-[var(--border)]">
          <div>
            <Link href="/patients" className="inline-flex items-center gap-2 text-[var(--text-dim)] hover:text-[var(--text-primary)] text-[11px] uppercase tracking-widest font-bold mb-4 transition-colors">
              <ChevronLeft size={14} aria-hidden="true" /> Back to Registry
            </Link>
            <h1 className="text-3xl font-semibold text-[var(--text-primary)] tracking-tight mb-2">
              Doe, John <span className="text-[var(--text-secondary)] font-mono text-sm ml-2">{mrn}</span>
            </h1>
            <p className="text-[var(--text-secondary)] text-sm font-mono flex items-center gap-4">
              <span>DOB: 1985-04-12 (38Y)</span>
              <span>SEX: M</span>
              <span>WT: 82.5 KG</span>
              <span>HT: 180 CM</span>
            </p>
          </div>
          <div className="flex gap-3">
            <button className="btn btn-secondary text-xs font-semibold uppercase tracking-wider flex items-center gap-2" aria-label="Export CCDA document">
              <FileDigit size={14} aria-hidden="true" /> Export CCDA
            </button>
            <button className="btn btn-primary text-xs font-semibold uppercase tracking-wider flex items-center gap-2" aria-label="Run AI diagnostic analysis">
              <BrainCircuit size={14} aria-hidden="true" /> Run AI Diagnostic
            </button>
          </div>
        </header>

        <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
          {/* Left Column: Vitals & Labs */}
          <div className="xl:col-span-1 space-y-6">
            <div className="panel p-5" role="region" aria-label="Live vital signs telemetry">
              <h3 className="section-label mb-4 flex justify-between">
                Live Telemetry <span className="text-[var(--success)] animate-pulse" aria-label="Live indicator">●</span>
              </h3>
              
              <div className="space-y-6">
                <div>
                  <div className="flex justify-between items-baseline mb-1">
                    <span className="text-[var(--text-secondary)] text-xs font-mono uppercase">Heart Rate</span>
                    <span className="text-3xl font-light text-[var(--success)] font-mono">{Math.round(vitals[vitals.length - 1]?.hr || 0)} <span className="text-xs">BPM</span></span>
                  </div>
                  <div className="h-8 w-full" aria-hidden="true">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={vitals}>
                        <Line type="monotone" dataKey="hr" stroke="#10b981" strokeWidth={2} dot={false} isAnimationActive={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between items-baseline mb-1">
                    <span className="text-[var(--text-secondary)] text-xs font-mono uppercase">Blood Pressure</span>
                    <span className="text-3xl font-light text-[var(--accent)] font-mono">{Math.round(vitals[vitals.length - 1]?.bp || 0)}/80 <span className="text-xs">mmHg</span></span>
                  </div>
                  <div className="h-8 w-full" aria-hidden="true">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={vitals}>
                        <Line type="monotone" dataKey="bp" stroke="#0066cc" strokeWidth={2} dot={false} isAnimationActive={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between items-baseline mb-1">
                    <span className="text-[var(--text-secondary)] text-xs font-mono uppercase">SpO2</span>
                    <span className="text-3xl font-light text-[var(--warning)] font-mono">{Math.round(vitals[vitals.length - 1]?.o2 || 0)}%</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="panel p-5" role="region" aria-label="Latest laboratory results">
              <h3 className="section-label mb-4">Latest Labs</h3>
              <div className="space-y-2 font-mono text-xs">
                <div className="flex justify-between py-1 border-b border-[var(--border-subtle)]">
                  <span className="text-[var(--text-secondary)]">WBC</span>
                  <span className="text-[var(--danger)] font-bold">14.2 ▲</span>
                </div>
                <div className="flex justify-between py-1 border-b border-[var(--border-subtle)]">
                  <span className="text-[var(--text-secondary)]">HGB</span>
                  <span className="text-[var(--text-primary)]">13.8</span>
                </div>
                <div className="flex justify-between py-1 border-b border-[var(--border-subtle)]">
                  <span className="text-[var(--text-secondary)]">PLT</span>
                  <span className="text-[var(--text-primary)]">210</span>
                </div>
                <div className="flex justify-between py-1 border-b border-[var(--border-subtle)]">
                  <span className="text-[var(--text-secondary)]">Lactate</span>
                  <span className="text-[var(--danger)] font-bold">3.1 ▲</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-[var(--text-secondary)]">Creatinine</span>
                  <span className="text-[var(--text-primary)]">1.1</span>
                </div>
              </div>
            </div>
          </div>

          {/* Middle Column: Active Problems & Notes */}
          <div className="xl:col-span-2 space-y-6">
            <div className="panel p-5" role="region" aria-label="Active problem list">
              <h3 className="section-label mb-4">Active Problem List</h3>
              <ul className="space-y-3">
                <li className="flex gap-4 p-3 bg-[var(--bg-card)] border border-[var(--danger-border)] rounded">
                  <div className="w-1.5 h-auto bg-[var(--danger)] rounded-full" aria-hidden="true" />
                  <div>
                    <h4 className="text-sm font-semibold text-[var(--text-primary)]">A41.9 Sepsis, unspecified organism</h4>
                    <p className="text-xs text-[var(--text-secondary)] mt-1">Onset: 24h ago. Lactate elevated. Blood cultures pending.</p>
                  </div>
                </li>
                <li className="flex gap-4 p-3 bg-[var(--bg-card)] border border-[var(--border)] rounded">
                  <div className="w-1.5 h-auto bg-[var(--accent)] rounded-full" aria-hidden="true" />
                  <div>
                    <h4 className="text-sm font-semibold text-[var(--text-primary)]">I10 Essential Hypertension</h4>
                    <p className="text-xs text-[var(--text-secondary)] mt-1">Chronic. Maintained on Lisinopril 10mg daily.</p>
                  </div>
                </li>
              </ul>
            </div>

            <div className="panel p-5 h-full min-h-[300px]" role="region" aria-label="Clinical AI synthesis">
              <h3 className="section-label mb-4">Clinical AI Synthesis</h3>
              <div className="prose prose-invert prose-sm max-w-none text-[var(--text-secondary)]">
                <p>
                  <strong>AI SUMMARY (Generated {new Date().toLocaleTimeString()}):</strong><br/>
                  Patient presents with signs consistent with systemic inflammatory response syndrome (SIRS). 
                  Elevated WBC (14.2) and Lactate (3.1) strongly suggest early sepsis protocol initiation. 
                  Continuous HR monitoring shows sinus tachycardia ranging 100-115 BPM.
                </p>
                <p>
                  <strong>RECOMMENDED ACTIONS:</strong><br/>
                  1. Administer 30cc/kg crystalloid fluid bolus.<br/>
                  2. Obtain peripheral blood cultures x2.<br/>
                  3. Initiate broad-spectrum IV antibiotics (e.g., Vancomycin + Cefepime) within 1 hour.
                </p>
              </div>
            </div>
          </div>

          {/* Right Column: DICOM / Imaging Mock */}
          <div className="xl:col-span-1 space-y-6">
            <div className="bg-[var(--bg-primary)] border border-[var(--border)] p-0 flex flex-col h-[400px]" role="region" aria-label="PACS DICOM viewer">
              <div className="px-4 py-3 border-b border-[var(--border)] flex justify-between items-center bg-[var(--bg-secondary)]">
                <h3 className="section-label">PACS / DICOM Viewer</h3>
                <span className="text-[11px] bg-[var(--bg-card)] border border-[var(--border)] px-2 py-0.5 rounded text-[var(--text-primary)]">CT CHEST W/ CONTRAST</span>
              </div>
              <div className="flex-1 relative flex items-center justify-center bg-[var(--bg-card)] overflow-hidden">
                {/* Mock Chest CT Image visualization */}
                <div className="w-48 h-48 rounded-full border-4 border-[var(--border)] border-dashed opacity-20 animate-[spin_10s_linear_infinite]" aria-hidden="true" />
                <div className="absolute inset-0 flex flex-col items-center justify-center text-[var(--text-dim)] font-mono text-xs">
                  <Activity size={24} className="mb-2 opacity-50" aria-hidden="true" />
                  RENDERING SLICE 42/128<br/>
                  <span className="text-[var(--success)] mt-1">AI DETECTED: NO ACUTE INFILTRATE</span>
                </div>
              </div>
              <div className="px-4 py-2 border-t border-[var(--border)] bg-[var(--bg-secondary)] flex justify-between mono-meta">
                <span>WL: 40 WW: 400</span>
                <span>ZOOM: 1.2X</span>
              </div>
            </div>

            <div className="panel p-5" role="region" aria-label="Active medications">
              <h3 className="section-label mb-4">Medications</h3>
              <div className="space-y-3 font-mono text-[11px]">
                <div className="p-2 border border-[var(--border)] rounded bg-[var(--bg-card)]">
                  <div className="text-[var(--text-primary)] font-bold">Lisinopril 10mg TAB</div>
                  <div className="text-[var(--text-secondary)] mt-1">Sig: 1 tab PO Daily</div>
                </div>
                <div className="p-2 border border-[var(--border)] rounded bg-[var(--bg-card)]">
                  <div className="text-[var(--text-primary)] font-bold">Vancomycin 1g IVPB</div>
                  <div className="text-[var(--danger)] mt-1">STAT - PENDING ADMIN</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function AlertPulse() {
  return (
    <div className="relative flex h-2 w-2" aria-hidden="true">
      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--danger)] opacity-75"></span>
      <span className="relative inline-flex rounded-full h-2 w-2 bg-[var(--danger)]"></span>
    </div>
  );
}
