/**
 * CommandPalette — Ctrl+K / ⌘K modal for quick navigation.
 * Lazy-loaded to keep it out of the critical rendering path.
 */
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "@/lib/auth";
import { motion, AnimatePresence } from "framer-motion";
import { Search, X, Command } from "lucide-react";
import { COMMAND_ITEMS } from "./nav-config";

interface CommandPaletteProps {
  open: boolean;
  onClose: () => void;
}

export default function CommandPalette({ open, onClose }: CommandPaletteProps) {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);

  // Reset on open/close
  useEffect(() => {
    if (open) {
      setSearchQuery("");
      setSelectedIndex(0);
    }
  }, [open]);

  // Filter items
  const filteredCommandItems = COMMAND_ITEMS.filter((item) => {
    if (item.category === "Admin" && (!user || user.role !== "admin")) return false;
    const query = searchQuery.toLowerCase();
    return (
      item.label.toLowerCase().includes(query) ||
      item.desc.toLowerCase().includes(query) ||
      item.category.toLowerCase().includes(query)
    );
  });

  // Reset selected on search change
  useEffect(() => {
    setSelectedIndex(0);
  }, [searchQuery]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
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
        onClose();
      }
    } else if (e.key === "Escape") {
      onClose();
    }
  };

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.6 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-[100] bg-black/70 backdrop-blur-sm"
          />

          {/* Modal */}
          <div className="fixed inset-0 z-[101] flex items-start justify-center p-4 sm:p-10 pt-[10vh] sm:pt-[15vh] pointer-events-none">
            <motion.div
              initial={{ scale: 0.96, opacity: 0, y: -20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.96, opacity: 0, y: -20 }}
              transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
              className="w-full max-w-xl bg-[rgba(12,12,14,0.95)] border border-[var(--border-focus)] rounded-xl shadow-[var(--shadow-lg)] overflow-hidden flex flex-col pointer-events-auto max-h-[80vh] backdrop-blur-2xl"
              onKeyDown={handleKeyDown}
            >
              {/* Search Input */}
              <div className="flex items-center gap-3 px-4 py-3.5 border-b border-white/[0.04] relative">
                <Search size={15} className="text-[var(--text-dim)] shrink-0" />
                <input
                  type="text"
                  placeholder="Search modules, predictors, billing, or profile settings..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="flex-1 text-xs text-[var(--text-primary)] placeholder-[var(--text-muted)] bg-transparent outline-none border-none py-0.5"
                  autoFocus
                />
                <div className="flex items-center gap-1.5 shrink-0">
                  <span className="text-[8px] font-bold font-mono px-1 rounded bg-white/[0.06] border border-white/[0.08] text-[var(--text-dim)]">
                    ESC
                  </span>
                  <button
                    onClick={onClose}
                    className="p-1 rounded hover:bg-white/[0.04] text-[var(--text-dim)] hover:text-[var(--text-primary)] transition-colors cursor-pointer"
                    aria-label="Close search"
                  >
                    <X size={14} />
                  </button>
                </div>
              </div>

              {/* Command Items */}
              <div className="flex-1 overflow-y-auto p-2 space-y-3 max-h-[50vh]">
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
                      <h4 className="px-3 py-1.5 text-[9px] font-mono font-bold uppercase tracking-wider text-[var(--accent)]">
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
                                onClose();
                              }}
                              onMouseEnter={() => setSelectedIndex(globalIndex)}
                              className={`w-full flex items-center gap-3 p-2.5 rounded-lg text-left transition-all duration-150 group cursor-pointer ${
                                isSelected
                                  ? "bg-[var(--accent-muted)] border border-[var(--accent-border)]"
                                  : "bg-transparent border border-transparent hover:bg-white/[0.01]"
                              }`}
                            >
                              <div
                                className={`p-2 rounded-lg transition-colors shrink-0 ${
                                  isSelected
                                    ? "bg-[var(--accent)]/15 text-[var(--accent)] border border-[var(--accent)]/20"
                                    : "bg-white/[0.02] text-[var(--text-dim)] border border-white/[0.04] group-hover:text-[var(--text-primary)]"
                                }`}
                              >
                                <item.icon size={13} />
                              </div>
                              <div className="min-w-0 flex-1">
                                <div className="flex items-center justify-between">
                                  <span
                                    className={`text-[11px] font-bold transition-colors truncate ${
                                      isSelected
                                        ? "text-[var(--accent)]"
                                        : "text-[var(--text-primary)]"
                                    }`}
                                  >
                                    {item.label}
                                  </span>
                                  {isSelected && (
                                    <span className="text-[8px] font-bold font-mono px-1 rounded bg-[var(--accent)]/10 text-[var(--accent)] uppercase tracking-wider scale-90">
                                      Open
                                    </span>
                                  )}
                                </div>
                                <p className="text-[9px] text-[var(--text-dim)] truncate mt-0.5 group-hover:text-[var(--text-secondary)] transition-colors">
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
                  <div className="py-8 text-center">
                    <Command size={20} className="mx-auto text-white/[0.04] mb-2" />
                    <p className="text-xs font-bold text-[var(--text-secondary)] uppercase">
                      No matching modules found
                    </p>
                    <p className="text-[10px] text-[var(--text-dim)] mt-1">
                      Try searching for keywords like &quot;heart&quot;, &quot;predict&quot;,
                      &quot;beds&quot;, or &quot;settings&quot;.
                    </p>
                  </div>
                )}
              </div>

              {/* Footer */}
              <div className="px-4 py-2 bg-white/[0.01] border-t border-white/[0.03] flex justify-between items-center text-[8px] font-mono text-[var(--text-dim)] uppercase tracking-wider">
                <div className="flex gap-3">
                  <span>↑↓ to navigate</span>
                  <span>↵ to open</span>
                </div>
                <span>Quick Console Navigator</span>
              </div>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
}
