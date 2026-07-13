import { useCallback, useEffect, useMemo, useState, FormEvent } from "react";
import { AlertTriangle, Pill, RefreshCcw, Plus, ShieldAlert, Sparkles, Loader2, CheckCircle2 } from "lucide-react";
import { useAuthStore } from "@/lib/auth";
import {
  getDoctorPatientPrescriptions,
  getPatientPrescriptions,
  type Prescription,
  type PrescriptionItem,
} from "@/lib/api";
import { checkPrescribingSafety, fetchGenericSubstitution, fetchMedicationPricing } from "@/lib/apiIntelligence";
import { apiFetch } from "@/lib/apiCore";

interface PatientMedicationsPanelProps {
  patientId: number;
  refreshIntervalMs?: number;
}

const DEFAULT_CLINICAL_NOTE = "Prescriptions support clinician and pharmacist workflows.";
const PATIENT_MEDICATION_NOTE = "Medication details are for review. Consult your provider before changes.";

function statusStyle(status: string) {
  const normalized = status.toLowerCase();
  if (normalized === "dispensed") {
    return "border-[var(--success-border)] bg-[var(--success-muted)] text-[var(--success)]";
  }
  if (normalized === "partially_dispensed") {
    return "border-[var(--warning-border)] bg-[var(--warning-muted)] text-[var(--warning)]";
  }
  return "border-[var(--accent-border)] bg-[var(--accent-muted)] text-[var(--accent)]";
}

function formatStatus(status: string) {
  return status
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(" ");
}

function itemQuantityText(item: PrescriptionItem) {
  return `${item.quantity_prescribed} units prescribed`;
}

function sortedPrescriptions(prescriptions: Prescription[]) {
  return [...prescriptions].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
}

