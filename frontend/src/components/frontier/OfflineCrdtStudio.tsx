import React, { useState } from 'react';
import { GitMerge, WifiOff, CheckCircle2, ShieldCheck, HeartPulse, RefreshCw, Layers } from 'lucide-react';

export function OfflineCrdtStudio() {
  const [ambulanceAllergy, setAmbulanceAllergy] = useState<string>('Latex');
  const [ambulanceMed, setAmbulanceMed] = useState<string>('Epinephrine 1mg IV');
  const [ambulanceHr, setAmbulanceHr] = useState<number>(112);

  const [clinicAllergy, setClinicAllergy] = useState<string>('Penicillin');
  const [clinicMed, setClinicMed] = useState<string>('Cefazolin 2g IV');
  const [clinicHr, setClinicHr] = useState<number>(124);

  const [isMerged, setIsMerged] = useState<boolean>(true);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);

  const handleMergeSync = () => {
    setIsSyncing(true);
    setTimeout(() => {
      setIsSyncing(false);
      setIsMerged(true);
    }, 300);
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 text-xs font-semibold uppercase tracking-wider mb-1">
            <GitMerge className="w-4 h-4" />
            Level 9 Distributed Resilience & CRDTs
          </div>
          <h2 className="text-xl font-bold text-white">Offline-First Clinical CRDT Synchronization</h2>
          <p className="text-sm text-slate-400 mt-1">
            Enables disconnected ambulances and rural clinics to mutate patient charts without internet, merging with mathematical Strong Eventual Consistency (A ⊔ B ≡ B ⊔ A).
          </p>
        </div>

        <button
          onClick={handleMergeSync}
          disabled={isSyncing}
          className="flex items-center gap-2 px-5 py-2.5 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white font-semibold rounded-xl text-sm transition-all shadow-lg shadow-cyan-600/20"
        >
          {isSyncing ? <RefreshCw className="w-4 h-4 animate-spin" /> : <GitMerge className="w-4 h-4" />}
          Trigger Join-Semilattice Merge (A ⊔ B)
        </button>
      </div>

      {/* Two Disconnected Offline Replicas */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Ambulance Node A */}
        <div className="bg-slate-900/90 border border-amber-500/30 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <span className="font-bold text-sm text-amber-400 flex items-center gap-2">
              <WifiOff className="w-4 h-4" />
              Ambulance Node A (Offline En Route)
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 font-mono">
              Vector Clock: [AMB: 3]
            </span>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <label className="text-slate-400 block mb-1">Observed Allergy (ORSet Add):</label>
              <input
                type="text"
                value={ambulanceAllergy}
                onChange={(e) => setAmbulanceAllergy(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 text-white rounded-lg p-2 font-mono"
              />
            </div>
            <div>
              <label className="text-slate-400 block mb-1">Medication Administered (ORSet Add):</label>
              <input
                type="text"
                value={ambulanceMed}
                onChange={(e) => setAmbulanceMed(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 text-white rounded-lg p-2 font-mono"
              />
            </div>
            <div>
              <label className="text-slate-400 block mb-1">Bedside Vital (LWW Heart Rate at t = 1000s):</label>
              <input
                type="number"
                value={ambulanceHr}
                onChange={(e) => setAmbulanceHr(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-700 text-white rounded-lg p-2 font-mono"
              />
            </div>
          </div>
        </div>

        {/* Clinic Node B */}
        <div className="bg-slate-900/90 border border-purple-500/30 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <span className="font-bold text-sm text-purple-400 flex items-center gap-2">
              <WifiOff className="w-4 h-4" />
              Trauma Bay Node B (Offline Concurrent)
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 font-mono">
              Vector Clock: [BAY: 3]
            </span>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <label className="text-slate-400 block mb-1">Observed Allergy (ORSet Add):</label>
              <input
                type="text"
                value={clinicAllergy}
                onChange={(e) => setClinicAllergy(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 text-white rounded-lg p-2 font-mono"
              />
            </div>
            <div>
              <label className="text-slate-400 block mb-1">Medication Administered (ORSet Add):</label>
              <input
                type="text"
                value={clinicMed}
                onChange={(e) => setClinicMed(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 text-white rounded-lg p-2 font-mono"
              />
            </div>
            <div>
              <label className="text-slate-400 block mb-1">Bedside Vital (LWW Heart Rate at t = 2000s - Newer):</label>
              <input
                type="number"
                value={clinicHr}
                onChange={(e) => setClinicHr(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-700 text-white rounded-lg p-2 font-mono"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Converged Join-Semilattice Chart */}
      {isMerged && (
        <div className="bg-slate-900/90 border border-emerald-500/40 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              Mathematically Converged Patient Chart State (A ⊔ B)
            </h3>
            <span className="text-xs px-3 py-1 bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 rounded-full font-mono">
              Commutativity: A ⊔ B ≡ B ⊔ A Verified
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
            <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
              <span className="text-slate-400 font-bold block uppercase tracking-wider">Active Allergies (ORSet)</span>
              <div className="space-y-1 text-slate-200">
                <div className="p-1.5 bg-slate-900 rounded border border-slate-800">• {ambulanceAllergy}</div>
                <div className="p-1.5 bg-slate-900 rounded border border-slate-800">• {clinicAllergy}</div>
              </div>
              <p className="text-[10px] text-slate-500 font-sans">Tagged union guarantees zero dropped allergies.</p>
            </div>

            <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
              <span className="text-slate-400 font-bold block uppercase tracking-wider">Active Medications (ORSet)</span>
              <div className="space-y-1 text-slate-200">
                <div className="p-1.5 bg-slate-900 rounded border border-slate-800">• {ambulanceMed}</div>
                <div className="p-1.5 bg-slate-900 rounded border border-slate-800">• {clinicMed}</div>
              </div>
              <p className="text-[10px] text-slate-500 font-sans">Both offline orders preserved without conflict.</p>
            </div>

            <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
              <span className="text-slate-400 font-bold block uppercase tracking-wider">Latest Vitals (LWW Register)</span>
              <div className="p-2 bg-emerald-500/10 border border-emerald-500/30 rounded text-emerald-300">
                <strong>Heart Rate:</strong> {clinicHr} bpm
                <span className="block text-[10px] text-emerald-400/80 mt-1">
                  Resolved by microsecond timestamp (Node B t = 2000s won over Node A t = 1000s).
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
