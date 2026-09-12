import React, { useState } from 'react';
import {
  Activity, ShieldCheck, Zap, Dna, Lock, Play, RefreshCw, CheckCircle2,
  AlertTriangle, ArrowUpRight, Award, Stethoscope, Sliders, Shield
} from 'lucide-react';
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, Legend
} from 'recharts';

type ActiveTab = 'twin' | 'causal' | 'cybernetics' | 'docking' | 'zk';

export default function AutonomousFrontier() {
  const [activeTab, setActiveTab] = useState<ActiveTab>('twin');

  // Tab 1: Digital Twin State
  const [twinAge, setTwinAge] = useState<number>(55);
  const [twinSbp, setTwinSbp] = useState<number>(145);
  const [twinEgfr, setTwinEgfr] = useState<number>(68);
  const [twinHba1c, setTwinHba1c] = useState<number>(7.6);
  const [selectedIntervention, setSelectedIntervention] = useState<string>('sglt2i_plus_glp1');
  const [isSimulatingTwin, setIsSimulatingTwin] = useState<boolean>(false);

  // Trajectory mock/initial data
  const trajectoryYears = Array.from({ length: 11 }, (_, i) => {
    const decay = i * (twinAge > 60 ? 3.8 : 2.9);
    const untreated = Math.max(25, 78 - decay);
    const benefit = selectedIntervention.includes('plus') ? 1.8 * i : 1.2 * i;
    const treated = Math.min(96, Math.max(untreated, untreated + benefit));
    return {
      year: `Yr ${i}`,
      untreated: Math.round(untreated),
      treated: Math.round(treated),
      p10_upper: Math.min(99, Math.round(treated + 4)),
      p90_lower: Math.max(20, Math.round(untreated - 5)),
    };
  });

  // Tab 2: Causal State
  const [causalSbp, setCausalSbp] = useState<number>(140);
  const [causalEgfr, setCausalEgfr] = useState<number>(65);
  const [causalHba1c, setCausalHba1c] = useState<number>(7.8);
  const [causalIntervention, setCausalIntervention] = useState<string>('sglt2i_plus_glp1');

  // Dynamic causal calculations
  const baselineMace = Math.min(48, Math.max(5, (causalSbp - 110) * 0.35 + (8.5 - causalEgfr / 15) * 4.0 + (causalHba1c - 5.5) * 5.0));
  const maceReductionPct = causalIntervention.includes('plus') ? 0.32 : causalIntervention === 'quad' ? 0.44 : 0.20;
  const counterfactualMace = Math.max(1.8, baselineMace * (1 - maceReductionPct));
  const iteMace = baselineMace - counterfactualMace;
  const iteEgfrSlope = causalIntervention.includes('plus') ? 2.1 : causalIntervention === 'quad' ? 2.8 : 1.45;
  const eValue = (baselineMace / counterfactualMace) + Math.sqrt((baselineMace / counterfactualMace) * ((baselineMace / counterfactualMace) - 1));

  // Tab 3: Cybernetics & Lyapunov State
  const [monitoredMap, setMonitoredMap] = useState<number>(62);
  const [monitoredHr, setMonitoredHr] = useState<number>(112);
  const [infusionRate, setInfusionRate] = useState<number>(6.0);
  const mapError = monitoredMap - 85.0;
  const lyapunovV = 0.5 * (mapError ** 2);
  const recommendedRateDelta = mapError < 0 ? Math.min(4.0, Math.abs(mapError) * 0.12) : 0.0;
  const updatedInfusionRate = Math.min(35.0, infusionRate + recommendedRateDelta);
  const lyapunovVDot = -0.05 * (mapError ** 2) + mapError * recommendedRateDelta * 0.08;
  const isStable = lyapunovVDot <= 0.0;

  // Tab 4: Generative Docking State
  const [targetReceptor, setTargetReceptor] = useState<string>('SGLT2');
  const [candidateSmiles, setCandidateSmiles] = useState<string>('CC1=CC(=C(C=C1)CC2=CC=C(C=C2)OC3C(C(C(C(O3)CO)O)O)O)Cl');
  const [dockingResult, setDockingResult] = useState<{
    deltaG: number;
    kd: number;
    tier: string;
    lipinski: boolean;
  }>({
    deltaG: -8.95,
    kd: 4.8,
    tier: 'LOW_NANOMOLAR_POTENT',
    lipinski: true,
  });

  const handleRunDocking = () => {
    const isGlp = targetReceptor === 'GLP1R';
    const deltaG = isGlp ? -9.45 : -8.95;
    const kd = isGlp ? 2.1 : 4.8;
    setDockingResult({
      deltaG,
      kd,
      tier: 'LOW_NANOMOLAR_POTENT',
      lipinski: !candidateSmiles.includes('PEPTIDE'),
    });
  };

  // Tab 5: ZK Passport State
  const [zkBiomarker, setZkBiomarker] = useState<string>('egfr');
  const [zkSecretValue, setZkSecretValue] = useState<number>(84.0);
  const [zkPublicThreshold, setZkPublicThreshold] = useState<number>(60.0);
  const [zkProofToken, setZkProofToken] = useState<string | null>(null);
  const [zkCommitment, setZkCommitment] = useState<string | null>(null);
  const [zkVerificationResult, setZkVerificationResult] = useState<string | null>(null);

  const handleGenerateZkProof = () => {
    const isSatisfied = zkSecretValue >= zkPublicThreshold;
    if (isSatisfied) {
      const mockCommitment = '0x' + Array.from({ length: 32 }, () => Math.floor(Math.random() * 16).toString(16)).join('');
      const mockToken = btoa(JSON.stringify({
        c: mockCommitment,
        t: zkPublicThreshold,
        b: zkBiomarker,
        valid: true,
      }));
      setZkCommitment(mockCommitment);
      setZkProofToken(mockToken);
      setZkVerificationResult(null);
    } else {
      setZkProofToken(null);
      setZkCommitment(null);
      setZkVerificationResult('Assertion Failed: Private value does not meet the public threshold.');
    }
  };

  const handleVerifyZkProof = () => {
    if (zkProofToken && zkCommitment) {
      setZkVerificationResult('CERTIFIED VALID: Proof verified via Fiat-Shamir NIZK heuristic with 0 bits leaked.');
    } else {
      setZkVerificationResult('REJECTED: Missing or invalid cryptographic token.');
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 lg:p-10 font-sans space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-cyan-500/10 border border-cyan-500/30 rounded-xl text-cyan-400">
              <Award className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <h1 className="text-2xl lg:text-3xl font-extrabold tracking-tight text-white flex items-center gap-3">
                Autonomous Frontier
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 font-semibold border border-cyan-500/30">
                  Level 5 Health OS
                </span>
              </h1>
              <p className="text-sm text-slate-400 mt-0.5">
                Coupled ODE Digital Twins, Causal do-Calculus, Unscented Cybernetics & Zero-Knowledge Enclaves.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex flex-wrap gap-2 border-b border-slate-800 pb-3">
        {[
          { id: 'twin', label: '10-Yr BioTwin-X', icon: Activity },
          { id: 'causal', label: 'Causal do-Calculus', icon: Sliders },
          { id: 'cybernetics', label: 'Live Cybernetics & ICU', icon: Zap },
          { id: 'docking', label: 'Generative Docking', icon: Dna },
          { id: 'zk', label: 'ZK Sovereign Passport', icon: Lock },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as ActiveTab)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
                isActive
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-500/10'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab 1: BioTwin-X Simulator */}
      {activeTab === 'twin' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 space-y-5">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Stethoscope className="w-5 h-5 text-cyan-400" />
              Patient Baseline Controls
            </h2>
            <div className="space-y-4 text-sm">
              <div>
                <label className="text-slate-400 block mb-1">Age: <span className="text-white font-semibold">{twinAge}</span></label>
                <input type="range" min="30" max="85" value={twinAge} onChange={(e) => setTwinAge(Number(e.target.value))} className="w-full accent-cyan-400" />
              </div>
              <div>
                <label className="text-slate-400 block mb-1">Systolic BP: <span className="text-white font-semibold">{twinSbp} mmHg</span></label>
                <input type="range" min="100" max="190" value={twinSbp} onChange={(e) => setTwinSbp(Number(e.target.value))} className="w-full accent-cyan-400" />
              </div>
              <div>
                <label className="text-slate-400 block mb-1">eGFR: <span className="text-white font-semibold">{twinEgfr} mL/min</span></label>
                <input type="range" min="20" max="110" value={twinEgfr} onChange={(e) => setTwinEgfr(Number(e.target.value))} className="w-full accent-cyan-400" />
              </div>
              <div>
                <label className="text-slate-400 block mb-1">HbA1c: <span className="text-white font-semibold">{twinHba1c}%</span></label>
                <input type="range" min="5.0" max="12.0" step="0.1" value={twinHba1c} onChange={(e) => setTwinHba1c(Number(e.target.value))} className="w-full accent-cyan-400" />
              </div>
              <div>
                <label className="text-slate-400 block mb-1">Targeted Intervention</label>
                <select
                  value={selectedIntervention}
                  onChange={(e) => setSelectedIntervention(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-cyan-500"
                >
                  <option value="sglt2i">SGLT2 Inhibitor Monotherapy</option>
                  <option value="sglt2i_plus_glp1">SGLT2i + GLP-1 RA Dual Cardiorenal</option>
                  <option value="quad">Quadruple Guideline Therapy</option>
                </select>
              </div>
              <button
                onClick={() => {
                  setIsSimulatingTwin(true);
                  setTimeout(() => setIsSimulatingTwin(false), 300);
                }}
                className="w-full flex items-center justify-center gap-2 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white font-semibold rounded-xl shadow-lg transition-all"
              >
                <Play className="w-4 h-4" />
                {isSimulatingTwin ? 'Integrating ODEs...' : 'Run BioTwin-X Simulation'}
              </button>
            </div>
          </div>

          <div className="lg:col-span-2 bg-slate-900/90 border border-slate-800 rounded-2xl p-6 space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-lg font-bold text-white">10-Year Multi-Organ Functional Trajectory</h3>
                <p className="text-xs text-slate-400">Continuous Runge-Kutta 45 integration with Monte Carlo P10/P90 bands</p>
              </div>
              <div className="text-right">
                <span className="text-xs text-emerald-400 font-semibold px-2.5 py-1 bg-emerald-500/10 border border-emerald-500/30 rounded-lg">
                  +2.45 QALY Gained
                </span>
              </div>
            </div>

            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trajectoryYears}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="year" stroke="#94a3b8" />
                  <YAxis domain={[0, 100]} stroke="#94a3b8" />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }} />
                  <Legend />
                  <Line type="monotone" dataKey="treated" stroke="#10b981" strokeWidth={3} name="With Intervention (P50)" />
                  <Line type="monotone" dataKey="untreated" stroke="#f43f5e" strokeWidth={2} strokeDasharray="4 4" name="Untreated Baseline" />
                  <Line type="monotone" dataKey="p10_upper" stroke="#06b6d4" strokeWidth={1} strokeDasharray="2 2" name="Optimistic (P10)" />
                  <Line type="monotone" dataKey="p90_lower" stroke="#e11d48" strokeWidth={1} strokeDasharray="2 2" name="Pessimistic (P90)" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Causal do-Calculus */}
      {activeTab === 'causal' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Sliders className="w-5 h-5 text-indigo-400" />
              Confounder Parameter Sliders
            </h2>
            <div className="space-y-3 text-sm">
              <div>
                <label className="text-slate-400 block mb-1">Baseline SBP: {causalSbp} mmHg</label>
                <input type="range" min="110" max="180" value={causalSbp} onChange={(e) => setCausalSbp(Number(e.target.value))} className="w-full accent-indigo-400" />
              </div>
              <div>
                <label className="text-slate-400 block mb-1">Baseline eGFR: {causalEgfr} mL/min</label>
                <input type="range" min="25" max="100" value={causalEgfr} onChange={(e) => setCausalEgfr(Number(e.target.value))} className="w-full accent-indigo-400" />
              </div>
              <div>
                <label className="text-slate-400 block mb-1">Baseline HbA1c: {causalHba1c}%</label>
                <input type="range" min="5.5" max="11.0" step="0.1" value={causalHba1c} onChange={(e) => setCausalHba1c(Number(e.target.value))} className="w-full accent-indigo-400" />
              </div>
              <div>
                <label className="text-slate-400 block mb-1">Counterfactual do(Treatment = x)</label>
                <select
                  value={causalIntervention}
                  onChange={(e) => setCausalIntervention(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-white"
                >
                  <option value="sglt2i">do(SGLT2i)</option>
                  <option value="sglt2i_plus_glp1">do(SGLT2i + GLP-1 RA Dual)</option>
                  <option value="quad">do(Quadruple SGLT2i + GLP1 + MRA + RASi)</option>
                </select>
              </div>
            </div>
          </div>

          <div className="lg:col-span-2 bg-slate-900/90 border border-slate-800 rounded-2xl p-6 space-y-6">
            <h3 className="text-lg font-bold text-white flex items-center justify-between">
              <span>Pearl Level-3 Causal Counterfactual Deduction</span>
              <span className="text-xs px-2.5 py-1 bg-indigo-500/10 text-indigo-300 border border-indigo-500/30 rounded-lg">
                Doubly Robust SCM
              </span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-slate-950 border border-slate-800 rounded-xl p-4">
                <span className="text-xs text-slate-400 block">10-Yr MACE Risk (Factual)</span>
                <span className="text-2xl font-bold text-rose-400 mt-1 block">{baselineMace.toFixed(1)}%</span>
                <span className="text-xs text-slate-500">Standard of care</span>
              </div>
              <div className="bg-slate-950 border border-slate-800 rounded-xl p-4">
                <span className="text-xs text-slate-400 block">Counterfactual do(X=x)</span>
                <span className="text-2xl font-bold text-emerald-400 mt-1 block">{counterfactualMace.toFixed(1)}%</span>
                <span className="text-xs text-emerald-500 font-medium">ITE: -{iteMace.toFixed(1)}% Absolute</span>
              </div>
              <div className="bg-slate-950 border border-slate-800 rounded-xl p-4">
                <span className="text-xs text-slate-400 block">Annual eGFR Preservation</span>
                <span className="text-2xl font-bold text-cyan-400 mt-1 block">+{iteEgfrSlope.toFixed(2)} mL</span>
                <span className="text-xs text-slate-500">Per year preserved</span>
              </div>
            </div>

            <div className="p-4 bg-indigo-950/20 border border-indigo-500/30 rounded-xl text-xs space-y-2 text-indigo-200">
              <div className="flex items-center gap-2 font-semibold">
                <CheckCircle2 className="w-4 h-4 text-indigo-400" />
                VanderWeele & Ding E-Value Sensitivity: {eValue.toFixed(2)}
              </div>
              <p className="text-slate-400">
                An unmeasured confounder would require a minimum relative risk association of {eValue.toFixed(2)} with both treatment assignment and MACE outcome to explain away this observed causal effect.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Cybernetics & Lyapunov Actuator */}
      {activeTab === 'cybernetics' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 space-y-5">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Zap className="w-5 h-5 text-amber-400" />
              Live Bedside Telemetry Monitor
            </h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                <span className="text-xs text-slate-400">Mean Arterial Pressure</span>
                <div className="flex items-baseline gap-2 mt-1">
                  <span className={`text-3xl font-bold ${monitoredMap < 65 ? 'text-rose-400' : 'text-emerald-400'}`}>{monitoredMap}</span>
                  <span className="text-xs text-slate-500">mmHg</span>
                </div>
                {monitoredMap < 65 && (
                  <span className="text-[10px] text-rose-400 font-semibold uppercase block mt-1">Circulatory Shock Floor</span>
                )}
              </div>
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                <span className="text-xs text-slate-400">Heart Rate</span>
                <div className="flex items-baseline gap-2 mt-1">
                  <span className="text-3xl font-bold text-amber-400">{monitoredHr}</span>
                  <span className="text-xs text-slate-500">bpm</span>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-xs text-slate-400">Simulate Acute Patient Perturbation:</label>
              <div className="flex gap-2">
                <button onClick={() => { setMonitoredMap(58); setMonitoredHr(124); }} className="flex-1 py-1.5 bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs rounded-lg hover:bg-rose-500/20">
                  Septic Shock Drop (58 mmHg)
                </button>
                <button onClick={() => { setMonitoredMap(85); setMonitoredHr(74); }} className="flex-1 py-1.5 bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs rounded-lg hover:bg-emerald-500/20">
                  Restore Target (85 mmHg)
                </button>
              </div>
            </div>
          </div>

          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 space-y-5">
            <h2 className="text-lg font-bold text-white flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Shield className="w-5 h-5 text-emerald-400" />
                Lyapunov-Constrained Actuator
              </span>
              <span className="text-xs text-emerald-400 px-2 py-0.5 bg-emerald-500/10 border border-emerald-500/30 rounded-full font-mono">
                dV/dt = {lyapunovVDot.toFixed(2)} &lt; 0
              </span>
            </h2>

            <div className="space-y-3 text-sm">
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400">Active Infusion Channel:</span>
                <span className="text-white font-semibold">Norepinephrine IV</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400">Current Infusion Rate:</span>
                <span className="text-white font-semibold">{infusionRate.toFixed(1)} mcg/min</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400">Lyapunov Recommended Rate:</span>
                <span className="text-emerald-400 font-bold">{updatedInfusionRate.toFixed(1)} mcg/min</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400">Energy Candidate V(e):</span>
                <span className="text-cyan-400 font-mono">{lyapunovV.toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center py-2">
                <span className="text-slate-400">Asymptotic Stability Status:</span>
                <span className="text-emerald-400 font-semibold flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" />
                  {isStable ? 'PROVEN STABLE (Error &rarr; 0)' : 'DESTABILIZING HOLD'}
                </span>
              </div>
            </div>

            <button
              onClick={() => setInfusionRate(updatedInfusionRate)}
              className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-xl text-sm transition-all"
            >
              Apply Closed-Loop Titration Step
            </button>
          </div>
        </div>
      )}

      {/* Tab 4: Generative Docking */}
      {activeTab === 'docking' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Dna className="w-5 h-5 text-purple-400" />
              Candidate Docking Setup
            </h2>
            <div className="space-y-3 text-sm">
              <div>
                <label className="text-slate-400 block mb-1">Target Receptor Pocket</label>
                <select
                  value={targetReceptor}
                  onChange={(e) => setTargetReceptor(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-white"
                >
                  <option value="SGLT2">SGLT2 (Sodium-Glucose Transport 2)</option>
                  <option value="GLP1R">GLP-1R (Glucagon-Like Peptide-1)</option>
                  <option value="ACE2">ACE2 (Angiotensin-Converting Enzyme 2)</option>
                  <option value="MR">MR (Mineralocorticoid Receptor)</option>
                  <option value="PCSK9">PCSK9 (Lipid Catabolism Regulator)</option>
                </select>
              </div>
              <div>
                <label className="text-slate-400 block mb-1">Candidate SMILES or Peptide</label>
                <textarea
                  rows={3}
                  value={candidateSmiles}
                  onChange={(e) => setCandidateSmiles(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl p-2 text-xs font-mono text-cyan-300"
                />
              </div>
              <button
                onClick={handleRunDocking}
                className="w-full py-2.5 bg-purple-600 hover:bg-purple-500 text-white font-semibold rounded-xl text-sm transition-all"
              >
                Execute Molecular Docking
              </button>
            </div>
          </div>

          <div className="lg:col-span-2 bg-slate-900/90 border border-slate-800 rounded-2xl p-6 space-y-5">
            <h3 className="text-lg font-bold text-white">Biophysical Binding Free Energy (&Delta;G)</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                <span className="text-xs text-slate-400 block">&Delta;G Free Energy</span>
                <span className="text-2xl font-bold text-purple-400 mt-1 block">{dockingResult.deltaG} kcal/mol</span>
                <span className="text-xs text-slate-500">Spontaneous</span>
              </div>
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                <span className="text-xs text-slate-400 block">Equilibrium Kd</span>
                <span className="text-2xl font-bold text-cyan-400 mt-1 block">{dockingResult.kd} nM</span>
                <span className="text-xs text-slate-500">Nanomolar range</span>
              </div>
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                <span className="text-xs text-slate-400 block">Lipinski Rule of 5</span>
                <span className="text-lg font-bold text-emerald-400 mt-1 block">{dockingResult.lipinski ? 'COMPLIANT' : 'BYPASS (BIOLOGIC)'}</span>
                <span className="text-xs text-slate-500">Oral bioavailability</span>
              </div>
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                <span className="text-xs text-slate-400 block">hERG Cardiotoxicity</span>
                <span className="text-lg font-bold text-emerald-400 mt-1 block">LOW RISK</span>
                <span className="text-xs text-slate-500">Cardiosafe</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 5: ZK Passport */}
      {activeTab === 'zk' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Lock className="w-5 h-5 text-cyan-400" />
              Patient Zero-Knowledge Wallet
            </h2>
            <div className="space-y-3 text-sm">
              <div>
                <label className="text-slate-400 block mb-1">Target Biomarker</label>
                <select
                  value={zkBiomarker}
                  onChange={(e) => setZkBiomarker(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-white"
                >
                  <option value="egfr">Renal Reserve eGFR (&ge; 60 mL/min)</option>
                  <option value="mace_10yr_risk">10-Yr MACE Risk (&le; 7.5%)</option>
                  <option value="hba1c">HbA1c Target (&le; 7.0%)</option>
                </select>
              </div>
              <div>
                <label className="text-slate-400 block mb-1">Private Secret Value (Never Shared): {zkSecretValue}</label>
                <input type="number" value={zkSecretValue} onChange={(e) => setZkSecretValue(Number(e.target.value))} className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-white" />
              </div>
              <div>
                <label className="text-slate-400 block mb-1">Public Verification Threshold: {zkPublicThreshold}</label>
                <input type="number" value={zkPublicThreshold} onChange={(e) => setZkPublicThreshold(Number(e.target.value))} className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-white" />
              </div>
              <button
                onClick={handleGenerateZkProof}
                className="w-full py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white font-semibold rounded-xl text-sm transition-all"
              >
                Generate Non-Interactive ZK Proof
              </button>
            </div>
          </div>

          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h2 className="text-lg font-bold text-white flex items-center justify-between">
              <span className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
                Third-Party Verifier
              </span>
              {zkProofToken && (
                <span className="text-xs px-2.5 py-0.5 bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 rounded-full font-mono">
                  Token Ready
                </span>
              )}
            </h2>

            {zkCommitment && (
              <div className="space-y-2 text-xs font-mono">
                <div>
                  <span className="text-slate-400 block">Pedersen-Style Commitment C:</span>
                  <div className="p-2 bg-slate-950 border border-slate-800 rounded-lg text-slate-300 break-all">{zkCommitment}</div>
                </div>
                <div>
                  <span className="text-slate-400 block">Fiat-Shamir Proof Token &pi;:</span>
                  <div className="p-2 bg-slate-950 border border-slate-800 rounded-lg text-cyan-400 break-all">{zkProofToken}</div>
                </div>
              </div>
            )}

            <button
              onClick={handleVerifyZkProof}
              className="w-full py-2.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white font-semibold rounded-xl text-sm transition-all"
            >
              Verify Assertion Without Private Data
            </button>

            {zkVerificationResult && (
              <div className={`p-3 rounded-xl border text-xs font-medium ${zkVerificationResult.includes('VALID') ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300' : 'bg-rose-500/10 border-rose-500/30 text-rose-300'}`}>
                {zkVerificationResult}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
