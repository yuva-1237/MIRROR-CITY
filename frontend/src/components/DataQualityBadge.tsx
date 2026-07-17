import { CheckCircle, AlertTriangle, XCircle, Clock, Wifi, Database } from 'lucide-react';

export type DataSource = 'live_api' | 'cache' | 'simulation' | 'estimated' | 'live';

interface DataQualityBadgeProps {
  source?: DataSource | string;
  confidence?: number;
  compact?: boolean;
  cachedAt?: number;   // seconds ago
  className?: string;
}

/**
 * DataQualityBadge
 * ─────────────────────────────────────────────────────────────
 * Renders a color-coded pill showing the data quality / source:
 *   🟢 Live API   — real-time feed, high confidence
 *   🔵 Live       — live sensor data
 *   🟡 Cached     — last-known-good within 5 min
 *   🟠 Simulation — physics-based estimate
 *   🔴 Stale/Low  — confidence below 50%
 */
const SOURCE_CONFIG: Record<string, { label: string; color: string; bg: string; Icon: any }> = {
  live_api: {
    label: 'Live API',
    color: 'text-emerald-400',
    bg:    'bg-emerald-500/10 border border-emerald-500/30',
    Icon:  Wifi,
  },
  live: {
    label: 'Live',
    color: 'text-emerald-400',
    bg:    'bg-emerald-500/10 border border-emerald-500/30',
    Icon:  CheckCircle,
  },
  cache: {
    label: 'Cached',
    color: 'text-amber-400',
    bg:    'bg-amber-500/10 border border-amber-500/30',
    Icon:  Database,
  },
  simulation: {
    label: 'Simulated',
    color: 'text-sky-400',
    bg:    'bg-sky-500/10 border border-sky-500/30',
    Icon:  AlertTriangle,
  },
  estimated: {
    label: 'Estimated',
    color: 'text-orange-400',
    bg:    'bg-orange-500/10 border border-orange-500/30',
    Icon:  AlertTriangle,
  },
};

export default function DataQualityBadge({
  source = 'simulation',
  confidence,
  compact = false,
  cachedAt,
  className = '',
}: DataQualityBadgeProps) {
  const cfg = SOURCE_CONFIG[source] ?? SOURCE_CONFIG.simulation;
  const Icon = cfg.Icon;

  // Override to red if confidence is very low
  const isLowConfidence = confidence !== undefined && confidence < 50;
  const color  = isLowConfidence ? 'text-red-400'  : cfg.color;
  const bg     = isLowConfidence ? 'bg-red-500/10 border border-red-500/30' : cfg.bg;
  const label  = isLowConfidence ? 'Low Quality' : cfg.label;
  const FinalIcon = isLowConfidence ? XCircle : Icon;

  if (compact) {
    return (
      <span
        title={`Data source: ${label}${confidence !== undefined ? ` (${confidence}% confidence)` : ''}`}
        className={`inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider ${bg} ${color} ${className}`}
      >
        <FinalIcon className="h-2.5 w-2.5" />
        {label}
      </span>
    );
  }

  return (
    <div className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-lg ${bg} ${className}`}>
      <FinalIcon className={`h-3.5 w-3.5 ${color}`} />
      <div className="flex flex-col">
        <span className={`text-[10px] font-bold uppercase tracking-wider ${color}`}>{label}</span>
        {confidence !== undefined && (
          <div className="flex items-center gap-1 mt-0.5">
            <div className="w-16 bg-slate-800 h-0.5 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-700 ${
                  confidence >= 80 ? 'bg-emerald-500' :
                  confidence >= 60 ? 'bg-amber-500' :
                  'bg-red-500'
                }`}
                style={{ width: `${confidence}%` }}
              />
            </div>
            <span className="text-[9px] text-slate-400 font-mono">{confidence}%</span>
          </div>
        )}
        {cachedAt !== undefined && source === 'cache' && (
          <span className="text-[9px] text-slate-500 flex items-center gap-0.5 mt-0.5">
            <Clock className="h-2.5 w-2.5" />
            {cachedAt < 60 ? `${cachedAt}s ago` : `${Math.round(cachedAt / 60)}m ago`}
          </span>
        )}
      </div>
    </div>
  );
}
