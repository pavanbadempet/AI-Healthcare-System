import { useEffect, useRef, memo } from "react";

interface LiveECGMonitorProps {
  hr: number;
  status: "Stable" | "Alert";
  mode?: "ecg" | "spo2" | "resp";
}

const workerCode = `
  let canvas = null;
  let ctx = null;
  let width = 400;
  let height = 100;
  let hr = 72;
  let status = "Stable";
  let mode = "ecg";
  let phase = 0;
  let points = [];
  let drawIndex = 0;
  let animationFrameId = null;

  self.onmessage = (e) => {
    const msg = e.data;
    if (msg.type === "INIT") {
      canvas = msg.canvas;
      ctx = canvas.getContext("2d");
      width = msg.width || 400;
      height = msg.height || 100;
      points = new Array(width).fill(50);
      tick();
    } else if (msg.type === "UPDATE") {
      hr = msg.hr;
      status = msg.status;
      mode = msg.mode;
    }
  };

  function tick() {
    if (!canvas || !ctx) return;

    let speedFactor = 1.0;
    if (mode === "resp") {
      speedFactor = 0.25;
    }

    const bps = hr / 60;
    const phaseDelta = (bps / 60) * speedFactor;
    phase = (phase + phaseDelta) % 1;

    let waveValue = 50;

    if (mode === "ecg") {
      if (phase >= 0.0 && phase < 0.08) {
        const t = phase / 0.08;
        waveValue -= Math.sin(t * Math.PI) * 4;
      } else if (phase >= 0.10 && phase < 0.12) {
        const t = (phase - 0.10) / 0.02;
        waveValue += Math.sin(t * Math.PI) * 3;
      } else if (phase >= 0.12 && phase < 0.16) {
        const t = (phase - 0.12) / 0.04;
        if (t < 0.5) {
          waveValue -= (t / 0.5) * 35;
        } else {
          waveValue -= 35 - ((t - 0.5) / 0.5) * 47;
        }
      } else if (phase >= 0.16 && phase < 0.19) {
        const t = (phase - 0.16) / 0.03;
        waveValue += 12 - (t * 12);
      } else if (phase >= 0.24 && phase < 0.36) {
        const t = (phase - 0.24) / 0.12;
        waveValue -= Math.sin(t * Math.PI) * 8;
      }
    } else if (mode === "spo2") {
      if (phase >= 0.0 && phase < 0.22) {
        const t = phase / 0.22;
        waveValue -= Math.sin(t * (Math.PI / 2)) * 32;
      } else if (phase >= 0.22 && phase < 0.35) {
        const t = (phase - 0.22) / 0.13;
        waveValue -= 32 - Math.sin(t * Math.PI) * 5;
      } else if (phase >= 0.35 && phase < 0.85) {
        const t = (phase - 0.35) / 0.50;
        waveValue -= 32 * (1 - t);
      }
    } else if (mode === "resp") {
      waveValue -= Math.sin(phase * 2 * Math.PI) * 20;
    }

    waveValue += (Math.random() - 0.5) * 0.7;
    points[drawIndex] = waveValue;
    drawIndex = (drawIndex + 1) % width;

    ctx.clearRect(0, 0, width, height);

    ctx.strokeStyle = "rgba(255, 255, 255, 0.02)";
    ctx.lineWidth = 1;
    ctx.shadowBlur = 0;

    for (let x = 0; x < width; x += 20) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
    for (let y = 0; y < height; y += 20) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }

    const isAlert = status === "Alert";
    let accentColor = "#00bcd4";
    let glowColor = "rgba(0, 188, 212, 0.4)";
    if (mode === "ecg") {
      accentColor = isAlert ? "#ff4a4a" : "#00bcd4";
      glowColor = isAlert ? "rgba(255, 74, 74, 0.4)" : "rgba(0, 188, 212, 0.4)";
    } else if (mode === "spo2") {
      accentColor = "#00e676";
      glowColor = "rgba(0, 230, 118, 0.4)";
    } else if (mode === "resp") {
      accentColor = "#8656f5";
      glowColor = "rgba(134, 86, 245, 0.4)";
    }

    ctx.lineWidth = 2.2;
    ctx.strokeStyle = accentColor;
    ctx.shadowColor = glowColor;
    ctx.shadowBlur = 6;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";

    ctx.beginPath();
    let started = false;
    for (let i = drawIndex + 3; i < width; i++) {
      if (!started) {
        ctx.moveTo(i, points[i]);
        started = true;
      } else {
        ctx.lineTo(i, points[i]);
      }
    }
    started = false;
    for (let i = 0; i < drawIndex - 3; i++) {
      if (!started) {
        ctx.moveTo(i, points[i]);
        started = true;
      } else {
        ctx.lineTo(i, points[i]);
      }
    }
    ctx.stroke();

    // Sweep cursor head
    ctx.beginPath();
    ctx.arc(drawIndex, points[drawIndex], 3.2, 0, 2 * Math.PI);
    ctx.fillStyle = "#ffffff";
    ctx.shadowBlur = 10;
    ctx.shadowColor = accentColor;
    ctx.fill();

    animationFrameId = requestAnimationFrame(tick);
  }
`;

