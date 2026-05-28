"use client";

import { motion } from "framer-motion";
import { Activity, Heart, Droplets, Wind, Clipboard, ArrowRight } from "lucide-react";
import Link from "next/link";

const ASSESSMENT_MODES = [
  {
    id: "diabetes",
    title: "Diabetes Assessment",
    description: "Multi-factor endocrine analysis utilizing BRFSS behavioral data points.",
    icon: Droplets,
    color: "var(--accent)",
    href: "/predict/diabetes",
    meta: "BRFSS v1.0 • 9 Features"
  },
  {
    id: "heart",
    title: "Cardiovascular Analysis",
    description: "Comprehensive cardiac risk modeling based on the Cleveland clinical dataset.",
    icon: Heart,
    color: "var(--danger)",
    href: "/predict/heart",
    meta: "Cleveland v2.1 • 13 Features"
  },
  {
    id: "liver",
    title: "Hepatic Diagnostics",
    description: "Assessment of liver enzyme efficacy and hepatic dysfunction probability.",
    icon: Activity,
    color: "var(--success)",
    href: "/predict/liver",
    meta: "ILPD v1.5 • 10 Features"
  },
  {
    id: "kidney",
    title: "Renal Function Panel",
    description: "Chronic kidney disease detection via comprehensive urinalysis and blood markers.",
    icon: Clipboard,
    color: "var(--warning)",
    href: "/predict/kidney",
    meta: "Renal v3.0 • 24 Features"
  },
  {
    id: "lungs",
    title: "Pulmonary Screening",
    description: "Evaluation of lung cancer risk based on symptomatic and behavioral telemetry.",
    icon: Wind,
    color: "var(--accent)",
    href: "/predict/lungs",
    meta: "Pulm v1.2 • 15 Features"
  }
];

export default function PredictHub() {
  return (
    <div className="py-8 space-y-12">
      <header className="space-y-2 border-l-4 border-[var(--accent)] pl-6">
        <h1 className="text-3xl font-bold text-[var(--text-primary)] uppercase tracking-wider">Predictive Diagnostics</h1>
        <p className="text-[var(--text-dim)] text-sm font-mono tracking-wide max-w-2xl">
          Select a diagnostic subsystem to initiate a clinical assessment. All models are running on-premises within the secure AI enclave.
        </p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6" role="list" aria-label="Available diagnostic models">
        {ASSESSMENT_MODES.map((mode, i) => (
          <Link key={mode.id} href={mode.href}>
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              whileHover={{ scale: 1.02 }}
              className="group relative panel p-8 h-full flex flex-col cursor-pointer overflow-hidden transition-all duration-300 hover:border-[var(--border-focus)]"
              role="listitem"
            >
              {/* Background Glow */}
              <div 
                className="absolute -top-24 -right-24 w-48 h-48 rounded-full blur-[80px] opacity-0 group-hover:opacity-20 transition-opacity duration-500"
                style={{ backgroundColor: mode.color }}
                aria-hidden="true"
              />

              <div className="flex justify-between items-start mb-8">
                <div className="p-3 bg-[var(--bg-card)] border border-[var(--border)] text-[var(--text-dim)] group-hover:text-[var(--text-primary)] group-hover:border-transparent transition-all" style={{ backgroundColor: `color-mix(in srgb, ${mode.color} 5%, transparent)` }}>
                  <mode.icon size={24} aria-hidden="true" />
                </div>
                <div className="mono-meta text-[var(--border-focus)]">
                  {mode.meta}
                </div>
              </div>

              <h3 className="text-xl font-bold text-[var(--text-primary)] uppercase tracking-wide mb-3 group-hover:text-[var(--text-primary)] transition-colors">
                {mode.title}
              </h3>
              
              <p className="text-sm text-[var(--text-dim)] font-mono leading-relaxed mb-8 flex-1">
                {mode.description}
              </p>

              <div className="flex items-center gap-2 section-label text-[var(--border-focus)] group-hover:text-[var(--text-primary)] transition-all">
                Access Node <ArrowRight size={14} className="group-hover:translate-x-1 transition-transform" aria-hidden="true" />
              </div>

              {/* Decorative Corner */}
              <div className="absolute bottom-0 right-0 p-1" aria-hidden="true">
                <div className="w-4 h-4 border-b border-r border-[var(--border)] group-hover:border-[var(--text-primary)] transition-colors" />
              </div>
            </motion.div>
          </Link>
        ))}
      </div>
    </div>
  );
}
