import { useState, useEffect } from "react";
import { resetPassword } from "@/lib/api";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Lock, ArrowRight, ShieldCheck, Sparkles, Check, X } from "lucide-react";

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") || "";
  const navigate = useNavigate();

  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
  }, []);

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  // Real-time validation criteria
  const isMinLength = password.length >= 8;
  const hasLetter = /[A-Za-z]/.test(password);
  const hasNumber = /\d/.test(password);
  const passwordsMatch = password === confirmPassword && confirmPassword.length > 0;
  const isValid = isMinLength && hasLetter && hasNumber && passwordsMatch;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isValid) return;
    setError("");
    setSuccess("");
    setLoading(true);

    try {
      const res = await resetPassword(token, password);
      setSuccess(res.message || "Password updated successfully. Redirecting...");
      setTimeout(() => {
        navigate("/login");
      }, 3000);
    } catch (err: any) {
      setError(err.message || "Failed to reset password.");
    } finally {
      setLoading(false);
    }
  };

  if (!mounted) {
    return <div className="min-h-screen bg-[#09090b]" />;
  }

  return (
    <div className="min-h-screen flex bg-[var(--bg-primary)] overflow-hidden relative items-center justify-center p-6">
      {/* Dynamic Mesh Gradients */}
      <div className="absolute top-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-[var(--accent)]/5 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-[var(--accent-purple)]/4 blur-[120px] pointer-events-none" />

      <div className="max-w-sm w-full relative z-20">
        {/* Glass Form Container */}
        <div className="glass-card p-8 md:p-10 border border-white/[0.04] shadow-[var(--shadow-lg)] rounded-2xl relative overflow-hidden backdrop-blur-3xl bg-[rgba(6,6,12,0.45)]">
          {/* Top light edge glow */}
          <div className="absolute top-0 inset-x-0 h-[1.5px] bg-gradient-to-r from-transparent via-[var(--accent-purple)] to-transparent opacity-85" />
          
          {/* Header */}
          <div className="space-y-2 mb-6">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded bg-gradient-to-br from-[var(--accent-purple)] to-[var(--accent)] flex items-center justify-center text-white shadow-md">
                <Sparkles size={12} />
              </div>
              <span className="text-[9px] font-bold uppercase tracking-wider text-[var(--text-secondary)]">Terminal Key Reset</span>
            </div>
            <h1 className="text-xl font-black tracking-widest text-[var(--text-primary)] uppercase display-title">
              New Password
            </h1>
            <p className="text-[10px] text-[var(--text-secondary)] font-mono uppercase tracking-wider opacity-70">
              Establish a new secure authentication credential.
            </p>
          </div>

          {!token ? (
            <div className="p-3 bg-[var(--danger-muted)] text-[var(--danger)] border border-[var(--danger-border)] text-[10px] font-mono rounded-lg mb-4 uppercase tracking-wide text-center">
              ⚠️ Invalid session. No token provided.
              <div className="mt-4">
                <Link to="/login" className="btn btn-cyber-primary py-1.5 px-4 font-bold inline-block text-[9px]">
                  Return to Sign In
                </Link>
              </div>
            </div>
          ) : (
            <>
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -5 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="p-3 bg-[var(--danger-muted)] text-[var(--danger)] border border-[var(--danger-border)] text-[10px] font-mono rounded-lg mb-4 uppercase tracking-wide"
                >
                  {error}
                </motion.div>
              )}

              {success && (
                <motion.div
                  initial={{ opacity: 0, y: -5 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="p-3 bg-[var(--success-muted)] text-[var(--success)] border border-[var(--success-border)] text-[10px] font-mono rounded-lg mb-4 uppercase tracking-wide"
                >
                  {success}
                </motion.div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-1">
                  <label className="section-label" htmlFor="reset-new-password">New Password</label>
                  <div className="relative">
                    <Lock size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-dim)]" />
                    <input
                      id="reset-new-password"
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••"
                      className="input-clinical pl-9"
                      required
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="section-label" htmlFor="reset-confirm-password">Confirm Password</label>
                  <div className="relative">
                    <Lock size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-dim)]" />
                    <input
                      id="reset-confirm-password"
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="••••••••"
                      className="input-clinical pl-9"
                      required
                    />
                  </div>
                </div>

                {/* Password Strength Validation Rules Display */}
                <div className="p-3 bg-white/[0.02] border border-white/[0.04] rounded-lg space-y-1.5 font-mono text-[9px] uppercase tracking-wide text-[var(--text-dim)]">
                  <div className="flex items-center gap-1.5">
                    {isMinLength ? <Check size={10} className="text-[var(--success)]" /> : <X size={10} className="text-[var(--danger)]" />}
                    <span className={isMinLength ? "text-white" : ""}>At least 8 characters</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    {hasLetter ? <Check size={10} className="text-[var(--success)]" /> : <X size={10} className="text-[var(--danger)]" />}
                    <span className={hasLetter ? "text-white" : ""}>Contains letters</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    {hasNumber ? <Check size={10} className="text-[var(--success)]" /> : <X size={10} className="text-[var(--danger)]" />}
                    <span className={hasNumber ? "text-white" : ""}>Contains numbers</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    {passwordsMatch ? <Check size={10} className="text-[var(--success)]" /> : <X size={10} className="text-[var(--danger)]" />}
                    <span className={passwordsMatch ? "text-white" : ""}>Passwords match</span>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading || !isValid}
                  className="btn btn-cyber-primary w-full py-3 mt-4 flex items-center justify-center gap-2 cursor-pointer transition-all rounded-lg font-bold text-[11px] uppercase tracking-widest"
                >
                  {loading ? (
                    <>
                      <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Updating Key...
                    </>
                  ) : (
                    <>
                      Update Password
                      <ArrowRight size={13} />
                    </>
                  )}
                </button>
              </form>

              <div className="pt-6 mt-6 border-t border-white/[0.04] text-center text-[10px] text-[var(--text-dim)] uppercase tracking-wider font-bold">
                <Link to="/login" className="text-[var(--accent-purple)] font-bold hover:underline">
                  Back to Sign In
                </Link>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
