import { useState } from "react";
import { toast } from "@/lib/toast";

export interface WebLLMProgress {
  text: string;
  progress: number;
}

export function useWebLLMEngine() {
  const [showModelManager, setShowModelManager] = useState(false);
  const [selectedModel, setSelectedModel] = useState("meta/llama-3.1-8b-instruct");
  const [currentWebLLMModel, setCurrentWebLLMModel] = useState("Llama-3.2-1B-Instruct-q4f32_1-MLC");
  const [webllmActive, setWebllmActive] = useState(false);
  const [webllmLoading, setWebllmLoading] = useState<string | null>(null);
  const [webllmProgress, setWebllmProgress] = useState<WebLLMProgress | null>(null);

  const handleWebLLMLoad = async (modelId: string) => {
    setWebllmLoading(modelId);
    setWebllmProgress({ text: "Loading model files into WebGPU...", progress: 0 });
    try {
      const webllm = await import("@/lib/webllm");
      await webllm.loadModel(modelId, (report) => {
        setWebllmProgress({ text: report.text, progress: report.progress });
      });
      setCurrentWebLLMModel(modelId);
      setWebllmActive(true);
      setShowModelManager(false);
      toast.success(`Local model ${modelId} ready in browser memory!`);
    } catch (err: any) {
      toast.error(`WebLLM load failed: ${err.message || err}`);
    } finally {
      setWebllmLoading(null);
      setWebllmProgress(null);
    }
  };

  const handleWebLLMUnload = async () => {
    try {
      const webllm = await import("@/lib/webllm");
      await webllm.unloadModel();
      setWebllmActive(false);
      toast.info("Local WebGPU memory released.");
    } catch (err: any) {
      toast.error(`Unload failed: ${err.message || err}`);
    }
  };

  return {
    showModelManager,
    setShowModelManager,
    selectedModel,
    setSelectedModel,
    currentWebLLMModel,
    setCurrentWebLLMModel,
    webllmActive,
    setWebllmActive,
    webllmLoading,
    webllmProgress,
    handleWebLLMLoad,
    handleWebLLMUnload,
  };
}
