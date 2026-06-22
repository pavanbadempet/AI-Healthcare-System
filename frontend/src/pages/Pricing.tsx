
import { useState } from "react";
import { createPaymentOrder, verifyPayment } from "@/lib/api";
import { fetchProcedureCostEstimate } from "@/lib/apiIntelligence";
import { motion } from "framer-motion";
import { Check, Star, Shield, Zap, AlertCircle } from "lucide-react";
import { useAuthStore } from "@/lib/auth";

const PLANS = [
  {
    id: "basic",
    name: "Basic Health",
    price: "Free",
    amount: 0,
    icon: Shield,
    color: "var(--accent-blue)",
    features: ["10 AI Predictions per month", "Standard ML Models", "Basic health dashboard", "Community support"]
  },
  {
    id: "pro",
    name: "Pro Copilot",
    price: "₹999",
    period: "/mo",
    amount: 999,
    icon: Zap,
    color: "var(--accent)",
    popular: true,
    features: ["Unlimited AI Predictions", "Advanced Ensemble Models", "Priority Doctor Consultations", "RAG Medical Context Generation", "Export Health Reports"]
  },
  {
    id: "enterprise",
    name: "Family Plan",
    price: "₹2499",
    period: "/mo",
    amount: 2499,
    icon: Star,
    color: "var(--accent-purple)",
    features: ["Up to 5 family members", "All Pro features included", "24/7 Priority Support", "Dedicated Health Concierge"]
  }
];

