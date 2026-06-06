import { motion } from "framer-motion";
import { Activity, Heart, Droplets, Wind, Clipboard, ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";

const ASSESSMENT_MODES = [
  {
    id: "diabetes",
    title: "Diabetes Assessment",
    description: "Endocrine metrics screening utilizing BRFSS behavior models.",
    icon: Droplets,
    color: "var(--accent)",
    href: "/predict/diabetes",
    meta: "BRFSS v1.0 • 9 features"
  },
  {
    id: "heart",
    title: "Cardiovascular Analysis",
    description: "Cardiac risk evaluation based on Cleveland clinical datasets.",
    icon: Heart,
    color: "var(--danger)",
    href: "/predict/heart",
    meta: "Cleveland v2.1 • 13 features"
  },
  {
    id: "liver",
    title: "Hepatic Diagnostics",
    description: "Functional assessment of liver enzyme profiles and biliary indexes.",
    icon: Activity,
    color: "var(--success)",
    href: "/predict/liver",
    meta: "ILPD v1.5 • 10 features"
  },
  {
    id: "kidney",
    title: "Renal Function Panel",
    description: "Urinalysis and nephrotic index glomerular filtration markers.",
    icon: Clipboard,
    color: "var(--warning)",
    href: "/predict/kidney",
    meta: "Renal v3.0 • 24 features"
  },
  {
    id: "lungs",
    title: "Pulmonary Screening",
    description: "Lung cancer hazard scoring based on symptomatic telemetry.",
    icon: Wind,
    color: "var(--accent-purple)",
    href: "/predict/lungs",
    meta: "Pulm v1.2 • 15 features"
  }
];

export default function PredictHub() {
  return (
    <div className="py-6 space-y-6">
      <header className="space-y-1.5 border-l-2 border-[var(--accent)] pl-4">
        <h1 className="text-xl font-bold text-[var(--text-primary)] uppercase tracking-wider">Predictive Diagnostics</h1>
        <p className="text-[var(--text-dim)] text-xs font-mono tracking-wide max-w-xl uppercase">
          Select a diagnostic subsystem node to open an assessment interface. Models run on-premises in the secure AI enclave.
        </p>
      </header>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4" role="list" aria-label="Available diagnostic models">
        {ASSESSMENT_MODES.map((mode, i) => (
          <Link key={mode.id} to={mode.href}>
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.04 }}
              whileHover={{ scale: 1.01 }}
              className="group relative panel p-6 h-full flex flex-col cursor-pointer overflow-hidden transition-all duration-200 border-[var(--border)] hover:border-[var(--border-focus)] bg-[rgba(24,24,27,0.4)]"
              role="listitem"
            >
              {/* Radial subtle hover glow */}
              <div 
                className="absolute -top-20 -right-20 w-40 h-40 rounded-full blur-[60px] opacity-0 group-hover:opacity-10 transition-opacity duration-300 pointer-events-none"
                style={{ backgroundColor: mode.color }}
                aria-hidden="true"
              />

              <div className="flex justify-between items-start mb-6">
                <div 
                  className="p-2 rounded bg-[rgba(255,255,255,0.02)] border border-[var(--border)] text-[var(--text-dim)] group-hover:text-white transition-colors"
                  style={{ color: mode.color }}
                >
                  <mode.icon size={18} aria-hidden="true" />
                </div>
                <div className="mono-meta text-[var(--text-dim)]">
                  {mode.meta}
                </div>
              </div>

              <h3 className="text-sm font-bold text-[var(--text-primary)] uppercase tracking-wider mb-2">
                {mode.title}
              </h3>
              
              <p className="text-xs text-[var(--text-secondary)] font-mono uppercase leading-relaxed mb-6 flex-1">
                {mode.description}
              </p>

              <div className="flex items-center gap-1.5 section-label text-[var(--text-dim)] group-hover:text-[var(--accent)] transition-all">
                Open Subsystem <ArrowRight size={12} className="group-hover:translate-x-1 transition-transform" aria-hidden="true" />
              </div>
            </motion.div>
          </Link>
        ))}
      </div>
    </div>
  );
}
