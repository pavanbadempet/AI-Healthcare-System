
import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Server, Database, Activity, Network, ShieldCheck, HardDrive, Cpu, Terminal, ArrowRightLeft } from "lucide-react";

// Mock stable starting telemetry
const INITIAL_SERVERS = [
  { name: "DB-MASTER-01", ip: "192.168.10.100", cpu: 12, ram: 45 },
  { name: "MIRTH-NODE-A", ip: "192.168.10.101", cpu: 28, ram: 34 },
  { name: "MIRTH-NODE-B", ip: "192.168.10.102", cpu: 22, ram: 31 },
  { name: "AI-GPU-WORKER-1", ip: "192.168.10.103", cpu: 45, ram: 68 },
];

const MOCK_HL7_TEMPLATES = [
  "MSH|^~\\&|EPIC|HOSP|MIRTH|HOSP|202605061044||ADT^A01|MSG00001|P|2.5.1",
  "EVN|A01|202605061044",
  "PID|1||MRN123456^^^HOSP^MR||DOE^JOHN^A||19800101|M|||123 MAIN ST^^CITY",
  "PV1|1|I|ICU^BED04^1||||1234^SMITH^JOHN^^DR|||||||||||V12345",
  "MSH|^~\\&|LAB|HOSP|MIRTH|HOSP|202605061043||ORU^R01|MSG00002|P|2.5.1",
  "OBX|1|NM|WBC^White Blood Count||14.2|10*3/uL|4.5-11.0|H|||F",
  "MSH|^~\\&|PHARM|HOSP|EPIC|HOSP|202605061042||RDE^O11|MSG00003|P|2.5.1",
  "ORC|NW|1000^OE|2000^RX||||^^^202605061042|||||1234^SMITH^JOHN",
  "RXE|^^^202605061042^^R|64980-415-01^METFORMIN^RX||500|MG|||||||||||||",
];

