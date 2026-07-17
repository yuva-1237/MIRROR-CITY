import React from 'react';
import { Users, Map, FlaskConical, Eye, Shield, Activity, CloudRain, Zap, ChevronRight } from 'lucide-react';

export type UserRole = 'Citizen' | 'Planner' | 'Administrator' | 'Researcher' | string;

interface RoleDashboardProps {
  role: UserRole;
  streamData: any;
  children: React.ReactNode;          // Full Planner UI
  onRoleOverride: (r: UserRole) => void;
  activeOverride: UserRole | null;
}

/**
 * RoleDashboard
 * ─────────────────────────────────────────────────────────────
 * Wraps the main application and:
 *  • Citizen     → Simple weather/flood/traffic card summary
 *  • Planner     → Full existing Command Center UI (children)
 *  • Administrator → Full UI + System Health tab unlocked
 *  • Researcher  → Full UI + Raw telemetry inspector
 *
 * A role-switcher pill is always visible so the user can change view.
 */

const ROLES: { id: UserRole; label: string; icon: any; desc: string }[] = [
  { id: 'Citizen',       label: 'Citizen',       icon: Users,        desc: 'Simple city status' },
  { id: 'Planner',       label: 'Planner',        icon: Map,          desc: 'Full twin control'  },
  { id: 'Administrator', label: 'Administrator',  icon: Shield,       desc: 'System & users'     },
  { id: 'Researcher',    label: 'Researcher',     icon: FlaskConical, desc: 'Raw telemetry'      },
];

// ── Citizen View ────────────────────────────────────────────────────────────
function CitizenView({ data }: { data: any }) {
  if (!data) return (
    <div className="flex-1 flex items-center justify-center text-slate-500">
      Connecting to city systems...
    </div>
  );

  const w = data.telemetry?.weather ?? {};
  const floods = Object.values(data.telemetry?.flood ?? {}) as any[];
  const maxFlood = floods.length ? Math.max(...floods.map((f: any) => f.water_level_cm ?? 0)) : 0;
  const traffic  = Object.values(data.telemetry?.traffic ?? {}) as any[];
  const avgCong  = traffic.length
    ? traffic.reduce((s: number, t: any) => s + (t.congestion_percentage ?? 0), 0) / traffic.length
    : 0;

  const alertLevel = data.master_recommendation?.alert_level ?? 'normal';
  const alertColor = alertLevel === 'danger' ? 'border-red-500 bg-red-900/20' :
                     alertLevel === 'warning' ? 'border-amber-500 bg-amber-900/20' :
                     'border-emerald-500/30 bg-emerald-900/10';
  const alertText  = alertLevel === 'danger' ? '🚨 Emergency Alert Active'   :
                     alertLevel === 'warning' ? '⚠️ Advisory in Effect'       :
                     '✅ All Systems Normal';

  return (
    <div className="flex-1 p-6 max-w-3xl mx-auto space-y-6">
      <div className={`rounded-2xl border p-4 text-sm font-semibold ${alertColor}`}>
        {alertText}
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Weather */}
        <div className="glass-panel p-5 rounded-2xl border border-brand-border/60 space-y-3">
          <div className="flex items-center gap-2 text-brand-neonCyan">
            <CloudRain className="h-5 w-5" />
            <span className="text-xs font-bold uppercase tracking-wider">Weather</span>
          </div>
          <p className="text-3xl font-bold text-white">{w.temp ?? '--'}°C</p>
          <p className="text-sm text-slate-300">{w.condition ?? 'Loading...'}</p>
          <p className="text-xs text-slate-400">Humidity {w.humidity ?? '--'}% · Wind {w.wind_speed ?? '--'} km/h</p>
        </div>

        {/* Flood Risk */}
        <div className="glass-panel p-5 rounded-2xl border border-brand-border/60 space-y-3">
          <div className="flex items-center gap-2 text-brand-neonCyan">
            <Activity className="h-5 w-5" />
            <span className="text-xs font-bold uppercase tracking-wider">Flood Risk</span>
          </div>
          <p className={`text-3xl font-bold ${maxFlood > 50 ? 'text-red-400' : maxFlood > 20 ? 'text-amber-400' : 'text-emerald-400'}`}>
            {maxFlood.toFixed(1)} cm
          </p>
          <p className="text-sm text-slate-300">{maxFlood > 50 ? 'Critical' : maxFlood > 20 ? 'Moderate' : 'Low risk'}</p>
          <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
            <div className={`h-full rounded-full ${maxFlood > 50 ? 'bg-red-500' : maxFlood > 20 ? 'bg-amber-500' : 'bg-emerald-500'}`}
              style={{ width: `${Math.min(100, (maxFlood / 120) * 100)}%` }} />
          </div>
        </div>

        {/* Traffic */}
        <div className="glass-panel p-5 rounded-2xl border border-brand-border/60 space-y-3">
          <div className="flex items-center gap-2 text-brand-neonCyan">
            <Zap className="h-5 w-5" />
            <span className="text-xs font-bold uppercase tracking-wider">Traffic</span>
          </div>
          <p className={`text-3xl font-bold ${avgCong > 70 ? 'text-red-400' : avgCong > 40 ? 'text-amber-400' : 'text-emerald-400'}`}>
            {avgCong.toFixed(0)}%
          </p>
          <p className="text-sm text-slate-300">{avgCong > 70 ? 'Severe congestion' : avgCong > 40 ? 'Moderate flow' : 'Clear roads'}</p>
        </div>

        {/* Active Alerts */}
        <div className="glass-panel p-5 rounded-2xl border border-brand-border/60 space-y-2 overflow-y-auto max-h-[160px]">
          <div className="flex items-center gap-2 text-brand-neonOrange">
            <Eye className="h-5 w-5" />
            <span className="text-xs font-bold uppercase tracking-wider">AI Alerts</span>
          </div>
          {data.master_recommendation?.explainability_chain?.slice(0, 3).map((s: string, i: number) => (
            <p key={i} className="text-xs text-slate-300 border-l-2 border-brand-neonOrange/40 pl-2">{s}</p>
          )) ?? <p className="text-xs text-slate-500">No active alerts</p>}
        </div>
      </div>
    </div>
  );
}

