import React, { useEffect, useState } from 'react';
import { Activity, Heart, Zap, RefreshCw } from 'lucide-react';

interface PatientTelemetry {
  patientId: number;
  name: string;
  heartRate: number;
  bpSystolic: number;
  bpDiastolic: number;
  oxygenSat: number;
  status: 'STABLE' | 'WARNING' | 'CRITICAL';
}

export const LiveVitalsStreamViewer: React.FC = () => {
  const [telemetryList, setTelemetryList] = useState<PatientTelemetry[]>([
    { patientId: 101, name: 'John Doe', heartRate: 74, bpSystolic: 122, bpDiastolic: 80, oxygenSat: 98, status: 'STABLE' },
    { patientId: 102, name: 'Jane Smith', heartRate: 88, bpSystolic: 138, bpDiastolic: 88, oxygenSat: 96, status: 'STABLE' },
    { patientId: 103, name: 'Robert Johnson', heartRate: 112, bpSystolic: 155, bpDiastolic: 95, oxygenSat: 92, status: 'WARNING' },
  ]);

  const [isSimulating, setIsSimulating] = useState<boolean>(true);

  useEffect(() => {
    if (!isSimulating) return;
    const interval = setInterval(() => {
      setTelemetryList((prev) =>
        prev.map((item) => {
          const hrDelta = Math.floor(Math.random() * 5) - 2;
          const newHr = Math.max(50, Math.min(160, item.heartRate + hrDelta));
          const newStatus = newHr > 110 ? 'WARNING' : 'STABLE';
          return {
            ...item,
            heartRate: newHr,
            status: newStatus,
          };
        })
      );
    }, 2000);
    return () => clearInterval(interval);
  }, [isSimulating]);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
        <div className="flex items-center gap-2.5">
          <Activity className="w-5 h-5 text-emerald-400 animate-pulse" />
          <h3 className="text-base font-semibold text-slate-100">
            Real-Time ICU Telemetry & Vitals Stream
          </h3>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            WebSocket Live Broadcast Active
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {telemetryList.map((item) => (
          <div
            key={item.patientId}
            className={`p-4 rounded-xl border transition-all ${
              item.status === 'WARNING'
                ? 'bg-amber-950/20 border-amber-500/40 shadow-lg shadow-amber-500/10'
                : 'bg-slate-950/60 border-slate-800'
            }`}
          >
            <div className="flex items-center justify-between mb-3">
              <div>
                <div className="text-sm font-semibold text-slate-200">{item.name}</div>
                <div className="text-xs text-slate-500 font-mono">ID: #{item.patientId}</div>
              </div>
              <span
                className={`text-[10px] font-mono px-2 py-0.5 rounded font-semibold ${
                  item.status === 'WARNING'
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                    : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                }`}
              >
                {item.status}
              </span>
            </div>

            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="bg-slate-900/80 p-2 rounded border border-slate-800">
                <div className="text-[10px] text-slate-400 uppercase font-mono flex items-center justify-center gap-1">
                  <Heart className="w-3 h-3 text-rose-400" /> HR
                </div>
                <div className="text-base font-bold text-slate-100 font-mono">{item.heartRate}</div>
                <div className="text-[9px] text-slate-500">bpm</div>
              </div>

              <div className="bg-slate-900/80 p-2 rounded border border-slate-800">
                <div className="text-[10px] text-slate-400 uppercase font-mono flex items-center justify-center gap-1">
                  <Zap className="w-3 h-3 text-cyan-400" /> BP
                </div>
                <div className="text-base font-bold text-slate-100 font-mono">
                  {item.bpSystolic}/{item.bpDiastolic}
                </div>
                <div className="text-[9px] text-slate-500">mmHg</div>
              </div>

              <div className="bg-slate-900/80 p-2 rounded border border-slate-800">
                <div className="text-[10px] text-slate-400 uppercase font-mono">SpO2</div>
                <div className="text-base font-bold text-slate-100 font-mono">{item.oxygenSat}%</div>
                <div className="text-[9px] text-slate-500">O2 Sat</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
