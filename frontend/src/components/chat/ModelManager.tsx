import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Download, Trash2, Check, Loader2, HardDrive, Zap, ChevronLeft, AlertCircle, Globe, Monitor, ExternalLink } from 'lucide-react';
import * as webllm from '@/lib/webllm';
import { useAuthStore } from '@/lib/auth';

const API_BASE = import.meta.env.NEXT_PUBLIC_API_URL || import.meta.env.VITE_PUBLIC_API_URL || "http://127.0.0.1:8000";

/* Types */
interface CatalogModel {
  name: string;
  label: string;
  size: string;
  speed: string;
  quality: string;
  description: string;
  downloaded?: boolean;
}

interface DownloadedModel {
  name: string;
  size: string;
  size_bytes: number;
  parameter_size: string;
  family: string;
  quantization: string;
}

interface PullProgress {
  status: string;
  progress: number;
  error?: string;
}

/* Helpers */
const SPEED_COLORS: Record<string, string> = {
  fastest: 'text-emerald-400',
  fast: 'text-green-400',
  medium: 'text-amber-400',
  slower: 'text-orange-400',
};

const QUALITY_BADGES: Record<string, string> = {
  good: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
  great: 'bg-violet-500/15 text-violet-400 border-violet-500/30',
  excellent: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
};

