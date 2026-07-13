import { useState, useEffect } from "react";
import { useAuthStore } from "@/lib/auth";
import { login, fetchProfile } from "@/lib/api";
import { useNavigate, Link, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import { Activity, Lock, Mail, User, ArrowRight, HeartPulse, Sparkles, ShieldCheck } from "lucide-react";
import { useTranslation } from "@/lib/i18n";

export default function LoginPage() {
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  const isExpired = searchParams.get("expired") === "1";
  const [mounted, setMounted] = useState(false);
  const [inIframe, setInIframe] = useState(false);
  useEffect(() => {
    setMounted(true);
    try {
      setInIframe(window.self !== window.top);
    } catch (e) {
      setInIframe(true);
    }
  }, []);

  const [view, setView] = useState<'login' | 'forgot'>('login');
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
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

  const handleForgotPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccessMsg("");
    setLoading(true);

    try {
      const { forgotPassword } = await import("@/lib/api");
      const res = await forgotPassword(email);
      setSuccessMsg(res.message);
    } catch (err: any) {
      setError(err.message || "Failed to submit request.");
    } finally {
      setLoading(false);
    }
  };

  if (!mounted) {
    return <div className="min-h-screen bg-[#09090b]" />;
  }

  return (
    <div className="min-h-screen flex bg-[var(--bg-primary)] overflow-hidden relative">
      {/* Dynamic Mesh Gradients */}
      <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-[var(--accent)]/5 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-[var(--accent-purple)]/4 blur-[120px] pointer-events-none" />

      {/* Left Panel: Visual — Modern dashboard preview */}
      <div className="hidden lg:flex w-1/2 relative overflow-hidden items-center justify-center border-r border-[var(--border)] bg-[#020204]/40 backdrop-blur-md">
        {/* Dot grid texture */}
        <div className="absolute inset-0 opacity-[0.035]" style={{ backgroundImage: "radial-gradient(circle at 1px 1px, #ffffff 1px, transparent 0)", backgroundSize: "24px 24px" }} />

        {/* Ambient glows */}
        <div className="absolute top-[25%] left-[20%] w-[320px] h-[320px] rounded-full bg-[var(--accent)]/8 blur-[100px] animate-pulse-slow" />
        <div className="absolute bottom-[25%] right-[20%] w-[280px] h-[280px] rounded-full bg-[var(--accent-blue)]/6 blur-[90px] animate-pulse-slow" />

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="relative z-10 max-w-md text-center px-8 flex flex-col items-center"
        >
          {/* Central Logo HUD Container */}
          <div className="mb-10 relative h-48 w-48 flex items-center justify-center">
            {/* Spinning Dotted Outer Ring */}
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 35, repeat: Infinity, ease: "linear" }}
              className="absolute inset-0 border border-dashed border-[var(--accent)]/30 rounded-full"
            />
            {/* Spinning Dashed Middle Ring */}
            <motion.div
              animate={{ rotate: -360 }}
              transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
              className="absolute inset-4 border-2 border-dashed border-[var(--accent-blue)]/20 rounded-full"
            />
            {/* Solid Ring with ticks */}
            <motion.div
              animate={{ rotate: 180 }}
              transition={{ duration: 45, repeat: Infinity, ease: "linear" }}
              className="absolute inset-8 border border-white/[0.04] rounded-full flex items-center justify-between p-2"
            >
              <div className="w-1.5 h-1.5 bg-[var(--accent-blue)]/40 rounded-full" />
              <div className="w-1.5 h-1.5 bg-[var(--accent-purple)]/40 rounded-full" />
            </motion.div>
            
            {/* Core Biometric Heart Icon */}
            <motion.div
              animate={{ scale: [0.96, 1.04, 0.96] }}
              transition={{ duration: 2.5, repeat: Infinity, ease: "easeInOut" }}
              className="w-24 h-24 rounded-full bg-[rgba(10,10,15,0.7)] border border-white/[0.06] flex items-center justify-center shadow-[0_0_35px_rgba(95,95,247,0.15)] relative z-10"
            >
              <HeartPulse size={48} className="text-[var(--accent)]" strokeWidth={1.5} />
            </motion.div>
          </div>

          <h2 className="text-3xl font-black uppercase tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-[var(--text-primary)] via-white to-[var(--text-secondary)] display-hero mb-4">
            AI Healthcare Console
          </h2>
          <p className="text-[var(--text-secondary)] text-[11px] font-mono max-w-xs leading-relaxed uppercase tracking-wider mb-8 opacity-75">
            Access secure diagnostic modeling, real-time patient ADT telemetry, and on-premises clinical AI synthesis.
          </p>

          {/* Core system properties */}
          <div className="flex items-center justify-center gap-4 text-[9px] font-mono text-[var(--text-dim)] uppercase tracking-wider border-t border-white/[0.04] pt-6 w-full">
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 bg-[var(--success)] rounded-full animate-pulse" /> Secure Session
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 bg-[var(--accent)] rounded-full animate-pulse" /> JWT Encrypted
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 bg-[var(--warning)] rounded-full" /> Audit Active
            </span>
          </div>
        </motion.div>

        {/* Dynamic Telemetry Log Terminal */}
        <div className="absolute bottom-6 left-6 p-4 glass-card border border-white/[0.03] bg-black/40 font-mono text-[9px] text-[var(--accent-blue)] space-y-1 rounded-xl w-64 text-left shadow-2xl pointer-events-none">
          <div className="flex items-center gap-1.5 uppercase font-bold text-white mb-2 pb-1.5 border-b border-white/[0.05]">
            <span className="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-ping" /> Connection Console
          </div>
          <div>&gt; HOST: 127.0.0.1:8000</div>
          <div>&gt; FHIR BROKER: SYNCED</div>
          <div>&gt; SECURE TUNNEL: ACTIVE</div>
          <div className="text-[var(--success)]">&gt; SESSION STATUS: ONLINE</div>
        </div>
      </div>

      {/* Right Panel: Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 lg:p-12 relative z-20">
        <div className="max-w-sm w-full relative">
          {/* Glass Form Container */}
          <div className="glass-card p-8 md:p-10 border border-white/[0.04] shadow-[var(--shadow-lg)] rounded-2xl relative overflow-hidden backdrop-blur-3xl bg-[rgba(6,6,12,0.45)]">
            {/* Top light edge glow */}
            <div className="absolute top-0 inset-x-0 h-[1.5px] bg-gradient-to-r from-transparent via-[var(--accent)] to-transparent opacity-85" />
            
            {/* Header */}
            <div className="space-y-2 mb-6">
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded bg-gradient-to-br from-[var(--accent)] to-[var(--accent-purple)] flex items-center justify-center text-white shadow-md">
                  <Sparkles size={12} />
                </div>
                <span className="text-[9px] font-bold uppercase tracking-wider text-[var(--text-secondary)]">AI Clinical Hub</span>
              </div>
              <h1 className="text-xl font-black tracking-widest text-[var(--text-primary)] uppercase display-title">
                {view === 'login' ? t.signIn : "Reset Key"}
              </h1>
              <p className="text-[10px] text-[var(--text-secondary)] font-mono uppercase tracking-wider opacity-70">
                {view === 'login' ? "Enter credentials to link with telemetry." : "Request a secure temporary reset token."}
              </p>
            </div>

            {inIframe && (
              <motion.div
                initial={{ opacity: 0, y: -5 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-3 bg-[var(--warning-muted)] text-[var(--warning)] border border-[var(--warning-border)] text-[10px] font-mono rounded-xl mb-4 uppercase tracking-wide flex flex-col gap-1.5"
              >
                <div className="font-bold flex items-center gap-1">
                  <span>⚠️</span> Nested in Iframe
                </div>
                <div className="text-[9px] leading-relaxed">
                  Browser storage partitioning may cause issues or redirect to login on new tabs.
                </div>
                <a
                  href={window.location.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-1 text-center py-1.5 px-2 bg-yellow-500 hover:bg-yellow-400 text-black font-black rounded-lg transition-colors text-[9px] uppercase tracking-wider block font-bold"
                >
                  Open Direct App Link ↗️
                </a>
              </motion.div>
            )}

            {isExpired && !error && (
              <motion.div
                initial={{ opacity: 0, y: -5 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-3 bg-[var(--warning-muted)] text-[var(--warning)] border border-[var(--warning-border)] text-[10px] font-mono rounded-lg mb-4 uppercase tracking-wide"
              >
                Clinical session expired. Please sign in.
              </motion.div>
            )}

            {error && (
              <motion.div
                initial={{ opacity: 0, y: -5 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-3 bg-[var(--danger-muted)] text-[var(--danger)] border border-[var(--danger-border)] text-[10px] font-mono rounded-lg mb-4 uppercase tracking-wide"
              >
                {error}
              </motion.div>
            )}

            {successMsg && (
              <motion.div
                initial={{ opacity: 0, y: -5 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-3 bg-[var(--success-muted)] text-[var(--success)] border border-[var(--success-border)] text-[10px] font-mono rounded-lg mb-4 uppercase tracking-wide"
              >
                {successMsg}
              </motion.div>
            )}

            {view === 'login' ? (
              <form onSubmit={handleLogin} className="space-y-5">
                <div className="space-y-1.5">
                  <label className="section-label" htmlFor="login-username">{t.username}</label>
                  <div className="relative">
                    <User size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-dim)]" />
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
                    <button
                      type="button"
                      onClick={() => {
                        setView('forgot');
                        setError("");
                        setSuccessMsg("");
                      }}
                      className="text-[9px] font-bold text-[var(--accent-blue)] hover:underline uppercase tracking-wider bg-transparent border-0 cursor-pointer"
                    >
                      Forgot?
                    </button>
                  </div>
                  <div className="relative">
                    <Lock size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-dim)]" />
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
                  className="btn btn-cyber-primary w-full py-3 mt-4 flex items-center justify-center gap-2 cursor-pointer transition-all rounded-lg font-bold text-[11px] uppercase tracking-widest"
                >
                  {loading ? (
                    <>
                      <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Authenticating...
                    </>
                  ) : (
                    <>
                      {t.accessConsole}
                      <ArrowRight size={13} />
                    </>
                  )}
                </button>
              </form>
            ) : (
              <form onSubmit={handleForgotPassword} className="space-y-5">
                <div className="space-y-1.5">
                  <label className="section-label" htmlFor="forgot-email">Registered Email</label>
                  <div className="relative">
                    <Mail size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-dim)]" />
                    <input
                      id="forgot-email"
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="name@hospital.org"
                      className="input-clinical pl-9"
                      required
                      aria-label="Email Address"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading || !email}
                  className="btn btn-cyber-primary w-full py-3 mt-4 flex items-center justify-center gap-2 cursor-pointer transition-all rounded-lg font-bold text-[11px] uppercase tracking-widest"
                >
                  {loading ? (
                    <>
                      <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Sending...
                    </>
                  ) : (
                    <>
                      Send Reset Link
                      <ArrowRight size={13} />
                    </>
                  )}
                </button>

                <div className="text-center mt-4">
                  <button
                    type="button"
                    onClick={() => {
                      setView('login');
                      setError("");
                      setSuccessMsg("");
                    }}
                    className="text-[9px] font-bold text-[var(--text-secondary)] hover:text-white hover:underline uppercase tracking-wider bg-transparent border-0 cursor-pointer"
                  >
                    Back to Sign In
                  </button>
                </div>
              </form>
            )}

            <div className="pt-6 mt-6 border-t border-white/[0.04] text-center text-[10px] text-[var(--text-dim)] uppercase tracking-wider font-bold">
              Don&apos;t have terminal key?{" "}
              <Link to="/signup" className="text-[var(--accent-blue)] font-bold hover:underline">
                Request Admission
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
