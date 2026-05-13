"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Server, Database, Activity, Network, ShieldCheck, HardDrive, Cpu, Terminal, ArrowRightLeft } from "lucide-react";

export default function InfrastructurePage() {
  const [mounted, setMounted] = useState(false);
  
  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return (
    <div className="w-full min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] font-sans selection:bg-[var(--accent)] selection:text-white pb-20">
      {/* Top Status Bar */}
      <div className="w-full bg-[var(--bg-secondary)] border-b border-[var(--border)] px-4 py-1.5 flex justify-between items-center text-[11px] font-mono tracking-widest text-[var(--text-dim)] uppercase" role="status" aria-label="Infrastructure status">
        <div className="flex gap-4">
          <span className="flex items-center gap-1.5 text-[var(--success)]">
            <div className="w-1.5 h-1.5 bg-[var(--success)] rounded-full animate-pulse" aria-hidden="true" /> 
            CORE INTERFACE ENGINE: ONLINE
          </span>
          <span>ON-PREM NODE: DFW-MED-01</span>
        </div>
        <div className="flex gap-4">
          <span>HSM: SECURE</span>
          <span>UPTIME: 99.999%</span>
        </div>
      </div>

      <div className="p-6 md:p-8 max-w-[1800px] mx-auto space-y-6">
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }} className="flex flex-col md:flex-row md:items-end justify-between gap-4 pb-6 border-b border-[var(--border)]">
          <div>
            <h1 className="text-3xl font-semibold text-[var(--text-primary)] mb-1 tracking-tight flex items-center gap-3">
              Interoperability & Infrastructure <span className="text-[11px] bg-[var(--bg-card)] border border-[var(--border)] px-2 py-1 rounded text-[var(--text-secondary)] uppercase tracking-widest align-middle">HL7/FHIR GATEWAY</span>
            </h1>
            <p className="text-[var(--text-secondary)] text-sm font-mono mt-1">Live interface message routing, database replication, and server telemetry.</p>
          </div>
          
          <div className="flex gap-3">
            <button className="btn btn-secondary text-xs font-bold uppercase tracking-wider flex items-center gap-2" aria-label="Open secure shell terminal">
              <Terminal size={14} aria-hidden="true" /> Open Secure Shell
            </button>
          </div>
        </motion.div>

        {/* Global Node Map / Status */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="md:col-span-3 panel p-6 relative overflow-hidden h-[300px] flex items-center justify-center" role="img" aria-label="System architecture node diagram">
            {/* Visual background lines */}
            <div className="absolute inset-0 opacity-10 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-[var(--accent)] via-[var(--bg-primary)] to-[var(--bg-primary)]" aria-hidden="true" />
            
            <div className="relative z-10 w-full flex justify-between items-center px-12">
              {/* Node 1: EHR Database */}
              <div className="flex flex-col items-center">
                <div className="w-16 h-16 rounded-full bg-[var(--bg-card)] border border-[var(--accent)] flex items-center justify-center mb-4 relative">
                  <Database size={24} className="text-[var(--accent)]" aria-hidden="true" />
                  <div className="absolute -top-1 -right-1 w-3 h-3 bg-[var(--success)] rounded-full border-2 border-[var(--bg-card)]" aria-hidden="true" />
                </div>
                <span className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-widest">EHR Main DB</span>
                <span className="mono-meta mt-1">PostgreSQL 15</span>
              </div>

              {/* Connecting Line */}
              <div className="flex-1 h-px bg-gradient-to-r from-[var(--accent)] to-[var(--success)] mx-4 relative overflow-hidden flex items-center justify-center" aria-hidden="true">
                <span className="bg-[var(--bg-secondary)] px-2 mono-meta">HL7 v2.5.1 / ADT</span>
              </div>

              {/* Node 2: Interface Engine */}
              <div className="flex flex-col items-center">
                <div className="w-24 h-24 rounded-xl bg-[var(--accent-muted)] border-2 border-[var(--accent-border)] flex items-center justify-center mb-4 relative shadow-[0_0_30px_rgba(0,102,204,0.2)]">
                  <Network size={32} className="text-[var(--accent)]" aria-hidden="true" />
                </div>
                <span className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-widest">Mirth Interface Engine</span>
                <span className="mono-meta mt-1">Routing 14.2k msg/s</span>
              </div>

              {/* Connecting Line */}
              <div className="flex-1 h-px bg-gradient-to-r from-[var(--success)] to-[var(--warning)] mx-4 relative overflow-hidden flex items-center justify-center" aria-hidden="true">
                <span className="bg-[var(--bg-secondary)] px-2 mono-meta">FHIR R4 / JSON</span>
              </div>

              {/* Node 3: AI Inference Cluster */}
              <div className="flex flex-col items-center">
                <div className="w-16 h-16 rounded-full bg-[var(--bg-card)] border border-[var(--warning)] flex items-center justify-center mb-4 relative">
                  <Cpu size={24} className="text-[var(--warning)]" aria-hidden="true" />
                  <div className="absolute -top-1 -right-1 w-3 h-3 bg-[var(--success)] rounded-full border-2 border-[var(--bg-card)]" aria-hidden="true" />
                </div>
                <span className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-widest">AI Inference</span>
                <span className="mono-meta mt-1">GPU Cluster 04</span>
              </div>
            </div>
          </div>

          <div className="panel flex flex-col">
            <div className="panel-header bg-[var(--bg-card)]">
              <h3 className="section-title flex items-center gap-2">
                <ShieldCheck size={14} className="text-[var(--success)]" aria-hidden="true" /> Security Audits
              </h3>
            </div>
            <div className="p-5 flex-1 flex flex-col justify-center gap-6" role="region" aria-label="Security audit metrics">
              <div>
                <div className="flex justify-between items-baseline mb-2">
                  <span className="mono-meta">Active Directory Sync</span>
                  <span className="text-xs font-bold text-[var(--success)]">OK</span>
                </div>
                <div className="h-1 w-full bg-[var(--border)] rounded-full overflow-hidden"><div className="h-full bg-[var(--success)] w-full" /></div>
              </div>
              <div>
                <div className="flex justify-between items-baseline mb-2">
                  <span className="mono-meta">Firewall Drops/min</span>
                  <span className="text-xs font-bold text-[var(--accent)]">142</span>
                </div>
                <div className="h-1 w-full bg-[var(--border)] rounded-full overflow-hidden"><div className="h-full bg-[var(--accent)] w-[15%]" /></div>
              </div>
              <div>
                <div className="flex justify-between items-baseline mb-2">
                  <span className="mono-meta">Database Backup Lag</span>
                  <span className="text-xs font-bold text-[var(--warning)]">42ms</span>
                </div>
                <div className="h-1 w-full bg-[var(--border)] rounded-full overflow-hidden"><div className="h-full bg-[var(--warning)] w-[40%]" /></div>
              </div>
            </div>
          </div>
        </div>

        {/* Server & Message Stats */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="panel">
            <div className="panel-header bg-[var(--bg-card)] flex justify-between items-center">
              <h3 className="section-title flex items-center gap-2">
                <Server size={14} aria-hidden="true" /> Local Server Hardware
              </h3>
            </div>
            <div className="p-0 divide-y divide-[var(--border)]" role="list" aria-label="Server hardware status">
              {['DB-MASTER-01', 'MIRTH-NODE-A', 'MIRTH-NODE-B', 'AI-GPU-WORKER-1'].map((server, i) => {
                const cpu = Math.floor(Math.random() * 40) + 10;
                const ram = Math.floor(Math.random() * 60) + 20;
                return (
                  <div key={server} className="p-4 flex items-center justify-between" role="listitem">
                    <div className="flex items-center gap-4">
                      <HardDrive size={24} className="text-[var(--border-focus)]" aria-hidden="true" />
                      <div>
                        <div className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-widest">{server}</div>
                        <div className="mono-meta mt-0.5">192.168.10.{100 + i}</div>
                      </div>
                    </div>
                    <div className="flex gap-6 mono-meta">
                      <div className="flex flex-col items-end">
                        <span>CPU</span>
                        <span className={`font-bold ${cpu > 80 ? 'text-[var(--danger)]' : 'text-[var(--text-primary)]'}`}>{cpu}%</span>
                      </div>
                      <div className="flex flex-col items-end">
                        <span>RAM</span>
                        <span className={`font-bold ${ram > 80 ? 'text-[var(--danger)]' : 'text-[var(--text-primary)]'}`}>{ram}%</span>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          <div className="panel">
            <div className="panel-header bg-[var(--bg-card)] flex justify-between items-center">
              <h3 className="section-title flex items-center gap-2">
                <ArrowRightLeft size={14} aria-hidden="true" /> Live Interface Messages (HL7)
              </h3>
              <span className="status-badge status-badge-accent">POLLING: 1s</span>
            </div>
            <div className="p-4 font-mono text-[11px] space-y-2 h-[260px] overflow-hidden flex flex-col-reverse relative" role="log" aria-label="Live HL7 message stream">
              {/* Fake HL7 messages scrolling up */}
              <div className="absolute inset-0 bg-gradient-to-t from-transparent to-[var(--bg-secondary)] pointer-events-none z-10 h-12" aria-hidden="true" />
              {[
                "MSH|^~\\&|EPIC|HOSP|MIRTH|HOSP|202605061044||ADT^A01|MSG00001|P|2.5.1",
                "EVN|A01|202605061044",
                "PID|1||MRN123456^^^HOSP^MR||DOE^JOHN^A||19800101|M|||123 MAIN ST^^CITY^ST^12345",
                "PV1|1|I|ICU^BED04^1||||1234^SMITH^JOHN^^DR|||||||||||V12345",
                "MSH|^~\\&|LAB|HOSP|MIRTH|HOSP|202605061043||ORU^R01|MSG00002|P|2.5.1",
                "OBX|1|NM|WBC^White Blood Count||14.2|10*3/uL|4.5-11.0|H|||F",
                "MSH|^~\\&|PHARM|HOSP|EPIC|HOSP|202605061042||RDE^O11|MSG00003|P|2.5.1"
              ].map((msg, i) => (
                <div key={i} className="text-[var(--text-secondary)] border-b border-[var(--bg-card)] pb-1 break-all">
                  <span className="text-[var(--accent)] mr-2">[{new Date().toLocaleTimeString()}]</span>
                  {msg}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
