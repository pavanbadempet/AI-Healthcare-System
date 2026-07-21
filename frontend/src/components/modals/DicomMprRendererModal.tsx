import React, { useState } from "react";
import { motion } from "framer-motion";
import { X, Layers, Box, Eye, Sliders, RefreshCw, Activity, Sparkles, CheckCircle2 } from "lucide-react";
import { dispatchCareEvent } from "@/lib/api";
import { toast } from "@/lib/toast";

interface DicomMprRendererModalProps {
  patientName?: string;
  mrn?: string;
  onClose: () => void;
}

export const DicomMprRendererModal: React.FC<DicomMprRendererModalProps> = ({
  patientName = "Marcus Thorne",
  mrn = "MRN-123456",
  onClose,
}) => {
  const [sliceAxial, setSliceAxial] = useState(64);
  const [sliceSagittal, setSliceSagittal] = useState(32);
  const [sliceCoronal, setSliceCoronal] = useState(32);
  const [windowPreset, setWindowPreset] = useState<"SOFT_TISSUE" | "LUNG" | "BONE" | "MIP">("SOFT_TISSUE");
  const [isProcessing, setIsProcessing] = useState(false);

  const handleReconstructVolume = async () => {
    setIsProcessing(true);
    await new Promise((r) => setTimeout(r, 600));
    setIsProcessing(false);

    await dispatchCareEvent({
      event_type: "rapid-response",
      title: `3D MPR Reconstruction Processed: ${patientName}`,
      summary: `Generated 3D Multi-Planar Reconstruction (Axial: ${sliceAxial}, Sagittal: ${sliceSagittal}, Coronal: ${sliceCoronal}) with ${windowPreset} preset for ${patientName}.`,
      severity: "info",
    });

    toast.success("3D Volumetric Multi-Planar Reconstruction (MPR) successfully generated!");
  };

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/80 backdrop-blur-md p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 15 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 15 }}
        className="bg-[#0b0c10] border border-white/10 rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col shadow-2xl font-sans"
        role="dialog"
        aria-modal="true"
        aria-labelledby="mpr-modal-title"
      >
        {/* Header */}
        <div className="bg-white/[0.02] border-b border-white/10 p-5 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 shrink-0">
              <Layers size={18} />
            </div>
            <div>
              <h2 id="mpr-modal-title" className="text-sm font-bold text-white uppercase tracking-wider">
                3D Volumetric DICOM Multi-Planar Reconstruction (MPR) Renderer
              </h2>
              <p className="text-[10px] text-[var(--text-secondary)] font-mono uppercase">
                Tri-Planar Synchronized Crosshair • Patient: {patientName} ({mrn})
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

        {/* Content Controls & 4-Viewport Grid */}
        <div className="p-6 space-y-4 overflow-y-auto flex-1 font-mono text-xs">
          {/* Top Controls Toolbar */}
          <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-xl bg-white/[0.02] border border-white/10 font-sans">
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-zinc-400 font-bold uppercase font-mono">W/L Preset:</span>
              <select
                value={windowPreset}
                onChange={(e) => setWindowPreset(e.target.value as any)}
                className="bg-zinc-900 border border-white/10 rounded-lg px-2.5 py-1 text-xs text-purple-300 font-mono font-bold"
              >
                <option value="SOFT_TISSUE">Abdomen / Soft Tissue (W:400, L:40)</option>
                <option value="LUNG">Thoracic Lung Window (W:1500, L:-600)</option>
                <option value="BONE">Skeletal Bone Window (W:2000, L:300)</option>
                <option value="MIP">Angiography MIP (Max Intensity Projection)</option>
              </select>
            </div>

            <button
              onClick={handleReconstructVolume}
              disabled={isProcessing}
              className="px-4 py-1.5 bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs uppercase tracking-wider rounded-lg transition-all shadow-lg shadow-purple-600/20 flex items-center gap-1.5"
            >
              {isProcessing ? <RefreshCw size={14} className="animate-spin" /> : <Sparkles size={14} />}
              Recompute 3D Raycast Volume
            </button>
          </div>

          {/* 4-Viewport Tri-Planar Grid */}
          <div className="grid grid-cols-2 gap-3 h-[380px]">
            {/* Viewport 1: Axial */}
            <div className="border border-white/10 rounded-xl bg-black overflow-hidden flex flex-col relative">
              <div className="px-3 py-1.5 bg-zinc-900/80 border-b border-white/10 flex justify-between text-[10px] text-purple-400 font-bold">
                <span>AXIAL VIEWPORT (Z-AXIS)</span>
                <span>Slice {sliceAxial}/128</span>
              </div>
              <div className="flex-1 bg-zinc-950 flex items-center justify-center relative overflow-hidden">
                <div className="w-40 h-40 rounded-full border-2 border-purple-500/40 bg-purple-950/20 flex items-center justify-center text-[10px] text-purple-300 font-bold">
                  [ AXIAL CROSS SECTION ]
                </div>
                {/* Crosshairs */}
                <div className="absolute inset-x-0 top-1/2 border-b border-purple-500/30 pointer-events-none" />
                <div className="absolute inset-y-0 left-1/2 border-r border-purple-500/30 pointer-events-none" />
              </div>
              <div className="p-2 bg-zinc-900/40 border-t border-white/10">
                <input
                  type="range"
                  min={1}
                  max={128}
                  value={sliceAxial}
                  onChange={(e) => setSliceAxial(Number(e.target.value))}
                  className="w-full accent-purple-500 h-1"
                />
              </div>
            </div>

            {/* Viewport 2: Sagittal */}
            <div className="border border-white/10 rounded-xl bg-black overflow-hidden flex flex-col relative">
              <div className="px-3 py-1.5 bg-zinc-900/80 border-b border-white/10 flex justify-between text-[10px] text-cyan-400 font-bold">
                <span>SAGITTAL VIEWPORT (X-AXIS)</span>
                <span>Slice {sliceSagittal}/64</span>
              </div>
              <div className="flex-1 bg-zinc-950 flex items-center justify-center relative overflow-hidden">
                <div className="w-36 h-44 rounded border-2 border-cyan-500/40 bg-cyan-950/20 flex items-center justify-center text-[10px] text-cyan-300 font-bold">
                  [ SAGITTAL LATERAL PROFILE ]
                </div>
                {/* Crosshairs */}
                <div className="absolute inset-x-0 top-1/2 border-b border-cyan-500/30 pointer-events-none" />
                <div className="absolute inset-y-0 left-1/2 border-r border-cyan-500/30 pointer-events-none" />
              </div>
              <div className="p-2 bg-zinc-900/40 border-t border-white/10">
                <input
                  type="range"
                  min={1}
                  max={64}
                  value={sliceSagittal}
                  onChange={(e) => setSliceSagittal(Number(e.target.value))}
                  className="w-full accent-cyan-500 h-1"
                />
              </div>
            </div>

            {/* Viewport 3: Coronal */}
            <div className="border border-white/10 rounded-xl bg-black overflow-hidden flex flex-col relative">
              <div className="px-3 py-1.5 bg-zinc-900/80 border-b border-white/10 flex justify-between text-[10px] text-emerald-400 font-bold">
                <span>CORONAL VIEWPORT (Y-AXIS)</span>
                <span>Slice {sliceCoronal}/64</span>
              </div>
              <div className="flex-1 bg-zinc-950 flex items-center justify-center relative overflow-hidden">
                <div className="w-40 h-36 rounded border-2 border-emerald-500/40 bg-emerald-950/20 flex items-center justify-center text-[10px] text-emerald-300 font-bold">
                  [ CORONAL FRONTAL PLANE ]
                </div>
                {/* Crosshairs */}
                <div className="absolute inset-x-0 top-1/2 border-b border-emerald-500/30 pointer-events-none" />
                <div className="absolute inset-y-0 left-1/2 border-r border-emerald-500/30 pointer-events-none" />
              </div>
              <div className="p-2 bg-zinc-900/40 border-t border-white/10">
                <input
                  type="range"
                  min={1}
                  max={64}
                  value={sliceCoronal}
                  onChange={(e) => setSliceCoronal(Number(e.target.value))}
                  className="w-full accent-emerald-500 h-1"
                />
              </div>
            </div>

            {/* Viewport 4: 3D Volumetric Mesh */}
            <div className="border border-white/10 rounded-xl bg-black overflow-hidden flex flex-col relative">
              <div className="px-3 py-1.5 bg-zinc-900/80 border-b border-white/10 flex justify-between text-[10px] text-amber-400 font-bold">
                <span>3D RAYCASTING VOLUME MESH</span>
                <span>ISO-SURFACE ACTIVE</span>
              </div>
              <div className="flex-1 bg-zinc-950 flex items-center justify-center relative overflow-hidden">
                <div className="w-40 h-40 rounded-2xl border-2 border-amber-500/40 bg-amber-950/20 flex flex-col items-center justify-center text-[10px] text-amber-300 font-bold gap-1 animate-pulse">
                  <Box size={28} />
                  <span>[ 3D VOLUME MESH ]</span>
                </div>
              </div>
              <div className="p-2 bg-zinc-900/40 border-t border-white/10 text-[9px] text-zinc-400 text-center uppercase">
                Interactive 3D Iso-surface Raycasting Active
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="bg-white/[0.02] border-t border-white/10 p-4 flex items-center justify-between font-sans">
          <button
            onClick={onClose}
            className="btn btn-secondary text-xs uppercase font-bold tracking-wide py-2.5 px-4"
          >
            Close 3D MPR Renderer
          </button>
        </div>
      </motion.div>
    </div>
  );
};
