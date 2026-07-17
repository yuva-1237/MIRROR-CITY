import { useState } from 'react';
import { apiFetch, apiPost } from '../lib/api';
import LiveMetricsGauges from './LiveMetricsGauges';
import AgentReasoningPanel from './AgentReasoningPanel';
import LiveEventFeed from './LiveEventFeed';
import PredictionTimeline from './PredictionTimeline';
import ExplainabilityPanel from './ExplainabilityPanel';
import IncidentReporter from './IncidentReporter';
import MapPanel from './MapPanel'; // High-fidelity interactive Leaflet Map
import LiveMap3D from './LiveMap3D'; // 3D deck.gl basemap
import { Radio, AlertCircle, RefreshCw, Shield, Clock, Search, Globe } from 'lucide-react';

import { useEffect } from 'react';

interface CommandCenterProps {
  authToken: string;
  role: string;
  streamData: any;
  streamConnected: boolean;
}

export default function CommandCenter({ authToken, role, streamData: data, streamConnected: connected }: CommandCenterProps) {
  const [selectedCoords, setSelectedCoords] = useState<[number, number] | null>(null);
  const [mapMode, setMapMode] = useState<'3d' | '2d'>('3d');
  const [activeCityOverride, setActiveCityOverride] = useState<any>(null);

  // Universal Location Search states
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  const [loadingCity, setLoadingCity] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);

  // Clear instant override once WebSocket ticks the updated city
  useEffect(() => {
    if (data?.active_city && activeCityOverride && data.active_city.name === activeCityOverride.name) {
      setActiveCityOverride(null);
    }
  }, [data?.active_city, activeCityOverride]);

  const activeCity = activeCityOverride || data?.active_city;

  // When the user selects a new city, the WebSocket's city_graph is still for the
  // OLD city (takes ~3 s to update). Detect this and pass null graph so MapPanel
  // immediately regenerates a synthetic grid at the new city's coordinates.
  const isGraphStale = Boolean(
    activeCityOverride &&
    data?.active_city?.name &&
    activeCityOverride.name !== data?.active_city?.name
  );
  const resolvedGraph = isGraphStale ? null : data?.city_graph;

  // Calculate overall alerts
  const alertCount = data ? Object.values(data.agent_outputs as Record<string, any>).filter((a: any) => a.alert_level !== 'normal').length : 0;

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setSearching(true);
    setShowDropdown(true);
    try {
      const resData = await apiFetch<any[]>(`/api/geospatial/search?query=${encodeURIComponent(searchQuery)}`, {
        token: authToken
      });
      setSearchResults(resData);
    } catch (err) {
      console.error('[CommandCenter] Search failed:', err);
    } finally {
      setSearching(false);
    }
  };

  const handleSelectCity = async (city: any) => {
    setLoadingCity(true);
    setShowDropdown(false);
    // ⚡ Instant map fly-to — don't wait for the next WebSocket tick (up to 3s)
    setActiveCityOverride(city);
    try {
      const resData = await apiPost<any>(
        '/api/geospatial/load',
        city,
        { token: authToken }
      );
      console.log('[CommandCenter] City loaded:', resData);
      setSearchQuery('');
    } catch (err) {
      console.error('[CommandCenter] Select city failed:', err);
      // Revert override on failure so the map stays on the last known city
      setActiveCityOverride(null);
    } finally {
      setLoadingCity(false);
    }
  };

  return (
    <div className="h-full overflow-y-auto bg-brand-dark text-slate-100 flex flex-col p-4 space-y-4 font-sans select-none" style={{ overscrollBehavior: 'contain' }}>
      
      {/* Header telemetry status bar */}
      <header className="glass-panel p-4 rounded-xl border border-brand-border/60 bg-brand-panel/60 flex flex-col md:flex-row justify-between items-center gap-3">
        <div className="flex items-center gap-3">
          <div className="bg-brand-accent/20 p-2 rounded-lg border border-brand-accent/40 flex items-center justify-center">
            <Radio className="h-5 w-5 text-brand-neonCyan animate-pulse" />
          </div>
          <div>
            <h1 className="text-base font-extrabold tracking-tight text-white uppercase flex items-center gap-2">
              MIRROR CITY <span className="text-xs bg-brand-accent/20 text-brand-neonCyan px-1.5 py-0.5 rounded font-mono font-normal">v2.0 Twin</span>
            </h1>
            <p className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold font-mono">
              Live Operations Control Command Center
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4 flex-wrap text-xs">
          {/* Connection Status indicator */}
          <div className="flex items-center gap-2 bg-slate-900/60 px-3 py-1.5 rounded-lg border border-brand-border/40 font-mono">
            <span className={`h-2.5 w-2.5 rounded-full ${connected ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`} />
            <span className="text-[10px] text-slate-300">
              {connected ? 'CONNECTED TO CITY BUS' : 'DISCONNECTED / RETRYING'}
            </span>
          </div>

          {/* Active Alerts */}
          <div className="flex items-center gap-2 bg-slate-900/60 px-3 py-1.5 rounded-lg border border-brand-border/40 font-mono">
            <AlertCircle className={`h-4 w-4 ${alertCount > 0 ? 'text-brand-neonOrange animate-bounce' : 'text-slate-500'}`} />
            <span className="text-[10px] text-slate-300">
              ALERTS: <span className="font-bold text-brand-neonOrange">{alertCount}</span>
            </span>
          </div>

          {/* User role profile badge */}
          <div className="flex items-center gap-2 bg-slate-900/60 px-3 py-1.5 rounded-lg border border-brand-border/40 font-mono">
            <Shield className="h-4 w-4 text-brand-neonPurple" />
            <span className="text-[10px] text-slate-300 uppercase">
              Security clearance: <span className="font-bold text-brand-neonPurple">{role}</span>
            </span>
          </div>

          {/* Live system clock tick */}
          <div className="flex items-center gap-2 bg-slate-900/60 px-3 py-1.5 rounded-lg border border-brand-border/40 font-mono">
            <Clock className="h-4 w-4 text-brand-neonCyan" />
            <span className="text-[10px] text-slate-300">
              TICK: <span className="font-bold text-brand-neonCyan">{data?.tick || 0}</span>
            </span>
          </div>
        </div>
      </header>

      {/* Universal Location Intelligence Bar */}
      <section className="glass-panel p-4 rounded-xl border border-brand-border/60 bg-brand-panel/40 grid grid-cols-1 lg:grid-cols-12 gap-4 items-center">
        {/* Search Input */}
        <div className="lg:col-span-4 relative">
          <form onSubmit={handleSearch} className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
              <input
                type="text"
                placeholder="Search global town, village, city..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-slate-900/60 border border-brand-border rounded-lg pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-brand-neonCyan focus:border-brand-neonCyan"
              />
            </div>
            <button
              type="submit"
              disabled={searching}
              className="bg-brand-accent hover:bg-brand-accent/80 text-white font-bold text-xs px-4 py-2 rounded-lg transition-all disabled:opacity-50 flex items-center gap-1 shrink-0"
            >
              {searching ? 'RESOLVE' : 'RESOLVE'}
            </button>
          </form>

          {/* Autocomplete / Dropdown */}
          {showDropdown && searchResults.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-2 z-[2000] bg-slate-900 border border-brand-border rounded-xl shadow-2xl p-2 max-h-[250px] overflow-y-auto">
              <div className="flex justify-between items-center px-2 pb-2 border-b border-brand-border/40 mb-1">
                <span className="text-[9px] font-bold text-slate-500 uppercase tracking-wide">Resolved Places</span>
                <button onClick={() => setShowDropdown(false)} className="text-[9px] text-slate-400 hover:text-white font-mono">[close]</button>
              </div>
              {searchResults.map((city, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSelectCity(city)}
                  className="w-full text-left p-2 hover:bg-brand-accent/10 rounded-lg border border-transparent hover:border-brand-accent/20 transition flex justify-between items-center group font-sans"
                >
                  <div className="flex-1 pr-2">
                    <h5 className="text-xs font-bold text-slate-200 group-hover:text-brand-neonCyan">{city.name}</h5>
                    <p className="text-[9px] text-slate-400 mt-0.5">{city.hierarchy.join(' > ')}</p>
                  </div>
                  <span className="text-[9px] font-mono text-slate-500 uppercase bg-slate-950 px-2 py-0.5 rounded border border-brand-border/40 shrink-0">
                    {city.location_type}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Resolved Location Metadata */}
        <div className="lg:col-span-5 flex flex-wrap gap-x-4 gap-y-2 items-center text-xs">
          {loadingCity ? (
            <div className="text-slate-400 text-xs animate-pulse flex items-center gap-2">
              <RefreshCw className="h-4 w-4 animate-spin text-brand-neonCyan" />
              Initializing dynamic digital twin...
            </div>
          ) : data?.active_city ? (
            <>
              <div className="flex items-center gap-1.5">
                <Globe className="h-4 w-4 text-brand-neonCyan" />
                <div>
                  <span className="text-[9px] text-slate-500 block uppercase font-mono font-bold leading-none">Hierarchy</span>
                  <span className="text-xs text-slate-200 font-bold">{data.active_city.hierarchy.join(' > ')}</span>
                </div>
              </div>

              <div className="flex gap-4">
                <div>
                  <span className="text-[10px] text-slate-500 block uppercase font-mono font-bold leading-none">Type</span>
                  <span className="text-xs text-brand-neonPurple font-bold uppercase">{data.active_city.location_type}</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 block uppercase font-mono font-bold leading-none">Elevation</span>
                  <span className="text-xs text-slate-200 font-mono font-bold">{data.active_city.elevation} m</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 block uppercase font-mono font-bold leading-none">Population</span>
                  <span className="text-xs text-slate-200 font-mono font-bold">
                    {data.active_city.population >= 1000000 
                      ? `${(data.active_city.population / 1000000).toFixed(1)}M` 
                      : data.active_city.population.toLocaleString()}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 block uppercase font-mono font-bold leading-none">Area</span>
                  <span className="text-xs text-slate-200 font-mono font-bold">{data.active_city.area_sq_km} km²</span>
                </div>
              </div>
            </>
          ) : (
            <span className="text-slate-500 italic text-[11px]">No active dynamic city loaded. Utilizing baseline.</span>
          )}
        </div>

        {/* Dataset Status Widget */}
        <div className="lg:col-span-3 flex justify-end gap-2">
          {data?.active_city?.datasets && (
            <div className="flex gap-1.5">
              {Object.entries(data.active_city.datasets).map(([key, dataset]: [string, any]) => {
                let badgeColor = "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
                if (dataset.status === "estimated") {
                  badgeColor = "bg-amber-500/10 text-amber-400 border-brand-neonOrange/20";
                } else if (dataset.status === "disabled") {
                  badgeColor = "bg-red-500/10 text-red-400 border-red-500/20";
                }
                return (
                  <div
                    key={key}
                    title={`${key.replace('_', ' ').toUpperCase()}: ${dataset.source}`}
                    className={`px-2 py-1 text-[9px] uppercase font-mono font-bold rounded border cursor-help ${badgeColor}`}
                  >
                    {key.split('_')[0]}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </section>

      {/* Main Real-time telemetry widgets */}
      {data ? (
        <div className="space-y-4 flex-1 flex flex-col justify-between">
          {/* Layer 5.1: Top Row KPI meters */}
          <LiveMetricsGauges telemetry={data.telemetry} dataQuality={data.data_quality} />

          {/* Layer 5.2: Middle Row - 3D Map Visualizer & Logs Panel */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
            
            {/* GIS City Map Engine */}
            <div className="lg:col-span-8 flex flex-col h-[500px]">
              <div className="flex justify-between items-center bg-[#101625]/60 border border-brand-border px-4 py-2 rounded-t-xl border-b-0 glass-panel">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-300 font-mono">GIS Spatial Twin Map</span>
                <div className="flex gap-1.5">
                  <button
                    onClick={() => setMapMode('3d')}
                    className={`px-3 py-1 text-[10px] uppercase font-bold rounded font-mono border transition ${
                      mapMode === '3d' ? 'bg-brand-accent/20 border-brand-accent text-white' : 'bg-slate-900/40 border-brand-border text-slate-400 hover:text-white'
                    }`}
                  >
                    3D Telemetry (deck.gl)
                  </button>
                  <button
                    onClick={() => setMapMode('2d')}
                    className={`px-3 py-1 text-[10px] uppercase font-bold rounded font-mono border transition ${
                      mapMode === '2d' ? 'bg-brand-accent/20 border-brand-accent text-white' : 'bg-slate-900/40 border-brand-border text-slate-400 hover:text-white'
                    }`}
                  >
                    2D Map View (Leaflet)
                  </button>
                </div>
              </div>

              <div className="flex-1 rounded-b-xl overflow-hidden border border-brand-border/80 shadow-2xl relative min-h-[440px]">
                {mapMode === '3d' ? (
                  <LiveMap3D
                    telemetry={data.telemetry}
                    activeCity={activeCity}
                    buildings={data.buildings}
                    graph={resolvedGraph}
                    onSelectCoordinates={(lat, lng) => setSelectedCoords([lat, lng])}
                  />
                ) : (
                  <MapPanel
                    scenarioId={1}
                    elements={data.active_elements}
                    activeCity={activeCity}
                    graph={resolvedGraph}
                    onSelectCoordinates={(lat, lng) => setSelectedCoords([lat, lng])}
                    authToken={authToken}
                  />
                )}
                
                {/* Float disaster warning if active */}
                {data.telemetry.disaster?.active && (
                  <div className="absolute top-4 left-4 z-[999] bg-red-950/90 border border-red-500 rounded-lg p-3 max-w-sm animate-pulse shadow-[0_0_15px_rgba(239,68,68,0.3)]">
                    <h4 className="text-red-400 font-extrabold text-xs uppercase tracking-wide flex items-center gap-1.5">
                      🚨 ACTIVE DISASTER: {data.telemetry.disaster.disaster_type}
                    </h4>
                    <p className="text-[10px] text-red-200 mt-1">
                      Severity: {((data.telemetry.disaster?.severity ?? 0) * 100).toFixed(0)}% | Affected Population: {data.telemetry.disaster?.affected_population ?? 'Unknown'}
                    </p>
                    <p className="text-[10px] text-red-300 mt-0.5">
                      Evacuation protocols active. Est. Recovery: {data.telemetry.disaster.estimated_recovery_time_hrs} hrs.
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* scrolling events and citizen reporting panel */}
            <div className="lg:col-span-4 flex flex-col gap-4">
              <LiveEventFeed
                telemetry={data.telemetry}
                agentOutputs={data.agent_outputs}
                masterRec={data.master_recommendation}
              />
              
              <IncidentReporter
                authToken={authToken}
                onReportSuccess={() => {}}
                selectedCoordinates={selectedCoords}
              />
            </div>
          </div>

          {/* Layer 5.3: Bottom Row - Agent reasoning network & timelines */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
            
            {/* 10 Autonomous agents cards */}
            <div className="lg:col-span-8">
              <AgentReasoningPanel agentOutputs={data.agent_outputs} />
            </div>

            {/* AI Explainability & Cascade recommendation */}
            <div className="lg:col-span-4">
              <ExplainabilityPanel masterRec={data.master_recommendation} dataQuality={data.data_quality} />
            </div>
          </div>

          {/* Layer 5.4: Predictive Horizons */}
          <PredictionTimeline predictions={data.predictions} />
          
        </div>
      ) : (
        <div className="flex-1 flex flex-col items-center justify-center py-20 text-slate-400 gap-3 font-mono">
          <RefreshCw className="h-10 w-10 text-brand-accent animate-spin" />
          <span>ESTABLISHING BROADCAST CONNECTION TO SMART CITY SIMULATOR BUS...</span>
        </div>
      )}
    </div>
  );
}