/* Component */
export const ModelManager: React.FC<{
  onClose: () => void;
  onOllamaSelect: (model: string) => void;
  onWebLLMSelect: (modelId: string) => void;
  onWebLLMUnload: () => void;
  onWebLLMLoad: (modelId: string) => Promise<void>;
  currentOllamaModel: string;
  currentWebLLMModel: string | null;
  webllmActive: boolean;
  webllmLoading: string | null;
  webllmProgress: webllm.WebLLMProgress | null;
}> = ({ onClose, onOllamaSelect, onWebLLMSelect, onWebLLMUnload, onWebLLMLoad, currentOllamaModel, currentWebLLMModel, webllmActive, webllmLoading, webllmProgress }) => {
  const { token, user } = useAuthStore();
  const isAdmin = user?.role === 'admin';
  const [catalog, setCatalog] = useState<CatalogModel[]>([]);
  const [downloaded, setDownloaded] = useState<DownloadedModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [ollamaAvailable, setOllamaAvailable] = useState(true);
  const [pulling, setPulling] = useState<string | null>(null);
  const [pullProgress, setPullProgress] = useState<PullProgress | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [tab, setTab] = useState<'library' | 'downloaded' | 'browser'>('library');

  // WebLLM state
  const [webGPUSupported] = useState(() => webllm.isWebGPUSupported());

  const abortRef = useRef<AbortController | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [libRes, modRes] = await Promise.all([
        fetch(`${API_BASE}/ai/models/library`),
        fetch(`${API_BASE}/ai/models`),
      ]);
      if (libRes.ok) {
        const libData = await libRes.json();
        setCatalog(libData.catalog || []);
      }
      if (modRes.ok) {
        const modData = await modRes.json();
        setDownloaded(modData.models || []);
        setOllamaAvailable(modData.available !== false);
      }
    } catch {
      setOllamaAvailable(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);
  useEffect(() => { return () => { abortRef.current?.abort(); }; }, []);

  const modelMutationHeaders = useCallback(() => ({
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }), [token]);

  // Auto-switch to Browser tab if no Ollama
  useEffect(() => {
    if (!loading && !ollamaAvailable && webGPUSupported) {
      setTab('browser');
    }
  }, [loading, ollamaAvailable, webGPUSupported]);

  /* Ollama Handlers */
  const handlePull = useCallback(async (modelName: string) => {
    if (!isAdmin) {
      setPullProgress({ status: 'error', progress: 0, error: 'Admin access required to download server models.' });
      return;
    }
    setPulling(modelName);
    setPullProgress({ status: 'starting', progress: 0 });
    const controller = new AbortController();
    abortRef.current = controller;
    try {
      const response = await fetch(`${API_BASE}/ai/models/pull`, {
        method: 'POST',
        headers: modelMutationHeaders(),
        body: JSON.stringify({ name: modelName }),
        signal: controller.signal,
      });
      if (!response.ok || !response.body) {
        const body = await response.json().catch(() => ({}));
        setPullProgress({ status: 'error', progress: 0, error: body.detail || 'Failed to start download' });
        setPulling(null);
        return;
      }
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith('data: ')) continue;
          try {
            const data = JSON.parse(trimmed.substring(6));
            if (data.error) {
              setPullProgress({ status: 'error', progress: 0, error: data.error });
              setPulling(null);
              return;
            }
            setPullProgress({ status: data.status || 'downloading', progress: data.progress || 0 });
          } catch { /* skip */ }
        }
      }
      reader.releaseLock();
      setPullProgress(null);
      setPulling(null);
      fetchData();
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        setPullProgress({ status: 'error', progress: 0, error: String(err) });
      }
      setPulling(null);
    }
  }, [fetchData, isAdmin, modelMutationHeaders]);

  const handleDelete = useCallback(async (modelName: string) => {
    if (!isAdmin) return;
    if (!confirm(`Delete ${modelName}? This cannot be undone.`)) return;
    setDeleting(modelName);
    try {
      const res = await fetch(`${API_BASE}/ai/models`, {
        method: 'DELETE',
        headers: modelMutationHeaders(),
        body: JSON.stringify({ name: modelName }),
      });
      if (res.ok) fetchData();
    } catch { /* ignore */ }
    finally { setDeleting(null); }
  }, [fetchData, isAdmin, modelMutationHeaders]);

  const handleSelect = useCallback((modelName: string) => {
    onOllamaSelect(modelName);
    onClose();
  }, [onOllamaSelect, onClose]);

  /* WebLLM Handlers */

  const downloadedNames = new Set(downloaded.map(m => m.name));

  return (
    <div className="absolute inset-0 z-50 bg-zinc-950/95 backdrop-blur-3xl flex flex-col animate-in fade-in zoom-in-95 duration-200">
      {/* Header */}
      <div className="shrink-0 flex items-center justify-between px-5 py-4 border-b border-zinc-800/50 bg-zinc-900/50">
        <div className="flex items-center gap-3">
          <button onClick={onClose} aria-label="Close model manager" className="p-1.5 rounded-lg hover:bg-zinc-800 text-zinc-400 hover:text-white transition-colors">
            <ChevronLeft className="w-4 h-4" />
          </button>
          <div className="flex items-center gap-2">
            <HardDrive className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-bold tracking-tight text-white uppercase">Model Manager</h3>
          </div>
        </div>
      </div>

      {/* Ollama unavailable notice (only on non-browser tabs) */}
      {!ollamaAvailable && !loading && tab !== 'browser' && (
        <div className="mx-4 mt-4 p-4 rounded-xl bg-orange-500/10 border border-orange-500/30 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-orange-400 mt-0.5 shrink-0" />
          <div className="text-xs text-orange-300/90 space-y-2">
            <p className="font-bold text-orange-400 uppercase tracking-wide">Ollama Runtime Not Detected</p>
            <p className="leading-relaxed">
              Local inference requires the Ollama engine. 
              Install it securely from <a href="https://ollama.com/download" target="_blank" rel="noreferrer" className="underline font-bold text-white hover:text-orange-200 inline-flex items-center gap-1">ollama.com <ExternalLink size={10} /></a> to download hardware-accelerated models.
            </p>
            <div className="pt-2">
              <button onClick={() => setTab('browser')} className="px-3 py-1.5 rounded-lg bg-orange-500/20 hover:bg-orange-500/30 font-bold text-orange-400 transition-colors">
                Use Browser AI Instead
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="shrink-0 flex border-b border-zinc-800/50 mx-4 mt-4">
        {([
          { key: 'library' as const, label: `Catalog (${catalog.length})`, icon: Monitor },
          { key: 'downloaded' as const, label: `Installed (${downloaded.length})`, icon: HardDrive },
          { key: 'browser' as const, label: 'Browser AI', icon: Globe },
        ]).map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex-1 py-3 text-[10px] font-bold tracking-widest uppercase transition-all border-b-2 flex items-center justify-center gap-1.5 ${
              tab === t.key ? 'text-cyan-400 border-cyan-400 bg-cyan-400/5' : 'text-zinc-500 border-transparent hover:text-zinc-300 hover:bg-zinc-800/30'
            }`}
          >
            <t.icon className="w-3.5 h-3.5" />
            {t.label}
          </button>
        ))}
      </div>

      {/* Download / Load Progress Bar */}
      {((pulling && pullProgress) || webllmProgress) && (
        <div className="shrink-0 mx-4 mt-4 p-4 rounded-xl bg-cyan-500/10 border border-cyan-500/30 shadow-[0_0_20px_rgba(6,182,212,0.15)]">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-cyan-400 truncate flex items-center gap-2">
              <Loader2 className="w-3.5 h-3.5 animate-spin" /> {pulling || webllmLoading || 'Loading...'}
            </span>
            <span className="text-xs text-cyan-300 font-mono font-bold">
              {pullProgress
                ? `${pullProgress.progress.toFixed(0)}%`
                : `${((webllmProgress?.progress ?? 0) * 100).toFixed(0)}%`}
            </span>
          </div>
          <div className="h-2 rounded-full bg-zinc-900 overflow-hidden border border-zinc-800">
            <div
              className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-blue-500 transition-all duration-300 ease-out shadow-[0_0_10px_rgba(6,182,212,0.8)]"
              style={{
                width: pullProgress
                  ? `${Math.min(pullProgress.progress, 100)}%`
                  : `${Math.min((webllmProgress?.progress ?? 0) * 100, 100)}%`,
              }}
            />
          </div>
          <p className="text-[10px] text-cyan-500/70 mt-2 truncate font-mono uppercase tracking-wide">
            {pullProgress?.status || webllmProgress?.text || 'Processing...'}
          </p>
          {pullProgress?.error && <p className="text-[10px] text-red-400 mt-2 font-bold bg-red-500/10 p-2 rounded">{pullProgress.error}</p>}
        </div>
      )}

      {/* Content */}
      <div className="flex-1 min-h-0 overflow-y-auto px-4 py-4 space-y-3 no-scrollbar">
        {loading && tab !== 'browser' ? (
          <div className="flex items-center justify-center py-20">
            <div className="relative">
              <div className="absolute inset-0 rounded-full blur-xl bg-cyan-500/20"></div>
              <Loader2 className="w-8 h-8 text-cyan-400 animate-spin relative" />
            </div>
          </div>

        ) : tab === 'browser' ? (
          /* Browser AI (WebLLM) */
          <>
            {!webGPUSupported ? (
              <div className="flex flex-col items-center justify-center py-16 text-center bg-zinc-900/30 rounded-2xl border border-zinc-800/50 mt-4">
                <AlertCircle className="w-10 h-10 text-orange-400/60 mb-4" />
                <p className="text-sm font-bold text-white uppercase tracking-wide">WebGPU Not Available</p>
                <p className="text-xs text-zinc-400 mt-2 max-w-[280px] leading-relaxed">
                  Browser AI requires WebGPU hardware acceleration (Chrome 113+ or Edge 113+). Please update your browser or use the Ollama engine.
                </p>
              </div>
            ) : (
              <>
                <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 mb-4 flex gap-3 shadow-[0_0_20px_rgba(16,185,129,0.05)]">
                  <Globe className="w-5 h-5 text-emerald-400 shrink-0" />
                  <div>
                    <span className="text-xs font-bold text-emerald-400 uppercase tracking-widest block mb-1">Browser AI Engine</span>
                    <p className="text-[11px] text-emerald-500/70 leading-relaxed font-medium">
                      Inference runs entirely in your local browser VRAM via WebGPU. No server, no daemon. Data never leaves your device.
                    </p>
                  </div>
                </div>

                {webllm.WEBLLM_MODELS.map(model => {
                  const isActive = webllmActive && currentWebLLMModel === model.id;
                  const isLoading = webllmLoading === model.id;

                  return (
                    <div
                      key={model.id}
                      className={`rounded-xl border transition-all duration-300 ${
                        isActive
                          ? 'border-emerald-500/50 bg-emerald-500/10 shadow-[0_0_15px_rgba(16,185,129,0.1)]'
                          : 'border-zinc-800/60 bg-zinc-900/40 hover:border-zinc-700 hover:bg-zinc-800/60'
                      }`}
                    >
                      <div className="p-4">
                        <div className="flex items-center gap-2 flex-wrap mb-1">
                          <span className="text-sm font-bold text-white">{model.label}</span>
                          {isActive && (
                            <span className="px-2 py-0.5 text-[9px] font-black uppercase tracking-widest rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 shadow-[0_0_10px_rgba(16,185,129,0.3)]">Active VRAM</span>
                          )}
                        </div>
                        <p className="text-xs text-zinc-400 leading-relaxed">{model.description}</p>
                        <div className="flex items-center gap-3 mt-3">
                          <span className="text-[10px] text-zinc-500 font-mono font-bold bg-zinc-950 px-2 py-1 rounded border border-zinc-800">{model.size}</span>
                          <span className="text-[10px] px-2 py-1 rounded border bg-cyan-500/10 text-cyan-400 border-cyan-500/30 font-bold uppercase tracking-widest">WebGPU</span>
                        </div>

                        <div className="flex items-center gap-2 mt-4 pt-4 border-t border-zinc-800/50">
                          {isActive ? (
                            <>
                              <span className="flex-1 py-2 rounded-lg bg-emerald-500/20 text-emerald-400 text-xs font-bold flex items-center justify-center gap-2">
                                <Check className="w-4 h-4" /> Loaded in Browser
                              </span>
                              <button
                                onClick={onWebLLMUnload}
                                className="px-4 py-2 rounded-lg border border-red-500/30 text-xs font-bold text-red-400 hover:bg-red-500/10 transition-colors"
                              >
                                Free VRAM
                              </button>
                            </>
                          ) : (
                            <button
                              onClick={() => onWebLLMLoad(model.id)}
                              disabled={!!webllmLoading}
                              className="w-full py-2.5 rounded-lg bg-white text-zinc-950 text-xs font-bold hover:bg-zinc-200 transition-all flex items-center justify-center gap-2 disabled:opacity-40"
                            >
                              {isLoading ? (
                                <><Loader2 className="w-4 h-4 animate-spin" /> Allocating Memory...</>
                              ) : (
                                <><Zap className="w-4 h-4" /> Load Engine to VRAM</>
                              )}
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </>
            )}
          </>

        ) : tab === 'library' ? (
          /* Ollama Library Catalog */
          catalog.map(model => {
            const isDownloaded = model.downloaded || downloadedNames.has(model.name);
            const isPulling = pulling === model.name;
            const isActive = currentOllamaModel === model.name;
            
            // To fix missing modelMode reference, we rely on the parent logic, but we can assume if it's selected it's active.
            // Wait, we don't have modelMode here. Let's just use currentOllamaModel.
            
            return (
              <div key={model.name} className={`group rounded-xl border transition-all duration-300 ${currentOllamaModel === model.name ? 'border-cyan-500/40 bg-cyan-500/5 shadow-[0_0_15px_rgba(6,182,212,0.1)]' : 'border-zinc-800/60 bg-zinc-900/40 hover:border-zinc-700 hover:bg-zinc-800/60'}`}>
                <div className="p-4">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap mb-1">
                        <span className="text-sm font-bold text-white">{model.label}</span>
                        {currentOllamaModel === model.name && <span className="px-2 py-0.5 text-[9px] font-black uppercase tracking-widest rounded bg-cyan-500/20 text-cyan-400 border border-cyan-500/40 shadow-[0_0_10px_rgba(6,182,212,0.3)]">Target</span>}
                      </div>
                      <p className="text-xs text-zinc-400 leading-relaxed">{model.description}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 mt-3 flex-wrap">
                    <span className="text-[10px] text-zinc-500 font-mono font-bold bg-zinc-950 px-2 py-1 rounded border border-zinc-800">{model.size}</span>
                    <span className={`text-[9px] font-black uppercase tracking-widest ${SPEED_COLORS[model.speed] || 'text-zinc-500'}`}>{model.speed}</span>
                    <span className={`text-[9px] px-2 py-1 rounded border font-black uppercase tracking-widest ${QUALITY_BADGES[model.quality] || ''}`}>{model.quality}</span>
                  </div>
                  <div className="flex items-center gap-2 mt-4 pt-4 border-t border-zinc-800/50">
                    {isDownloaded ? (
                      <>
                        <button onClick={() => handleSelect(model.name)} disabled={currentOllamaModel === model.name} className={`flex-1 py-2.5 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-2 ${currentOllamaModel === model.name ? 'bg-cyan-500/20 text-cyan-400 cursor-default' : 'bg-white text-zinc-950 hover:bg-zinc-200 shadow-[0_0_15px_rgba(255,255,255,0.1)]'}`}>
                          {currentOllamaModel === model.name ? <><Check className="w-4 h-4" /> Selected</> : <><Zap className="w-4 h-4" /> Set as Active Model</>}
                        </button>
                        {currentOllamaModel !== model.name && isAdmin && (
                          <button onClick={() => handleDelete(model.name)} disabled={deleting === model.name} aria-label={`Delete ${model.name}`} className="px-4 py-2.5 rounded-lg border border-red-500/30 text-xs font-bold text-red-400 hover:bg-red-500/10 transition-colors flex items-center justify-center gap-2">
                            {deleting === model.name ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                          </button>
                        )}
                      </>
                    ) : isAdmin ? (
                      <button onClick={() => handlePull(model.name)} disabled={!!pulling || !ollamaAvailable} className="w-full py-2.5 rounded-lg border border-cyan-500/50 text-xs font-bold text-cyan-400 hover:bg-cyan-500/10 transition-all flex items-center justify-center gap-2 disabled:opacity-40 disabled:border-zinc-700 disabled:text-zinc-500 disabled:hover:bg-transparent">
                        {isPulling ? <><Loader2 className="w-4 h-4 animate-spin" /> Downloading to Local Daemon...</> : <><Download className="w-4 h-4" /> Download to Local Hub</>}
                      </button>
                    ) : (
                      <div className="w-full py-2.5 rounded-lg border border-zinc-800 text-xs font-bold text-zinc-500 bg-zinc-950/40 flex items-center justify-center gap-2">
                        <AlertCircle className="w-4 h-4" /> Admin access required
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })

        ) : (
          /* Downloaded Models */
          downloaded.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-center bg-zinc-900/30 rounded-2xl border border-zinc-800/50 mt-4">
              <HardDrive className="w-12 h-12 text-zinc-700 mb-4" />
              <p className="text-sm font-bold text-white uppercase tracking-wide">No Local Models Found</p>
              <p className="text-xs text-zinc-500 mt-2">Browse the Catalog tab to download high-performance models</p>
            </div>
          ) : (
            downloaded.map(model => {
              const isActive = currentOllamaModel === model.name;
              return (
                <div key={model.name} className={`rounded-xl border p-4 transition-all duration-300 ${isActive ? 'border-cyan-500/40 bg-cyan-500/5 shadow-[0_0_15px_rgba(6,182,212,0.1)]' : 'border-zinc-800/60 bg-zinc-900/40 hover:border-zinc-700 hover:bg-zinc-800/60'}`}>
                  <div className="flex items-center justify-between">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-bold text-white truncate">{model.name}</span>
                        {isActive && <span className="px-2 py-0.5 text-[9px] font-black uppercase tracking-widest rounded bg-cyan-500/20 text-cyan-400 border border-cyan-500/40">Active</span>}
                      </div>
                      <div className="flex items-center gap-3 mt-2">
                        <span className="text-[10px] text-zinc-500 font-mono font-bold bg-zinc-950 px-2 py-1 rounded border border-zinc-800">{model.size}</span>
                        {model.parameter_size && <span className="text-[10px] text-zinc-400">{model.parameter_size} parameters</span>}
                        {model.quantization && <span className="text-[10px] px-1.5 py-0.5 rounded border border-zinc-700 text-zinc-500 uppercase">{model.quantization}</span>}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0 ml-4">
                      <button onClick={() => handleSelect(model.name)} disabled={isActive} className={`py-2 px-4 rounded-lg text-xs font-bold transition-all shadow-md ${isActive ? 'bg-cyan-500/20 text-cyan-400 cursor-default shadow-none' : 'bg-white text-zinc-950 hover:bg-zinc-200 shadow-[0_0_15px_rgba(255,255,255,0.1)]'}`}>
                        {isActive ? 'Active' : 'Select'}
                      </button>
                      {!isActive && isAdmin && (
                        <button onClick={() => handleDelete(model.name)} disabled={deleting === model.name} aria-label={`Delete ${model.name}`} className="p-2 rounded-lg border border-zinc-800 hover:border-red-500/50 hover:bg-red-500/10 hover:text-red-400 text-zinc-500 transition-colors">
                          {deleting === model.name ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })
          )
        )}
      </div>
    </div>
  );
};
