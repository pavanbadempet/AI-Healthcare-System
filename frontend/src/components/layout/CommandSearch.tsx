/**
 * CommandSearch – Search bar with keyboard navigation and filtered results.
 * Extracted from TopNav.tsx for maintainability.
 */
import { useRef, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import Tooltip from "./Tooltip";
import { COMMAND_ITEMS } from "./nav-config";

interface CommandSearchProps {
  user: { role: string } | null;
}

export default function CommandSearch({ user }: CommandSearchProps) {
  const navigate = useNavigate();
  const [searchFocused, setSearchFocused] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const searchContainerRef = useRef<HTMLDivElement>(null);

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

  useEffect(() => {
    setSelectedIndex(0);
  }, [searchQuery]);

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

  // Click outside
  useEffect(() => {
    const handler = (event: MouseEvent) => {
      if (searchFocused && searchContainerRef.current && !searchContainerRef.current.contains(event.target as Node)) {
        setSearchFocused(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [searchFocused]);

  return (
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
  );
}
