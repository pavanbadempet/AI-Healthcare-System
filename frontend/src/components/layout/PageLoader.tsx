import React from 'react';

export default function PageLoader() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] w-full p-6 space-y-6">
      {/* Premium custom spinner with outer glow and heartbeat-like pulse */}
      <div className="relative flex items-center justify-center w-20 h-20">
        <div className="absolute inset-0 border-4 border-emerald-500/10 rounded-full"></div>
        <div className="absolute inset-0 border-4 border-transparent border-t-emerald-500 border-l-emerald-400 rounded-full animate-spin"></div>
        <div className="absolute w-8 h-8 bg-emerald-500/10 rounded-full animate-ping"></div>
        <div className="absolute w-4 h-4 bg-emerald-500 rounded-full shadow-[0_0_12px_rgba(16,185,129,0.5)]"></div>
      </div>
      
      {/* Skeleton Text */}
      <div className="flex flex-col items-center space-y-2 w-full max-w-xs">
        <div className="h-4 w-32 bg-gray-200 dark:bg-gray-800 rounded-full animate-pulse"></div>
        <div className="h-3 w-48 bg-gray-100 dark:bg-gray-900 rounded-full animate-pulse delay-75"></div>
      </div>
    </div>
  );
}
