import { useState, useEffect } from 'react';
import { ArrowLeftRight, Check, Layers } from 'lucide-react';

interface ScenarioCompareProps {
  scenarios: any[];
  authToken: string;
}

export default function ScenarioCompare({ scenarios, authToken }: ScenarioCompareProps) {
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [comparisonData, setComparisonData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const toggleSelect = (id: number) => {
    setSelectedIds(prev => 
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const handleCompare = async () => {
    if (selectedIds.length === 0) return;
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/api/simulations/compare?ids=${selectedIds.join(',')}`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      if (!response.ok) throw new Error("Comparison query failed");
      const data = await response.json();
      setComparisonData(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Run automatically when scenarios list changes or IDs update
  useEffect(() => {
    if (selectedIds.length > 0) {
      handleCompare();
    } else {
      setComparisonData([]);
    }
  }, [selectedIds]);

  const renderMetricRow = (label: string, key: string, isCost = false, isPercent = false, lowerIsBetter = false) => {
    return (
      <tr className="border-b border-brand-border hover:bg-white/5 transition-all">
        <td className="py-3 px-4 text-xs font-semibold text-slate-400">{label}</td>
        {comparisonData.map((data, idx) => {
          const val = data.metrics[key];
          if (val === undefined) return <td key={idx} className="py-3 px-4 text-xs text-slate-600">N/A</td>;
          
          let colorClass = "text-white";
          // Quick styling check relative to other columns or baseline
          const isBaseline = data.status === 'baseline';
          if (!isBaseline && comparisonData.length > 1) {
            const baseVal = comparisonData.find(x => x.status === 'baseline')?.metrics[key];
            if (baseVal !== undefined) {
              const improved = lowerIsBetter ? (val < baseVal) : (val > baseVal);
              const degraded = lowerIsBetter ? (val > baseVal) : (val < baseVal);
              if (improved) colorClass = "text-brand-neonGreen font-semibold";
              else if (degraded) colorClass = "text-red-400 font-semibold";
            }
          }

          let displayVal = val;
          if (isCost) displayVal = `$${val.toLocaleString()}`;
          else if (isPercent) displayVal = `${val}%`;

          return (
            <td key={idx} className={`py-3 px-4 text-xs text-center ${colorClass}`}>
              {displayVal}
            </td>
          );
        })}
      </tr>
    );
  };

  return (
    <div className="w-full space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <ArrowLeftRight className="text-brand-neonPurple" size={20} />
            Scenario Comparison Visualizer
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Check multiple planning scenarios below to compare performance side-by-side.
          </p>
        </div>
      </div>

      {/* Scenario Checkboxes */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {scenarios.map((scen) => {
          const isSelected = selectedIds.includes(scen.id);
          return (
            <button
              key={scen.id}
              onClick={() => toggleSelect(scen.id)}
              className={`p-3 rounded-xl border text-left flex flex-col justify-between transition-all ${
                isSelected 
                  ? 'bg-brand-neonPurple/10 border-brand-neonPurple text-white shadow-lg shadow-brand-neonPurple/5' 
                  : 'bg-brand-panel border-brand-border text-slate-400 hover:border-slate-700 hover:text-white'
              }`}
            >
              <div className="flex justify-between items-start w-full">
                <span className="text-[10px] uppercase font-bold tracking-wider opacity-60">
                  {scen.status}
                </span>
                {isSelected && <Check size={12} className="text-brand-neonPurple" />}
              </div>
              <h4 className="text-xs font-bold truncate mt-2 w-full">{scen.name}</h4>
            </button>
          );
        })}
      </div>

      {/* Comparison Grid */}
      {selectedIds.length > 0 ? (
        <div className="bg-[#101625]/60 border border-brand-border rounded-2xl overflow-hidden glass-panel">
          {loading ? (
            <div className="p-12 text-center text-xs text-slate-500 italic">
              Loading scenario matrices...
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[600px] border-collapse text-left">
                <thead>
                  <tr className="bg-brand-panel border-b border-brand-border text-slate-300 text-xs">
                    <th className="py-3.5 px-4 font-bold">Metric / Variable</th>
                    {comparisonData.map((data, idx) => (
                      <th key={idx} className="py-3.5 px-4 font-bold text-center">
                        {data.name}
                        <span className="block text-[9px] font-normal uppercase text-slate-500 mt-1">
                          {data.status} • {data.element_count} Assets
                        </span>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {renderMetricRow("Traffic Congestion Score (0-100)", "traffic_score", false, false, false)}
                  {renderMetricRow("Average Commute Time (mins)", "travel_time", false, false, true)}
                  {renderMetricRow("Emergency Response Speed (mins)", "emergency_response", false, false, true)}
                  {renderMetricRow("Healthcare Catchment Coverage", "population_coverage", false, true, false)}
                  {renderMetricRow("Daily Carbon Index (CO2 Tons)", "carbon_footprint", false, false, true)}
                  {renderMetricRow("Sustainability Score (0-100)", "sustainability_score", false, false, false)}
                  {renderMetricRow("Disaster Flood/Heat Risk Index", "risk_level", false, false, true)}
                  {renderMetricRow("Urban Economic Growth Rate", "economic_growth", false, true, false)}
                  {renderMetricRow("Estimated Construction Cost", "cost", true, false, true)}
                  {renderMetricRow("ROI Rate of Returns", "roi", false, true, false)}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ) : (
        <div className="p-8 text-center bg-brand-panel/40 border border-dashed border-brand-border rounded-2xl text-xs text-slate-500 flex flex-col items-center justify-center gap-2">
          <Layers size={24} className="text-slate-600" />
          Select at least one scenario above to initialize the side-by-side matrices comparison.
        </div>
      )}
    </div>
  );
}