export default function PatientMedicationsPanel({
  patientId,
  refreshIntervalMs = 30000,
}: PatientMedicationsPanelProps) {
  const { user } = useAuthStore();
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);
  const [safetyNote, setSafetyNote] = useState(DEFAULT_CLINICAL_NOTE);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  // Prescribing Form State
  const [showPrescribeForm, setShowPrescribeForm] = useState(false);
  const [medName, setMedName] = useState("");
  const [dosage, setDosage] = useState("");
  const [frequency, setFrequency] = useState("");
  const [duration, setDuration] = useState("");
  const [quantity, setQuantity] = useState(1);
  const [instructions, setInstructions] = useState("");
  const [additionalAllergies, setAdditionalAllergies] = useState("");
  
  // Safety check state
  const [safetyAlerts, setSafetyAlerts] = useState<any[]>([]);
  const [checkingSafety, setCheckingSafety] = useState(false);
  const [overrideJustification, setOverrideJustification] = useState("");

  // Alternatives and Pricing compare state
  const [genericAlternative, setGenericAlternative] = useState<any>(null);
  const [priceComparison, setPriceComparison] = useState<any>(null);
  const [checkingAlternatives, setCheckingAlternatives] = useState(false);

  const runAlternativesAndPricingCheck = async () => {
    if (!medName) return;
    setCheckingAlternatives(true);
    setGenericAlternative(null);
    setPriceComparison(null);
    try {
      const [genericRes, priceRes] = await Promise.all([
        fetchGenericSubstitution(medName),
        fetchMedicationPricing(medName)
      ]);
      if (genericRes.substituted) {
        setGenericAlternative(genericRes);
      }
      if (priceRes.prices) {
        setPriceComparison(priceRes);
      }
    } catch (err) {
      console.error("Alternatives/pricing check failed:", err);
    } finally {
      setCheckingAlternatives(false);
    }
  };

  const runSafetyCheck = async () => {
    if (!medName) return;
    setCheckingSafety(true);
    try {
      const res = await checkPrescribingSafety({
        patient_id: patientId,
        medication_name: medName,
        dosage,
        frequency,
        duration,
        additional_allergies: additionalAllergies ? additionalAllergies.split(",").map(s => s.trim()) : undefined
      });
      setSafetyAlerts(res.alerts || []);
    } catch (err) {
      console.error("Safety check failed:", err);
    } finally {
      setCheckingSafety(false);
    }
  };

  const handlePrescribe = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    
    const hasCritical = safetyAlerts.some(a => a.severity === "critical");
    if (hasCritical && !overrideJustification.trim()) {
      setError("Please provide a clinical override justification for the critical warning.");
      return;
    }

    try {
      await apiFetch("/pharmacy/prescriptions", {
        method: "POST",
        body: JSON.stringify({
          patient_id: patientId,
          diagnosis_context: hasCritical ? `Override: ${overrideJustification}` : undefined,
          items: [
            {
              medication_name: medName,
              dosage,
              frequency,
              duration,
              quantity_prescribed: quantity,
              instructions
            }
          ]
        })
      });
      
      // Reset form fields
      setMedName("");
      setDosage("");
      setFrequency("");
      setDuration("");
      setQuantity(1);
      setInstructions("");
      setOverrideJustification("");
      setSafetyAlerts([]);
      setShowPrescribeForm(false);
      
      // Reload prescriptions
      await loadPrescriptions(true);
    } catch (err: any) {
      setError(err.message || "Failed to create prescription");
    }
  };


  const canLoadPrescriptions = useMemo(() => {
    const role = user?.role || "";
    return role === "doctor" || (role === "patient" && user?.id === patientId);
  }, [user, patientId]);

  const orderedPrescriptions = useMemo(() => sortedPrescriptions(prescriptions), [prescriptions]);

  const loadPrescriptions = useCallback(async (isManualRefresh = false) => {
    if (!canLoadPrescriptions) {
      setLoading(false);
      return;
    }

    if (isManualRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError("");

    try {
      if (user?.role === "doctor") {
        const feed = await getDoctorPatientPrescriptions(patientId);
        setPrescriptions(feed.prescriptions);
        setSafetyNote(feed.clinical_safety_note ?? DEFAULT_CLINICAL_NOTE);
      } else {
        setPrescriptions(await getPatientPrescriptions());
        setSafetyNote(PATIENT_MEDICATION_NOTE);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load medication orders");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [canLoadPrescriptions, user, patientId]);

  useEffect(() => {
    void loadPrescriptions();
    if (!canLoadPrescriptions || refreshIntervalMs <= 0) return;

    const timer = window.setInterval(() => {
      void loadPrescriptions(true);
    }, refreshIntervalMs);

    return () => window.clearInterval(timer);
  }, [canLoadPrescriptions, loadPrescriptions, refreshIntervalMs]);

  if (!canLoadPrescriptions) {
    return (
      <div className="panel p-4" role="region" aria-label="Active medications">
        <h3 className="section-label mb-3">Medication Orders</h3>
        <div className="rounded border border-[var(--border)] bg-[rgba(255,255,255,0.01)] p-3 text-xs font-mono text-[var(--text-secondary)] uppercase">
          No active medication records.
        </div>
      </div>
    );
  }

  return (
    <section className="panel overflow-hidden" role="region" aria-label="Medication orders">
      <div className="panel-header flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between bg-[rgba(15,15,17,0.5)]">
        <div>
          <div className="section-label mb-1.5 flex items-center gap-1.5 text-[var(--accent)]">
            <Pill size={13} aria-hidden="true" /> Pharmacotherapy Prescriptions
          </div>
          <h2 className="text-sm font-bold text-[var(--text-primary)] uppercase">Active Medications</h2>
          <p className="mt-1 text-xs text-[var(--text-secondary)] uppercase">
            {safetyNote}
          </p>
        </div>
        <div className="flex gap-2">
          {user?.role === "doctor" && (
            <button
              type="button"
              onClick={() => setShowPrescribeForm(!showPrescribeForm)}
              className="btn btn-primary text-xs flex items-center justify-center gap-1 cursor-pointer"
              aria-label="Prescribe new medication"
            >
              <Plus size={13} aria-hidden="true" />
              {showPrescribeForm ? "Cancel Form" : "Prescribe"}
            </button>
          )}
          <button
            type="button"
            onClick={() => void loadPrescriptions(true)}
            disabled={refreshing}
            className="btn btn-secondary text-xs flex items-center justify-center gap-1 cursor-pointer"
            aria-label="Refresh medication orders"
          >
            <RefreshCcw size={13} className={refreshing ? "animate-spin" : ""} aria-hidden="true" />
            Sync Rx
          </button>
        </div>
      </div>

      {showPrescribeForm && (
        <form onSubmit={handlePrescribe} className="border-b border-[var(--border)] bg-[rgba(255,255,255,0.02)] p-4 space-y-4">
          <h3 className="text-xs font-bold text-[var(--text-primary)] uppercase flex items-center gap-1">
            <Sparkles size={13} className="text-[var(--accent)]" /> Prescribe New Medication
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-[10px] font-mono uppercase text-[var(--text-secondary)] mb-1">Medication Name</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={medName}
                  onChange={(e) => {
                    setMedName(e.target.value);
                    setGenericAlternative(null);
                    setPriceComparison(null);
                  }}
                  placeholder="e.g. Metformin, Lisinopril"
                  className="input-clinical flex-1"
                  required
                />
                <button
                  type="button"
                  onClick={runAlternativesAndPricingCheck}
                  disabled={checkingAlternatives || !medName}
                  className="btn btn-secondary text-xs px-2 cursor-pointer flex items-center gap-1"
                >
                  {checkingAlternatives ? (
                    <Loader2 size={12} className="animate-spin animate-duration-1000" />
                  ) : (
                    "Check Prices & Alternatives"
                  )}
                </button>
              </div>
            </div>
            <div>
              <label className="block text-[10px] font-mono uppercase text-[var(--text-secondary)] mb-1">Dosage</label>
              <input
                type="text"
                value={dosage}
                onChange={(e) => setDosage(e.target.value)}
                placeholder="e.g. 500mg, 10ml"
                className="input-clinical w-full"
                required
              />
            </div>
            <div>
              <label className="block text-[10px] font-mono uppercase text-[var(--text-secondary)] mb-1">Frequency</label>
              <input
                type="text"
                value={frequency}
                onChange={(e) => setFrequency(e.target.value)}
                placeholder="e.g. Twice daily, every 12 hours"
                className="input-clinical w-full"
                required
              />
            </div>
            <div>
              <label className="block text-[10px] font-mono uppercase text-[var(--text-secondary)] mb-1">Duration</label>
              <input
                type="text"
                value={duration}
                onChange={(e) => setDuration(e.target.value)}
                placeholder="e.g. 30 days, 7 days"
                className="input-clinical w-full"
                required
              />
            </div>
            <div>
              <label className="block text-[10px] font-mono uppercase text-[var(--text-secondary)] mb-1">Quantity</label>
              <input
                type="number"
                value={quantity}
                onChange={(e) => setQuantity(Number(e.target.value))}
                min={1}
                className="input-clinical w-full"
                required
              />
            </div>
            <div>
              <label className="block text-[10px] font-mono uppercase text-[var(--text-secondary)] mb-1">Additional Allergies (comma-separated)</label>
              <input
                type="text"
                value={additionalAllergies}
                onChange={(e) => setAdditionalAllergies(e.target.value)}
                placeholder="e.g. Penicillin, Sulfa"
                className="input-clinical w-full"
              />
            </div>
          </div>

          {/* Generic Substitutions & Price Comparisons */}
          {(genericAlternative || priceComparison) && (
            <div className="border border-[var(--border)] rounded p-3 bg-[rgba(0,0,0,0.15)] space-y-3">
              {genericAlternative && (
                <div className="flex items-center justify-between p-2 rounded border border-[rgba(16,185,129,0.3)] bg-[rgba(16,185,129,0.05)] text-xs">
                  <div className="text-[var(--text-primary)]">
                    <span className="font-bold text-[rgba(16,185,129,1)]">Generic Alternative:</span> {genericAlternative.generic_name} (Strength: {genericAlternative.strength_match}). Estimated savings: <span className="font-bold font-mono text-[var(--accent)] text-sm">${genericAlternative.savings.toFixed(2)}</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setMedName(genericAlternative.generic_name);
                      setGenericAlternative(null);
                    }}
                    className="btn btn-primary text-[10px] py-0.5 px-1.5 cursor-pointer"
                  >
                    Swap to Generic
                  </button>
                </div>
              )}

              {priceComparison && (
                <div className="space-y-1.5">
                  <span className="text-[9px] font-mono uppercase text-[var(--text-secondary)]">Local Pharmacy Price Comparison (Cheapest First)</span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                    {priceComparison.prices.map((item: any, idx: number) => (
                      <div key={idx} className="p-2 rounded border border-[var(--border)] bg-[rgba(0,0,0,0.25)] flex justify-between items-center text-xs">
                        <div>
                          <div className="font-bold text-[var(--text-primary)]">{item.chain}</div>
                          <div className="text-[10px] text-[var(--text-secondary)]">{item.distance} miles away</div>
                        </div>
                        <div className="text-right">
                          <div className="font-mono font-bold text-[var(--accent)] text-sm">${item.price.toFixed(2)}</div>
                          <div className="text-[8px] text-[rgba(16,185,129,1)] font-bold uppercase">In Stock</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
          
          <div>
            <label className="block text-[10px] font-mono uppercase text-[var(--text-secondary)] mb-1">Instructions / Notes</label>
            <input
              type="text"
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              placeholder="e.g. Take with food, swallow whole"
              className="input-clinical w-full"
            />
          </div>

          {/* Safety Check Trigger and Display */}
          <div className="border border-[var(--border)] rounded p-3 bg-[rgba(0,0,0,0.2)] space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono uppercase text-[var(--text-secondary)] flex items-center gap-1">
                <ShieldAlert size={12} className="text-[var(--warning)]" /> Prescribing Safety Audit
              </span>
              <button
                type="button"
                onClick={runSafetyCheck}
                disabled={checkingSafety || !medName}
                className="btn btn-secondary text-[10px] px-2 py-1 flex items-center gap-1 cursor-pointer"
              >
                {checkingSafety ? (
                  <>
                    <Loader2 size={10} className="animate-spin animate-duration-1000" />
                    Auditing...
                  </>
                ) : (
                  "Run Safety Check"
                )}
              </button>
            </div>

            <div className="p-2 rounded border border-[var(--warning-border)] bg-[rgba(245,158,11,0.03)] text-[9px] font-mono text-[var(--warning)] uppercase leading-normal">
              Medical Disclaimer: Safety audits are AI-generated decision support. They do not replace professional pharmacological evaluation.
            </div>

            {safetyAlerts.length > 0 ? (
              <div className="space-y-2">
                {safetyAlerts.map((alert, idx) => {
                  const isCritical = alert.severity === "critical";
                  const isWarning = alert.severity === "warning";
                  const severityColor = isCritical
                    ? "text-[var(--danger)] border-[var(--danger-border)] bg-[rgba(239,68,68,0.05)]"
                    : isWarning
                    ? "text-[var(--warning)] border-[var(--warning-border)] bg-[rgba(245,158,11,0.05)]"
                    : "text-[var(--info)] border-[var(--info-border)] bg-[rgba(59,130,246,0.05)]";
                  
                  return (
                    <div key={idx} className={`p-2 rounded border text-xs ${severityColor}`}>
                      <div className="font-bold flex items-center gap-1 uppercase text-[10px]">
                        <AlertTriangle size={11} /> {alert.severity} alert - {alert.type}
                      </div>
                      <div className="mt-1">{alert.message}</div>
                      {alert.evidence && (
                        <div className="mt-1 text-[10px] opacity-75 font-mono">Evidence: {alert.evidence}</div>
                      )}
                    </div>
                  );
                })}

                {safetyAlerts.some(a => a.severity === "critical") && (
                  <div className="space-y-1 pt-2 border-t border-[var(--border)]">
                    <label className="block text-[10px] font-mono uppercase text-[var(--danger)] font-bold">
                      Clinical Override Justification Required
                    </label>
                    <input
                      type="text"
                      value={overrideJustification}
                      onChange={(e) => setOverrideJustification(e.target.value)}
                      placeholder="Specify why benefits outweigh risks (e.g., patient is monitored regularly)"
                      className="input-clinical w-full border-[var(--danger-border)] focus:border-[var(--danger)]"
                      required
                    />
                  </div>
                )}
              </div>
            ) : (
              !checkingSafety && (
                <div className="text-[10px] font-mono text-[var(--text-dim)] uppercase">
                  No alerts loaded. Run check to verify patient compatibility.
                </div>
              )
            )}
          </div>

          {error && (
            <div className="text-xs text-[var(--danger)] font-mono flex items-center gap-1">
              <AlertTriangle size={12} /> {error}
            </div>
          )}

          <div className="flex gap-2 justify-end">
            <button
              type="button"
              onClick={() => {
                setShowPrescribeForm(false);
                setSafetyAlerts([]);
                setOverrideJustification("");
              }}
              className="btn btn-secondary text-xs px-3 py-1.5 cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary text-xs px-3 py-1.5 cursor-pointer"
            >
              Issue Prescription
            </button>
          </div>
          
          <div className="text-[9px] text-[var(--text-dim)] uppercase tracking-wide border-t border-[var(--border)] pt-2 mt-2">
            ⚠️ Disclaimer: AI-generated checks are advisory. The prescribing clinician retains final diagnostic and therapeutic responsibility.
          </div>
        </form>
      )}

      <div className="p-4 space-y-3">
        <div className="flex justify-between items-center text-[10px] font-mono uppercase text-[var(--text-dim)] pb-2 border-b border-[var(--border)]">
          <span>{orderedPrescriptions.length} active orders</span>
          <span>Pharmacy log</span>
        </div>

        {loading ? (
          <div className="p-3 text-xs font-mono text-[var(--text-dim)] uppercase tracking-wider">
            Loading Rx list...
          </div>
        ) : error ? (
          <div className="flex items-center gap-1.5 p-3 text-xs font-mono text-[var(--danger)]" role="alert">
            <AlertTriangle size={13} aria-hidden="true" /> {error}
          </div>
        ) : orderedPrescriptions.length === 0 ? (
          <div className="p-3 text-xs font-mono text-[var(--text-dim)] uppercase tracking-wide">
            No medication orders logged.
          </div>
        ) : (
          <div className="space-y-3" aria-label="Medication order list">
            {orderedPrescriptions.map((prescription) => (
              <div key={prescription.id} className="space-y-2 p-2.5 rounded border border-[var(--border)] bg-[rgba(255,255,255,0.01)]">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--border)] pb-2">
                  <span className={`px-1.5 py-0.5 rounded-sm border text-[9px] uppercase font-bold font-mono tracking-wider ${statusStyle(prescription.status)}`}>
                    {formatStatus(prescription.status)}
                  </span>
                  {prescription.diagnosis_context && (
                    <span className="mono-meta text-[9px]">{prescription.diagnosis_context}</span>
                  )}
                </div>
                
                <div className="space-y-2">
                  {prescription.items.map((item) => (
                    <div key={item.id} className="rounded border border-[var(--border-subtle)] bg-[rgba(255,255,255,0.015)] p-2">
                      <h3 className="text-xs font-bold text-[var(--text-primary)] uppercase">{item.medication_name}</h3>
                      <p className="text-[10px] font-mono text-[var(--text-secondary)] uppercase mt-0.5">
                        {item.dosage} / {item.frequency} / {item.duration}
                      </p>
                      <div className="mt-1 flex flex-wrap gap-2 text-[9px] font-mono text-[var(--text-dim)] uppercase">
                        <span>{itemQuantityText(item)}</span>
                        <span>{item.quantity_dispensed} dispensed</span>
                        <span>{formatStatus(item.status)}</span>
                      </div>
                      {item.instructions && (
                        <p className="mt-1 text-[10px] font-mono text-[var(--text-secondary)] uppercase border-t border-[var(--border-subtle)] pt-1">Notes: {item.instructions}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
