import { useState } from 'react';
import { Eye, Brain, Cpu } from 'lucide-react';

interface AgentReasoningPanelProps {
  agentOutputs: Record<string, any>;
}

export default function AgentReasoningPanel({ agentOutputs }: AgentReasoningPanelProps) {
  const [selectedDomain, setSelectedDomain] = useState<string | null>(null);

  if (!agentOutputs || Object.keys(agentOutputs).length === 0) {
    return (
      <div className="glass-panel rounded-xl p-6 text-center text-slate-500">
        Initializing AI Agent Reasoning network...
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 border-b border-brand-border/40 pb-2">
        <Brain className="h-5 w-5 text-brand-neonPurple" />
        <h3 className="font-semibold text-sm tracking-wide text-slate-200 uppercase">Autonomous Agent Network</h3>
      </div>
      
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {Object.entries(agentOutputs).map(([domain, agent]) => {
          const isSelected = selectedDomain === domain;
          
          let alertColor = "bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]";
          let borderColor = "border-brand-border/40 hover:border-emerald-500/50";
          if (agent.alert_level === 'danger') {
            alertColor = "bg-red-500 animate-pulse shadow-[0_0_12px_rgba(239,68,68,0.7)]";
            borderColor = "border-red-500/40 hover:border-red-500";
          } else if (agent.alert_level === 'warning') {
            alertColor = "bg-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.5)]";
            borderColor = "border-amber-500/40 hover:border-amber-500";
          }

          return (
            <button
              key={domain}
              onClick={() => setSelectedDomain(isSelected ? null : domain)}
              className={`glass-panel p-3 rounded-lg border text-left transition duration-300 relative group flex flex-col justify-between h-[110px] ${borderColor} ${
                isSelected ? 'bg-brand-panel/90 scale-102 ring-1 ring-brand-neonPurple/50' : 'bg-brand-panel/40'
              }`}
            >
              <div className="flex justify-between items-start w-full">
                <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider font-mono">
                  {domain}
                </span>
                <div className="flex flex-col items-end gap-1">
                  <span className={`h-2.5 w-2.5 rounded-full ${alertColor}`} />
                  {/* Confidence score badge */}
                  {(() => {
                    const score = agent.confidence_score ??
                      (agent.alert_level === 'normal' ? 88 :
                       agent.alert_level === 'warning' ? 65 : 45);
                    return (
                      <span className={`text-[8px] font-bold font-mono px-1 py-0.5 rounded ${
                        score >= 80 ? 'text-emerald-400 bg-emerald-500/10' :
                        score >= 60 ? 'text-amber-400 bg-amber-500/10' :
                        'text-red-400 bg-red-500/10'
                      }`}>
                        {score}%
                      </span>
                    );
                  })()}
                </div>
              </div>
              
              <div className="mt-1">
                <h4 className="text-xs font-semibold text-slate-200 tracking-wide">
                  {agent.name}
                </h4>
                <p className="text-[9px] text-slate-400 truncate mt-0.5">
                  {agent.reasoning[agent.reasoning.length - 1] || "Stable telemetry."}
                </p>
              </div>

              {/* Hover indicator */}
              <span className="absolute bottom-1 right-2 opacity-0 group-hover:opacity-100 transition-opacity text-[8px] text-brand-neonPurple flex items-center gap-0.5">
                <Eye className="h-3 w-3" /> Inspect
              </span>
            </button>
          );
        })}
      </div>

      {/* Expanded Reasoning Panel — overflow-hidden prevents layout-shift scroll */}
      {selectedDomain && agentOutputs[selectedDomain] && (
        <div className="overflow-hidden">
        <div className="glass-panel p-4 rounded-xl border border-brand-neonPurple/30 bg-brand-panel/80 animate-fadeIn space-y-3">
          <div className="flex items-center justify-between border-b border-brand-border/40 pb-2">
            <div className="flex items-center gap-2">
              <Cpu className="h-4 w-4 text-brand-neonPurple" />
              <h4 className="font-semibold text-sm text-slate-100">
                {agentOutputs[selectedDomain].name} Reasoning Logs
              </h4>
            </div>
            <button 
              onClick={() => setSelectedDomain(null)}
              className="text-slate-500 hover:text-slate-200 text-xs font-mono"
            >
              [close]
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Reasoning Steps */}
            <div>
              <span className="text-[10px] uppercase font-bold tracking-wider text-brand-neonPurple font-mono">
                Cognitive Reasoning Chain
              </span>
              <ul className="list-disc pl-4 text-xs text-slate-300 space-y-1.5 mt-2">
                {agentOutputs[selectedDomain].reasoning.map((step: string, i: number) => (
                  <li key={i}>{step}</li>
                ))}
              </ul>
            </div>

            {/* Predictions & Actions */}
            <div className="space-y-3">
              <div>
                <span className="text-[10px] uppercase font-bold tracking-wider text-brand-neonCyan font-mono">
                  Future Horizon Projections
                </span>
                <div className="mt-2 bg-black/20 p-2.5 rounded border border-brand-border/40 text-xs">
                  <div className="flex justify-between items-center text-slate-300 mb-1">
                    <span className="font-mono text-slate-400">Next 5m:</span>
                    <span className="font-semibold">{agentOutputs[selectedDomain].predictions?.["5m"]?.description || "Stable conditions."}</span>
                  </div>
                  <div className="flex justify-between items-center text-slate-300">
                    <span className="font-mono text-slate-400">Next 1h:</span>
                    <span className="font-semibold">{agentOutputs[selectedDomain].predictions?.["1h"]?.description || "Stable conditions."}</span>
                  </div>
                </div>
              </div>

              {agentOutputs[selectedDomain].recommendations && agentOutputs[selectedDomain].recommendations.length > 0 && (
                <div>
                  <span className="text-[10px] uppercase font-bold tracking-wider text-brand-neonOrange font-mono">
                    Autonomous Response Recommendations
                  </span>
                  <div className="mt-2 space-y-2">
                    {agentOutputs[selectedDomain].recommendations.map((rec: any, idx: number) => (
                      <div key={idx} className="bg-brand-neonOrange/10 border border-brand-neonOrange/20 p-2.5 rounded text-xs flex flex-col gap-1">
                        <div className="flex justify-between items-center text-brand-neonOrange">
                          <span className="font-semibold">{rec.action}</span>
                          <span className="font-mono text-[9px] bg-brand-neonOrange/20 px-1.5 py-0.5 rounded">Benefit: {rec.estimated_benefit}</span>
                        </div>
                        <p className="text-slate-300 text-[11px]">{rec.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
        </div>
      )}
    </div>
  );
}
