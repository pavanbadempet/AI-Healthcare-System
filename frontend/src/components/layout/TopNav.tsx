"use client";

import { useState, useRef } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuthStore } from "@/lib/auth";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard, MessageSquare, Heart, Activity, 
  FlaskConical, Stethoscope, Wind, User, LogOut,
  Sparkles, CreditCard, Video, Info, ShieldCheck, ChevronDown, BrainCircuit, Database, BedDouble, Server
} from "lucide-react";

const MEGA_MENUS = {
  operations: {
    label: "Operations",
    items: [
      { label: "Command Center", href: "/dashboard", icon: LayoutDashboard, desc: "Global telemetry and health overview" },
      { label: "Patient Registry", href: "/patients", icon: User, desc: "Manage multiple patient profiles" },
      { label: "Capacity & Beds", href: "/capacity", icon: BedDouble, desc: "Hospital ADT & throughput tracker" },
      { label: "Telemedicine", href: "/telemedicine", icon: Video, desc: "Secure video consultations" },
      { label: "Infrastructure", href: "/infrastructure", icon: Server, desc: "HL7/FHIR Node Status & Sync" },
    ]
  },
  diagnostics: {
    label: "Diagnostics AI",
    items: [
      { label: "Cardiology", href: "/predict/heart", icon: Heart, desc: "Heart disease risk assessment", color: "text-rose-400" },
      { label: "Pulmonology", href: "/predict/lungs", icon: Wind, desc: "Lung capacity and disease modeling", color: "text-sky-400" },
      { label: "Hepatology", href: "/predict/liver", icon: FlaskConical, desc: "Hepatic function analysis", color: "text-amber-400" },
      { label: "Nephrology", href: "/predict/kidney", icon: Stethoscope, desc: "Renal failure prediction", color: "text-emerald-400" },
      { label: "Endocrinology", href: "/predict/diabetes", icon: Activity, desc: "Metabolic syndrome tracking", color: "text-indigo-400" },
    ]
  },
  intelligence: {
    label: "Intelligence",
    items: [
      { label: "AI Copilot", href: "/chat", icon: MessageSquare, desc: "Singularity LLM medical assistant" },
      { label: "System Architecture", href: "/about", icon: Info, desc: "View infrastructure and whitepapers" },
      { label: "Enterprise Billing", href: "/pricing", icon: CreditCard, desc: "Manage hospital API usage" },
    ]
  }
};

