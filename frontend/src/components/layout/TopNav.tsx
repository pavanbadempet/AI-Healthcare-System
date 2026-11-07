import { useState, useRef, useEffect, lazy, Suspense } from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuthStore } from "@/lib/auth";
import { prefetchRoute } from "@/lib/prefetch";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles,
  LayoutDashboard,
  Users,
  Calendar,
  BedDouble,
  MessageSquare,
  AlertTriangle,
  Menu,
} from "lucide-react";
import Tooltip from "./Tooltip";
import { useTranslation } from "@/lib/i18n";
import CommandSearch from "./CommandSearch";
import LanguageSelector from "./LanguageSelector";
import ProfileDropdown from "./ProfileDropdown";
import { useNetworkStatus } from "@/lib/offlineSync";

const MobileDrawer = lazy(() => import("@/components/layout/MobileDrawer"));

interface NavLinkItem {
  id: string;
  label: string;
  href: string;
  icon: React.ElementType;
}

export default function TopNav({
  mobileOpen,
  setMobileOpen,
}: {
  mobileOpen?: boolean;
  setMobileOpen?: (val: boolean) => void;
}) {
  const location = useLocation();
  const pathname = location.pathname;
  const { user, logout } = useAuthStore();
  const { language, setLanguage, t } = useTranslation();
  const { isOnline, queueCount } = useNetworkStatus();

  const [alarm, setAlarm] = useState<{ active: boolean; bed?: string; name?: string; hr?: number } | null>(null);
  const [showNotifications, setShowNotifications] = useState(false);
  const notificationsRef = useRef<HTMLDivElement>(null);
  const alarmRef = useRef(alarm);

  useEffect(() => {
    alarmRef.current = alarm;
  }, [alarm]);

  useEffect(() => {
    const handleAlarm = (e: Event) => {
      const customEvent = e as CustomEvent;
      const newAlarm = customEvent.detail;
      if (newAlarm?.active && !alarmRef.current?.active) {
        setShowNotifications(true);
      }
      setAlarm(newAlarm);
    };
    window.addEventListener("clinical-alarm", handleAlarm);
    return () => window.removeEventListener("clinical-alarm", handleAlarm);
  }, []);

  const resolveAlarm = (action: "code-blue" | "dismiss") => {
    window.dispatchEvent(new CustomEvent("resolve-alarm", { detail: { action } }));
    setShowNotifications(false);
  };

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        showNotifications &&
        notificationsRef.current &&
        !notificationsRef.current.contains(e.target as Node)
      ) {
        setShowNotifications(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [showNotifications]);

  // Clean, human clinical navigation links
  const navLinks: NavLinkItem[] = [
    { id: "dashboard", label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { id: "patients", label: "Patients", href: "/patients", icon: Users },
    { id: "telemedicine", label: "Visits & Telehealth", href: "/telemedicine", icon: Calendar },
    { id: "capacity", label: "Beds & Rooms", href: "/capacity", icon: BedDouble },
    { id: "copilot", label: "AI Copilot", href: "/chat", icon: MessageSquare },
  ];

  return (
    <>
      <header className="sticky top-0 z-40 w-full h-14 bg-zinc-950/80 backdrop-blur-xl border-b border-white/[0.06] px-4 md:px-6 flex items-center justify-between transition-colors">
        {/* ─── Left: Brand Logo ─── */}
        <Link
          to="/dashboard"
          onMouseEnter={() => prefetchRoute("/dashboard")}
          className="flex items-center gap-2.5 shrink-0 group focus:outline-none"
          aria-label="AI Healthcare System Dashboard"
        >
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white shadow-sm shadow-indigo-500/20 group-hover:scale-105 transition-transform duration-200">
            <Sparkles size={16} aria-hidden="true" />
          </div>
          <div className="flex flex-col">
            <h1 className="text-xs font-bold text-zinc-100 tracking-tight flex items-center gap-1.5 leading-none">
              AI Healthcare <span className="text-indigo-400 font-semibold">System</span>
            </h1>
            <span className="text-[10px] text-zinc-400 font-medium tracking-normal mt-0.5 leading-none">
              Clinical Workspace
            </span>
          </div>
        </Link>

        {/* ─── Center: Essential Direct Navigation ─── */}
        <nav
          className="hidden md:flex items-center gap-1 h-full"
          aria-label="Main clinical navigation"
        >
          {navLinks.map((link) => {
            const isActive =
              link.href === "/dashboard"
                ? pathname === "/dashboard" || pathname === "/"
                : pathname?.startsWith(link.href);

            const Icon = link.icon;

            return (
              <Link
                key={link.id}
                to={link.href}
                onMouseEnter={() => prefetchRoute(link.href)}
                className={`relative px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-2 transition-colors duration-150 ${
                  isActive
                    ? "text-white font-semibold"
                    : "text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.03]"
                }`}
              >
                <Icon
                  size={14}
                  className={`transition-colors duration-150 ${
                    isActive ? "text-indigo-400" : "text-zinc-400"
                  }`}
                />
                <span>{link.label}</span>

                {/* Tactile active indicator pill */}
                {isActive && (
                  <motion.div
                    layoutId="top-nav-active-pill"
                    className="absolute inset-0 bg-white/[0.06] border border-white/[0.08] rounded-lg -z-10 shadow-sm"
                    transition={{ type: "spring", stiffness: 450, damping: 35 }}
                  />
                )}
              </Link>
            );
          })}
        </nav>

        {/* ─── Right: Actions & Profile ─── */}
        <div className="flex items-center gap-2.5 shrink-0">
          {/* Offline Queue Indicator */}
          {!isOnline && (
            <div className="flex items-center gap-1.5 px-2.5 py-1 border border-amber-500/30 bg-amber-500/10 rounded-lg text-[10px] font-semibold text-amber-400">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping" />
              <span>Offline ({queueCount})</span>
            </div>
          )}

          {/* Quick Command Search (⌘K) */}
          <CommandSearch user={user} />

          {/* Vitals Emergency Alarm Bell */}
          <div ref={notificationsRef} className="relative flex items-center">
            <Tooltip content={alarm?.active ? "Active Vitals Alarm!" : "Notifications"} position="bottom">
              <button
                onClick={() => setShowNotifications(!showNotifications)}
                className={`relative p-2 rounded-lg border transition-all duration-200 cursor-pointer ${
                  alarm?.active
                    ? "bg-red-500/15 border-red-500/40 text-red-400 animate-pulse hover:bg-red-500/25"
                    : "text-zinc-400 hover:text-zinc-200 border-transparent hover:border-white/[0.06] hover:bg-white/[0.03]"
                }`}
                aria-label="View notifications"
              >
                <AlertTriangle size={15} />
                {alarm?.active && (
                  <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-red-500 ring-2 ring-zinc-950 animate-ping" />
                )}
              </button>
            </Tooltip>

            {/* Notification Dropdown */}
            <AnimatePresence>
              {showNotifications && (
                <motion.div
                  initial={{ opacity: 0, y: 8, scale: 0.98 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 8, scale: 0.98 }}
                  transition={{ duration: 0.15 }}
                  className="absolute right-0 top-full mt-2 w-80 bg-zinc-900 border border-white/[0.08] shadow-2xl rounded-xl p-4 z-50 text-xs"
                >
                  <div className="flex items-center justify-between border-b border-white/[0.06] pb-2 mb-3">
                    <span className="font-semibold text-zinc-200">Clinical Alerts</span>
                    {alarm?.active && (
                      <span className="px-1.5 py-0.5 rounded bg-red-500/20 text-red-400 text-[10px] font-semibold uppercase">
                        Critical
                      </span>
                    )}
                  </div>

                  {alarm?.active ? (
                    <div className="space-y-3">
                      <div className="flex items-start gap-2.5">
                        <AlertTriangle className="text-red-400 shrink-0 mt-0.5" size={16} />
                        <div>
                          <p className="font-semibold text-red-400">Emergency Vital Alarm</p>
                          <p className="text-zinc-300 mt-1 leading-relaxed">
                            {alarm.bed}: {alarm.name} exhibits abnormal heart rate ({alarm.hr} BPM).
                          </p>
                        </div>
                      </div>

                      <div className="flex flex-col gap-1.5 pt-2">
                        <button
                          onClick={() => resolveAlarm("code-blue")}
                          className="w-full py-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-white font-semibold text-xs transition-colors cursor-pointer"
                        >
                          Send Emergency Team (Code Blue)
                        </button>
                        <button
                          onClick={() => resolveAlarm("dismiss")}
                          className="w-full py-1.5 rounded-lg border border-white/[0.08] hover:bg-white/[0.04] text-zinc-300 hover:text-white font-medium text-xs transition-colors cursor-pointer"
                        >
                          Dismiss Alarm
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="py-4 text-center text-zinc-500">
                      No active critical alerts
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Language Selector */}
          <LanguageSelector language={language} setLanguage={setLanguage} />

          {/* User Profile Dropdown */}
          {user && (
            <ProfileDropdown user={user} logout={logout} adminLabel={t.adminConsole} />
          )}

          {/* Mobile Menu trigger */}
          <button
            onClick={() => {
              if (setMobileOpen) setMobileOpen(true);
            }}
            className="md:hidden p-2 text-zinc-400 hover:text-zinc-200 border border-white/[0.06] hover:bg-white/[0.04] rounded-lg transition-all cursor-pointer"
            aria-label="Open mobile menu"
          >
            <Menu size={16} aria-hidden="true" />
          </button>
        </div>
      </header>

      {/* ─── Mobile Drawer ─── */}
      <AnimatePresence>
        {mobileOpen && (
          <Suspense fallback={null}>
            <MobileDrawer
              open={mobileOpen}
              onClose={() => {
                if (setMobileOpen) setMobileOpen(false);
              }}
              setCommandMenuOpen={() => {}}
              dynamicMenuGroups={[
                {
                  key: "clinical",
                  label: "Clinical Workspace",
                  emoji: "🏥",
                  accentColor: "text-indigo-400",
                  cols: 1,
                  routes: ["/dashboard", "/patients", "/telemedicine", "/capacity", "/chat"],
                  items: [
                    { id: "dashboard", title: "Dashboard", href: "/dashboard", icon: LayoutDashboard, desc: "Overview & Vitals", longDesc: "", color: "text-indigo-400", bg: "bg-indigo-500/10", borderHover: "", glow: "", gradient: "" },
                    { id: "patients", title: "Patients", href: "/patients", icon: Users, desc: "Medical Records", longDesc: "", color: "text-emerald-400", bg: "bg-emerald-500/10", borderHover: "", glow: "", gradient: "" },
                    { id: "telemedicine", title: "Visits & Telehealth", href: "/telemedicine", icon: Calendar, desc: "Appointments", longDesc: "", color: "text-cyan-400", bg: "bg-cyan-500/10", borderHover: "", glow: "", gradient: "" },
                    { id: "capacity", title: "Beds & Rooms", href: "/capacity", icon: BedDouble, desc: "Ward Allocation", longDesc: "", color: "text-rose-400", bg: "bg-rose-500/10", borderHover: "", glow: "", gradient: "" },
                    { id: "copilot", title: "AI Copilot", href: "/chat", icon: MessageSquare, desc: "Clinical Assistant", longDesc: "", color: "text-purple-400", bg: "bg-purple-500/10", borderHover: "", glow: "", gradient: "" },
                  ],
                },
              ]}
              telemetryStats={{ cpu: 5, latency: 1 }}
              user={user}
              logout={logout}
            />
          </Suspense>
        )}
      </AnimatePresence>
    </>
  );
}
