"use client";

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
    color: "var(--success)",
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
        key: process.env.NEXT_PUBLIC_RAZORPAY_KEY_ID || "rzp_test_placeholder",
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
          color: "#c7a36a"
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
    <div className="w-full mx-auto pb-16">
      <div className="text-center mb-16">
        <h1 className="text-4xl font-bold text-[var(--text-primary)] mb-4">Upgrade Your Health Intelligence</h1>
        <p className="text-lg max-w-2xl mx-auto text-[var(--text-dim)]">
          Unlock advanced ML models, priority consultations, and unlimited AI health context generation.
        </p>
      </div>

      {error && (
        <div className="mb-8 p-4 flex justify-center items-center gap-2 max-w-md mx-auto text-sm bg-[var(--danger-muted)] text-[var(--danger)] border border-[var(--danger-border)]" role="alert">
          <AlertCircle size={18} aria-hidden="true" /> {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto" role="list" aria-label="Pricing plans">
        {PLANS.map((plan, i) => (
          <motion.div 
            key={plan.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className={`panel p-8 flex flex-col relative ${plan.popular ? 'transform md:-translate-y-4 shadow-2xl border-t-4' : ''}`}
            style={plan.popular ? { borderTopColor: plan.color } : {}}
            role="listitem"
          >
            {plan.popular && (
              <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 px-3 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider text-white" style={{ background: plan.color }}>
                Most Popular
              </div>
            )}
            
            <div className="p-3 w-fit mb-6 border" style={{ backgroundColor: `color-mix(in srgb, ${plan.color} 10%, transparent)`, color: plan.color, borderColor: `color-mix(in srgb, ${plan.color} 20%, transparent)` }}>
              <plan.icon size={24} aria-hidden="true" />
            </div>
            
            <h3 className="text-xl font-bold text-[var(--text-primary)] mb-2">{plan.name}</h3>
            <div className="flex items-baseline gap-1 mb-6">
              <span className="text-4xl font-extrabold text-[var(--text-primary)]">{plan.price}</span>
              {plan.period && <span className="text-sm font-medium text-[var(--text-dim)]">{plan.period}</span>}
            </div>

            <ul className="space-y-4 mb-8 flex-1">
              {plan.features.map((feat, j) => (
                <li key={j} className="flex items-start gap-3 text-sm text-[var(--text-secondary)]">
                  <Check size={18} className="shrink-0 mt-0.5" style={{ color: plan.color }} aria-hidden="true" />
                  <span>{feat}</span>
                </li>
              ))}
            </ul>

            <button 
              onClick={() => handleUpgrade(plan)}
              disabled={loading === plan.id || plan.amount === 0}
              className={`w-full py-3 text-sm font-bold uppercase tracking-wider transition-colors ${plan.popular ? 'btn btn-primary' : 'btn btn-secondary'}`}
              aria-label={plan.amount === 0 ? "Current plan" : `Upgrade to ${plan.name}`}
            >
              {loading === plan.id ? "Processing..." : plan.amount === 0 ? "Current Plan" : "Upgrade Now"}
            </button>
          </motion.div>
        ))}
      </div>
      
      {/* Razorpay Script Injection */}
      <script src="https://checkout.razorpay.com/v1/checkout.js" async></script>
    </div>
  );
}
