import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Plug, Plus, Trash2, Play, Shield, Globe, Terminal,
  Loader2, CheckCircle2, AlertCircle, X, Search
} from 'lucide-react';
import {
  fetchSmartApps, registerSmartApp, deleteSmartApp, launchSmartApp, type SmartApp
} from '@/lib/apiSmart';
import SmartAppSandbox from '@/components/smart/SmartAppSandbox';

export default function AppRegistry() {
  const [apps, setApps] = useState<SmartApp[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  // Registration Form Modal state
  const [showRegModal, setShowRegModal] = useState(false);
  const [appName, setAppName] = useState('');
  const [redirectUri, setRedirectUri] = useState('');
  const [launchUrl, setLaunchUrl] = useState('');
  const [scopes, setScopes] = useState('launch/patient patient/*.read');
  const [regLoading, setRegLoading] = useState(false);
  const [regError, setRegError] = useState<string | null>(null);

  // Launch Modal state
  const [launchingApp, setLaunchingApp] = useState<SmartApp | null>(null);
  const [patientId, setPatientId] = useState('');
  const [launchToken, setLaunchToken] = useState<string | null>(null);
  const [launchUrlWithToken, setLaunchUrlWithToken] = useState<string | null>(null);

  // Load registered apps
  const loadApps = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchSmartApps();
      setApps(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load SMART applications');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadApps();
  }, []);

  // Handle register submission
  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setRegLoading(true);
    setRegError(null);
    try {
      await registerSmartApp({
        app_name: appName,
        redirect_uri: redirectUri,
        launch_url: launchUrl,
        scopes,
      });
      // Reset form
      setAppName('');
      setRedirectUri('');
      setLaunchUrl('');
      setScopes('launch/patient patient/*.read');
      setShowRegModal(false);
      loadApps();
    } catch (err: any) {
      setRegError(err.message || 'Failed to register application');
    } finally {
      setRegLoading(false);
    }
  };

  // Handle delete
  const handleDelete = async (appId: number) => {
    if (!window.confirm('Are you sure you want to remove this application?')) return;
    try {
      await deleteSmartApp(appId);
      loadApps();
    } catch (err: any) {
      alert(err.message || 'Failed to delete application');
    }
  };

  // Handle launch
  const handleLaunch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!launchingApp || !patientId) return;
    try {
      const response = await launchSmartApp(launchingApp.id, parseInt(patientId));
      setLaunchToken(response.launch_token);
      setLaunchUrlWithToken(launchingApp.launch_url);
      setLaunchingApp(null); // Close launch modal
      setPatientId('');
    } catch (err: any) {
      alert(err.message || 'Failed to launch SMART application');
    }
  };

  const filteredApps = apps.filter(app =>
    app.app_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-slate-950 text-white p-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-10">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2.5 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400">
              <Plug className="w-6 h-6" />
            </div>
            <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
              SMART App Registry
            </h1>
          </div>
          <p className="text-slate-400 text-sm max-w-xl">
            Integrate and manage third-party clinical applications securely.
            Pluggable SMART on FHIR authorization and sandboxed EHR data isolation.
          </p>
        </div>

        <button
          onClick={() => setShowRegModal(true)}
          className="flex items-center justify-center gap-2 px-5 py-2.5 bg-sky-500 hover:bg-sky-600 active:bg-sky-700 text-white font-medium rounded-xl shadow-lg shadow-sky-500/25 transition-all hover:scale-[1.02]"
        >
          <Plus className="w-5 h-5" />
          <span>Register SMART App</span>
        </button>
      </div>

      {/* Search & Stats */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8 bg-slate-900/40 border border-slate-800/60 p-4 rounded-2xl backdrop-blur-md">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search registered apps..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-950/60 border border-slate-800 rounded-xl py-2 pl-10 pr-4 text-sm focus:outline-none focus:border-sky-500/50 transition-colors"
          />
        </div>
        <div className="flex items-center gap-6 text-sm text-slate-400">
          <div>
            Total Apps: <span className="font-semibold text-white">{apps.length}</span>
          </div>
          <div className="h-4 w-px bg-slate-800" />
          <div>
            Sandbox State: <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">Active</span>
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 gap-4">
          <Loader2 className="w-8 h-8 text-sky-400 animate-spin" />
          <p className="text-slate-400 text-sm">Loading application registry...</p>
        </div>
      ) : error ? (
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-6 rounded-2xl flex items-start gap-4">
          <AlertCircle className="w-6 h-6 flex-shrink-0" />
          <div>
            <h3 className="font-semibold mb-1">Error Loading Registry</h3>
            <p className="text-sm opacity-90">{error}</p>
          </div>
        </div>
      ) : filteredApps.length === 0 ? (
        <div className="text-center py-24 bg-slate-900/20 border border-dashed border-slate-800 rounded-3xl">
          <Plug className="w-12 h-12 text-slate-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium mb-1">No Applications Registered</h3>
          <p className="text-slate-400 text-sm max-w-sm mx-auto">
            {searchQuery ? 'No apps match your search terms.' : 'Register a new third-party SMART on FHIR application to get started.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <AnimatePresence mode="popLayout">
            {filteredApps.map((app) => (
              <motion.div
                key={app.id}
                layout
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="bg-slate-900/50 hover:bg-slate-900/85 border border-slate-800 hover:border-slate-700/80 rounded-2xl p-6 transition-all shadow-md flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-4 mb-4">
                    <h3 className="font-bold text-lg text-slate-100 line-clamp-1">{app.app_name}</h3>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-sky-500/10 text-sky-400 border border-sky-500/25">
                      OAuth2 Client
                    </span>
                  </div>

                  <div className="space-y-3.5 mb-6 text-sm">
                    <div>
                      <div className="text-xs text-slate-500 mb-0.5 font-mono">CLIENT ID</div>
                      <div className="font-mono text-slate-300 bg-slate-950/50 border border-slate-800/40 px-2.5 py-1 rounded-lg text-xs select-all">
                        {app.client_id}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-500 mb-0.5">LAUNCH ENDPOINT</div>
                      <div className="text-slate-300 font-mono text-xs truncate" title={app.launch_url}>
                        {app.launch_url}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-500 mb-0.5">SCOPES</div>
                      <div className="text-slate-300 font-mono text-xs flex flex-wrap gap-1.5">
                        {app.scopes.split(' ').map((s, idx) => (
                          <span key={idx} className="bg-slate-950 px-2 py-0.5 rounded border border-slate-800 text-[11px]">
                            {s}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between border-t border-slate-800/60 pt-4 mt-2">
                  <button
                    onClick={() => handleDelete(app.id)}
                    className="p-2 rounded-xl text-slate-400 hover:bg-red-500/10 hover:text-red-400 transition-all active:scale-95"
                    title="Delete Application"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>

                  <button
                    onClick={() => setLaunchingApp(app)}
                    className="flex items-center gap-1.5 px-4.5 py-2 bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-400 border border-emerald-500/30 rounded-xl font-medium transition-all active:scale-95"
                  >
                    <Play className="w-4 h-4 fill-emerald-400/20" />
                    <span>Launch</span>
                  </button>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}

      {/* SMART App registration Modal */}
      <AnimatePresence>
        {showRegModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full overflow-hidden shadow-2xl"
            >
              <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <Plug className="w-5 h-5 text-sky-400" />
                  <h3 className="font-bold text-lg">Register SMART App</h3>
                </div>
                <button
                  onClick={() => setShowRegModal(false)}
                  className="p-1 rounded-lg text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleRegister} className="p-6 space-y-4">
                {regError && (
                  <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-3 rounded-lg text-sm flex gap-2">
                    <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                    <span>{regError}</span>
                  </div>
                )}

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-400 uppercase">Application Name</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Cardiac Risk Analytics"
                    value={appName}
                    onChange={(e) => setAppName(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-500"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-400 uppercase">Launch URL</label>
                  <input
                    type="url"
                    required
                    placeholder="https://clientapp.com/launch"
                    value={launchUrl}
                    onChange={(e) => setLaunchUrl(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-500"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-400 uppercase">Redirect URI</label>
                  <input
                    type="url"
                    required
                    placeholder="https://clientapp.com/callback"
                    value={redirectUri}
                    onChange={(e) => setRedirectUri(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-500"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-400 uppercase">Scopes</label>
                  <input
                    type="text"
                    placeholder="launch/patient patient/*.read"
                    value={scopes}
                    onChange={(e) => setScopes(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-500 font-mono"
                  />
                </div>

                <div className="flex gap-3 justify-end pt-4">
                  <button
                    type="button"
                    onClick={() => setShowRegModal(false)}
                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 active:bg-slate-650 rounded-xl text-sm font-medium transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={regLoading}
                    className="flex items-center gap-1.5 px-5 py-2 bg-sky-500 hover:bg-sky-600 active:bg-sky-700 disabled:opacity-50 rounded-xl text-sm font-medium transition-colors"
                  >
                    {regLoading && <Loader2 className="w-4 h-4 animate-spin" />}
                    <span>Register</span>
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Launch app context config modal */}
      <AnimatePresence>
        {launchingApp && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full overflow-hidden shadow-2xl"
            >
              <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
                <h3 className="font-bold text-lg">App Launch Authorization</h3>
                <button
                  onClick={() => setLaunchingApp(null)}
                  className="p-1 rounded-lg text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleLaunch} className="p-6 space-y-4">
                <p className="text-slate-400 text-xs leading-relaxed">
                  Establish a secure patient context for <span className="text-white font-semibold">{launchingApp.app_name}</span>.
                  The app will be granted access to the specified patient record via scope-guarded FHIR tokens.
                </p>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-400 uppercase">Target Patient ID</label>
                  <input
                    type="number"
                    required
                    placeholder="Enter Patient ID (e.g. 1)"
                    value={patientId}
                    onChange={(e) => setPatientId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div className="flex gap-3 justify-end pt-4">
                  <button
                    type="button"
                    onClick={() => setLaunchingApp(null)}
                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-xl text-sm font-medium transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="flex items-center gap-1.5 px-5 py-2 bg-emerald-500 hover:bg-emerald-600 rounded-xl text-sm font-medium transition-colors"
                  >
                    <Play className="w-4 h-4 fill-white/10" />
                    <span>Generate Context & Launch</span>
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Render SMART App sandbox inside iframe if token is generated */}
      {launchToken && launchUrlWithToken && (
        <SmartAppSandbox
          launchUrl={launchUrlWithToken}
          launchToken={launchToken}
          onClose={() => {
            setLaunchToken(null);
            setLaunchUrlWithToken(null);
          }}
        />
      )}
    </div>
  );
}
