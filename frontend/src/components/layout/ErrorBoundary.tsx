import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log sanitized error information to console
    console.error('ErrorBoundary caught an unhandled error:', error, errorInfo);
  }

  private handleReload = () => {
    window.location.reload();
  };

  private handleGoHome = () => {
    window.location.href = '/dashboard';
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 dark:bg-gray-950 px-4 py-12 text-gray-900 dark:text-gray-100">
          <div className="w-full max-w-md p-8 bg-white dark:bg-gray-900 border border-red-200/50 dark:border-red-900/50 rounded-2xl shadow-xl space-y-6">
            <div className="flex items-center justify-center w-16 h-16 mx-auto bg-red-100 dark:bg-red-950/50 rounded-full">
              <svg
                className="w-8 h-8 text-red-600 dark:text-red-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </div>

            <div className="text-center space-y-2">
              <h2 className="text-2xl font-bold tracking-tight">Something went wrong</h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                An unexpected error occurred while rendering this page.
              </p>
            </div>

            {/* Error Message Box */}
            <div className="p-4 bg-gray-50 dark:bg-gray-950 border border-gray-100 dark:border-gray-800 rounded-xl overflow-hidden">
              <p className="text-xs font-mono text-gray-600 dark:text-gray-400 break-all select-all">
                Error: {this.state.error?.message || 'Unknown application error'}
              </p>
            </div>

            {/* Actions */}
            <div className="flex flex-col sm:flex-row gap-3 pt-2">
              <button
                onClick={this.handleReload}
                className="flex-1 px-4 py-2 text-sm font-medium text-white bg-emerald-600 hover:bg-emerald-500 active:bg-emerald-700 dark:bg-emerald-500 dark:hover:bg-emerald-400 dark:active:bg-emerald-600 rounded-xl transition shadow-md hover:shadow-emerald-500/15"
              >
                Reload Page
              </button>
              <button
                onClick={this.handleGoHome}
                className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 bg-gray-100 hover:bg-gray-200 active:bg-gray-300 dark:text-gray-300 dark:hover:text-gray-100 dark:bg-gray-800 dark:hover:bg-gray-700 dark:active:bg-gray-600 rounded-xl transition"
              >
                Go to Dashboard
              </button>
            </div>

            {/* Medical Disclaimer */}
            <div className="text-center border-t border-gray-100 dark:border-gray-800 pt-6">
              <p className="text-[11px] leading-relaxed text-gray-400 dark:text-gray-500 italic">
                Disclaimer: The AI Healthcare System provides clinical decision support tools for reference only. 
                It is not a substitute for professional medical judgment, diagnosis, or treatment. 
                If you are experiencing a medical emergency, please contact local emergency services immediately.
              </p>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
