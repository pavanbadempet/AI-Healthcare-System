import React, { useState } from 'react';
import { Layers, Box, Eye, ZoomIn, RefreshCw } from 'lucide-react';

interface Dicom3dMprViewerProps {
  studyInstanceUid?: string;
  seriesInstanceUid?: string;
}

export const Dicom3dMprViewer: React.FC<Dicom3dMprViewerProps> = ({
  studyInstanceUid = '1.2.840.113619.2.55.3.42710189',
  seriesInstanceUid = '1.2.840.113619.2.55.3.42710189.1',
}) => {
  const [activePlane, setActivePlane] = useState<'axial' | 'sagittal' | 'coronal' | '3d'>('axial');
  const [windowLevel, setWindowLevel] = useState<number>(40);
  const [windowWidth, setWindowWidth] = useState<number>(400);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-xl">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
        <div className="flex items-center gap-2">
          <Layers className="w-5 h-5 text-cyan-400" />
          <h3 className="text-sm font-semibold text-slate-100">
            3D DICOM WebGL Volumetric PACS (MPR Viewer)
          </h3>
        </div>
        <span className="text-xs px-2.5 py-1 rounded-full bg-cyan-500/10 text-cyan-400 font-mono border border-cyan-500/20">
          DICOMweb QIDO-RS / WADO-RS
        </span>
      </div>

      {/* Plane Select Controls */}
      <div className="flex items-center gap-2 mb-4">
        {(['axial', 'sagittal', 'coronal', '3d'] as const).map((plane) => (
          <button
            key={plane}
            onClick={() => setActivePlane(plane)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-all ${
              activePlane === plane
                ? 'bg-cyan-500 text-slate-950 font-semibold shadow-lg shadow-cyan-500/20'
                : 'bg-slate-800/80 text-slate-400 hover:text-slate-200'
            }`}
          >
            {plane === '3d' ? '3D Volume Mesh' : `${plane} View`}
          </button>
        ))}
      </div>

      {/* Volumetric Render Canvas Simulation */}
      <div className="relative aspect-video bg-slate-950 rounded-lg border border-slate-800/80 flex items-center justify-center overflow-hidden group">
        <div className="absolute inset-0 bg-gradient-to-tr from-cyan-950/20 via-transparent to-slate-900/40" />

        {/* Axis Marker */}
        <div className="absolute top-3 left-3 flex flex-col gap-1 text-[10px] font-mono text-slate-400 bg-slate-900/80 p-2 rounded border border-slate-800">
          <div>Series: {seriesInstanceUid.slice(-12)}</div>
          <div>Plane: {activePlane.toUpperCase()}</div>
          <div>W: {windowWidth} L: {windowLevel}</div>
        </div>

        <div className="text-center z-10 p-6">
          <Box className="w-12 h-12 text-cyan-400 mx-auto mb-2 animate-pulse" />
          <div className="text-xs font-medium text-slate-200">
            {activePlane === '3d' ? '3D Volumetric Mesh Render' : `Multi-Planar Slice (${activePlane.toUpperCase()})`}
          </div>
          <div className="text-[11px] text-slate-500 mt-1 font-mono">
            High-Resolution DICOM Slice Rendering • WebGL Acceleration Active
          </div>
        </div>

        {/* Interactive Controls Overlay */}
        <div className="absolute bottom-3 right-3 flex items-center gap-2">
          <button
            onClick={() => {
              setWindowWidth(400);
              setWindowLevel(40);
            }}
            className="p-1.5 rounded bg-slate-900 text-slate-400 hover:text-slate-100 border border-slate-800"
            title="Reset Window/Level"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
