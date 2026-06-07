import { useState, useEffect } from "react";
import { signup, login } from "@/lib/api";
import { useAuthStore } from "@/lib/auth";
import { useNavigate, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Activity, Lock, Mail, User, ArrowRight, ShieldCheck, Sparkles, Database, BrainCircuit } from "lucide-react";

export default function SignupPage() {
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
  }, []);

  const [formData, setFormData] = useState({ username: "", email: "", password: "", full_name: "", dob: "" });

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  
  const { setAuth } = useAuthStore();
  const navigate = useNavigate();

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await signup(formData);
      const res = await login(formData.username, formData.password);
      useAuthStore.getState().setAuth(res.access_token, null as any);
      const { fetchProfile } = await import("@/lib/api");
      const profile = await fetchProfile();
      setAuth(res.access_token, profile);
      navigate("/dashboard");
    } catch (err: any) {
      setError(err.message || "Failed to sign up.");
    } finally {
      setLoading(false);
    }
  };

  const fields = [
    { id: "signup-fullname", label: "Full Name", icon: User, type: "text", value: formData.full_name, placeholder: "Dr. John Doe", onChange: (v: string) => setFormData({ ...formData, full_name: v }) },
    { id: "signup-username", label: "Username", icon: User, type: "text", value: formData.username, placeholder: "Username identifier", onChange: (v: string) => setFormData({ ...formData, username: v }) },
    { id: "signup-dob", label: "Date of Birth", icon: Activity, type: "date", value: formData.dob, placeholder: "", onChange: (v: string) => setFormData({ ...formData, dob: v }) },
    { id: "signup-email", label: "Email Address", icon: Mail, type: "email", value: formData.email, placeholder: "name@hospital.org", onChange: (v: string) => setFormData({ ...formData, email: v }) },
    { id: "signup-password", label: "Password", icon: Lock, type: "password", value: formData.password, placeholder: "Strong password", onChange: (v: string) => setFormData({ ...formData, password: v }), minLength: 8 },
  ];

  if (!mounted) {
    return <div className="min-h-screen bg-[#09090b]" />;
  }

  return (
    <div className="min-h-screen flex bg-[var(--bg-primary)] overflow-hidden relative">
      {/* Dynamic Mesh Gradients */}
      <div className="absolute top-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-[var(--accent)]/5 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-[var(--accent-emerald)]/3 blur-[120px] pointer-events-none" />

      {/* Left Panel: Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 lg:p-12 relative border-r border-[var(--border)] z-20">
        <div className="max-w-sm w-full relative">
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
                <span className="text-[9px] font-bold uppercase tracking-wider text-[var(--text-secondary)]">Create Terminal Key</span>
              </div>
              <h1 className="text-xl font-black tracking-widest text-[var(--text-primary)] uppercase display-title">
                Registration
              </h1>
              <p className="text-[10px] text-[var(--text-secondary)] font-mono uppercase tracking-wider opacity-70">
                Submit credentials to connect a new client node.
              </p>
            </div>

            {error && (
              <motion.div
                initial={{ opacity: 0, y: -5 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-3 bg-[var(--danger-muted)] text-[var(--danger)] border border-[var(--danger-border)] text-[10px] font-mono rounded-lg mb-4 uppercase tracking-wide"
              >
                {error}
              </motion.div>
            )}

            <form onSubmit={handleSignup} className="space-y-4">
              {fields.map((field) => (
                <div key={field.id} className="space-y-1">
                  <label className="section-label" htmlFor={field.id}>{field.label}</label>
                  <div className="relative">
                    <field.icon size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-dim)]" />
                    <input
                      id={field.id}
                      type={field.type}
                      value={field.value}
                      onChange={(e) => field.onChange(e.target.value)}
                      placeholder={field.placeholder}
                      className="input-clinical pl-9"
                      required
                      minLength={(field as any).minLength}
                      aria-label={field.label}
                    />
                  </div>
                </div>
              ))}

              <button
                type="submit"
                disabled={loading}
                className="btn btn-cyber-primary w-full py-3 mt-4 flex items-center justify-center gap-2 cursor-pointer transition-all rounded-lg font-bold text-[11px] uppercase tracking-widest"
              >
                {loading ? (
                  <>
                    <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Creating Terminal...
                  </>
                ) : (
                  <>
                    Initialize Node
                    <ArrowRight size={13} />
                  </>
                )}
              </button>
            </form>

            <div className="pt-6 mt-6 border-t border-white/[0.04] text-center text-[10px] text-[var(--text-dim)] uppercase tracking-wider font-bold">
              Already registered?{" "}
              <Link to="/login" className="text-[var(--accent-purple)] font-bold hover:underline">
                Log In
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Right Panel: Visual */}
      <div className="hidden lg:flex w-1/2 relative overflow-hidden items-center justify-center bg-[#020204]/40 backdrop-blur-md">
        {/* Dot grid texture */}
        <div className="absolute inset-0 opacity-[0.035]" style={{ backgroundImage: "radial-gradient(circle at 1px 1px, #ffffff 1px, transparent 0)", backgroundSize: "24px 24px" }} />

        {/* Ambient glows */}
        <div className="absolute top-[30%] right-[20%] w-[320px] h-[320px] rounded-full bg-[var(--accent-purple)]/8 blur-[100px] animate-pulse-slow" />
        <div className="absolute bottom-[20%] left-[30%] w-[250px] h-[250px] rounded-full bg-[var(--accent-emerald)]/6 blur-[90px] animate-pulse-slow" />

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
          className="relative z-10 max-w-md text-center px-8 flex flex-col items-center"
        >
          {/* Central Logo HUD Container */}
          <div className="mb-10 relative h-48 w-48 flex items-center justify-center">
            {/* Spinning Dotted Outer Ring */}
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 30, repeat: Infinity, ease: "linear" }}
              className="absolute inset-0 border border-dashed border-[var(--accent-purple)]/30 rounded-full"
            />
            {/* Spinning Dashed Middle Ring */}
            <motion.div
              animate={{ rotate: -360 }}
              transition={{ duration: 40, repeat: Infinity, ease: "linear" }}
              className="absolute inset-4 border-2 border-dashed border-[var(--accent-emerald)]/20 rounded-full"
            />
            
            {/* Core Biometric Shield Icon */}
            <motion.div
              animate={{ scale: [0.97, 1.03, 0.97] }}
              transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
              className="w-24 h-24 rounded-full bg-[rgba(10,10,15,0.7)] border border-white/[0.06] flex items-center justify-center shadow-[0_0_35px_rgba(134,86,245,0.15)] relative z-10"
            >
              <ShieldCheck size={48} className="text-[var(--accent-purple)]" strokeWidth={1.5} />
            </motion.div>
          </div>

          <h2 className="text-3xl font-black uppercase tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-[var(--text-primary)] via-white to-[var(--text-secondary)] display-hero mb-4">
            Clinician Core Network
          </h2>
          <p className="text-[var(--text-secondary)] text-[11px] font-mono max-w-xs leading-relaxed uppercase tracking-wider mb-8 opacity-75">
            Gain immediate telemetry views, secure diagnostic enclaves, and full HL7 interop sandboxes.
          </p>

          {/* Feature list */}
          <div className="space-y-3 text-left w-64">
            {[
              { icon: BrainCircuit, text: "Clinical risk prediction nodes" },
              { icon: Database, text: "Retrieved local patient history" },
              { icon: ShieldCheck, text: "HIPAA-grade access boundaries" },
            ].map((item, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 + i * 0.1 }}
                className="flex items-center gap-3 p-2 bg-white/[0.015] border border-white/[0.03] rounded-xl text-[10px] text-[var(--text-secondary)] font-mono uppercase tracking-wider shadow-sm hover:border-[var(--accent-purple)]/30 hover:bg-white/[0.03] transition-all"
              >
                <div className="w-7 h-7 flex items-center justify-center bg-[rgba(255,255,255,0.02)] border border-white/[0.04] rounded-lg">
                  <item.icon size={13} className="text-[var(--accent-purple)]" />
                </div>
                <span>{item.text}</span>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
