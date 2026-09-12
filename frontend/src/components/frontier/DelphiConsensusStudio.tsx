import React, { useState } from 'react';
import { Users, AlertTriangle, ShieldCheck, CheckCircle2, Play, RefreshCw, Activity, HeartPulse } from 'lucide-react';

interface SpecialistOpinion {
  role: string;
  specialist: string;
  color: string;
  recommendation: string;
  concerns: string[];
}

export function DelphiConsensusStudio() {
  const [scenario, setScenario] = useState<string>('chest_pain');
  const [isDeliberating, setIsDeliberating] = useState<boolean>(false);
  const [delphiRounds, setDelphiRounds] = useState<number>(2);
  const [kendallW, setKendallW] = useState<number>(0.84);
  const [hasDeliberated, setHasDeliberated] = useState<boolean>(true);

  const scenarioData: Record<string, { title: string; patient: string; opinions: SpecialistOpinion[]; adversarialWarning: string }> = {
    chest_pain: {
      title: 'Atypical Chest Pain & Sinus Tachycardia',
      patient: '58M, SBP 88/54, HR 118 bpm, Troponin T 0.08 ng/mL, sudden retrosternal tearing sensation.',
      opinions: [
        {
          role: 'Internist',
          specialist: 'Internal Medicine',
          color: 'text-sky-400 border-sky-500/30 bg-sky-500/10',
          recommendation: 'Acute Coronary Syndrome (NSTEMI) high probability. Initiate dual antiplatelet therapy & heparin.',
          concerns: ['Troponin mildly elevated', 'T-wave flattening in V4-V6'],
        },
        {
          role: 'Pharmacologist',
          specialist: 'Clinical Pharmacy',
          color: 'text-amber-400 border-amber-500/30 bg-amber-500/10',
          recommendation: 'Hold full-dose anticoagulation pending vascular imaging. Review CYP2C19 genotype before Plavix.',
          concerns: ['Renal clearance 42 mL/min', 'Bleeding risk score elevated'],
        },
        {
          role: 'Intensivist',
          specialist: 'Critical Care / ICU',
          color: 'text-purple-400 border-purple-500/30 bg-purple-500/10',
          recommendation: 'Cardiogenic shock risk. MAP 65 floor violated. Norepinephrine infusion line on standby.',
          concerns: ['Lactate 2.8 mmol/L', 'Orthostatic pulse pressure narrowing'],
        },
        {
          role: 'Adversarial Skeptic',
          specialist: "Devil's Advocate Falsifier",
          color: 'text-rose-400 border-rose-500/30 bg-rose-500/10',
          recommendation: 'CRITICAL COGNITIVE BIAS ALERT: Anchoring on ACS without falsifying Acute Aortic Dissection Stanford Type A. Retrosternal tearing pain + BP disparity in extremities mandates emergent bedside TTE and CT Aortogram before antithrombotic therapy!',
          concerns: ['Anchoring bias on troponin', 'Fatal risk if heparinized during dissection'],
        },
      ],
      adversarialWarning: 'Adversarial Skeptic successfully intercepted premature closure: CTA Aortogram prioritized over cath lab.',
    },
    sepsis: {
      title: 'Septic Shock vs Vasoplegic Collapse',
      patient: '71F, Temp 38.9C, WBC 18.2k, Lactate 3.4, SBP 82/46 on 30 mL/kg crystalloids.',
      opinions: [
        {
          role: 'Internist',
          specialist: 'Infectious Disease',
          color: 'text-sky-400 border-sky-500/30 bg-sky-500/10',
          recommendation: 'Refractory Septic Shock secondary to pyelonephritis. Broad spectrum Vancomycin + Cefepime.',
          concerns: ['Urine dipstick positive for nitrites', 'Procalcitonin 8.2 ng/mL'],
        },
        {
          role: 'Pharmacologist',
          specialist: 'Clinical Pharmacy',
          color: 'text-amber-400 border-amber-500/30 bg-amber-500/10',
          recommendation: 'Vancomycin trough target 15-20. Dose adjust Cefepime for eGFR 28 to prevent neurotoxicity.',
          concerns: ['Renal accumulation', 'Concurrent loop diuretic'],
        },
        {
          role: 'Intensivist',
          specialist: 'Critical Care / ICU',
          color: 'text-purple-400 border-purple-500/30 bg-purple-500/10',
          recommendation: 'Dynamic arterial line monitoring. Initiate Vasopressin 0.03 U/min as secondary agent.',
          concerns: ['Fluid responsiveness exhausted (SVV < 10%)', 'Risk of pulmonary edema'],
        },
        {
          role: 'Adversarial Skeptic',
          specialist: "Devil's Advocate Falsifier",
          color: 'text-rose-400 border-rose-500/30 bg-rose-500/10',
          recommendation: 'FALSIFICATION CHECK: Ensure adrenal insufficiency crisis (Addisonian shock) is ruled out. Request immediate cortisol check and stress-dose hydrocortisone 100mg IV if refractory to high-dose vasopressors.',
          concerns: ['Steroid withdrawal history', 'Relative refractory vasoplegia'],
        },
      ],
      adversarialWarning: 'Adversarial Skeptic added hydrocortisone contingency; Kendall agreement reached at W = 0.88.',
    },
  };

  const activeScenario = scenarioData[scenario] || scenarioData.chest_pain;

  const handleRunDeliberation = () => {
    setIsDeliberating(true);
    setTimeout(() => {
      setIsDeliberating(false);
      setHasDeliberated(true);
      setDelphiRounds(2);
      setKendallW(0.86);
    }, 400);
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 text-xs font-semibold uppercase tracking-wider mb-1">
            <Users className="w-4 h-4" />
            Level 8 Multi-Agent Clinical Consensus
          </div>
          <h2 className="text-xl font-bold text-white">Delphi Swarm with Adversarial Falsification</h2>
          <p className="text-sm text-slate-400 mt-1">
            Simulates specialist clinical deliberation with an active Adversarial Skeptic detecting cognitive bias (anchoring, premature closure).
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={scenario}
            onChange={(e) => setScenario(e.target.value)}
            className="bg-slate-950 border border-slate-700 text-slate-200 text-sm rounded-xl px-3 py-2"
          >
            <option value="chest_pain">Case 1: Chest Pain & Tachycardia</option>
            <option value="sepsis">Case 2: Septic Shock vs Vasoplegia</option>
          </select>
          <button
            onClick={handleRunDeliberation}
            disabled={isDeliberating}
            className="flex items-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white font-semibold rounded-xl text-sm transition-all"
          >
            {isDeliberating ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            Execute Delphi Rounds
          </button>
        </div>
      </div>

      {/* Patient Synopsis */}
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-4 flex items-center justify-between">
        <div>
          <span className="text-xs text-slate-400 block font-medium">Patient Presentation:</span>
          <span className="text-sm font-semibold text-white">{activeScenario.patient}</span>
        </div>
        <div className="flex items-center gap-4 text-xs font-mono">
          <div className="text-center">
            <span className="text-slate-400 block">Delphi Rounds</span>
            <span className="text-cyan-400 font-bold text-base">{delphiRounds}</span>
          </div>
          <div className="text-center">
            <span className="text-slate-400 block">Kendall&apos;s W</span>
            <span className="text-emerald-400 font-bold text-base">{kendallW}</span>
          </div>
        </div>
      </div>

      {/* 4 Specialized Agent Panes */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {activeScenario.opinions.map((op, idx) => (
          <div key={idx} className={`p-5 rounded-2xl border ${op.color} backdrop-blur-sm space-y-3`}>
            <div className="flex items-center justify-between">
              <span className="font-bold text-sm text-white flex items-center gap-2">
                <HeartPulse className="w-4 h-4" />
                {op.role}
              </span>
              <span className="text-xs px-2 py-0.5 rounded-full border border-current font-mono opacity-80">
                {op.specialist}
              </span>
            </div>
            <p className="text-xs leading-relaxed text-slate-200 font-medium">
              {op.recommendation}
            </p>
            <div className="pt-2 border-t border-slate-800/60 flex flex-wrap gap-1.5">
              {op.concerns.map((c, i) => (
                <span key={i} className="text-[10px] px-2 py-0.5 bg-slate-950/60 rounded text-slate-300 font-mono">
                  • {c}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Consensus & Adversarial Falsification Result */}
      {hasDeliberated && (
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 space-y-4">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            Delphi Consensus & Falsification Summary
          </h3>
          <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl space-y-3">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
              <div className="text-xs text-slate-300 leading-relaxed">
                <strong className="text-amber-300 block mb-1">Adversarial Falsification Gate:</strong>
                {activeScenario.adversarialWarning}
              </div>
            </div>
            <div className="flex items-start gap-3 pt-3 border-t border-slate-800/80">
              <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />
              <div className="text-xs text-slate-300 leading-relaxed">
                <strong className="text-emerald-300 block mb-1">Converged Action Plan (Kendall W = {kendallW}):</strong>
                1. Immediate Bedside POCUS for aortic root & pericardial effusion.<br />
                2. STAT non-contrast CT aortogram prior to therapeutic anticoagulation.<br />
                3. Invasive arterial blood pressure line placement; hold vasopressors unless MAP &lt; 65 mmHg.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