export default function TopNav({ mobileOpen, setMobileOpen }: { mobileOpen?: boolean, setMobileOpen?: (val: boolean) => void }) {
  const pathname = usePathname();
  const { user, logout } = useAuthStore();
  const [activeMenu, setActiveMenu] = useState<string | null>(null);

  const hoverTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const handleMouseEnter = (menuKey: string) => {
    if (hoverTimeoutRef.current) clearTimeout(hoverTimeoutRef.current);
    setActiveMenu(menuKey);
  };

  const handleMouseLeave = () => {
    hoverTimeoutRef.current = setTimeout(() => {
      setActiveMenu(null);
    }, 150); // Small delay to prevent flickering when moving between items
  };

  return (
    <header className="fixed top-0 left-0 right-0 h-14 z-50 bg-[var(--bg-primary)] border-b border-[var(--border)] flex items-center px-4 md:px-6 justify-between" role="banner">
      {/* Left: Logo */}
      <Link href="/dashboard" className="flex items-center gap-3 shrink-0 group" aria-label="AI Healthcare System - Go to dashboard">
        <div className="w-8 h-8 rounded-md flex items-center justify-center text-[var(--text-primary)] bg-[var(--bg-card)] border border-[var(--border)] group-hover:border-[var(--border-focus)] transition-colors">
          <Sparkles size={16} aria-hidden="true" />
        </div>
        <div className="hidden sm:block">
          <h1 className="text-sm font-semibold text-[var(--text-primary)] tracking-tight">AI Healthcare<span className="text-[var(--text-secondary)] ml-1">System</span></h1>
        </div>
      </Link>

      {/* Middle: Desktop Mega Navigation */}
      <nav className="hidden lg:flex items-center gap-2 h-full absolute left-1/2 -translate-x-1/2" onMouseLeave={handleMouseLeave} aria-label="Main navigation">
        {Object.entries(MEGA_MENUS).map(([key, menu]) => {
          const isActive = activeMenu === key;
          const isCurrentRoute = menu.items.some(item => pathname?.startsWith(item.href));
          
          return (
            <div key={key} className="h-full flex items-center" onMouseEnter={() => handleMouseEnter(key)}>
              <button
                className={`px-3 py-1.5 rounded-md text-[13px] font-medium transition-colors flex items-center gap-1.5 ${isActive || isCurrentRoute ? "text-[var(--text-primary)] bg-[var(--bg-card-hover)]" : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"}`}
                aria-expanded={isActive}
                aria-haspopup="true"
              >
                {menu.label}
                <ChevronDown size={12} className={`transition-transform duration-200 ${isActive ? "rotate-180" : ""}`} aria-hidden="true" />
              </button>

              {/* Mega Dropdown Panel */}
              <AnimatePresence>
                {isActive && (
                  <motion.div
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 5 }}
                    transition={{ duration: 0.1 }}
                    className="absolute top-[48px] left-1/2 -translate-x-1/2 w-[500px] pt-2 z-50"
                  >
                    <div className="bg-[var(--bg-secondary)] border border-[var(--border)] p-4 rounded-lg shadow-xl relative overflow-hidden" role="menu">
                      <div className="grid grid-cols-2 gap-2">
                        {menu.items.map((item) => (
                          <Link 
                            key={item.href} 
                            href={item.href}
                            onClick={() => setActiveMenu(null)}
                            className="flex items-start gap-3 p-3 rounded-md hover:bg-[var(--bg-card)] transition-colors group"
                            role="menuitem"
                          >
                            <div className="mt-0.5 text-[var(--text-dim)] group-hover:text-[var(--text-primary)] transition-colors">
                              <item.icon size={16} aria-hidden="true" />
                            </div>
                            <div>
                              <h3 className="text-[13px] font-medium text-[var(--text-primary)] mb-0.5">{item.label}</h3>
                              <p className="text-[12px] text-[var(--text-dim)] leading-snug">{item.desc}</p>
                            </div>
                          </Link>
                        ))}
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          );
        })}
      </nav>

      {/* Right: User & Status */}
      <div className="flex items-center gap-4 shrink-0">
        <div className="hidden md:flex items-center gap-2 mr-4">
          <span className="status-badge status-badge-success">
            <Database size={10} aria-hidden="true" /> Online
          </span>
        </div>

        {user && user.role === "admin" && (
          <Link href="/admin" className="hidden lg:flex p-1.5 text-[var(--text-secondary)] hover:text-[var(--text-primary)] rounded-md transition-colors hover:bg-[var(--bg-card)]" aria-label="Admin panel">
            <ShieldCheck size={16} aria-hidden="true" />
          </Link>
        )}
        
        {user && (
          <Link href="/profile" className="hidden sm:flex items-center gap-2 px-2 py-1 rounded-md hover:bg-[var(--bg-card)] transition-colors border border-transparent hover:border-[var(--border)] cursor-pointer" aria-label={`Profile: ${user.full_name || user.username}`}>
            <div className="w-6 h-6 rounded bg-[var(--bg-card-hover)] border border-[var(--border)] flex items-center justify-center text-[var(--text-primary)] font-medium text-[11px]">
              {(user.full_name || user.username).charAt(0).toUpperCase()}
            </div>
            <div className="text-left hidden md:block">
              <p className="text-[13px] font-medium text-[var(--text-primary)] leading-none">{user.full_name || user.username}</p>
            </div>
          </Link>
        )}

        <button onClick={logout} className="p-1.5 text-[var(--text-dim)] hover:text-[var(--danger)] rounded-md transition-colors hover:bg-[var(--danger-muted)]" title="Sign out" aria-label="Sign out">
          <LogOut size={16} aria-hidden="true" />
        </button>

        {/* Mobile menu toggle */}
        <button onClick={() => setMobileOpen && setMobileOpen(true)} className="lg:hidden p-1.5 text-[var(--text-secondary)] hover:text-[var(--text-primary)] rounded-md transition-colors" aria-label="Open mobile menu">
          <BrainCircuit size={18} aria-hidden="true" />
        </button>
      </div>

      {/* Mobile Mega Menu Overlay */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="lg:hidden fixed inset-0 z-50 bg-[var(--bg-primary)] overflow-y-auto pt-20 px-4 pb-20"
            role="dialog"
            aria-label="Mobile navigation menu"
          >
            <button onClick={() => setMobileOpen && setMobileOpen(false)} className="absolute top-4 right-4 p-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)] rounded-md bg-[var(--bg-card)] border border-[var(--border)]" aria-label="Close mobile menu">
              Close
            </button>
            
            <nav className="space-y-8 max-w-md mx-auto" aria-label="Mobile navigation">
              {Object.entries(MEGA_MENUS).map(([key, menu]) => (
                <div key={key}>
                  <h2 className="section-label text-[var(--accent)] mb-3 ml-1">{menu.label}</h2>
                  <div className="space-y-2">
                    {menu.items.map((item) => (
                      <Link 
                        key={item.href} 
                        href={item.href}
                        onClick={() => setMobileOpen && setMobileOpen(false)}
                        className="flex items-center gap-3 p-3 rounded-md bg-[var(--bg-card)] border border-[var(--border)] hover:border-[var(--border-focus)] transition-colors"
                      >
                        <div className="p-2 rounded-md bg-[var(--accent-muted)] text-[var(--accent)] border border-[var(--accent-border)]">
                          <item.icon size={16} aria-hidden="true" />
                        </div>
                        <div>
                          <h3 className="text-[13px] font-medium text-[var(--text-primary)]">{item.label}</h3>
                          <p className="text-[11px] text-[var(--text-dim)] mt-0.5">{item.desc}</p>
                        </div>
                      </Link>
                    ))}
                  </div>
                </div>
              ))}
            </nav>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
