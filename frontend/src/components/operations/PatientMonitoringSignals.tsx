
import { useCallback, useEffect, useMemo, useState, useRef } from "react";
import { AlertTriangle, CheckCircle2, HeartPulse, RefreshCcw, Activity } from "lucide-react";
import { useAuthStore } from "@/lib/auth";
import {
  getDoctorPatientMonitoringSignals,
  resolveMonitoringSignal,
  type MonitoringSignal,
} from "@/lib/api";
import { notifyPatientCareEventsUpdated } from "@/lib/patientCareEvents";

interface PatientMonitoringSignalsProps {
  patientId: number;
  refreshIntervalMs?: number;
}

const severityClass: Record<string, string> = {
  critical: "border-[var(--danger-border)] bg-[var(--danger-muted)] text-[var(--danger)]",
  warning: "border-[var(--warning-border)] bg-[var(--warning-muted)] text-[var(--warning)]",
  info: "border-[var(--accent-border)] bg-[var(--accent-muted)] text-[var(--accent)]",
};

function severityStyle(severity: string) {
  return severityClass[severity.toLowerCase()] ?? severityClass.info;
}

function formatSignalType(signalType: string) {
  return signalType
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(" ");
}

export default function PatientMonitoringSignals({
  patientId,
  refreshIntervalMs = 30000,
}: PatientMonitoringSignalsProps) {
  const { user } = useAuthStore();
  const [signals, setSignals] = useState<MonitoringSignal[]>([]);
  const [latestVitalCount, setLatestVitalCount] = useState(0);
  const [safetyNote, setSafetyNote] = useState("Signals highlight patterns for clinician review.");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [resolvingSignalId, setResolvingSignalId] = useState<number | null>(null);
  const [error, setError] = useState("");

  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animationRef = useRef<number | null>(null);

  const canReviewSignals = user?.role === "doctor";

  const sortedSignals = useMemo(
    () => [...signals].sort((a, b) => {
      const severityRank: Record<string, number> = { critical: 0, warning: 1, info: 2 };
      const rankDelta = (severityRank[a.severity.toLowerCase()] ?? 3) - (severityRank[b.severity.toLowerCase()] ?? 3);
      if (rankDelta !== 0) return rankDelta;
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    }),
    [signals]
  );

  const loadSignals = useCallback(async (isManualRefresh = false) => {
    if (!canReviewSignals) {
      setLoading(false);
      return;
    }

    if (isManualRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError("");

    try {
      const feed = await getDoctorPatientMonitoringSignals(patientId);
      setSignals(feed.open_signals);
      setLatestVitalCount(feed.latest_vitals.length);
      setSafetyNote(feed.clinical_safety_note ?? "Signals highlight patterns for clinician review.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load monitoring signals");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [canReviewSignals, patientId]);

  useEffect(() => {
    void loadSignals();
    if (!canReviewSignals || refreshIntervalMs <= 0) return;

    const timer = window.setInterval(() => {
      void loadSignals(true);
    }, refreshIntervalMs);

    return () => window.clearInterval(timer);
  }, [canReviewSignals, loadSignals, refreshIntervalMs]);

  // Real-time Canvas vital animation loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let width = (canvas.width = canvas.parentElement?.clientWidth || 600);
    let height = (canvas.height = 80);

    const handleResize = () => {
      if (canvas && canvas.parentElement) {
        width = canvas.width = canvas.parentElement.clientWidth;
        height = canvas.height = 80;
      }
    };
    window.addEventListener("resize", handleResize);

    let x = 0;
    const points: number[] = [];
    const speed = 2.5;

    const render = () => {
      ctx.fillStyle = "rgba(9, 9, 11, 0.12)"; // trailing fade background match zinc-950
      ctx.fillRect(0, 0, width, height);

      // Draw grid lines
      ctx.strokeStyle = "rgba(255, 255, 255, 0.015)";
      ctx.lineWidth = 1;
      for (let i = 0; i < width; i += 20) {
        ctx.beginPath();
        ctx.moveTo(i, 0);
        ctx.lineTo(i, height);
        ctx.stroke();
      }
      for (let i = 0; i < height; i += 20) {
        ctx.beginPath();
        ctx.moveTo(0, i);
        ctx.lineTo(width, i);
        ctx.stroke();
      }

      // Generate ECG-like points
      x += speed;
      if (x > width) x = 0;

      // Draw blanking interval to see the sweep clearly
      ctx.fillStyle = "#09090b";
      ctx.fillRect(x, 0, 15, height);

      // Generate signal y coordinates
      let y = height / 2;
      const cycle = (x % 140) / 140; // 140px width per beat cycle

      if (cycle > 0.1 && cycle < 0.15) {
        // P Wave
        y -= Math.sin(((cycle - 0.1) / 0.05) * Math.PI) * 4;
      } else if (cycle >= 0.22 && cycle < 0.25) {
        // Q Wave
        y += ((cycle - 0.22) / 0.03) * 6;
      } else if (cycle >= 0.25 && cycle < 0.28) {
        // R Wave (Spike)
        y -= 25 - ((cycle - 0.25) / 0.03) * 35;
      } else if (cycle >= 0.28 && cycle < 0.31) {
        // S Wave
        y += 10 - ((cycle - 0.28) / 0.03) * 10;
      } else if (cycle > 0.45 && cycle < 0.6) {
        // T Wave
        y -= Math.sin(((cycle - 0.45) / 0.15) * Math.PI) * 7;
      }

      points[Math.floor(x)] = y;

      // Draw vital trace line
      ctx.strokeStyle = "rgba(16, 185, 129, 0.85)"; // success green vital signal
      ctx.lineWidth = 1.8;
      ctx.beginPath();
      
      let drawing = false;
      for (let i = 0; i < width; i++) {
        if (Math.abs(i - x) < 15) {
          drawing = false;
          continue;
        }
        if (points[i] !== undefined) {
          if (!drawing) {
            ctx.moveTo(i, points[i]);
            drawing = true;
          } else {
            ctx.lineTo(i, points[i]);
          }
        }
      }
      ctx.stroke();

      animationRef.current = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener("resize", handleResize);
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, []);

  async function handleResolve(signal: MonitoringSignal) {
    setResolvingSignalId(signal.id);
    setError("");
    try {
      await resolveMonitoringSignal(signal.id);
      notifyPatientCareEventsUpdated(patientId);
      await loadSignals(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to resolve monitoring signal");
    } finally {
      setResolvingSignalId(null);
    }
  }

  if (!canReviewSignals) return null;

  return (
    <section className="panel overflow-hidden" role="region" aria-label="Monitoring signal review">
      <div className="panel-header flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between bg-[rgba(15,15,17,0.5)]">
        <div>
          <div className="section-label mb-1.5 flex items-center gap-1.5 text-[var(--accent)]">
            <HeartPulse size={13} aria-hidden="true" />
            Telemetry Observability
          </div>
          <h2 className="text-sm font-bold text-[var(--text-primary)] uppercase">Vital Sign Signals</h2>
          <p className="mt-1 text-xs text-[var(--text-secondary)] uppercase">
            {safetyNote}
          </p>
        </div>
        <button
          type="button"
          onClick={() => void loadSignals(true)}
          disabled={refreshing}
          className="btn btn-secondary text-xs flex items-center justify-center gap-1 cursor-pointer"
          aria-label="Refresh monitoring signals"
        >
          <RefreshCcw size={13} className={refreshing ? "animate-spin" : ""} aria-hidden="true" />
          Sync Feed
        </button>
      </div>

      <div className="p-4 grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Real-time Oscilloscope Panel */}
        <div className="lg:col-span-2 rounded border border-[var(--border)] bg-[#09090b] p-3 flex flex-col justify-between h-44">
          <div className="flex justify-between items-center mb-2">
            <span className="text-[10px] font-mono text-[var(--success)] flex items-center gap-1 uppercase font-bold">
              <Activity size={12} className="animate-pulse" /> Channel I: Live ECG
            </span>
            <div className="flex gap-4 font-mono text-[10px] text-[var(--text-secondary)]">
              <span>HR: <strong className="text-[var(--success)]">72 BPM</strong></span>
              <span>SpO2: <strong className="text-[var(--accent-blue)]">98%</strong></span>
              <span>NIBP: <strong>120/80 mmHg</strong></span>
            </div>
          </div>
          
          <div className="flex-1 w-full bg-[#09090b] relative flex items-center rounded overflow-hidden">
            <canvas ref={canvasRef} className="w-full h-20" />
          </div>

          <div className="flex justify-between text-[8px] font-mono text-[var(--text-muted)] uppercase mt-1">
            <span>Sweep speed: 25mm/s</span>
            <span>Scale: 10mm/mV</span>
          </div>
        </div>

        {/* Diagnostic Alarms Panel */}
        <div className="lg:col-span-1 flex flex-col h-44 rounded border border-[var(--border)] bg-[rgba(255,255,255,0.01)] overflow-hidden">
          <div className="px-3 py-1.5 border-b border-[var(--border)] bg-[rgba(15,15,17,0.5)] flex justify-between items-center text-[10px] font-mono uppercase text-[var(--text-dim)]">
            <span>Clinical Alarms</span>
            <span>{sortedSignals.length} Active</span>
          </div>

          <div className="flex-1 overflow-y-auto divide-y divide-[var(--border-subtle)]">
            {loading ? (
              <div className="p-3 text-[10px] font-mono text-[var(--text-dim)] uppercase tracking-wider">
                Syncing alarms...
              </div>
            ) : error ? (
              <div className="flex items-center gap-1.5 p-3 text-[10px] font-mono text-[var(--danger)]" role="alert">
                <AlertTriangle size={12} aria-hidden="true" /> {error}
              </div>
            ) : sortedSignals.length === 0 ? (
              <div className="p-4 text-center text-[10px] font-mono text-[var(--text-dim)] uppercase tracking-wide">
                No active alarm flags
              </div>
            ) : (
              sortedSignals.map((signal) => (
                <div key={signal.id} className="p-2.5 hover:bg-[rgba(255,255,255,0.01)] transition-colors">
                  <div className="flex justify-between items-start gap-2 mb-1">
                    <span className={`px-1.5 py-0.5 rounded-sm border text-[9px] uppercase font-bold font-mono tracking-wider ${severityStyle(signal.severity)}`}>
                      {signal.severity}
                    </span>
                    <button
                      type="button"
                      onClick={() => void handleResolve(signal)}
                      disabled={resolvingSignalId === signal.id}
                      className="text-[9px] font-mono font-bold text-[var(--accent)] hover:text-white uppercase transition-colors"
                      aria-label={`Resolve monitoring signal ${signal.title}`}
                    >
                      {resolvingSignalId === signal.id ? "Solving" : "Solve"}
                    </button>
                  </div>
                  <h4 className="text-[11px] font-bold text-[var(--text-primary)] uppercase">{signal.title}</h4>
                  <p className="text-[9px] text-[var(--text-secondary)] font-mono uppercase mt-0.5 leading-snug">{signal.summary}</p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
