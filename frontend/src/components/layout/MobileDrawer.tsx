import React from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { X, Search, LogOut } from "lucide-react";
import { prefetchRoute } from "@/lib/prefetch";
import { getIconStyles, colorKeyFromMenuItem } from "./nav-config";

interface MobileDrawerProps {
  open: boolean;
  onClose: () => void;
  setCommandMenuOpen: (open: boolean) => void;
  dynamicMenuGroups: any[];
  telemetryStats: { cpu: number; latency: number };
  user: any;
  logout: () => void;
}

export default function MobileDrawer({
  open,
  onClose,
  setCommandMenuOpen,
  dynamicMenuGroups,
  telemetryStats,
  user,
  logout,
}: MobileDrawerProps) {
  return (
    <>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 0.5 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="lg:hidden fixed inset-0 z-40 bg-black"
      />

      <motion.div
        initial={{ x: "100%" }}
        animate={{ x: 0 }}
        exit={{ x: "100%" }}
        transition={{ type: "spring", damping: 25, stiffness: 220 }}
        className="lg:hidden fixed right-0 top-0 bottom-0 w-80 max-w-[90vw] z-50 bg-[var(--bg-secondary)] border-l border-[var(--border)] flex flex-col pt-6 px-5 pb-6 overflow-y-auto"
        role="dialog"
        aria-label="Mobile navigation menu"
      >
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-[10px] font-bold uppercase tracking-widest text-[var(--text-dim)]">
            Console Hub
          </h2>
          <button
            onClick={onClose}
            className="p-1 text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-white/[0.04] border border-[var(--border)] rounded-md cursor-pointer"
            aria-label="Close mobile menu"
          >
            <X size={15} />
          </button>
        </div>

        {/* Mobile Quick Search */}
        <button
          onClick={() => {
            onClose();
            setCommandMenuOpen(true);
          }}
          className="w-full flex items-center justify-between p-2.5 rounded-lg border border-[var(--border)] bg-white/[0.02] text-[var(--text-secondary)] mb-6 text-xs text-left"
        >
          <span className="flex items-center gap-2">
            <Search size={13} /> Quick Search...
          </span>
          <kbd className="text-[8px] font-mono border border-white/[0.08] px-1 rounded bg-white/[0.04]">
            ⌘K
          </kbd>
        </button>

        <nav className="flex-1 space-y-6" aria-label="Mobile navigation">
          {dynamicMenuGroups.map((group) => (
            <div key={group.key}>
              <h2 className="text-[10px] font-bold uppercase tracking-wider text-[var(--accent)] mb-2.5 ml-1 flex items-center gap-1.5">
                <span>{group.emoji}</span> {group.label}
              </h2>
              <div className="space-y-1">
                {group.items.map((item: any) => (
                  <Link
                    key={item.href}
                    to={item.href}
                    onClick={onClose}
                    onMouseEnter={() => prefetchRoute(item.href)}
                    className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/[0.03] border border-transparent hover:border-[var(--border)] transition-colors group"
                  >
                    <div className={`p-1.5 rounded-md ${getIconStyles(colorKeyFromMenuItem(item))}`}>
                      <item.icon size={13} aria-hidden="true" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between">
                        <h3 className="text-xs font-bold text-[var(--text-primary)]">
                          {item.title}
                        </h3>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </nav>

        {/* Mobile footer */}
        <div className="mt-8 pt-6 border-t border-white/[0.03] space-y-3">
          <div className="flex justify-between items-center text-[9px] font-bold font-mono uppercase text-[var(--text-dim)]">
            <span>CPU Core Load</span>
            <span>{telemetryStats.cpu}%</span>
          </div>
          <div className="flex justify-between items-center text-[9px] font-bold font-mono uppercase text-[var(--text-dim)]">
            <span>Broker Sync</span>
            <span className="text-[var(--success)]">Connected</span>
          </div>
          {user && (
            <div className="mt-4 p-2 bg-white/[0.02] border border-white/[0.03] rounded-lg flex items-center gap-2.5">
              <div className="w-7 h-7 rounded bg-[var(--accent-muted)] border border-[var(--accent-border)] flex items-center justify-center text-[var(--accent)] font-bold text-xs">
                {(user.full_name || user.username).charAt(0).toUpperCase()}
              </div>
              <div className="min-w-0 flex-1">
                <h4 className="text-[11px] font-bold text-[var(--text-primary)] truncate">
                  {user.full_name || user.username}
                </h4>
                <p className="text-[8px] font-mono text-[var(--accent)] uppercase">
                  {user.role}
                </p>
              </div>
              <button
                onClick={() => {
                  onClose();
                  logout();
                }}
                className="p-1.5 text-[var(--text-dim)] hover:text-[var(--danger)] hover:bg-[var(--danger-muted)] rounded transition-colors"
                aria-label="Sign out"
              >
                <LogOut size={13} />
              </button>
            </div>
          )}
        </div>
      </motion.div>
    </>
  );
}
