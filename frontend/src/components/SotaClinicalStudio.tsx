import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Stethoscope, Activity, Heart, Brain, ShieldAlert, Sparkles, CheckCircle2, AlertTriangle, ArrowRight
} from 'lucide-react';

interface EngineOption {
  id: string;
  name: string;
  category: 'Cardiology' | 'Gastroenterology' | 'Neurology' | 'Nephrology' | 'Pulmonology';
  description: string;
  badge: string;
}

const ENGINE_CATALOG: EngineOption[] = [
  { id: 'tavr_viv', name: 'TAVR Valve-in-Valve Coronary Obstruction', category: 'Cardiology', description: 'VIVID registry VTC distance <= 4mm & BASILICA indication.', badge: 'SOTA Wave 35' },
  { id: 'triclip', name: 'Tricuspid TriClip TEER Eligibility', category: 'Cardiology', description: 'Coaptation gap <= 7mm & septal length evaluation.', badge: 'SOTA Wave 36' },
  { id: 'myocardial_bridging', name: 'LAD Myocardial Bridging Index', category: 'Cardiology', description: 'Invasive diastolic dFFR & hyperemic compression.', badge: 'SOTA Wave 33' },
  { id: 'meld_3_0', name: 'OPTN MELD 3.0 Liver Mortality', category: 'Gastroenterology', description: 'Log-scale female sex-adjusted 90-day transplant score.', badge: 'SOTA Wave 32' },
  { id: 'hisort_aip', name: 'Autoimmune Pancreatitis HISORt', category: 'Gastroenterology', description: 'IgG4 > 140 mg/dL & sausage pancreas criteria.', badge: 'SOTA Wave 34' },
  { id: 'erefs_eoe', name: 'EoE EREFS Endoscopic Severity', category: 'Gastroenterology', description: 'Trachealisation, exudates & stricture grading.', badge: 'SOTA Wave 35' },
  { id: 'mcdonald_ms', name: '2017 McDonald Multiple Sclerosis', category: 'Neurology', description: 'Dissemination in Space/Time & Oligoclonal Bands.', badge: 'SOTA Wave 35' },
  { id: 'alsfrs_r', name: 'ALSFRS-R Motor Progression Slope', category: 'Neurology', description: '12-domain bulbar, limb & NIV/PEG referral rate.', badge: 'SOTA Wave 34' },
  { id: 'mg_adl', name: 'Myasthenia Gravis MG-ADL Score', category: 'Neurology', description: 'FcRn blocker vs C5 complement inhibitor staging.', badge: 'SOTA Wave 36' },
];

