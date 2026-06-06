import { useState, useEffect } from "react";
import { useAuthStore } from "@/lib/auth";
import { login, fetchProfile } from "@/lib/api";
import { useNavigate, Link, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import { Activity, Lock, User, ArrowRight, HeartPulse, Sparkles, ShieldCheck } from "lucide-react";
import { useTranslation } from "@/lib/i18n";

export default function LoginPage() {
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  const isExpired = searchParams.get("expired") === "1";
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
  }, []);

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  
  const { setAuth } = useAuthStore();
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await login(username, password);
      useAuthStore.getState().setAuth(res.access_token, null as any);
      const profile = await fetchProfile();
      setAuth(res.access_token, profile);
      navigate("/dashboard");
    } catch (err: any) {
      setError(err.message || "Failed to login. Please check your credentials.");
      useAuthStore.getState().logout();
    } finally {
      setLoading(false);
    }
  };

  if (!mounted) {
    return <div className="min-h-screen bg-[#09090b]" />;
  }

  return (
    <div className="min-h-screen flex bg-[var(--bg-primary)] overflow-hidden">
      {/* Left Panel: Visual — Modern dashboard preview */}
      <div className="hidden lg:flex w-1/2 relative overflow-hidden items-center justify-center bg-[#09090b] border-r border-[var(--border)]">
        {/* Dot grid texture */}
        <div className="absolute inset-0 opacity-[0.03]" style={{ backgroundImage: "radial-gradient(circle at 1px 1px, #ffffff 1px, transparent 0)", backgroundSize: "20px 20px" }} />

        {/* Ambient glows */}
        <div className="absolute top-[20%] left-[20%] w-[350px] h-[350px] rounded-full bg-[var(--accent)]/10 blur-[120px] animate-pulse" />
        <div className="absolute bottom-[20%] right-[20%] w-[300px] h-[300px] rounded-full bg-[var(--accent-purple)]/10 blur-[100px] animate-pulse" />

        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="relative z-10 max-w-md text-center px-8"
        >
          {/* Central Logo Container */}
          <div className="mb-8 relative h-44 w-44 mx-auto flex items-center justify-center">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 30, repeat: Infinity, ease: "linear" }}
              className="absolute inset-0 border border-dashed border-[var(--border-focus)] rounded-full"
            />
            <motion.div
              animate={{ rotate: -360 }}
              transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
              className="absolute inset-4 border border-[var(--border)] rounded-full"
            />
            <div className="w-20 h-20 rounded-full bg-[rgba(255,255,255,0.02)] border border-[var(--border-focus)] flex items-center justify-center shadow-[0_0_24px_rgba(99,102,241,0.15)] relative z-10">
              <HeartPulse size={40} className="text-[var(--accent)]" strokeWidth={1.5} />
            </div>
          </div>

          <h2 className="text-3xl font-extrabold tracking-tight text-[var(--text-primary)] mb-3 uppercase">
            AI Healthcare Console
          </h2>
          <p className="text-[var(--text-secondary)] text-xs font-mono max-w-xs mx-auto leading-relaxed uppercase tracking-wider mb-8">
            Access secure diagnostic modeling, real-time patient ADT telemetry, and on-premises clinical AI synthesis.
          </p>

          {/* Core system properties */}
          <div className="flex items-center justify-center gap-4 text-[10px] font-mono text-[var(--text-dim)] uppercase tracking-wider">
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 bg-[var(--accent-emerald)] rounded-full" /> Secure Session
            </span>
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 bg-[var(--accent)] rounded-full" /> JWT Encrypted
            </span>
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 bg-[var(--warning)] rounded-full" /> Audit Active
            </span>
          </div>
        </motion.div>
      </div>

      {/* Right Panel: Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 lg:p-12 bg-[#09090b] relative z-20">
        <div className="max-w-sm w-full space-y-6 relative z-10">
          
          {/* Header */}
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded bg-gradient-to-br from-[var(--accent)] to-[var(--accent-purple)] flex items-center justify-center text-white">
                <Sparkles size={14} />
              </div>
              <span className="text-xs font-bold uppercase tracking-wider text-[var(--text-secondary)]">AI Clinical Hub</span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-[var(--text-primary)] uppercase">
              {t.signIn}
            </h1>
            <p className="text-xs text-[var(--text-secondary)] font-mono uppercase tracking-wider">
              Enter your credentials to link with the telemetry network.
            </p>
          </div>

          {isExpired && !error && (
            <motion.div
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-3 bg-[var(--warning-muted)] text-[var(--warning)] border border-[var(--warning-border)] text-xs font-mono rounded"
            >
              Your clinical session has expired due to inactivity. Please sign in again.
            </motion.div>
          )}

          {error && (
            <motion.div
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-3 bg-[var(--danger-muted)] text-[var(--danger)] border border-[var(--danger-border)] text-xs font-mono rounded"
            >
              {error}
            </motion.div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <div className="space-y-1.5">
              <label className="section-label" htmlFor="login-username">{t.username}</label>
              <div className="relative">
                <User size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-dim)]" />
                <input
                  id="login-username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Clinical staff username"
                  className="input-clinical pl-9"
                  required
                  aria-label="Username"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between items-center">
                <label className="section-label" htmlFor="login-password">{t.password}</label>
                <a href="#" className="text-[10px] font-bold text-[var(--accent)] hover:underline uppercase tracking-wider">
                  Forgot?
                </a>
              </div>
              <div className="relative">
                <Lock size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-dim)]" />
                <input
                  id="login-password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="input-clinical pl-9"
                  required
                  aria-label="Password"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || !username || !password}
              className="btn btn-primary w-full py-2.5 mt-2 flex items-center justify-center gap-2 cursor-pointer"
            >
              {loading ? (
                <>
                  <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  AUTHENTICATING...
                </>
              ) : (
                <>
                  {t.accessConsole}
                  <ArrowRight size={13} />
                </>
              )}
            </button>
          </form>

          <div className="pt-2 text-center text-xs text-[var(--text-dim)]">
            Don&apos;t have a terminal key?{" "}
            <Link to="/signup" className="text-[var(--accent)] font-semibold hover:underline uppercase tracking-wider">
              Request Admission
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
