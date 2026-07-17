import React, { useEffect, useState } from 'react';
import { Server, Database, Brain, Radio, CloudLightning, ShieldCheck, RefreshCw, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import { apiGet } from '../lib/api';

interface HealthComponent {
  status: string;
  [key: string]: any;
}
interface HealthData {
  status: string;
  uptime_human: string;
  uptime_seconds: number;
  components: {
    database:        HealthComponent;
    ai_coordinator:  HealthComponent;
    websocket_bus:   HealthComponent;
    weather_service: HealthComponent;
    rate_limiter:    HealthComponent;
  };
}

interface SystemHealthPanelProps {
  authToken: string;
}

const STATUS_ICON: Record<string, React.ReactNode> = {
  healthy:    <CheckCircle className="h-4 w-4 text-emerald-400" />,
  active:     <CheckCircle className="h-4 w-4 text-emerald-400" />,
  live_api:   <CheckCircle className="h-4 w-4 text-emerald-400" />,
  simulation: <AlertTriangle className="h-4 w-4 text-sky-400" />,
  degraded:   <AlertTriangle className="h-4 w-4 text-amber-400" />,
  inactive:   <XCircle className="h-4 w-4 text-slate-500" />,
  unreachable:<XCircle className="h-4 w-4 text-red-500" />,
};

const STATUS_COLOR: Record<string, string> = {
  healthy:     'text-emerald-400',
  active:      'text-emerald-400',
  live_api:    'text-emerald-400',
  simulation:  'text-sky-400',
  degraded:    'text-amber-400',
  inactive:    'text-slate-500',
  unreachable: 'text-red-400',
};

function statusIcon(s: string) {
  return STATUS_ICON[s] ?? <AlertTriangle className="h-4 w-4 text-amber-400" />;
}
function statusColor(s: string) {
  return STATUS_COLOR[s] ?? 'text-amber-400';
}

export default function SystemHealthPanel({ authToken }: SystemHealthPanelProps) {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const fetchHealth = async () => {
    setLoading(true);
    try {
      const data = await apiGet<HealthData>('/api/health/detailed', { token: authToken });
      setHealth(data);
    } catch (e) {
      console.error('[SystemHealthPanel] fetch error:', e);
    } finally {
      setLoading(false);
      setLastRefresh(new Date());
    }
  };

  // Auto-refresh every 15 s
  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 15_000);
    return () => clearInterval(interval);
  }, []);

  const services = health ? [
    {
      name:  'Database',
      icon:  Database,
      key:   'database',
      color: 'text-brand-neonCyan',
      extra: health.components.database.status === 'healthy'
        ? `${health.components.database.users_registered} users · ${health.components.database.scenarios_loaded} scenarios`
        : health.components.database.error ?? '',
    },
    {
      name:  'AI Coordinator',
      icon:  Brain,
      key:   'ai_coordinator',
      color: 'text-brand-neonPurple',
      extra: `Tick #${health.components.ai_coordinator.tick ?? 0} · ${Object.keys(health.components.ai_coordinator.agents ?? {}).length} agents`,
    },
    {
      name:  'WebSocket Bus',
      icon:  Radio,
      key:   'websocket_bus',
      color: 'text-emerald-400',
      extra: `${health.components.websocket_bus.active_connections} active connections`,
    },
    {
      name:  'Weather Service',
      icon:  CloudLightning,
      key:   'weather_service',
      color: 'text-sky-400',
      extra: `Circuit breaker: ${health.components.weather_service.circuit_breaker ?? 'closed'}`,
    },
    {
      name:  'Rate Limiter',
      icon:  ShieldCheck,
      key:   'rate_limiter',
      color: 'text-brand-neonOrange',
      extra: 'Per-IP sliding window · Active',
    },
  ] : [];

  return (
    <div className="glass-panel rounded-xl border border-brand-border/60 p-5 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-brand-border/40 pb-3">
        <div className="flex items-center gap-2">
          <Server className="h-5 w-5 text-brand-neonCyan" />
          <h3 className="font-semibold text-sm tracking-wide text-slate-200 uppercase">System Health Monitor</h3>
          {health && (
            <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase border ${
              health.status === 'healthy'
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
            }`}>
              {health.status}
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          {health && (
            <span className="text-[10px] text-slate-400 font-mono">
              ⏱ {health.uptime_human}
            </span>
          )}
          <button
            onClick={fetchHealth}
            disabled={loading}
            className="text-slate-400 hover:text-white transition-colors"
            title="Refresh health"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin text-brand-neonCyan' : ''}`} />
          </button>
        </div>
      </div>

      {/* Service rows */}
      {loading && !health ? (
        <div className="flex items-center justify-center py-8 text-slate-500 text-sm">
          <RefreshCw className="h-5 w-5 animate-spin mr-2" />
          Loading system health...
        </div>
      ) : (
        <div className="space-y-2">
          {services.map(({ name, icon: Icon, key, color, extra }) => {
            const comp = health!.components[key as keyof HealthData['components']];
            const s = comp?.status ?? 'unknown';
            return (
              <div
                key={key}
                className="flex items-center justify-between p-3 bg-slate-900/40 rounded-lg border border-brand-border/20 hover:border-brand-border/60 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <Icon className={`h-4 w-4 ${color}`} />
                  <div>
                    <span className="text-xs font-semibold text-slate-200">{name}</span>
                    {extra && (
                      <p className="text-[10px] text-slate-400 mt-0.5">{extra}</p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {statusIcon(s)}
                  <span className={`text-[10px] font-bold uppercase font-mono ${statusColor(s)}`}>
                    {s}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <p className="text-[10px] text-slate-600 text-right">
        Last refreshed: {lastRefresh.toLocaleTimeString()} · auto-refresh every 15s
      </p>
    </div>
  );
}
