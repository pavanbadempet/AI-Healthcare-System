import React from 'react';
import { FileText, Loader2, BrainCircuit, AlertCircle } from 'lucide-react';

export interface SmartLabAnalyzerTabProps {
  selectedFile: File | null;
  setSelectedFile: (file: File | null) => void;
  uploadingReport: boolean;
  analyzerResult: any;
  analyzerError: string;
  onUploadReport: (e: React.FormEvent) => void;
}

export const SmartLabAnalyzerTab: React.FC<SmartLabAnalyzerTabProps> = ({
  selectedFile,
  setSelectedFile,
  uploadingReport,
  analyzerResult,
  analyzerError,
  onUploadReport
}) => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 animate-fadeIn">
      {/* Left Column: Report File Upload and Status */}
      <div className="lg:col-span-5 bg-slate-900/20 border border-slate-900 rounded-3xl p-6 flex flex-col space-y-4">
        <div className="flex items-center gap-2 border-b border-slate-900 pb-4">
          <FileText className="w-5 h-5 text-indigo-400" />
          <h2 className="font-bold text-slate-200 uppercase tracking-wide">Smart Lab Report Analyzer</h2>
        </div>

        <p className="text-xs text-slate-400 leading-relaxed uppercase">
          Upload a digital image (JPEG/PNG) of pathology results or a clinical referral letter. The Google Gemini Vision model will read the image text and parse key parameters into structured entries.
        </p>

        <form onSubmit={onUploadReport} className="space-y-4 pt-2">
          <div className="flex flex-col items-center justify-center p-6 border-2 border-dashed border-slate-800 rounded-2xl bg-slate-950/40 hover:bg-slate-950/60 transition-colors cursor-pointer relative group">
            <input
              type="file"
              accept="image/jpeg,image/png,image/jpg"
              onChange={(e) => {
                if (e.target.files && e.target.files.length > 0) {
                  setSelectedFile(e.target.files[0]);
                }
              }}
              className="absolute inset-0 opacity-0 cursor-pointer"
              required
            />
            <FileText className="w-8 h-8 text-slate-650 mb-2 group-hover:text-indigo-400 transition-colors" />
            <span className="text-xs text-slate-400 group-hover:text-slate-200 transition-colors uppercase font-mono font-bold">
              {selectedFile ? selectedFile.name.toUpperCase() : 'Select Report Image'}
            </span>
            <span className="text-[10px] text-slate-500 font-mono mt-1">JPEG, PNG (Max 5MB)</span>
          </div>

          <button
            type="submit"
            disabled={uploadingReport || !selectedFile}
            className="w-full btn btn-primary py-2.5 cursor-pointer flex items-center justify-center gap-1.5 text-xs uppercase"
          >
            {uploadingReport ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}
            {uploadingReport ? 'Analyzing...' : 'Analyze Lab Report'}
          </button>
        </form>

        {analyzerError && (
          <div
            className="p-3 text-[10px] font-mono uppercase bg-[rgba(255,74,74,0.08)] border border-[var(--danger-border)] rounded text-[var(--danger)] flex items-start gap-2"
            role="alert"
          >
            {analyzerError}
          </div>
        )}
      </div>

      {/* Right Column: Parsed Results */}
      <div className="lg:col-span-7 bg-slate-900/20 border border-slate-900 rounded-3xl p-6 flex flex-col space-y-4">
        <div className="flex items-center gap-2 border-b border-slate-900 pb-4">
          <BrainCircuit className="w-5 h-5 text-indigo-400" />
          <h2 className="font-bold text-slate-200 uppercase tracking-wide">Vision Model Extraction</h2>
        </div>

        {uploadingReport ? (
          <div className="flex-1 flex flex-col items-center justify-center text-slate-500 py-12 space-y-2">
            <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
            <span className="text-xs uppercase font-mono tracking-wider animate-pulse">Running Gemini Vision OCR...</span>
          </div>
        ) : analyzerResult ? (
          <div className="space-y-6">
            <div className="space-y-2">
              <span className="text-xs uppercase font-bold text-slate-500 font-mono">Summary & Analysis</span>
              <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-900 text-xs text-slate-300 leading-relaxed">
                {analyzerResult.summary}
              </div>
            </div>

            {analyzerResult.extracted_data && Object.keys(analyzerResult.extracted_data).length > 0 ? (
              <div className="space-y-2">
                <span className="text-xs uppercase font-bold text-slate-500 font-mono">Extracted Lab Metrics</span>
                <div className="border border-slate-900 rounded-2xl overflow-hidden">
                  <table className="w-full text-xs font-mono uppercase">
                    <thead>
                      <tr className="bg-slate-950/60 border-b border-slate-900 text-slate-400 text-left">
                        <th className="p-3">Metric Name</th>
                        <th className="p-3 text-right">Reported Value</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-900 text-slate-300">
                      {Object.entries(analyzerResult.extracted_data).map(([key, val]: any) => (
                        <tr key={key} className="hover:bg-slate-950/20 transition-all">
                          <td className="p-3 text-indigo-300 font-semibold">{key.replace(/_/g, ' ')}</td>
                          <td className="p-3 text-right font-bold">{val}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              <div className="py-6 text-center text-slate-500 text-xs font-mono uppercase border border-dashed border-slate-900 rounded-2xl">
                No clinical metrics were extracted.
              </div>
            )}

            {analyzerResult.disclaimer && (
              <div className="p-3.5 bg-amber-500/5 border border-amber-500/15 rounded-2xl flex items-start gap-2.5 mt-4">
                <AlertCircle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
                <span className="text-[10px] leading-relaxed text-amber-500/80 font-medium font-sans">
                  {analyzerResult.disclaimer}
                </span>
              </div>
            )}
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-slate-500 py-12 border border-dashed border-slate-900 rounded-2xl">
            <FileText className="w-10 h-10 text-slate-700 mb-2" />
            <span className="text-xs uppercase font-mono text-slate-500">Upload a report file to view extracted parameters</span>
          </div>
        )}
      </div>
    </div>
  );
};
