/**
 * AIAgentsPanel – AI Agents Control Suite panel for the System Administration page.
 * Provides a highly interactive dashboard to trigger and inspect SOTA Clinical AI Agents.
 */
import React, { useState } from "react";
import { 
  Cpu, FileText, ShieldAlert, Sparkles, Terminal, Activity,
  Users, RefreshCw, Layers, PhoneCall, AlertTriangle, ShieldCheck, Heart, Play
} from "lucide-react";
import { 
  triggerBillingAudit,
  triggerMafBillingAudit,
  triggerMafHandoffAudit,
  triggerLanggraphTriage,
  triggerDischargeSummary,
  triggerNursingHandoff,
  triggerSecurityPatch,
  triggerAutoFix,
  triggerAutoCall,
  triggerWellnessAdvisory
} from "@/lib/api";

type AgentKey = "billing" | "discharge" | "nursing" | "patch" | "fix" | "call";

interface AgentConfig {
  key: AgentKey;
  name: string;
  role: string;
  icon: React.ElementType;
  description: string;
  defaultInputs: Record<string, string>;
  examples: { label: string; inputs: Record<string, string> }[];
}

const AGENTS_CONFIG: AgentConfig[] = [
  {
    key: "billing",
    name: "Clinical Billing Auditor",
    role: "ICD-10/CPT Compliance",
    icon: FileText,
    description: "Audits clinical SOAP notes for billing integrity, assigns standard ICD-10/CPT codes, and predicts claims denial risks with mitigation reasons.",
    defaultInputs: {
      soap_note: "Subjective: Patient reports sudden onset chest pain radiating to left arm. Associated with mild dyspnea and diaphoresis.\nObjective: BP 142/90, HR 88, O2 Sat 96%. ECG shows sinus rhythm with no acute ST changes.\nAssessment: Chest pain, suspected angina pectoris. Underlying history of Type 2 Diabetes.\nPlan: Order troponin enzymes. Refer to cardiologist.",
      mode: "sota"
    },
    examples: [
      {
        label: "Angina SOAP Note",
        inputs: {
          soap_note: "Subjective: Patient reports sudden onset chest pain radiating to left arm. Associated with mild dyspnea and diaphoresis.\nObjective: BP 142/90, HR 88, O2 Sat 96%. ECG shows sinus rhythm with no acute ST changes.\nAssessment: Chest pain, suspected angina pectoris. Underlying history of Type 2 Diabetes.\nPlan: Order troponin enzymes. Refer to cardiologist.",
          mode: "sota"
        }
      },
      {
        label: "Diabetic Foot SOAP Note (MAF)",
        inputs: {
          soap_note: "Subjective: Patient presents for checkup of diabetic foot ulcer. Reports mild localized pain.\nObjective: Ulcer on right metatarsal head, 2cm, clean margins, no active drainage. Foot pulse intact.\nAssessment: Diabetic foot ulcer, stage 2. Controlled type 2 diabetes mellitus.\nPlan: Local debridement. Sterile dressing change. Patient education on glucose tracking.",
          mode: "maf"
        }
      },
      {
        label: "Multi-Agent Handoff SOAP Note (MAF)",
        inputs: {
          soap_note: "Subjective: Elderly patient reports severe dyspnea, dry cough, and mild leg swelling.\nObjective: Rales in bilateral bases, pitting edema in ankles. O2 Sat 91% on room air.\nAssessment: Acute exacerbation of congestive heart failure.\nPlan: Administer furosemide. Monitor vitals. Patient safety/compliance watch.",
          mode: "maf_handoff"
        }
      }
    ]
  },
  {
    key: "discharge",
    name: "Discharge Coordinator",
    role: "Transition of Care Plan",
    icon: Layers,
    description: "Aggregates clinical records, diagnostics, and vitals to generate a transition-of-care summary, medication plans, and instructions tailored for patient compliance.",
    defaultInputs: {
      patient_id: "1"
    },
    examples: [
      {
        label: "Patient #1 (Default)",
        inputs: { patient_id: "1" }
      },
      {
        label: "Patient #2",
        inputs: { patient_id: "2" }
      }
    ]
  },
  {
    key: "nursing",
    name: "Ward Shift Nurse",
    role: "Shift Handoff & Tasks",
    icon: Users,
    description: "Generates nurse handover cards, vital trend summaries, fall risk warnings, and patient task lists to optimize clinical safety during shift changes.",
    defaultInputs: {
      patient_id: "1"
    },
    examples: [
      {
        label: "Patient #1 (Default)",
        inputs: { patient_id: "1" }
      },
      {
        label: "Patient #2",
        inputs: { patient_id: "2" }
      }
    ]
  },
  {
    key: "patch",
    name: "Security Auto-Patcher",
    role: "Postures & Dependency virtual patches",
    icon: ShieldAlert,
    description: "Analyzes system requirements and active environment configurations to detect vulnerabilities and automatically suggest hotpatch directives.",
    defaultInputs: {
      dependencies: "fastapi>=0.110.0, python-jose>=3.3.0, passlib[bcrypt]>=1.7.4, pyjwt>=2.8.0, cryptography>=41.0.0",
      env_config: "SECRET_KEY=default_fallback_secret, ALLOWED_HOSTS=*, DEBUG=True, CORS_ORIGIN=*"
    },
    examples: [
      {
        label: "Vulnerable Default Env Stack",
        inputs: {
          dependencies: "fastapi>=0.110.0, python-jose>=3.3.0, passlib[bcrypt]>=1.7.4, pyjwt>=2.8.0, cryptography>=41.0.0",
          env_config: "SECRET_KEY=default_fallback_secret, ALLOWED_HOSTS=*, DEBUG=True, CORS_ORIGIN=*"
        }
      },
      {
        label: "Hardened Enterprise Config",
        inputs: {
          dependencies: "fastapi>=0.136.3, python-jose[cryptography]>=3.5.0, bcrypt==3.2.0, pyjwt>=2.13.0",
          env_config: "SECRET_KEY=rsa_private_key_production_vault, ALLOWED_HOSTS=127.0.0.1,clinic.com, DEBUG=False"
        }
      }
    ]
  },
  {
    key: "fix",
    name: "Self-Healing Recoverer",
    role: "Database & Cache Recovery",
    icon: RefreshCw,
    description: "Inspects system exceptions and host health signals to diagnose issues and trigger programmatic self-healing actions (such as cache clearing or DB vacuuming).",
    defaultInputs: {
      error_logs: "OperationalError: database is locked; too many active connections in pool",
      health_signals: "CPU: 91% (Spike), Memory: 84%, Active DB Connections: 95/100, SQLite Lock: True"
    },
    examples: [
      {
        label: "SQLite DB Lock Crash",
        inputs: {
          error_logs: "OperationalError: database is locked; too many active connections in pool",
          health_signals: "CPU: 91% (Spike), Memory: 84%, Active DB Connections: 95/100, SQLite Lock: True"
        }
      },
      {
        label: "Redis Cache Out of Memory",
        inputs: {
          error_logs: "RedisError: OOM command not allowed when used memory > 'maxmemory'",
          health_signals: "CPU: 45%, Memory: 96% (Critical), Cache Memory: 512MB/512MB"
        }
      }
    ]
  },
  {
    key: "call",
    name: "Telephony Coordinator",
    role: "Emergency Alarm Routing",
    icon: PhoneCall,
    description: "Handles critical telemetry alarms, matches the on-call specialist directory, and generates synthesized doctor call scripts for automated emergency response.",
    defaultInputs: {
      alert_details: "CRITICAL VITAL ALARM - Patient #1 (John Doe) telemetry shows severe Ventricular Tachycardia (HR: 172 bpm, Systolic BP: 88 mmHg). Immediate intervention required.",
      staff_directory: "Dr. Sarah Jenkins (Cardiologist, On-Call, +1-555-0199), Dr. Mark Patel (Endocrinologist, +1-555-0188), Nursing Desk Station 2 (+1-555-0102)"
    },
    examples: [
      {
        label: "Cardiac Arrhythmia Emergency",
        inputs: {
          alert_details: "CRITICAL VITAL ALARM - Patient #1 (John Doe) telemetry shows severe Ventricular Tachycardia (HR: 172 bpm, Systolic BP: 88 mmHg). Immediate intervention required.",
          staff_directory: "Dr. Sarah Jenkins (Cardiologist, On-Call, +1-555-0199), Dr. Mark Patel (Endocrinologist, +1-555-0188), Nursing Desk Station 2 (+1-555-0102)"
        }
      },
      {
        label: "Severe Hypoglycemic Triage",
        inputs: {
          alert_details: "WARNING ALARM - Patient #3 (Diabetes Panel) reports blood glucose drop to 42 mg/dL. Confused mental state reported.",
          staff_directory: "Dr. Mark Patel (Endocrinologist, On-Call, +1-555-0188), ER Triage Team (+1-555-0110)"
        }
      }
    ]
  }
];

