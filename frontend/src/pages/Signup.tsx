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
    <div className="min-h-screen flex bg-[var(--bg-primary)] overflow-hidden">
      {/* Left Panel: Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 lg:p-12 bg-[#09090b] relative border-r border-[var(--border)] z-20">
        <div className="max-w-sm w-full space-y-6 relative z-10">

          {/* Header */}
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded bg-gradient-to-br from-[var(--accent)] to-[var(--accent-purple)] flex items-center justify-center text-white">
                <Sparkles size={14} />
              </div>
              <span className="text-xs font-bold uppercase tracking-wider text-[var(--text-secondary)]">Create Terminal Key</span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-[var(--text-primary)] uppercase">
              Registration
            </h1>
            <p className="text-xs text-[var(--text-secondary)] font-mono uppercase tracking-wider">
              Submit your credentials to connect a new client node.
            </p>
          </div>

          {error && (
            <motion.div
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-3 bg-[var(--danger-muted)] text-[var(--danger)] border border-[var(--danger-border)] text-xs font-mono rounded"
            >
              {error}
            </motion.div>
          )}

          <form onSubmit={handleSignup} className="space-y-4">
            {fields.map((field) => (
              <div key={field.id} className="space-y-1.5">
                <label className="section-label" htmlFor={field.id}>{field.label}</label>
                <div className="relative">
                  <field.icon size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-dim)]" />
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
              className="btn btn-primary w-full py-2.5 mt-2 flex items-center justify-center gap-2 cursor-pointer"
            >
              {loading ? (
                <>
                  <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  CREATING TERMINAL...
                </>
              ) : (
                <>
                  INITIALIZE NODE
                  <ArrowRight size={13} />
                </>
              )}
            </button>
          </form>

          <div className="text-center text-xs text-[var(--text-dim)]">
            Already registered?{" "}
            <Link to="/login" className="text-[var(--accent)] font-semibold hover:underline uppercase tracking-wider">
              Log In
            </Link>
          </div>
        </div>
      </div>

      {/* Right Panel: Visual */}
      <div className="hidden lg:flex w-1/2 relative overflow-hidden items-center justify-center bg-[#09090b]">
        {/* Dot grid texture */}
        <div className="absolute inset-0 opacity-[0.03]" style={{ backgroundImage: "radial-gradient(circle at 1px 1px, #ffffff 1px, transparent 0)", backgroundSize: "20px 20px" }} />

        {/* Ambient glows */}
        <div className="absolute top-[30%] right-[20%] w-[300px] h-[300px] rounded-full bg-[var(--accent)]/10 blur-[120px] animate-pulse" />
        <div className="absolute bottom-[20%] left-[30%] w-[250px] h-[250px] rounded-full bg-[var(--accent-emerald)]/10 blur-[100px] animate-pulse" />

        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="relative z-10 max-w-md text-center px-8"
        >
          {/* Central Logo Container */}
          <div className="mb-8 relative h-44 w-44 mx-auto flex items-center justify-center">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
              className="absolute inset-0 border border-dashed border-[var(--border-focus)] rounded-full"
            />
            <motion.div
              animate={{ rotate: -360 }}
              transition={{ duration: 40, repeat: Infinity, ease: "linear" }}
              className="absolute inset-4 border border-[var(--border)] rounded-full"
            />
            <div className="w-20 h-20 rounded-full bg-[rgba(255,255,255,0.02)] border border-[var(--border-focus)] flex items-center justify-center shadow-[0_0_24px_rgba(99,102,241,0.15)] relative z-10">
              <ShieldCheck size={40} className="text-[var(--accent)]" strokeWidth={1.5} />
            </div>
          </div>

          <h2 className="text-3xl font-extrabold tracking-tight text-[var(--text-primary)] mb-3 uppercase">
            Clinician Core Network
          </h2>
          <p className="text-[var(--text-secondary)] text-xs font-mono max-w-xs mx-auto leading-relaxed uppercase tracking-wider mb-8">
            Gain immediate telemetry views, secure diagnostic enclaves, and full HL7 interop sandboxes.
          </p>

          {/* Feature list */}
          <div className="space-y-2 text-left max-w-xs mx-auto">
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
                className="flex items-center gap-2.5 text-[11px] text-[var(--text-secondary)] font-mono uppercase tracking-wider"
              >
                <div className="w-7 h-7 flex items-center justify-center bg-[rgba(255,255,255,0.02)] border border-[var(--border)] rounded">
                  <item.icon size={13} className="text-[var(--accent)]" />
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
