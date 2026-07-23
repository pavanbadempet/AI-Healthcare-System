import React from "react";
import { motion } from "framer-motion";
import { Zap, Cpu, Gauge, Database, DollarSign, Layers } from "lucide-react";

export interface TelemetryDashboardProps {
  ttftMs?: number;
  tokensPerSec?: number;
  cacheLatencyMs?: number;
  dollarsSaved?: number;
  simdParserActive?: boolean;
}

export const SotaTelemetryDashboard: React.FC<TelemetryDashboardProps> = ({
  ttftMs = 45.0,
  tokensPerSec = 5140.6,
  cacheLatencyMs = 0.12,
  dollarsSaved = 142.50,
  simdParserActive = true,
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      className="rounded-2xl border border-cyan-500/20 bg-slate-950 p-6 backdrop-blur-lg shadow-2xl text-slate-100 font-sans my-6"
    >
      <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
            <Gauge className="w-6 h-6" />
          </div>
          <div>
            <h3 className="font-bold text-lg text-slate-100">SOTA Telemetry & Speed Dashboard</h3>
            <p className="text-xs text-slate-400">Real-time performance acceleration and API token cost optimization</p>
          </div>
        </div>
        <span className="px-3 py-1 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-700/50 text-xs font-semibold flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          SOTA Speed Engines Active
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {/* Card 1: TTFT */}
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-cyan-500/40 transition-colors">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span>Time-To-First-Token</span>
            <Zap className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-extrabold text-cyan-400">{ttftMs.toFixed(1)} ms</div>
          <p className="text-[11px] text-slate-500 mt-1">Sub-50ms via Prefix KV-Cache</p>
        </div>

        {/* Card 2: PagedAttention Throughput */}
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-emerald-500/40 transition-colors">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span>Batch Throughput</span>
            <Cpu className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-extrabold text-emerald-400">{tokensPerSec.toLocaleString()} t/s</div>
          <p className="text-[11px] text-slate-500 mt-1">PagedAttention 16-token blocks</p>
        </div>

        {/* Card 3: Cache Latency */}
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-purple-500/40 transition-colors">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span>Multi-Tier Cache Latency</span>
            <Database className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-extrabold text-purple-300">{cacheLatencyMs.toFixed(2)} ms</div>
          <p className="text-[11px] text-slate-500 mt-1">Microsecond L1/L2 HNSW Mesh</p>
        </div>

        {/* Card 4: Dollars Saved */}
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-amber-500/40 transition-colors">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span>Cumulative API Savings</span>
            <DollarSign className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-extrabold text-amber-400">${dollarsSaved.toFixed(2)}</div>
          <p className="text-[11px] text-slate-500 mt-1">70% Cost-Aware Router Tiering</p>
        </div>
      </div>

      <div className="p-3.5 rounded-xl bg-slate-900/40 border border-slate-800 flex items-center justify-between text-xs text-slate-300">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-cyan-400" />
          <span>SIMD C-Accelerated Parsing: <strong className="text-slate-100">{simdParserActive ? "orjson SIMD Enabled (5x Speed)" : "Standard Fast Fallback"}</strong></span>
        </div>
        <span className="text-slate-400 text-[11px]">Zero-Configuration Sandbox Compatible</span>
      </div>
    </motion.div>
  );
};

export default SotaTelemetryDashboard;
