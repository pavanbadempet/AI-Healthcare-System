import React, { useState } from "react";
import { Layers, RotateCw, ZoomIn, Eye, Activity, ShieldCheck } from "lucide-react";

interface Dicom3DViewerProps {
  patientId?: string;
  scanType?: string;
}

export const Dicom3DViewer: React.FC<Dicom3DViewerProps> = ({
  patientId = "PATIENT-CT-9921",
  scanType = "Chest CT (Multi-Slice Volumetric)"
}) => {
  const [sliceIndex, setSliceIndex] = useState(24);
  const [rotation, setRotation] = useState(0);
  const [contrast, setContrast] = useState(100);

  return (
    <div className="glass-card p-6 rounded-2xl border border-white/[0.06] bg-[rgba(10,10,20,0.6)] space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/[0.06] pb-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-[var(--accent-purple)]/20 border border-[var(--accent-purple)]/40 flex items-center justify-center text-[var(--accent-purple)]">
            <Layers size={18} />
          </div>
          <div>
            <h3 className="text-sm font-bold text-[var(--text-primary)] uppercase tracking-wider">
              3D Volumetric DICOM Viewport
            </h3>
            <p className="text-[10px] text-[var(--text-dim)] font-mono">
              {patientId} — {scanType}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-2 py-1 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[9px] font-mono uppercase font-bold flex items-center gap-1">
            <ShieldCheck size={10} /> WebGL 3D Active
          </span>
        </div>
      </div>

      {/* Main 3D Canvas / Viewport */}
      <div className="relative w-full h-64 bg-black rounded-xl border border-white/[0.08] flex items-center justify-center overflow-hidden group">
        {/* Animated Scan Line */}
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[var(--accent)]/10 to-transparent pointer-events-none animate-pulse" />

        {/* 3D Scan Visual Simulation */}
        <div
          className="relative transition-transform duration-300 flex items-center justify-center"
          style={{ transform: `rotate(${rotation}deg)` }}
        >
          <div
            className="w-44 h-44 rounded-full border-4 border-dashed border-[var(--accent-cyan)]/40 flex items-center justify-center relative"
            style={{ filter: `contrast(${contrast}%)` }}
          >
            <div className="w-32 h-32 rounded-full bg-gradient-to-tr from-[var(--accent-purple)]/30 to-[var(--accent)]/30 blur-sm flex items-center justify-center">
              <Activity size={32} className="text-[var(--accent-cyan)] opacity-75" />
            </div>
            <span className="absolute bottom-2 text-[9px] font-mono text-[var(--text-secondary)] font-bold">
              Slice {sliceIndex}/64
            </span>
          </div>
        </div>

        {/* Floating Controls Overlay */}
        <div className="absolute bottom-3 right-3 flex items-center gap-2 bg-black/70 backdrop-blur-md px-3 py-1.5 rounded-lg border border-white/10">
          <button
            onClick={() => setRotation((r) => (r + 90) % 360)}
            className="p-1 text-[var(--text-secondary)] hover:text-white transition-colors"
            title="Rotate 90°"
          >
            <RotateCw size={14} />
          </button>
          <button
            onClick={() => setContrast((c) => (c === 100 ? 150 : 100))}
            className="p-1 text-[var(--text-secondary)] hover:text-white transition-colors"
            title="Toggle Contrast"
          >
            <Eye size={14} />
          </button>
        </div>
      </div>

      {/* Slice Slider Controls */}
      <div className="space-y-2 pt-1">
        <div className="flex justify-between text-[10px] font-mono text-[var(--text-secondary)]">
          <span>Axial Slice Depth</span>
          <span className="font-bold text-[var(--accent-cyan)]">Slice #{sliceIndex} of 64</span>
        </div>
        <input
          type="range"
          min="1"
          max="64"
          value={sliceIndex}
          onChange={(e) => setSliceIndex(parseInt(e.target.value))}
          className="w-full h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer accent-[var(--accent-cyan)]"
        />
      </div>
    </div>
  );
};