// ── Researcher View (wraps children + raw inspector) ────────────────────────
function ResearcherView({ data, children }: { data: any; children: React.ReactNode }) {
  const [showRaw, setShowRaw] = React.useState(false);
  return (
    <div className="flex-1 flex flex-col">
      {children}
      <div className="mx-4 mb-4 rounded-xl border border-brand-neonPurple/30 overflow-hidden">
        <button
          onClick={() => setShowRaw(v => !v)}
          className="w-full flex items-center justify-between p-3 bg-brand-panel/60 text-xs font-bold text-brand-neonPurple uppercase tracking-wider hover:bg-brand-panel/80 transition"
        >
          <span>🔬 Raw Telemetry Inspector (Researcher Mode)</span>
          <ChevronRight className={`h-4 w-4 transition-transform ${showRaw ? 'rotate-90' : ''}`} />
        </button>
        {showRaw && (
          <pre className="text-[10px] text-slate-300 bg-black/60 p-4 overflow-auto max-h-64 font-mono leading-relaxed">
            {JSON.stringify(data?.telemetry ?? {}, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}

// ── Main RoleDashboard ───────────────────────────────────────────────────────
export default function RoleDashboard({
  role,
  streamData,
  children,
  onRoleOverride,
  activeOverride,
}: RoleDashboardProps) {
  const effectiveRole: UserRole = activeOverride ?? role;

  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* Role Switcher Bar */}
      <div className="px-4 py-1.5 bg-slate-900/60 border-b border-brand-border/30 flex items-center gap-2 overflow-x-auto">
        <span className="text-[9px] text-slate-500 uppercase tracking-widest font-bold shrink-0 pr-1">View:</span>
        {ROLES.map(r => {
          const Icon = r.icon;
          const isActive = effectiveRole === r.id;
          return (
            <button
              key={r.id}
              onClick={() => onRoleOverride(r.id)}
              title={r.desc}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all duration-200 shrink-0 ${
                isActive
                  ? 'bg-brand-accent/20 border border-brand-accent text-white'
                  : 'border border-transparent text-slate-500 hover:text-slate-200 hover:border-brand-border/60'
              }`}
            >
              <Icon className="h-3 w-3" />
              {r.label}
            </button>
          );
        })}
      </div>

      {/* Role-specific content */}
      {effectiveRole === 'Citizen' ? (
        <CitizenView data={streamData} />
      ) : effectiveRole === 'Researcher' ? (
        <ResearcherView data={streamData}>{children}</ResearcherView>
      ) : (
        // Planner + Administrator → full existing UI
        <div className="flex-1 flex flex-col min-h-0">{children}</div>
      )}
    </div>
  );
}