export default function PricingPage() {
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState("");
  const { user } = useAuthStore();

  const [calcProcedure, setCalcProcedure] = useState("mri");
  const [calcInsurance, setCalcInsurance] = useState("");
  const [calcRegion, setCalcRegion] = useState("US");
  const [loadingEstimate, setLoadingEstimate] = useState(false);
  const [estimateResult, setEstimateResult] = useState<any>(null);
  const [estimateError, setEstimateError] = useState("");

  const handleEstimateCost = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoadingEstimate(true);
    setEstimateError("");
    setEstimateResult(null);
    try {
      const data = await fetchProcedureCostEstimate(calcProcedure, calcInsurance || undefined, calcRegion);
      setEstimateResult(data);
    } catch (err: any) {
      setEstimateError(err.message || "Failed to fetch cost estimate");
    } finally {
      setLoadingEstimate(false);
    }
  };

  const handleUpgrade = async (plan: typeof PLANS[0]) => {
    if (plan.amount === 0) return;
    
    setLoading(plan.id);
    setError("");

    try {
      const order = await createPaymentOrder(plan.id);
      
      const options = {
        key: import.meta.env.NEXT_PUBLIC_RAZORPAY_KEY_ID || import.meta.env.VITE_PUBLIC_RAZORPAY_KEY_ID || "rzp_test_placeholder",
        amount: order.amount,
        currency: "INR",
        name: "AI Healthcare System",
        description: `Upgrade to ${plan.name}`,
        order_id: order.id,
        handler: async function (response: any) {
          try {
            await verifyPayment({
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature
            });
            alert("Payment successful! Your account has been upgraded.");
            window.location.reload();
          } catch (err: any) {
            setError(err.message || "Payment verification failed.");
          }
        },
        prefill: {
          name: user?.full_name || user?.username,
          email: user?.email,
        },
        theme: {
          color: "#6366f1"
        }
      };

      const rzp = new (window as any).Razorpay(options);
      rzp.on('payment.failed', function (response: any){
        setError(`Payment failed: ${response.error.description}`);
      });
      rzp.open();
    } catch (err: any) {
      setError(err.message || "Failed to initiate payment");
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="w-full mx-auto pb-12 selection:bg-[var(--accent)] selection:text-white">
      <div className="text-center mb-10">
        <h1 className="text-xl font-bold text-[var(--text-primary)] uppercase tracking-wider">Pricing Plans</h1>
        <p className="text-xs text-[var(--text-secondary)] font-mono uppercase tracking-wide mt-1 max-w-xl mx-auto leading-relaxed">
          Upgrade your diagnostic scope to unlock advanced ensemble models, RAG document references, and priority consultations.
        </p>
      </div>

      {error && (
        <div className="mb-6 p-3 flex justify-center items-center gap-2 max-w-md mx-auto text-xs font-mono uppercase bg-[var(--danger-muted)] text-[var(--danger)] border border-[var(--danger-border)] rounded" role="alert">
          <AlertCircle size={14} aria-hidden="true" /> {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto" role="list" aria-label="Pricing plans">
        {PLANS.map((plan, i) => (
          <motion.div 
            key={plan.id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className={`panel p-6 flex flex-col justify-between relative bg-[rgba(24,24,27,0.4)] ${plan.popular ? 'border-[var(--accent)] shadow-[0_0_15px_rgba(99,102,241,0.15)] md:-translate-y-2' : 'border-[var(--border)]'}`}
            role="listitem"
          >
            {plan.popular && (
              <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 px-2.5 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider text-white bg-[var(--accent)]">
                Most Popular
              </div>
            )}
            
            <div className="space-y-4">
              <div className="flex justify-between items-start">
                <div className="p-2 rounded bg-[rgba(255,255,255,0.02)] border border-[var(--border)] text-[var(--text-secondary)]" style={{ color: plan.color }}>
                  <plan.icon size={18} aria-hidden="true" />
                </div>
                <div className="flex items-baseline gap-0.5">
                  <span className="text-xl font-extrabold text-[var(--text-primary)] font-mono">{plan.price}</span>
                  {plan.period && <span className="text-[10px] font-mono text-[var(--text-dim)] uppercase">{plan.period}</span>}
                </div>
              </div>
              
              <div>
                <h3 className="text-sm font-bold text-[var(--text-primary)] uppercase tracking-wide">{plan.name}</h3>
              </div>

              <ul className="space-y-3 pt-3 border-t border-[var(--border)]" aria-label={`Features for ${plan.name}`}>
                {plan.features.map((feat, j) => (
                  <li key={j} className="flex items-start gap-2 text-xs font-mono uppercase text-[var(--text-secondary)] leading-relaxed">
                    <Check size={13} className="shrink-0 mt-0.5 text-[var(--accent-emerald)]" aria-hidden="true" />
                    <span>{feat}</span>
                  </li>
                ))}
              </ul>
            </div>

            <button 
              onClick={() => handleUpgrade(plan)}
              disabled={loading === plan.id || plan.amount === 0}
              className={`w-full py-2 mt-6 text-xs font-bold uppercase tracking-wider transition-colors cursor-pointer ${plan.popular ? 'btn btn-primary' : 'btn btn-secondary'}`}
              aria-label={plan.amount === 0 ? "Current plan" : `Upgrade to ${plan.name}`}
            >
              {loading === plan.id ? "Processing..." : plan.amount === 0 ? "Active Plan" : "Upgrade Subsystem"}
            </button>
          </motion.div>
        ))}
      </div>

      {/* Procedure Cost Estimator Section (Itch 9) */}
      <div className="mt-12 max-w-2xl mx-auto">
        <div className="panel p-6 space-y-6 bg-[rgba(24,24,27,0.4)] border border-[var(--border)]">
          <div className="flex items-center gap-2 pb-3 border-b border-[var(--border)]">
            <Star size={16} className="text-[var(--accent)] animate-pulse" />
            <h2 className="text-sm font-bold text-[var(--text-primary)] uppercase tracking-wide">Procedure Cost Estimator</h2>
          </div>
          <p className="text-xs text-[var(--text-secondary)] font-mono uppercase">
            Avoid surprise billing. Select a clinical procedure and insurance coverage to query real-time cost-sharing breakdowns.
          </p>

          <form onSubmit={handleEstimateCost} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="section-label mb-1 block" htmlFor="calc-procedure">Procedure Type</label>
                <select
                  id="calc-procedure"
                  value={calcProcedure}
                  onChange={(e) => setCalcProcedure(e.target.value)}
                  className="input-clinical"
                  required
                >
                  <option value="mri" className="bg-[var(--bg-card)]">MAGNETIC RESONANCE IMAGING (MRI)</option>
                  <option value="blood" className="bg-[var(--bg-card)]">COMPREHENSIVE BLOOD PANEL</option>
                  <option value="cardiac" className="bg-[var(--bg-card)]">CARDIAC EKG / ECG</option>
                  <option value="consult" className="bg-[var(--bg-card)]">ATTENDING CLINIC CONSULT</option>
                </select>
              </div>

              <div>
                <label className="section-label mb-1 block" htmlFor="calc-insurance">Insurance Provider</label>
                <select
                  id="calc-insurance"
                  value={calcInsurance}
                  onChange={(e) => setCalcInsurance(e.target.value)}
                  className="input-clinical"
                >
                  <option value="" className="bg-[var(--bg-card)]">SELF-PAY / CASH</option>
                  <option value="blue" className="bg-[var(--bg-card)]">BLUE CROSS BLUE SHIELD</option>
                  <option value="medicare" className="bg-[var(--bg-card)]">MEDICARE</option>
                  <option value="aetna" className="bg-[var(--bg-card)]">AETNA</option>
                  <option value="other" className="bg-[var(--bg-card)]">OTHER PROVIDER</option>
                </select>
              </div>

              <div>
                <label className="section-label mb-1 block" htmlFor="calc-region">Billing Region</label>
                <select
                  id="calc-region"
                  value={calcRegion}
                  onChange={(e) => setCalcRegion(e.target.value)}
                  className="input-clinical"
                  required
                >
                  <option value="US" className="bg-[var(--bg-card)]">UNITED STATES (USD)</option>
                  <option value="IN" className="bg-[var(--bg-card)]">INDIA (INR)</option>
                  <option value="UK" className="bg-[var(--bg-card)]">UNITED KINGDOM (GBP)</option>
                  <option value="EU" className="bg-[var(--bg-card)]">EUROPEAN UNION (EUR)</option>
                </select>
              </div>
            </div>

            <button
              type="submit"
              disabled={loadingEstimate}
              className="w-full btn btn-primary py-2.5 cursor-pointer flex items-center justify-center gap-1.5 text-xs uppercase"
            >
              {loadingEstimate ? "Calculating..." : "Query Out-Of-Pocket Breakdown"}
            </button>
          </form>

          {estimateError && (
            <div className="p-3 text-xs font-mono uppercase bg-[var(--danger-muted)] text-[var(--danger)] border border-[var(--danger-border)] rounded" role="alert">
              {estimateError}
            </div>
          )}

          {estimateResult && (
            <div className="mt-4 p-4 rounded-xl bg-slate-950/60 border border-[var(--border)] space-y-4">
              <div className="flex justify-between items-center text-xs font-mono uppercase">
                <span className="text-[var(--text-dim)]">Pricing Standard</span>
                <span className="text-[var(--text-secondary)] font-bold">{estimateResult.pricing_model}</span>
              </div>

              <div className="divide-y divide-[var(--border)] text-xs font-mono uppercase">
                <div className="flex justify-between py-2">
                  <span className="text-[var(--text-dim)]">Doctor Fee</span>
                  <span className="text-[var(--text-primary)]">{estimateResult.currency_symbol || "₹"}{estimateResult.breakdown.doctor_fee}</span>
                </div>
                <div className="flex justify-between py-2">
                  <span className="text-[var(--text-dim)]">Facility Fee</span>
                  <span className="text-[var(--text-primary)]">{estimateResult.currency_symbol || "₹"}{estimateResult.breakdown.facility_fee}</span>
                </div>
                <div className="flex justify-between py-2">
                  <span className="text-[var(--text-dim)]">Laboratory Fee</span>
                  <span className="text-[var(--text-primary)]">{estimateResult.currency_symbol || "₹"}{estimateResult.breakdown.lab_fee}</span>
                </div>
                <div className="flex justify-between py-2 font-bold text-[var(--accent)]">
                  <span>Gross Total Cost</span>
                  <span>{estimateResult.currency_symbol || "₹"}{estimateResult.gross_total}</span>
                </div>
                <div className="flex justify-between py-2">
                  <span className="text-[var(--text-dim)]">Insurance Covered ({estimateResult.coverage_percentage}%)</span>
                  <span className="text-[var(--accent-emerald)]">-{estimateResult.currency_symbol || "₹"}{estimateResult.insurance_covered}</span>
                </div>
                <div className="flex justify-between py-2 font-bold text-base text-[var(--danger)] pt-3 border-t border-[var(--border)]">
                  <span>Patient Responsibility</span>
                  <span>{estimateResult.currency_symbol || "₹"}{estimateResult.patient_responsibility}</span>
                </div>
              </div>
              <p className="text-[10px] text-[var(--text-dim)] font-mono uppercase text-center mt-2 leading-relaxed">
                * Note: Estimates are based on standard hospital chargemasters. Co-pays may vary depending on individual deductible limits.
              </p>
            </div>
          )}
        </div>
      </div>
      
      <script src="https://checkout.razorpay.com/v1/checkout.js" async></script>
    </div>
  );
}
