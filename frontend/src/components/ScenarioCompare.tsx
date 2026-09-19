import { useState, useEffect, useMemo } from 'react';
import { 
  ArrowLeftRight, FileDown, TrendingUp, TrendingDown, 
  Sparkles, Building, DollarSign, Clock, ShieldAlert, Leaf, Car, Copy, CheckCheck, Loader2
} from 'lucide-react';
import { apiFetch } from '../lib/api';

interface ScenarioCompareProps {
  scenarios: any[];
  authToken: string;
}

export default function ScenarioCompare({ scenarios, authToken }: ScenarioCompareProps) {
  const [selectedIdA, setSelectedIdA] = useState<number | null>(null);
  const [selectedIdB, setSelectedIdB] = useState<number | null>(null);
  const [comparisonData, setComparisonData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  // Initialize selection on mount: A = baseline, B = first non-baseline
  useEffect(() => {
    if (scenarios && scenarios.length > 0) {
      const baseline = scenarios.find(s => s.status === 'baseline') || scenarios[0];
      const alternative = scenarios.find(s => s.id !== baseline.id) || scenarios[0];
      setSelectedIdA(baseline.id);
      setSelectedIdB(alternative.id);
    }
  }, [scenarios]);

  // Fetch comparison metrics whenever selection changes
  useEffect(() => {
    const fetchComparison = async () => {
      if (!selectedIdA || !selectedIdB) return;
      setLoading(true);
      try {
        const ids = Array.from(new Set([selectedIdA, selectedIdB])).join(',');
        const data = await apiFetch<any[]>(`/api/simulations/compare?ids=${ids}`, {
          token: authToken
        });
        setComparisonData(data);
      } catch (err) {
        console.error('[ScenarioCompare] Compare failed:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchComparison();
  }, [selectedIdA, selectedIdB, authToken]);

  const scenarioA = useMemo(() => comparisonData.find(s => s.scenario_id === selectedIdA), [comparisonData, selectedIdA]);
  const scenarioB = useMemo(() => comparisonData.find(s => s.scenario_id === selectedIdB), [comparisonData, selectedIdB]);

  // Helper to compute delta between Scenario B and Scenario A
  const computeDelta = (key: string, lowerIsBetter = false) => {
    if (!scenarioA?.metrics || !scenarioB?.metrics) return null;
    const valA = scenarioA.metrics[key] ?? 0;
    const valB = scenarioB.metrics[key] ?? 0;
    const diff = valB - valA;
    const pct = valA !== 0 ? ((diff / valA) * 100) : 0;
    const improved = lowerIsBetter ? (diff < 0) : (diff > 0);
    const degraded = lowerIsBetter ? (diff > 0) : (diff < 0);
    return {
      valA,
      valB,
      diff,
      pct,
      improved,
      degraded,
      isNeutral: Math.abs(diff) < 0.001
    };
  };

  // Asset differences between B and A
  const assetDiff = useMemo(() => {
    const elementsA: any[] = scenarioA?.elements || [];
    const elementsB: any[] = scenarioB?.elements || [];
    
    // Group elements by type
    const countsA: Record<string, number> = {};
    const countsB: Record<string, number> = {};
    for (const e of elementsA) countsA[e.type] = (countsA[e.type] || 0) + 1;
    for (const e of elementsB) countsB[e.type] = (countsB[e.type] || 0) + 1;

    const allTypes = Array.from(new Set([...Object.keys(countsA), ...Object.keys(countsB)]));
    const deltas: { type: string; diff: number; countA: number; countB: number }[] = [];

    for (const t of allTypes) {
      const cA = countsA[t] || 0;
      const cB = countsB[t] || 0;
      deltas.push({ type: t, diff: cB - cA, countA: cA, countB: cB });
    }

    return deltas;
  }, [scenarioA, scenarioB]);

  // Export to CSV / Excel-compatible format
  const exportToCSV = () => {
    if (!scenarioA || !scenarioB) return;
    const rows = [
      ['Metric', `${scenarioA.name} (Scenario A)`, `${scenarioB.name} (Scenario B)`, 'Delta Value', 'Delta %'],
      ['Traffic Score (0-100)', scenarioA.metrics.traffic_score, scenarioB.metrics.traffic_score, (scenarioB.metrics.traffic_score - scenarioA.metrics.traffic_score).toFixed(1), `${computeDelta('traffic_score')?.pct.toFixed(1)}%`],
      ['Commute Time (mins)', scenarioA.metrics.travel_time, scenarioB.metrics.travel_time, (scenarioB.metrics.travel_time - scenarioA.metrics.travel_time).toFixed(1), `${computeDelta('travel_time', true)?.pct.toFixed(1)}%`],
      ['Emergency Response (mins)', scenarioA.metrics.emergency_response, scenarioB.metrics.emergency_response, (scenarioB.metrics.emergency_response - scenarioA.metrics.emergency_response).toFixed(1), `${computeDelta('emergency_response', true)?.pct.toFixed(1)}%`],
      ['Population Coverage (%)', scenarioA.metrics.population_coverage, scenarioB.metrics.population_coverage, (scenarioB.metrics.population_coverage - scenarioA.metrics.population_coverage).toFixed(1), `${computeDelta('population_coverage')?.pct.toFixed(1)}%`],
      ['Carbon Footprint (Tons)', scenarioA.metrics.carbon_footprint, scenarioB.metrics.carbon_footprint, (scenarioB.metrics.carbon_footprint - scenarioA.metrics.carbon_footprint).toFixed(1), `${computeDelta('carbon_footprint', true)?.pct.toFixed(1)}%`],
      ['Sustainability Score (0-100)', scenarioA.metrics.sustainability_score, scenarioB.metrics.sustainability_score, (scenarioB.metrics.sustainability_score - scenarioA.metrics.sustainability_score).toFixed(1), `${computeDelta('sustainability_score')?.pct.toFixed(1)}%`],
      ['Disaster Risk Level', scenarioA.metrics.risk_level, scenarioB.metrics.risk_level, (scenarioB.metrics.risk_level - scenarioA.metrics.risk_level).toFixed(1), `${computeDelta('risk_level', true)?.pct.toFixed(1)}%`],
      ['Estimated Cost ($)', scenarioA.metrics.cost, scenarioB.metrics.cost, (scenarioB.metrics.cost - scenarioA.metrics.cost).toFixed(0), 'N/A'],
      ['Net ROI (%)', scenarioA.metrics.roi, scenarioB.metrics.roi, (scenarioB.metrics.roi - scenarioA.metrics.roi).toFixed(1), `${computeDelta('roi')?.pct.toFixed(1)}%`]
    ];

    const csvContent = "data:text/csv;charset=utf-8," + rows.map(e => e.join(",")).join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `MirrorCity_Planner_Comparison_${scenarioA.name}_vs_${scenarioB.name}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Copy summary clipboard
  const copyExecutiveSummary = () => {
    if (!scenarioA || !scenarioB) return;
    const trfDelta = computeDelta('traffic_score');
    const timeDelta = computeDelta('travel_time', true);
    const costDiff = (scenarioB.metrics.cost ?? 0) - (scenarioA.metrics.cost ?? 0);
    const summary = `Mirror City Planning Briefing: Comparing "${scenarioA.name}" vs "${scenarioB.name}". Traffic Congestion: ${trfDelta?.pct.toFixed(1)}% delta. Commute Time: ${timeDelta?.diff.toFixed(1)} mins. Capital Outlay Diff: $${costDiff.toLocaleString()}.`;
    navigator.clipboard.writeText(summary);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Metrics list to render
  const metricConfigs = [
    { label: 'Traffic Congestion (0-100)', key: 'traffic_score', icon: Car, lowerIsBetter: false, unit: 'pts' },
    { label: 'Average Commute Delay', key: 'travel_time', icon: Clock, lowerIsBetter: true, unit: 'mins' },
    { label: 'Emergency Response SLA', key: 'emergency_response', icon: ShieldAlert, lowerIsBetter: true, unit: 'mins' },
    { label: 'Healthcare Catchment', key: 'population_coverage', icon: Building, lowerIsBetter: false, unit: '%' },
    { label: 'Carbon Emissions Index', key: 'carbon_footprint', icon: Leaf, lowerIsBetter: true, unit: 'Tons CO2' },
    { label: 'Sustainability Score', key: 'sustainability_score', icon: Sparkles, lowerIsBetter: false, unit: 'pts' },
    { label: 'Disaster Inundation Risk', key: 'risk_level', icon: ShieldAlert, lowerIsBetter: true, unit: 'index' },
    { label: 'Net Capital Investment', key: 'cost', icon: DollarSign, lowerIsBetter: true, unit: '$', isCurrency: true },
    { label: 'Projected 5Y ROI', key: 'roi', icon: TrendingUp, lowerIsBetter: false, unit: '%' }
  ];

  return (
    <div className="w-full space-y-6 select-none font-sans">
      {/* Top Header & Export Toolbar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass-panel p-4 rounded-2xl border border-brand-border/80 bg-[#0c121e]/90 shadow-xl">
        <div>
          <div className="flex items-center gap-2">
            <div className="bg-brand-neonPurple/20 p-2 rounded-xl border border-brand-neonPurple/40">
              <ArrowLeftRight className="h-5 w-5 text-brand-neonPurple" />
            </div>
            <div>
              <h2 className="text-base font-bold tracking-tight text-white uppercase font-mono flex items-center gap-2">
                Scenario A/B Planner Comparison
                {loading && <Loader2 className="h-4 w-4 text-brand-neonCyan animate-spin" />}
              </h2>
              <p className="text-xs text-slate-400 font-mono">
                Side-by-side comparative dashboard with automated delta variance & asset diff matrix
              </p>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={copyExecutiveSummary}
            disabled={!scenarioA || !scenarioB}
            className="px-3 py-2 bg-slate-900/80 hover:bg-slate-800 border border-brand-border text-slate-300 hover:text-white rounded-xl text-xs font-mono font-semibold flex items-center gap-1.5 transition"
          >
            {copied ? <CheckCheck className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
            {copied ? 'Copied Briefing' : 'Copy Summary'}
          </button>
          <button
            onClick={exportToCSV}
            disabled={!scenarioA || !scenarioB}
            className="px-3.5 py-2 bg-brand-neonCyan/10 hover:bg-brand-neonCyan/20 border border-brand-neonCyan/40 text-brand-neonCyan rounded-xl text-xs font-mono font-bold flex items-center gap-1.5 transition shadow-lg shadow-brand-neonCyan/5"
          >
            <FileDown className="h-3.5 w-3.5" />
            Export Excel / CSV
          </button>
        </div>
      </div>

      {/* Selector Dropdown Bar */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Scenario A Selector */}
        <div className="bg-[#101625]/80 border border-brand-border/80 p-3.5 rounded-xl space-y-2">
          <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-brand-neonCyan block">
            BASELINE / BENCHMARK (SCENARIO A)
          </span>
          <select
            value={selectedIdA ?? ''}
            onChange={(e) => setSelectedIdA(Number(e.target.value))}
            className="w-full bg-slate-900 border border-brand-border/60 text-white rounded-lg p-2.5 text-xs font-mono focus:outline-none focus:border-brand-neonCyan"
          >
            {scenarios.map(s => (
              <option key={s.id} value={s.id}>
                {s.name} ({s.status.toUpperCase()} • {s.elements?.length || 0} Assets)
              </option>
            ))}
          </select>
        </div>

        {/* Scenario B Selector */}
        <div className="bg-[#101625]/80 border border-brand-border/80 p-3.5 rounded-xl space-y-2">
          <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-brand-neonPurple block">
            PROPOSED INTERVENTION (SCENARIO B)
          </span>
          <select
            value={selectedIdB ?? ''}
            onChange={(e) => setSelectedIdB(Number(e.target.value))}
            className="w-full bg-slate-900 border border-brand-border/60 text-white rounded-lg p-2.5 text-xs font-mono focus:outline-none focus:border-brand-neonPurple"
          >
            {scenarios.map(s => (
              <option key={s.id} value={s.id}>
                {s.name} ({s.status.toUpperCase()} • {s.elements?.length || 0} Assets)
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Executive Diff Summary Banner */}
      {scenarioA && scenarioB && (
        <div className="bg-gradient-to-r from-brand-neonPurple/15 via-[#131b2e] to-brand-neonCyan/15 border border-brand-neonPurple/40 p-4 rounded-2xl shadow-xl space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-brand-neonPurple flex items-center gap-1.5">
              <Sparkles className="h-4 w-4" /> Urban Planners Executive Synthesis
            </span>
            <span className="text-[10px] font-mono bg-white/10 px-2 py-0.5 rounded text-slate-300">
              Delta Variance (B relative to A)
            </span>
          </div>

          <p className="text-xs font-semibold text-slate-200 leading-relaxed font-mono">
            {computeDelta('travel_time', true)?.improved ? (
              <span>
                PROPOSED INTERVENTION: Reduces travel delay by <span className="text-emerald-400 font-bold">{Math.abs(computeDelta('travel_time', true)?.diff || 0).toFixed(1)} mins</span> while maintaining{' '}
                <span className="text-brand-neonCyan font-bold">{scenarioB.metrics.population_coverage}%</span> medical coverage.
              </span>
            ) : (
              <span>
                PROPOSED INTERVENTION: Focuses on commercial density with a net cost differential of{' '}
                <span className="text-amber-400 font-bold">${((scenarioB.metrics.cost || 0) - (scenarioA.metrics.cost || 0)).toLocaleString()}</span>.
              </span>
            )}
          </p>

          {/* 4 Flagship Delta Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 pt-1">
            {/* Traffic Congestion Delta */}
            {(() => {
              const d = computeDelta('traffic_score');
              return (
                <div className="bg-slate-950/70 p-3 rounded-xl border border-brand-border/60">
                  <span className="text-[10px] text-slate-400 font-mono block">Traffic Flow</span>
                  <div className="flex items-center gap-1.5 mt-1">
                    {d?.improved ? <TrendingUp className="h-4 w-4 text-emerald-400" /> : <TrendingDown className="h-4 w-4 text-red-400" />}
                    <span className={`text-base font-bold font-mono ${d?.improved ? 'text-emerald-400' : 'text-red-400'}`}>
                      {d?.diff && d.diff > 0 ? `+${d.diff.toFixed(1)}` : d?.diff?.toFixed(1)} pts
                    </span>
                  </div>
                  <span className="text-[9px] text-slate-500 font-mono">{d?.pct && d.pct > 0 ? `+${d.pct.toFixed(1)}%` : `${d?.pct?.toFixed(1)}%`} variance</span>
                </div>
              );
            })()}

            {/* Commute Time Delta */}
            {(() => {
              const d = computeDelta('travel_time', true);
              return (
                <div className="bg-slate-950/70 p-3 rounded-xl border border-brand-border/60">
                  <span className="text-[10px] text-slate-400 font-mono block">Average Commute</span>
                  <div className="flex items-center gap-1.5 mt-1">
                    {d?.improved ? <TrendingDown className="h-4 w-4 text-emerald-400" /> : <TrendingUp className="h-4 w-4 text-red-400" />}
                    <span className={`text-base font-bold font-mono ${d?.improved ? 'text-emerald-400' : 'text-red-400'}`}>
                      {d?.diff?.toFixed(1)} mins
                    </span>
                  </div>
                  <span className="text-[9px] text-slate-500 font-mono">{d?.improved ? 'Commuters save time' : 'Additional travel delay'}</span>
                </div>
              );
            })()}

            {/* Carbon Delta */}
            {(() => {
              const d = computeDelta('carbon_footprint', true);
              return (
                <div className="bg-slate-950/70 p-3 rounded-xl border border-brand-border/60">
                  <span className="text-[10px] text-slate-400 font-mono block">Carbon Output</span>
                  <div className="flex items-center gap-1.5 mt-1">
                    {d?.improved ? <TrendingDown className="h-4 w-4 text-emerald-400" /> : <TrendingUp className="h-4 w-4 text-amber-400" />}
                    <span className={`text-base font-bold font-mono ${d?.improved ? 'text-emerald-400' : 'text-amber-400'}`}>
                      {d?.diff && d.diff > 0 ? `+${d.diff.toFixed(0)}` : d?.diff?.toFixed(0)} Tons
                    </span>
                  </div>
                  <span className="text-[9px] text-slate-500 font-mono">{d?.improved ? 'Reduced emissions' : 'Higher emissions'}</span>
                </div>
              );
            })()}

            {/* Capital Cost Diff */}
            {(() => {
              const diffCost = (scenarioB.metrics.cost ?? 0) - (scenarioA.metrics.cost ?? 0);
              return (
                <div className="bg-slate-950/70 p-3 rounded-xl border border-brand-border/60">
                  <span className="text-[10px] text-slate-400 font-mono block">Capital Delta</span>
                  <div className="flex items-center gap-1 mt-1">
                    <DollarSign className="h-4 w-4 text-brand-neonCyan" />
                    <span className="text-base font-bold font-mono text-white">
                      {diffCost >= 0 ? `+$${diffCost.toLocaleString()}` : `-$${Math.abs(diffCost).toLocaleString()}`}
                    </span>
                  </div>
                  <span className="text-[9px] text-slate-500 font-mono">Net budget variance</span>
                </div>
              );
            })()}
          </div>
        </div>
      )}

      {/* Side-by-Side Dual Column Metric Grid */}
      {scenarioA && scenarioB ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          
          {/* Column A: Scenario A Dashboard */}
          <div className="bg-[#101625]/80 border border-brand-border rounded-2xl p-5 space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-brand-border/50 pb-3">
              <div>
                <span className="text-[9px] uppercase font-mono font-bold px-2 py-0.5 rounded bg-brand-neonCyan/10 text-brand-neonCyan border border-brand-neonCyan/30">
                  SCENARIO A • {scenarioA.status.toUpperCase()}
                </span>
                <h3 className="text-sm font-bold text-white mt-1">{scenarioA.name}</h3>
              </div>
              <span className="text-xs font-mono text-slate-400">{scenarioA.element_count} Assets</span>
            </div>

            {/* Metrics Bars */}
            <div className="space-y-3 font-mono">
              {metricConfigs.map(m => {
                const val = scenarioA.metrics[m.key];
                return (
                  <div key={m.key} className="space-y-1">
                    <div className="flex justify-between text-xs text-slate-300">
                      <span className="flex items-center gap-1.5 text-slate-400">
                        <m.icon className="h-3.5 w-3.5 text-slate-500" /> {m.label}
                      </span>
                      <span className="font-bold text-white">
                        {m.isCurrency ? `$${Number(val).toLocaleString()}` : `${val} ${m.unit}`}
                      </span>
                    </div>
                    {/* Visual Bar */}
                    <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                      <div
                        className="bg-brand-neonCyan h-full rounded-full transition-all duration-500"
                        style={{ width: `${Math.min(100, Math.max(5, (val / (m.key === 'cost' ? 50000 : 100)) * 100))}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Column B: Scenario B Dashboard with Comparative Deltas */}
          <div className="bg-[#101625]/80 border border-brand-neonPurple/50 rounded-2xl p-5 space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-brand-border/50 pb-3">
              <div>
                <span className="text-[9px] uppercase font-mono font-bold px-2 py-0.5 rounded bg-brand-neonPurple/20 text-brand-neonPurple border border-brand-neonPurple/40">
                  SCENARIO B • {scenarioB.status.toUpperCase()}
                </span>
                <h3 className="text-sm font-bold text-white mt-1">{scenarioB.name}</h3>
              </div>
              <span className="text-xs font-mono text-slate-400">{scenarioB.element_count} Assets</span>
            </div>

            {/* Metrics Bars with Relative Deltas */}
            <div className="space-y-3 font-mono">
              {metricConfigs.map(m => {
                const val = scenarioB.metrics[m.key];
                const d = computeDelta(m.key, m.lowerIsBetter);
                return (
                  <div key={m.key} className="space-y-1">
                    <div className="flex justify-between text-xs text-slate-300">
                      <span className="flex items-center gap-1.5 text-slate-400">
                        <m.icon className="h-3.5 w-3.5 text-brand-neonPurple" /> {m.label}
                      </span>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-white">
                          {m.isCurrency ? `$${Number(val).toLocaleString()}` : `${val} ${m.unit}`}
                        </span>
                        {d && !d.isNeutral && (
                          <span className={`text-[10px] font-bold px-1.5 py-0.2 rounded border ${
                            d.improved
                              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                              : 'bg-red-500/10 text-red-400 border-red-500/30'
                          }`}>
                            {d.diff > 0 ? `+${d.diff.toFixed(1)}` : d.diff.toFixed(1)}
                          </span>
                        )}
                      </div>
                    </div>
                    {/* Visual Bar */}
                    <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                      <div
                        className="bg-brand-neonPurple h-full rounded-full transition-all duration-500"
                        style={{ width: `${Math.min(100, Math.max(5, (val / (m.key === 'cost' ? 50000 : 100)) * 100))}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

        </div>
      ) : (
        <div className="p-12 text-center bg-slate-900/50 border border-dashed border-brand-border rounded-2xl text-xs text-slate-500 font-mono">
          Loading scenario comparison matrices...
        </div>
      )}

      {/* Infrastructure Asset Delta Diff Table */}
      {scenarioA && scenarioB && (
        <div className="bg-[#101625]/80 border border-brand-border/80 rounded-2xl p-5 space-y-3 glass-panel">
          <div className="flex items-center justify-between border-b border-brand-border/50 pb-2">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
              <Building className="h-4 w-4 text-brand-neonCyan" /> Infrastructure Asset Delta Diff
            </span>
            <span className="text-[10px] font-mono text-slate-400">
              Elements added, modified, or preserved in Scenario B
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono">
            {assetDiff.length > 0 ? (
              assetDiff.map(item => (
                <div key={item.type} className="bg-slate-950/60 p-3 rounded-xl border border-brand-border/60 flex items-center justify-between">
                  <div>
                    <span className="text-[10px] uppercase text-slate-400 font-bold block">{item.type.replace('_', ' ')}</span>
                    <span className="text-xs text-slate-200">
                      {item.countA} → {item.countB}
                    </span>
                  </div>
                  <span className={`text-xs font-bold px-2 py-1 rounded border ${
                    item.diff > 0
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                      : item.diff < 0
                      ? 'bg-red-500/10 text-red-400 border-red-500/30'
                      : 'bg-white/5 text-slate-400 border-white/10'
                  }`}>
                    {item.diff > 0 ? `+${item.diff}` : item.diff === 0 ? '0' : item.diff}
                  </span>
                </div>
              ))
            ) : (
              <div className="col-span-4 text-center py-4 text-slate-500 text-xs italic">
                Zero infrastructure element variances between Scenario A and Scenario B.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
