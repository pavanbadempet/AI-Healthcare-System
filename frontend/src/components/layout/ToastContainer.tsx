import { useToastStore } from "@/lib/toast";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, AlertTriangle, AlertCircle, Info, X } from "lucide-react";

export default function ToastContainer() {
  const toasts = useToastStore((state) => state.toasts);
  const removeToast = useToastStore((state) => state.removeToast);

  return (
    <div className="fixed bottom-6 left-6 z-[9999] flex flex-col gap-2 max-w-sm pointer-events-none">
      <AnimatePresence>
        {toasts.map((t) => {
          const Icon =
            t.type === "success"
              ? CheckCircle2
              : t.type === "error"
              ? AlertCircle
              : t.type === "warning"
              ? AlertTriangle
              : Info;

          const theme =
            t.type === "success"
              ? { border: "border-emerald-500/30", bg: "bg-emerald-950/90", text: "text-emerald-400" }
              : t.type === "error"
              ? { border: "border-rose-500/30", bg: "bg-rose-950/90", text: "text-rose-400" }
              : t.type === "warning"
              ? { border: "border-amber-500/30", bg: "bg-amber-950/90", text: "text-amber-400" }
              : { border: "border-blue-500/30", bg: "bg-blue-950/90", text: "text-blue-400" };

          return (
            <motion.div
              key={t.id}
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: -20 }}
              className={`pointer-events-auto flex items-start gap-3 p-4 rounded-xl border ${theme.border} ${theme.bg} backdrop-blur-2xl shadow-[0_20px_40px_rgba(0,0,0,0.6)] min-w-[280px] max-w-sm`}
            >
              <Icon className={`${theme.text} shrink-0 mt-0.5`} size={16} />
              <div className="flex-1 min-w-0">
                <p className="text-xs font-bold text-white/90 leading-relaxed font-sans">
                  {t.message}
                </p>
              </div>
              <button
                onClick={() => removeToast(t.id)}
                className="text-white/40 hover:text-white/80 transition-colors shrink-0 cursor-pointer"
              >
                <X size={14} />
              </button>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
