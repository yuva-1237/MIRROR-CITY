import React from 'react';
import { Wifi, WifiOff, RefreshCw, AlertTriangle } from 'lucide-react';

interface ConnectionStatusBadgeProps {
  connected: boolean;
  retryCount: number;
  isStale?: boolean;
}

export const ConnectionStatusBadge: React.FC<ConnectionStatusBadgeProps> = ({
  connected,
  retryCount,
  isStale = false,
}) => {
  if (connected && !isStale) {
    return (
      <div 
        id="ws-status-badge"
        className="flex items-center gap-1.5 px-2.5 py-1 bg-emerald-500/10 border border-emerald-500/30 rounded-full text-emerald-400 text-xs font-mono font-medium shadow-sm shadow-emerald-950/20"
        title="Live WebSocket Stream Connected (Heartbeat Active)"
      >
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
        </span>
        <Wifi className="w-3 h-3 text-emerald-400" />
        <span>LIVE BUS</span>
      </div>
    );
  }

  if (connected && isStale) {
    return (
      <div 
        id="ws-status-badge"
        className="flex items-center gap-1.5 px-2.5 py-1 bg-amber-500/10 border border-amber-500/30 rounded-full text-amber-400 text-xs font-mono font-medium"
        title="WebSocket frames lagging; watchdog monitoring"
      >
        <AlertTriangle className="w-3 h-3 text-amber-400 animate-pulse" />
        <span>STREAM LAG</span>
      </div>
    );
  }

  if (retryCount > 0) {
    return (
      <div 
        id="ws-status-badge"
        className="flex items-center gap-1.5 px-2.5 py-1 bg-amber-500/15 border border-amber-500/40 rounded-full text-amber-300 text-xs font-mono font-medium animate-pulse"
        title={`Reconnecting to backend bus... (Attempt ${retryCount})`}
      >
        <RefreshCw className="w-3 h-3 animate-spin text-amber-400" />
        <span>RECONNECTING #{retryCount}</span>
      </div>
    );
  }

  return (
    <div 
      id="ws-status-badge"
      className="flex items-center gap-1.5 px-2.5 py-1 bg-rose-500/15 border border-rose-500/40 rounded-full text-rose-400 text-xs font-mono font-medium"
      title="WebSocket Disconnected"
    >
      <WifiOff className="w-3 h-3 text-rose-400" />
      <span>DISCONNECTED</span>
    </div>
  );
};

export default ConnectionStatusBadge;
