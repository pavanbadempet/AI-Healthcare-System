"use client";

import { motion } from "framer-motion";
import { Sparkles, Activity, Shield, Database, Brain, Cpu, Server, Lock } from "lucide-react";

export default function AboutPage() {
  return (
    <div className="w-full max-w-5xl mx-auto space-y-16 pb-12">
      
      {/* Hero */}
      <div className="text-center space-y-4">
        <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="w-20 h-20 mx-auto flex items-center justify-center mb-6 shadow-lg bg-[var(--accent)] border-2 border-[var(--accent-border)]" aria-hidden="true">
          <Sparkles size={40} className="text-white" />
        </motion.div>
        <motion.h1 initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="text-4xl md:text-5xl font-bold text-[var(--text-primary)] tracking-tight">
          AI Healthcare System
        </motion.h1>
        <motion.p initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="text-lg max-w-2xl mx-auto text-[var(--text-dim)]">
          A secure, high-performance platform integrating tri-tier AI inference with robust data engineering pipelines to deliver real-time medical insights.
        </motion.p>
      </div>

      {/* Architecture Grid */}
      <div>
        <h2 className="text-2xl font-bold text-[var(--text-primary)] mb-8 text-center">System Architecture</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6" role="list" aria-label="System architecture components">
          
          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="panel p-8" role="listitem">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-[var(--accent-muted)] text-[var(--accent)] border border-[var(--accent-border)]"><Cpu size={24} aria-hidden="true" /></div>
              <h3 className="text-xl font-semibold text-[var(--text-primary)]">Tri-Tier Inference Engine</h3>
            </div>
            <p className="text-sm leading-relaxed text-[var(--text-secondary)]">
              A fallback inference chain designed for privacy-conscious resilience. The system prioritizes local <strong>WebGPU</strong> execution directly in the browser. If unavailable, it falls back to a local <strong>Ollama</strong> instance, and finally routes to enterprise <strong>Cloud endpoints</strong> (Gemini/OpenAI) for maximum capability.
            </p>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.1 }} className="panel p-8" role="listitem">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-[var(--accent-purple-muted)] text-[var(--accent-purple)] border border-[var(--accent-purple-border)]"><Brain size={24} aria-hidden="true" /></div>
              <h3 className="text-xl font-semibold text-[var(--text-primary)]">Context-Aware RAG</h3>
            </div>
            <p className="text-sm leading-relaxed text-[var(--text-secondary)]">
              The AI Copilot does not just answer general questions. It utilizes a Retrieval-Augmented Generation (RAG) pipeline to dynamically build a <strong>Clinical Context Profile</strong> based on your specific historical assessments, vitals, and profile data.
            </p>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="panel p-8" role="listitem">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-[var(--success-muted)] text-[var(--success)] border border-[var(--success-border)]"><Server size={24} aria-hidden="true" /></div>
              <h3 className="text-xl font-semibold text-[var(--text-primary)]">Decoupled UI & Data Layers</h3>
            </div>
            <p className="text-sm leading-relaxed text-[var(--text-secondary)]">
              The frontend is built on <strong>Next.js 15 (App Router)</strong> and completely isolated from the backend logic. This allows data engineers to deploy complex Spark pipelines or modify the FastAPI PostgreSQL schema without ever risking UI downtime.
            </p>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.1 }} className="panel p-8" role="listitem">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-[var(--warning-muted)] text-[var(--warning)] border border-[var(--warning)]/20"><Lock size={24} aria-hidden="true" /></div>
              <h3 className="text-xl font-semibold text-[var(--text-primary)]">Security & Privacy</h3>
            </div>
            <p className="text-sm leading-relaxed text-[var(--text-secondary)]">
              Built with healthcare privacy safeguards in mind. Passwords are hashed via bcrypt, sessions use JWT, and local AI execution can keep selected AI workflows on-device when configured.
            </p>
          </motion.div>

        </div>
      </div>

      <div className="text-center pt-8 border-t border-[var(--border)]">
        <p className="text-sm text-[var(--text-dim)]">
          Developed by <strong>Pavan Badempet</strong><br/>
          <span className="text-xs opacity-60 mt-2 block">Data Engineering & AI Systems</span>
        </p>
      </div>

    </div>
  );
}
