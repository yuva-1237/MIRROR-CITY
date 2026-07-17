import { Clock, TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react';

interface PredictionTimelineProps {
  predictions: Record<string, any>;
}

export default function PredictionTimeline({ predictions }: PredictionTimelineProps) {
  if (!predictions) {
    return (
      <div className="glass-panel p-4 text-center text-slate-500 text-xs rounded-xl">
        Awaiting predictive calculations...
      </div>
    );
  }

  const horizons = [
    { key: '5m', label: 'In 5 Minutes' },
    { key: '15m', label: 'In 15 Minutes' },
    { key: '1h', label: 'In 1 Hour' },
    { key: '24h', label: 'In 24 Hours' },
    { key: '7d', label: 'In 7 Days' }
  ];

  return (
    <div className="glass-panel p-4 rounded-xl border border-brand-border/60 bg-brand-panel/40 space-y-3">
      <div className="flex items-center gap-2 border-b border-brand-border/40 pb-2">
        <Clock className="h-5 w-5 text-brand-neonCyan" />
        <h3 className="font-semibold text-sm tracking-wide text-slate-200">MULTI-HORIZON PREDICTIVE SYSTEM</h3>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
        {horizons.map(({ key, label }) => {
          const pred = predictions[key];
          if (!pred) return null;

          const alert = pred.alert;
          let alertBadge = "border-emerald-500/20 text-emerald-400 bg-emerald-500/5";
          let alertIcon = CheckCircle;
          if (alert === 'danger') {
            alertBadge = "border-red-500/20 text-red-400 bg-red-500/5";
            alertIcon = AlertTriangle;
          } else if (alert === 'warning') {
            alertBadge = "border-amber-500/20 text-amber-400 bg-amber-500/5";
            alertIcon = AlertTriangle;
          }
          const Icon = alertIcon;

          return (
            <div key={key} className="bg-brand-panel/60 p-3 rounded-lg border border-brand-border/40 flex flex-col justify-between h-[130px] hover:border-brand-accent/20 transition duration-300">
              <div className="flex justify-between items-start">
                <span className="text-[11px] font-semibold text-slate-200">{label}</span>
                <span className={`text-[9px] uppercase font-bold px-1.5 py-0.5 rounded border flex items-center gap-1 ${alertBadge}`}>
                  <Icon className="h-3 w-3" /> {alert || 'normal'}
                </span>
              </div>

              <div className="space-y-1.5 mt-2">
                <div className="flex justify-between text-[11px]">
                  <span className="text-slate-400 font-mono">Traffic:</span>
                  <span className="font-semibold text-slate-300">{pred.traffic_congestion}%</span>
                </div>
                <div className="flex justify-between text-[11px]">
                  <span className="text-slate-400 font-mono">AQI:</span>
                  <span className="font-semibold text-slate-300">{pred.aqi}</span>
                </div>
                <div className="flex justify-between text-[11px]">
                  <span className="text-slate-400 font-mono">Flood Runoff:</span>
                  <span className="font-semibold text-slate-300">{pred.water_level} cm</span>
                </div>
              </div>

              <span className="text-[8px] text-brand-neonCyan flex items-center gap-0.5 mt-1">
                <TrendingUp className="h-2.5 w-2.5" /> continuous predictive model
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
