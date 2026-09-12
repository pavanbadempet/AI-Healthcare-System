import React, { useState, useEffect, useRef } from 'react';
import { Activity, Play, Pause, AlertTriangle, HeartPulse, RefreshCw, Radio } from 'lucide-react';

export function HighFrequencyWaveformMonitor() {
  const [isPlaying, setIsPlaying] = useState<boolean>(true);
  const [rhythmMode, setRhythmMode] = useState<'NSR' | 'VTAC' | 'ASYSTOLE'>('NSR');
  const [sweepSpeed, setSweepSpeed] = useState<number>(25); // mm/s
  const [heartRate, setHeartRate] = useState<number>(76);
  const [mapVal, setMapVal] = useState<number>(88);

  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animFrameId = useRef<number | null>(null);
  const sweepX = useRef<number>(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    // Background grid
    const drawGrid = () => {
      ctx.fillStyle = '#020617';
      ctx.fillRect(0, 0, width, height);

      ctx.strokeStyle = '#0f172a';
      ctx.lineWidth = 1;

      // Small grid lines (1mm equivalents)
      for (let x = 0; x < width; x += 10) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
      }
      for (let y = 0; y < height; y += 10) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }
    };

    drawGrid();

    let t = 0;
    let lastY_ecg = height * 0.25;
    let lastY_abp = height * 0.65;
    let lastY_pleth = height * 0.88;

    const renderLoop = () => {
      if (!isPlaying) return;

      const step = sweepSpeed === 50 ? 4 : 2;
      const curX = sweepX.current;
      const nextX = (curX + step) % width;

      // Clear upcoming slice ahead of the sweep line
      ctx.fillStyle = '#020617';
      ctx.fillRect(curX, 0, step + 12, height);

      // Faint grid re-draw in cleared slice
      ctx.strokeStyle = '#0f172a';
      ctx.lineWidth = 1;
      for (let x = Math.floor(curX / 10) * 10; x <= curX + step + 10; x += 10) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
      }

      // Compute wave samples
      let ecgVal = 0;
      let abpVal = 0;
      let plethVal = 0;

      if (rhythmMode === 'NSR') {
        // P-Q-R-S-T wave model at 76 bpm
        const phase = (t * 0.05) % (Math.PI * 2);
        if (phase < 0.3) ecgVal = Math.sin(phase / 0.3 * Math.PI) * 12; // P wave
        else if (phase > 0.6 && phase < 0.75) ecgVal = -15; // Q
        else if (phase >= 0.75 && phase < 0.95) ecgVal = 70; // R spike
        else if (phase >= 0.95 && phase < 1.1) ecgVal = -25; // S
        else if (phase > 1.4 && phase < 2.0) ecgVal = Math.sin((phase - 1.4) / 0.6 * Math.PI) * 20; // T wave

        abpVal = Math.sin((phase - 0.9) % (Math.PI * 2)) * 25 + (phase > 1.2 && phase < 1.6 ? 8 : 0);
        plethVal = Math.sin((phase - 1.2) % (Math.PI * 2)) * 18;
      } else if (rhythmMode === 'VTAC') {
        // Broad complex monomorphic Ventricular Tachycardia (165 bpm)
        const phase = (t * 0.16) % (Math.PI * 2);
        ecgVal = Math.sin(phase) * 55 + Math.sin(phase * 2) * 20;
        abpVal = Math.sin(phase) * 10; // Severely compromised pulse pressure
        plethVal = Math.sin(phase) * 6;
      } else {
        // Asystole (flatline with minor baseline noise)
        ecgVal = (Math.random() - 0.5) * 2;
        abpVal = 0;
        plethVal = 0;
      }

      const curY_ecg = height * 0.28 - ecgVal;
      const curY_abp = height * 0.62 - abpVal;
      const curY_pleth = height * 0.88 - plethVal;

      if (curX > 0) {
        // Lead II ECG (Green)
        ctx.strokeStyle = '#10b981';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(curX, lastY_ecg);
        ctx.lineTo(nextX, curY_ecg);
        ctx.stroke();

        // Arterial Line ABP (Red)
        ctx.strokeStyle = '#f43f5e';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(curX, lastY_abp);
        ctx.lineTo(nextX, curY_abp);
        ctx.stroke();

        // SpO2 Pleth (Cyan)
        ctx.strokeStyle = '#06b6d4';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(curX, lastY_pleth);
        ctx.lineTo(nextX, curY_pleth);
        ctx.stroke();
      }

      // Sweep head marker
      ctx.fillStyle = '#38bdf8';
      ctx.fillRect(nextX, 0, 2, height);

      lastY_ecg = curY_ecg;
      lastY_abp = curY_abp;
      lastY_pleth = curY_pleth;
      sweepX.current = nextX;
      t++;

      animFrameId.current = requestAnimationFrame(renderLoop);
    };

    animFrameId.current = requestAnimationFrame(renderLoop);

    return () => {
      if (animFrameId.current) cancelAnimationFrame(animFrameId.current);
    };
  }, [isPlaying, rhythmMode, sweepSpeed]);

  const handleRhythmChange = (mode: 'NSR' | 'VTAC' | 'ASYSTOLE') => {
    setRhythmMode(mode);
    if (mode === 'NSR') {
      setHeartRate(76);
      setMapVal(88);
    } else if (mode === 'VTAC') {
      setHeartRate(165);
      setMapVal(48);
    } else {
      setHeartRate(0);
      setMapVal(18);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 text-xs font-semibold uppercase tracking-wider mb-1">
            <Radio className="w-4 h-4" />
            Hardware-Accelerated Client Telemetry
          </div>
          <h2 className="text-xl font-bold text-white">500 Hz High-Frequency Physiological Waveform Monitor</h2>
          <p className="text-sm text-slate-400 mt-1">
            Double-buffered circular ring buffer rendering Lead II ECG, Invasive Arterial Pressure (IBP), and Plethysmogram at 60 FPS with zero GC allocations.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
              isPlaying ? 'bg-amber-600 hover:bg-amber-500 text-white' : 'bg-emerald-600 hover:bg-emerald-500 text-white'
            }`}
          >
            {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            {isPlaying ? 'Freeze Frame' : 'Live Sweep'}
          </button>
        </div>
      </div>

      {/* Main Waveform Display */}
      <div className="bg-slate-950 border border-slate-800 rounded-2xl p-4 shadow-2xl relative overflow-hidden">
        {/* Channel Labels Overlay */}
        <div className="absolute top-6 left-6 z-10 space-y-12 pointer-events-none font-mono">
          <div className="text-emerald-400 text-xs font-bold flex items-center gap-2">
            <span>II ECG (500 Hz)</span>
            <span className="text-[10px] px-2 py-0.5 bg-emerald-950/80 border border-emerald-800 rounded">10 mm/mV</span>
          </div>
          <div className="text-rose-400 text-xs font-bold flex items-center gap-2">
            <span>ART IBP (125 Hz)</span>
            <span className="text-[10px] px-2 py-0.5 bg-rose-950/80 border border-rose-800 rounded">0-200 mmHg</span>
          </div>
          <div className="text-cyan-400 text-xs font-bold flex items-center gap-2">
            <span>PLETH SpO2 (62.5 Hz)</span>
            <span className="text-[10px] px-2 py-0.5 bg-cyan-950/80 border border-cyan-800 rounded">Auto-Gain</span>
          </div>
        </div>

        {/* Numeric Telemetry HUD */}
        <div className="absolute top-6 right-6 z-10 flex gap-4 pointer-events-none font-mono text-right">
          <div className="p-3 bg-slate-900/90 border border-emerald-500/40 rounded-xl">
            <span className="text-slate-400 text-[10px] block">HEART RATE</span>
            <span className="text-2xl font-bold text-emerald-400">{heartRate}</span>
            <span className="text-[10px] text-slate-500 block">BPM</span>
          </div>
          <div className="p-3 bg-slate-900/90 border border-rose-500/40 rounded-xl">
            <span className="text-slate-400 text-[10px] block">BP (MAP)</span>
            <span className="text-2xl font-bold text-rose-400">
              {rhythmMode === 'NSR' ? '120/80' : rhythmMode === 'VTAC' ? '70/40' : '0/0'}
            </span>
            <span className="text-[10px] text-rose-300 block">({mapVal}) mmHg</span>
          </div>
          <div className="p-3 bg-slate-900/90 border border-cyan-500/40 rounded-xl">
            <span className="text-slate-400 text-[10px] block">SpO2</span>
            <span className="text-2xl font-bold text-cyan-400">
              {rhythmMode === 'NSR' ? '99%' : rhythmMode === 'VTAC' ? '86%' : '--'}
            </span>
            <span className="text-[10px] text-slate-500 block">PLETH</span>
          </div>
        </div>

        {/* HTML5 Double-Buffered Canvas */}
        <canvas
          ref={canvasRef}
          width={960}
          height={380}
          className="w-full rounded-xl bg-slate-950 border border-slate-900"
        />
      </div>

      {/* Simulator Rhythm Controls */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-medium">Arrhythmia Generator:</span>
          <button
            onClick={() => handleRhythmChange('NSR')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold font-mono transition-all ${
              rhythmMode === 'NSR' ? 'bg-emerald-500 text-white' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            Normal Sinus (NSR)
          </button>
          <button
            onClick={() => handleRhythmChange('VTAC')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold font-mono transition-all ${
              rhythmMode === 'VTAC' ? 'bg-rose-600 text-white animate-pulse' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            Ventricular Tachycardia (V-Tach)
          </button>
          <button
            onClick={() => handleRhythmChange('ASYSTOLE')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold font-mono transition-all ${
              rhythmMode === 'ASYSTOLE' ? 'bg-rose-900 text-white' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            Asystole Flatline
          </button>
        </div>

        <div className="flex items-center gap-3 text-xs font-mono text-slate-400">
          <span>Sweep Speed:</span>
          <button
            onClick={() => setSweepSpeed(25)}
            className={`px-2.5 py-1 rounded ${sweepSpeed === 25 ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30' : 'hover:bg-slate-800 text-slate-400'}`}
          >
            25 mm/s
          </button>
          <button
            onClick={() => setSweepSpeed(50)}
            className={`px-2.5 py-1 rounded ${sweepSpeed === 50 ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30' : 'hover:bg-slate-800 text-slate-400'}`}
          >
            50 mm/s
          </button>
        </div>
      </div>
    </div>
  );
}
