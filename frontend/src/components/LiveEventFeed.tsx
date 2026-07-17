import { useEffect, useState } from 'react';
import { Terminal } from 'lucide-react';
import { useScrollToBottom } from '../hooks/useScrollToBottom';

interface LiveEventFeedProps {
  telemetry: any;
  agentOutputs: any;
  masterRec: any;
}

export default function LiveEventFeed({ telemetry, agentOutputs }: LiveEventFeedProps) {
  const [logs, setLogs] = useState<Array<{ id: number; time: string; type: string; message: string; severity: 'info' | 'warn' | 'error' | 'success' }>>([]);
  const { containerRef, sentinelRef } = useScrollToBottom([logs], 120);

  useEffect(() => {
    if (!telemetry) return;
    
    const timeStr = new Date().toLocaleTimeString();
    const newLogs: typeof logs = [];
    
    // Add weather report logs occasionally
    if (Math.random() < 0.2) {
      newLogs.push({
        id: Date.now() + 1,
        time: timeStr,
        type: 'WEATHER',
        message: `Weather station reports: ${telemetry.weather.condition} (${telemetry.weather.temp}°C).`,
        severity: telemetry.weather.rain_intensity > 0.5 ? 'warn' : 'info'
      });
    }

    // Add flood telemetry alert log if critical
    if (telemetry.flood_simulation?.max_water_level_cm > 40) {
      newLogs.push({
        id: Date.now() + 2,
        time: timeStr,
        type: 'FLOOD',
        message: `High runoff detected! Max flood water level at ${telemetry.flood_simulation.max_water_level_cm} cm.`,
        severity: 'error'
      });
    }

    // Add agent thinking alerts
    Object.values(agentOutputs || {}).forEach((agent: any) => {
      if (agent.alert_level === 'danger' && Math.random() < 0.4) {
        newLogs.push({
          id: Date.now() + Math.random(),
          time: timeStr,
          type: agent.name.toUpperCase(),
          message: agent.reasoning[agent.reasoning.length - 1] || 'Elevated risk parameters identified.',
          severity: 'error'
        });
      } else if (agent.alert_level === 'warning' && Math.random() < 0.3) {
        newLogs.push({
          id: Date.now() + Math.random(),
          time: timeStr,
          type: agent.name.toUpperCase(),
          message: agent.reasoning[agent.reasoning.length - 1] || 'Evaluating border-line grid load variances.',
          severity: 'warn'
        });
      }
    });

    if (newLogs.length > 0) {
      setLogs((prev) => {
        const combined = [...prev, ...newLogs];
        return combined.slice(-50); // Keep last 50 logs
      });
    }
  }, [telemetry, agentOutputs]);


  return (
    <div className="glass-panel rounded-xl border border-brand-border/60 p-4 h-[350px] flex flex-col">
      <div className="flex items-center gap-2 mb-3 border-b border-brand-border/40 pb-2">
        <Terminal className="h-5 w-5 text-brand-neonCyan" />
        <h3 className="font-semibold text-sm tracking-wide text-slate-200">LIVE TELEMETRY INCIDENT STREAM</h3>
        <span className="ml-auto flex h-2 w-2 relative">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
        </span>
      </div>

      <div ref={containerRef} className="flex-1 overflow-y-auto font-mono text-[11px] space-y-2 pr-1" style={{ overscrollBehavior: 'contain' }}>
        {logs.length === 0 ? (
          <div className="text-slate-500 text-center py-10">
            Waiting for live telemetry packets...
          </div>
        ) : (
          logs.map((log) => (
            <div key={log.id} className="flex items-start gap-2 border-b border-brand-border/10 pb-1 hover:bg-white/[0.02] p-1 rounded transition">
              <span className="text-brand-neonCyan/70">[{log.time}]</span>
              <span className={`font-semibold shrink-0 ${
                log.severity === 'error' ? 'text-red-400' :
                log.severity === 'warn' ? 'text-amber-400' :
                log.severity === 'success' ? 'text-emerald-400' : 'text-blue-400'
              }`}>
                {log.type}:
              </span>
              <span className="text-slate-300">{log.message}</span>
            </div>
          ))
        )}
        <div ref={sentinelRef} />
      </div>
    </div>
  );
}
