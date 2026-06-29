import { useEffect, useRef } from "react";

interface LiveECGMonitorProps {
  hr: number;
  status: "Stable" | "Alert";
}

export default function LiveECGMonitor({ hr, status }: LiveECGMonitorProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number | null>(null);
  const phaseRef = useRef<number>(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Handle high-DPI displays safely (guard for JSDOM/test environment stubs)
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
    const accentColor = isAlert ? "#ff4a4a" : "#00bcd4";
    const glowColor = isAlert ? "rgba(255, 74, 74, 0.4)" : "rgba(0, 188, 212, 0.4)";

    // Buffer to hold the trace points for scrolling
    const points: number[] = new Array(width).fill(50);
    let drawIndex = 0;

    const tick = () => {
      // Advance phase based on heart rate
      // 60 BPM = 1 beat per second. At 60fps, phase advances by (hr / 60) / 60 per frame.
      const bps = hr / 60;
      const phaseDelta = bps / 60;
      phaseRef.current = (phaseRef.current + phaseDelta) % 1;

      const p = phaseRef.current;
      let ecgValue = 50; // baseline height (center)

      // Cardiac cycle waveform generator (P-Q-R-S-T)
      if (p >= 0.0 && p < 0.08) {
        // P-wave: small smooth bump
        const t = (p - 0.0) / 0.08;
        ecgValue -= Math.sin(t * Math.PI) * 4;
      } else if (p >= 0.10 && p < 0.12) {
        // Q-wave: brief dip
        const t = (p - 0.10) / 0.02;
        ecgValue += Math.sin(t * Math.PI) * 3;
      } else if (p >= 0.12 && p < 0.16) {
        // R-wave: sharp high spike
        const t = (p - 0.12) / 0.04;
        if (t < 0.5) {
          ecgValue -= (t / 0.5) * 35;
        } else {
          ecgValue -= 35 - ((t - 0.5) / 0.5) * 47;
        }
      } else if (p >= 0.16 && p < 0.19) {
        // S-wave: sharp dip returning to baseline
        const t = (p - 0.16) / 0.03;
        ecgValue += 12 - (t * 12);
      } else if (p >= 0.24 && p < 0.36) {
        // T-wave: medium smooth bump
        const t = (p - 0.24) / 0.12;
        ecgValue -= Math.sin(t * Math.PI) * 8;
      }

      // Add a tiny bit of random high-frequency baseline noise for clinical realism
      ecgValue += (Math.random() - 0.5) * 0.8;

      // Update the scrolling buffer
      points[drawIndex] = ecgValue;
      drawIndex = (drawIndex + 1) % width;

      // Clear canvas
      ctx.clearRect(0, 0, width, height);

      // Draw grid lines
      ctx.strokeStyle = "rgba(255, 255, 255, 0.025)";
      ctx.lineWidth = 1;
      ctx.shadowBlur = 0; // Disable shadow for grid lines to keep them sharp

      // Vertical grid lines
      for (let x = 0; x < width; x += 20) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
      }
      // Horizontal grid lines
      for (let y = 0; y < height; y += 20) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }

      // Draw the scrolling ECG line with sweep cursor effect
      ctx.lineWidth = 2.5;
      ctx.strokeStyle = accentColor;
      ctx.shadowColor = glowColor;
      ctx.shadowBlur = 6;
      ctx.lineCap = "round";
      ctx.lineJoin = "round";

      ctx.beginPath();
      // Draw first segment (from sweep index to end of canvas)
      let started = false;
      for (let i = drawIndex + 3; i < width; i++) {
        const x = i;
        const y = points[i];
        if (!started) {
          ctx.moveTo(x, y);
          started = true;
        } else {
          ctx.lineTo(x, y);
        }
      }

      // Draw second segment (from start of canvas to sweep index)
      started = false;
      for (let i = 0; i < drawIndex - 3; i++) {
        const x = i;
        const y = points[i];
        if (!started) {
          ctx.moveTo(x, y);
          started = true;
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();

      // Draw the bright glowing sweep cursor head
      if (hasArc) {
        ctx.beginPath();
        ctx.arc(drawIndex, points[drawIndex], 3.5, 0, 2 * Math.PI);
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
  }, [hr, status]);

  return (
    <canvas
      ref={canvasRef}
      style={{ width: "100%", height: "100%" }}
      className="block"
    />
  );
}
