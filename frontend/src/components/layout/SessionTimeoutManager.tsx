import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "@/lib/auth";
import { motion, AnimatePresence } from "framer-motion";
import { ShieldAlert, Clock, LogOut, RefreshCw } from "lucide-react";

const TIMEOUT_MS = 15 * 60 * 1000; // 15 minutes
const WARNING_MS = 30 * 1000; // 30 seconds

export default function SessionTimeoutManager({ children }: { children: React.ReactNode }) {
  const { token, logout } = useAuthStore();
  const navigate = useNavigate();

  const [showWarning, setShowWarning] = useState(false);
  const [secondsLeft, setSecondsLeft] = useState(30);

  const inactivityTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const countdownIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Reset the main inactivity timer
  const resetTimer = () => {
    // Clear existing timer
    if (inactivityTimerRef.current) {
      clearTimeout(inactivityTimerRef.current);
    }
    if (countdownIntervalRef.current) {
      clearInterval(countdownIntervalRef.current);
    }

    setShowWarning(false);
    setSecondsLeft(30);

    // Set new timer to trigger warning
    inactivityTimerRef.current = setTimeout(() => {
      triggerWarning();
    }, TIMEOUT_MS - WARNING_MS);
  };

  // Trigger the 30-second warning countdown
  const triggerWarning = () => {
    setShowWarning(true);
    setSecondsLeft(30);

    countdownIntervalRef.current = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          clearInterval(countdownIntervalRef.current!);
          handleTimeout();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  // Perform automatic logout
  const handleTimeout = () => {
    logout();
    navigate("/login?expired=1");
  };

  // Manual logout from the warning modal
  const handleManualLogout = () => {
    logout();
    navigate("/login");
  };

  // Extend the session when user clicks the extension action
  const extendSession = () => {
    resetTimer();
  };

  useEffect(() => {
    if (!token) return;

    // Listen to user activity to reset inactivity timer
    const activityEvents = ["mousemove", "keydown", "click", "scroll"];
    
    const handleUserActivity = () => {
      // If we are showing the warning modal, do not reset automatically on minor jitter (e.g. mousemove).
      // They must explicitly click "Extend Session" to reset.
      if (!showWarning) {
        resetTimer();
      }
    };

    // Initialize timers
    resetTimer();

    activityEvents.forEach((event) => {
      window.addEventListener(event, handleUserActivity);
    });

    return () => {
      if (inactivityTimerRef.current) clearTimeout(inactivityTimerRef.current);
      if (countdownIntervalRef.current) clearInterval(countdownIntervalRef.current);
      activityEvents.forEach((event) => {
        window.removeEventListener(event, handleUserActivity);
      });
    };
  }, [token, showWarning]);

  return (
    <>
      {children}

      <AnimatePresence>
        {showWarning && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.7 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/80 backdrop-blur-md"
              onClick={extendSession} // Clicking backdrop is also a safe extension gesture
            />

            {/* Warning Dialog */}
            <motion.div
              initial={{ scale: 0.95, opacity: 0, y: 15 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.95, opacity: 0, y: 15 }}
              transition={{ type: "spring", damping: 25, stiffness: 350 }}
              className="w-full max-w-md bg-[rgba(15,15,18,0.96)] border border-red-500/20 rounded-2xl shadow-[0_24px_50px_rgba(0,0,0,0.8)] overflow-hidden relative z-10 p-6 space-y-6"
              role="alertdialog"
              aria-labelledby="timeout-title"
              aria-describedby="timeout-desc"
            >
              {/* Outer top border warning highlight */}
              <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-red-500 via-amber-500 to-red-500" />

              {/* Warning Header */}
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center w-12 h-12 bg-red-500/10 border border-red-500/20 rounded-xl text-red-500 animate-pulse">
                  <ShieldAlert size={22} />
                </div>
                <div>
                  <h3 id="timeout-title" className="text-sm font-black uppercase tracking-wider text-white">
                    Clinical Session Timeout
                  </h3>
                  <p id="timeout-desc" className="text-[11px] text-[var(--text-dim)] font-mono uppercase mt-0.5">
                    HIPAA Inactivity Safe Protection
                  </p>
                </div>
              </div>

              {/* Countdown Progress Circle & Text */}
              <div className="flex flex-col items-center justify-center py-4 bg-white/[0.01] border border-white/[0.03] rounded-xl relative overflow-hidden">
                <div className="relative flex items-center justify-center w-24 h-24">
                  {/* SVG progress circle */}
                  <svg className="w-full h-full transform -rotate-90">
                    <circle
                      cx="48"
                      cy="48"
                      r="40"
                      className="stroke-white/[0.04]"
                      strokeWidth="6"
                      fill="transparent"
                    />
                    <circle
                      cx="48"
                      cy="48"
                      r="40"
                      className="stroke-red-500 transition-all duration-1000"
                      strokeWidth="6"
                      fill="transparent"
                      strokeDasharray="251.2"
                      strokeDashoffset={251.2 - (251.2 * secondsLeft) / 30}
                    />
                  </svg>
                  <div className="absolute flex flex-col items-center justify-center">
                    <Clock size={16} className="text-red-400 mb-0.5" />
                    <span className="text-xl font-black font-mono text-white leading-none">
                      {secondsLeft}s
                    </span>
                  </div>
                </div>
                <p className="text-[11px] text-[var(--text-secondary)] font-medium mt-4 max-w-[260px] text-center">
                  Your session is about to be terminated due to {Math.round(TIMEOUT_MS / 60 / 1000)} minutes of clinician inactivity.
                </p>
              </div>

              {/* Core Actions */}
              <div className="flex flex-col sm:flex-row gap-3 pt-2">
                <button
                  onClick={extendSession}
                  className="flex-1 px-4 py-2.5 text-xs font-bold uppercase tracking-wider text-white bg-red-600 hover:bg-red-500 active:bg-red-700 rounded-xl transition shadow-lg hover:shadow-red-500/15 flex items-center justify-center gap-2 cursor-pointer"
                >
                  <RefreshCw size={13} className="animate-spin" style={{ animationDuration: '4s' }} />
                  Extend Session
                </button>
                <button
                  onClick={handleManualLogout}
                  className="flex-1 px-4 py-2.5 text-xs font-bold uppercase tracking-wider text-gray-400 hover:text-white bg-white/[0.02] border border-white/[0.06] hover:bg-white/[0.05] hover:border-white/[0.1] rounded-xl transition flex items-center justify-center gap-2 cursor-pointer"
                >
                  <LogOut size={13} />
                  Log Out
                </button>
              </div>

              {/* Medical Notice */}
              <p className="text-[10px] leading-relaxed text-gray-500 font-medium italic text-center border-t border-white/[0.03] pt-4">
                Access audit records will reflect session timeouts and logoffs to comply with institutional security policies.
              </p>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
}
