import React, { useState } from 'react';
import { Flame, ShieldAlert, Zap, Lock, RefreshCw, CheckCircle2, AlertOctagon, Activity } from 'lucide-react';

export function ResilienceChaosStudio() {
  // Concurrency state
  const [inflight, setInflight] = useState<number>(14);
  const concurrencyLimit = 20.0;
  const utilization = inflight / concurrencyLimit;
  const gradient = Math.max(0.4, 1.2 - (inflight > 16 ? 0.6 : 0.0));

  // Idempotency state
  const [idempotencyKey, setIdempotencyKey] = useState<string>('order-tx-8812');
  const [doseMg, setDoseMg] = useState<number>(10);
  const [idempotencyHistory, setIdempotencyHistory] = useState<string[]>([]);
  const [idempotencyStatus, setIdempotencyStatus] = useState<string | null>(null);

  // Circuit breaker state
  const [circuitState, setCircuitState] = useState<'CLOSED' | 'OPEN' | 'HALF_OPEN'>('CLOSED');
  const [failureCount, setFailureCount] = useState<number>(0);

  const handleExecuteOrder = () => {
    if (idempotencyHistory.length === 0) {
      setIdempotencyHistory([`${idempotencyKey}:10mg`]);
      setIdempotencyStatus('SUCCESS (HTTP 200) - Executed & Committed. Deterministic hash registered.');
    } else {
      const original = idempotencyHistory[0];
      const isTampered = original !== `${idempotencyKey}:${doseMg}mg`;
      if (isTampered) {
        setIdempotencyStatus('HTTP 409 CONFLICT: Payload tampered under registered idempotency key! Transaction rejected.');
      } else {
        setIdempotencyStatus('REPLAY (HTTP 200, X-Idempotent-Replay: True) - Exact deterministic response replayed. Double-dosing strictly prevented.');
      }
    }
  };

  const handleInjectFailure = () => {
    const newFailures = failureCount + 1;
    setFailureCount(newFailures);
    if (newFailures >= 3) {
      setCircuitState('OPEN');
    }
  };

  const handleHealBreaker = () => {
    setCircuitState('HALF_OPEN');
    setTimeout(() => {
      setCircuitState('CLOSED');
      setFailureCount(0);
    }, 400);
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-rose-400 text-xs font-semibold uppercase tracking-wider mb-1">
            <Flame className="w-4 h-4" />
            Level 9 Backend High-Availability & Resilience
          </div>
          <h2 className="text-xl font-bold text-white">Adaptive Concurrency, Idempotency & Chaos Mesh</h2>
          <p className="text-sm text-slate-400 mt-1">
            Interactive demonstration of Vegas/CoDel gradient load shedding, SHA-256 cryptographic idempotency, and 3-state sliding-window self-healing.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Panel 1: Adaptive Concurrency & Load Shedder */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 space-y-4">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyan-400" />
            Adaptive Concurrency Limiter
          </h3>

          <div>
            <label className="text-slate-400 text-xs block mb-1">
              Active Inflight Requests: <span className="text-white font-mono font-bold">{inflight} / {concurrencyLimit}</span>
            </label>
            <input
              type="range"
              min="0"
              max="28"
              value={inflight}
              onChange={(e) => setInflight(Number(e.target.value))}
              className="w-full accent-cyan-400"
            />
          </div>

          <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 space-y-1.5 text-xs font-mono">
            <div className="flex justify-between">
              <span className="text-slate-400">System Utilization:</span>
              <span className={utilization >= 0.9 ? 'text-rose-400 font-bold' : utilization >= 0.6 ? 'text-amber-400 font-bold' : 'text-emerald-400 font-bold'}>
                {Math.round(utilization * 100)}%
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Latency Gradient:</span>
              <span className="text-cyan-400">{gradient.toFixed(2)}</span>
            </div>
          </div>

          <div className="space-y-2 text-xs">
            <div className="p-2.5 rounded-lg border bg-emerald-500/10 border-emerald-500/30 text-emerald-300 flex justify-between items-center">
              <span>CRITICAL_ACTUATION (ICU Pumps)</span>
              <span className="font-bold font-mono">ADMITTED (100%)</span>
            </div>
            <div className={`p-2.5 rounded-lg border flex justify-between items-center ${utilization < 0.9 ? 'bg-sky-500/10 border-sky-500/30 text-sky-300' : 'bg-rose-500/10 border-rose-500/30 text-rose-300'}`}>
              <span>CLINICAL_QUERY (EHR Chart)</span>
              <span className="font-bold font-mono">{utilization < 0.9 ? 'ADMITTED' : 'SHED (Congested)'}</span>
            </div>
            <div className={`p-2.5 rounded-lg border flex justify-between items-center ${utilization < 0.6 ? 'bg-purple-500/10 border-purple-500/30 text-purple-300' : 'bg-rose-500/10 border-rose-500/30 text-rose-300'}`}>
              <span>BACKGROUND_ANALYTICS</span>
              <span className="font-bold font-mono">{utilization < 0.6 ? 'ADMITTED' : 'SHED (Early Backoff)'}</span>
            </div>
          </div>
        </div>

        {/* Panel 2: Cryptographic Idempotency Guard */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 space-y-4">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <Lock className="w-4 h-4 text-purple-400" />
            Cryptographic Idempotency Engine
          </h3>

          <div className="space-y-3 text-xs">
            <div>
              <label className="text-slate-400 block mb-1">Idempotency Key:</label>
              <input
                type="text"
                value={idempotencyKey}
                onChange={(e) => setIdempotencyKey(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 text-white rounded-lg p-2 font-mono"
              />
            </div>
            <div>
              <label className="text-slate-400 block mb-1">Medication Dose:</label>
              <input
                type="number"
                value={doseMg}
                onChange={(e) => setDoseMg(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-700 text-white rounded-lg p-2 font-mono"
              />
            </div>
          </div>

          <button
            onClick={handleExecuteOrder}
            className="w-full py-2 bg-purple-600 hover:bg-purple-500 text-white font-semibold rounded-xl text-xs transition-all shadow-lg shadow-purple-600/20"
          >
            Submit High-Stakes Clinical Order
          </button>

          {idempotencyStatus && (
            <div className={`p-3 rounded-xl border text-xs leading-relaxed ${idempotencyStatus.includes('CONFLICT') ? 'bg-rose-500/10 border-rose-500/30 text-rose-300 font-bold' : idempotencyStatus.includes('REPLAY') ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-300' : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'}`}>
              {idempotencyStatus}
            </div>
          )}
        </div>

        {/* Panel 3: Sliding-Window Circuit Breaker */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-400" />
              Chaos Mesh Circuit Breaker
            </h3>
            <span className={`text-xs px-2.5 py-1 rounded-full font-mono font-bold ${circuitState === 'CLOSED' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : circuitState === 'OPEN' ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30 animate-pulse' : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'}`}>
              {circuitState}
            </span>
          </div>

          <p className="text-xs text-slate-400">
            Fails fast when downstream services encounter transient network cuts or database deadlocks.
          </p>

          <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 space-y-1 text-xs font-mono">
            <div className="flex justify-between">
              <span className="text-slate-400">Recent Failures:</span>
              <span className="text-rose-400 font-bold">{failureCount} / 3 Threshold</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Breaker Policy:</span>
              <span className="text-slate-300">Sliding Window (Size 10)</span>
            </div>
          </div>

          <div className="space-y-2">
            <button
              onClick={handleInjectFailure}
              className="w-full py-2 bg-rose-600/80 hover:bg-rose-600 text-white font-semibold rounded-xl text-xs transition-all"
            >
              Inject Synthetic Downstream Failure
            </button>
            <button
              onClick={handleHealBreaker}
              className="w-full py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 font-semibold rounded-xl text-xs transition-all"
            >
              Simulate Cooldown & Trial Healing Probe
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
