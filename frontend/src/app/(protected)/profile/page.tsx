"use client";

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
    <div className="w-full max-w-4xl mx-auto space-y-8 pb-8">
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-bold text-[var(--text-primary)] mb-2">Patient Profile</h1>
        <p className="text-[var(--text-dim)]">Manage your personal and clinical information.</p>
      </motion.div>

      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }} className="panel p-8">
        {status.type && (
          <div className={`mb-6 p-4 flex items-center gap-3 text-sm border ${
            status.type === "success" 
              ? "bg-[var(--success-muted)] text-[var(--success)] border-[var(--success-border)]" 
              : "bg-[var(--danger-muted)] text-[var(--danger)] border-[var(--danger-border)]"
          }`} role="alert">
            {status.type === "success" ? <CheckCircle2 size={18} aria-hidden="true" /> : <AlertCircle size={18} aria-hidden="true" />}
            <p>{status.message}</p>
          </div>
        )}

        <form onSubmit={handleSave} className="space-y-6">
          <div className="flex items-center gap-6 mb-8 pb-8 border-b border-[var(--border)]">
            <div className="w-24 h-24 rounded-full flex items-center justify-center text-3xl font-bold text-[var(--text-primary)] shadow-lg bg-[var(--accent)] border-4 border-[var(--accent-border)]">
              {user.full_name?.[0]?.toUpperCase() || user.username[0].toUpperCase()}
            </div>
            <div>
              <h2 className="text-xl font-bold text-[var(--text-primary)]">{user.full_name || user.username}</h2>
              <p className="text-sm mt-1 text-[var(--text-dim)]">{user.email}</p>
              <div className="mt-3 status-badge status-badge-accent">
                <Activity size={14} aria-hidden="true" /> Tier: {user.plan_tier || "Standard"}
              </div>
            </div>
          </div>

          <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Clinical Details</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-1.5">
              <label className="section-label" htmlFor="profile-fullname">Full Name</label>
              <div className="relative">
                <User size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-dim)]" aria-hidden="true" />
                <input id="profile-fullname" type="text" name="full_name" value={formData.full_name || ""} onChange={handleChange} className="input-clinical pl-10" aria-label="Full name" />
              </div>
            </div>
            
            <div className="space-y-1.5">
              <label className="section-label" htmlFor="profile-email">Email</label>
              <div className="relative">
                <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-dim)]" aria-hidden="true" />
                <input id="profile-email" type="email" name="email" value={formData.email || ""} disabled className="input-clinical pl-10 opacity-50 cursor-not-allowed" aria-label="Email (read-only)" />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="section-label" htmlFor="profile-gender">Gender</label>
              <select id="profile-gender" name="gender" value={formData.gender || ""} onChange={handleChange} className="input-clinical appearance-none" aria-label="Gender">
                <option value="" className="bg-[var(--bg-card)]">Select Gender</option>
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
              <select id="profile-blood" name="blood_type" value={formData.blood_type || ""} onChange={handleChange} className="input-clinical appearance-none" aria-label="Blood type">
                <option value="" className="bg-[var(--bg-card)]">Select Type</option>
                <option value="A+" className="bg-[var(--bg-card)]">A+</option><option value="A-" className="bg-[var(--bg-card)]">A-</option>
                <option value="B+" className="bg-[var(--bg-card)]">B+</option><option value="B-" className="bg-[var(--bg-card)]">B-</option>
                <option value="AB+" className="bg-[var(--bg-card)]">AB+</option><option value="AB-" className="bg-[var(--bg-card)]">AB-</option>
                <option value="O+" className="bg-[var(--bg-card)]">O+</option><option value="O-" className="bg-[var(--bg-card)]">O-</option>
              </select>
            </div>

            <div className="flex gap-4">
              <div className="space-y-1.5 flex-1">
                <label className="section-label" htmlFor="profile-height">Height (CM)</label>
                <input id="profile-height" type="number" name="height" value={formData.height || ""} onChange={handleChange} placeholder="175" className="input-clinical" aria-label="Height in centimeters" />
              </div>
              <div className="space-y-1.5 flex-1">
                <label className="section-label" htmlFor="profile-weight">Weight (KG)</label>
                <input id="profile-weight" type="number" name="weight" value={formData.weight || ""} onChange={handleChange} placeholder="70" className="input-clinical" aria-label="Weight in kilograms" />
              </div>
            </div>
          </div>

          <div className="space-y-1.5 pt-4">
            <label className="section-label" htmlFor="profile-history">Medical History / About</label>
            <textarea 
              id="profile-history"
              name="about_me" 
              value={formData.about_me || ""} 
              onChange={handleChange} 
              rows={4}
              placeholder="Any known allergies, chronic conditions, or past surgeries..."
              className="input-clinical resize-none h-auto"
              aria-label="Medical history"
            />
          </div>

          <div className="pt-4 flex justify-end">
            <button type="submit" disabled={loading} className="btn btn-primary px-8 py-3 text-sm flex items-center gap-2" aria-label={loading ? "Saving profile" : "Save profile"}>
              {loading ? "Saving..." : <><Save size={16} aria-hidden="true" /> Save Profile</>}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}
