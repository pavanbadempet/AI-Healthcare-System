import { useEffect, useRef } from "react";

interface LiveECGMonitorProps {
  hr: number;
  status: "Stable" | "Alert";
  mode?: "ecg" | "spo2" | "resp";
}

export default function LiveECGMonitor({ hr, status, mode = "ecg" }: LiveECGMonitorProps) {
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
    
    // Choose theme colors based on mode
    let accentColor = "#00bcd4"; // Cyan for ECG Stable
    let glowColor = "rgba(0, 188, 212, 0.4)";
    if (mode === "ecg") {
      accentColor = isAlert ? "#ff4a4a" : "#00bcd4";
      glowColor = isAlert ? "rgba(255, 74, 74, 0.4)" : "rgba(0, 188, 212, 0.4)";
    } else if (mode === "spo2") {
      accentColor = "#00e676"; // Green for SpO2 Pleth
      glowColor = "rgba(0, 230, 118, 0.4)";
    } else if (mode === "resp") {
      accentColor = "#8656f5"; // Purple for respiration
      glowColor = "rgba(134, 86, 245, 0.4)";
    }

    // Buffer to hold the trace points for scrolling
    const points: number[] = new Array(width).fill(50);
    let drawIndex = 0;

    const tick = () => {
      // Calculate speed factor. Respiration runs much slower than ECG/SpO2.
      let speedFactor = 1.0;
      if (mode === "resp") {
        speedFactor = 0.25; // 4x slower respiration cycles
      }

      const bps = hr / 60;
      const phaseDelta = (bps / 60) * speedFactor;
      phaseRef.current = (phaseRef.current + phaseDelta) % 1;

      const p = phaseRef.current;
      let waveValue = 50; // baseline center height (0-100)

      if (mode === "ecg") {
        // --- Cardiac Cycle waveform (P-Q-R-S-T) ---
        if (p >= 0.0 && p < 0.08) {
          // P-wave
          const t = (p - 0.0) / 0.08;
          waveValue -= Math.sin(t * Math.PI) * 4;
        } else if (p >= 0.10 && p < 0.12) {
          // Q-wave
          const t = (p - 0.10) / 0.02;
          waveValue += Math.sin(t * Math.PI) * 3;
        } else if (p >= 0.12 && p < 0.16) {
          // R-wave
          const t = (p - 0.12) / 0.04;
          if (t < 0.5) {
            waveValue -= (t / 0.5) * 35;
          } else {
            waveValue -= 35 - ((t - 0.5) / 0.5) * 47;
          }
        } else if (p >= 0.16 && p < 0.19) {
          // S-wave
          const t = (p - 0.16) / 0.03;
          waveValue += 12 - (t * 12);
        } else if (p >= 0.24 && p < 0.36) {
          // T-wave
          const t = (p - 0.24) / 0.12;
          waveValue -= Math.sin(t * Math.PI) * 8;
        }
      } else if (mode === "spo2") {
        // --- SpO2 Plethysmograph Waveform (Rapid Ascent, Dicrotic Notch, Slow Decay) ---
        if (p >= 0.0 && p < 0.22) {
          // Rapid ascent
          const t = p / 0.22;
          waveValue -= Math.sin(t * (Math.PI / 2)) * 32;
        } else if (p >= 0.22 && p < 0.35) {
          // Dicrotic notch (slight dip and bounce)
          const t = (p - 0.22) / 0.13;
          const notchDip = Math.sin(t * Math.PI) * 5;
          waveValue -= 32 - notchDip;
        } else if (p >= 0.35 && p < 0.85) {
          // Slow decay back to baseline
          const t = (p - 0.35) / 0.50;
          waveValue -= 32 * (1 - t);
        }
      } else if (mode === "resp") {
        // --- Respiration Waveform (Smooth Sine Wave) ---
        waveValue -= Math.sin(p * 2 * Math.PI) * 20;
      }

      // Add a tiny bit of random high-frequency baseline noise for clinical realism
      waveValue += (Math.random() - 0.5) * 0.7;

      // Update the scrolling buffer
      points[drawIndex] = waveValue;
      drawIndex = (drawIndex + 1) % width;

      // Clear canvas
      ctx.clearRect(0, 0, width, height);

      // Draw grid lines
      ctx.strokeStyle = "rgba(255, 255, 255, 0.02)";
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

      // Draw the scrolling signal line with sweep cursor effect
      ctx.lineWidth = 2.2;
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
        ctx.arc(drawIndex, points[drawIndex], 3.2, 0, 2 * Math.PI);
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
}
