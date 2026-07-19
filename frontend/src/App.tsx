import React, { useState, useEffect } from 'react';
import { User as UserIcon, LogOut, FileDown, Plus, LayoutDashboard, ArrowLeftRight, Settings, Radio, ShieldAlert } from 'lucide-react';
import { apiFetch, apiPost, apiDelete, isTokenExpired, clearAuthState, registerOn401Handler, API_BASE_URL } from './lib/api';
import AuthScreen from './components/AuthScreen';
import MapPanel from './components/MapPanel';
import Dashboard from './components/Dashboard';
import PlanningAssistant from './components/PlanningAssistant';
import ScenarioCompare from './components/ScenarioCompare';
import AdminPanel from './components/AdminPanel';
import OfflineBanner from './components/OfflineBanner';
import RoleDashboard from './components/RoleDashboard';
import SystemHealthPanel from './components/SystemHealthPanel';
import { useCityStream } from './hooks/useCityStream';
import CommandCenter from './components/CommandCenter';
import { useLocationStore } from './store/locationStore';


interface Scenario {
  id: number;
  name: string;
  description: string;
  baseline_id: number | null;
  created_by: number;
  status: string;
  elements: any[];
}

export default function App() {
  const { data: streamData, connected: streamConnected, retryCount } = useCityStream();
  const { activeLocation, initActiveLocation } = useLocationStore();

  const [token, setToken] = useState<string>(localStorage.getItem('token') || '');

  useEffect(() => {
    if (token) {
      initActiveLocation(token);
    }
  }, [token, initActiveLocation]);
  const [role, setRole] = useState<string>(localStorage.getItem('role') || '');
  const [roleOverride, setRoleOverride] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'live_twin' | 'dashboard' | 'compare' | 'admin' | 'health'>('live_twin');
  const [sessionExpired, setSessionExpired] = useState(false);
  const [lastTickTimestamp, setLastTickTimestamp] = useState<string | undefined>();

  // Track last-known-good tick timestamp for offline banner
  useEffect(() => {
    if (streamData?.timestamp) setLastTickTimestamp(streamData.timestamp);
  }, [streamData?.timestamp]);

  const [scenarios, setScenarios] = useState<Scenario[]>([]);

  const [activeScenarioId, setActiveScenarioId] = useState<number | null>(null);
  const [elements, setElements] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>({});
  const [explanation, setExplanation] = useState<string>('');
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [forecast, setForecast] = useState<any>(null);

  const [selectedTool, setSelectedTool] = useState<string | null>(null);
  const [simulating, setSimulating] = useState(false);
  const [creatingScenario, setCreatingScenario] = useState(false);
  const [newScenName, setNewScenName] = useState('');
  const [newScenDesc, setNewScenDesc] = useState('');

  // Handle Authentication Success
  const handleAuthSuccess = (newToken: string, newRole: string) => {
    localStorage.setItem('token', newToken);
    localStorage.setItem('role', newRole);
    setToken(newToken);
    setRole(newRole);
    setSessionExpired(false);
  };

  // Handle Logout
  const handleLogout = () => {
    clearAuthState();
    setToken('');
    setRole('');
    setSessionExpired(false);
  };

  // Register global 401 handler — fires when any apiFetch call gets a 401
  useEffect(() => {
    registerOn401Handler(() => {
      setSessionExpired(true);
      setToken('');
      setRole('');
    });
  }, []);

  // Check token expiry on mount — clear stale tokens before any fetch
  useEffect(() => {
    if (token && isTokenExpired()) {
      console.warn('[Auth] Stored JWT is expired — clearing auth state.');
      clearAuthState();
      setToken('');
      setRole('');
      setSessionExpired(true);
    }
  }, []);

  // Fetch all Scenarios
  const fetchScenarios = async () => {
    if (!token) return;
    try {
      const data = await apiFetch<Scenario[]>('/api/scenarios', { token });
      setScenarios(data);
      // Auto-select baseline scenario if none selected yet
      if (data.length > 0 && activeScenarioId === null) {
        const baseline = data.find((s: any) => s.status === 'baseline');
        const selectedId = baseline ? baseline.id : data[0].id;
        setActiveScenarioId(selectedId);
      }
    } catch (err) {
      console.error('[App] fetchScenarios failed:', err);
    }
  };

  // Fetch active scenario elements and metrics
  const fetchScenarioDetails = async (id: number) => {
    if (!token) return;
    try {
      const data = await apiFetch<any>(`/api/scenarios/${id}`, { token });
      setElements(data.elements);
      // Run simulation trigger to load initial stats & forecast
      triggerSimulation(id);
    } catch (err) {
      console.error('[App] fetchScenarioDetails failed:', err);
    }
  };

  // Trigger Backend Simulation
  const triggerSimulation = async (id: number) => {
    if (!token) return;
    setSimulating(true);
    try {
      const data = await apiFetch<any>(`/api/simulations/run/${id}`, {
        method: 'POST',
        token
      });
      setMetrics(data.metrics);
      setExplanation(data.explanation);
      setRecommendations(data.recommendations);
      setForecast(data.forecast);
    } catch (err) {
      console.error('[App] triggerSimulation failed:', err);
    } finally {
      setSimulating(false);
    }
  };

  // Add Planning Element on the Map
  const handleAddElement = async (type: string, name: string, coords: [number, number]) => {
    if (!activeScenarioId || !token) return;
    try {
      await apiPost(
        `/api/scenarios/${activeScenarioId}/elements`,
        {
          type,
          name,
          location_geojson: JSON.stringify({ type: 'Point', coordinates: coords }),
          radius: type === 'hospital' ? 1500 : (type === 'metro' ? 800 : (type === 'green_space' ? 1000 : 0)),
          capacity: type === 'hospital' ? 500 : (type === 'metro' ? 15000 : 0),
          cost: type === 'hospital' ? 120000000 : (type === 'metro' ? 75000000 : (type === 'green_space' ? 8000000 : (type === 'flyover' ? 18000000 : (type === 'road_widening' ? 4000000 : 50000))))
        },
        { token }
      );
      // Refresh scenario details (triggers simulation automatically)
      fetchScenarioDetails(activeScenarioId);
    } catch (err: any) {
      console.error('[App] handleAddElement failed:', err);
      alert(err?.message ?? 'Unable to add element');
    }
  };

  // Remove Planning Element
  const handleRemoveElement = async (elementId: number) => {
    if (!activeScenarioId || !token) return;
    try {
      await apiDelete(
        `/api/scenarios/${activeScenarioId}/elements/${elementId}`,
        { token }
      );
      // Refresh
      fetchScenarioDetails(activeScenarioId);
    } catch (err) {
      console.error('[App] handleRemoveElement failed:', err);
    }
  };

  // Create Custom Scenario
  const handleCreateScenario = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newScenName.trim() || !token) return;

    try {
      const data = await apiPost<Scenario>(
        '/api/scenarios',
        {
          name: newScenName,
          description: newScenDesc,
          baseline_id: scenarios.find(s => s.status === 'baseline')?.id
        },
        { token }
      );
      setScenarios(prev => [...prev, data]);
      setActiveScenarioId(data.id);
      setNewScenName('');
      setNewScenDesc('');
      setCreatingScenario(false);
    } catch (err) {
      console.error('[App] handleCreateScenario failed:', err);
    }
  };

  // Download Report
  const handleDownloadReport = () => {
    if (!activeScenarioId) return;
    window.open(`${API_BASE_URL}/api/reports/download/${activeScenarioId}?token=${token}`, '_blank');
  };

  // Load scenarios on authentication
  useEffect(() => {
    if (token) {
      fetchScenarios();
    }
  }, [token]);

  // Load active scenario details when scenario selection changes
  useEffect(() => {
    if (activeScenarioId) {
      fetchScenarioDetails(activeScenarioId);
    }
  }, [activeScenarioId]);

  if (!token) {
    return <AuthScreen onAuthSuccess={handleAuthSuccess} sessionExpired={sessionExpired} />;
  }

  return (
    <div className="h-screen overflow-hidden flex flex-col bg-[#090d16] text-gray-100">
      {/* Offline / reconnection banner */}
      <OfflineBanner
        isConnected={streamConnected}
        lastSyncTimestamp={lastTickTimestamp}
        retryCount={retryCount}
      />
      {/* Top Navbar */}
      <header className="border-b border-brand-border bg-[#101625]/80 backdrop-blur-md sticky top-0 z-[2000] px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="text-xl">🏙️</div>
          <div>
            <h1 className="text-md font-bold tracking-tight text-white">MIRROR CITY</h1>
            <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest">
              AI DIGITAL TWIN PLATFORM
            </span>
          </div>
        </div>

        {/* Tab Selection */}
        <nav className="flex items-center gap-1.5 bg-[#0d1220] p-1 border border-brand-border rounded-xl">
          <button
            onClick={() => setActiveTab('live_twin')}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              activeTab === 'live_twin'
                ? 'bg-blue-600 text-white'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Radio size={13} className="animate-pulse text-brand-neonCyan" />
            Live 3D Twin
          </button>
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              activeTab === 'dashboard'
                ? 'bg-blue-600 text-white'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <LayoutDashboard size={13} />
            Telemetry Cockpit
          </button>
          <button
            onClick={() => setActiveTab('compare')}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              activeTab === 'compare'
                ? 'bg-blue-600 text-white'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <ArrowLeftRight size={13} />
            Multi-Scenario
          </button>
          {role === 'Administrator' && (
            <button
              onClick={() => setActiveTab('admin')}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                activeTab === 'admin'
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Settings size={13} />
              System Admin
            </button>
          )}
          {(role === 'Administrator' || roleOverride === 'Administrator') && (
            <button
              onClick={() => setActiveTab('health')}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                activeTab === 'health'
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <ShieldAlert size={13} />
              Health
            </button>
          )}
        </nav>

        {/* User Info & Actions */}
        <div className="flex items-center gap-4">
          <div className="hidden sm:flex flex-col items-end">
            <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
              <UserIcon size={12} className="text-brand-neonCyan" />
              {role}
            </span>
            <span className="text-[9px] text-slate-500">Connected</span>
          </div>
          <button
            onClick={handleLogout}
            className="p-2 bg-brand-panel hover:bg-brand-border border border-brand-border text-slate-400 hover:text-white rounded-lg transition-all"
            title="Log Out"
          >
            <LogOut size={14} />
          </button>
        </div>
      </header>

      {/* Role-based dashboard wrapper */}
      <RoleDashboard
        role={role}
        streamData={streamData}
        onRoleOverride={setRoleOverride}
        activeOverride={roleOverride}
      >

      {/* Live Twin full-screen mode */}
      {activeTab === 'live_twin' ? (
        <CommandCenter authToken={token} role={role} streamData={streamData} streamConnected={streamConnected} />
      ) : (
      <main className="flex-1 overflow-y-auto grid grid-cols-1 lg:grid-cols-12 gap-6 p-6" style={{ overscrollBehavior: 'contain' }}>
        {/* Left Interactive Workspace (Map / Comparison / Admin) */}
        <section className="lg:col-span-8 flex flex-col gap-6">
          {activeTab === 'dashboard' ? (
            <>
              {/* Map Panel Wrapper */}
              <div className="h-[460px] w-full">
                <MapPanel
                  elements={elements}
                  onAddElement={handleAddElement}
                  onRemoveElement={handleRemoveElement}
                  selectedTool={selectedTool}
                  setSelectedTool={setSelectedTool}
                  trafficData={forecast}
                  activeCity={streamData?.active_city || activeLocation}
                  graph={streamData?.city_graph}
                />
              </div>

              {/* Map Planning Tools & Action bar */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-[#101625]/60 border border-brand-border p-4 rounded-2xl glass-panel">
                {/* Deployment tools */}
                <div>
                  <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3">
                    Deploy Infrastructure Assets
                  </h3>
                  <div className="grid grid-cols-3 gap-2">
                    <button
                      onClick={() => setSelectedTool('metro')}
                      className={`py-2 px-3 border text-xs font-semibold rounded-xl text-center transition-all ${
                        selectedTool === 'metro' 
                          ? 'bg-blue-600 border-blue-500 text-white' 
                          : 'bg-brand-panel border-brand-border text-slate-400 hover:text-white'
                      }`}
                    >
                      🚇 Metro
                    </button>
                    <button
                      onClick={() => setSelectedTool('hospital')}
                      className={`py-2 px-3 border text-xs font-semibold rounded-xl text-center transition-all ${
                        selectedTool === 'hospital' 
                          ? 'bg-red-600 border-red-500 text-white' 
                          : 'bg-brand-panel border-brand-border text-slate-400 hover:text-white'
                      }`}
                    >
                      🏥 Hospital
                    </button>
                    <button
                      onClick={() => setSelectedTool('green_space')}
                      className={`py-2 px-3 border text-xs font-semibold rounded-xl text-center transition-all ${
                        selectedTool === 'green_space' 
                          ? 'bg-green-600 border-green-500 text-white' 
                          : 'bg-brand-panel border-brand-border text-slate-400 hover:text-white'
                      }`}
                    >
                      🌳 Park
                    </button>
                    <button
                      onClick={() => setSelectedTool('road_widening')}
                      className={`py-2 px-3 border text-xs font-semibold rounded-xl text-center transition-all ${
                        selectedTool === 'road_widening' 
                          ? 'bg-yellow-600 border-yellow-500 text-white' 
                          : 'bg-brand-panel border-brand-border text-slate-400 hover:text-white'
                      }`}
                    >
                      ↔️ Widen
                    </button>
                    <button
                      onClick={() => setSelectedTool('flyover')}
                      className={`py-2 px-3 border text-xs font-semibold rounded-xl text-center transition-all ${
                        selectedTool === 'flyover' 
                          ? 'bg-purple-600 border-purple-500 text-white' 
                          : 'bg-brand-panel border-brand-border text-slate-400 hover:text-white'
                      }`}
                    >
                      🌉 Flyover
                    </button>
                    <button
                      onClick={() => setSelectedTool('closure')}
                      className={`py-2 px-3 border text-xs font-semibold rounded-xl text-center transition-all ${
                        selectedTool === 'closure' 
                          ? 'bg-gray-600 border-gray-500 text-white' 
                          : 'bg-brand-panel border-brand-border text-slate-400 hover:text-white'
                      }`}
                    >
                      🚫 Close Road
                    </button>
                  </div>
                </div>

                {/* Scenario manager */}
                <div className="flex flex-col justify-between">
                  <div>
                    <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
                      Active Planning Scenario
                    </h3>
                    <div className="flex gap-2">
                      <select
                        value={activeScenarioId || ''}
                        onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setActiveScenarioId(Number(e.target.value))}
                        className="bg-[#0d1220] border border-brand-border rounded-xl text-xs px-3 py-2 text-slate-300 focus:outline-none focus:border-brand-neonCyan cursor-pointer flex-1"
                      >
                        {scenarios.map((s) => (
                          <option key={s.id} value={s.id}>
                            {s.name} ({s.status})
                          </option>
                        ))}
                      </select>
                      <button
                        onClick={() => setCreatingScenario(!creatingScenario)}
                        className="p-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl transition-all"
                        title="Create Scenario"
                      >
                        <Plus size={16} />
                      </button>
                    </div>
                  </div>

                  {/* PDF report trigger */}
                  <button
                    onClick={handleDownloadReport}
                    disabled={!activeScenarioId}
                    className="w-full flex items-center justify-center gap-2 py-2 bg-brand-panel hover:bg-brand-border border border-brand-border text-slate-300 hover:text-white font-semibold text-xs rounded-xl shadow transition-all mt-3"
                  >
                    <FileDown size={14} className="text-brand-neonCyan" />
                    Download Executive Report (PDF)
                  </button>
                </div>
              </div>

              {/* Collapsible Scenario Creator Form */}
              {creatingScenario && (
                <form onSubmit={handleCreateScenario} className="bg-[#101625]/60 border border-brand-border p-4 rounded-2xl glass-panel space-y-3">
                  <h4 className="text-xs font-bold text-white uppercase">New Planning Project</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <input
                      type="text"
                      required
                      placeholder="Scenario Name (e.g. Metro Line B Proposal)"
                      value={newScenName}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewScenName(e.target.value)}
                      className="bg-[#0d1220] border border-brand-border rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-neonCyan"
                    />
                    <input
                      type="text"
                      placeholder="Brief description of structural modifications..."
                      value={newScenDesc}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewScenDesc(e.target.value)}
                      className="bg-[#0d1220] border border-brand-border rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-neonCyan"
                    />
                  </div>
                  <div className="flex justify-end gap-2 text-xs font-bold pt-1">
                    <button
                      type="button"
                      onClick={() => setCreatingScenario(false)}
                      className="px-3 py-1.5 border border-brand-border rounded-lg text-slate-400 hover:text-white"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
                    >
                      Create Project
                    </button>
                  </div>
                </form>
              )}
            </>
          ) : activeTab === 'compare' ? (
            <ScenarioCompare scenarios={scenarios} authToken={token} />
          ) : activeTab === 'health' ? (
            <SystemHealthPanel authToken={token} />
          ) : (
            <AdminPanel authToken={token} />
          )}
        </section>

        {/* Right Dashboard Telemetry Column */}
        <section className="lg:col-span-4 flex flex-col gap-6">
          {/* AI Planning Chat Assistant */}
          <div className="h-[280px]">
            <PlanningAssistant
              scenarioId={activeScenarioId}
              authToken={token}
              onDeploySuggestedTool={(toolType) => setSelectedTool(toolType)}
            />
          </div>

          {/* Real-time KPI charts and explainable AI */}
          {activeTab === 'dashboard' && (
            <div className="flex-1">
              <Dashboard
                metrics={metrics}
                explanation={explanation}
                recommendations={recommendations}
                forecast={forecast}
                onRunSimulation={() => activeScenarioId && triggerSimulation(activeScenarioId)}
                simulating={simulating}
              />
            </div>
          )}
        </section>
      </main>
      )}

      </RoleDashboard>
    </div>
  );
}
