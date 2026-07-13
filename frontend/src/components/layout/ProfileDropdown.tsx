/**
 * ProfileDropdown – User profile and session dropdown.
 * Extracted from TopNav.tsx for maintainability.
 */
import { useState, useRef, useEffect } from "react";
import { Link } from "react-router-dom";
import { Settings, Shield, CreditCard, LogOut, ChevronDown } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { prefetchRoute } from "@/lib/prefetch";
import Tooltip from "./Tooltip";

interface User {
  full_name?: string;
  username: string;
  role: string;
}

interface ProfileDropdownProps {
  user: User;
  logout: () => void;
  adminLabel: string;
}

export default function ProfileDropdown({ user, logout, adminLabel }: ProfileDropdownProps) {
  const [profileOpen, setProfileOpen] = useState(false);
  const profileRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (event: MouseEvent) => {
      if (profileOpen && profileRef.current && !profileRef.current.contains(event.target as Node)) {
        setProfileOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [profileOpen]);

  const displayName = user.full_name || user.username;
  const initial = displayName.charAt(0).toUpperCase();

  return (
    <div ref={profileRef} className="relative">
      <Tooltip content="Account Settings & Session" position="bottom">
        <button
          onClick={() => setProfileOpen(!profileOpen)}
          className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-white/[0.02] border border-[var(--border)] hover:bg-white/[0.05] hover:border-[var(--border-focus)] transition-all cursor-pointer"
          aria-label={`Profile: ${displayName}`}
        >
          <div className="w-5.5 h-5.5 rounded-md bg-[var(--accent-muted)] border border-[var(--accent-border)] flex items-center justify-center text-[var(--accent)] font-bold text-[10px]">
            {initial}
          </div>
          <div className="text-left hidden md:block">
            <p className="text-[11px] font-bold text-[var(--text-primary)] leading-none">
              {displayName}
            </p>
          </div>
          <ChevronDown
            size={11}
            className={`text-[var(--text-dim)] hidden sm:block transition-transform duration-200 ${
              profileOpen ? "rotate-180" : ""
            }`}
          />
        </button>
      </Tooltip>

      <AnimatePresence>
        {profileOpen && (
          <motion.div
            initial={{ opacity: 0, y: 8, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.95 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 top-[38px] w-56 pt-1 z-50"
          >
            <div className="glass-card bg-[rgba(15,15,18,0.95)] border border-[var(--border-focus)] rounded-xl shadow-[var(--shadow-lg)] overflow-hidden">
              {/* Profile Header */}
              <div className="p-3 bg-white/[0.02] border-b border-white/[0.03] flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[var(--accent)] to-[var(--accent-purple)] flex items-center justify-center text-white font-bold text-xs shadow-md">
                  {initial}
                </div>
                <div className="min-w-0">
                  <h4 className="text-xs font-bold text-[var(--text-primary)] truncate">
                    {displayName}
                  </h4>
                  <span className="text-[9px] font-mono text-[var(--accent)] uppercase tracking-wider font-bold">
                    {user.role === "admin" ? "Administrator" : "Clinician"}
                  </span>
                </div>
              </div>

              {/* Profile Options */}
              <div className="p-1">
                <Link
                  to="/profile"
                  onClick={() => setProfileOpen(false)}
                  onMouseEnter={() => prefetchRoute('/profile')}
                  className="flex items-center gap-2 px-2.5 py-2 text-[11px] font-bold uppercase tracking-wider text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-white/[0.03] rounded-lg transition-colors"
                >
                  <Settings size={12} className="text-[var(--text-dim)]" /> Profile Settings
                </Link>

                {user.role === "admin" && (
                  <Link
                    to="/admin"
                    onClick={() => setProfileOpen(false)}
                    onMouseEnter={() => prefetchRoute('/admin')}
                    className="flex items-center gap-2 px-2.5 py-2 text-[11px] font-bold uppercase tracking-wider text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-white/[0.03] rounded-lg transition-colors"
                  >
                    <Shield size={12} className="text-[var(--text-dim)]" /> {adminLabel}
                  </Link>
                )}

                <Link
                  to="/pricing"
                  onClick={() => setProfileOpen(false)}
                  onMouseEnter={() => prefetchRoute('/pricing')}
                  className="flex items-center gap-2 px-2.5 py-2 text-[11px] font-bold uppercase tracking-wider text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-white/[0.03] rounded-lg transition-colors"
                >
                  <CreditCard size={12} className="text-[var(--text-dim)]" /> Billing Console
                </Link>
              </div>

              <div className="p-1 border-t border-white/[0.03]">
                <button
                  onClick={() => {
                    setProfileOpen(false);
                    logout();
                  }}
                  className="w-full flex items-center gap-2 px-2.5 py-2 text-[11px] font-bold uppercase tracking-wider text-[var(--danger)] hover:text-white hover:bg-[var(--danger)]/10 rounded-lg transition-colors text-left cursor-pointer"
                >
                  <LogOut size={12} /> Logout
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
