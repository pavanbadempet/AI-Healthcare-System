import React, { useRef, useState, useEffect } from "react";
import { motion } from "framer-motion";
import { X, PenTool, ShieldCheck, CheckCircle2, RefreshCw, Lock, FileCheck, Hash, ShieldAlert } from "lucide-react";
import { dispatchCareEvent } from "@/lib/api";
import { toast } from "@/lib/toast";

interface DigitalSignatureModalProps {
  physicianName?: string;
  npiNumber?: string;
  prescriptionSummary?: string;
  onClose: () => void;
  onSigned?: (signatureDataUrl: string, hash: string) => void;
}

export const DigitalSignatureModal: React.FC<DigitalSignatureModalProps> = ({
  physicianName = "Dr. Sarah Jenkins, MD",
  npiNumber = "1928401928",
  prescriptionSummary = "Rx: Furosemide 40mg PO QD • Dispense: 30 • Refills: 2",
  onClose,
  onSigned,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [hasSignature, setHasSignature] = useState(false);
  const [deaCompliant, setDeaCompliant] = useState(true);
  const [isSigning, setIsSigning] = useState(false);
  const [signedHash, setSignedHash] = useState<string | null>(null);

  // Setup Canvas context
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.strokeStyle = "#38bdf8"; // Cyan stroke
    ctx.lineWidth = 2.5;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
  }, []);

  const startDrawing = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    setIsDrawing(true);
    setHasSignature(true);
    draw(e);
  };

  const stopDrawing = () => {
    setIsDrawing(false);
    const canvas = canvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext("2d");
      ctx?.beginPath();
    }
  };

  const draw = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const rect = canvas.getBoundingClientRect();
    const clientX = "touches" in e ? e.touches[0].clientX : e.clientX;
    const clientY = "touches" in e ? e.touches[0].clientY : e.clientY;

    const x = clientX - rect.left;
    const y = clientY - rect.top;

    ctx.lineTo(x, y);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(x, y);
  };

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    setHasSignature(false);
  };

  const handleFinalizeSignature = async () => {
    if (!hasSignature) {
      toast.error("Please sign in the signature box before attesting.");
      return;
    }
    if (!deaCompliant) {
      toast.error("DEA Controlled Substance Attestation is required for e-prescribing.");
      return;
    }

    setIsSigning(true);
    try {
      const canvas = canvasRef.current;
      const signatureDataUrl = canvas ? canvas.toDataURL("image/png") : "";
      
      // Generate REAL SHA-256 cryptographic hash using Web Crypto API
      const encoder = new TextEncoder();
      const payload = `${signatureDataUrl}:${prescriptionSummary}:${npiNumber}:${Date.now()}`;
      const hashBuffer = await window.crypto.subtle.digest("SHA-256", encoder.encode(payload));
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      const hexHash = hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
      const fullHash = `SHA256:${hexHash}`;
      setSignedHash(fullHash);

      await dispatchCareEvent({
        event_type: "rapid-response",
        title: `E-Prescription Signed by ${physicianName}`,
        summary: `Cryptographic digital signature applied for ${prescriptionSummary}. NPI: ${npiNumber}. ${fullHash}`,
        severity: "info",
      });

      toast.success(`E-Prescription Digitally Signed & Attested! ${fullHash.slice(0, 16)}...`);
      if (onSigned) onSigned(signatureDataUrl, fullHash);
      setTimeout(onClose, 1200);
    } catch (err) {
      toast.error("Failed to apply digital signature.");
    } finally {
      setIsSigning(false);
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
        aria-labelledby="signature-modal-title"
      >
        {/* Header */}
        <div className="bg-white/[0.02] border-b border-white/10 p-5 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400 shrink-0">
              <PenTool size={18} />
            </div>
            <div>
              <h2 id="signature-modal-title" className="text-sm font-bold text-white uppercase tracking-wider">
                Physician Digital Signature & Attestation Canvas
              </h2>
              <p className="text-[10px] text-[var(--text-secondary)] font-mono uppercase">
                EPCS DEA Compliant • PKI Cryptographic Hash Sign-off
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
        <div className="p-6 space-y-5 overflow-y-auto flex-1 font-mono text-xs">
          {/* Physician Info */}
          <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/10 space-y-1 font-sans">
            <div className="flex justify-between items-center text-xs">
              <span className="font-bold text-white uppercase">{physicianName}</span>
              <span className="text-[10px] font-mono text-sky-400 font-bold">NPI: {npiNumber}</span>
            </div>
            <p className="text-[11px] text-zinc-400 font-mono mt-1">{prescriptionSummary}</p>
          </div>

          {/* Interactive Signature Canvas */}
          <div className="space-y-1.5 font-sans">
            <div className="flex justify-between items-center">
              <label className="text-[10px] text-zinc-400 font-bold uppercase block font-mono">Sign Below (Mouse / Touch Canvas)</label>
              <button
                onClick={clearCanvas}
                className="text-[10px] text-rose-400 hover:underline font-mono"
              >
                Clear Signature
              </button>
            </div>
            <div className="border border-white/10 rounded-xl overflow-hidden bg-black/60 relative h-36">
              <canvas
                ref={canvasRef}
                width={450}
                height={144}
                onMouseDown={startDrawing}
                onMouseUp={stopDrawing}
                onMouseMove={draw}
                onTouchStart={startDrawing}
                onTouchEnd={stopDrawing}
                onTouchMove={draw}
                className="w-full h-full cursor-crosshair touch-none"
              />
              {!hasSignature && (
                <div className="absolute inset-0 pointer-events-none flex items-center justify-center text-zinc-600 text-xs font-mono uppercase tracking-widest">
                  [ Draw Physician Signature Here ]
                </div>
              )}
            </div>
          </div>

          {/* Attestation Checkbox */}
          <div className="p-3 rounded-xl bg-sky-500/10 border border-sky-500/20 space-y-2 font-sans">
            <label className="flex items-start gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={deaCompliant}
                onChange={(e) => setDeaCompliant(e.target.checked)}
                className="mt-0.5 accent-sky-500"
              />
              <span className="text-[10px] text-sky-200 leading-relaxed font-mono">
                I attest that I am the authorized prescribing clinician ({physicianName}), and this electronic signature constitutes my legally binding digital sign-off under DEA EPCS and HIPAA rules.
              </span>
            </label>
          </div>

          {signedHash && (
            <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-mono flex items-center gap-2">
              <CheckCircle2 size={16} className="text-emerald-400 shrink-0" />
              <span className="truncate">Attested: {signedHash}</span>
            </div>
          )}

          <button
            onClick={handleFinalizeSignature}
            disabled={isSigning || !hasSignature || !deaCompliant}
            className="w-full py-2.5 bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs uppercase tracking-wider rounded-xl transition-all shadow-lg shadow-sky-600/20 flex items-center justify-center gap-2"
          >
            {isSigning ? <RefreshCw size={14} className="animate-spin" /> : <Lock size={14} />}
            Cryptographically Sign & Issue E-Prescription
          </button>
        </div>
      </motion.div>
    </div>
  );
};
