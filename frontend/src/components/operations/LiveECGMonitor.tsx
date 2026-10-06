import { useEffect, useRef, memo } from "react";

interface LiveECGMonitorProps {
  hr: number;
  status: "Stable" | "Alert";
  mode?: "ecg" | "spo2" | "resp";
}

const WIDTH = 400;
const HEIGHT = 100;
const TARGET_FRAME_MS = 25; // ~40 FPS for silky-smooth clinical sweep with near-zero CPU/GPU overhead

/**
 * Ultra-High-Performance Hardware-Accelerated Clinical Waveform Monitor
 * 
 * Features:
 * - Direct 2D Canvas pipeline with dual-pass neon glow (0% shadowBlur GPU thrashing)
 * - Zero Web Worker memory overhead (prevents V8 isolate memory bloat and Chromium leak)
 * - Automatic pause on background tab (document.hidden) and off-screen scroll (IntersectionObserver)
 * - Fixed memory circular buffer (zero garbage collection churn)
 */
const LiveECGMonitor = memo(function LiveECGMonitor({
  hr,
  status,
  mode = "ecg",
}: LiveECGMonitorProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animFrameRef = useRef<number>(0);
  const isVisibleRef = useRef<boolean>(true);
  const lastTimeRef = useRef<number>(0);

  // Mutable animation state (avoids React re-render overhead)
  const stateRef = useRef({
    hr,
    status,
    mode,
    phase: 0,
    drawIndex: 0,
    points: new Float32Array(WIDTH).fill(50),
  });

  // Keep latest props synced to mutable ref without triggering effect re-binds
  useEffect(() => {
    stateRef.current.hr = hr;
    stateRef.current.status = status;
    stateRef.current.mode = mode;
  }, [hr, status, mode]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d", { alpha: true, desynchronized: true });
    if (!ctx) return;

    let isRunning = true;

    const tick = (now: number) => {
      if (!isRunning) return;

      const delta = now - lastTimeRef.current;
      if (delta >= TARGET_FRAME_MS) {
        lastTimeRef.current = now - (delta % TARGET_FRAME_MS);

        const state = stateRef.current;
        const currentMode = state.mode;
        const currentHr = state.hr || 72;
        const currentStatus = state.status;
        const points = state.points;

        // Waveform speed and phase advance
        let speedFactor = 1.0;
        if (currentMode === "resp") {
          speedFactor = 0.25;
        }

        const bps = currentHr / 60;
        const phaseDelta = (bps / 40) * speedFactor;
        state.phase = (state.phase + phaseDelta) % 1;
        const p = state.phase;

        let waveValue = 50;

        if (currentMode === "ecg") {
          if (p >= 0.0 && p < 0.08) {
            const t = p / 0.08;
            waveValue -= Math.sin(t * Math.PI) * 4;
          } else if (p >= 0.10 && p < 0.12) {
            const t = (p - 0.10) / 0.02;
            waveValue += Math.sin(t * Math.PI) * 3;
          } else if (p >= 0.12 && p < 0.16) {
            const t = (p - 0.12) / 0.04;
            if (t < 0.5) {
              waveValue -= (t / 0.5) * 35;
            } else {
              waveValue -= 35 - ((t - 0.5) / 0.5) * 47;
            }
          } else if (p >= 0.16 && p < 0.19) {
            const t = (p - 0.16) / 0.03;
            waveValue += 12 - t * 12;
          } else if (p >= 0.24 && p < 0.36) {
            const t = (p - 0.24) / 0.12;
            waveValue -= Math.sin(t * Math.PI) * 8;
          }
        } else if (currentMode === "spo2") {
          if (p >= 0.0 && p < 0.22) {
            const t = p / 0.22;
            waveValue -= Math.sin(t * (Math.PI / 2)) * 32;
          } else if (p >= 0.22 && p < 0.35) {
            const t = (p - 0.22) / 0.13;
            waveValue -= 32 - Math.sin(t * Math.PI) * 5;
          } else if (p >= 0.35 && p < 0.85) {
            const t = (p - 0.35) / 0.5;
            waveValue -= 32 * (1 - t);
          }
        } else if (currentMode === "resp") {
          waveValue -= Math.sin(p * 2 * Math.PI) * 20;
        }

        // Slight natural physiological variance
        waveValue += (Math.random() - 0.5) * 0.6;
        const currentDrawIndex = state.drawIndex;
        points[currentDrawIndex] = waveValue;
        state.drawIndex = (currentDrawIndex + 1) % WIDTH;

        // Render Frame
        ctx.clearRect(0, 0, WIDTH, HEIGHT);

        const isAlert = currentStatus === "Alert";
        let accentColor = "#00bcd4";
        let glowColor = "rgba(0, 188, 212, 0.25)";

        if (currentMode === "ecg") {
          accentColor = isAlert ? "#ff4a4a" : "#00bcd4";
          glowColor = isAlert ? "rgba(255, 74, 74, 0.25)" : "rgba(0, 188, 212, 0.25)";
        } else if (currentMode === "spo2") {
          accentColor = "#00e676";
          glowColor = "rgba(0, 230, 118, 0.25)";
        } else if (currentMode === "resp") {
          accentColor = "#8656f5";
          glowColor = "rgba(134, 86, 245, 0.25)";
        }

        // Trace line path
        const drawSegments = () => {
          ctx.beginPath();
          let started = false;
          const idx = state.drawIndex;

          for (let i = idx + 4; i < WIDTH; i++) {
            if (!started) {
              ctx.moveTo(i, points[i]);
              started = true;
            } else {
              ctx.lineTo(i, points[i]);
            }
          }

          started = false;
          for (let i = 0; i < idx - 4; i++) {
            if (!started) {
              ctx.moveTo(i, points[i]);
              started = true;
            } else {
              ctx.lineTo(i, points[i]);
            }
          }
        };

        ctx.lineCap = "round";
        ctx.lineJoin = "round";

        // Pass 1: Soft luminous aura (simulates phosphor glow without expensive shadowBlur)
        ctx.lineWidth = 3.5;
        ctx.strokeStyle = glowColor;
        drawSegments();
        ctx.stroke();

        // Pass 2: High-contrast sharp core ray
        ctx.lineWidth = 1.6;
        ctx.strokeStyle = accentColor;
        drawSegments();
        ctx.stroke();

        // Sweep cursor head
        const sweepY = points[state.drawIndex];

        // Outer glow halo
        ctx.beginPath();
        ctx.arc(state.drawIndex, sweepY, 4.5, 0, 2 * Math.PI);
        ctx.fillStyle = glowColor;
        ctx.fill();

        // Sharp beam core
        ctx.beginPath();
        ctx.arc(state.drawIndex, sweepY, 2.2, 0, 2 * Math.PI);
        ctx.fillStyle = "#ffffff";
        ctx.fill();
      }

      if (isRunning && isVisibleRef.current && !document.hidden) {
        animFrameRef.current = requestAnimationFrame(tick);
      }
    };

    const startAnimation = () => {
      if (!animFrameRef.current && isRunning) {
        lastTimeRef.current = performance.now();
        animFrameRef.current = requestAnimationFrame(tick);
      }
    };

    const stopAnimation = () => {
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
        animFrameRef.current = 0;
      }
    };

    // Auto-pause when page/tab is backgrounded to eliminate idle CPU & battery drain
    const handleVisibilityChange = () => {
      if (document.hidden) {
        stopAnimation();
      } else if (isVisibleRef.current) {
        startAnimation();
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);

    // Auto-pause when monitor is scrolled off screen
    let observer: IntersectionObserver | null = null;
    if (typeof IntersectionObserver !== "undefined") {
      observer = new IntersectionObserver(
        ([entry]) => {
          isVisibleRef.current = entry.isIntersecting;
          if (entry.isIntersecting && !document.hidden) {
            startAnimation();
          } else {
            stopAnimation();
          }
        },
        { threshold: 0.05 }
      );
      observer.observe(canvas);
    } else {
      startAnimation();
    }

    return () => {
      isRunning = false;
      stopAnimation();
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      if (observer) {
        observer.disconnect();
      }
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      width={WIDTH}
      height={HEIGHT}
      style={{
        width: "100%",
        height: "100%",
        backgroundImage: `
          linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px),
          linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px)
        `,
        backgroundSize: "20px 20px",
      }}
      className="block"
      aria-label={`${mode.toUpperCase()} live waveform monitor (${status})`}
    />
  );
});

export default LiveECGMonitor;
