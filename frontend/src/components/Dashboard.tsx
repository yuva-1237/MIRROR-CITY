
import { useState } from 'react';
import { Line, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { ShieldCheck, Activity, Trees, Flame, Compass, RefreshCw } from 'lucide-react';
import BaselineComparisonChart from './BaselineComparisonChart';
import { ClimateDNACard, ClimateDNAModal } from './ClimateDNA';
import { useLocationStore } from '../store/locationStore';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface DashboardProps {
  metrics: any;
  explanation: string;
  recommendations: any[];
  forecast: any;
  onRunSimulation: () => void;
  simulating: boolean;
  climateData?: any;
  authToken?: string;
}

export default function Dashboard({
  metrics,
  explanation,
  recommendations,
  forecast,
  onRunSimulation,
  simulating,
  climateData,
  authToken
}: DashboardProps) {
  const [climateModalOpen, setClimateModalOpen] = useState(false);
  const { activeLocation } = useLocationStore();
  const token = authToken || localStorage.getItem('token') || '';
  
  // Format the 24h forecasting chart data
  const hoursLabels = Array.from({ length: 24 }, (_, i) => `${i}:00`);

  const trafficAQIData = {
    labels: hoursLabels,
    datasets: [
      {
        label: 'Traffic Congestion (0-100)',
        data: forecast?.traffic || Array(24).fill(0),
        borderColor: '#06b6d4',
        backgroundColor: 'rgba(6, 182, 212, 0.1)',
        fill: true,
        tension: 0.4,
        yAxisID: 'y',
      },
      {
        label: 'Air Quality (AQI)',
        data: forecast?.pollution || Array(24).fill(0),
        borderColor: '#f97316',
        backgroundColor: 'rgba(249, 115, 22, 0.1)',
        fill: true,
        tension: 0.4,
        yAxisID: 'y1',
      }
    ]
  };

  const utilityData = {
    labels: hoursLabels,
    datasets: [
      {
        label: 'Grid Demand (MW)',
        data: forecast?.energy || Array(24).fill(0),
        backgroundColor: '#8b5cf6',
        borderRadius: 4,
      },
      {
        label: 'Water Demand (ML/h)',
        data: forecast?.water || Array(24).fill(0),
        backgroundColor: '#3b82f6',
        borderRadius: 4,
      }
    ]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: { color: '#94a3b8', font: { size: 10 } }
      }
    },
    scales: {
      x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
      y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } }
    }
  };

  const doubleAxisOptions = {
    ...chartOptions,
    scales: {
      x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
      y: { type: 'linear' as const, display: true, position: 'left' as const, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
      y1: { type: 'linear' as const, display: true, position: 'right' as const, grid: { drawOnChartArea: false }, ticks: { color: '#94a3b8' } },
    }
  };

  return (
    <div className="space-y-6">
      {/* Simulation Trigger Bar */}
      <div className="flex flex-col gap-3 bg-[#101625]/60 border border-brand-border p-4 rounded-2xl glass-panel">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-sm font-semibold text-slate-300">Run Planning Core</h2>
            <p className="text-[10px] text-slate-500 mt-0.5">Propagates routes & loops GNN nodes on change</p>
          </div>
          <button
            onClick={onRunSimulation}
            disabled={simulating}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium text-xs rounded-xl shadow-lg hover:shadow-blue-500/25 transition-all"
          >
            <RefreshCw size={14} className={simulating ? 'animate-spin' : ''} />
            {simulating ? 'Recalculating Twin...' : 'Recalculate City State'}
          </button>
        </div>
        
        {simulating && (
          <div className="space-y-1 animate-fadeIn">
            <div className="flex justify-between text-[9px] text-brand-neonCyan font-mono">
              <span className="animate-pulse">⚡ SOLVING TRANSPORTATION ROUTING & CLOUD COGNITION GNN NODES...</span>
              <span>calculating...</span>
            </div>
            <div className="w-full bg-slate-950 h-1.5 rounded-full overflow-hidden border border-brand-border/20">
              <div 
                className="h-full bg-gradient-to-r from-blue-500 via-brand-neonCyan to-emerald-500 rounded-full animate-simulationProgress shadow-[0_0_10px_rgba(6,182,212,0.5)]"
                style={{ width: '90%', transition: 'width 4s cubic-bezier(0.1, 0.8, 0.1, 1)' }}
              />
            </div>
          </div>
        )}
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        {/* KPI 1 */}
        <div className="bg-[#101625]/60 border border-brand-border p-4 rounded-2xl glass-panel">
          <div className="flex justify-between text-slate-400">
            <span className="text-[10px] uppercase font-bold tracking-wider">Traffic Congestion</span>
            <Activity size={14} className="text-brand-neonCyan" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-white">{metrics?.traffic_score || 0}</span>
            <span className="text-[10px] text-slate-500">/ 100</span>
          </div>
          <div className="text-[9px] text-slate-400 mt-1">Average Commute: {metrics?.travel_time || 0} min</div>
        </div>

        {/* KPI 2 */}
        <div className="bg-[#101625]/60 border border-brand-border p-4 rounded-2xl glass-panel">
          <div className="flex justify-between text-slate-400">
            <span className="text-[10px] uppercase font-bold tracking-wider">Carbon Footprint</span>
            <Trees size={14} className="text-brand-neonGreen" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-white">{metrics?.carbon_footprint || 0}</span>
            <span className="text-[9px] text-slate-500">Tons CO2/day</span>
          </div>
          <div className="text-[9px] text-brand-neonGreen mt-1">Sustainability: {metrics?.sustainability_score || 0}</div>
        </div>

        {/* KPI 3 */}
        <div className="bg-[#101625]/60 border border-brand-border p-4 rounded-2xl glass-panel">
          <div className="flex justify-between text-slate-400">
            <span className="text-[10px] uppercase font-bold tracking-wider">Emergency Speed</span>
            <Compass size={14} className="text-brand-neonOrange" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-white">{metrics?.emergency_response || 0}</span>
            <span className="text-[9px] text-slate-500">min response</span>
          </div>
          <div className="text-[9px] text-slate-400 mt-1">Outreach Coverage: {metrics?.population_coverage || 0}%</div>
        </div>

        {/* KPI 4 */}
        <div className="bg-[#101625]/60 border border-brand-border p-4 rounded-2xl glass-panel">
          <div className="flex justify-between text-slate-400">
            <span className="text-[10px] uppercase font-bold tracking-wider">Disaster Risk</span>
            <Flame size={14} className="text-red-500" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-white">{metrics?.risk_level || 0}</span>
            <span className="text-[10px] text-slate-500">/ 100</span>
          </div>
          <div className="text-[9px] text-slate-400 mt-1">Flood/Heat vulnerability</div>
        </div>

        {/* KPI 5 */}
        <div className="bg-[#101625]/60 border border-brand-border p-4 rounded-2xl glass-panel">
          <div className="flex justify-between text-slate-400">
            <span className="text-[10px] uppercase font-bold tracking-wider">Scenario Cost</span>
            <ShieldCheck size={14} className="text-brand-neonPurple" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-lg font-extrabold text-white">
              {metrics?.cost > 0 ? `$${(metrics.cost / 1000000).toFixed(1)}M` : '$0.0'}
            </span>
          </div>
          <div className="text-[9px] text-brand-neonPurple mt-1.5">Forecasted ROI: {metrics?.roi || 0}%</div>
        </div>
      </div>

      {/* CLIMATE DNA ENSO Intelligence Card */}
      <ClimateDNACard
        climateData={climateData}
        onExplore={() => setClimateModalOpen(true)}
      />

      {/* Analytics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 1 */}
        <div className="bg-[#101625]/60 border border-brand-border p-4 rounded-2xl glass-panel h-80">
          <h3 className="text-xs font-bold text-slate-300 mb-3 uppercase tracking-wider">24h Traffic & Air Pollution Forecast</h3>
          <div className="h-64">
            <Line data={trafficAQIData} options={doubleAxisOptions} />
          </div>
        </div>

        {/* Chart 2 */}
        <div className="bg-[#101625]/60 border border-brand-border p-4 rounded-2xl glass-panel h-80">
          <h3 className="text-xs font-bold text-slate-300 mb-3 uppercase tracking-wider">24h Municipal Utilities Loading</h3>
          <div className="h-64">
            <Bar data={utilityData} options={chartOptions} />
          </div>
        </div>
      </div>

      {/* Empirical Baseline Model Comparison Chart */}
      <BaselineComparisonChart />

      {/* Explainable AI Recommendations Panel */}
      <div className="bg-[#101625]/60 border border-brand-border p-5 rounded-2xl glass-panel">
        <h3 className="text-xs font-bold text-slate-300 mb-4 uppercase tracking-wider flex items-center gap-2">
          <ShieldCheck className="text-brand-neonGreen" size={16} />
          Explainable AI Consensus Reasoning
        </h3>
        <p className="text-xs leading-5 text-slate-300">
          {explanation}
        </p>
        
        {recommendations.length > 0 && (
          <div className="mt-6 border-t border-brand-border pt-4">
            <h4 className="text-xs font-semibold text-slate-400 uppercase mb-3">Recommended Actions</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {recommendations.map((action, idx) => (
                <div key={idx} className="p-3 bg-[#0d1220] border border-brand-border rounded-xl">
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-bold text-white">{action.title}</span>
                    <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full ${
                      action.priority === 'High' 
                        ? 'bg-red-500/20 text-red-400' 
                        : (action.priority === 'Medium' ? 'bg-orange-500/20 text-orange-400' : 'bg-green-500/20 text-green-400')
                    }`}>
                      {action.priority}
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-400 mt-1">{action.description}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* CLIMATE DNA Intelligence Modal */}
      <ClimateDNAModal
        isOpen={climateModalOpen}
        onClose={() => setClimateModalOpen(false)}
        activeCity={activeLocation}
        authToken={token}
      />
    </div>
  );
}
