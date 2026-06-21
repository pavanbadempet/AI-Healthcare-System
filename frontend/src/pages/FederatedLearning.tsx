import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Shield, ShieldAlert, ShieldCheck, RefreshCw, Play,
  Activity, Database, Loader2, Calendar, Lock, CheckCircle2, AlertTriangle
} from 'lucide-react';
import {
  fetchFederatedStats,
  fetchFederatedAudits,
  triggerFederatedSync,
  type FederatedStats,
  type SyncAudit
} from '@/lib/apiFederated';
import { runFederatedSimulation } from '@/lib/api';

export default function FederatedLearning() {
  const [stats, setStats] = useState<FederatedStats | null>(null);
  const [audits, setAudits] = useState<SyncAudit[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [selectedModel, setSelectedModel] = useState('heart_disease');
  const [epsilon, setEpsilon] = useState(1.0);
  const [error, setError] = useState<string | null>(null);

  // Phase 7 Federated Simulator States
  const [simEpochs, setSimEpochs] = useState(10);
  const [simEpsilon, setSimEpsilon] = useState(1.5);
  const [simulating, setSimulating] = useState(false);
  const [simResult, setSimResult] = useState<any>(null);

  const refreshInterval = useRef<any>(null);

  const loadData = async (silent = false) => {
    try {
      if (!silent) setLoading(true);
      setError(null);
      const [statsData, auditsData] = await Promise.all([
        fetchFederatedStats(),
        fetchFederatedAudits()
      ]);
      setStats(statsData);
      setAudits(auditsData);
    } catch (err: any) {
      setError(err.message || 'Failed to load federated sync data');
    } finally {
      if (!silent) setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // Auto-refresh every 15 seconds
    refreshInterval.current = setInterval(() => loadData(true), 15000);
    return () => {
      if (refreshInterval.current) clearInterval(refreshInterval.current);
    };
  }, []);

  const handleSync = async (e: React.FormEvent) => {
    e.preventDefault();
    setSyncing(true);
    try {
      await triggerFederatedSync({
        model_name: selectedModel,
        epsilon: epsilon,
        sensitivity: 1.0
      });
      loadData();
      alert('Federated Sync Bridge completed successfully! Differential Privacy noise injected.');
    } catch (err: any) {
      alert(err.message || 'Failed to run Federated Sync');
    } finally {
      setSyncing(false);
    }
  };

  const handleSimRun = async (e: React.FormEvent) => {
    e.preventDefault();
    setSimulating(true);
    setSimResult(null);
    try {
      const res = await runFederatedSimulation(simEpochs, simEpsilon);
      if (res && res.status === 'success') {
        setSimResult(res.results);
      } else {
        alert('Simulation failed to return results');
      }
    } catch (err: any) {
      alert(err.message || 'Failed to run Federated DP Simulation');
    } finally {
      setSimulating(false);
    }
  };

  const getEpsilonGaugeColor = (eps: number) => {
    if (eps < 4.0) return 'from-emerald-500 to-teal-500';
    if (eps < 7.5) return 'from-amber-500 to-orange-500';
    return 'from-red-500 to-rose-600';
  };

  const getEpsilonStatusText = (eps: number) => {
    if (eps < 4.0) return 'SAFE (Strong Privacy)';
    if (eps < 7.5) return 'WARNING (Moderate Privacy)';
    return 'EXHAUSTION RISK (Limit: 10.0)';
  };

  const getModelLabel = (modelKey: string) => {
    const mapping: Record<string, string> = {
      heart_disease: 'Cardiovascular Classifier',
      diabetes: 'Diabetes Prediction Model',
      liver: 'Hepatic ONNX Classifier',
      kidney: 'Renal Diagnostic Model',
      lungs: 'Pulmonary ONNX Classifier',
    };
    return mapping[modelKey] || modelKey;
  };

  const currentEps = stats?.total_epsilon_spent || 0.0;
  const epsPercent = Math.min((currentEps / 10.0) * 100, 100);

  return (
    <div className="min-h-screen bg-slate-950 text-white p-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-10">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2.5 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400">
              <Shield className="w-6 h-6" />
            </div>
            <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
              Federated Privacy Mesh
            </h1>
          </div>
          <p className="text-slate-400 text-sm max-w-xl">
            Secure clinical model retraining bridge. Leverages Local Differential Privacy (LDP)
            with gradient clipping and Laplace noise injection to prevent patient data leaks.
          </p>
        </div>

        <button
          onClick={() => loadData()}
          disabled={loading}
          className="flex items-center justify-center gap-2 px-4 py-2 bg-slate-900 hover:bg-slate-850 active:bg-slate-800 text-slate-300 font-medium rounded-xl border border-slate-800 transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh stats</span>
        </button>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-6 rounded-2xl mb-8 flex items-start gap-4">
          <ShieldAlert className="w-6 h-6 flex-shrink-0" />
          <div>
            <h3 className="font-semibold mb-1">Audit Failure</h3>
            <p className="text-sm opacity-90">{error}</p>
          </div>
        </div>
      )}

      {/* Grid Zone 1: Stats & Privacy Budget */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-10">
        {/* Privacy Budget Gauge Card */}
        <div className="lg:col-span-2 bg-slate-900/40 border border-slate-800/60 rounded-3xl p-6 backdrop-blur-md relative overflow-hidden flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Lock className="w-5 h-5 text-purple-400" />
              <h3 className="font-bold text-slate-200">Global Privacy Budget (\(\epsilon\))</h3>
            </div>
            <span className="text-xs font-mono bg-purple-500/10 text-purple-400 border border-purple-500/20 px-2.5 py-1 rounded-full">
              {getEpsilonStatusText(currentEps)}
            </span>
          </div>

          <div className="my-6">
            <div className="flex justify-between items-baseline mb-2">
              <div className="text-slate-400 text-sm">Cumulative Epsilon Spent</div>
              <div className="text-3xl font-extrabold font-mono text-white">
                {currentEps.toFixed(2)} <span className="text-sm font-normal text-slate-500">/ 10.00</span>
              </div>
            </div>
            {/* Progress bar */}
            <div className="w-full h-4 bg-slate-950 rounded-full overflow-hidden border border-slate-800 p-0.5">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${epsPercent}%` }}
                transition={{ duration: 0.8, ease: 'easeOut' }}
                className={`h-full rounded-full bg-gradient-to-r ${getEpsilonGaugeColor(currentEps)}`}
              />
            </div>
          </div>

          <p className="text-xs text-slate-500 leading-relaxed">
            * Epsilon (\(\epsilon\)) represents the strict privacy loss metric. When the cumulative spent
            exceeds 10.0, the node automatically rejects further syncs to prevent reconstruction attacks.
          </p>
        </div>

        {/* Stats Summary cards */}
        <div className="flex flex-col gap-4">
          {/* Pending feedbacks card */}
          <div className="bg-slate-900/40 border border-slate-800/60 rounded-2xl p-5 flex items-center justify-between backdrop-blur-md">
            <div>
              <div className="text-xs text-slate-400 uppercase tracking-widest font-semibold mb-1">Pending Sync Records</div>
              <div className="text-4xl font-extrabold font-mono text-amber-400">
                {stats ? stats.pending_count : 0}
              </div>
              <p className="text-[11px] text-slate-500 mt-2">Clinician corrections waiting for sync bridge.</p>
            </div>
            <div className="p-4 rounded-xl bg-amber-500/10 text-amber-400">
              <Activity className="w-6 h-6 animate-pulse" />
            </div>
          </div>

          {/* Sync status check */}
          <div className="bg-slate-900/40 border border-slate-800/60 rounded-2xl p-5 flex items-center justify-between backdrop-blur-md">
            <div>
              <div className="text-xs text-slate-400 uppercase tracking-widest font-semibold mb-1">Sync Audits Logged</div>
              <div className="text-4xl font-extrabold font-mono text-teal-400">
                {audits.length}
              </div>
              <p className="text-[11px] text-slate-500 mt-2">Differential privacy compliance check ledger.</p>
            </div>
            <div className="p-4 rounded-xl bg-teal-500/10 text-teal-400">
              <Database className="w-6 h-6" />
            </div>
          </div>
        </div>
      </div>

      {/* Grid Zone 2: Sync Control & History */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Sync Trigger form */}
        <div className="bg-slate-900/40 border border-slate-800/60 rounded-3xl p-6 backdrop-blur-md">
          <div className="flex items-center gap-2 mb-6">
            <Play className="w-5 h-5 text-emerald-400" />
            <h3 className="font-bold text-slate-200">Trigger Sync Bridge</h3>
          </div>

          <form onSubmit={handleSync} className="space-y-5">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-400 uppercase">Target ML Model</label>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-purple-500"
              >
                <option value="heart_disease">Heart Disease Classifier</option>
                <option value="diabetes">Diabetes Classifier</option>
                <option value="liver">Liver Disease Model</option>
                <option value="kidney">Kidney Diagnostic Model</option>
                <option value="lungs">Pulmonary Classifier</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between items-center">
                <label className="text-xs font-semibold text-slate-400 uppercase">Epsilon Parameter (\(\epsilon\))</label>
                <span className="text-xs font-mono font-bold text-purple-400">{epsilon.toFixed(1)}</span>
              </div>
              <input
                type="range"
                min="0.1"
                max="5.0"
                step="0.1"
                value={epsilon}
                onChange={(e) => setEpsilon(parseFloat(e.target.value))}
                className="w-full accent-purple-500 bg-slate-950 rounded-lg appearance-none h-2 border border-slate-800"
              />
              <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                <span>0.1 (Max Privacy)</span>
                <span>5.0 (High Precision)</span>
              </div>
            </div>

            <div className="p-3.5 bg-slate-950/60 rounded-xl border border-slate-800/80 text-xs text-slate-400 space-y-2">
              <div className="flex items-center gap-1.5 font-semibold text-slate-300">
                <Lock className="w-3.5 h-3.5 text-emerald-400" />
                <span>Local DP Active</span>
              </div>
              <p className="leading-relaxed">
                Aggregates pending feedbacks, clips local gradients to L2-norm of 1.0,
                and injects Laplace noise. Epsilon spent will be permanently logged.
              </p>
            </div>

            <button
              type="submit"
              disabled={syncing || (stats ? stats.pending_count === 0 : false)}
              className="w-full flex items-center justify-center gap-2 px-5 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-800 disabled:text-slate-500 disabled:cursor-not-allowed font-medium rounded-xl transition-colors shadow-lg shadow-purple-600/10 mt-2"
            >
              {syncing ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Syncing Node...</span>
                </>
              ) : (
                <>
                  <ShieldCheck className="w-5 h-5" />
                  <span>Execute Sync Bridge</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Sync Audits History table */}
        <div className="lg:col-span-2 bg-slate-900/40 border border-slate-800/60 rounded-3xl p-6 backdrop-blur-md overflow-hidden flex flex-col">
          <div className="flex items-center justify-between mb-6">
            <h3 className="font-bold text-slate-200">Compliance Audit Ledger</h3>
            <span className="text-xs text-slate-500">Auto-refresh: 15s</span>
          </div>

          <div className="flex-1 overflow-x-auto">
            <table className="w-full text-left text-sm border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-xs font-semibold text-slate-400 uppercase">
                  <th className="py-3 px-4">Sync Run ID</th>
                  <th className="py-3 px-4">Model</th>
                  <th className="py-3 px-4">Records</th>
                  <th className="py-3 px-4">Epsilon (\(\epsilon\))</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40 font-mono text-xs">
                {loading && audits.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-12 text-center text-slate-500">
                      <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2 text-purple-400" />
                      Loading history...
                    </td>
                  </tr>
                ) : audits.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-12 text-center text-slate-500 font-sans">
                      No sync runs have been executed yet.
                    </td>
                  </tr>
                ) : (
                  audits.map((audit) => (
                    <tr key={audit.id} className="hover:bg-slate-900/30 transition-colors">
                      <td className="py-3 px-4 text-slate-400 select-all" title={audit.sync_run_id}>
                        {audit.sync_run_id.slice(0, 8)}...
                      </td>
                      <td className="py-3 px-4 text-slate-200 font-sans">
                        {getModelLabel(audit.model_name)}
                      </td>
                      <td className="py-3 px-4 text-slate-300 font-bold">{audit.records_synced}</td>
                      <td className="py-3 px-4 text-slate-300">
                        {audit.epsilon_consumed > 0 ? `\u03b5=${audit.epsilon_consumed.toFixed(2)}` : '0.00'}
                      </td>
                      <td className="py-3 px-4">
                        <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-medium border ${
                          audit.status === 'completed'
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/25'
                            : audit.status === 'rejected'
                            ? 'bg-rose-500/10 text-rose-400 border-rose-500/25'
                            : 'bg-red-500/10 text-red-400 border-red-500/25'
                        }`}>
                          {audit.status === 'completed' && <CheckCircle2 className="w-3 h-3" />}
                          {audit.status === 'rejected' && <Lock className="w-3 h-3" />}
                          {audit.status === 'failed' && <AlertTriangle className="w-3 h-3" />}
                          {audit.status.toUpperCase()}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-500 font-sans">
                        {new Date(audit.created_at).toLocaleTimeString()} ({new Date(audit.created_at).toLocaleDateString()})
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Grid Zone 3: Federated Simulation Console (Phase 7) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mt-10">
        {/* Simulator Form */}
        <div className="bg-slate-900/40 border border-slate-800/60 rounded-3xl p-6 backdrop-blur-md">
          <div className="flex items-center gap-2 mb-6">
            <Activity className="w-5 h-5 text-purple-400" />
            <h3 className="font-bold text-slate-200">Collab Training Simulator</h3>
          </div>

          <form onSubmit={handleSimRun} className="space-y-5">
            <div className="space-y-1.5">
              <div className="flex justify-between items-center">
                <label className="text-xs font-semibold text-slate-400 uppercase">Training Epochs</label>
                <span className="text-xs font-mono font-bold text-purple-400">{simEpochs}</span>
              </div>
              <input
                type="range"
                min="2"
                max="30"
                step="1"
                value={simEpochs}
                onChange={(e) => setSimEpochs(parseInt(e.target.value))}
                className="w-full accent-purple-500 bg-slate-950 rounded-lg appearance-none h-2 border border-slate-800"
              />
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between items-center">
                <label className="text-xs font-semibold text-slate-400 uppercase">Sim Epsilon (\(\epsilon\))</label>
                <span className="text-xs font-mono font-bold text-purple-400">{simEpsilon.toFixed(1)}</span>
              </div>
              <input
                type="range"
                min="0.5"
                max="5.0"
                step="0.1"
                value={simEpsilon}
                onChange={(e) => setSimEpsilon(parseFloat(e.target.value))}
                className="w-full accent-purple-500 bg-slate-950 rounded-lg appearance-none h-2 border border-slate-800"
              />
            </div>

            <button
              type="submit"
              disabled={simulating}
              className="w-full flex items-center justify-center gap-2 px-5 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-800 disabled:text-slate-500 disabled:cursor-not-allowed font-medium rounded-xl transition-colors shadow-lg shadow-purple-600/10 mt-4"
            >
              {simulating ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Simulating DP-FedAvg...</span>
                </>
              ) : (
                <>
                  <Play className="w-5 h-5" />
                  <span>Run DP-FedAvg Sim</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Simulator Results Chart & Details */}
        <div className="lg:col-span-2 bg-slate-900/40 border border-slate-800/60 rounded-3xl p-6 backdrop-blur-md flex flex-col justify-between">
          <div>
            <h3 className="font-bold text-slate-200 mb-4">DP-FedAvg Accuracy Convergence</h3>
            {!simResult ? (
              <div className="flex-1 flex flex-col items-center justify-center py-10 text-slate-500 font-sans border border-dashed border-slate-800 rounded-2xl bg-slate-950/20">
                <Shield className="w-8 h-8 text-slate-700 mb-2" />
                <p className="text-xs">No active simulation run. Adjust parameters and trigger above.</p>
              </div>
            ) : (
              <div className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-slate-950/40 border border-slate-850 p-4 rounded-2xl">
                    <span className="text-[10px] text-slate-500 uppercase font-semibold">Centralized Baseline Accuracy</span>
                    <div className="text-2xl font-extrabold text-emerald-400 font-mono">{(simResult.acc_central * 100).toFixed(2)}%</div>
                    <div className="w-full h-1.5 bg-slate-900 rounded-full mt-2 overflow-hidden">
                      <div className="h-full bg-emerald-400" style={{ width: `${simResult.acc_central * 100}%` }}></div>
                    </div>
                  </div>
                  <div className="bg-slate-950/40 border border-slate-850 p-4 rounded-2xl">
                    <span className="text-[10px] text-slate-500 uppercase font-semibold">Federated DP Accuracy</span>
                    <div className="text-2xl font-extrabold text-purple-400 font-mono">{(simResult.acc_federated * 100).toFixed(2)}%</div>
                    <div className="w-full h-1.5 bg-slate-900 rounded-full mt-2 overflow-hidden">
                      <div className="h-full bg-purple-400" style={{ width: `${simResult.acc_federated * 100}%` }}></div>
                    </div>
                  </div>
                </div>

                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-semibold block mb-2">Epoch Training History</span>
                  <div className="grid grid-cols-5 sm:grid-cols-10 gap-2">
                    {simResult.history.map((acc: number, idx: number) => (
                      <div key={idx} className="bg-slate-950 border border-slate-850 rounded-lg p-1.5 flex flex-col items-center">
                        <span className="text-[8px] text-slate-500 font-mono">E{idx + 1}</span>
                        <span className="text-[10px] font-bold font-mono text-purple-400">{(acc * 100).toFixed(0)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
          <p className="text-[10px] text-slate-500 mt-4 leading-relaxed">
            * The DP-FedAvg simulator distributes synthetic diabetes clinical records across 3 local hospital nodes. It validates how injecting Laplace noise to clipped local weights preserves centralized accuracy baseline while protecting patient privacy.
          </p>
        </div>
      </div>
    </div>
  );
}
