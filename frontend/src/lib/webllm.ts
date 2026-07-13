/**
 * WebLLM Engine — Browser-native AI via WebGPU
 * Ported from Universe Dex.
 * Runs LLM inference entirely in the browser with no server needed.
 * Uses @mlc-ai/web-llm with OpenAI-compatible streaming API.
 */

import type { InitProgressReport, MLCEngine } from '@mlc-ai/web-llm';

/* ─── Types ─── */
export interface WebLLMModel {
  id: string;
  label: string;
  size: string;
  description: string;
}

export interface WebLLMProgress {
  text: string;
  progress: number; // 0-1
}

type ProgressCallback = (p: WebLLMProgress) => void;
type ChunkCallback = (text: string) => void;

/* ─── Curated Browser Models ─── */
export const WEBLLM_MODELS: WebLLMModel[] = [
  { id: 'Llama-3.2-1B-Instruct-q4f16_1-MLC', label: 'Llama 3.2 1B', size: '~0.7 GB', description: 'Ultra-light, fastest option for basic medical Q&A' },
  { id: 'Llama-3-8B-Instruct-q4f32_1-MLC', label: 'Llama 3 8B', size: '~4.3 GB', description: 'Highly capable reasoning model for advanced diagnostics' },
];

/* ─── State ─── */
let _engine: MLCEngine | null = null;
let _activeModel: string | null = null;
let _loading = false;
let _modulePromise: Promise<typeof import('@mlc-ai/web-llm')> | null = null;

async function loadWebLLMModule() {
  if (!_modulePromise) {
    _modulePromise = import('@mlc-ai/web-llm');
  }
  return _modulePromise;
}

/* ─── WebGPU Detection ─── */
export function isWebGPUSupported(): boolean {
  return typeof navigator !== 'undefined' && 'gpu' in navigator;
}

/* ─── Engine Lifecycle ─── */
export async function loadModel(
  modelId: string,
  onProgress?: ProgressCallback,
): Promise<void> {
  if (_activeModel === modelId && _engine) return; // Already loaded
  if (_loading) throw new Error('Another model is currently loading');

  _loading = true;

  try {
    // Unload previous model
    if (_engine) {
      await _engine.unload();
      _engine = null;
      _activeModel = null;
    }

    const { CreateMLCEngine } = await loadWebLLMModule();
    _engine = await CreateMLCEngine(modelId, {
      initProgressCallback: (report: InitProgressReport) => {
        onProgress?.({
          text: report.text,
          progress: report.progress,
        });
      },
    });

    _activeModel = modelId;
  } finally {
    _loading = false;
  }
}

export function isLoaded(): boolean {
  return _engine !== null && _activeModel !== null;
}

export function getActiveModel(): string | null {
  return _activeModel;
}

export function isModelLoading(): boolean {
  return _loading;
}

export async function unloadModel(): Promise<void> {
  if (_engine) {
    await _engine.unload();
    _engine = null;
    _activeModel = null;
  }
}

/* ─── Chat Streaming ─── */
export async function chatStream(
  messages: Array<{ role: string; content: string }>,
  systemPrompt: string,
  onChunk: ChunkCallback,
): Promise<void> {
  if (!_engine) throw new Error('No model loaded. Load a model first.');

  const fullMessages: Array<{ role: 'system' | 'user' | 'assistant'; content: string }> = [
    { role: 'system', content: systemPrompt },
    ...messages.map(m => ({
      role: m.role as 'user' | 'assistant',
      content: m.content,
    })),
  ];

  const stream = await _engine.chat.completions.create({
    messages: fullMessages,
    stream: true,
    max_tokens: 512,
    temperature: 0.7,
  });

  for await (const chunk of stream) {
    const content = chunk.choices[0]?.delta?.content;
    if (content) {
      onChunk(content);
    }
  }
}
