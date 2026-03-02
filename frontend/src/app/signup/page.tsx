"use client";

import { useState } from "react";
import { signup, login } from "@/lib/api";
import { useAuthStore } from "@/lib/auth";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Activity, Lock, Mail, User, ArrowRight, ShieldCheck, Sparkles, Database, BrainCircuit } from "lucide-react";
import Link from "next/link";

export default function SignupPage() {
  const [formData, setFormData] = useState({ username: "", email: "", password: "", full_name: "", dob: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  
  const { setAuth } = useAuthStore();
  const router = useRouter();

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
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Failed to sign up.");
    } finally {
      setLoading(false);
    }
  };

  const fields = [
    { id: "signup-fullname", label: "Full Name", icon: User, type: "text", value: formData.full_name, placeholder: "e.g. Dr. John Doe", onChange: (v: string) => setFormData({ ...formData, full_name: v }) },
    { id: "signup-username", label: "Username", icon: User, type: "text", value: formData.username, placeholder: "Choose a username", onChange: (v: string) => setFormData({ ...formData, username: v }) },
    { id: "signup-dob", label: "Date of Birth", icon: Activity, type: "date", value: formData.dob, placeholder: "", onChange: (v: string) => setFormData({ ...formData, dob: v }) },
    { id: "signup-email", label: "Email Address", icon: Mail, type: "email", value: formData.email, placeholder: "you@hospital.org", onChange: (v: string) => setFormData({ ...formData, email: v }) },
    { id: "signup-password", label: "Password", icon: Lock, type: "password", value: formData.password, placeholder: "Create a strong password", onChange: (v: string) => setFormData({ ...formData, password: v }), minLength: 8 },
  ];

  return (
    <div className="min-h-screen flex bg-[var(--bg-primary)]">
      {/* Left Panel: Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 lg:p-12 bg-[var(--bg-primary)] relative border-r border-[var(--border)] z-20">
        <div className="max-w-md w-full space-y-5 relative z-10">

          {/* Logo mark */}
          <div className="flex items-center gap-3 mb-1">
            <div className="w-8 h-8 flex items-center justify-center bg-[var(--bg-card)] border border-[var(--border)]">
              <Sparkles size={16} className="text-[var(--text-primary)]" />
            </div>
            <span className="text-sm font-semibold text-[var(--text-primary)] tracking-tight">
              AI Healthcare<span className="text-[var(--text-secondary)] ml-1">System</span>
            </span>
          </div>

          <div>
            <h1 className="text-2xl lg:text-3xl font-semibold text-[var(--text-primary)] tracking-tight mb-1">
              Create your account
            </h1>
            <p className="text-[var(--text-secondary)] text-sm">
              Join the next generation of intelligent healthcare.
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

          <form onSubmit={handleSignup} className="space-y-4">
            {fields.map((field) => (
              <div key={field.id} className="space-y-1.5">
                <label className="section-label ml-0.5" htmlFor={field.id}>{field.label}</label>
                <div className="relative">
                  <field.icon size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-dim)]" />
                  <input
                    id={field.id}
                    type={field.type}
                    value={field.value}
                    onChange={(e) => field.onChange(e.target.value)}
                    placeholder={field.placeholder}
                    className="input-clinical pl-10"
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
              className="btn btn-primary w-full py-3 text-sm group relative overflow-hidden mt-2"
              aria-label="Create account"
            >
              <div className="absolute inset-0 bg-[var(--accent-hover)] translate-x-[-100%] group-hover:translate-x-0 transition-transform duration-300 ease-out" />
              <span className="relative z-10 flex items-center justify-center gap-2 w-full font-semibold uppercase tracking-widest text-[12px]">
                {loading ? (
                  <>
                    <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: "linear" }}>
                      <Activity size={14} />
                    </motion.div>
                    Creating Account...
                  </>
                ) : (
                  <>
                    Create Account
                    <ArrowRight size={14} />
                  </>
                )}
              </span>
            </button>
          </form>

          <p className="text-center text-[var(--text-dim)] font-medium text-xs pt-2">
            Already have an account?{" "}
            <Link href="/login" className="text-[var(--accent)] hover:text-[var(--text-primary)] font-bold transition-colors">
              Sign in here
            </Link>
          </p>
        </div>
      </div>

      {/* Right Panel: Visual */}
      <div className="hidden lg:flex w-1/2 relative overflow-hidden items-center justify-center bg-[var(--bg-secondary)]">
        {/* Dot grid texture */}
        <div className="absolute inset-0 opacity-[0.07]" style={{ backgroundImage: "radial-gradient(circle at 1px 1px, var(--text-dim) 1px, transparent 0)", backgroundSize: "24px 24px" }} />

        {/* Accent glow */}
        <div className="absolute top-[30%] right-[20%] w-[250px] h-[250px] rounded-full bg-[var(--accent)]/5 blur-[100px]" />
        <div className="absolute bottom-[20%] left-[30%] w-[200px] h-[200px] rounded-full bg-[var(--accent-emerald)]/5 blur-[80px]" />

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="relative z-10 max-w-md text-center px-8"
        >
          {/* Central Icon */}
          <div className="mb-10 relative h-48 w-48 mx-auto flex items-center justify-center">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 30, repeat: Infinity, ease: "linear" }}
              className="absolute inset-0 border border-dashed border-[var(--border-focus)] rounded-full"
            />
            <motion.div
              animate={{ rotate: -360 }}
              transition={{ duration: 50, repeat: Infinity, ease: "linear" }}
              className="absolute inset-6 border border-[var(--border)] rounded-full"
            />
            <div className="bg-[var(--bg-card)] border border-[var(--border)] p-6 relative z-10">
              <ShieldCheck size={56} className="text-[var(--accent)]" strokeWidth={1.5} />
            </div>
          </div>

          <h2 className="text-3xl font-semibold text-[var(--text-primary)] tracking-tight mb-4 leading-tight">
            Your Health Data,<br />Secured & Analyzed
          </h2>
          <p className="text-[var(--text-secondary)] text-sm leading-relaxed max-w-sm mx-auto">
            Enterprise-grade medical predictions powered by our Singularity Tri-Tier AI Engine with full HIPAA compliance.
          </p>

          {/* Feature list */}
          <div className="mt-8 space-y-3 text-left max-w-xs mx-auto">
            {[
              { icon: BrainCircuit, text: "Multi-organ diagnostic AI models" },
              { icon: Database, text: "RAG-powered clinical copilot" },
              { icon: ShieldCheck, text: "End-to-end encrypted health records" },
            ].map((item, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 + i * 0.1 }}
                className="flex items-center gap-3 text-[12px] text-[var(--text-secondary)]"
              >
                <div className="w-7 h-7 flex items-center justify-center bg-[var(--accent-muted)] border border-[var(--accent-border)]">
                  <item.icon size={14} className="text-[var(--accent)]" />
                </div>
                <span className="font-medium">{item.text}</span>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
