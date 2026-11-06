import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown } from 'lucide-react';

export interface CIProfileOption {
  id: number;
  name: string;
  desc: string;
}

export const CI_PATIENT_OPTIONS: CIProfileOption[] = [
  { id: 2, name: "Sarah Jenkins", desc: "MRN: 102048 • ICU-A" },
  { id: 3, name: "Marcus Thorne", desc: "MRN: 103072 • Cardiac Care" },
  { id: 4, name: "Linda Zhao", desc: "MRN: 104096 • Med-Surg 4B" },
  { id: 5, name: "Robert Garcia", desc: "MRN: 105120 • Med-Surg 4B" },
  { id: 6, name: "Emily Watson", desc: "MRN: 106144 • Pediatric Ward" },
  { id: 7, name: "Oscar Meyer", desc: "MRN: 107168 • ICU-A" },
];

export interface CIProfileSelectProps {
  value: number;
  onSelect: (idx: number) => void;
}

// Custom Searchable Combobox for Clinical Intelligence
export const CIProfileSelect = ({ value, onSelect }: CIProfileSelectProps) => {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const selectRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (selectRef.current && !selectRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const filteredOptions = query === "" 
    ? CI_PATIENT_OPTIONS 
    : CI_PATIENT_OPTIONS.filter((opt) => 
        opt.name.toLowerCase().includes(query.toLowerCase()) || 
        opt.desc.toLowerCase().includes(query.toLowerCase())
      );

  const selectedOption = CI_PATIENT_OPTIONS.find(o => o.id === value);
  const displayValue = open ? query : (selectedOption ? selectedOption.name : "");

  return (
    <div className="relative w-64" ref={selectRef}>
      <div 
        className={`w-full bg-[rgba(255,255,255,0.02)] border ${
          open ? 'border-indigo-500 ring-1 ring-indigo-500' : 'border-slate-800 hover:bg-[rgba(255,255,255,0.04)]'
        } px-3 py-2 text-slate-200 text-sm rounded-lg transition-all flex justify-between items-center`}
      >
        <input
          type="text"
          className="w-full bg-transparent outline-none placeholder:text-slate-500 font-medium"
          placeholder="Search patient..."
          value={displayValue}
          onChange={(e) => {
            setQuery(e.target.value);
            if (!open) setOpen(true);
          }}
          onFocus={() => {
            setQuery("");
            setOpen(true);
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && filteredOptions.length > 0) {
              onSelect(filteredOptions[0].id);
              setOpen(false);
            }
          }}
        />
        <ChevronDown 
          size={14} 
          className={`text-slate-400 transition-transform cursor-pointer ${open ? "rotate-180 text-indigo-400" : ""}`} 
          onClick={() => setOpen(!open)} 
          aria-hidden="true" 
        />
      </div>
      
      <AnimatePresence>
        {open && (
          <motion.div 
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.1 }}
            className="absolute top-full left-0 right-0 mt-1 bg-slate-900 border border-slate-700 rounded-lg overflow-hidden z-50 shadow-xl"
          >
            <div className="max-h-52 overflow-y-auto py-1">
              {filteredOptions.length === 0 ? (
                <div className="px-3 py-2 text-sm text-slate-500">No patients found.</div>
              ) : (
                filteredOptions.map((opt) => (
                  <div 
                    key={opt.id}
                    onClick={() => {
                      onSelect(opt.id);
                      setOpen(false);
                    }}
                    className={`px-3 py-2 hover:bg-indigo-500/10 hover:text-indigo-400 text-sm cursor-pointer transition-colors text-slate-300 border-b border-[rgba(255,255,255,0.02)] last:border-0 ${
                      value === opt.id ? 'bg-indigo-500/10 text-indigo-400' : ''
                    }`}
                  >
                    <div className="font-semibold">{opt.name}</div>
                    <div className="text-[11px] text-slate-500 mt-0.5">{opt.desc}</div>
                  </div>
                ))
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
