
import { motion } from "framer-motion";
import { Sparkles, Brain, Cpu, Server, Lock, ArrowRight, Laptop, Network, Globe, Activity } from "lucide-react";

export default function AboutPage() {
  return (
    <div className="w-full max-w-5xl mx-auto space-y-16 pb-16 selection:bg-[var(--accent)] selection:text-white">
      
      {/* Hero Section with Ambient Glows */}
      <div className="text-center space-y-6 pt-6 relative overflow-hidden">
        {/* Animated Radial Orb */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[300px] h-[300px] bg-gradient-to-tr from-[var(--accent)] to-[var(--accent-purple)] rounded-full blur-[120px] opacity-15 pointer-events-none" />

        <motion.div 
          initial={{ opacity: 0, scale: 0.8 }} 
          animate={{ opacity: 1, scale: 1 }} 
          transition={{ type: "spring", stiffness: 100 }}
          className="relative w-20 h-20 mx-auto flex items-center justify-center mb-4 rounded-2xl bg-gradient-to-br from-[var(--accent)] to-[var(--accent-purple)] p-[1px] shadow-[0_0_30px_rgba(99,102,241,0.2)]"
        >
          <div className="w-full h-full bg-[#121214] rounded-2xl flex items-center justify-center">
            <Sparkles size={36} className="text-[var(--accent)] animate-pulse" />
          </div>
        </motion.div>

        <div className="space-y-3">
          <motion.h1 
            initial={{ opacity: 0, y: 12 }} 
            animate={{ opacity: 1, y: 0 }} 
            transition={{ duration: 0.4 }}
            className="text-4xl md:text-5xl font-black text-[var(--text-primary)] tracking-tight uppercase"
          >
            System Architecture
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0, y: 12 }} 
            animate={{ opacity: 1, y: 0 }} 
            transition={{ duration: 0.4, delay: 0.1 }} 
            className="text-xs md:text-sm max-w-2xl mx-auto text-[var(--text-secondary)] font-mono uppercase tracking-wide leading-relaxed"
          >
            Secure, high-performance platform integrating tri-tier AI inference with robust medical data pipelines.
          </motion.p>
        </div>
      </div>

      {/* Interactive Architecture Flow Diagram */}
      <motion.div 
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        className="panel p-6 md:p-8 bg-[rgba(24,24,27,0.35)] border border-[var(--border)] rounded-lg relative overflow-hidden"
      >
        <div className="absolute top-0 right-0 p-3 text-[9px] font-mono text-[var(--text-dim)] uppercase tracking-wider select-none">
          Active Fallback Topology
        </div>
        
        <div className="mb-6">
          <h3 className="text-sm font-bold uppercase tracking-wider text-[var(--text-primary)] flex items-center gap-2">
            <Activity size={14} className="text-[var(--accent)]" />
            Tri-Tier AI Execution Pipeline
          </h3>
          <p className="text-xs text-[var(--text-secondary)] mt-1 max-w-xl">
            Demonstrates how inference automatically cascades down execution contexts to guarantee zero downtime and maximum privacy.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 items-center relative py-4">
          {/* Tier 1: WebGPU */}
          <div className="col-span-1 p-4 rounded border border-[var(--accent-border)] bg-[var(--accent-muted)] flex flex-col items-center text-center relative group hover:border-[var(--accent)] transition-all">
            <div className="absolute -top-2.5 px-2 py-0.5 rounded bg-[var(--accent)] text-[8px] font-bold text-white uppercase tracking-wider">
              Priority 01
            </div>
            <Laptop size={24} className="text-[var(--accent)] mb-2" />
            <h4 className="text-xs font-bold uppercase text-[var(--text-primary)]">Local WebGPU</h4>
            <p className="text-[10px] text-[var(--text-secondary)] mt-1 font-mono uppercase">On-Device WASM</p>
            <span className="text-[8px] text-[var(--accent-emerald)] font-bold mt-2 bg-emerald-500/10 px-1 rounded uppercase">
              Zero Cost / Offline
            </span>
          </div>

          {/* Connection 1 */}
          <div className="hidden lg:flex col-span-1 justify-center items-center">
            <div className="flex flex-col items-center text-center">
              <span className="text-[9px] font-mono text-[var(--text-dim)] uppercase mb-1">Fallback</span>
              <div className="flex items-center gap-1">
                <div className="w-6 h-[1px] bg-[var(--border)]" />
                <ArrowRight size={12} className="text-[var(--text-dim)] animate-pulse" />
                <div className="w-6 h-[1px] bg-[var(--border)]" />
              </div>
            </div>
          </div>

          {/* Tier 2: Ollama */}
          <div className="col-span-1 p-4 rounded border border-[var(--accent-purple-border)] bg-[var(--accent-purple-muted)] flex flex-col items-center text-center relative hover:border-[var(--accent-purple)] transition-all">
            <div className="absolute -top-2.5 px-2 py-0.5 rounded bg-[var(--accent-purple)] text-[8px] font-bold text-white uppercase tracking-wider">
              Priority 02
            </div>
            <Network size={24} className="text-[var(--accent-purple)] mb-2" />
            <h4 className="text-xs font-bold uppercase text-[var(--text-primary)]">Local Ollama</h4>
            <p className="text-[10px] text-[var(--text-secondary)] mt-1 font-mono uppercase">Intranet Core</p>
            <span className="text-[8px] text-[var(--accent-purple)] font-bold mt-2 bg-[var(--accent-purple-muted)] px-1 rounded uppercase">
              Self-Hosted Llama
            </span>
          </div>

          {/* Connection 2 */}
          <div className="hidden lg:flex col-span-1 justify-center items-center">
            <div className="flex flex-col items-center text-center">
              <span className="text-[9px] font-mono text-[var(--text-dim)] uppercase mb-1">Fallback</span>
              <div className="flex items-center gap-1">
                <div className="w-6 h-[1px] bg-[var(--border)]" />
                <ArrowRight size={12} className="text-[var(--text-dim)] animate-pulse" />
                <div className="w-6 h-[1px] bg-[var(--border)]" />
              </div>
            </div>
          </div>

          {/* Tier 3: Cloud APIs */}
          <div className="col-span-1 p-4 rounded border border-[var(--accent-blue-border)] bg-[var(--accent-blue-muted)] flex flex-col items-center text-center relative hover:border-[var(--accent-blue)] transition-all">
            <div className="absolute -top-2.5 px-2 py-0.5 rounded bg-[var(--accent-blue)] text-[8px] font-bold text-white uppercase tracking-wider">
              Priority 03
            </div>
            <Globe size={24} className="text-[var(--accent-blue)] mb-2" />
            <h4 className="text-xs font-bold uppercase text-[var(--text-primary)]">Cloud Endpoint</h4>
            <p className="text-[10px] text-[var(--text-secondary)] mt-1 font-mono uppercase">Gemini / OpenAI</p>
            <span className="text-[8px] text-[var(--accent-blue)] font-bold mt-2 bg-[var(--accent-blue-muted)] px-1 rounded uppercase">
              Max Capability
            </span>
          </div>
        </div>
      </motion.div>

      {/* Core Architecture Components Grid */}
      <div className="space-y-8">
        <h2 className="text-xl font-bold text-[var(--text-primary)] uppercase tracking-wider text-center">Architectural Anchors</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6" role="list" aria-label="System architecture components">
          
          {/* Component 1 */}
          <motion.div 
            initial={{ opacity: 0, y: 15 }} 
            whileInView={{ opacity: 1, y: 0 }} 
            viewport={{ once: true }} 
            className="panel p-6 hover:border-[var(--border-focus)] transition-colors relative flex flex-col justify-between"
            role="listitem"
          >
            <div>
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2.5 bg-[var(--accent-muted)] text-[var(--accent)] border border-[var(--accent-border)] rounded">
                  <Cpu size={18} aria-hidden="true" />
                </div>
                <h3 className="text-sm font-bold uppercase tracking-wider text-[var(--text-primary)]">Resilient Hybrid Inference</h3>
              </div>
              <p className="text-xs leading-relaxed text-[var(--text-secondary)] font-mono uppercase">
                The frontend dynamically coordinates client-side execution loops using device-local WebGPU pipelines. In low-compute environments or browsers without WebGPU adapters, the client automatically establishes server-sent event streams with the back-end to leverage intranet nodes or cloud arrays.
              </p>
            </div>
          </motion.div>

          {/* Component 2 */}
          <motion.div 
            initial={{ opacity: 0, y: 15 }} 
            whileInView={{ opacity: 1, y: 0 }} 
            viewport={{ once: true }} 
            transition={{ delay: 0.05 }}
            className="panel p-6 hover:border-[var(--border-focus)] transition-colors relative flex flex-col justify-between"
            role="listitem"
          >
            <div>
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2.5 bg-[var(--accent-purple-muted)] text-[var(--accent-purple)] border border-[var(--accent-purple-border)] rounded">
                  <Brain size={18} aria-hidden="true" />
                </div>
                <h3 className="text-sm font-bold uppercase tracking-wider text-[var(--text-primary)]">Contextual RAG Routing</h3>
              </div>
              <p className="text-xs leading-relaxed text-[var(--text-secondary)] font-mono uppercase">
                Integrates user profiles, diagnostics logs, and real-time vital streams to compile structured medical context profiles. When consulting the AI Copilot, a multi-layer RAG processor extracts matching clinical data from vector representations, embedding references securely prior to model prompting.
              </p>
            </div>
          </motion.div>

          {/* Component 3 */}
          <motion.div 
            initial={{ opacity: 0, y: 15 }} 
            whileInView={{ opacity: 1, y: 0 }} 
            viewport={{ once: true }} 
            className="panel p-6 hover:border-[var(--border-focus)] transition-colors relative flex flex-col justify-between"
            role="listitem"
          >
            <div>
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2.5 bg-[var(--success-muted)] text-[var(--success)] border border-[var(--success-border)] rounded">
                  <Server size={18} aria-hidden="true" />
                </div>
                <h3 className="text-sm font-bold uppercase tracking-wider text-[var(--text-primary)]">Decoupled Architecture</h3>
              </div>
              <p className="text-xs leading-relaxed text-[var(--text-secondary)] font-mono uppercase">
                The UI layer runs inside an optimized Next.js App Router context, strictly interfacing with the database via standard FastAPI gateways. This ensures frontend presentation components remain unaffected by backend analytics pipeline modifications or machine learning model training operations.
              </p>
            </div>
          </motion.div>

          {/* Component 4 */}
          <motion.div 
            initial={{ opacity: 0, y: 15 }} 
            whileInView={{ opacity: 1, y: 0 }} 
            viewport={{ once: true }} 
            transition={{ delay: 0.05 }}
            className="panel p-6 hover:border-[var(--border-focus)] transition-colors relative flex flex-col justify-between"
            role="listitem"
          >
            <div>
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2.5 bg-[var(--warning-muted)] text-[var(--warning)] border border-[var(--warning-border)] rounded">
                  <Lock size={18} aria-hidden="true" />
                </div>
                <h3 className="text-sm font-bold uppercase tracking-wider text-[var(--text-primary)]">Privacy-First Data Guard</h3>
              </div>
              <p className="text-xs leading-relaxed text-[var(--text-secondary)] font-mono uppercase">
                Engineered with strict healthcare security conventions. All diagnostic and patient records undergo local sanitizer sweeps to prevent raw PII from reaching external telemetry. Passwords use secure bcrypt hashes and active session scopes are guarded with JWT headers.
              </p>
            </div>
          </motion.div>

        </div>
      </div>

      {/* Footer / Author section */}
      <div className="text-center pt-8 border-t border-[var(--border)]">
        <p className="text-xs font-mono uppercase text-[var(--text-dim)]">
          AI Healthcare Infrastructure Map • Version 2.1.0
        </p>
        <span className="text-[10px] font-mono text-[var(--text-secondary)] uppercase mt-2.5 block">
          Pavan Badempet • Data Engineering & Intelligent Systems
        </span>
      </div>

    </div>
  );
}
