import { useState, useEffect } from "react";

export interface OfflineRequest {
  id: string;
  url: string;
  method: string;
  body?: string;
  headers?: Record<string, string>;
  timestamp: number;
}

const OFFLINE_QUEUE_KEY = "AI Healthcare System_offline_queue";

// Get all pending requests in localStorage queue
export function getOfflineQueue(): OfflineRequest[] {
  try {
    const raw = localStorage.getItem(OFFLINE_QUEUE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

// Save a pending request into queue
export function addToOfflineQueue(url: string, method: string, body?: any, headers?: any) {
  const queue = getOfflineQueue();
  const newRequest: OfflineRequest = {
    id: Math.random().toString(36).substring(2, 9),
    url,
    method,
    body: body ? JSON.stringify(body) : undefined,
    headers,
    timestamp: Date.now()
  };
  queue.push(newRequest);
  localStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(queue));
}

// Clear request from queue
export function removeFromOfflineQueue(id: string) {
  const queue = getOfflineQueue().filter((req) => req.id !== id);
  localStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(queue));
}

// Process and execute queued writes when back online
export async function syncOfflineQueue(onProgress?: (msg: string) => void): Promise<number> {
  const queue = getOfflineQueue();
  if (queue.length === 0) return 0;

  let successCount = 0;
  for (const req of queue) {
    try {
      if (onProgress) onProgress(`Syncing pending action: ${req.url}`);
      const response = await fetch(req.url, {
        method: req.method,
        headers: {
          "Content-Type": "application/json",
          ...(req.headers || {})
        },
        body: req.body
      });

      if (response.ok) {
        removeFromOfflineQueue(req.id);
        successCount++;
      }
    } catch (e) {
      console.warn("Failed to sync offline operation: ", req.url, e);
      // Stop syncing rest if connection dropped again
      break;
    }
  }

  return successCount;
}

// React hook to monitor network status and queue length
export function useNetworkStatus() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [queueCount, setQueueCount] = useState(0);

  useEffect(() => {
    const updateStatus = () => {
      setIsOnline(navigator.onLine);
      setQueueCount(getOfflineQueue().length);
    };

    window.addEventListener("online", updateStatus);
    window.addEventListener("offline", updateStatus);

    // Initial check
    setQueueCount(getOfflineQueue().length);

    // Periodically update queue count in case it changes
    const interval = setInterval(() => {
      setQueueCount(getOfflineQueue().length);
    }, 2000);

    return () => {
      window.removeEventListener("online", updateStatus);
      window.removeEventListener("offline", updateStatus);
      clearInterval(interval);
    };
  }, []);

  return { isOnline, queueCount };
}
