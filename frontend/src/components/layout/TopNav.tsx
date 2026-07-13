
import { useState, useRef, useEffect, lazy, Suspense } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuthStore } from "@/lib/auth";
import { prefetchRoute } from "@/lib/prefetch";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, ChevronDown, BrainCircuit, ShieldCheck } from "lucide-react";
import Tooltip from "./Tooltip";
import { useTranslation } from "@/lib/i18n";
import {
  type MenuItem, type MenuGroup,
  operationsItems, diagnosticsItems, intelligenceItems, clinosItems,
  MENU_GROUPS, getIconStyles, colorKeyFromMenuItem,
  COMMAND_ITEMS,
} from "./nav-config";
import MegaMenuPanel from "./MegaMenuPanel";
import CommandSearch from "./CommandSearch";
import TelemetryDropdown from "./TelemetryDropdown";
import LanguageSelector from "./LanguageSelector";
import ProfileDropdown from "./ProfileDropdown";

const MobileDrawer = lazy(() => import("@/components/layout/MobileDrawer"));

/* ═══════════════════════════════════════════════════
   TopNav Component
   ═══════════════════════════════════════════════════ */
export default function TopNav({
  mobileOpen,
  setMobileOpen,
}: {
  mobileOpen?: boolean;
  setMobileOpen?: (val: boolean) => void;
}) {
  const location = useLocation();
  const pathname = location.pathname;
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const { language, setLanguage, t } = useTranslation();

  // Menu & UI state
  const [activeMenu, setActiveMenu] = useState<string | null>(null);
  const [hoveredTab, setHoveredTab] = useState<string | null>(null);

  // Refs
  const navContainerRef = useRef<HTMLDivElement>(null);
  const hoverTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Dynamic menu items and groups computation
  const dynamicOperationsItems = operationsItems.map(item => {
    if (item.id === "dashboard") return { ...item, title: t.commandCenter };
    if (item.id === "patients") return { ...item, title: t.patientRegistry };
    if (item.id === "capacity") return { ...item, title: t.infrastructure };
    if (item.id === "telemedicine") return { ...item, title: t.telemedicine };
    return item;
  });

  const dynamicIntelligenceItems = intelligenceItems.map(item => {
    if (item.id === "copilot") return { ...item, title: t.engageCopilot };
    if (item.id === "architecture") return { ...item, title: t.adminConsole };
    return item;
  });

  const dynamicClinosItems = clinosItems.map(item => {
    return item;
  });

  const dynamicMenuGroups = [
    {
      key: "operations",
      label: language === "es" ? "Operaciones" : language === "hi" ? "संचालन" : "Operations",
      emoji: "🛰️",
      accentColor: "text-indigo-400 data-[state=open]:text-indigo-400",
      items: dynamicOperationsItems,
      cols: 2,
      routes: ["/dashboard", "/patients", "/capacity", "/telemedicine", "/infrastructure"],
    },
    {
      key: "diagnostics",
      label: language === "es" ? "Diagnósticos AI" : language === "hi" ? "निदान एआई" : "Diagnostics AI",
      emoji: "🧬",
      accentColor: "text-rose-400 data-[state=open]:text-rose-400",
      items: diagnosticsItems,
      cols: 2,
      routes: ["/predict/heart", "/predict/lungs", "/predict/liver", "/predict/kidney", "/predict/diabetes"],
    },
    {
      key: "intelligence",
      label: language === "es" ? "Inteligencia" : language === "hi" ? "बुद्धिमत्ता" : "Intelligence",
      emoji: "⚡",
      accentColor: "text-purple-400 data-[state=open]:text-purple-400",
      items: dynamicIntelligenceItems,
      cols: 1,
      routes: ["/chat", "/about", "/pricing"],
    },
    {
      key: "clinos",
      label: language === "es" ? "Sistemas ClinOS" : language === "hi" ? "क्लिओएस" : "ClinOS",
      emoji: "🚀",
      accentColor: "text-sky-400 data-[state=open]:text-sky-400",
      items: dynamicClinosItems,
      cols: 2,
      routes: ["/apps", "/federated", "/intelligence", "/companion"],
    },
  ];

  // Click outside handler for menu
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node;
      if (activeMenu && navContainerRef.current && !navContainerRef.current.contains(target)) {
        setActiveMenu(null);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [activeMenu]);

  const handleMouseEnter = (menuKey: string) => {
    if (hoverTimeoutRef.current) clearTimeout(hoverTimeoutRef.current);
    setActiveMenu(menuKey);
  };

  const handleMouseLeave = () => {
    hoverTimeoutRef.current = setTimeout(() => {
      setActiveMenu(null);
    }, 200);
  };

  const closeAllMenus = () => {
    setActiveMenu(null);
    setHoveredTab(null);
  };

  return (
    <>
      <header
        className="fixed top-2.5 left-1/2 -translate-x-1/2 w-[calc(100%-1.5rem)] md:w-[calc(100%-3rem)] max-w-[1550px] h-14 z-50 flex items-center px-4 md:px-6 justify-between border border-[var(--border)] bg-[var(--bg-card)] backdrop-blur-2xl rounded-2xl shadow-[var(--shadow-soft)] transition-all duration-300 hover:border-[var(--border-focus)] hover:shadow-[0_4px_30px_rgba(95,95,247,0.08)]"
        role="banner"
      >
        {/* Top glow */}
        <div
          className="pointer-events-none absolute inset-x-6 top-0 h-px bg-gradient-to-r from-transparent via-[var(--accent)] to-transparent opacity-60"
          aria-hidden="true"
        />

        {/* ─── Left: Brand Logo ─── */}
        <Tooltip content="Command Center / Dashboard" position="bottom">
          <Link
            to="/dashboard"
            onMouseEnter={() => prefetchRoute('/dashboard')}
            className="flex items-center gap-2 shrink-0 group"
            aria-label="AI Healthcare System - Go to dashboard"
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[var(--accent)] to-[var(--accent-purple)] flex items-center justify-center text-white shadow-[0_0_12px_rgba(99,102,241,0.25)] group-hover:scale-105 transition-transform duration-200">
              <Sparkles size={15} aria-hidden="true" />
            </div>
            <div className="hidden sm:block">
              <h1 className="text-xs font-bold text-[var(--text-primary)] tracking-wide uppercase">
                AI Healthcare{" "}
                <span className="text-[var(--text-secondary)] font-normal">System</span>
              </h1>
            </div>
          </Link>
        </Tooltip>

        {/* ─── Center: Navigation with Mega Menus ─── */}
        <nav
          ref={navContainerRef}
          className="hidden lg:flex items-center gap-1 h-full relative"
          onMouseLeave={() => {
            handleMouseLeave();
            setHoveredTab(null);
          }}
          aria-label="Main navigation"
        >
          {dynamicMenuGroups.map((group) => {
            const isCurrentRoute = group.routes.some((r) => pathname?.startsWith(r));

            return (
              <div
                key={group.key}
                className="h-full flex items-center relative"
                onMouseEnter={() => {
                  if (hoverTimeoutRef.current) clearTimeout(hoverTimeoutRef.current);
                  setActiveMenu(group.key);
                  setHoveredTab(group.key);
                }}
              >
                <button
                  onClick={() => {
                    if (activeMenu === group.key) {
                      setActiveMenu(null);
                      setHoveredTab(null);
                    } else {
                      setActiveMenu(group.key);
                      setHoveredTab(group.key);
                    }
                  }}
                  className={`relative z-10 px-3 py-1.5 rounded-lg text-[10px] font-black tracking-wider uppercase transition-all duration-200 flex items-center gap-1.5 cursor-pointer ${
                    activeMenu === group.key || isCurrentRoute
                      ? "text-[var(--text-primary)]"
                      : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                  }`}
                  aria-expanded={activeMenu === group.key}
                  aria-haspopup="true"
                >
                  <span className="text-sm">{group.emoji}</span>
                  {group.label}
                  <ChevronDown
                    size={11}
                    className={`transition-transform duration-200 ${
                      activeMenu === group.key
                        ? "rotate-180 text-[var(--accent)]"
                        : "text-[var(--text-dim)]"
                    }`}
                    aria-hidden="true"
                  />
                </button>

                {/* Hover pill */}
                {hoveredTab === group.key && (
                  <motion.div
                    layoutId="nav-hover-pill"
                    className="absolute inset-0 bg-white/[0.04] border border-white/[0.02] rounded-lg -z-10"
                    transition={{ type: "spring", stiffness: 350, damping: 28 }}
                  />
                )}

                {/* Active underline */}
                {isCurrentRoute && activeMenu !== group.key && (
                  <motion.div
                    layoutId="nav-active-pill"
                    className="absolute bottom-1 inset-x-3.5 h-0.5 bg-[var(--accent)] rounded-full"
                    transition={{ type: "spring", stiffness: 380, damping: 30 }}
                  />
                )}
              </div>
            );
          })}

          {/* ─── Mega Menu Panel ─── */}
          <AnimatePresence mode="wait">
            {activeMenu && (
              <motion.div
                key={activeMenu}
                initial={{ opacity: 0, y: 12, scale: 0.97 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 12, scale: 0.97 }}
                transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
                onMouseEnter={() => {
                  if (hoverTimeoutRef.current) clearTimeout(hoverTimeoutRef.current);
                }}
                onMouseLeave={() => {
                  handleMouseLeave();
                  setHoveredTab(null);
                }}
                className="absolute top-[44px] left-1/2 -translate-x-1/2 pt-2 z-50"
              >
                {(() => {
                  const group = dynamicMenuGroups.find((g) => g.key === activeMenu);
                  if (!group) return null;
                  return (
                    <MegaMenuPanel
                      items={group.items}
                      cols={group.cols}
                      onNavigate={closeAllMenus}
                    />
                  );
                })()}
              </motion.div>
            )}
          </AnimatePresence>
        </nav>

        {/* ─── Right: Actions ─── */}
        <div className="flex items-center gap-2 md:gap-3 shrink-0">
          {/* Command Search */}
          <CommandSearch user={user} />

          {/* Telemetry Dropdown */}
          <TelemetryDropdown />

          {/* Admin Icon */}
          {user && user.role === "admin" && (
            <Tooltip content="Clinician Admin Console" position="bottom">
              <Link
                to="/admin"
                onMouseEnter={() => prefetchRoute('/admin')}
                className="hidden sm:flex p-2 text-[var(--text-secondary)] hover:text-[var(--accent)] border border-transparent hover:border-[var(--border)] hover:bg-white/[0.02] rounded-lg transition-colors"
                aria-label="Admin panel"
              >
                <ShieldCheck size={15} aria-hidden="true" />
              </Link>
            </Tooltip>
          )}

          {/* Language Selector Dropdown */}
          <LanguageSelector language={language} setLanguage={setLanguage} />

          {/* User Profile Dropdown */}
          {user && (
            <ProfileDropdown user={user} logout={logout} adminLabel={t.adminConsole} />
          )}

          {/* Mobile Menu trigger */}
          <Tooltip content="Open Navigation Menu" position="bottom">
            <button
              onClick={() => {
                if (setMobileOpen) setMobileOpen(true);
              }}
              className="lg:hidden p-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)] border border-[var(--border)] hover:border-[var(--border-focus)] bg-white/[0.02] hover:bg-white/[0.05] rounded-lg transition-all cursor-pointer"
              aria-label="Open mobile menu"
            >
              <BrainCircuit size={16} aria-hidden="true" />
            </button>
          </Tooltip>
        </div>

        {/* ─── Mobile Drawer ─── */}
        <AnimatePresence>
          {mobileOpen && (
            <Suspense fallback={null}>
              <MobileDrawer
                open={mobileOpen}
                onClose={() => {
                  if (setMobileOpen) setMobileOpen(false);
                }}
                setCommandMenuOpen={(val) => {
                  // Integrate with CommandSearch if needed
                }}
                dynamicMenuGroups={dynamicMenuGroups}
                telemetryStats={{ cpu: 12, latency: 22 }}
                user={user}
                logout={logout}
              />
            </Suspense>
          )}
        </AnimatePresence>
      </header>
    </>
  );
}
