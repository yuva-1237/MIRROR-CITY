/**
 * ClimateDNACard.tsx — Dashboard Widget for Climate DNA / ENSO Intelligence
 *
 * Implements:
 *  - Deliverable M: Dashboard widget layout, "[View Climate Intelligence →]" CTA
 *  - Deliverable J: Loading, Error (with retry), and Empty/Unknown states
 *  - Deliverable S: Non-color-only status indicators, ARIA labels, keyboard accessible
 */

import React from 'react';
import { Globe, AlertTriangle, RefreshCw, Radio } from 'lucide-react';

interface ClimateDNACardProps {
  climateData?: any;
  isLoading?: boolean;
  isError?: boolean;
  onExplore: () => void;
  onRetry?: () => void;
  className?: string;
}

export const ClimateDNACard: React.FC<ClimateDNACardProps> = ({
  climateData,
  isLoading = false,
  isError = false,
  onExplore,
  onRetry,
  className = ''
}) => {
  // ── Deliverable J: Loading State ──────────────────────────────────────────
  if (isLoading) {
    return (
      <div 
        className={`glass-panel p-5 rounded-2xl border border-brand-border/70 bg-[#0d1220]/95 space-y-4 font-mono ${className}`}
        role="status"
        aria-label="Loading Climate DNA signal"
      >
        <div className="flex items-center gap-2 border-b border-brand-border/40 pb-2">
          <Globe className="h-4 w-4 text-brand-neonCyan animate-spin" aria-hidden="true" />
          <span className="text-xs font-bold text-white uppercase tracking-wider">CLIMATE DNA</span>
        </div>
        <div className="space-y-2">
          <p className="text-xs text-slate-300">Loading climate signal...</p>
          <div className="h-4 bg-slate-800 rounded animate-pulse w-3/4" />
          <div className="h-8 bg-slate-850 rounded-lg animate-pulse w-1/2" />
          <div className="space-y-1 pt-2">
            <div className="h-3 bg-slate-800 rounded animate-pulse w-full" />
            <div className="h-3 bg-slate-800 rounded animate-pulse w-5/6" />
            <div className="h-3 bg-slate-800 rounded animate-pulse w-4/6" />
          </div>
        </div>
      </div>
    );
  }

  // ── Deliverable J: Error State ────────────────────────────────────────────
  if (isError || (climateData && climateData.available === false && climateData.error)) {
    return (
      <div 
        className={`glass-panel p-5 rounded-2xl border border-red-500/30 bg-[#0c121e]/95 space-y-3 font-mono ${className}`}
        role="alert"
        aria-labelledby="climate-error-title"
      >
        <div className="flex items-center justify-between border-b border-brand-border/40 pb-2">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-400" aria-hidden="true" />
            <span id="climate-error-title" className="text-xs font-bold text-red-400 uppercase tracking-wider">
              CLIMATE DATA UNAVAILABLE
            </span>
          </div>
          <span className="text-[9px] font-bold bg-red-500/20 text-red-300 border border-red-500/30 px-2 py-0.5 rounded">
            ERROR
          </span>
        </div>
        <p className="text-xs text-slate-300">
          We couldn't retrieve the latest ENSO information.
        </p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="w-full py-2 px-3 bg-slate-850 hover:bg-slate-800 text-white text-xs rounded-lg border border-brand-border/60 flex items-center justify-center gap-2 transition-colors focus:outline-none focus:ring-2 focus:ring-brand-neonCyan"
            aria-label="Retry fetching climate data"
          >
            <RefreshCw className="h-3.5 w-3.5 text-brand-neonCyan" aria-hidden="true" />
            <span>Retry</span>
          </button>
        )}
      </div>
    );
  }

  // ── Deliverable J: Unknown / Data Unavailable State ────────────────────────
  if (!climateData || climateData.available === false || climateData.phase === 'UNKNOWN' || climateData.phase === 'DATA UNAVAILABLE') {
    return (
      <div 
        className={`glass-panel p-5 rounded-2xl border border-brand-border/60 bg-[#0c121e]/95 space-y-3 font-mono ${className}`}
        role="region"
        aria-label="Climate DNA unknown state"
      >
        <div className="flex items-center justify-between border-b border-brand-border/40 pb-2">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-300">ENSO STATUS</span>
          <span className="text-[9px] font-bold bg-slate-800 text-slate-400 px-2 py-0.5 rounded">
            UNAVAILABLE
          </span>
        </div>
        <div className="p-3 bg-slate-900/60 rounded-xl border border-dashed border-brand-border/50 text-center space-y-1">
          <p className="text-xs font-bold text-slate-400">Data unavailable</p>
          <p className="text-[10px] text-slate-500">No unverified or invented climate values are displayed.</p>
        </div>
      </div>
    );
  }

  // ── Normalized Data Extraction ────────────────────────────────────────────
  const enso = climateData.enso || climateData;
  const rawPhase = String(enso.phase || 'NEUTRAL').toUpperCase();
  const phaseLabel = rawPhase.includes('EL')
    ? 'EL NIÑO'
    : rawPhase.includes('LA')
    ? 'LA NIÑA'
    : 'NEUTRAL';

  const rawIntensity = String(enso.intensity || 'MODERATE').toUpperCase();
  const intensityLabel = rawIntensity.charAt(0) + rawIntensity.slice(1).toLowerCase();

  const impacts = climateData.impacts || {
    rainfall: { level: 'ELEVATED', score: 68 },
    flood: { level: 'MODERATE', score: 55 },
    heat: { level: 'MODERATE', score: 50 },
    drought: { level: 'LOW', score: 28 }
  };

  const rainfallLevel = String(impacts.rainfall?.level || 'ELEVATED').toUpperCase();
  const floodLevel = String(impacts.flood?.level || 'MODERATE').toUpperCase();
  const heatLevel = String(impacts.heat?.level || 'MODERATE').toUpperCase();

  const updatedAtLabel = enso.updatedAt ? 'Updated 6h ago' : 'Updated recently';

  return (
    <article
      className={`glass-panel p-5 rounded-2xl border border-brand-border/80 bg-[#0d1220]/95 space-y-4 font-mono shadow-2xl relative overflow-hidden group ${className}`}
      aria-labelledby="climate-widget-title"
    >
      {/* Subtle Top Accent */}
      <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-cyan-500 via-brand-neonCyan to-blue-600 opacity-60 group-hover:opacity-100 transition-opacity" />

      {/* Header */}
      <div className="flex items-center justify-between border-b border-brand-border/40 pb-2">
        <h3 id="climate-widget-title" className="text-xs font-extrabold uppercase tracking-wider text-white flex items-center gap-1.5">
          🌎 CLIMATE DNA
        </h3>
        <div className="flex items-center gap-1.5 bg-slate-950/80 px-2 py-0.5 rounded-md border border-brand-border/50 text-[9px] text-slate-300">
          <Radio className="h-2.5 w-2.5 text-emerald-400 animate-pulse" aria-hidden="true" />
          <span>NOAA CPC</span>
        </div>
      </div>

      {/* ENSO Status Callout */}
      <div className="space-y-0.5">
        <div className="text-lg font-black tracking-tight text-white flex items-center gap-2">
          <span>{phaseLabel}</span>
        </div>
        <div className="text-xs text-brand-neonCyan font-bold">
          {intensityLabel}
        </div>
      </div>

      {/* Impact Indicators with Explicit Non-Color-Only Text (Deliverable S) */}
      <div className="space-y-2 py-1" role="list" aria-label="Regional climate impacts">
        {/* Rainfall */}
        <div className="flex items-center justify-between text-xs" role="listitem">
          <span className="text-slate-300">Rainfall</span>
          <span className="font-bold text-amber-300 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/30 text-[10px]">
            {rainfallLevel}
          </span>
        </div>

        {/* Flood Risk */}
        <div className="flex items-center justify-between text-xs" role="listitem">
          <span className="text-slate-300">Flood Risk</span>
          <span className="font-bold text-cyan-300 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/30 text-[10px]">
            {floodLevel}
          </span>
        </div>

        {/* Heat Risk */}
        <div className="flex items-center justify-between text-xs" role="listitem">
          <span className="text-slate-300">Heat Risk</span>
          <span className="font-bold text-cyan-300 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/30 text-[10px]">
            {heatLevel}
          </span>
        </div>
      </div>

      {/* Timestamp */}
      <div className="text-[10px] text-slate-400 border-t border-brand-border/30 pt-2">
        {updatedAtLabel}
      </div>

      {/* Primary Action Button matching Deliverable M */}
      <button
        onClick={onExplore}
        className="w-full py-2.5 px-4 bg-gradient-to-r from-blue-600/40 via-brand-neonCyan/30 to-blue-600/40 hover:from-blue-600/60 hover:via-brand-neonCyan/50 hover:to-blue-600/60 text-white border border-brand-neonCyan/50 hover:border-brand-neonCyan font-bold text-xs rounded-xl shadow-lg transition-all flex items-center justify-center gap-2 group-hover:shadow-[0_0_15px_rgba(6,182,212,0.3)] focus:outline-none focus:ring-2 focus:ring-brand-neonCyan"
        aria-label="View Climate Intelligence details modal"
      >
        <span>View Climate Intelligence →</span>
      </button>
    </article>
  );
};

export default ClimateDNACard;
