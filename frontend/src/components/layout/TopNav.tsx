
import { useState, useRef, useEffect, lazy, Suspense } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuthStore } from "@/lib/auth";
import { prefetchRoute } from "@/lib/prefetch";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles, LogOut, ChevronDown,
  BrainCircuit, Database, Server, Search, Cpu,
  Network, Settings, Shield, ArrowRight, Globe,
  CreditCard, ShieldCheck, X,
} from "lucide-react";
import Tooltip from "./Tooltip";
import { useTranslation } from "@/lib/i18n";
import {
  type MenuItem, type MenuGroup,
  operationsItems, diagnosticsItems, intelligenceItems,
  MENU_GROUPS, getIconStyles, colorKeyFromMenuItem,
  COMMAND_ITEMS,
} from "./nav-config";

const MobileDrawer = lazy(() => import("@/components/layout/MobileDrawer"));

/* ───────────────────────────────────────────────────
   MegaMenuPanel – Dynamic Hero + Grid
   ─────────────────────────────────────────────────── */
const MegaMenuPanel: React.FC<{
  items: MenuItem[];
  cols?: number;
  onNavigate?: () => void;
}> = ({ items, cols = 2, onNavigate }) => {
  const [activeId, setActiveId] = useState<string>(items[0].id);
  const activeItem = items.find((i) => i.id === activeId) || items[0];

  const activeGlowColor = activeItem.color.includes("indigo")
    ? "rgba(95, 95, 247, 0.25)"
    : activeItem.color.includes("rose")
      ? "rgba(255, 74, 74, 0.25)"
      : activeItem.color.includes("purple")
        ? "rgba(134, 86, 245, 0.25)"
        : activeItem.color.includes("cyan")
          ? "rgba(0, 188, 212, 0.25)"
          : activeItem.color.includes("emerald")
            ? "rgba(16, 185, 129, 0.25)"
            : activeItem.color.includes("amber")
              ? "rgba(255, 179, 0, 0.25)"
              : activeItem.color.includes("sky")
                ? "rgba(56, 189, 248, 0.25)"
                : "rgba(95, 95, 247, 0.25)";

  return (
    <div
      className="grid gap-5 p-6 lg:grid-cols-[360px_1fr] bg-[rgba(5,5,8,0.96)] backdrop-blur-3xl rounded-2xl relative overflow-hidden transition-all duration-300 border"
      style={{
        minWidth: cols === 1 ? 620 : 900,
        maxWidth: 1050,
        borderColor: activeGlowColor,
        boxShadow: `0 30px 60px rgba(0,0,0,0.8), 0 0 35px ${activeGlowColor}, inset 0 1px 0 rgba(255,255,255,0.02)`
      }}
    >
      {/* Subtle inner glow */}
      <div className="absolute inset-0 bg-gradient-to-b from-white/[0.02] to-transparent pointer-events-none" />

      {/* ─── Left: Dynamic Hero Feature ─── */}
      <div className="row-span-4 relative group/hero">
        <Link to={activeItem.href} onClick={onNavigate} onMouseEnter={() => prefetchRoute(activeItem.href)} className="block w-full h-full">
          <div
            className={`flex h-full w-full select-none flex-col justify-between overflow-hidden rounded-2xl ${activeItem.gradient} p-7 outline-none border border-white/[0.06] transition-all duration-300 relative min-h-[340px]`}
            style={{ borderColor: undefined }}
          >
            {/* Large background icon */}
            <div className="absolute -right-8 -top-8 opacity-[0.06] group-hover/hero:opacity-[0.12] group-hover/hero:scale-110 transition-all duration-700 pointer-events-none">
              <activeItem.icon
                key={`bg-${activeItem.id}`}
                className={`w-52 h-52 ${activeItem.color}`}
                style={{ transition: "all 0.5s" }}
              />
            </div>

            <div
              key={`content-${activeItem.id}`}
              className="relative z-10 h-full flex flex-col"
              style={{ animation: "fadeSlideIn 0.3s ease" }}
            >
              <div className="flex-1">
                {/* Icon badge */}
                <div
                  className={`flex items-center justify-center w-12 h-12 rounded-xl border mb-5 transition-transform duration-500 ${activeItem.bg} border-white/10 group-hover/hero:scale-110`}
                  style={{
                    filter: `drop-shadow(0 0 12px ${activeItem.color.includes("rose") ? "rgba(244,63,94,0.4)" : activeItem.color.includes("emerald") ? "rgba(52,211,153,0.4)" : activeItem.color.includes("sky") ? "rgba(56,189,248,0.4)" : activeItem.color.includes("amber") ? "rgba(245,158,11,0.4)" : activeItem.color.includes("purple") ? "rgba(168,85,247,0.4)" : activeItem.color.includes("indigo") ? "rgba(99,102,241,0.4)" : activeItem.color.includes("cyan") ? "rgba(34,211,238,0.4)" : "rgba(99,102,241,0.4)"})`
                  }}
                >
                  <activeItem.icon className={`h-6 w-6 ${activeItem.color}`} />
                </div>
                {/* Title */}
                <div
                  className={`mb-3 text-xl font-black uppercase tracking-widest drop-shadow-sm ${activeItem.color}`}
                >
                  {activeItem.title}
                </div>
                {/* Long description */}
                <p className="text-[12px] leading-relaxed text-white/50 font-medium">
                  {activeItem.longDesc}
                </p>
              </div>

              {/* Bottom area: highlights + sub-actions */}
              <div className="mt-5 border-t border-white/[0.06] pt-4">
                {activeItem.highlights && activeItem.highlights.length > 0 && (
                  <div className="mb-3">
                    <div className="text-[9px] uppercase tracking-widest text-white/25 font-bold mb-2">
                      Featured Data
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {activeItem.highlights.map((hl) => (
                        <span
                          key={hl}
                          className={`px-2 py-0.5 rounded-md bg-white/[0.04] border border-white/[0.06] text-[10px] font-bold ${activeItem.color} opacity-80 cursor-default`}
                        >
                          {hl}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {activeItem.subActions && activeItem.subActions.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {activeItem.subActions.map((action) => (
                      <Link
                        key={action.title}
                        to={action.href}
                        onClick={onNavigate}
                        onMouseEnter={() => prefetchRoute(action.href)}
                        className="px-3 py-1.5 rounded-full bg-white/[0.04] border border-white/[0.06] text-[10px] font-bold text-white/70 hover:bg-white/[0.08] hover:border-white/[0.12] transition-colors flex items-center gap-1.5"
                      >
                        {action.title}{" "}
                        <ArrowRight className="w-3 h-3 opacity-50" />
                      </Link>
                    ))}
                  </div>
                ) : (
                  <Link
                    to={activeItem.href}
                    onClick={onNavigate}
                    onMouseEnter={() => prefetchRoute(activeItem.href)}
                    className="mt-1 px-4 py-2 rounded-full bg-white/[0.04] border border-white/[0.06] text-[10px] font-bold text-white/70 hover:bg-white/[0.08] hover:border-white/[0.12] transition-colors inline-flex items-center gap-2"
                  >
                    Open Module{" "}
                    <ArrowRight className="w-3.5 h-3.5 opacity-50" />
                  </Link>
                )}
              </div>
            </div>
          </div>
        </Link>
      </div>

      {/* ─── Right: Grid of Items ─── */}
      <div className="col-span-1 min-h-[340px]">
        <div
          className={`grid ${cols === 1 ? "grid-cols-1" : "grid-cols-2"} gap-y-2 gap-x-3 relative z-10 h-full content-start`}
        >
          {items.map((component) => (
            <div
              key={component.id}
              onMouseEnter={() => setActiveId(component.id)}
            >
              <Link to={component.href} onClick={onNavigate} onMouseEnter={() => prefetchRoute(component.href)} className="block w-full h-full">
                <div
                  className={`flex items-center group/item select-none rounded-xl p-3 no-underline outline-none transition-all duration-200 hover:bg-white/[0.03] border ${
                    activeId === component.id
                      ? "border-white/[0.08] bg-white/[0.03] shadow-sm"
                      : "border-transparent"
                  } hover:border-white/[0.08] hover:shadow-sm`}
                >
                  <div
                    className={`flex items-center justify-center w-10 h-10 rounded-lg ${component.bg} border border-white/[0.04] group-hover/item:border-white/[0.12] transition-colors shadow-sm mr-3.5 shrink-0`}
                  >
                    <component.icon
                      className={`w-4 h-4 ${component.color} group-hover/item:scale-110 transition-transform`}
                    />
                  </div>
                  <div className="flex flex-col justify-center min-w-0">
                    <div className="text-[12px] font-bold text-white/90 group-hover/item:text-[var(--accent)] transition-colors truncate">
                      {component.title}
                    </div>
                    <p className="text-[10px] text-white/35 mt-0.5 truncate font-medium">
                      {component.desc}
                    </p>
                  </div>
                </div>
              </Link>
            </div>
          ))}
        </div>
      </div>


    </div>
  );
};

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
  const [telemetryOpen, setTelemetryOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [languageOpen, setLanguageOpen] = useState(false);
  const [searchFocused, setSearchFocused] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);

  // Refs
  const navContainerRef = useRef<HTMLDivElement>(null);
  const telemetryRef = useRef<HTMLDivElement>(null);
  const profileRef = useRef<HTMLDivElement>(null);
  const languageRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const searchContainerRef = useRef<HTMLDivElement>(null);
  const hoverTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

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
  ];

  // Telemetry sim
  const [telemetryStats, setTelemetryStats] = useState({ cpu: 12, latency: 22 });

  useEffect(() => {
    const interval = setInterval(() => {
      setTelemetryStats({
        cpu: Math.floor(Math.random() * 8) + 8,
        latency: Math.floor(Math.random() * 6) + 19,
      });
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  const filteredCommandItems = COMMAND_ITEMS.filter((item) => {
    if (item.category === "Admin" && (!user || user.role !== "admin")) return false;
    const query = searchQuery.toLowerCase();
    return (
      item.label.toLowerCase().includes(query) ||
      item.desc.toLowerCase().includes(query) ||
      item.category.toLowerCase().includes(query)
    );
  });

  const handleSearchKeyDown = (e: React.KeyboardEvent) => {
    if (filteredCommandItems.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % filteredCommandItems.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + filteredCommandItems.length) % filteredCommandItems.length);
    } else if (e.key === "Enter") {
      e.preventDefault();
      const targetItem = filteredCommandItems[selectedIndex];
      if (targetItem) {
        navigate(targetItem.href);
        setSearchFocused(false);
        setSearchQuery("");
      }
    } else if (e.key === "Escape") {
      setSearchFocused(false);
    }
  };

  // Reset selected on search change
  useEffect(() => {
    setSelectedIndex(0);
  }, [searchQuery]);

  // Ctrl+K shortcut to focus input
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.key === "k" || e.key === "K") && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setSearchFocused(true);
        setTimeout(() => searchInputRef.current?.focus(), 50);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Click outside handler
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node;
      if (telemetryOpen && telemetryRef.current && !telemetryRef.current.contains(target)) {
        setTelemetryOpen(false);
      }
      if (profileOpen && profileRef.current && !profileRef.current.contains(target)) {
        setProfileOpen(false);
      }
      if (languageOpen && languageRef.current && !languageRef.current.contains(target)) {
        setLanguageOpen(false);
      }
      if (activeMenu && navContainerRef.current && !navContainerRef.current.contains(target)) {
        setActiveMenu(null);
      }
      if (searchFocused && searchContainerRef.current && !searchContainerRef.current.contains(target)) {
        setSearchFocused(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [telemetryOpen, profileOpen, languageOpen, activeMenu, searchFocused]);

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

          {/* ─── Universe Dex-Style Mega Menu Panel ─── */}
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
          <div ref={searchContainerRef} className="relative shrink-0">
            <Tooltip content="Command Search Console (Ctrl+K)" position="bottom">
              <div
                className={`flex items-center gap-2 px-3 py-1.5 border transition-all duration-300 rounded-lg bg-white/[0.02] shrink-0 ${
                  searchFocused
                    ? "w-56 md:w-72 border-[var(--accent-blue)] bg-white/[0.04] shadow-glow-cyan"
                    : "w-32 md:w-40 border-[var(--border)] hover:bg-white/[0.05] hover:border-[var(--border-focus)]"
                }`}
              >
                <button
                  onClick={() => {
                    setSearchFocused(true);
                    setTimeout(() => searchInputRef.current?.focus(), 50);
                  }}
                  aria-label="Open Command Search Console"
                  className="flex items-center gap-1.5 w-full text-left bg-transparent border-none p-0 cursor-pointer text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                  style={{ display: searchFocused ? 'none' : 'flex' }}
                >
                  <Search size={13} aria-hidden="true" />
                  <span className="hidden md:inline text-[9px] font-bold uppercase tracking-wider text-[var(--text-dim)]">
                    Search
                  </span>
                  <kbd className="hidden sm:inline-flex items-center gap-0.5 text-[8px] font-bold font-mono bg-white/[0.06] border border-white/[0.08] px-1 rounded text-[var(--text-dim)]">
                    Ctrl K
                  </kbd>
                </button>

                {searchFocused && (
                  <div className="flex items-center gap-2 w-full">
                    <Search size={13} className="text-[var(--accent-blue)] shrink-0" />
                    <input
                      ref={searchInputRef}
                      type="text"
                      placeholder="Search patients, rooms, or tools..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      onKeyDown={handleSearchKeyDown}
                      className="flex-1 text-[10px] font-bold uppercase tracking-wider text-[var(--text-primary)] placeholder-[var(--text-muted)] bg-transparent outline-none border-none py-0.5"
                      autoFocus
                    />
                    <button
                      aria-label="Close search console"
                      onClick={() => {
                        setSearchFocused(false);
                        setSearchQuery("");
                      }}
                      className="p-0.5 rounded hover:bg-white/[0.04] text-[var(--text-dim)] hover:text-[var(--text-primary)] transition-colors cursor-pointer text-[0px]"
                    >
                      Close search <X size={12} className="inline-block" />
                    </button>
                  </div>
                )}
              </div>
            </Tooltip>

            {/* Dropdown Results */}
            <AnimatePresence>
              {searchFocused && (
                <motion.div
                  initial={{ opacity: 0, y: 8, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 8, scale: 0.95 }}
                  transition={{ duration: 0.15 }}
                  className="absolute right-0 top-[38px] w-72 sm:w-96 pt-1 z-50 pointer-events-auto"
                >
                  <div className="glass-card bg-[rgba(15,15,18,0.96)] border border-[var(--border-focus)] rounded-xl shadow-[var(--shadow-lg)] overflow-hidden flex flex-col max-h-[70vh]">
                    <div className="flex-1 overflow-y-auto p-2 space-y-3">
                      {filteredCommandItems.length > 0 ? (
                        Object.entries(
                          filteredCommandItems.reduce(
                            (acc, item) => {
                              if (!acc[item.category]) acc[item.category] = [];
                              acc[item.category].push(item);
                              return acc;
                            },
                            {} as Record<string, typeof COMMAND_ITEMS>
                          )
                        ).map(([category, items]) => (
                          <div key={category}>
                            <h4 className="px-3 py-1 text-[8px] font-mono font-bold uppercase tracking-wider text-[var(--accent-blue)]">
                              {category}
                            </h4>
                            <div className="space-y-0.5 mt-1">
                              {items.map((item) => {
                                const globalIndex = filteredCommandItems.indexOf(item);
                                const isSelected = globalIndex === selectedIndex;

                                return (
                                  <button
                                    key={item.href}
                                    onClick={() => {
                                      navigate(item.href);
                                      setSearchFocused(false);
                                      setSearchQuery("");
                                    }}
                                    onMouseEnter={() => setSelectedIndex(globalIndex)}
                                    className={`w-full flex items-center gap-2.5 p-2 rounded-lg text-left transition-all duration-150 group cursor-pointer ${
                                      isSelected
                                        ? "bg-[var(--accent-muted)] border border-[var(--accent-border)]"
                                        : "bg-transparent border border-transparent hover:bg-white/[0.01]"
                                    }`}
                                  >
                                    <div
                                      className={`p-1.5 rounded-lg transition-colors shrink-0 ${
                                        isSelected
                                          ? "bg-[var(--accent)]/15 text-[var(--accent)] border border-[var(--accent)]/20"
                                          : "bg-white/[0.02] text-[var(--text-dim)] border border-white/[0.04] group-hover:text-[var(--text-primary)]"
                                      }`}
                                    >
                                      <item.icon size={11} />
                                    </div>
                                    <div className="min-w-0 flex-1">
                                      <div className="flex items-center justify-between">
                                        <span
                                          className={`text-[10px] font-bold transition-colors truncate ${
                                            isSelected
                                              ? "text-[var(--accent)]"
                                              : "text-[var(--text-primary)]"
                                          }`}
                                        >
                                          {item.label}
                                        </span>
                                      </div>
                                      <p className="text-[8px] text-[var(--text-dim)] truncate mt-0.5 group-hover:text-[var(--text-secondary)] transition-colors">
                                        {item.desc}
                                      </p>
                                    </div>
                                  </button>
                                );
                              })}
                            </div>
                          </div>
                        ))
                      ) : (
                        <div className="py-6 text-center">
                          <p className="text-[10px] font-bold text-[var(--text-secondary)] uppercase">
                            No matching modules found
                          </p>
                        </div>
                      )}
                    </div>
                    {/* Footer */}
                    <div className="px-3 py-1.5 bg-white/[0.01] border-t border-white/[0.03] flex justify-between items-center text-[7px] font-mono text-[var(--text-dim)] uppercase tracking-wider">
                      <span>↑↓ to navigate · ↵ to open</span>
                      <span>Console Navigator</span>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Telemetry Dropdown */}
          <div ref={telemetryRef} className="relative">
            <Tooltip content="System Telemetry & Load Status" position="bottom">
              <button
                onClick={() => setTelemetryOpen(!telemetryOpen)}
                className="status-badge status-badge-success flex items-center gap-1 px-2.5 py-1 rounded-full text-[9px] cursor-pointer hover:bg-[var(--success-muted)] border-[var(--success-border)] transition-colors font-bold uppercase"
                aria-label="Toggle system telemetry details"
              >
                <span className="w-1.5 h-1.5 bg-[var(--success)] rounded-full animate-pulse" />
                <span className="hidden sm:inline">Telemetry</span>
                <ChevronDown
                  size={9}
                  className={`transition-transform duration-200 ${telemetryOpen ? "rotate-180" : ""}`}
                />
              </button>
            </Tooltip>

            <AnimatePresence>
              {telemetryOpen && (
                <motion.div
                  initial={{ opacity: 0, y: 8, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 8, scale: 0.95 }}
                  transition={{ duration: 0.15 }}
                  className="absolute right-0 top-[38px] w-64 pt-1 z-50"
                >
                  <div className="glass-card p-3.5 bg-[rgba(15,15,18,0.95)] border border-[var(--border-focus)] rounded-xl shadow-[var(--shadow-lg)]">
                    <h3 className="section-label text-[var(--success)] mb-2.5 flex items-center gap-1">
                      <Cpu size={10} /> Live System Status
                    </h3>
                    <div className="space-y-3">
                      <div>
                        <div className="flex justify-between items-center text-[10px] font-bold font-mono uppercase text-[var(--text-secondary)] mb-1">
                          <span>CPU Core Load</span>
                          <span className="text-[var(--text-primary)]">{telemetryStats.cpu}%</span>
                        </div>
                        <div className="h-1.5 w-full bg-white/[0.04] rounded-full overflow-hidden border border-white/[0.02]">
                          <motion.div
                            className="h-full bg-[var(--success)] rounded-full"
                            animate={{ width: `${telemetryStats.cpu}%` }}
                            transition={{ duration: 0.5 }}
                          />
                        </div>
                      </div>

                      <div className="flex justify-between items-center text-[10px] font-bold font-mono uppercase border-t border-white/[0.03] pt-2">
                        <span className="text-[var(--text-secondary)] flex items-center gap-1">
                          <Network size={10} className="text-sky-400" /> API Latency
                        </span>
                        <span className="text-sky-400 font-bold">{telemetryStats.latency} ms</span>
                      </div>

                      <div className="flex justify-between items-center text-[10px] font-bold font-mono uppercase border-t border-white/[0.03] pt-2">
                        <span className="text-[var(--text-secondary)] flex items-center gap-1">
                          <Database size={10} className="text-amber-400" /> FHIR Broker
                        </span>
                        <span className="text-[var(--success)] font-bold">Synced</span>
                      </div>

                      <div className="flex justify-between items-center text-[10px] font-bold font-mono uppercase border-t border-white/[0.03] pt-2">
                        <span className="text-[var(--text-secondary)] flex items-center gap-1">
                          <Server size={10} className="text-purple-400" /> SQLite Store
                        </span>
                        <span className="text-[var(--text-primary)] font-bold">0.5 MB</span>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

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
          <div ref={languageRef} className="relative">
            <Tooltip content="Select Language" position="bottom">
              <button
                onClick={() => setLanguageOpen(!languageOpen)}
                className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-white/[0.02] border border-[var(--border)] hover:bg-white/[0.05] hover:border-[var(--border-focus)] transition-all cursor-pointer text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                aria-label="Select Language"
              >
                <Globe size={13} aria-hidden="true" />
                <span className="hidden sm:inline text-[9px] font-bold uppercase tracking-wider">
                  {language === 'en' ? 'EN' : language === 'es' ? 'ES' : 'HI'}
                </span>
                <ChevronDown
                  size={11}
                  className={`text-[var(--text-dim)] transition-transform duration-200 ${
                    languageOpen ? "rotate-180" : ""
                  }`}
                />
              </button>
            </Tooltip>

            <AnimatePresence>
              {languageOpen && (
                <motion.div
                  initial={{ opacity: 0, y: 8, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 8, scale: 0.95 }}
                  transition={{ duration: 0.15 }}
                  className="absolute right-0 top-[38px] w-36 pt-1 z-50"
                >
                  <div className="glass-card bg-[rgba(15,15,18,0.95)] border border-[var(--border-focus)] rounded-xl shadow-[var(--shadow-lg)] overflow-hidden p-1">
                    <button
                      onClick={() => {
                        setLanguage('en');
                        setLanguageOpen(false);
                      }}
                      className={`w-full flex items-center justify-between px-2.5 py-2 text-[10px] font-bold uppercase tracking-wider rounded-lg transition-colors text-left cursor-pointer ${
                        language === 'en'
                          ? "bg-[var(--accent)]/10 text-[var(--accent)]"
                          : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-white/[0.03]"
                      }`}
                    >
                      English
                      {language === 'en' && <span className="w-1.5 h-1.5 bg-[var(--accent)] rounded-full" />}
                    </button>
                    <button
                      onClick={() => {
                        setLanguage('es');
                        setLanguageOpen(false);
                      }}
                      className={`w-full flex items-center justify-between px-2.5 py-2 text-[10px] font-bold uppercase tracking-wider rounded-lg transition-colors text-left cursor-pointer ${
                        language === 'es'
                          ? "bg-[var(--accent)]/10 text-[var(--accent)]"
                          : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-white/[0.03]"
                      }`}
                    >
                      Español
                      {language === 'es' && <span className="w-1.5 h-1.5 bg-[var(--accent)] rounded-full" />}
                    </button>
                    <button
                      onClick={() => {
                        setLanguage('hi');
                        setLanguageOpen(false);
                      }}
                      className={`w-full flex items-center justify-between px-2.5 py-2 text-[10px] font-bold uppercase tracking-wider rounded-lg transition-colors text-left cursor-pointer ${
                        language === 'hi'
                          ? "bg-[var(--accent)]/10 text-[var(--accent)]"
                          : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-white/[0.03]"
                      }`}
                    >
                      हिन्दी
                      {language === 'hi' && <span className="w-1.5 h-1.5 bg-[var(--accent)] rounded-full" />}
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* User Profile Dropdown */}
          {user && (
            <div ref={profileRef} className="relative">
              <Tooltip content="Account Settings & Session" position="bottom">
                <button
                  onClick={() => setProfileOpen(!profileOpen)}
                  className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-white/[0.02] border border-[var(--border)] hover:bg-white/[0.05] hover:border-[var(--border-focus)] transition-all cursor-pointer"
                  aria-label={`Profile: ${user.full_name || user.username}`}
                >
                  <div className="w-5.5 h-5.5 rounded-md bg-[var(--accent-muted)] border border-[var(--accent-border)] flex items-center justify-center text-[var(--accent)] font-bold text-[10px]">
                    {(user.full_name || user.username).charAt(0).toUpperCase()}
                  </div>
                  <div className="text-left hidden md:block">
                    <p className="text-[11px] font-bold text-[var(--text-primary)] leading-none">
                      {user.full_name || user.username}
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
                          {(user.full_name || user.username).charAt(0).toUpperCase()}
                        </div>
                        <div className="min-w-0">
                          <h4 className="text-xs font-bold text-[var(--text-primary)] truncate">
                            {user.full_name || user.username}
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
                            <Shield size={12} className="text-[var(--text-dim)]" /> {t.adminConsole}
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
                          <LogOut size={12} /> {t.logout}
                        </button>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
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
                  setSearchFocused(val);
                  if (val) setTimeout(() => searchInputRef.current?.focus(), 50);
                }}
                dynamicMenuGroups={dynamicMenuGroups}
                telemetryStats={telemetryStats}
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