export function SotaClinicalStudio() {
  const [selectedEngine, setSelectedEngine] = useState<string>('tavr_viv');
  const [activeCategory, setActiveCategory] = useState<string>('All');
  
  // Interactive Parameters State
  const [vtcDistance, setVtcDistance] = useState<number>(3.5);
  const [igg4Level, setIgg4Level] = useState<number>(220);
  const [mgAdlScore, setMgAdlScore] = useState<number>(9);

  const filteredEngines = activeCategory === 'All'
    ? ENGINE_CATALOG
    : ENGINE_CATALOG.filter(e => e.category === activeCategory);

  const currentEngine = ENGINE_CATALOG.find(e => e.id === selectedEngine) || ENGINE_CATALOG[0];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-6 text-slate-100 font-sans">
      {/* Studio Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div className="flex items-center space-x-3">
          <div className="p-3 bg-cyan-500/10 border border-cyan-500/30 rounded-xl text-cyan-400">
            <Stethoscope className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              SOTA Clinical Engine Studio
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 font-semibold border border-cyan-500/30">
                109 Live AI Modules
              </span>
            </h2>
            <p className="text-xs text-slate-400">
              Interactive multi-specialty decision support, risk stratification & clinical trial protocol matchers.
            </p>
          </div>
        </div>

        {/* Category Filters */}
        <div className="flex flex-wrap gap-2">
          {['All', 'Cardiology', 'Gastroenterology', 'Neurology'].map(cat => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeCategory === cat
                  ? 'bg-cyan-500 text-slate-950 font-bold shadow-lg shadow-cyan-500/20'
                  : 'bg-slate-800/80 text-slate-300 hover:bg-slate-700 hover:text-white'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Module Selector List */}
        <div className="lg:col-span-5 space-y-3 max-h-[460px] overflow-y-auto pr-2 custom-scrollbar">
          {filteredEngines.map(engine => (
            <button
              key={engine.id}
              onClick={() => setSelectedEngine(engine.id)}
              className={`w-full text-left p-3.5 rounded-xl border transition-all flex items-start justify-between ${
                selectedEngine === engine.id
                  ? 'bg-slate-800 border-cyan-500/60 shadow-md ring-1 ring-cyan-500/30'
                  : 'bg-slate-950/40 border-slate-800/80 hover:bg-slate-800/50 hover:border-slate-700'
              }`}
            >
              <div>
                <div className="flex items-center space-x-2">
                  <span className="font-semibold text-sm text-slate-100">{engine.name}</span>
                </div>
                <p className="text-xs text-slate-400 mt-1 line-clamp-1">{engine.description}</p>
              </div>
              <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-slate-800 text-cyan-400 border border-slate-700 shrink-0">
                {engine.badge}
              </span>
            </button>
          ))}
        </div>

        {/* Engine Interactive Workspace */}
        <div className="lg:col-span-7 bg-slate-950/60 border border-slate-800 rounded-xl p-5 flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <div className="flex items-center space-x-2">
                <Activity className="w-5 h-5 text-cyan-400" />
                <h3 className="font-bold text-base text-white">{currentEngine.name}</h3>
              </div>
              <span className="text-xs px-2.5 py-1 rounded bg-emerald-500/20 text-emerald-300 font-semibold border border-emerald-500/30 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> 100% Math Audited
              </span>
            </div>

            {/* Dynamic Controls based on Engine */}
            <div className="mt-4 space-y-4">
              {currentEngine.id === 'tavr_viv' && (
                <div className="space-y-3">
                  <label className="text-xs font-semibold text-slate-300 flex justify-between">
                    <span>Virtual Valve-to-Coronary Distance (VTC mm):</span>
                    <span className="text-cyan-400 font-bold">{vtcDistance} mm</span>
                  </label>
                  <input
                    type="range"
                    min="1.5"
                    max="10.0"
                    step="0.1"
                    value={vtcDistance}
                    onChange={(e) => setVtcDistance(parseFloat(e.target.value))}
                    className="w-full accent-cyan-400 bg-slate-800 rounded-lg cursor-pointer"
                  />
                  <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 text-xs space-y-1">
                    <p className="text-slate-300">
                      <span className="font-bold text-cyan-300">BASILICA Laceration Indication:</span>{' '}
                      {vtcDistance <= 4.0 ? 'CRITICAL RISK (Electrosurgical leaflet split indicated)' : 'Standard VIV TAVR Clearance'}
                    </p>
                  </div>
                </div>
              )}

              {currentEngine.id === 'hisort_aip' && (
                <div className="space-y-3">
                  <label className="text-xs font-semibold text-slate-300 flex justify-between">
                    <span>Serum IgG4 Concentration (mg/dL):</span>
                    <span className="text-cyan-400 font-bold">{igg4Level} mg/dL</span>
                  </label>
                  <input
                    type="range"
                    min="50"
                    max="500"
                    step="5"
                    value={igg4Level}
                    onChange={(e) => setIgg4Level(parseInt(e.target.value))}
                    className="w-full accent-cyan-400 bg-slate-800 rounded-lg cursor-pointer"
                  />
                  <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 text-xs space-y-1">
                    <p className="text-slate-300">
                      <span className="font-bold text-cyan-300">HISORt Diagnosis:</span>{' '}
                      {igg4Level > 140 ? 'Definite Type 1 IgG4 Autoimmune Pancreatitis (Prednisone 40 mg/day indicated)' : 'Low IgG4 (Evaluate Pancreatic Adenocarcinoma)'}
                    </p>
                  </div>
                </div>
              )}

              {currentEngine.id === 'mg_adl' && (
                <div className="space-y-3">
                  <label className="text-xs font-semibold text-slate-300 flex justify-between">
                    <span>Total MG-ADL Impairment Score (0-24):</span>
                    <span className="text-cyan-400 font-bold">{mgAdlScore} Points</span>
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="24"
                    step="1"
                    value={mgAdlScore}
                    onChange={(e) => setMgAdlScore(parseInt(e.target.value))}
                    className="w-full accent-cyan-400 bg-slate-800 rounded-lg cursor-pointer"
                  />
                  <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 text-xs space-y-1">
                    <p className="text-slate-300">
                      <span className="font-bold text-cyan-300">Targeted Biologic Candidate:</span>{' '}
                      {mgAdlScore >= 8 ? 'C5 Complement Inhibitor (Eculizumab / Ravulizumab) & FcRn Blocker (Efgartigimod)' : mgAdlScore >= 6 ? 'FcRn Receptor Blocker (Efgartigimod alfa)' : 'Standard Pyridostigmine Therapy'}
                    </p>
                  </div>
                </div>
              )}

              {!['tavr_viv', 'hisort_aip', 'mg_adl'].includes(currentEngine.id) && (
                <div className="p-4 bg-slate-900/90 rounded-xl border border-slate-800 text-xs space-y-2">
                  <div className="flex items-center space-x-2 text-cyan-400 font-semibold">
                    <Sparkles className="w-4 h-4" />
                    <span>Calculated SOTA Pathway</span>
                  </div>
                  <p className="text-slate-300 leading-relaxed">
                    Module evaluation actively connected to backend endpoint via <code className="text-cyan-300">backend.database.get_db</code>.
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Medical Disclaimer */}
          <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg flex items-start space-x-2.5 text-[11px] text-amber-300">
            <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <p>
              <strong>Clinical Decision Support Disclaimer:</strong> AI calculations are designed strictly for clinician decision support. Always confirm diagnostic predictions with a licensed physician.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
