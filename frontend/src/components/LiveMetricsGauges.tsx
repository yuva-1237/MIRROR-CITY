import { Activity, Wind, Zap, Droplets, Users } from 'lucide-react';
import DataQualityBadge from './DataQualityBadge';

interface LiveMetricsGaugesProps {
  telemetry: any;
  dataQuality?: any;
}

export default function LiveMetricsGauges({ telemetry, dataQuality }: LiveMetricsGaugesProps) {
  if (!telemetry) return null;

  const weatherSource = dataQuality?.weather_source ?? 'simulation';
  const overallQuality = dataQuality?.overall_quality ?? 85;

  // Compute stats
  const congestions = Object.values(telemetry.traffic || {}).map((t: any) => t.congestion_percentage);
  const avgCongest = congestions.length ? congestions.reduce((a, b) => a + b, 0) / congestions.length : 0.0;
  
  const aqis = Object.values(telemetry.air_quality || {}).map((a: any) => a.aqi);
  const avgAqi = aqis.length ? aqis.reduce((a, b) => a + b, 0) / aqis.length : 50;

  const loads = Object.values(telemetry.power || {}).map((p: any) => p.load_percentage);
  const avgLoad = loads.length ? loads.reduce((a, b) => a + b, 0) / loads.length : 0.0;

  const floodLevels = Object.values(telemetry.flood || {}).map((f: any) => f.water_level_cm);
  const maxFlood = floodLevels.length ? Math.max(...floodLevels) : 0.0;

  const densities = Object.values(telemetry.crowd || {}).map((c: any) => c.density_people_m2);
  const avgCrowd = densities.length ? densities.reduce((a, b) => a + b, 0) / densities.length : 0.0;

  const items = [
    {
      title: 'TRAFFIC CONGESTION',
      value: `${avgCongest.toFixed(1)}%`,
      icon: Activity,
      color: avgCongest > 70 ? 'text-red-400' : (avgCongest > 40 ? 'text-amber-400' : 'text-emerald-400'),
      barColor: avgCongest > 70 ? 'bg-red-500' : (avgCongest > 40 ? 'bg-amber-500' : 'bg-emerald-500'),
      percent: avgCongest,
      desc: avgCongest > 70 ? 'Severe bottlenecks' : 'Stable flow'
    },
    {
      title: 'AIR QUALITY INDEX',
      value: `${avgAqi.toFixed(0)} AQI`,
      icon: Wind,
      color: avgAqi > 150 ? 'text-red-400' : (avgAqi > 80 ? 'text-amber-400' : 'text-emerald-400'),
      barColor: avgAqi > 150 ? 'bg-red-500' : (avgAqi > 80 ? 'bg-amber-500' : 'bg-emerald-500'),
      percent: Math.min(100, (avgAqi / 300) * 100),
      desc: avgAqi > 150 ? 'Unhealthy conditions' : 'Good/Moderate'
    },
    {
      title: 'GRID ENERGY LOAD',
      value: `${avgLoad.toFixed(1)}%`,
      icon: Zap,
      color: avgLoad > 85 ? 'text-red-400' : (avgLoad > 60 ? 'text-amber-400' : 'text-emerald-400'),
      barColor: avgLoad > 85 ? 'bg-red-500' : (avgLoad > 60 ? 'bg-amber-500' : 'bg-emerald-500'),
      percent: avgLoad,
      desc: avgLoad > 85 ? 'High demand surge' : 'Nominal grid load'
    },
    {
      title: 'FLOOD RUN-OFF LEVEL',
      value: `${maxFlood.toFixed(1)} cm`,
      icon: Droplets,
      color: maxFlood > 50 ? 'text-red-400' : (maxFlood > 20 ? 'text-amber-400' : 'text-emerald-400'),
      barColor: maxFlood > 50 ? 'bg-red-500' : (maxFlood > 20 ? 'bg-amber-500' : 'bg-emerald-500'),
      percent: Math.min(100, (maxFlood / 120) * 100),
      desc: maxFlood > 50 ? 'Critical flooding' : 'Normal runoff'
    },
    {
      title: 'CROWD DENSITY',
      value: `${avgCrowd.toFixed(2)}/m²`,
      icon: Users,
      color: avgCrowd > 1.0 ? 'text-red-400' : (avgCrowd > 0.5 ? 'text-amber-400' : 'text-emerald-400'),
      barColor: avgCrowd > 1.0 ? 'bg-red-500' : (avgCrowd > 0.5 ? 'bg-amber-500' : 'bg-emerald-500'),
      percent: Math.min(100, (avgCrowd / 2.0) * 100),
      desc: avgCrowd > 1.0 ? 'Congested zones' : 'Sparse safety index'
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
      {items.map((item, idx) => {
        const Icon = item.icon;
        return (
          <div key={idx} className="glass-panel p-4 rounded-xl border border-brand-border/60 bg-brand-panel/40 flex flex-col justify-between hover:border-brand-accent/40 transition duration-300">
            <div className="flex justify-between items-start">
              <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                {item.title}
              </span>
              <Icon className={`h-4.5 w-4.5 ${item.color}`} />
            </div>

            <div className="mt-3">
              <h2 className={`text-2xl font-bold tracking-tight ${item.color}`}>
                {item.value}
              </h2>
              <div className="w-full bg-slate-800 h-1.5 rounded-full mt-2 overflow-hidden">
                <div 
                  className={`h-full rounded-full transition-all duration-1000 ${item.barColor}`} 
                  style={{ width: `${item.percent}%` }}
                />
              </div>
            </div>

            <div className="mt-2 flex justify-between items-center text-[10px] text-slate-400">
              <span>{item.desc}</span>
              <DataQualityBadge
                source={weatherSource as any}
                confidence={overallQuality}
                compact
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
