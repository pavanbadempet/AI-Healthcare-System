import React, { useState } from "react";
import { motion } from "framer-motion";
import { X, Package, Truck, CheckCircle2, Clock, MapPin, Send, AlertTriangle, ShieldCheck } from "lucide-react";
import { dispatchCareEvent } from "@/lib/api";
import { toast } from "@/lib/toast";

interface HomeDiagnosticKitModalProps {
  patientId?: number | string;
  patientName?: string;
  onClose: () => void;
  onOrderSuccess?: (trackingId: string) => void;
}

export const HomeDiagnosticKitModal: React.FC<HomeDiagnosticKitModalProps> = ({
  patientId = 1,
  patientName = "Marcus Thorne",
  onClose,
  onOrderSuccess,
}) => {
  const [kitType, setKitType] = useState("cgm");
  const [courier, setCourier] = useState("fedex");
  const [isPriority, setIsPriority] = useState(true);
  const [shippingAddress, setShippingAddress] = useState("742 Evergreen Terrace, Sector 4, Metro Medical Zone");
  const [specialInstructions, setSpecialInstructions] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const kitOptions: Record<string, { name: string; desc: string; icon: string }> = {
    cgm: { name: "Continuous Glucose Monitor (CGM) Pack", desc: "14-day continuous subcutaneous interstitial glucose sensor with Bluetooth sync.", icon: "🩺" },
    ecg: { name: "12-Lead Wireless Patch ECG Monitor", desc: "Wearable continuous arrhythmia patch with automated QTc interval logging.", icon: "🫀" },
    oximeter: { name: "Remote Spirometer & Oximeter Kit", desc: "Digital peak-flow meter & SpO2 sensor with cellular baseline upload.", icon: "🫁" },
    abpm: { name: "Ambulatory Blood Pressure Monitor (ABPM)", desc: "24-hour cuff-based blood pressure logger with nocturnal dipping analytics.", icon: "🩸" },
  };

  const handleOrderSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    const trackingId = `TRK-${courier.toUpperCase()}-${Math.floor(100000 + Math.random() * 900000)}-CLINICAL`;
    const selectedKit = kitOptions[kitType];

    try {
      await dispatchCareEvent({
        event_type: "rapid-response",
        title: `Home Diagnostic Kit Dispatched: ${selectedKit.name}`,
        summary: `Dispatched ${selectedKit.name} to ${patientName} via ${courier.toUpperCase()} Priority (${trackingId}). Address: ${shippingAddress}.`,
        severity: "info",
      });

      toast.success(`Home Diagnostic Kit ordered for ${patientName}! Tracking: ${trackingId}`);
      if (onOrderSuccess) onOrderSuccess(trackingId);
      onClose();
    } catch (err) {
      toast.error("Failed to process diagnostic kit order.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/80 backdrop-blur-md p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 15 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 15 }}
        className="bg-[#0b0c10] border border-white/10 rounded-2xl w-full max-w-lg max-h-[90vh] overflow-hidden flex flex-col shadow-2xl font-sans"
        role="dialog"
        aria-modal="true"
        aria-labelledby="kit-modal-title"
      >
        {/* Header */}
        <div className="bg-white/[0.02] border-b border-white/10 p-5 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 shrink-0">
              <Package size={18} />
            </div>
            <div>
              <h2 id="kit-modal-title" className="text-sm font-bold text-white uppercase tracking-wider">
                Remote Home Diagnostic Kit Dispatch
              </h2>
              <p className="text-[10px] text-[var(--text-secondary)] font-mono uppercase">
                Patient: {patientName} • MRN #{patientId}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-zinc-400 hover:text-white p-1.5 rounded-lg hover:bg-white/5 transition-colors"
            aria-label="Close modal"
          >
            <X size={18} />
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleOrderSubmit} className="p-6 space-y-4 font-mono text-xs overflow-y-auto flex-1">
          {/* Kit Type Selection */}
          <div className="space-y-1.5 font-sans">
            <label className="text-[10px] text-zinc-400 font-bold uppercase block font-mono">Select Diagnostic Hardware Kit</label>
            <div className="space-y-2">
              {Object.entries(kitOptions).map(([key, item]) => (
                <div
                  key={key}
                  onClick={() => setKitType(key)}
                  className={`p-3 rounded-xl border transition-all cursor-pointer flex items-start gap-3 ${
                    kitType === key
                      ? "bg-cyan-500/10 border-cyan-500/50 shadow-md"
                      : "bg-white/[0.02] border-white/5 hover:border-white/10"
                  }`}
                >
                  <span className="text-lg shrink-0">{item.icon}</span>
                  <div>
                    <div className="text-xs font-bold text-white uppercase font-sans">{item.name}</div>
                    <div className="text-[10px] text-zinc-400 font-mono mt-0.5 leading-relaxed">{item.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Courier & Priority */}
          <div className="grid grid-cols-2 gap-3 font-sans">
            <div>
              <label className="text-[10px] text-zinc-400 font-bold uppercase block font-mono mb-1">Medical Courier Partner</label>
              <select
                value={courier}
                onChange={(e) => setCourier(e.target.value)}
                className="w-full bg-zinc-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-cyan-500"
              >
                <option value="fedex">FedEx Clinical Priority</option>
                <option value="dhl">DHL Express Healthcare</option>
                <option value="ups">UPS Next Day Air Medical</option>
              </select>
            </div>

            <div>
              <label className="text-[10px] text-zinc-400 font-bold uppercase block font-mono mb-1">Delivery Priority</label>
              <button
                type="button"
                onClick={() => setIsPriority(!isPriority)}
                className={`w-full py-2 px-3 rounded-xl text-xs font-bold font-mono border transition-all flex items-center justify-center gap-1.5 ${
                  isPriority
                    ? "bg-amber-500/20 border-amber-500 text-amber-300"
                    : "bg-white/[0.02] border-white/10 text-zinc-400"
                }`}
              >
                <Truck size={13} /> {isPriority ? "Overnight Priority" : "Standard 2-Day"}
              </button>
            </div>
          </div>

          {/* Shipping Address */}
          <div className="space-y-1.5 font-sans">
            <label className="text-[10px] text-zinc-400 font-bold uppercase block font-mono flex items-center gap-1">
              <MapPin size={11} className="text-cyan-400" /> Destination Shipping Address
            </label>
            <textarea
              rows={2}
              value={shippingAddress}
              onChange={(e) => setShippingAddress(e.target.value)}
              className="w-full bg-white/[0.03] border border-white/10 rounded-xl p-2.5 text-xs text-white font-mono focus:outline-none focus:border-cyan-500 resize-none"
            />
          </div>

          {/* Footer */}
          <div className="pt-2 flex items-center justify-between font-sans border-t border-white/10">
            <button
              type="button"
              onClick={onClose}
              className="btn btn-secondary text-xs uppercase font-bold tracking-wide py-2.5 px-4"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="btn bg-cyan-600 hover:bg-cyan-500 text-white text-xs uppercase font-bold tracking-wide py-2.5 px-5 flex items-center gap-2 rounded-xl shadow-lg shadow-cyan-600/20 disabled:opacity-50"
            >
              <Send size={14} /> {isSubmitting ? "Dispatching..." : "Confirm & Dispatch Kit"}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  );
};
