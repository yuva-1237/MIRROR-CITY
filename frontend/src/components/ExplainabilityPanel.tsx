import { useState } from 'react';
import { HelpCircle, CheckSquare, Database, Activity, AlertCircle } from 'lucide-react';
import DataQualityBadge from './DataQualityBadge';

interface ExplainabilityPanelProps {
  masterRec: any;
  dataQuality?: any;   // data_quality field from the WS stream
  agentOutputs?: Record<string, any>;
}

export default function ExplainabilityPanel({ masterRec, dataQuality, agentOutputs }: ExplainabilityPanelProps) {
  const [activeTab, setActiveTab] = useState<'drivers' | 'chain'>('drivers');

  if (!masterRec) return null;

  const confidence   = masterRec.confidence_score ?? dataQuality?.overall_quality ?? 75;
  const weatherSrc   = dataQuality?.weather_source ?? 'simulation';
  const weatherConf  = dataQuality?.weather_confidence ?? 65;
  const anomalyCount = dataQuality?.anomaly_count ?? 0;
  const completeness = dataQuality?.data_completeness ?? 100;

  // Confidence ring color
  const ringColor = confidence >= 80 ? '#10b981' : confidence >= 60 ? '#f59e0b' : '#ef4444';

  // Aggregate telemetry drivers from recommendations, masterRec, and agentOutputs
  const collectedDrivers: any[] = [];

  // 1. From master recommendations
  if (masterRec.recommendations) {
    for (const rec of masterRec.recommendations) {
      if (rec.telemetry_driver) {
        collectedDrivers.push({
          ...rec.telemetry_driver,
          rec_title: rec.title,
          rec_priority: rec.priority
        });
      }
    }
  }

  // 2. From direct masterRec.telemetry_drivers
  if (masterRec.telemetry_drivers) {
    for (const d of masterRec.telemetry_drivers) {
      if (!collectedDrivers.some(x => x.metric_key === d.metric_key && x.entity === d.entity)) {
        collectedDrivers.push(d);
      }
    }
  }

  // 3. Fallback from agentOutputs if available
  if (agentOutputs) {
    for (const [domain, agent] of Object.entries(agentOutputs)) {
      if (agent.telemetry_drivers) {
        for (const d of agent.telemetry_drivers) {
          if (!collectedDrivers.some(x => x.metric_key === d.metric_key && x.entity === d.entity)) {
            collectedDrivers.push({ ...d, domain });
          }
        }
      }
    }
  }

  // Filtered telemetry drivers
  const filteredDrivers = collectedDrivers;

  return (
    <div className="glass-panel rounded-xl border border-brand-border/60 p-4 flex flex-col gap-3 font-sans">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-brand-border/40 pb-2">
        <div className="flex items-center gap-2">
          <HelpCircle className="h-5 w-5 text-brand-neonCyan" />
          <div>
            <h3 className="font-semibold text-xs tracking-wide text-slate-200 uppercase font-mono">
              EXPLAINABLE AI (XAI)
            </h3>
            <span className="text-[9px] text-slate-400 font-mono">Sensor Telemetry Attribution Engine</span>
          </div>
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
            <p className="text-[8px] text-slate-400 uppercase tracking-wider font-mono">Confidence</p>
            <p className="text-[10px] font-semibold text-slate-200">
              {confidence >= 80 ? 'High' : confidence >= 60 ? 'Medium' : 'Low'}
            </p>
          </div>
        </div>
      </div>

      {/* Mode Select Tabs & Data Quality bar */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex bg-slate-900/60 p-0.5 rounded-lg border border-brand-border/40 font-mono text-[9px]">
          <button
            onClick={() => setActiveTab('drivers')}
            className={`px-2 py-1 rounded transition ${activeTab === 'drivers' ? 'bg-brand-neonCyan/20 text-brand-neonCyan font-bold' : 'text-slate-400 hover:text-white'}`}
          >
            Telemetry Attribution ({filteredDrivers.length})
          </button>
          <button
            onClick={() => setActiveTab('chain')}
            className={`px-2 py-1 rounded transition ${activeTab === 'chain' ? 'bg-brand-neonCyan/20 text-brand-neonCyan font-bold' : 'text-slate-400 hover:text-white'}`}
          >
            Causal Reasoning Chain
          </button>
        </div>

        {/* Data Source badges */}
        <div className="flex items-center gap-1 text-[9px] font-mono">
          <DataQualityBadge source={weatherSrc} confidence={weatherConf} compact />
          <DataQualityBadge source="simulation" confidence={85} compact />
          {anomalyCount > 0 && (
            <span className="text-amber-400 flex items-center gap-0.5 ml-1">
              <AlertCircle className="h-3 w-3" /> {anomalyCount}
            </span>
          )}
        </div>
      </div>

      {/* Sensor Coverage Progress */}
      <div>
        <div className="flex justify-between text-[9px] text-slate-400 mb-0.5 font-mono">
          <span className="flex items-center gap-1">
            <Database className="h-3 w-3 text-slate-500" /> Sensor Coverage Completeness
          </span>
          <span className="font-bold text-slate-300">{completeness.toFixed(0)}%</span>
        </div>
        <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-700 ${completeness >= 90 ? 'bg-emerald-500' : completeness >= 70 ? 'bg-amber-500' : 'bg-red-500'}`}
            style={{ width: `${completeness}%` }}
          />
        </div>
      </div>

      {/* Main Tab View: Drivers vs Chain */}
      {activeTab === 'drivers' ? (
        <div className="space-y-2 flex-1 overflow-y-auto max-h-[170px] pr-1">
          {filteredDrivers.length > 0 ? (
            filteredDrivers.map((driver: any, idx: number) => {
              const isOver = (driver.comparison === '>') || (driver.delta_from_threshold && driver.delta_from_threshold.startsWith('+'));
              return (
                <div
                  key={idx}
                  className="bg-[#0b101b] border border-brand-border/60 hover:border-brand-neonCyan/40 p-2.5 rounded-lg space-y-1.5 transition-all text-xs"
                >
                  {/* Driver Header */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5 font-mono text-[10px]">
                      <Activity className={`h-3 w-3 ${isOver ? 'text-red-400' : 'text-emerald-400'}`} />
                      <span className="font-bold text-white">{driver.metric_label || driver.metric_key}</span>
                      <span className="text-slate-500">· {driver.entity}</span>
                    </div>
                    <span className={`text-[8px] font-mono uppercase font-bold px-1.5 py-0.2 rounded border ${
                      isOver
                        ? 'bg-red-500/10 text-red-400 border-red-500/30'
                        : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                    }`}>
                      {isOver ? `Exceeds Threshold (${driver.delta_from_threshold})` : 'Nominal'}
                    </span>
                  </div>

                  {/* Highlighted Exact Rationale Quote */}
                  <div className="bg-slate-900/80 border-l-2 border-brand-neonCyan p-1.5 rounded-r font-mono text-[10px] text-slate-200">
                    "{driver.rationale || `${driver.metric_label} at ${driver.observed_value}${driver.unit} triggered advisory recommendation.`}"
                  </div>

                  {/* Telemetry Comparison Metrics */}
                  <div className="flex items-center justify-between text-[9px] font-mono text-slate-400 pt-0.5">
                    <div className="flex items-center gap-3">
                      <div>
                        <span className="text-slate-500 block">Observed:</span>
                        <span className={`font-bold ${isOver ? 'text-red-400' : 'text-white'}`}>
                          {driver.observed_value} {driver.unit}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-500 block">Safe Threshold:</span>
                        <span className="font-bold text-slate-300">
                          {driver.threshold} {driver.unit}
                        </span>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-slate-500 block">Sensor Source:</span>
                      <span className="text-slate-400 truncate block max-w-[120px]">
                        {driver.sensor_source || 'Telemetry Node'}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="text-slate-400 text-xs italic py-4 text-center">
              All telemetry values within nominal regulatory tolerances.
            </div>
          )}
        </div>
      ) : (
        /* Explainability Cascade Chain */
        <div className="space-y-2 flex-1 overflow-y-auto max-h-[170px] pr-1">
          {masterRec.explainability_chain && masterRec.explainability_chain.length > 0 ? (
            masterRec.explainability_chain.map((step: string, idx: number) => (
              <div key={idx} className="flex gap-2 text-[10px] text-slate-300 items-start bg-slate-900/50 p-2 rounded border border-brand-border/30">
                <span className="text-brand-neonCyan font-mono font-bold shrink-0">STEP {idx + 1}:</span>
                <span className="leading-relaxed">{step}</span>
              </div>
            ))
          ) : (
            <div className="text-slate-400 text-xs italic py-4 text-center">
              All systems nominal. No active risk cascades detected.
            </div>
          )}
        </div>
      )}

      {/* Advisory Recommendations Footer */}
      <div className="border-t border-brand-border/40 pt-2">
        <span className="text-[9px] uppercase font-bold tracking-wider text-brand-neonOrange font-mono flex items-center gap-1">
          <CheckSquare className="h-3 w-3" /> MASTER ADVISORY RECOMMENDATIONS
        </span>
        <div className="mt-1.5 space-y-1.5 max-h-[75px] overflow-y-auto pr-1">
          {masterRec.recommendations && masterRec.recommendations.length > 0 ? (
            masterRec.recommendations.map((rec: any, idx: number) => (
              <div key={idx} className="bg-brand-neonOrange/10 border border-brand-neonOrange/20 p-2 rounded text-xs flex justify-between items-center">
                <div className="truncate mr-2">
                  <h4 className="font-semibold text-brand-neonOrange text-[11px] truncate">{rec.title}</h4>
                  <p className="text-[9px] text-slate-400 truncate">{rec.description}</p>
                </div>
                <span className={`text-[8px] font-mono font-bold uppercase px-1.5 py-0.5 rounded shrink-0 ${
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
