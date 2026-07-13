
import { useState, useEffect } from "react";
import { useAuthStore } from "@/lib/auth";
import { updateProfile, type UserProfile } from "@/lib/api";
import { motion } from "framer-motion";
import { User, Mail, Activity, Save, AlertCircle, CheckCircle2 } from "lucide-react";

export default function ProfilePage() {
  const { user, setUser } = useAuthStore();
  const [formData, setFormData] = useState<Partial<UserProfile>>({});
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<{ type: "success" | "error" | null, message: string }>({ type: null, message: "" });

  useEffect(() => {
    if (user) {
      setFormData(user);
    }
  }, [user]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setStatus({ type: null, message: "" });

    try {
      const updatedUser = await updateProfile(formData);
      setUser(updatedUser);
      setStatus({ type: "success", message: "Profile updated successfully." });
    } catch (err: any) {
      setStatus({ type: "error", message: err.message || "Failed to update profile." });
    } finally {
      setLoading(false);
    }
  };

  if (!user) return null;

  return (
    <div className="w-full max-w-3xl mx-auto space-y-6 pb-12 selection:bg-[var(--accent)] selection:text-white">
      <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-xl font-bold text-[var(--text-primary)] uppercase tracking-wider">Patient Profile</h1>
        <p className="text-xs text-[var(--text-secondary)] font-mono uppercase tracking-wide mt-1">Manage personal and clinical metrics.</p>
      </motion.div>

      <motion.div 
        initial={{ opacity: 0 }} 
        animate={{ opacity: 1 }} 
        transition={{ delay: 0.05 }} 
        className="panel p-6"
      >
        {status.type && (
          <div className={`mb-6 p-3 flex items-center gap-2 text-xs font-mono uppercase border rounded ${
            status.type === "success" 
              ? "bg-[var(--success-muted)] text-[var(--success)] border-[var(--success-border)]" 
              : "bg-[var(--danger-muted)] text-[var(--danger)] border-[var(--danger-border)]"
          }`} role="alert">
            {status.type === "success" ? <CheckCircle2 size={14} aria-hidden="true" /> : <AlertCircle size={14} aria-hidden="true" />}
            <p>{status.message}</p>
          </div>
        )}

        <form onSubmit={handleSave} className="space-y-6">
          <div className="flex items-center gap-6 mb-6 pb-6 border-b border-[var(--border)]">
            <div className="w-16 h-16 rounded-md bg-gradient-to-br from-[var(--accent)] to-[var(--accent-purple)] flex items-center justify-center text-xl font-bold text-white shadow-[0_0_12px_rgba(99,102,241,0.2)]">
              {user.full_name?.[0]?.toUpperCase() || user.username[0].toUpperCase()}
            </div>
            <div>
              <h2 className="text-sm font-bold text-[var(--text-primary)] uppercase tracking-wider">{user.full_name || user.username}</h2>
              <p className="text-xs text-[var(--text-secondary)] font-mono">{user.email}</p>
              <div className="mt-2.5 status-badge status-badge-accent">
                <Activity size={12} aria-hidden="true" /> Tier: {user.plan_tier || "Standard"}
              </div>
            </div>
          </div>

          <h3 className="section-title border-b border-[var(--border)] pb-2 mb-4">Clinical Details</h3>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="section-label" htmlFor="profile-fullname">Full Name</label>
              <div className="relative">
                <User size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-dim)]" aria-hidden="true" />
                <input id="profile-fullname" type="text" name="full_name" value={formData.full_name || ""} onChange={handleChange} className="input-clinical pl-9" aria-label="Full name" />
              </div>
            </div>
            
            <div className="space-y-1.5">
              <label className="section-label" htmlFor="profile-email">Email</label>
              <div className="relative">
                <Mail size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-dim)]" aria-hidden="true" />
                <input id="profile-email" type="email" name="email" value={formData.email || ""} disabled className="input-clinical pl-9 opacity-40 cursor-not-allowed" aria-label="Email (read-only)" />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="section-label" htmlFor="profile-gender">Gender</label>
              <select id="profile-gender" name="gender" value={formData.gender || ""} onChange={handleChange} className="input-clinical uppercase font-mono" aria-label="Gender">
                <option value="" className="bg-[var(--bg-card)]">-- SELECT GENDER --</option>
                <option value="Male" className="bg-[var(--bg-card)]">Male</option>
                <option value="Female" className="bg-[var(--bg-card)]">Female</option>
                <option value="Other" className="bg-[var(--bg-card)]">Other</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="section-label" htmlFor="profile-dob">Date of Birth</label>
              <input id="profile-dob" type="date" name="dob" value={formData.dob || ""} onChange={handleChange} className="input-clinical" aria-label="Date of birth" />
            </div>

            <div className="space-y-1.5">
              <label className="section-label" htmlFor="profile-blood">Blood Type</label>
              <select id="profile-blood" name="blood_type" value={formData.blood_type || ""} onChange={handleChange} className="input-clinical uppercase font-mono" aria-label="Blood type">
                <option value="" className="bg-[var(--bg-card)]">-- SELECT TYPE --</option>
                <option value="A+" className="bg-[var(--bg-card)]">A+</option><option value="A-" className="bg-[var(--bg-card)]">A-</option>
                <option value="B+" className="bg-[var(--bg-card)]">B+</option><option value="B-" className="bg-[var(--bg-card)]">B-</option>
                <option value="AB+" className="bg-[var(--bg-card)]">AB+</option><option value="AB-" className="bg-[var(--bg-card)]">AB-</option>
                <option value="O+" className="bg-[var(--bg-card)]">O+</option><option value="O-" className="bg-[var(--bg-card)]">O-</option>
              </select>
            </div>

            <div className="flex gap-4">
              <div className="space-y-1.5 flex-1">
                <label className="section-label" htmlFor="profile-height">Height (CM)</label>
                <input id="profile-height" type="number" name="height" value={formData.height || ""} onChange={handleChange} placeholder="Height in cm" className="input-clinical" aria-label="Height in centimeters" />
              </div>
              <div className="space-y-1.5 flex-1">
                <label className="section-label" htmlFor="profile-weight">Weight (KG)</label>
                <input id="profile-weight" type="number" name="weight" value={formData.weight || ""} onChange={handleChange} placeholder="Weight in kg" className="input-clinical" aria-label="Weight in kilograms" />
              </div>
            </div>
          </div>

          <div className="space-y-1.5 pt-2">
            <label className="section-label" htmlFor="profile-history">Clinical History Summary</label>
            <textarea 
              id="profile-history"
              name="about_me" 
              value={formData.about_me || ""} 
              onChange={handleChange} 
              rows={3}
              placeholder="Document known allergies, operations, or active drug therapies..."
              className="input-clinical resize-none h-auto uppercase font-mono"
              aria-label="Medical history"
            />
          </div>

          <div className="pt-2 flex justify-end">
            <button type="submit" disabled={loading} className="btn btn-primary px-6 py-2 flex items-center gap-1.5 cursor-pointer">
              {loading ? "Saving..." : <><Save size={14} aria-hidden="true" /> Save Profile</>}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}
