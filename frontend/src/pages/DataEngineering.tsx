import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { 
  Database, Server, Activity, ArrowRight, Layers, Workflow, 
  Cpu, FileJson, CheckCircle2, RefreshCw, Box, AlertTriangle, ShieldCheck
} from "lucide-react";
import { useTelemetry } from "@/lib/useTelemetry";

const PipelineNode = ({ 
  icon: Icon, title, subtitle, status, delay = 0, isActive = false 
}: { 
  icon: React.ElementType, title: string, subtitle: string, status: "idle" | "processing" | "done" | "error", delay?: number, isActive?: boolean
}) => {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className={`relative p-5 rounded-2xl border backdrop-blur-md transition-all duration-500
        ${isActive ? 'border-[var(--accent)] bg-[var(--accent-muted)] shadow-[0_0_20px_rgba(95,95,247,0.15)]' : 'border-white/[0.05] bg-black/40'}
      `}
    >
      {isActive && (
        <span className="absolute -top-1 -right-1 flex h-3 w-3">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--accent)] opacity-75"></span>
          <span className="relative inline-flex rounded-full h-3 w-3 bg-[var(--accent)]"></span>
        </span>
      )}
      <div className="flex items-center gap-4">
        <div className={`p-3 rounded-xl ${isActive ? 'bg-[var(--accent)] text-white' : 'bg-white/5 text-[var(--text-secondary)]'}`}>
          <Icon size={24} className={isActive && status === 'processing' ? 'animate-pulse' : ''} />
        </div>
        <div>
          <h3 className={`font-bold text-sm ${isActive ? 'text-white' : 'text-[var(--text-primary)]'}`}>{title}</h3>
          <p className="text-xs text-[var(--text-dim)] font-mono mt-1">{subtitle}</p>
        </div>
      </div>
      
      <div className="mt-4 pt-4 border-t border-white/[0.05] flex justify-between items-center text-[10px] font-mono uppercase tracking-wider">
        <span className="text-[var(--text-dim)]">Status</span>
        {status === 'processing' ? (
          <span className="text-[var(--accent-blue)] flex items-center gap-1"><RefreshCw size={10} className="animate-spin" /> Ingesting</span>
        ) : status === 'done' ? (
          <span className="text-[var(--success)] flex items-center gap-1"><CheckCircle2 size={10} /> Stable</span>
        ) : status === 'error' ? (
           <span className="text-[var(--danger)] flex items-center gap-1"><AlertTriangle size={10} /> Alert</span>
        ) : (
          <span className="text-[var(--text-secondary)]">Awaiting</span>
        )}
      </div>
    </motion.div>
  );
};

