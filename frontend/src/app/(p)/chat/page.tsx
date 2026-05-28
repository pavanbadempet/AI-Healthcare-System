"use client";

import { useState, useEffect, useRef } from "react";
import { useAuthStore } from "@/lib/auth";
import { streamChat, getChatHistory, clearChatHistory, getChatSuggestions, type ChatMessage } from "@/lib/api";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Bot, User, Trash2, Zap, Settings2, FileText, Database, ShieldAlert, Cpu, BrainCircuit, Loader2, Info } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export default function ChatCopilotPage() {
  const { user } = useAuthStore();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Settings state
  const [ragScope, setRagScope] = useState("patient");
  const [showSettings, setShowSettings] = useState(false);
  const canUseGlobalScope = user?.role === "doctor" || user?.role === "admin";
  const ragOptions = [
    ...(canUseGlobalScope ? [{ id: 'global', label: 'Global DB & Literature', icon: Database }] : []),
    { id: 'patient', label: 'Active Patient Record', icon: User },
    { id: 'guidelines', label: 'Clinical Guidelines', icon: FileText }
  ];

  useEffect(() => {
    getChatHistory()
      .then(history => {
        if (history && history.length > 0) setMessages(history);
      })
      .catch(console.error);

    getChatSuggestions()
      .then(res => setSuggestions(res.suggestions || []))
      .catch(console.error);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  useEffect(() => {
    if (!canUseGlobalScope && ragScope === "global") {
      setRagScope("patient");
    }
  }, [canUseGlobalScope, ragScope]);

  const handleClear = async () => {
    await clearChatHistory();
    setMessages([]);
  };

  const handleSend = async (text: string) => {
    if (!text.trim() || isLoading) return;
    const currentInput = text;
    setInput("");
    
    const newMsg: ChatMessage = { role: "user", content: currentInput };
    setMessages(prev => [...prev, newMsg]);
    setIsLoading(true);

    const history = messages.map(m => ({ role: m.role, content: m.content }));
    
    // Create a placeholder for the assistant reply
    setMessages(prev => [...prev, { role: "assistant", content: "" }]);

    streamChat(
      currentInput,
      history,
      (chunk) => {
        if (chunk.content) {
          setMessages(prev => {
            const newArr = [...prev];
            const last = newArr[newArr.length - 1];
            if (last.role === 'assistant') {
              last.content += chunk.content;
            }
            return newArr;
          });
        }
      },
      () => setIsLoading(false),
      (err) => {
        console.error("Stream error:", err);
        setMessages(prev => {
          const newArr = [...prev];
          const last = newArr[newArr.length - 1];
          if (last.role === 'assistant') {
            last.content += "\n\n**Error:** Connection interrupted.";
          }
          return newArr;
        });
        setIsLoading(false);
      },
      ragScope
    );
  };

  return (
    <div className="w-full h-full flex text-[var(--text-primary)] font-sans selection:bg-[var(--accent)] selection:text-black">
      <div className="w-full flex gap-4 h-full">
        
        {/* Left Side: Clinical Intelligence Engine */}
        <div className="flex-1 flex flex-col panel relative overflow-hidden">
          
          {/* Engine Header */}
          <div className="panel-header flex justify-between items-center">
            <div className="flex items-center gap-3">
              <BrainCircuit size={18} className="text-[var(--accent)]" aria-hidden="true" />
              <div>
                <h1 className="text-sm font-bold text-[var(--text-primary)] uppercase tracking-widest">Medical Intelligence Copilot</h1>
                <p className="mono-meta mt-0.5">RAG CONTEXT | RESPONSE TIME VARIES</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button 
                onClick={handleClear} 
                className="p-1.5 text-[var(--text-dim)] hover:text-[var(--danger)] bg-[var(--bg-card)] border border-[var(--border)] rounded transition-colors"
                title="Purge Memory Context"
                aria-label="Clear chat history"
              >
                <Trash2 size={14} aria-hidden="true" />
              </button>
              <button 
                onClick={() => setShowSettings(!showSettings)}
                className={`p-1.5 border rounded transition-colors ${showSettings ? 'bg-[var(--accent-muted)] text-[var(--accent)] border-[var(--accent-border)]' : 'text-[var(--text-dim)] hover:text-[var(--text-primary)] bg-[var(--bg-card)] border-[var(--border)]'}`}
                aria-label={showSettings ? "Close settings panel" : "Open settings panel"}
                aria-expanded={showSettings}
              >
                <Settings2 size={14} aria-hidden="true" />
              </button>
            </div>
          </div>

          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6" role="log" aria-label="Chat messages" aria-live="polite">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center opacity-50">
                <Database size={48} className="text-[var(--accent)] mb-4" aria-hidden="true" />
                <h2 className="text-lg font-bold text-[var(--text-primary)] uppercase tracking-widest">Engine Ready</h2>
                <p className="text-sm text-[var(--text-dim)] font-mono mt-2 max-w-md">Ask about saved health records, recent checkups, or general medical questions.</p>
                
                <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-2xl">
                  {suggestions.map((s, i) => (
                    <button 
                      key={i} 
                      onClick={() => handleSend(s)}
                      className="p-3 text-left bg-[var(--bg-card)] border border-[var(--border)] hover:border-[var(--accent-border)] hover:bg-[var(--accent-muted)] transition-colors text-xs font-mono text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                    >
                      <Zap size={12} className="inline mr-2 text-[var(--accent)]" aria-hidden="true" /> {s}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((msg, idx) => (
                <motion.div 
                  key={idx} 
                  initial={{ opacity: 0, y: 5 }} 
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`max-w-[85%] md:max-w-[75%] flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                    <div className={`w-8 h-8 rounded shrink-0 flex items-center justify-center border ${
                      msg.role === 'user' 
                        ? 'bg-[var(--bg-card)] text-[var(--text-primary)] border-[var(--border-focus)]' 
                        : 'bg-[var(--accent-muted)] text-[var(--accent)] border-[var(--accent-border)]'
                    }`} aria-hidden="true">
                      {msg.role === 'user' ? <User size={14} /> : <Bot size={14} />}
                    </div>
                    
                    <div className={`px-4 py-3 text-sm rounded ${
                      msg.role === 'user' 
                        ? 'bg-[var(--bg-card-hover)] border border-[var(--border)] text-[var(--text-primary)]' 
                        : 'bg-[var(--bg-card)] border border-[var(--border)] text-[var(--text-primary)]'
                    }`}>
                      {msg.role === 'assistant' ? (
                        <div className="prose prose-invert prose-sm max-w-none prose-p:leading-relaxed prose-pre:bg-[var(--bg-primary)] prose-pre:border prose-pre:border-[var(--border)]">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {msg.content || "..."}
                          </ReactMarkdown>
                        </div>
                      ) : (
                        <p className="whitespace-pre-wrap font-mono text-xs">{msg.content}</p>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))
            )}
            {isLoading && messages[messages.length - 1]?.role === 'user' && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-start">
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded shrink-0 flex items-center justify-center bg-[var(--accent-muted)] text-[var(--accent)] border border-[var(--accent-border)]" aria-hidden="true">
                    <Loader2 size={14} className="animate-spin" />
                  </div>
                  <div className="px-4 py-3 bg-[var(--bg-card)] border border-[var(--border)] rounded text-[var(--text-dim)] text-xs font-mono flex items-center" role="status">
                    ANALYZING CLINICAL VECTORS...
                  </div>
                </div>
              </motion.div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="p-4 bg-[var(--bg-secondary)] border-t border-[var(--border)]">
            <div className="relative flex items-center max-w-4xl mx-auto">
              <label htmlFor="chat-input" className="sr-only">Chat message input</label>
              <input 
                id="chat-input"
                type="text" 
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => { if(e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(input); } }}
                placeholder="Query patient data, run diagnostics, or analyze research..."
                disabled={isLoading}
                className="input-clinical pr-12"
                aria-label="Type a message to the AI copilot"
              />
              <button 
                onClick={() => handleSend(input)}
                disabled={!input.trim() || isLoading}
                className="absolute right-2 p-2 bg-[var(--accent)] text-[var(--text-primary)] hover:bg-[var(--accent-hover)] disabled:opacity-50 disabled:bg-[var(--border)] disabled:text-[var(--text-dim)] transition-colors"
                aria-label="Send message"
              >
                <Send size={16} aria-hidden="true" />
              </button>
            </div>
            <div className="max-w-4xl mx-auto mt-2 flex justify-between items-center mono-meta">
              <span className="flex items-center gap-1"><ShieldAlert size={10} aria-hidden="true" /> ACCOUNT-SCOPED CONTEXT. CLINICIAN REVIEW RECOMMENDED.</span>
              <span>PRESS ENTER TO EXECUTE</span>
            </div>
          </div>
        </div>

        {/* Right Side: Execution Context & Settings */}
        <AnimatePresence>
          {showSettings && (
            <motion.div 
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 320, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              className="hidden lg:flex flex-col panel overflow-hidden shrink-0"
              role="complementary"
              aria-label="Execution context settings"
            >
              <div className="panel-header">
                <h2 className="section-label flex items-center gap-2">
                  <Cpu size={14} className="text-[var(--text-secondary)]" aria-hidden="true" /> Execution Context
                </h2>
              </div>
              
              <div className="p-5 space-y-6 flex-1 overflow-y-auto">
                {/* RAG Scope */}
                <div className="space-y-3">
                  <label className="section-label">RAG Data Context</label>
                  <div className="flex flex-col gap-2" role="radiogroup" aria-label="RAG data context scope">
                    {ragOptions.map(option => (
                      <button 
                        key={option.id}
                        onClick={() => setRagScope(option.id)}
                        className={`flex items-center gap-3 p-3 text-left border transition-colors ${ragScope === option.id ? 'bg-[var(--accent-muted)] border-[var(--accent-border)] text-[var(--accent)]' : 'bg-[var(--bg-card)] border-[var(--border)] text-[var(--text-secondary)] hover:border-[var(--border-focus)]'}`}
                        role="radio"
                        aria-checked={ragScope === option.id}
                      >
                        <option.icon size={14} aria-hidden="true" />
                        <span className="text-[11px] font-bold uppercase tracking-wider">{option.label}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* System Diagnostics */}
                <div className="space-y-3 pt-4 border-t border-[var(--border)]">
                  <label className="section-label">System Diagnostics</label>
                  <div className="bg-[var(--bg-card)] border border-[var(--border)] p-3 text-[11px] font-mono text-[var(--text-secondary)] space-y-2">
                    <div className="flex justify-between">
                      <span>LLM:</span>
                      <span className="text-[var(--text-primary)]">Backend selected</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Mode:</span>
                      <span className="text-[var(--text-primary)]">Medical QA</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Embeddings:</span>
                      <span className="text-[var(--text-primary)]">Backend managed</span>
                    </div>
                    <div className="flex justify-between">
                      <span>RAG scope:</span>
                      <span className="text-[var(--success)]">Role-aware</span>
                    </div>
                  </div>
                </div>
                
                {/* Information Box */}
                <div className="bg-[var(--bg-card)] border border-[var(--border)] p-3 flex gap-3 text-[11px] font-mono text-[var(--text-dim)] leading-relaxed">
                  <Info size={14} className="shrink-0 mt-0.5 text-[var(--accent)]" aria-hidden="true" />
                  <p>Responses can use retrieval-augmented context from account-scoped records and configured clinical references. This is informational and should be reviewed with a qualified clinician.</p>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
