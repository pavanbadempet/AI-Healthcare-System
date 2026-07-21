import React, { useState } from "react";
import { motion } from "framer-motion";
import { X, ShieldCheck, Key, Lock, Clock, AlertTriangle, Save } from "lucide-react";
import { toast } from "@/lib/toast";

interface SecurityLockoutModalProps {
  onClose: () => void;
}

export const SecurityLockoutModal: React.FC<SecurityLockoutModalProps> = ({ onClose }) => {
  const [twoFactorEnforced, setTwoFactorEnforced] = useState(true);
  const [maxFailedAttempts, setMaxFailedAttempts] = useState(5);
  const [lockoutDurationMinutes, setLockoutDurationMinutes] = useState(15);
  const [sessionIdleTimeoutMinutes, setSessionIdleTimeoutMinutes] = useState(30);
  const [ipWhitelistOnly, setIpWhitelistOnly] = useState(false);

  const handleSave = () => {
    toast.success("Security & Lockout Policy parameters updated!");
    onClose();
  };

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/80 backdrop-blur-md p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 15 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 15 }}
        className="bg-[#0b0c10] border border-white/10 rounded-2xl w-full max-w-lg max-h-[90vh] overflow-hidden flex flex-col shadow-2xl font-sans"
        role="dialog"
        aria-modal="true"
        aria-labelledby="security-title"
      >
        {/* Header */}
        <div className="bg-white/[0.02] border-b border-white/10 p-5 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 shrink-0">
              <ShieldCheck size={18} />
            </div>
            <div>
              <h2 id="security-title" className="text-sm font-bold text-white uppercase tracking-wider">
                Security & Account Lockout Policy
              </h2>
              <p className="text-[10px] text-[var(--text-secondary)] font-mono uppercase">
                HIPAA Authentication & Session Lockout Configuration
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-zinc-400 hover:text-white p-1.5 rounded-lg hover:bg-white/5 transition-colors"
            aria-label="Close modal"
          >
            <X size={18} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4 font-mono text-xs overflow-y-auto flex-1">
          {/* 2FA Enforce */}
          <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5 flex items-center justify-between font-sans">
            <div>
              <span className="text-xs font-bold text-white uppercase block flex items-center gap-1.5">
                <Key size={14} className="text-indigo-400" /> Mandatory 2FA Authentication
              </span>
              <span className="text-[10px] text-zinc-400 font-mono">Require TOTP or SMS OTP for all clinical users</span>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={twoFactorEnforced}
                onChange={(e) => setTwoFactorEnforced(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-zinc-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-zinc-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
            </label>
          </div>

          {/* Failed Attempts */}
          <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5 space-y-2 font-sans">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-white uppercase flex items-center gap-1.5">
                <Lock size={14} className="text-amber-400" /> Max Failed Login Threshold
              </span>
              <span className="text-xs font-bold text-amber-400 font-mono">{maxFailedAttempts} Attempts</span>
            </div>
            <input
              type="range"
              min={3}
              max={10}
              step={1}
              value={maxFailedAttempts}
              onChange={(e) => setMaxFailedAttempts(Number(e.target.value))}
              className="w-full accent-indigo-500 bg-zinc-800 h-1.5 rounded-lg cursor-pointer"
            />
          </div>

          {/* Lockout Duration */}
          <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5 flex items-center justify-between font-sans">
            <div>
              <span className="text-xs font-bold text-white uppercase block">Account Lockout Duration</span>
              <span className="text-[10px] text-zinc-400 font-mono">Time account remains suspended after threshold breach</span>
            </div>
            <select
              value={lockoutDurationMinutes}
              onChange={(e) => setLockoutDurationMinutes(Number(e.target.value))}
              className="bg-zinc-900 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-indigo-300 font-mono font-bold"
            >
              <option value={15}>15 Minutes</option>
              <option value={30}>30 Minutes</option>
              <option value={60}>60 Minutes</option>
            </select>
          </div>

          {/* Session Idle Timeout */}
          <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5 flex items-center justify-between font-sans">
            <div>
              <span className="text-xs font-bold text-white uppercase block flex items-center gap-1.5">
                <Clock size={14} className="text-blue-400" /> Session Idle Auto-Logout
              </span>
              <span className="text-[10px] text-zinc-400 font-mono">Inactivity delay before automatic session termination</span>
            </div>
            <select
              value={sessionIdleTimeoutMinutes}
              onChange={(e) => setSessionIdleTimeoutMinutes(Number(e.target.value))}
              className="bg-zinc-900 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-blue-300 font-mono font-bold"
            >
              <option value={15}>15 Minutes</option>
              <option value={30}>30 Minutes</option>
              <option value={60}>60 Minutes</option>
            </select>
          </div>

          {/* IP Whitelist */}
          <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5 flex items-center justify-between font-sans">
            <div>
              <span className="text-xs font-bold text-white uppercase block">Hospital Subnet IP Restriction</span>
              <span className="text-[10px] text-zinc-400 font-mono">Restrict EMR access to internal hospital facility IPs</span>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={ipWhitelistOnly}
                onChange={(e) => setIpWhitelistOnly(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-zinc-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-zinc-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
            </label>
          </div>
        </div>

        {/* Footer */}
        <div className="bg-white/[0.02] border-t border-white/10 p-4 flex items-center justify-between font-sans">
          <button
            onClick={onClose}
            className="btn btn-secondary text-xs uppercase font-bold tracking-wide py-2.5 px-4"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="btn bg-indigo-600 hover:bg-indigo-500 text-white text-xs uppercase font-bold tracking-wide py-2.5 px-5 flex items-center gap-2 rounded-xl shadow-lg shadow-indigo-600/20"
          >
            <Save size={14} /> Update Security Policy
          </button>
        </div>
      </motion.div>
    </div>
  );
};
