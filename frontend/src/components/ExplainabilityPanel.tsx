import { HelpCircle, CheckSquare, Database, AlertCircle } from 'lucide-react';
import DataQualityBadge from './DataQualityBadge';

interface ExplainabilityPanelProps {
  masterRec: any;
  dataQuality?: any;   // data_quality field from the WS stream
}

export default function ExplainabilityPanel({ masterRec, dataQuality }: ExplainabilityPanelProps) {
  if (!masterRec) return null;

  const confidence   = masterRec.confidence_score ?? dataQuality?.overall_quality ?? 75;
  const weatherSrc   = dataQuality?.weather_source ?? 'simulation';
  const weatherConf  = dataQuality?.weather_confidence ?? 65;
  const anomalyCount = dataQuality?.anomaly_count ?? 0;
  const completeness = dataQuality?.data_completeness ?? 100;

  // Confidence ring color
  const ringColor = confidence >= 80 ? '#10b981' : confidence >= 60 ? '#f59e0b' : '#ef4444';

  return (
    <div className="glass-panel rounded-xl border border-brand-border/60 p-4 flex flex-col gap-3">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-brand-border/40 pb-2">
        <div className="flex items-center gap-2">
          <HelpCircle className="h-5 w-5 text-brand-neonCyan" />
          <h3 className="font-semibold text-sm tracking-wide text-slate-200">REAL-TIME AI EXPLAINABILITY</h3>
        </div>
        {/* Confidence score ring */}
        <div className="flex items-center gap-2">
          <svg width="36" height="36" viewBox="0 0 36 36" className="shrink-0">
            <circle cx="18" cy="18" r="14" fill="none" stroke="#1e293b" strokeWidth="4" />
            <circle
              cx="18" cy="18" r="14"
              fill="none"
              stroke={ringColor}
              strokeWidth="4"
              strokeDasharray={`${(confidence / 100) * 87.96} 87.96`}
              strokeLinecap="round"
              transform="rotate(-90 18 18)"
              style={{ transition: 'stroke-dasharray 1s ease' }}
            />
            <text x="18" y="22" textAnchor="middle" fontSize="9" fill={ringColor} fontWeight="bold" fontFamily="monospace">
              {Math.round(confidence)}%
            </text>
          </svg>
          <div>
            <p className="text-[9px] text-slate-400 uppercase tracking-wider">Confidence</p>
            <p className="text-[10px] font-semibold text-slate-200">
              {confidence >= 80 ? 'High' : confidence >= 60 ? 'Medium' : 'Low'}
            </p>
          </div>
        </div>
      </div>

      {/* Data quality row */}
      <div className="flex flex-wrap items-center gap-2 text-[10px]">
        <span className="text-slate-500 uppercase tracking-wider font-bold">Data Sources:</span>
        <DataQualityBadge source={weatherSrc} confidence={weatherConf} compact />
        <span className="text-slate-400">Weather</span>
        <span className="text-brand-border mx-1">·</span>
        <DataQualityBadge source="simulation" confidence={85} compact />
        <span className="text-slate-400">Sensors</span>
        {anomalyCount > 0 && (
          <>
            <span className="text-brand-border mx-1">·</span>
            <span className="text-amber-400 flex items-center gap-0.5">
              <AlertCircle className="h-3 w-3" />
              {anomalyCount} anomal{anomalyCount === 1 ? 'y' : 'ies'} detected
            </span>
          </>
        )}
      </div>

      {/* Data completeness bar */}
      <div>
        <div className="flex justify-between text-[9px] text-slate-400 mb-0.5">
          <span className="flex items-center gap-1">
            <Database className="h-3 w-3" /> Sensor Coverage
          </span>
          <span className="font-mono font-bold text-slate-300">{completeness.toFixed(0)}%</span>
        </div>
        <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-700 ${completeness >= 90 ? 'bg-emerald-500' : completeness >= 70 ? 'bg-amber-500' : 'bg-red-500'}`}
            style={{ width: `${completeness}%` }}
          />
        </div>
      </div>

      {/* Explainability chain */}
      <div className="space-y-2 flex-1 overflow-y-auto max-h-[140px] pr-1">
        {masterRec.explainability_chain && masterRec.explainability_chain.length > 0 ? (
          masterRec.explainability_chain.map((step: string, idx: number) => (
            <div key={idx} className="flex gap-2 text-[11px] text-slate-300 items-start bg-slate-900/40 p-2 rounded border border-brand-border/20">
              <span className="text-brand-neonCyan font-mono font-bold shrink-0">STEP {idx + 1}:</span>
              <span>{step}</span>
            </div>
          ))
        ) : (
          <div className="text-slate-400 text-xs italic py-2">
            All systems normal. No active risk cascades detected.
          </div>
        )}
      </div>

      {/* Recommendations */}
      <div className="border-t border-brand-border/30 pt-2">
        <span className="text-[10px] uppercase font-bold tracking-wider text-brand-neonOrange font-mono flex items-center gap-1">
          <CheckSquare className="h-3.5 w-3.5" /> MASTER ADVISORY RECOMMENDATIONS
        </span>
        <div className="mt-2 space-y-1.5 max-h-[80px] overflow-y-auto pr-1">
          {masterRec.recommendations && masterRec.recommendations.length > 0 ? (
            masterRec.recommendations.map((rec: any, idx: number) => (
              <div key={idx} className="bg-brand-neonOrange/10 border border-brand-neonOrange/20 p-2 rounded text-xs flex justify-between items-center">
                <div>
                  <h4 className="font-semibold text-brand-neonOrange">{rec.title}</h4>
                  <p className="text-[10px] text-slate-400">{rec.description}</p>
                </div>
                <span className={`text-[8px] font-bold uppercase px-1.5 py-0.5 rounded shrink-0 ml-2 ${
                  rec.priority === 'High'   ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                  rec.priority === 'Medium' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
                                              'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                }`}>
                  {rec.priority}
                </span>
              </div>
            ))
          ) : (
            <div className="text-slate-500 text-xs italic">No recommendations pending.</div>
          )}
        </div>
      </div>
    </div>
  );
}
