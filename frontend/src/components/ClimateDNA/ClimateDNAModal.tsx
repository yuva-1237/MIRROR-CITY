import { useState, useEffect } from 'react';
import {
  X, Globe, Radio, ShieldCheck, AlertCircle, Waves, Flame, CloudRain,
  Sun, Droplets, Zap, Building, Wheat, HelpCircle, Activity,
  RefreshCw, Layers, Compass
} from 'lucide-react';
import {
  getClimateImpact,
  getClimateTimeline,
  getTeleconnectionVisuals,
  simulateClimateScenario
} from '../../api/climateApi';

interface ClimateDNAModalProps {
  isOpen: boolean;
  onClose: () => void;
  activeCity?: any;
  authToken: string;
}

export default function ClimateDNAModal({
  isOpen,
  onClose,
  activeCity,
  authToken
}: ClimateDNAModalProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'risks' | 'timeline' | 'simulate' | 'teleconnection' | 'shadow_ai'>('overview');
  
  // Data states
  const [loading, setLoading] = useState(true);
  const [impactData, setImpactData] = useState<any>(null);
  const [timelineData, setTimelineData] = useState<any>(null);
  const [teleconnectionData, setTeleconnectionData] = useState<any>(null);
  const [fetchError, setFetchError] = useState<string | null>(null);

  // Simulation state
  const [simTargetPhase, setSimTargetPhase] = useState<'El Niño' | 'La Niña' | 'Neutral'>('El Niño');
  const [simLoading, setSimLoading] = useState(false);
  const [simResult, setSimResult] = useState<any>(null);

  // SHADOW AI interactive query state
  const [selectedQuestion, setSelectedQuestion] = useState<string>('flood');

  const cityName = activeCity?.name || 'Chennai';
  const cityLat = activeCity?.lat ?? 13.0827;
  const cityLng = activeCity?.lng ?? 80.2707;
  const cityElev = activeCity?.elevation ?? 20.0;

  // Fetch full climate intelligence data on open or city change
  useEffect(() => {
    if (!isOpen) return;

    let isMounted = true;
    setLoading(true);
    setFetchError(null);

    const loadData = async () => {
      try {
        const [impactRes, timelineRes, teleRes] = await Promise.all([
          getClimateImpact({
            city: cityName,
            lat: cityLat,
            lng: cityLng,
            elevation: cityElev,
          }),
          getClimateTimeline(),
          getTeleconnectionVisuals({
            lat: cityLat,
            lng: cityLng,
            city: cityName,
            token: authToken,
          }),
        ]);

        if (isMounted) {
          setImpactData((impactRes as any)?.data || impactRes);
          setTimelineData((timelineRes as any)?.data || timelineRes);
          setTeleconnectionData(teleRes);
          setLoading(false);
        }
      } catch (err: any) {
        console.error('[ClimateDNA] Failed to load climate data:', err);
        if (isMounted) {
          setFetchError(err?.message || 'Climate data temporarily unavailable.');
          setLoading(false);
        }
      }
    };

    loadData();
    return () => { isMounted = false; };
  }, [isOpen, cityName, cityLat, cityLng, cityElev, authToken]);

  // Handle What-If Simulation trigger
  const runSimulation = async (phase: 'El Niño' | 'La Niña' | 'Neutral') => {
    setSimTargetPhase(phase);
    setSimLoading(true);
    try {
      const res = await simulateClimateScenario({
        city: cityName,
        lat: cityLat,
        lng: cityLng,
        target_phase: phase,
        elevation: cityElev,
        token: authToken,
      });
      setSimResult(res);
    } catch (err: any) {
      console.error('[ClimateDNA] Simulation failed:', err);
    } finally {
      setSimLoading(false);
    }
  };

  // Initial simulation run on tab open
  useEffect(() => {
    if (activeTab === 'simulate' && !simResult && !simLoading) {
      runSimulation(simTargetPhase);
    }
  }, [activeTab]);

  if (!isOpen) return null;

  const enso = impactData?.enso || {};
  const ensoPhase = enso.phase || 'Neutral';
  const ensoIntensity = enso.intensity || 'Normal';
  const ensoAnomaly = enso.anomaly_c !== undefined ? enso.anomaly_c : 0.0;
  const ensoConfidence = Math.round((enso.confidence || 0.82) * 100);

  const impacts = impactData?.impacts || {};
  const climateDna = impactData?.climate_dna || {};
  const signals = climateDna.climate_signals || {};

  const getRiskIcon = (key: string) => {
    switch (key) {
      case 'rainfall': return <CloudRain className="h-4 w-4 text-cyan-400" />;
      case 'flood': return <Waves className="h-4 w-4 text-blue-400" />;
      case 'heat': return <Flame className="h-4 w-4 text-amber-400" />;
      case 'drought': return <Sun className="h-4 w-4 text-orange-400" />;
      case 'water_stress': return <Droplets className="h-4 w-4 text-sky-400" />;
      case 'energy_demand': return <Zap className="h-4 w-4 text-purple-400" />;
      case 'infrastructure': return <Building className="h-4 w-4 text-slate-300" />;
      case 'agriculture': return <Wheat className="h-4 w-4 text-emerald-400" />;
      default: return <Activity className="h-4 w-4 text-slate-400" />;
    }
  };

  const getRiskColor = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'high': return 'bg-red-500/20 text-red-400 border-red-500/40';
      case 'elevated': return 'bg-amber-500/20 text-amber-400 border-amber-500/40';
      case 'moderate': return 'bg-cyan-500/20 text-cyan-400 border-cyan-500/40';
      default: return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40';
    }
  };

  return (
    <div className="fixed inset-0 z-[5000] flex items-center justify-center p-3 sm:p-6 bg-black/85 backdrop-blur-xl animate-fadeIn select-none">
      <div className="w-full max-w-5xl h-[92vh] flex flex-col bg-[#0b101c] border border-brand-border rounded-2xl shadow-2xl overflow-hidden font-sans text-slate-100 relative">
        
        {/* Top Mission Control Header */}
        <header className="p-4 sm:p-5 bg-[#0f1627] border-b border-brand-border/80 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 relative z-10">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-brand-neonCyan/20 border border-brand-neonCyan/40 rounded-xl">
              <Globe className="h-6 w-6 text-brand-neonCyan animate-spin-slow" />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="text-base font-black tracking-tight text-white font-mono uppercase flex items-center gap-1.5">
                  CLIMATE DNA <span className="text-xs text-brand-neonCyan font-normal">v2.0</span>
                </h2>
                <span className="text-[10px] font-mono font-bold bg-blue-950/80 text-blue-300 border border-blue-500/40 px-2 py-0.5 rounded">
                  {cityName}
                </span>
                <span className="text-[10px] font-mono text-slate-400">
                  {cityLat.toFixed(2)}°N, {cityLng.toFixed(2)}°E · {cityElev}m AMSL
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-mono tracking-tight">
                Global climate signals → Local city impact
              </p>
            </div>
          </div>

          {/* Top Right Live Telemetry Badge & Close */}
          <div className="flex items-center gap-3 self-end sm:self-auto">
            <div className="flex items-center gap-2 bg-slate-950/80 px-3 py-1 rounded-lg border border-brand-border/60 text-xs font-mono">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-slate-300 text-[11px]">
                {enso.source?.includes('NOAA') ? 'NOAA CPC LIVE' : 'NOAA CPC'}
              </span>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white rounded-lg border border-brand-border transition-colors"
              title="Close Climate Intelligence"
            >
              <X size={18} />
            </button>
          </div>
        </header>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 bg-[#090d17] px-4 py-2 border-b border-brand-border/60 overflow-x-auto text-xs font-mono">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-3 py-1.5 rounded-lg transition-all whitespace-nowrap flex items-center gap-1.5 ${
              activeTab === 'overview'
                ? 'bg-blue-600 text-white font-bold shadow-md'
                : 'text-slate-400 hover:text-white hover:bg-slate-900/60'
            }`}
          >
            <Layers size={13} /> City DNA Overview
          </button>
          <button
            onClick={() => setActiveTab('risks')}
            className={`px-3 py-1.5 rounded-lg transition-all whitespace-nowrap flex items-center gap-1.5 ${
              activeTab === 'risks'
                ? 'bg-blue-600 text-white font-bold shadow-md'
                : 'text-slate-400 hover:text-white hover:bg-slate-900/60'
            }`}
          >
            <ShieldCheck size={13} /> 8-Sector Risk Engine
          </button>
          <button
            onClick={() => setActiveTab('timeline')}
            className={`px-3 py-1.5 rounded-lg transition-all whitespace-nowrap flex items-center gap-1.5 ${
              activeTab === 'timeline'
                ? 'bg-blue-600 text-white font-bold shadow-md'
                : 'text-slate-400 hover:text-white hover:bg-slate-900/60'
            }`}
          >
            <Activity size={13} /> Climate Timeline
          </button>
          <button
            onClick={() => setActiveTab('simulate')}
            className={`px-3 py-1.5 rounded-lg transition-all whitespace-nowrap flex items-center gap-1.5 ${
              activeTab === 'simulate'
                ? 'bg-brand-neonPurple/30 text-white border border-brand-neonPurple/50 font-bold shadow-md'
                : 'text-slate-400 hover:text-white hover:bg-slate-900/60'
            }`}
          >
            <RefreshCw size={13} className={simLoading ? 'animate-spin' : ''} /> "What If?" Scenario
          </button>
          <button
            onClick={() => setActiveTab('teleconnection')}
            className={`px-3 py-1.5 rounded-lg transition-all whitespace-nowrap flex items-center gap-1.5 ${
              activeTab === 'teleconnection'
                ? 'bg-blue-600 text-white font-bold shadow-md'
                : 'text-slate-400 hover:text-white hover:bg-slate-900/60'
            }`}
          >
            <Compass size={13} /> Pacific Teleconnection
          </button>
          <button
            onClick={() => setActiveTab('shadow_ai')}
            className={`px-3 py-1.5 rounded-lg transition-all whitespace-nowrap flex items-center gap-1.5 ${
              activeTab === 'shadow_ai'
                ? 'bg-cyan-600/30 text-cyan-300 border border-cyan-500/40 font-bold shadow-md'
                : 'text-slate-400 hover:text-white hover:bg-slate-900/60'
            }`}
          >
            <HelpCircle size={13} /> SHADOW AI Climate
          </button>
        </nav>

        {/* Modal Main Body */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
          {loading ? (
            <div className="flex flex-col items-center justify-center h-full py-20 text-slate-400 gap-3 font-mono">
              <RefreshCw className="h-10 w-10 text-brand-neonCyan animate-spin" />
              <span>SYNCHRONIZING WITH NOAA CPC GLOBAL ENSO TELEMETRY...</span>
            </div>
          ) : fetchError ? (
            <div className="p-6 bg-red-950/40 border border-red-500/50 rounded-2xl text-center space-y-2">
              <AlertCircle className="h-8 w-8 text-red-400 mx-auto" />
              <h3 className="text-sm font-bold text-white uppercase font-mono">CLIMATE DATA TEMPORARILY UNAVAILABLE</h3>
              <p className="text-xs text-slate-400">{fetchError}</p>
            </div>
          ) : (
            <>
              {/* TAB 1: CITY DNA & OVERVIEW */}
              {activeTab === 'overview' && (
                <div className="space-y-6 animate-fadeIn">
                  {/* Global ENSO Headline Card */}
                  <div className="p-5 bg-gradient-to-r from-blue-950/40 via-[#10172a]/60 to-purple-950/40 border border-brand-border rounded-2xl relative overflow-hidden">
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                      <div>
                        <span className="text-[10px] font-mono uppercase tracking-widest text-slate-400 font-bold">
                          Current Primary Climate Phase
                        </span>
                        <div className="text-3xl font-black text-white font-mono flex items-center gap-3 mt-1">
                          {ensoPhase}
                          <span className={`text-xs font-mono uppercase px-3 py-1 rounded-full border font-bold ${
                            ensoPhase.includes('EL')
                              ? 'bg-amber-500/20 text-amber-400 border-amber-500/40'
                              : (ensoPhase.includes('LA') ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40' : 'bg-cyan-500/20 text-cyan-400 border-cyan-500/40')
                          }`}>
                            {ensoIntensity}
                          </span>
                        </div>
                        <p className="text-xs text-slate-300 mt-2 max-w-2xl leading-relaxed">
                          {enso.status_description || 'Global ocean-atmosphere teleconnections active across the equatorial Pacific basin.'}
                        </p>
                      </div>

                      <div className="flex flex-row md:flex-col gap-3 bg-slate-950/80 p-3 rounded-xl border border-brand-border/60 text-xs font-mono shrink-0">
                        <div>
                          <span className="text-[9px] text-slate-500 block uppercase">Niño-3.4 SST Anomaly</span>
                          <span className="text-base font-bold text-brand-neonCyan">
                            {ensoAnomaly >= 0 ? `+${ensoAnomaly.toFixed(2)}` : ensoAnomaly.toFixed(2)}°C
                          </span>
                        </div>
                        <div>
                          <span className="text-[9px] text-slate-500 block uppercase">Diagnostic Confidence</span>
                          <span className="text-base font-bold text-white">{ensoConfidence}%</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Structured CITY DNA Environmental Tree */}
                  <div className="bg-[#101729]/80 border border-brand-border p-5 rounded-2xl space-y-4">
                    <div className="flex items-center justify-between border-b border-brand-border/60 pb-2">
                      <div className="flex items-center gap-2">
                        <Layers className="h-4 w-4 text-brand-neonCyan" />
                        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200 font-mono">
                          CITY DNA — Environmental Signal Architecture
                        </h3>
                      </div>
                      <span className="text-[9px] font-mono text-slate-500 uppercase">Hierarchical Coupling</span>
                    </div>

                    <div className="bg-slate-950/70 p-4 rounded-xl font-mono text-xs text-slate-300 space-y-2 border border-brand-border/40">
                      <div className="text-white font-bold flex items-center gap-2">
                        <span className="text-brand-neonCyan">LOCATION</span>
                        <span>{cityName}, {climateDna.region || 'India'}</span>
                      </div>
                      <div className="text-slate-400 pl-4 space-y-1.5 border-l border-brand-border/60 ml-2 mt-2">
                        <div className="text-slate-200 font-bold uppercase text-[11px]">CLIMATE SIGNALS</div>
                        <div className="flex items-center justify-between py-1 border-b border-slate-900">
                          <span className="text-slate-400">├── ENSO (El Niño–Southern Oscillation)</span>
                          <span className="font-bold text-white">
                            {signals.enso?.phase || ensoPhase} ({signals.enso?.intensity || ensoIntensity}, {ensoAnomaly >= 0 ? `+${ensoAnomaly.toFixed(2)}` : ensoAnomaly.toFixed(2)}°C)
                          </span>
                        </div>
                        <div className="flex items-center justify-between py-1 border-b border-slate-900">
                          <span className="text-slate-400">├── Indian Ocean Dipole (IOD)</span>
                          <span className="text-slate-300">{signals.indian_ocean_dipole?.state || 'Neutral'}</span>
                        </div>
                        <div className="flex items-center justify-between py-1 border-b border-slate-900">
                          <span className="text-slate-400">├── Seasonal Climatology</span>
                          <span className="text-slate-300">{signals.seasonal_monsoon?.regime || 'Active Cycle'}</span>
                        </div>
                        <div className="flex items-center justify-between py-1 border-b border-slate-900">
                          <span className="text-slate-400">├── Temperature Anomaly</span>
                          <span className="text-amber-400 font-bold">{signals.temperature_anomaly || 'Normal variance'}</span>
                        </div>
                        <div className="flex items-center justify-between py-1">
                          <span className="text-slate-400">└── Rainfall Anomaly Variance</span>
                          <span className="text-cyan-400 font-bold">{signals.rainfall_anomaly || 'Statistical shift'}</span>
                        </div>
                      </div>
                    </div>

                    <p className="text-[11px] text-slate-400 italic">
                      ℹ️ {climateDna.attribution_note || 'ENSO is one environmental signal among several. Local rainfall and urban drainage determine actual ground outcomes.'}
                    </p>
                  </div>

                  {/* Probabilistic Summary Card */}
                  <div className="p-4 bg-blue-950/20 border border-blue-500/30 rounded-xl space-y-1">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-blue-300 font-bold">
                      Probabilistic Climate Summary for {cityName}
                    </span>
                    <p className="text-xs text-slate-300 leading-relaxed font-sans">
                      {impactData?.summary_rationale}
                    </p>
                  </div>
                </div>
              )}

              {/* TAB 2: 8 MULTI-SECTOR RISK ENGINE */}
              {activeTab === 'risks' && (
                <div className="space-y-4 animate-fadeIn">
                  <div className="flex justify-between items-center">
                    <div>
                      <h3 className="text-xs font-bold text-white uppercase font-mono tracking-wider">
                        8-Sector Multi-Dimensional Risk Matrix
                      </h3>
                      <p className="text-[10px] text-slate-400 font-mono">
                        Statistical teleconnection sensitivity evaluated against urban infrastructure
                      </p>
                    </div>
                    <span className="text-[10px] font-mono text-brand-neonCyan font-bold">
                      Coupled Signal: {ensoPhase}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {Object.entries(impacts).map(([key, item]: [string, any]) => (
                      <div
                        key={key}
                        className="bg-[#101729]/80 border border-brand-border p-4 rounded-xl space-y-3 font-sans relative overflow-hidden hover:border-brand-neonCyan/40 transition-colors"
                      >
                        <div className="flex justify-between items-start">
                          <div className="flex items-center gap-2">
                            {getRiskIcon(key)}
                            <span className="text-xs font-bold text-white capitalize">
                              {key.replace('_', ' ')}
                            </span>
                          </div>
                          <span className={`text-[9px] uppercase font-mono font-bold px-2 py-0.5 rounded border ${getRiskColor(item.level)}`}>
                            {item.level}
                          </span>
                        </div>

                        {/* Progress score */}
                        <div className="space-y-1">
                          <div className="flex justify-between text-[10px] font-mono text-slate-400">
                            <span>Vulnerability Index</span>
                            <span className="font-bold text-white">{item.score}/100</span>
                          </div>
                          <div className="w-full bg-slate-950 h-1.5 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-brand-neonCyan rounded-full transition-all duration-800"
                              style={{ width: `${item.score}%` }}
                            />
                          </div>
                        </div>

                        {/* Contributing Drivers */}
                        <div className="space-y-1 border-t border-brand-border/40 pt-2">
                          <span className="text-[9px] font-mono uppercase text-slate-500 font-semibold block">
                            Key Drivers:
                          </span>
                          <ul className="text-[10px] text-slate-300 space-y-0.5 font-mono">
                            {item.drivers?.map((drv: string, i: number) => (
                              <li key={i} className="truncate text-slate-400 flex items-center gap-1">
                                <span className="text-brand-neonCyan">•</span> {drv}
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* TAB 3: CLIMATE TIMELINE */}
              {activeTab === 'timeline' && (
                <div className="space-y-6 animate-fadeIn">
                  <div className="bg-[#101729]/80 border border-brand-border p-5 rounded-2xl space-y-4">
                    <div className="flex justify-between items-center border-b border-brand-border/50 pb-2">
                      <div>
                        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200 font-mono">
                          Pacific Ocean ENSO Cycle Timeline (NOAA ONI 1950–2026)
                        </h3>
                        <p className="text-[10px] text-slate-400 font-mono">
                          Tri-monthly running mean SST anomalies in the Niño 3.4 region
                        </p>
                      </div>
                      <span className="text-[9px] font-mono text-brand-neonCyan font-bold">
                        Target: Fall/Winter 2026-27
                      </span>
                    </div>

                    {/* Visual Phase Progression Bar */}
                    <div className="p-4 bg-slate-950/70 rounded-xl border border-brand-border/40 font-mono space-y-2">
                      <div className="flex justify-between text-[10px] uppercase font-bold text-slate-400">
                        <span>PAST (2022-2024)</span>
                        <span className="text-brand-neonCyan font-black">NOW (2026)</span>
                        <span>FUTURE (2027)</span>
                      </div>
                      <div className="flex items-center justify-between text-xs py-2 px-3 bg-slate-900/80 rounded-lg border border-brand-border/50">
                        <span className="text-emerald-400 font-semibold">La Niña (Triple Dip)</span>
                        <span className="text-slate-500">───►</span>
                        <span className="text-amber-400 font-semibold">El Niño (Strong)</span>
                        <span className="text-slate-500">───►</span>
                        <span className="text-cyan-400 font-bold bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-500/40">
                          {ensoPhase} ({ensoIntensity})
                        </span>
                      </div>
                    </div>

                    {/* Historical Records Table */}
                    <div className="max-h-56 overflow-y-auto space-y-1 pr-1 font-mono text-xs">
                      {timelineData?.timeline?.slice(-12).reverse().map((rec: any, idx: number) => (
                        <div
                          key={idx}
                          className="flex items-center justify-between p-2 rounded-lg bg-slate-950/60 border border-brand-border/30 text-[11px]"
                        >
                          <div className="flex items-center gap-3">
                            <span className="font-bold text-white w-12">{rec.year}</span>
                            <span className="text-slate-400 w-16">{rec.season}</span>
                            <span className={`px-2 py-0.2 rounded text-[10px] font-semibold ${
                              rec.phase.includes('El')
                                ? 'bg-amber-500/10 text-amber-400'
                                : (rec.phase.includes('La') ? 'bg-emerald-500/10 text-emerald-400' : 'bg-cyan-500/10 text-cyan-400')
                            }`}>
                              {rec.phase}
                            </span>
                          </div>
                          <span className={`font-bold ${rec.anomaly >= 0 ? 'text-amber-400' : 'text-cyan-400'}`}>
                            {rec.anomaly >= 0 ? `+${rec.anomaly.toFixed(2)}` : rec.anomaly.toFixed(2)}°C
                          </span>
                        </div>
                      ))}
                    </div>

                    {/* Official IRI/CPC Probabilistic Outlook */}
                    {timelineData?.outlook && (
                      <div className="p-4 bg-slate-950/80 rounded-xl border border-brand-border/50 space-y-2 font-mono">
                        <div className="flex justify-between text-[11px]">
                          <span className="text-slate-300 font-bold">CPC/IRI Official Probabilistic Outlook:</span>
                          <span className="text-brand-neonCyan">{timelineData.outlook.target_season}</span>
                        </div>
                        <div className="grid grid-cols-3 gap-2 text-center text-[10px]">
                          <div className="p-2 bg-amber-950/30 border border-amber-500/30 rounded-lg">
                            <span className="text-slate-400 block">El Niño</span>
                            <span className="text-sm font-bold text-amber-400">
                              {Math.round(timelineData.outlook.el_nino_probability * 100)}%
                            </span>
                          </div>
                          <div className="p-2 bg-cyan-950/30 border border-cyan-500/30 rounded-lg">
                            <span className="text-slate-400 block">Neutral</span>
                            <span className="text-sm font-bold text-cyan-400">
                              {Math.round(timelineData.outlook.neutral_probability * 100)}%
                            </span>
                          </div>
                          <div className="p-2 bg-emerald-950/30 border border-emerald-500/30 rounded-lg">
                            <span className="text-slate-400 block">La Niña</span>
                            <span className="text-sm font-bold text-emerald-400">
                              {Math.round(timelineData.outlook.la_nina_probability * 100)}%
                            </span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* TAB 4: "WHAT IF?" CLIMATE SIMULATION */}
              {activeTab === 'simulate' && (
                <div className="space-y-6 animate-fadeIn">
                  {/* Warning Banner */}
                  <div className="p-3 bg-amber-950/40 border border-brand-neonOrange/50 rounded-xl flex items-center gap-3 text-xs font-mono text-amber-300">
                    <AlertCircle className="h-5 w-5 text-brand-neonOrange shrink-0" />
                    <div>
                      <strong className="block font-bold">SIMULATED SCENARIO — NOT A FORECAST</strong>
                      <span>Counterfactual modeling tests municipal resiliency against alternative global climate phases.</span>
                    </div>
                  </div>

                  {/* Scenario Selector */}
                  <div className="p-4 bg-[#101729]/80 border border-brand-border rounded-xl space-y-3 font-mono">
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-slate-300 font-bold uppercase">Select Alternative Global ENSO Scenario:</span>
                      <span className="text-slate-500">Current: {ensoPhase}</span>
                    </div>

                    <div className="grid grid-cols-3 gap-3">
                      {(['El Niño', 'La Niña', 'Neutral'] as const).map((phase) => (
                        <button
                          key={phase}
                          onClick={() => runSimulation(phase)}
                          disabled={simLoading}
                          className={`py-3 px-4 rounded-xl border text-xs font-bold transition-all flex items-center justify-center gap-2 ${
                            simTargetPhase === phase
                              ? 'bg-brand-neonPurple/30 border-brand-neonPurple text-white shadow-lg'
                              : 'bg-slate-950/60 border-brand-border/60 text-slate-400 hover:text-white'
                          }`}
                        >
                          {phase}
                          {simTargetPhase === phase && <span className="h-1.5 w-1.5 rounded-full bg-brand-neonPurple animate-ping" />}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Simulation Delta Results */}
                  {simResult && (
                    <div className="bg-[#101729]/80 border border-brand-border p-5 rounded-2xl space-y-4">
                      <div className="flex justify-between items-center border-b border-brand-border/60 pb-2">
                        <span className="text-xs font-mono font-bold uppercase text-white">
                          Potential City Impacts Delta for {cityName}
                        </span>
                        <span className="text-[10px] font-mono text-brand-neonPurple font-bold">
                          Scenario: {simTargetPhase}
                        </span>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 font-mono">
                        {simResult.deltas && Object.entries(simResult.deltas).map(([k, d]: [string, any]) => (
                          <div key={k} className="p-3 bg-slate-950/80 rounded-xl border border-brand-border/40 space-y-1">
                            <div className="flex justify-between items-center text-xs">
                              <span className="text-slate-300 font-bold capitalize">{k.replace('_', ' ')}</span>
                              <span className={`font-black text-sm flex items-center gap-0.5 ${
                                d.delta > 0 ? 'text-red-400' : (d.delta < 0 ? 'text-emerald-400' : 'text-slate-400')
                              }`}>
                                {d.trend} {d.delta > 0 ? `+${d.delta}` : d.delta}
                              </span>
                            </div>
                            <div className="flex justify-between text-[10px] text-slate-500">
                              <span>Baseline: {d.current_level}</span>
                              <span>Simulated: {d.simulated_level}</span>
                            </div>
                          </div>
                        ))}
                      </div>

                      <p className="text-xs font-sans text-slate-300 bg-slate-950/60 p-3 rounded-xl border border-brand-border/30">
                        {simResult.narrative}
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* TAB 5: PACIFIC TELECONNECTION & GLOBE */}
              {activeTab === 'teleconnection' && (
                <div className="space-y-6 animate-fadeIn">
                  <div className="bg-[#101729]/80 border border-brand-border p-5 rounded-2xl space-y-4">
                    <div className="flex justify-between items-center border-b border-brand-border/60 pb-2 font-mono">
                      <div>
                        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                          Pacific Ocean to {cityName} Teleconnection Propagation
                        </h3>
                        <p className="text-[10px] text-slate-400">
                          Atmospheric Walker & Rossby wave train vector linking ocean anomalies to local city
                        </p>
                      </div>
                      <span className="text-[10px] text-brand-neonCyan font-bold">
                        Niño-3.4 (0°N, 145°W)
                      </span>
                    </div>

                    {/* Diagram Representation */}
                    <div className="p-6 bg-slate-950/80 rounded-xl border border-brand-border/50 text-center space-y-4 font-mono">
                      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 max-w-2xl mx-auto py-2">
                        <div className="p-3 bg-blue-950/40 border border-blue-500/40 rounded-xl w-44">
                          <span className="text-[9px] text-slate-500 block uppercase">ORIGIN</span>
                          <span className="text-xs font-bold text-white">Pacific Ocean</span>
                          <span className="text-[10px] text-cyan-400 block mt-1">Niño-3.4 Anomaly</span>
                        </div>
                        <span className="text-brand-neonCyan font-bold text-lg animate-pulse">──►</span>
                        <div className="p-3 bg-purple-950/40 border border-brand-neonPurple/40 rounded-xl w-44">
                          <span className="text-[9px] text-slate-500 block uppercase">COUPLING</span>
                          <span className="text-xs font-bold text-white">Atmospheric Wave</span>
                          <span className="text-[10px] text-purple-300 block mt-1">Walker Circulation</span>
                        </div>
                        <span className="text-brand-neonCyan font-bold text-lg animate-pulse">──►</span>
                        <div className="p-3 bg-emerald-950/40 border border-emerald-500/40 rounded-xl w-44">
                          <span className="text-[9px] text-slate-500 block uppercase">RECEPTION</span>
                          <span className="text-xs font-bold text-white">{cityName}</span>
                          <span className="text-[10px] text-emerald-400 block mt-1">Urban Catchment</span>
                        </div>
                      </div>

                      <p className="text-xs text-slate-400 max-w-xl mx-auto font-sans leading-relaxed">
                        {teleconnectionData?.atmospheric_influence || 'Tropical ocean surface thermal anomalies displace atmospheric convection centers, modifying downstream wind shear, seasonal monsoon tracks, and precipitation distributions.'}
                      </p>
                    </div>

                    {/* Regional Teleconnection Centroids */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 font-mono text-xs">
                      <div className="p-3 bg-slate-950/60 rounded-xl border border-brand-border/40">
                        <span className="text-slate-500 text-[9px] block uppercase">Source Coordinates</span>
                        <span className="text-white font-bold">0.0°N, 145.0°W (Niño 3.4 Centroid)</span>
                      </div>
                      <div className="p-3 bg-slate-950/60 rounded-xl border border-brand-border/40">
                        <span className="text-slate-500 text-[9px] block uppercase">City Reception Node</span>
                        <span className="text-white font-bold">{cityLat.toFixed(2)}°N, {cityLng.toFixed(2)}°E</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 6: SHADOW AI CLIMATE REASONING */}
              {activeTab === 'shadow_ai' && (
                <div className="space-y-6 animate-fadeIn font-sans">
                  <div className="bg-[#101729]/80 border border-brand-border p-5 rounded-2xl space-y-4">
                    <div className="flex items-center gap-2 border-b border-brand-border/60 pb-2">
                      <HelpCircle className="h-5 w-5 text-brand-neonCyan" />
                      <div>
                        <h3 className="text-xs font-bold uppercase tracking-wider text-white font-mono">
                          SHADOW AI — Climate Signal Explainability Engine
                        </h3>
                        <p className="text-[10px] text-slate-400 font-mono">
                          Interactive climate causal chain analysis and primary driver attribution
                        </p>
                      </div>
                    </div>

                    {/* Suggested Inquiries */}
                    <div className="space-y-2">
                      <span className="text-[10px] font-mono uppercase text-slate-400 font-semibold block">
                        Select Diagnostic Inquiry:
                      </span>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 font-mono text-xs">
                        <button
                          onClick={() => setSelectedQuestion('flood')}
                          className={`p-2.5 rounded-xl border text-left transition ${
                            selectedQuestion === 'flood'
                              ? 'bg-blue-600/30 border-blue-500 text-white'
                              : 'bg-slate-950/60 border-brand-border/60 text-slate-400 hover:text-white'
                          }`}
                        >
                          "Why is flood risk evaluated as {impacts.flood?.level || 'moderate'}?"
                        </button>
                        <button
                          onClick={() => setSelectedQuestion('drought')}
                          className={`p-2.5 rounded-xl border text-left transition ${
                            selectedQuestion === 'drought'
                              ? 'bg-blue-600/30 border-blue-500 text-white'
                              : 'bg-slate-950/60 border-brand-border/60 text-slate-400 hover:text-white'
                          }`}
                        >
                          "What is driving regional drought & water stress?"
                        </button>
                        <button
                          onClick={() => setSelectedQuestion('coupling')}
                          className={`p-2.5 rounded-xl border text-left transition ${
                            selectedQuestion === 'coupling'
                              ? 'bg-blue-600/30 border-blue-500 text-white'
                              : 'bg-slate-950/60 border-brand-border/60 text-slate-400 hover:text-white'
                          }`}
                        >
                          "Does ENSO directly dictate tomorrow's weather?"
                        </button>
                      </div>
                    </div>

                    {/* SHADOW AI Response Panel */}
                    <div className="p-4 bg-slate-950/90 rounded-xl border border-brand-border/70 space-y-3">
                      <div className="flex items-center justify-between border-b border-brand-border/40 pb-2">
                        <span className="text-xs font-mono font-bold text-brand-neonCyan flex items-center gap-1.5">
                          🤖 SHADOW AI SYNTHESIS
                        </span>
                        <span className="text-[10px] font-mono text-slate-400">
                          Attribution Confidence: <span className="text-white font-bold">78%</span>
                        </span>
                      </div>

                      {selectedQuestion === 'flood' && (
                        <div className="space-y-3 text-xs leading-relaxed text-slate-200">
                          <p>
                            "The current climate signal ({ensoPhase} {ensoIntensity}) indicates conditions historically
                            associated with increased rainfall variability and higher probabilities of localized convective
                            cloudbursts in the {cityName} region."
                          </p>
                          <div className="bg-[#0c1220] p-3 rounded-lg border border-brand-border/40 font-mono text-[11px] space-y-1">
                            <span className="text-slate-400 uppercase font-bold text-[9px] block">Primary Contributing Drivers:</span>
                            <div className="text-slate-300">• Recent rainfall & seasonal precipitation conditions</div>
                            <div className="text-slate-300">• Surface elevation and catchment basin retention capacity</div>
                            <div className="text-slate-300">
                              • {ensoPhase} Pacific ocean-atmosphere teleconnection signal ({ensoAnomaly >= 0 ? `+${ensoAnomaly.toFixed(2)}` : ensoAnomaly.toFixed(2)}°C)
                            </div>
                          </div>
                        </div>
                      )}

                      {selectedQuestion === 'drought' && (
                        <div className="space-y-3 text-xs leading-relaxed text-slate-200">
                          <p>
                            "Drought risk is evaluated at <strong className="text-white uppercase">{impacts.drought?.level || 'low'}</strong>.
                            Statistical records indicate that tropical Pacific teleconnections modulate regional soil moisture
                            depletion and reservoir recharge velocity over multi-month seasonal horizons."
                          </p>
                          <div className="bg-[#0c1220] p-3 rounded-lg border border-brand-border/40 font-mono text-[11px] space-y-1">
                            <span className="text-slate-400 uppercase font-bold text-[9px] block">Primary Contributing Drivers:</span>
                            <div className="text-slate-300">• Groundwater recharge and seasonal reservoir storage</div>
                            <div className="text-slate-300">• Indian Ocean Dipole (IOD) secondary modulation</div>
                            <div className="text-slate-300">• Multi-week precipitation deficit index</div>
                          </div>
                        </div>
                      )}

                      {selectedQuestion === 'coupling' && (
                        <div className="space-y-3 text-xs leading-relaxed text-slate-200">
                          <p>
                            <strong>No.</strong> MIRROR CITY strictly accounts for the fact that ENSO influences regional climate
                            probabilistically, but does <em>not</em> deterministically dictate day-to-day weather events. Local
                            topography, urban drainage maintenance, and real-time Doppler radar readings remain the definitive
                            operational indicators.
                          </p>
                          <div className="bg-[#0c1220] p-3 rounded-lg border border-brand-border/40 font-mono text-[11px]">
                            <span className="text-emerald-400 font-bold">Rule Enforced:</span> Non-deterministic climate attribution protocol active.
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Modal Footer */}
        <footer className="p-3 sm:p-4 bg-[#090d16] border-t border-brand-border/60 flex flex-col sm:flex-row justify-between items-center gap-2 text-[10px] font-mono text-slate-400">
          <div className="flex items-center gap-2">
            <Radio size={12} className="text-emerald-400 animate-pulse" />
            <span>NOAA CPC Oceanic Niño Index (ONI) · 6-Hour Cache TTL Active</span>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-white rounded-lg border border-brand-border font-bold transition"
          >
            Close Intelligence Window
          </button>
        </footer>
      </div>
    </div>
  );
}
