
import { useState } from "react";
import { createPaymentOrder, verifyPayment } from "@/lib/api";
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
      
      <script src="https://checkout.razorpay.com/v1/checkout.js" async></script>
    </div>
  );
}
