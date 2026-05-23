"use client";

import { useState } from "react";
import { useAuthStore } from "@/lib/auth";
import { login, fetchProfile } from "@/lib/api";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Activity, Lock, User, ArrowRight, HeartPulse, Sparkles, ShieldCheck } from "lucide-react";
import Link from "next/link";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  
  const { setAuth } = useAuthStore();
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await login(username, password);
      useAuthStore.getState().setAuth(res.access_token, null as any);
      const profile = await fetchProfile();
      setAuth(res.access_token, profile);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Failed to login. Please check your credentials.");
      useAuthStore.getState().logout();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex bg-[var(--bg-primary)]">
      {/* Left Panel: Visual — Surgical dark with subtle animation */}
      <div className="hidden lg:flex w-1/2 relative overflow-hidden items-center justify-center bg-[var(--bg-secondary)] border-r border-[var(--border)]">
        {/* Dot grid texture */}
        <div className="absolute inset-0 opacity-[0.07]" style={{ backgroundImage: "radial-gradient(circle at 1px 1px, var(--text-dim) 1px, transparent 0)", backgroundSize: "24px 24px" }} />

        {/* Accent glow — subtle, not garish */}
        <div className="absolute top-[20%] left-[30%] w-[300px] h-[300px] rounded-full bg-[var(--accent)]/5 blur-[100px]" />
        <div className="absolute bottom-[10%] right-[20%] w-[200px] h-[200px] rounded-full bg-[var(--accent-emerald)]/5 blur-[80px]" />

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="relative z-10 max-w-md text-center px-8"
        >
          {/* Central Icon */}
          <div className="mb-10 relative h-48 w-48 mx-auto flex items-center justify-center">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 40, repeat: Infinity, ease: "linear" }}
              className="absolute inset-0 border border-dashed border-[var(--border-focus)] rounded-full"
            />
            <motion.div
              animate={{ rotate: -360 }}
              transition={{ duration: 60, repeat: Infinity, ease: "linear" }}
              className="absolute inset-6 border border-[var(--border)] rounded-full"
            />
            <div className="bg-[var(--bg-card)] border border-[var(--border)] p-6 relative z-10">
              <HeartPulse size={56} className="text-[var(--accent)]" strokeWidth={1.5} />
            </div>
          </div>

          <h2 className="text-3xl font-semibold text-[var(--text-primary)] tracking-tight mb-4 leading-tight">
            Welcome Back to<br />Intelligent Health
          </h2>
          <p className="text-[var(--text-secondary)] text-sm leading-relaxed max-w-sm mx-auto">
            Log in to view your latest predictions, chat with your AI medical copilot, and track your vital trends.
          </p>

          {/* Trust indicators */}
          <div className="mt-8 flex items-center justify-center gap-6 text-[11px] font-mono text-[var(--text-dim)] uppercase tracking-widest">
            <span className="flex items-center gap-1.5">
              <ShieldCheck size={12} className="text-[var(--accent-emerald)]" /> Access Control
            </span>
            <span className="flex items-center gap-1.5">
              <Lock size={12} className="text-[var(--accent)]" /> JWT Sessions
            </span>
            <span className="flex items-center gap-1.5">
              <Activity size={12} className="text-[var(--warning)]" /> Audit Logs
            </span>
          </div>
        </motion.div>
      </div>

      {/* Right Panel: Login Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 lg:p-12 bg-[var(--bg-primary)] relative z-20">
        <div className="max-w-md w-full space-y-6 relative z-10">

          {/* Logo mark */}
          <div className="flex items-center gap-3 mb-2">
            <div className="w-8 h-8 flex items-center justify-center bg-[var(--bg-card)] border border-[var(--border)]">
              <Sparkles size={16} className="text-[var(--text-primary)]" />
            </div>
            <span className="text-sm font-semibold text-[var(--text-primary)] tracking-tight">
              AI Healthcare<span className="text-[var(--text-secondary)] ml-1">System</span>
            </span>
          </div>

          <div>
            <h1 className="text-2xl lg:text-3xl font-semibold text-[var(--text-primary)] tracking-tight mb-1">
              Sign in
            </h1>
            <p className="text-[var(--text-secondary)] text-sm">
              Enter your credentials to access the command center.
            </p>
          </div>

          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-3 flex items-start gap-2 bg-[var(--danger-muted)] text-[var(--danger)] border border-[var(--danger-border)]"
            >
              <Activity size={14} className="shrink-0 mt-0.5" />
              <p className="text-xs font-mono uppercase tracking-wider">{error}</p>
            </motion.div>
          )}

          <form onSubmit={handleLogin} className="space-y-5">
            <div className="space-y-1.5">
              <label className="section-label ml-0.5" htmlFor="login-username">Username</label>
              <div className="relative">
                <User size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-dim)]" />
                <input
                  id="login-username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter your username"
                  className="input-clinical pl-10"
                  required
                  aria-label="Username"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between items-center ml-0.5">
                <label className="section-label" htmlFor="login-password">Password</label>
                <a href="#" className="text-[11px] font-semibold text-[var(--accent)] hover:text-[var(--text-primary)] transition-colors tracking-wider uppercase">
                  Forgot?
                </a>
              </div>
              <div className="relative">
                <Lock size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-dim)]" />
                <input
                  id="login-password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="input-clinical pl-10"
                  required
                  aria-label="Password"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || !username || !password}
              className="btn btn-primary w-full py-3 text-sm group relative overflow-hidden mt-2"
              aria-label="Sign in"
            >
              {/* Hover sweep effect */}
              <div className="absolute inset-0 bg-[var(--accent-hover)] translate-x-[-100%] group-hover:translate-x-0 transition-transform duration-300 ease-out" />
              <span className="relative z-10 flex items-center justify-center gap-2 w-full font-semibold uppercase tracking-widest text-[12px]">
                {loading ? (
                  <>
                    <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: "linear" }}>
                      <Activity size={14} />
                    </motion.div>
                    Authenticating...
                  </>
                ) : (
                  <>
                    Sign In
                    <ArrowRight size={14} />
                  </>
                )}
              </span>
            </button>
          </form>

          <p className="text-center text-[var(--text-dim)] font-medium text-xs pt-2">
            Don&apos;t have an account?{" "}
            <Link href="/signup" className="text-[var(--accent)] hover:text-[var(--text-primary)] font-bold transition-colors">
              Create one now
            </Link>
          </p>

          {/* Mobile-only trust bar */}
          <div className="lg:hidden flex items-center justify-center gap-6 pt-4 text-[11px] font-mono text-[var(--text-dim)] uppercase tracking-widest border-t border-[var(--border)]">
            <span className="flex items-center gap-1.5">
              <ShieldCheck size={12} className="text-[var(--accent-emerald)]" /> Access Control
            </span>
            <span className="flex items-center gap-1.5">
              <Lock size={12} className="text-[var(--accent)]" /> JWT Sessions
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
