import { useState } from 'react';
import { Scale, AlertTriangle, CheckCircle2, MessageSquare, ArrowRight, Sparkles } from 'lucide-react';

interface AgentCollaborationViewProps {
  collaborationLoop?: any;
  agentOutputs?: Record<string, any>;
}

export default function AgentCollaborationView({ collaborationLoop }: AgentCollaborationViewProps) {
  const [selectedConflictId, setSelectedConflictId] = useState<string | null>(null);

  const tradeOffReports: any[] = collaborationLoop?.trade_off_reports || [];
  const peerMessages: any[] = collaborationLoop?.peer_messages || [];
  const consensusIndex: number = collaborationLoop?.consensus_index ?? 92.0;

  // Consensus Ring Color
  const consensusColor = consensusIndex >= 85 ? '#10b981' : consensusIndex >= 70 ? '#f59e0b' : '#ef4444';

  return (
    <div className="glass-panel rounded-2xl border border-brand-border/80 bg-[#0c121e]/90 p-4 space-y-4 font-sans text-slate-100 shadow-2xl">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 border-b border-brand-border/40 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="bg-brand-neonPurple/20 p-2 rounded-xl border border-brand-neonPurple/40">
            <Scale className="h-5 w-5 text-brand-neonPurple" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold tracking-tight text-white uppercase font-mono">
                Multi-Agent Conflict Resolver & Collaboration Loop
              </h2>
              <span className="text-[9px] font-mono font-bold bg-brand-neonPurple/20 text-brand-neonPurple px-2 py-0.5 rounded-full border border-brand-neonPurple/30 flex items-center gap-1">
                <Sparkles className="h-2.5 w-2.5" /> AI ARBITRATION
              </span>
            </div>
            <p className="text-[10px] text-slate-400 font-mono">
              Autonomous negotiation cycle arbitrating competing urban priorities & generating trade-off reports
            </p>
          </div>
        </div>

        {/* Multi-Agent Consensus Meter */}
        <div className="flex items-center gap-3 bg-slate-900/80 px-3 py-1.5 rounded-xl border border-brand-border/60">
          <svg width="38" height="38" viewBox="0 0 36 36" className="shrink-0">
            <circle cx="18" cy="18" r="14" fill="none" stroke="#1e293b" strokeWidth="3.5" />
            <circle
              cx="18" cy="18" r="14"
              fill="none"
              stroke={consensusColor}
              strokeWidth="3.5"
              strokeDasharray={`${(consensusIndex / 100) * 87.96} 87.96`}
              strokeLinecap="round"
              transform="rotate(-90 18 18)"
              style={{ transition: 'stroke-dasharray 1s ease' }}
            />
            <text x="18" y="21.5" textAnchor="middle" fontSize="8" fill={consensusColor} fontWeight="bold" fontFamily="monospace">
              {Math.round(consensusIndex)}%
            </text>
          </svg>
          <div>
            <span className="text-[8px] uppercase tracking-wider font-mono text-slate-400 block leading-none">
              Consensus Index
            </span>
            <span className="text-xs font-bold font-mono text-white">
              {consensusIndex >= 85 ? 'High Alignment' : 'Compromise Required'}
            </span>
          </div>
        </div>
      </div>

      {/* Main Grid: Active Conflicts vs Inter-Agent Message Log */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        
        {/* Left Column: Quantified Trade-Off Reports (8 cols) */}
        <div className="lg:col-span-8 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono flex items-center gap-1.5">
              <AlertTriangle className="h-3.5 w-3.5 text-brand-neonOrange" />
              Active Trade-Off Arbitrations ({tradeOffReports.length})
            </span>
            <span className="text-[10px] text-slate-400 font-mono">
              Status: <span className="text-brand-neonCyan font-bold">Resolved with Mitigations</span>
            </span>
          </div>

          {tradeOffReports.length > 0 ? (
            <div className="space-y-3">
              {tradeOffReports.map((report: any) => {
                const isSelected = selectedConflictId === report.conflict_id || tradeOffReports.length === 1;
                return (
                  <div
                    key={report.conflict_id}
                    className={`rounded-xl border transition-all duration-300 overflow-hidden ${
                      isSelected
                        ? 'bg-gradient-to-b from-[#111827] to-[#0d131f] border-brand-neonPurple/50 shadow-xl shadow-brand-neonPurple/5'
                        : 'bg-slate-900/50 border-brand-border/60 hover:border-brand-border'
                    }`}
                  >
                    {/* Report Card Header */}
                    <div
                      onClick={() => setSelectedConflictId(isSelected && tradeOffReports.length > 1 ? null : report.conflict_id)}
                      className="p-3.5 cursor-pointer flex flex-col sm:flex-row justify-between sm:items-center gap-2 border-b border-brand-border/40"
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-[9px] font-mono font-bold bg-brand-neonOrange/20 text-brand-neonOrange px-1.5 py-0.5 rounded border border-brand-neonOrange/30">
                            {report.conflict_id}
                          </span>
                          <h4 className="text-xs font-bold text-white tracking-wide">
                            {report.title}
                          </h4>
                        </div>
                        <p className="text-[10px] text-slate-400 mt-1">
                          {report.dispute_description}
                        </p>
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        <span className="text-[9px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                          {report.consensus_score}% Agreement
                        </span>
                      </div>
                    </div>

                    {/* Expandable Dispute & Compromise Analysis */}
                    <div className="p-4 space-y-3">
                      {/* Competing Parties Duel */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {/* Party A: e.g. Economy AI */}
                        <div className="bg-slate-950/70 border border-brand-neonCyan/30 p-3 rounded-lg space-y-1.5">
                          <div className="flex items-center justify-between text-[10px] font-mono font-bold">
                            <span className="text-brand-neonCyan">{report.party_a.agent}</span>
                            <span className="text-slate-400 uppercase text-[8px]">Primary Stance</span>
                          </div>
                          <p className="text-xs font-bold text-slate-200">{report.party_a.stance}</p>
                          <p className="text-[10px] text-slate-300">Action: {report.party_a.desired_action}</p>
                          <div className="text-[10px] text-emerald-400 font-mono bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                            Upside: {report.party_a.benefit_projection}
                          </div>
                          {report.party_a.telemetry_driver && (
                            <div className="text-[9px] text-slate-400 font-mono mt-1 border-t border-brand-border/40 pt-1">
                              Driven by: <span className="text-slate-200">{report.party_a.telemetry_driver.observed_value}{report.party_a.telemetry_driver.unit}</span> (Threshold: {report.party_a.telemetry_driver.threshold}{report.party_a.telemetry_driver.unit})
                            </div>
                          )}
                        </div>

                        {/* Party B: e.g. Flood AI */}
                        <div className="bg-slate-950/70 border border-red-500/30 p-3 rounded-lg space-y-1.5">
                          <div className="flex items-center justify-between text-[10px] font-mono font-bold">
                            <span className="text-red-400">{report.party_b.agent}</span>
                            <span className="text-slate-400 uppercase text-[8px]">Counter Objection</span>
                          </div>
                          <p className="text-xs font-bold text-slate-200">{report.party_b.stance}</p>
                          <p className="text-[10px] text-slate-300">Action: {report.party_b.desired_action}</p>
                          <div className="text-[10px] text-red-400 font-mono bg-red-500/10 px-2 py-0.5 rounded border border-red-500/20">
                            Risk Flag: {report.party_b.risk_projection}
                          </div>
                          {report.party_b.telemetry_driver && (
                            <div className="text-[9px] text-slate-400 font-mono mt-1 border-t border-brand-border/40 pt-1">
                              Driven by: <span className="text-slate-200">{report.party_b.telemetry_driver.observed_value}{report.party_b.telemetry_driver.unit}</span> (Threshold: {report.party_b.telemetry_driver.threshold}{report.party_b.telemetry_driver.unit})
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Quantified Trade-Off Balance */}
                      {report.quantified_trade_offs && (
                        <div className="bg-slate-900/60 p-2.5 rounded-lg border border-brand-border/40 text-[10px] font-mono grid grid-cols-1 sm:grid-cols-3 gap-2">
                          <div>
                            <span className="text-slate-500 block">Economic Value Added:</span>
                            <span className="font-bold text-emerald-400">{report.quantified_trade_offs.economic_gain_raw || report.quantified_trade_offs.traffic_improvement}</span>
                          </div>
                          <div>
                            <span className="text-slate-500 block">Ecological/Risk Penalty:</span>
                            <span className="font-bold text-amber-400">{report.quantified_trade_offs.flood_damage_risk_raw || report.quantified_trade_offs.emissions_exposure}</span>
                          </div>
                          <div>
                            <span className="text-slate-500 block">Net Synthesized Balance:</span>
                            <span className="font-bold text-brand-neonCyan">{report.quantified_trade_offs.net_balance}</span>
                          </div>
                        </div>
                      )}

                      {/* Arbitrated Solution (The Coordinator's Compromise) */}
                      <div className="bg-gradient-to-r from-brand-neonPurple/20 via-blue-950/40 to-slate-950 p-3 rounded-lg border border-brand-neonPurple/40">
                        <span className="text-[9px] font-mono font-bold uppercase tracking-wider text-brand-neonPurple block mb-1">
                          Coordinator Arbitrated Compromise Policy
                        </span>
                        <p className="text-xs font-semibold text-white">
                          {report.arbitrated_solution}
                        </p>

                        {/* Action Items */}
                        {report.actionable_mitigations && (
                          <div className="mt-2 space-y-1">
                            {report.actionable_mitigations.map((item: string, i: number) => (
                              <div key={i} className="flex items-center gap-1.5 text-[10px] text-slate-300">
                                <CheckCircle2 className="h-3 w-3 text-emerald-400 shrink-0" />
                                <span>{item}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="bg-slate-900/30 border border-dashed border-brand-border/60 rounded-xl p-8 text-center text-xs text-slate-400 font-mono">
              All 10 agents operating in mutual consensus. No active priority disputes detected.
            </div>
          )}
        </div>

        {/* Right Column: Inter-Agent Negotiation Message Bus (4 cols) */}
        <div className="lg:col-span-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono flex items-center gap-1.5">
              <MessageSquare className="h-3.5 w-3.5 text-brand-neonCyan" />
              Inter-Agent Signals ({peerMessages.length})
            </span>
            <span className="text-[9px] text-slate-400 font-mono">Live Protocol</span>
          </div>

          <div className="space-y-2 max-h-[360px] overflow-y-auto pr-1">
            {peerMessages.length > 0 ? (
              peerMessages.map((msg: any, idx: number) => (
                <div
                  key={idx}
                  className={`p-2.5 rounded-lg border text-xs font-mono space-y-1 ${
                    msg.urgency === 'critical'
                      ? 'bg-red-950/30 border-red-500/40 text-red-200'
                      : 'bg-slate-900/60 border-brand-border/40 text-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between text-[9px] font-bold">
                    <span className="text-brand-neonCyan">{msg.sender}</span>
                    <ArrowRight className="h-2.5 w-2.5 text-slate-500" />
                    <span className="text-brand-neonPurple">{msg.recipient}</span>
                  </div>
                  <p className="text-[10px] leading-relaxed text-slate-300">
                    {msg.message}
                  </p>
                </div>
              ))
            ) : (
              <div className="bg-slate-900/30 border border-brand-border/30 rounded-lg p-6 text-center text-xs text-slate-500 italic">
                Peer messaging bus quiet.
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
