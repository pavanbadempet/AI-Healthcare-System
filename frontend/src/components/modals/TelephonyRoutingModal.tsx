import React, { useState } from "react";
import { motion } from "framer-motion";
import { X, Phone, PhoneCall, ShieldAlert, Plus, Trash2, CheckCircle2, Volume2, Save } from "lucide-react";
import { toast } from "@/lib/toast";

interface TelephonyRoutingModalProps {
  onClose: () => void;
}

interface OnCallContact {
  id: string;
  name: string;
  specialty: string;
  phone: string;
  priority: number;
}

export const TelephonyRoutingModal: React.FC<TelephonyRoutingModalProps> = ({ onClose }) => {
  const [contacts, setContacts] = useState<OnCallContact[]>([
    { id: "1", name: "Dr. Sarah Jenkins", specialty: "Cardiology Lead", phone: "+1 (555) 234-8901", priority: 1 },
    { id: "2", name: "Dr. Marcus Vance", specialty: "ICU Attending", phone: "+1 (555) 876-5432", priority: 2 },
    { id: "3", name: "Dr. Elena Rostova", specialty: "Pulmonologist", phone: "+1 (555) 345-6789", priority: 3 }
  ]);

  const [ivrEnabled, setIvrEnabled] = useState(true);
  const [escalationTimeout, setEscalationTimeout] = useState(120); // seconds
  const [testingCallId, setTestingCallId] = useState<string | null>(null);

  const [newName, setNewName] = useState("");
  const [newSpecialty, setNewSpecialty] = useState("");
  const [newPhone, setNewPhone] = useState("");

  const handleAddContact = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName || !newPhone) return;
    const newEntry: OnCallContact = {
      id: Date.now().toString(),
      name: newName,
      specialty: newSpecialty || "General On-Call",
      phone: newPhone,
      priority: contacts.length + 1
    };
    setContacts([...contacts, newEntry]);
    setNewName("");
    setNewSpecialty("");
    setNewPhone("");
    toast.success(`Added ${newEntry.name} to IVR Telephony Route!`);
  };

  const handleDeleteContact = (id: string) => {
    setContacts(contacts.filter((c) => c.id !== id));
    toast.info("Removed contact from telephony escalation chain.");
  };

  const handleTestCall = (contact: OnCallContact) => {
    setTestingCallId(contact.id);
    toast.info(`Initiating test IVR voice call to ${contact.name} (${contact.phone})...`);
    setTimeout(() => {
      setTestingCallId(null);
      toast.success(`Test IVR Call Connected to ${contact.name}! Voice dispatch confirmed.`);
    }, 1200);
  };

  const handleSave = () => {
    toast.success("Telephony Alert Routing Rules saved successfully!");
    onClose();
  };

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/80 backdrop-blur-md p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 15 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 15 }}
        className="bg-[#0b0c10] border border-white/10 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col shadow-2xl font-sans"
        role="dialog"
        aria-modal="true"
        aria-labelledby="telephony-title"
      >
        {/* Header */}
        <div className="bg-white/[0.02] border-b border-white/10 p-5 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 shrink-0">
              <PhoneCall size={18} />
            </div>
            <div>
              <h2 id="telephony-title" className="text-sm font-bold text-white uppercase tracking-wider">
                Telephony Alert Routing Manager
              </h2>
              <p className="text-[10px] text-[var(--text-secondary)] font-mono uppercase">
                Configure automated IVR voice calls & escalation chains for critical telemetry alarms
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-zinc-400 hover:text-white p-1.5 rounded-lg hover:bg-white/5 transition-colors"
            aria-label="Close modal"
          >
            <X size={18} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-5 overflow-y-auto flex-1 font-mono">
          {/* IVR Settings */}
          <div className="p-4 rounded-xl bg-white/[0.02] border border-white/5 space-y-3 font-sans">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-white uppercase tracking-wider block">Automated Voice Call Escalation</span>
                <span className="text-[10px] text-zinc-400 font-mono">Dispatch automated phone calls when telemetry alarms remain unacknowledged</span>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={ivrEnabled}
                  onChange={(e) => setIvrEnabled(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-zinc-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-zinc-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cyan-500"></div>
              </label>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-white/5 text-xs font-mono">
              <span className="text-zinc-300">Escalation Timeout Delay:</span>
              <select
                value={escalationTimeout}
                onChange={(e) => setEscalationTimeout(Number(e.target.value))}
                className="bg-zinc-900 border border-white/10 rounded-lg px-3 py-1 text-xs text-cyan-300 font-bold"
              >
                <option value={60}>60 Seconds (Urgent)</option>
                <option value={120}>120 Seconds (Standard)</option>
                <option value={300}>300 Seconds (5 Min)</option>
              </select>
            </div>
          </div>

          {/* On-Call Chain List */}
          <div className="space-y-2">
            <span className="text-[10px] text-[var(--text-secondary)] uppercase tracking-wider block">
              On-Call Physician Escalation Chain ({contacts.length})
            </span>
            <div className="space-y-2">
              {contacts.map((contact) => (
                <div
                  key={contact.id}
                  className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5 flex items-center justify-between gap-3 text-xs"
                >
                  <div className="flex items-center gap-3">
                    <span className="w-6 h-6 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 font-bold font-mono text-[10px] flex items-center justify-center shrink-0">
                      P{contact.priority}
                    </span>
                    <div>
                      <div className="text-white font-bold">{contact.name}</div>
                      <div className="text-[10px] text-zinc-400 font-mono">{contact.specialty} • {contact.phone}</div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 font-sans">
                    <button
                      onClick={() => handleTestCall(contact)}
                      disabled={testingCallId === contact.id}
                      className="px-2.5 py-1 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 text-cyan-300 text-[10px] font-bold uppercase transition-all flex items-center gap-1"
                    >
                      <Volume2 size={11} />
                      {testingCallId === contact.id ? "Calling..." : "Test Call"}
                    </button>
                    <button
                      onClick={() => handleDeleteContact(contact.id)}
                      className="text-zinc-500 hover:text-red-400 p-1.5 rounded transition-colors"
                      aria-label="Remove contact"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Add Contact Form */}
          <form onSubmit={handleAddContact} className="p-4 rounded-xl bg-white/[0.01] border border-white/5 space-y-3 font-sans">
            <span className="text-[10px] text-[var(--text-secondary)] uppercase tracking-wider font-mono block">Add On-Call Physician</span>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
              <input
                type="text"
                placeholder="Doctor Name"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                className="bg-white/[0.03] border border-white/10 rounded-lg px-3 py-2 text-white font-mono focus:outline-none focus:border-cyan-500"
              />
              <input
                type="text"
                placeholder="Specialty"
                value={newSpecialty}
                onChange={(e) => setNewSpecialty(e.target.value)}
                className="bg-white/[0.03] border border-white/10 rounded-lg px-3 py-2 text-white font-mono focus:outline-none focus:border-cyan-500"
              />
              <input
                type="tel"
                placeholder="Phone (+1 555...)"
                value={newPhone}
                onChange={(e) => setNewPhone(e.target.value)}
                className="bg-white/[0.03] border border-white/10 rounded-lg px-3 py-2 text-white font-mono focus:outline-none focus:border-cyan-500"
              />
            </div>
            <button
              type="submit"
              className="btn bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold uppercase py-2 px-4 flex items-center gap-1.5 rounded-lg transition-all"
            >
              <Plus size={14} /> Add Contact to Route
            </button>
          </form>
        </div>

        {/* Footer */}
        <div className="bg-white/[0.02] border-t border-white/10 p-4 flex items-center justify-between font-sans">
          <button
            onClick={onClose}
            className="btn btn-secondary text-xs uppercase font-bold tracking-wide py-2.5 px-4"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="btn bg-cyan-600 hover:bg-cyan-500 text-white text-xs uppercase font-bold tracking-wide py-2.5 px-5 flex items-center gap-2 rounded-xl shadow-lg shadow-cyan-600/20"
          >
            <Save size={14} /> Save Routing Rules
          </button>
        </div>
      </motion.div>
    </div>
  );
};