export default function InfrastructurePage() {
  const [mounted, setMounted] = useState(false);
  const [servers, setServers] = useState(INITIAL_SERVERS);
  const [logs, setLogs] = useState<{ id: string; time: string; msg: string }[]>([]);

  useEffect(() => {
    setMounted(true);

    // Initial logs setup
    const initialLogs = Array.from({ length: 6 }).map((_, i) => ({
      id: Math.random().toString(),
      time: new Date(Date.now() - (6 - i) * 10000).toLocaleTimeString(),
      msg: MOCK_HL7_TEMPLATES[i % MOCK_HL7_TEMPLATES.length],
    }));
    setLogs(initialLogs);

    // Dynamic Server Telemetry Updates
    const telemetryInterval = setInterval(() => {
      setServers((current) =>
        current.map((srv) => {
          const cpuDelta = Math.floor(Math.random() * 11) - 5; // -5 to +5
          const ramDelta = Math.floor(Math.random() * 7) - 3; // -3 to +3
          return {
            ...srv,
            cpu: Math.max(5, Math.min(95, srv.cpu + cpuDelta)),
            ram: Math.max(10, Math.min(95, srv.ram + ramDelta)),
          };
        })
      );
    }, 3000);

    // Live HL7 Log Stream Updates
    const logInterval = setInterval(() => {
      const randomMsg = MOCK_HL7_TEMPLATES[Math.floor(Math.random() * MOCK_HL7_TEMPLATES.length)];
      const newLog = {
        id: Math.random().toString(),
        time: new Date().toLocaleTimeString(),
        msg: randomMsg,
      };
      setLogs((current) => [newLog, ...current.slice(0, 8)]);
    }, 2500);

    return () => {
      clearInterval(telemetryInterval);
      clearInterval(logInterval);
    };
  }, []);

  if (!mounted) return null;

  return (
    <div className="w-full min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] font-sans selection:bg-[var(--accent)] selection:text-white pb-20">
      
      {/* Top Status Bar */}
      <div className="w-full bg-[var(--bg-secondary)] border-b border-[var(--border)] px-4 py-1.5 flex justify-between items-center text-[10px] font-mono tracking-widest text-[var(--text-dim)] uppercase" role="status" aria-label="Infrastructure status">
        <div className="flex gap-4 items-center">
          <span className="flex items-center gap-1.5 text-[var(--success)] font-bold">
            <div className="w-1.5 h-1.5 bg-[var(--success)] rounded-full animate-pulse" aria-hidden="true" /> 
            CORE INTERFACE ENGINE: ACTIVE
          </span>
          <span className="hidden sm:inline">ON-PREM NODE: DFW-MED-01</span>
        </div>
        <div className="flex gap-4">
          <span>HSM STATE: SECURE</span>
          <span className="hidden sm:inline">UPTIME: 99.999%</span>
        </div>
      </div>

      <div className="p-6 md:p-8 max-w-[1800px] mx-auto space-y-6">
        <motion.div 
          initial={{ opacity: 0, y: -8 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ duration: 0.25 }} 
          className="flex flex-col md:flex-row md:items-end justify-between gap-4 pb-6 border-b border-[var(--border)]"
        >
          <div>
            <h1 className="text-xl font-bold text-[var(--text-primary)] uppercase tracking-wider flex items-center gap-3">
              Interoperability Engine <span className="text-[9px] font-bold bg-[var(--bg-card)] border border-[var(--border)] px-2 py-0.5 rounded text-[var(--accent)] uppercase tracking-wider align-middle">HL7/FHIR GATEWAY</span>
            </h1>
            <p className="text-xs text-[var(--text-secondary)] font-mono uppercase mt-1">Live interface message routing, database replication, and server telemetry.</p>
          </div>
          
          <div className="flex gap-3">
            <button className="btn btn-secondary text-xs uppercase tracking-wider font-mono cursor-pointer" aria-label="Open secure shell terminal">
              <Terminal size={12} aria-hidden="true" /> Open Secure Shell
            </button>
          </div>
        </motion.div>

        {/* Global Node Map / Status */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-3 panel p-6 relative overflow-hidden h-[320px] flex flex-col justify-between" role="img" aria-label="System architecture node diagram">
            
            <div className="absolute top-0 right-0 p-3 text-[9px] font-mono text-[var(--text-dim)] uppercase tracking-wider select-none">
              Topology Pipeline
            </div>

            <div className="text-left">
              <div className="section-label mb-1">DATA FLOW GRID</div>
              <h3 className="text-sm font-bold uppercase tracking-wider text-[var(--text-primary)]">Transactional Mesh</h3>
            </div>

            {/* Visual background lines */}
            <div className="absolute inset-0 opacity-[0.02] bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-[var(--accent)] via-[var(--bg-primary)] to-[var(--bg-primary)]" aria-hidden="true" />
            
            <div className="relative z-10 w-full flex flex-col sm:flex-row justify-between items-center px-6 md:px-12 gap-8 sm:gap-4 my-auto">
              
              {/* Node 1: EHR Database */}
              <div className="flex flex-col items-center">
                <div className="w-14 h-14 rounded-full bg-[rgba(24,24,27,0.8)] border border-[var(--border)] flex items-center justify-center mb-3 relative group hover:border-[var(--accent)] transition-all">
                  <Database size={20} className="text-[var(--text-secondary)] group-hover:text-[var(--accent)] transition-colors" aria-hidden="true" />
                  <div className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-[var(--success)] rounded-full border-2 border-[var(--bg-card)]" aria-hidden="true" />
                </div>
                <span className="text-[10px] font-bold text-[var(--text-primary)] uppercase tracking-widest">EHR DB</span>
                <span className="mono-meta mt-1">PostgreSQL 15</span>
              </div>

              {/* Connecting Line 1 */}
              <div className="hidden sm:flex flex-1 h-[2px] bg-gradient-to-r from-[var(--accent)] to-[var(--accent-purple)] mx-2 relative overflow-hidden items-center justify-center" aria-hidden="true">
                <div className="absolute inset-0 w-full h-full bg-[linear-gradient(90deg,transparent,rgba(99,102,241,0.8),transparent)] animate-gradient-x" />
                <span className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded px-1.5 py-0.5 text-[8px] font-mono text-[var(--text-secondary)] uppercase z-10">HL7 v2.5.1</span>
              </div>

              {/* Node 2: Interface Engine */}
              <div className="flex flex-col items-center">
                <div className="w-18 h-18 rounded-lg bg-[var(--accent-muted)] border border-[var(--accent-border)] flex items-center justify-center mb-3 relative shadow-[0_0_20px_rgba(99,102,241,0.1)] hover:border-[var(--accent)] transition-colors">
                  <Network size={26} className="text-[var(--accent)]" aria-hidden="true" />
                </div>
                <span className="text-[10px] font-bold text-[var(--text-primary)] uppercase tracking-widest">Mirth Engine</span>
                <span className="mono-meta mt-1">14.2k MSG/SEC</span>
              </div>

              {/* Connecting Line 2 */}
              <div className="hidden sm:flex flex-1 h-[2px] bg-gradient-to-r from-[var(--accent-purple)] to-[var(--accent-blue)] mx-2 relative overflow-hidden items-center justify-center" aria-hidden="true">
                <div className="absolute inset-0 w-full h-full bg-[linear-gradient(90deg,transparent,rgba(139,92,246,0.8),transparent)] animate-gradient-x" />
                <span className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded px-1.5 py-0.5 text-[8px] font-mono text-[var(--text-secondary)] uppercase z-10">FHIR JSON</span>
              </div>

              {/* Node 3: AI Inference Cluster */}
              <div className="flex flex-col items-center">
                <div className="w-14 h-14 rounded-full bg-[rgba(24,24,27,0.8)] border border-[var(--border)] flex items-center justify-center mb-3 relative group hover:border-[var(--accent-purple)] transition-all">
                  <Cpu size={20} className="text-[var(--text-secondary)] group-hover:text-[var(--accent-purple)] transition-colors" aria-hidden="true" />
                  <div className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-[var(--success)] rounded-full border-2 border-[var(--bg-card)]" aria-hidden="true" />
                </div>
                <span className="text-[10px] font-bold text-[var(--text-primary)] uppercase tracking-widest">AI CLUSTER</span>
                <span className="mono-meta mt-1">GPU MASTER 04</span>
              </div>
            </div>

            <div className="h-2" />
          </div>

          <div className="panel flex flex-col">
            <div className="panel-header bg-[rgba(15,15,17,0.5)]">
              <h3 className="section-title flex items-center gap-2">
                <ShieldCheck size={13} className="text-[var(--success)]" aria-hidden="true" /> Security & Sync
              </h3>
            </div>
            <div className="p-5 flex-1 flex flex-col justify-center gap-6" role="region" aria-label="Security audit metrics">
              <div>
                <div className="flex justify-between items-baseline mb-2">
                  <span className="mono-meta">Active Directory Sync</span>
                  <span className="text-[10px] font-mono font-bold text-[var(--success)]">CONNECTED</span>
                </div>
                <div className="h-1 w-full bg-[var(--border)] rounded-full overflow-hidden">
                  <div className="h-full bg-[var(--success)] w-full rounded-full" />
                </div>
              </div>
              <div>
                <div className="flex justify-between items-baseline mb-2">
                  <span className="mono-meta">Firewall Drops/min</span>
                  <span className="text-[10px] font-mono font-bold text-[var(--accent)]">142 PKTS</span>
                </div>
                <div className="h-1 w-full bg-[var(--border)] rounded-full overflow-hidden">
                  <div className="h-full bg-[var(--accent)] w-[15%] rounded-full" />
                </div>
              </div>
              <div>
                <div className="flex justify-between items-baseline mb-2">
                  <span className="mono-meta">Replica Sync Lag</span>
                  <span className="text-[10px] font-mono font-bold text-[var(--warning)]">42ms</span>
                </div>
                <div className="h-1 w-full bg-[var(--border)] rounded-full overflow-hidden">
                  <div className="h-full bg-[var(--warning)] w-[40%] rounded-full" />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Server & Message Stats */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Server List */}
          <div className="panel">
            <div className="panel-header bg-[rgba(15,15,17,0.5)]">
              <h3 className="section-title flex items-center gap-2">
                <Server size={13} className="text-[var(--accent)]" aria-hidden="true" /> Local Node Cluster
              </h3>
            </div>
            <div className="p-0 divide-y divide-[var(--border)]" role="list" aria-label="Server hardware status">
              {servers.map((srv) => (
                <div key={srv.name} className="p-4 flex items-center justify-between" role="listitem">
                  <div className="flex items-center gap-4">
                    <HardDrive size={20} className="text-[var(--text-dim)]" aria-hidden="true" />
                    <div>
                      <div className="text-[11px] font-bold text-[var(--text-primary)] uppercase tracking-wider">{srv.name}</div>
                      <div className="mono-meta mt-1 font-mono">{srv.ip}</div>
                    </div>
                  </div>
                  <div className="flex gap-6 mono-meta font-mono">
                    <div className="flex flex-col items-end">
                      <span className="text-[9px] text-[var(--text-dim)]">CPU</span>
                      <span className={`font-bold text-[11px] ${srv.cpu > 80 ? 'text-[var(--danger)]' : 'text-[var(--text-primary)]'}`}>{srv.cpu}%</span>
                    </div>
                    <div className="flex flex-col items-end">
                      <span className="text-[9px] text-[var(--text-dim)]">RAM</span>
                      <span className={`font-bold text-[11px] ${srv.ram > 80 ? 'text-[var(--danger)]' : 'text-[var(--text-primary)]'}`}>{srv.ram}%</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* HL7 Transaction Ticker */}
          <div className="panel">
            <div className="panel-header bg-[rgba(15,15,17,0.5)] flex justify-between items-center">
              <h3 className="section-title flex items-center gap-2">
                <ArrowRightLeft size={13} className="text-[var(--accent-purple)]" aria-hidden="true" /> HL7 Message Stream
              </h3>
              <span className="status-badge status-badge-accent font-mono text-[9px]">LIVE STACK</span>
            </div>
            
            <div className="p-4 h-[240px] overflow-hidden relative" role="log" aria-label="Live HL7 message stream">
              <div className="absolute inset-0 bg-gradient-to-b from-[var(--bg-card)] via-transparent to-transparent pointer-events-none z-10 h-10" aria-hidden="true" />
              
              <div className="space-y-2 flex flex-col justify-start h-full overflow-y-hidden">
                <AnimatePresence initial={false}>
                  {logs.map((log) => (
                    <motion.div 
                      key={log.id}
                      initial={{ opacity: 0, y: -10, height: 0 }}
                      animate={{ opacity: 1, y: 0, height: "auto" }}
                      exit={{ opacity: 0, y: 10, height: 0 }}
                      transition={{ type: "spring", stiffness: 200, damping: 20 }}
                      className="text-[10px] font-mono text-[var(--text-secondary)] border-b border-[var(--border)] pb-2 flex items-start gap-3 w-full"
                    >
                      <span className="text-[var(--accent)] shrink-0 font-bold">[{log.time}]</span>
                      <span className="break-all font-mono uppercase tracking-wide flex-1">{log.msg}</span>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