export default function AIAgentsPanel() {
  const [activeAgentKey, setActiveAgentKey] = useState<AgentKey>("billing");
  const [inputs, setInputs] = useState<Record<string, string>>({
    ...AGENTS_CONFIG[0].defaultInputs
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const activeAgent = AGENTS_CONFIG.find(a => a.key === activeAgentKey)!;

  const handleAgentChange = (key: AgentKey) => {
    setActiveAgentKey(key);
    const config = AGENTS_CONFIG.find(a => a.key === key)!;
    setInputs({ ...config.defaultInputs });
    setResult(null);
    setError(null);
  };

  const handleInputChange = (field: string, value: string) => {
    setInputs(prev => ({ ...prev, [field]: value }));
  };

  const loadExample = (exInputs: Record<string, string>) => {
    setInputs({ ...exInputs });
    setResult(null);
    setError(null);
  };

  const triggerAgent = async () => {
    setLoading(true);
    setResult(null);
    setError(null);

    try {
      let res: any;
      if (activeAgentKey === "billing") {
        const mode = inputs.mode || "sota";
        if (mode === "maf") {
          res = await triggerMafBillingAudit(inputs.soap_note);
        } else if (mode === "maf_handoff") {
          res = await triggerMafHandoffAudit(inputs.soap_note);
        } else {
          res = await triggerBillingAudit(inputs.soap_note);
        }
      } else if (activeAgentKey === "discharge") {
        res = await triggerDischargeSummary(Number(inputs.patient_id || 1));
      } else if (activeAgentKey === "nursing") {
        res = await triggerNursingHandoff(Number(inputs.patient_id || 1));
      } else if (activeAgentKey === "patch") {
        res = await triggerSecurityPatch(inputs.dependencies, inputs.env_config);
      } else if (activeAgentKey === "fix") {
        res = await triggerAutoFix(inputs.error_logs, inputs.health_signals);
      } else if (activeAgentKey === "call") {
        res = await triggerAutoCall(inputs.alert_details, inputs.staff_directory);
      }

      setResult(res);
    } catch (err: any) {
      setError(err.message || "Execution failed. Please make sure the backend is active.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="panel overflow-hidden">
      
      {/* Banner / Header */}
      <div className="p-4 border-b border-[var(--border)] flex justify-between items-center bg-[rgba(15,15,17,0.5)]">
        <div>
          <h2 className="section-title flex items-center gap-2">
            <Cpu size={16} className="text-[var(--accent)]" /> Autonomous AI Agents Control Suite
          </h2>
          <p className="text-[10px] text-[var(--text-dim)] font-mono uppercase mt-0.5">
            Trigger, monitor, and audit on-premises clinical AI agent workflows
          </p>
        </div>
      </div>

      {/* Main Layout Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-0">
        
        {/* Sidebar: Agent Selector */}
        <div className="lg:col-span-4 border-r border-[var(--border)] bg-black/20">
          <nav className="p-2 space-y-1" aria-label="Clinical AI Agents list">
            {AGENTS_CONFIG.map((agent) => {
              const Icon = agent.icon;
              const isSelected = activeAgentKey === agent.key;
              return (
                <button
                  key={agent.key}
                  onClick={() => handleAgentChange(agent.key)}
                  className={`w-full flex items-center gap-3.5 px-3 py-3 rounded text-left transition-colors cursor-pointer
                    ${isSelected 
                      ? "bg-[rgba(14,165,233,0.06)] border border-[var(--accent)]/30 text-[var(--accent)]" 
                      : "hover:bg-white/[0.015] border border-transparent text-[var(--text-secondary)]"
                    }
                  `}
                >
                  <div className={`p-2 rounded ${isSelected ? "bg-[var(--accent)]/10 text-[var(--accent)]" : "bg-white/5 text-[var(--text-dim)]"}`}>
                    <Icon size={16} />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold uppercase tracking-wide">{agent.name}</h3>
                    <p className="text-[9px] text-[var(--text-dim)] font-mono uppercase tracking-wider mt-0.5">{agent.role}</p>
                  </div>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Input & Execution Workspace */}
        <div className="lg:col-span-8 p-6 space-y-6 bg-black/10 flex flex-col justify-between">
          
          <div className="space-y-6">
            
            {/* Active Agent Info */}
            <div className="border-l-2 border-[var(--accent)] pl-4 py-0.5">
              <h3 className="text-sm font-bold uppercase text-[var(--text-primary)] tracking-wider">
                {activeAgent.name}
              </h3>
              <p className="text-xs text-[var(--text-secondary)] leading-relaxed mt-1 font-mono uppercase">
                {activeAgent.description}
              </p>
            </div>

            {/* Quick Examples Loader */}
            {activeAgent.examples.length > 0 && (
              <div className="space-y-2">
                <span className="text-[10px] text-[var(--text-dim)] font-mono uppercase tracking-wider block">
                  Quick Load Demo Cases:
                </span>
                <div className="flex flex-wrap gap-2">
                  {activeAgent.examples.map((ex, idx) => (
                    <button
                      key={idx}
                      onClick={() => loadExample(ex.inputs)}
                      className="px-2.5 py-1 rounded bg-white/5 border border-white/[0.04] text-[10px] font-mono text-[var(--text-secondary)] hover:bg-white/10 hover:border-white/10 hover:text-white transition-colors cursor-pointer"
                    >
                      {ex.label}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Dynamic Inputs Builder */}
            <div className="space-y-4">
              
              {/* Billing: SOAP Note text area */}
              {activeAgentKey === "billing" && (
                <>
                  <div className="space-y-1">
                    <label htmlFor="soap_note" className="text-[10px] text-[var(--text-dim)] font-mono uppercase tracking-wider">
                      SOAP Clinical Note
                    </label>
                    <textarea
                      id="soap_note"
                      rows={6}
                      value={inputs.soap_note || ""}
                      onChange={(e) => handleInputChange("soap_note", e.target.value)}
                      className="w-full text-xs font-mono p-3 bg-black/40 border border-[var(--border)] rounded focus:outline-none focus:border-[var(--accent)] text-white"
                      placeholder="Enter patient clinical SOAP note..."
                    />
                  </div>

                  <div className="space-y-1">
                    <label htmlFor="mode" className="text-[10px] text-[var(--text-dim)] font-mono uppercase tracking-wider block">
                      Agent Orchestration Engine
                    </label>
                    <div className="grid grid-cols-3 gap-2">
                      {[
                        { key: "sota", label: "SOTA Agent" },
                        { key: "maf", label: "Microsoft Agent (MAF)" },
                        { key: "maf_handoff", label: "Multi-Agent Handoff (MAF)" }
                      ].map((m) => (
                        <button
                          key={m.key}
                          onClick={() => handleInputChange("mode", m.key)}
                          className={`px-3 py-1.5 border rounded text-[10px] font-mono uppercase tracking-wider cursor-pointer transition-colors
                            ${inputs.mode === m.key 
                              ? "bg-[var(--accent)]/10 border-[var(--accent)] text-[var(--accent)]" 
                              : "border-[var(--border)] text-[var(--text-secondary)] hover:bg-white/5"
                            }
                          `}
                        >
                          {m.label}
                        </button>
                      ))}
                    </div>
                  </div>
                </>
              )}

              {/* Patient Selector for Nursing & Discharge */}
              {(activeAgentKey === "discharge" || activeAgentKey === "nursing") && (
                <div className="space-y-1">
                  <label htmlFor="patient_id" className="text-[10px] text-[var(--text-dim)] font-mono uppercase tracking-wider block">
                    Select Patient Target ID
                  </label>
                  <select
                    id="patient_id"
                    value={inputs.patient_id || ""}
                    onChange={(e) => handleInputChange("patient_id", e.target.value)}
                    className="w-full sm:w-64 text-xs font-mono p-2 bg-black/40 border border-[var(--border)] rounded focus:outline-none focus:border-[var(--accent)] text-white uppercase"
                  >
                    <option value="1">Patient #1 (John Doe - Cardiology)</option>
                    <option value="2">Patient #2 (Jane Smith - Endocrinology)</option>
                    <option value="3">Patient #3 (Bob Wilson - Nephrology)</option>
                  </select>
                </div>
              )}

              {/* Security Patch Agent */}
              {activeAgentKey === "patch" && (
                <>
                  <div className="space-y-1">
                    <label htmlFor="dependencies" className="text-[10px] text-[var(--text-dim)] font-mono uppercase tracking-wider">
                      Dependencies Log
                    </label>
                    <textarea
                      id="dependencies"
                      rows={3}
                      value={inputs.dependencies || ""}
                      onChange={(e) => handleInputChange("dependencies", e.target.value)}
                      className="w-full text-xs font-mono p-3 bg-black/40 border border-[var(--border)] rounded focus:outline-none focus:border-[var(--accent)] text-white"
                      placeholder="e.g. fastapi, cryptography..."
                    />
                  </div>
                  <div className="space-y-1">
                    <label htmlFor="env_config" className="text-[10px] text-[var(--text-dim)] font-mono uppercase tracking-wider">
                      Active Environment Configuration
                    </label>
                    <textarea
                      id="env_config"
                      rows={3}
                      value={inputs.env_config || ""}
                      onChange={(e) => handleInputChange("env_config", e.target.value)}
                      className="w-full text-xs font-mono p-3 bg-black/40 border border-[var(--border)] rounded focus:outline-none focus:border-[var(--accent)] text-white"
                      placeholder="e.g. CORS_ORIGIN=*, DEBUG=True..."
                    />
                  </div>
                </>
              )}

              {/* Self-Healing Auto-Fix */}
              {activeAgentKey === "fix" && (
                <>
                  <div className="space-y-1">
                    <label htmlFor="error_logs" className="text-[10px] text-[var(--text-dim)] font-mono uppercase tracking-wider">
                      System Exception Logs
                    </label>
                    <textarea
                      id="error_logs"
                      rows={3}
                      value={inputs.error_logs || ""}
                      onChange={(e) => handleInputChange("error_logs", e.target.value)}
                      className="w-full text-xs font-mono p-3 bg-black/40 border border-[var(--border)] rounded focus:outline-none focus:border-[var(--accent)] text-white"
                      placeholder="Enter exception log..."
                    />
                  </div>
                  <div className="space-y-1">
                    <label htmlFor="health_signals" className="text-[10px] text-[var(--text-dim)] font-mono uppercase tracking-wider">
                      Active Host Health Telemetry
                    </label>
                    <input
                      id="health_signals"
                      type="text"
                      value={inputs.health_signals || ""}
                      onChange={(e) => handleInputChange("health_signals", e.target.value)}
                      className="w-full text-xs font-mono p-2.5 bg-black/40 border border-[var(--border)] rounded focus:outline-none focus:border-[var(--accent)] text-white"
                      placeholder="Enter health status..."
                    />
                  </div>
                </>
              )}

              {/* Call Coordinator Emergency Alarm */}
              {activeAgentKey === "call" && (
                <>
                  <div className="space-y-1">
                    <label htmlFor="alert_details" className="text-[10px] text-[var(--text-dim)] font-mono uppercase tracking-wider">
                      Vital Signal Alert Payload
                    </label>
                    <textarea
                      id="alert_details"
                      rows={3}
                      value={inputs.alert_details || ""}
                      onChange={(e) => handleInputChange("alert_details", e.target.value)}
                      className="w-full text-xs font-mono p-3 bg-black/40 border border-[var(--border)] rounded focus:outline-none focus:border-[var(--accent)] text-white"
                      placeholder="Tachycardia/Bradycardia alarm metrics..."
                    />
                  </div>
                  <div className="space-y-1">
                    <label htmlFor="staff_directory" className="text-[10px] text-[var(--text-dim)] font-mono uppercase tracking-wider">
                      Specialist Roster / Directory
                    </label>
                    <textarea
                      id="staff_directory"
                      rows={2}
                      value={inputs.staff_directory || ""}
                      onChange={(e) => handleInputChange("staff_directory", e.target.value)}
                      className="w-full text-xs font-mono p-3 bg-black/40 border border-[var(--border)] rounded focus:outline-none focus:border-[var(--accent)] text-white"
                      placeholder="Doctor phone numbers..."
                    />
                  </div>
                </>
              )}

            </div>

            {/* Run Button */}
            <div className="pt-2">
              <button
                onClick={triggerAgent}
                disabled={loading}
                className="w-full sm:w-auto px-6 py-2.5 rounded bg-[var(--accent)] text-white text-xs font-bold uppercase tracking-wider hover:bg-[rgba(14,165,233,0.85)] disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <RefreshCw size={13} className="animate-spin" /> Dispatching Agent...
                  </>
                ) : (
                  <>
                    <Play size={12} fill="white" /> Execute Agent
                  </>
                )}
              </button>
            </div>

          </div>

          {/* Results Output Console */}
          <div className="mt-8 pt-6 border-t border-[var(--border)] space-y-4">
            
            {loading && (
              <div className="p-8 text-center text-xs text-[var(--text-dim)] font-mono uppercase tracking-widest flex items-center justify-center gap-3">
                <span className="w-5 h-5 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin inline-block" />
                Awaiting Agent Telemetry and Structured Response...
              </div>
            )}

            {error && (
              <div className="p-4 bg-[var(--danger-muted)] border border-[var(--danger-border)] text-[var(--danger)] text-xs font-mono rounded flex gap-2">
                <AlertTriangle size={14} className="shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold block uppercase">Agent Dispatch Failed</span>
                  <span className="mt-1 block">{error}</span>
                </div>
              </div>
            )}

            {result && (
              <div className="space-y-4">
                
                {/* Telemetry Card */}
                {result.telemetry && (
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 bg-white/[0.01] border border-white/[0.03] p-3.5 rounded-lg text-[10px] font-mono uppercase tracking-wider text-[var(--text-secondary)]">
                    <div>
                      <span className="text-[var(--text-dim)] block">Execution Time</span>
                      <span className="text-white font-bold block text-xs mt-0.5">{result.telemetry.duration?.toFixed(2) || "0.00"}s</span>
                    </div>
                    <div>
                      <span className="text-[var(--text-dim)] block">Input Tokens</span>
                      <span className="text-white font-bold block text-xs mt-0.5">{result.telemetry.input_tokens || 0}</span>
                    </div>
                    <div>
                      <span className="text-[var(--text-dim)] block">Output Tokens</span>
                      <span className="text-white font-bold block text-xs mt-0.5">{result.telemetry.output_tokens || 0}</span>
                    </div>
                    <div>
                      <span className="text-[var(--text-dim)] block">Estimated Cost</span>
                      <span className="text-[var(--success)] font-bold block text-xs mt-0.5">${result.telemetry.estimated_cost?.toFixed(5) || "0.00000"}</span>
                    </div>
                  </div>
                )}

                {/* Console Log JSON Output */}
                <div className="space-y-1.5">
                  <span className="text-[10px] text-[var(--text-dim)] font-mono uppercase tracking-wider flex items-center gap-1.5">
                    <Terminal size={11} /> Agent Output Stream
                  </span>
                  <div className="max-h-72 overflow-y-auto p-4 rounded bg-black/60 border border-[var(--border)] font-mono text-[11px] leading-relaxed text-sky-400">
                    <pre className="whitespace-pre-wrap">
                      {JSON.stringify(result.data || result, null, 2)}
                    </pre>
                  </div>
                </div>

              </div>
            )}

            {/* Medical Disclaimer if relevant */}
            {activeAgentKey === "billing" && (
              <div className="p-3 bg-white/[0.01] border border-white/[0.03] rounded-lg">
                <p className="text-[10px] leading-normal text-gray-500 font-medium italic text-center">
                  Notice: Code recommendations are generated as CDSS advice. Final coding choices remain subject to human supervisor validation before actual claims clearance.
                </p>
              </div>
            )}

          </div>

        </div>

      </div>

    </div>
  );
}