export default function DataEngineering() {
  const { data: telemetry } = useTelemetry();
  const isProcessing = telemetry?.spark_batch_id !== undefined;
  
  // Fake historical throughput data for the chart visualization
  const [throughput, setThroughput] = useState<number[]>([12, 15, 24, 18, 22, 10, 19, 25, 28, 21]);

  useEffect(() => {
    if (isProcessing) {
      const interval = setInterval(() => {
        setThroughput(prev => {
          const newArray = [...prev.slice(1), Math.floor(Math.random() * 30) + 10];
          return newArray;
        });
      }, 3000);
      return () => clearInterval(interval);
    }
  }, [isProcessing]);

  return (
    <div className="min-h-screen bg-[var(--bg-main)] text-[var(--text-primary)] pb-20 pt-24 px-6">
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Header Section */}
        <header className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6 mb-10">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-lg bg-[var(--accent)]/10 border border-[var(--accent)]/20 flex items-center justify-center">
                <Workflow className="text-[var(--accent)]" size={20} />
              </div>
              <h1 className="text-2xl font-black font-display text-[var(--text-primary)]">Data Engineering Hub</h1>
            </div>
            <p className="text-[var(--text-secondary)] text-sm max-w-xl">
              Real-time monitoring of the PySpark Structured Streaming pipeline and Medallion Lakehouse architecture.
            </p>
          </div>
          
          <div className="flex gap-4">
            <div className="glass-card px-5 py-3 rounded-xl flex items-center gap-4">
              <div>
                <p className="text-[10px] text-[var(--text-dim)] uppercase tracking-wider font-mono">Engine Status</p>
                {telemetry?.is_real_stream ? (
                  <p className="text-sm font-bold text-[var(--success)] flex items-center gap-2 mt-0.5">
                    <span className="w-2 h-2 rounded-full bg-[var(--success)] animate-pulse" /> Real PySpark Active
                  </p>
                ) : (
                  <p className="text-sm font-bold text-[var(--warning)] flex items-center gap-2 mt-0.5">
                    <span className="w-2 h-2 rounded-full bg-[var(--warning)] animate-pulse" /> Spark Simulator
                  </p>
                )}
              </div>
            </div>
          </div>
        </header>

        {/* Live Metrics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="glass-card p-5 rounded-2xl">
            <p className="text-[10px] text-[var(--text-dim)] uppercase tracking-wider font-mono mb-2 flex items-center gap-2">
              <RefreshCw size={12} className={isProcessing ? "animate-spin" : ""} /> Batch ID
            </p>
            <p className="text-3xl font-black font-mono text-white">
              {telemetry?.spark_batch_id || "—"}
            </p>
          </div>
          <div className="glass-card p-5 rounded-2xl border-b-2 border-[var(--accent-blue)]">
            <p className="text-[10px] text-[var(--text-dim)] uppercase tracking-wider font-mono mb-2 flex items-center gap-2">
              <Activity size={12} /> Records Ingested
            </p>
            <p className="text-3xl font-black font-mono text-[var(--accent-blue)]">
              {telemetry?.spark_records_processed || 0} <span className="text-sm text-[var(--text-dim)] font-sans">/ batch</span>
            </p>
          </div>
          <div className="glass-card p-5 rounded-2xl border-b-2 border-[var(--accent-purple)]">
            <p className="text-[10px] text-[var(--text-dim)] uppercase tracking-wider font-mono mb-2 flex items-center gap-2">
              <Cpu size={12} /> ML Inference Latency
            </p>
            <p className="text-3xl font-black font-mono text-[var(--accent-purple)]">
              {telemetry?.spark_ml_latency_ms?.toFixed(1) || "—"} <span className="text-sm text-[var(--text-dim)] font-sans">ms</span>
            </p>
          </div>
          <div className="glass-card p-5 rounded-2xl">
            <p className="text-[10px] text-[var(--text-dim)] uppercase tracking-wider font-mono mb-2 flex items-center gap-2">
              <Server size={12} /> AI Node Cluster
            </p>
            <p className="text-3xl font-black font-mono text-white">
              {telemetry?.ai_nodes_active || 1} <span className="text-sm text-[var(--text-dim)] font-sans">nodes</span>
            </p>
          </div>
        </div>

        {/* DAG Visualization (Airflow-style) */}
        <div className="glass-card rounded-2xl border border-white/[0.05] p-6 lg:p-10 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-96 h-96 bg-[var(--accent)]/10 blur-[100px] rounded-full pointer-events-none" />
          
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-lg font-bold text-[var(--text-primary)]">Live Pipeline DAG</h2>
              <p className="text-xs text-[var(--text-dim)] font-mono mt-1">Airflow & PySpark Orchestration View</p>
            </div>
            {isProcessing && (
              <span className="px-3 py-1 bg-[var(--success-muted)] text-[var(--success)] text-[10px] font-bold font-mono uppercase rounded-full border border-[var(--success-border)] flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-[var(--success)] animate-pulse" /> DAG Running
              </span>
            )}
          </div>

          <div className="relative">
            {/* Connection Lines connecting nodes (Desktop only) */}
            <div className="hidden lg:block absolute top-1/2 left-0 w-full h-[2px] bg-gradient-to-r from-white/5 via-white/10 to-white/5 -translate-y-1/2 z-0" />
            
            {/* Animated Pulses on the line */}
            {isProcessing && (
              <>
                <motion.div 
                  initial={{ left: "0%" }} 
                  animate={{ left: "100%" }} 
                  transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                  className="hidden lg:block absolute top-1/2 w-16 h-[2px] bg-gradient-to-r from-transparent via-[var(--accent)] to-transparent -translate-y-1/2 z-0 blur-[1px]" 
                />
                <motion.div 
                  initial={{ left: "0%" }} 
                  animate={{ left: "100%" }} 
                  transition={{ duration: 2, repeat: Infinity, ease: "linear", delay: 1 }}
                  className="hidden lg:block absolute top-1/2 w-16 h-[2px] bg-gradient-to-r from-transparent via-[var(--success)] to-transparent -translate-y-1/2 z-0 blur-[1px]" 
                />
              </>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 relative z-10">
              <PipelineNode 
                delay={0.1}
                icon={FileJson}
                title="Hospital Sensors"
                subtitle="JSON Stream Generation"
                status={isProcessing ? "processing" : "idle"}
                isActive={isProcessing}
              />
              <PipelineNode 
                delay={0.2}
                icon={Box}
                title="Local / Kafka Stream"
                subtitle="Event Bus Topic"
                status={isProcessing ? "processing" : "idle"}
                isActive={isProcessing}
              />
              <PipelineNode 
                delay={0.3}
                icon={Activity}
                title="PySpark Structured Streaming"
                subtitle="In-Memory Micro-Batches"
                status={isProcessing ? "processing" : "idle"}
                isActive={isProcessing}
              />
              <div className="space-y-4">
                <PipelineNode 
                  delay={0.4}
                  icon={Database}
                  title="Bronze Layer"
                  subtitle="Raw Telemetry"
                  status={isProcessing ? "done" : "idle"}
                  isActive={false}
                />
                <PipelineNode 
                  delay={0.5}
                  icon={Layers}
                  title="Silver / Gold Layer"
                  subtitle="Cleaned & ML Ready"
                  status={isProcessing ? "done" : "idle"}
                  isActive={false}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Throughput Graph */}
        <div className="glass-card rounded-2xl p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-sm font-bold text-[var(--text-primary)]">Stream Throughput (Events/sec)</h2>
            <div className="flex items-center gap-2 text-[10px] text-[var(--text-dim)] font-mono">
              <span className="w-2 h-2 rounded bg-[var(--accent)]" /> Records Processed
            </div>
          </div>
          <div className="h-40 flex items-end gap-2">
            {throughput.map((val, i) => (
              <motion.div 
                key={i}
                initial={{ height: 0 }}
                animate={{ height: `${(val / 40) * 100}%` }}
                className="flex-1 bg-[var(--accent)]/20 hover:bg-[var(--accent)]/40 rounded-t-sm transition-colors border-t border-[var(--accent)]/50 relative group"
              >
                <div className="opacity-0 group-hover:opacity-100 absolute -top-8 left-1/2 -translate-x-1/2 bg-black text-white text-[10px] px-2 py-1 rounded shadow pointer-events-none transition-opacity">
                  {val} recs
                </div>
              </motion.div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