const LiveECGMonitor = memo(function LiveECGMonitor({ hr, status, mode = "ecg" }: LiveECGMonitorProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const workerRef = useRef<Worker | null>(null);
  const isWorkerModeRef = useRef<boolean>(false);

  // Fallback refs for main-thread loop
  const animationRef = useRef<number | null>(null);
  const phaseRef = useRef<number>(0);
  const pointsRef = useRef<number[] | null>(null);
  const drawIndexRef = useRef<number>(0);

  // Spawns Web Worker once on mount
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    // Detect OffscreenCanvas support (guard for browsers, JSDOM, or automated tests)
    const supportsOffscreen = typeof canvas.transferControlToOffscreen === "function";

    if (supportsOffscreen) {
      try {
        const blob = new Blob([workerCode], { type: "application/javascript" });
        const workerUrl = URL.createObjectURL(blob);
        const worker = new Worker(workerUrl);
        workerRef.current = worker;
        isWorkerModeRef.current = true;

        const dpr = window.devicePixelRatio || 1;
        const width = 400;
        const height = 100;
        canvas.width = width * dpr;
        canvas.height = height * dpr;

        const offscreen = canvas.transferControlToOffscreen();
        worker.postMessage({
          type: "INIT",
          canvas: offscreen,
          width,
          height
        }, [offscreen]);

        return () => {
          worker.terminate();
          URL.revokeObjectURL(workerUrl);
          workerRef.current = null;
          isWorkerModeRef.current = false;
        };
      } catch (err) {
        console.warn("Failed to initialize OffscreenCanvas worker, falling back to main thread:", err);
        isWorkerModeRef.current = false;
      }
    }
  }, []);

  // Update Web Worker properties dynamically
  useEffect(() => {
    if (isWorkerModeRef.current && workerRef.current) {
      workerRef.current.postMessage({
        type: "UPDATE",
        hr,
        status,
        mode
      });
    }
  }, [hr, status, mode]);

  // Main thread fallback loop (Only runs if OffscreenCanvas is not active)
  useEffect(() => {
    if (isWorkerModeRef.current) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const hasScale = typeof ctx.scale === "function";
    const hasArc = typeof ctx.arc === "function";

    const dpr = window.devicePixelRatio || 1;
    const width = 400;
    const height = 100;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    if (hasScale) {
      ctx.scale(dpr, dpr);
    }

    const isAlert = status === "Alert";
    let accentColor = "#00bcd4";
    let glowColor = "rgba(0, 188, 212, 0.4)";
    if (mode === "ecg") {
      accentColor = isAlert ? "#ff4a4a" : "#00bcd4";
      glowColor = isAlert ? "rgba(255, 74, 74, 0.4)" : "rgba(0, 188, 212, 0.4)";
    } else if (mode === "spo2") {
      accentColor = "#00e676";
      glowColor = "rgba(0, 230, 118, 0.4)";
    } else if (mode === "resp") {
      accentColor = "#8656f5";
      glowColor = "rgba(134, 86, 245, 0.4)";
    }

    if (!pointsRef.current) {
      pointsRef.current = new Array(width).fill(50);
    }
    const points = pointsRef.current;

    const tick = () => {
      let speedFactor = 1.0;
      if (mode === "resp") {
        speedFactor = 0.25;
      }

      const bps = hr / 60;
      const phaseDelta = (bps / 60) * speedFactor;
      phaseRef.current = (phaseRef.current + phaseDelta) % 1;

      const p = phaseRef.current;
      let waveValue = 50;

      if (mode === "ecg") {
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
          waveValue += 12 - (t * 12);
        } else if (p >= 0.24 && p < 0.36) {
          const t = (p - 0.24) / 0.12;
          waveValue -= Math.sin(t * Math.PI) * 8;
        }
      } else if (mode === "spo2") {
        if (p >= 0.0 && p < 0.22) {
          const t = p / 0.22;
          waveValue -= Math.sin(t * (Math.PI / 2)) * 32;
        } else if (p >= 0.22 && p < 0.35) {
          const t = (p - 0.22) / 0.13;
          waveValue -= 32 - Math.sin(t * Math.PI) * 5;
        } else if (p >= 0.35 && p < 0.85) {
          const t = (p - 0.35) / 0.50;
          waveValue -= 32 * (1 - t);
        }
      } else if (mode === "resp") {
        waveValue -= Math.sin(p * 2 * Math.PI) * 20;
      }

      waveValue += (Math.random() - 0.5) * 0.7;

      const currentDrawIndex = drawIndexRef.current;
      points[currentDrawIndex] = waveValue;
      drawIndexRef.current = (currentDrawIndex + 1) % width;

      ctx.clearRect(0, 0, width, height);

      ctx.strokeStyle = "rgba(255, 255, 255, 0.02)";
      ctx.lineWidth = 1;
      ctx.shadowBlur = 0;

      for (let x = 0; x < width; x += 20) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
      }
      for (let y = 0; y < height; y += 20) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }

      ctx.lineWidth = 2.2;
      ctx.strokeStyle = accentColor;
      ctx.shadowColor = glowColor;
      ctx.shadowBlur = 6;
      ctx.lineCap = "round";
      ctx.lineJoin = "round";

      ctx.beginPath();
      let started = false;
      const drawIndexVal = drawIndexRef.current;
      for (let i = drawIndexVal + 3; i < width; i++) {
        if (!started) {
          ctx.moveTo(i, points[i]);
          started = true;
        } else {
          ctx.lineTo(i, points[i]);
        }
      }
      started = false;
      for (let i = 0; i < drawIndexVal - 3; i++) {
        if (!started) {
          ctx.moveTo(i, points[i]);
          started = true;
        } else {
          ctx.lineTo(i, points[i]);
        }
      }
      ctx.stroke();

      if (hasArc) {
        ctx.beginPath();
        ctx.arc(drawIndexVal, points[drawIndexVal], 3.2, 0, 2 * Math.PI);
        ctx.fillStyle = "#ffffff";
        ctx.shadowBlur = 10;
        ctx.shadowColor = accentColor;
        ctx.fill();
      }

      animationRef.current = requestAnimationFrame(tick);
    };

    animationRef.current = requestAnimationFrame(tick);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [hr, status, mode]);

  return (
    <canvas
      ref={canvasRef}
      style={{ width: "100%", height: "100%" }}
      className="block"
    />
  );
});

export default LiveECGMonitor;


