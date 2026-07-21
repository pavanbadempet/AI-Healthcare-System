import React, { useState } from "react";
import { motion } from "framer-motion";
import { X, ShieldCheck, Cpu, Sliders, RefreshCw, Lock, Layers, Zap, Save, CheckCircle2, Server } from "lucide-react";
import { triggerFederatedSync } from "@/lib/apiFederated";
import { toast } from "@/lib/toast";

interface FederatedNodeOrchestratorModalProps {
  onClose: () => void;
  onConfigSaved?: () => void;
}

interface FederatedNode {
  id: string;
  name: string;
  region: string;
  weight: number;
  active: boolean;
  sampleCount: number;
}

export const FederatedNodeOrchestratorModal: React.FC<FederatedNodeOrchestratorModalProps> = ({ onClose, onConfigSaved }) => {
  const [nodes, setNodes] = useState<FederatedNode[]>([
    { id: "node-1", name: "Mount Sinai Hospital", region: "US-East (New York)", weight: 1.0, active: true, sampleCount: 14200 },
    { id: "node-2", name: "Mayo Clinic Network", region: "US-Midwest (Minnesota)", weight: 1.2, active: true, sampleCount: 18500 },
    { id: "node-3", name: "Apollo Healthcare Hub", region: "IN-South (Hyderabad)", weight: 0.8, active: true, sampleCount: 11300 },
    { id: "node-4", name: "Charité University Hospital", region: "EU-Central (Berlin)", weight: 0.9, active: false, sampleCount: 9400 },
  ]);

  const [epsilon, setEpsilon] = useState(1.5);
  const [delta, setDelta] = useState(1e-5);
  const [mechanism, setMechanism] = useState<"gaussian" | "laplace" | "renyi">("gaussian");
  const [gradientClipping, setGradientClipping] = useState(1.0);
  const [secureAggregation, setSecureAggregation] = useState(true);
  const [isExecuting, setIsExecuting] = useState(false);

  const toggleNodeActive = (id: string) => {
    setNodes((prev) =>
      prev.map((n) => (n.id === id ? { ...n, active: !n.active } : n))
    );
  };

  const handleWeightChange = (id: string, weight: number) => {
    setNodes((prev) =>
      prev.map((n) => (n.id === id ? { ...n, weight } : n))
    );
  };

  const activeNodesCount = nodes.filter((n) => n.active).length;
  const totalSamples = nodes.filter((n) => n.active).reduce((sum, n) => sum + n.sampleCount, 0);

  const handleRunOrchestration = async () => {
    setIsExecuting(true);
    try {
      await triggerFederatedSync({
        model_name: "heart_disease",
        epsilon: epsilon,
        sensitivity: gradientClipping,
      });
      toast.success(`Federated Round Aggregated across ${activeNodesCount} active nodes! ε = ${epsilon}`);
      if (onConfigSaved) onConfigSaved();
      onClose();
    } catch (err: any) {
      toast.error(err.message || "Federated aggregation failed.");
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/80 backdrop-blur-md p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 15 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 15 }}
        className="bg-[#0b0c10] border border-white/10 rounded-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col shadow-2xl font-sans"
        role="dialog"
        aria-modal="true"
        aria-labelledby="fed-title"
      >
        {/* Header */}
        <div className="bg-white/[0.02] border-b border-white/10 p-5 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 shrink-0">
              <ShieldCheck size={18} />
            </div>
            <div>
              <h2 id="fed-title" className="text-sm font-bold text-white uppercase tracking-wider">
                Federated Node Orchestrator & Privacy Tuner
              </h2>
              <p className="text-[10px] text-[var(--text-secondary)] font-mono uppercase">
                Multi-Center Gradient Aggregation with Differential Privacy Noise ($\varepsilon$, $\delta$)
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-zinc-400 hover:text-white p-1.5 rounded-lg hover:bg-white/5 transition-colors"
            aria-label="Close modal"
          >
            <X size={18} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-5 overflow-y-auto flex-1 font-mono text-xs">
          {/* Active Cluster Summary */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="p-3.5 rounded-xl bg-purple-500/5 border border-purple-500/20 space-y-1">
              <span className="text-[10px] text-zinc-400 uppercase font-bold block">Active Federated Nodes</span>
              <div className="text-base font-bold text-purple-300 flex items-center gap-1.5">
                <Server size={14} /> {activeNodesCount} / {nodes.length} Nodes
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-cyan-500/5 border border-cyan-500/20 space-y-1">
              <span className="text-[10px] text-zinc-400 uppercase font-bold block">Pooled Sample Volume</span>
              <div className="text-base font-bold text-cyan-300 flex items-center gap-1.5">
                <Layers size={14} /> {totalSamples.toLocaleString()} Samples
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-emerald-500/5 border border-emerald-500/20 space-y-1">
              <span className="text-[10px] text-zinc-400 uppercase font-bold block">Privacy Loss Budget</span>
              <div className="text-base font-bold text-emerald-300 flex items-center gap-1.5">
                <Lock size={14} /> $\varepsilon = {epsilon.toFixed(1)}$ (Strong DP)
              </div>
            </div>
          </div>

          {/* Differential Privacy Mechanism Settings */}
          <div className="p-4 rounded-xl bg-white/[0.02] border border-white/5 space-y-3 font-sans">
            <span className="text-xs font-bold text-white uppercase tracking-wider block flex items-center gap-1.5 font-mono">
              <Sliders size={14} className="text-purple-400" /> Differential Privacy Hyperparameters
            </span>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              <div>
                <label className="text-[10px] text-zinc-400 uppercase font-bold block mb-1">Noise Mechanism</label>
                <select
                  value={mechanism}
                  onChange={(e) => setMechanism(e.target.value as any)}
                  className="w-full bg-zinc-900 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-purple-300 font-mono font-bold"
                >
                  <option value="gaussian">Gaussian Noise ($\sigma$ clip)</option>
                  <option value="laplace">Laplace Mechanism</option>
                  <option value="renyi">Rényi Differential Privacy</option>
                </select>
              </div>

              <div>
                <label className="text-[10px] text-zinc-400 uppercase font-bold block mb-1">Privacy Budget ($\varepsilon$)</label>
                <input
                  type="range"
                  min={0.5}
                  max={5.0}
                  step={0.1}
                  value={epsilon}
                  onChange={(e) => setEpsilon(Number(e.target.value))}
                  className="w-full accent-purple-500 bg-zinc-800 h-1.5 rounded-lg cursor-pointer"
                />
                <span className="text-[10px] text-purple-400 font-mono font-bold mt-1 block">$\varepsilon = {epsilon}$</span>
              </div>

              <div>
                <label className="text-[10px] text-zinc-400 uppercase font-bold block mb-1">Max Gradient Norm (C)</label>
                <select
                  value={gradientClipping}
                  onChange={(e) => setGradientClipping(Number(e.target.value))}
                  className="w-full bg-zinc-900 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white font-mono font-bold"
                >
                  <option value={0.5}>0.5 (Strict Clip)</option>
                  <option value={1.0}>1.0 (Balanced Standard)</option>
                  <option value={2.0}>2.0 (High Gradient Tolerance)</option>
                </select>
              </div>
            </div>

            <div className="pt-2 border-t border-white/5 flex items-center justify-between font-mono text-[11px]">
              <span className="text-zinc-300 flex items-center gap-1">
                <Lock size={12} className="text-emerald-400" /> Secure Multi-Party Aggregation (SMPC Protocol)
              </span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={secureAggregation}
                  onChange={(e) => setSecureAggregation(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-9 h-5 bg-zinc-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-zinc-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-purple-600"></div>
              </label>
            </div>
          </div>

          {/* Node Participation List */}
          <div className="space-y-2">
            <span className="text-[10px] text-[var(--text-secondary)] uppercase tracking-wider block font-mono">
              Regional Federated Node Topology ({nodes.length} Nodes Configured)
            </span>
            <div className="space-y-2">
              {nodes.map((node) => (
                <div
                  key={node.id}
                  className={`p-3.5 rounded-xl border transition-all flex items-center justify-between gap-3 ${
                    node.active ? "bg-white/[0.02] border-white/10" : "bg-white/[0.005] border-white/5 opacity-50"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={node.active}
                      onChange={() => toggleNodeActive(node.id)}
                      className="accent-purple-500 cursor-pointer w-4 h-4"
                    />
                    <div>
                      <div className="text-white font-bold">{node.name}</div>
                      <div className="text-[10px] text-zinc-400 font-mono">{node.region} • {node.sampleCount.toLocaleString()} Local Encounters</div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 font-mono text-xs">
                    <span className="text-zinc-400 text-[10px]">Weight:</span>
                    <select
                      value={node.weight}
                      onChange={(e) => handleWeightChange(node.id, Number(e.target.value))}
                      disabled={!node.active}
                      className="bg-zinc-900 border border-white/10 rounded px-2 py-1 text-purple-300 font-bold"
                    >
                      <option value={0.5}>0.5x</option>
                      <option value={0.8}>0.8x</option>
                      <option value={1.0}>1.0x</option>
                      <option value={1.2}>1.2x</option>
                      <option value={1.5}>1.5x</option>
                    </select>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="bg-white/[0.02] border-t border-white/10 p-4 flex items-center justify-between font-sans">
          <button
            onClick={onClose}
            className="btn btn-secondary text-xs uppercase font-bold tracking-wide py-2.5 px-4"
          >
            Cancel
          </button>
          <button
            onClick={handleRunOrchestration}
            disabled={isExecuting || activeNodesCount === 0}
            className="btn bg-purple-600 hover:bg-purple-500 text-white text-xs uppercase font-bold tracking-wide py-2.5 px-5 flex items-center gap-2 rounded-xl shadow-lg shadow-purple-600/20 disabled:opacity-50"
          >
            {isExecuting ? <RefreshCw size={14} className="animate-spin" /> : <Zap size={14} />}
            Trigger Federated Round Aggregation
          </button>
        </div>
      </motion.div>
    </div>
  );
};
