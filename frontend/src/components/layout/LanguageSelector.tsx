/**
 * LanguageSelector – i18n language dropdown.
 * Extracted from TopNav.tsx for maintainability.
 */
import { useState, useRef, useEffect } from "react";
import { Globe, ChevronDown } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import Tooltip from "./Tooltip";
import type { Language } from "../../lib/i18n";

interface LanguageSelectorProps {
  language: Language;
  setLanguage: (lang: Language) => void;
}

export default function LanguageSelector({ language, setLanguage }: LanguageSelectorProps) {
  const [languageOpen, setLanguageOpen] = useState(false);
  const languageRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (event: MouseEvent) => {
      if (languageOpen && languageRef.current && !languageRef.current.contains(event.target as Node)) {
        setLanguageOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [languageOpen]);

  const languages: Array<{ code: Language; label: string }> = [
    { code: 'en', label: 'English' },
    { code: 'es', label: 'Español' },
    { code: 'hi', label: 'हिन्दी' },
  ];

  return (
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
              {languages.map((lang) => (
                <button
                  key={lang.code}
                  onClick={() => {
                    setLanguage(lang.code);
                    setLanguageOpen(false);
                  }}
                  className={`w-full flex items-center justify-between px-2.5 py-2 text-[10px] font-bold uppercase tracking-wider rounded-lg transition-colors text-left cursor-pointer ${
                    language === lang.code
                      ? "bg-[var(--accent)]/10 text-[var(--accent)]"
                      : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-white/[0.03]"
                  }`}
                >
                  {lang.label}
                  {language === lang.code && <span className="w-1.5 h-1.5 bg-[var(--accent)] rounded-full" />}
                </button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
