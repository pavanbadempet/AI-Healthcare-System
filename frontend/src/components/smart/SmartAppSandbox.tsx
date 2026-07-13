import { useEffect, useState } from 'react';
import { X, Shield } from 'lucide-react';

interface SmartAppSandboxProps {
  launchUrl: string;
  launchToken: string;
  onClose: () => void;
}

export default function SmartAppSandbox({ launchUrl, launchToken, onClose }: SmartAppSandboxProps) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    // Trigger fade-in after mount
    const raf = requestAnimationFrame(() => setVisible(true));
    return () => cancelAnimationFrame(raf);
  }, []);

  const handleClose = () => {
    setVisible(false);
    setTimeout(onClose, 300);
  };

  const iframeSrc = `${launchUrl}?launch=${encodeURIComponent(launchToken)}`;

  return (
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center"
      style={{
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        opacity: visible ? 1 : 0,
        transition: 'opacity 300ms ease-in-out',
      }}
    >
      {/* Backdrop click to close */}
      <div className="absolute inset-0" onClick={handleClose} />

      {/* Sandbox card */}
      <div
        className="relative z-10 w-[95vw] h-[90vh] max-w-[1400px] rounded-2xl overflow-hidden"
        style={{
          background: 'linear-gradient(145deg, rgba(15,23,42,0.95), rgba(30,41,59,0.9))',
          border: '1px solid rgba(148,163,184,0.15)',
          backdropFilter: 'blur(24px)',
          boxShadow: '0 25px 60px rgba(0,0,0,0.6), 0 0 40px rgba(56,189,248,0.08)',
          transform: visible ? 'scale(1) translateY(0)' : 'scale(0.95) translateY(20px)',
          transition: 'transform 300ms ease-out',
        }}
      >
        {/* Header bar */}
        <div
          className="flex items-center justify-between px-6 py-3"
          style={{
            background: 'linear-gradient(90deg, rgba(56,189,248,0.1), rgba(168,85,247,0.1))',
            borderBottom: '1px solid rgba(148,163,184,0.1)',
          }}
        >
          <div className="flex items-center gap-3">
            <Shield className="w-4 h-4 text-emerald-400" />
            <span className="text-xs font-mono tracking-widest text-slate-400 uppercase">
              Sandboxed SMART App
            </span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              SECURE
            </span>
          </div>
          <button
            onClick={handleClose}
            className="p-1.5 rounded-lg transition-colors hover:bg-white/10 text-slate-400 hover:text-white"
            aria-label="Close SMART app"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Iframe container */}
        <iframe
          src={iframeSrc}
          sandbox="allow-scripts allow-forms allow-same-origin"
          title="SMART on FHIR Application"
          className="w-full border-0"
          style={{ height: 'calc(100% - 52px)', background: '#0f172a' }}
        />
      </div>
    </div>
  );
}
