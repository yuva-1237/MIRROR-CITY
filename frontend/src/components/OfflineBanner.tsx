import { useEffect, useState } from 'react';
import { WifiOff, Database, RefreshCw, X } from 'lucide-react';

interface OfflineBannerProps {
  isConnected: boolean;
  lastSyncTimestamp?: string;   // ISO string of last successful WS tick
  retryCount?: number;
  onDismiss?: () => void;
}

/**
 * OfflineBanner
 * ─────────────────────────────────────────────────────────────
 * Appears at the top of the screen when the WebSocket is disconnected.
 * Shows:
 *   • Offline mode indicator with last-sync time
 *   • "Using cached data" warning
 *   • Retry counter
 *   • Auto-dismisses when connection is restored
 */
export default function OfflineBanner({
  isConnected,
  lastSyncTimestamp,
  retryCount = 0,
  onDismiss,
}: OfflineBannerProps) {
  const [visible, setVisible] = useState(!isConnected);
  const [reconnecting, setReconnecting] = useState(false);
  const [staleSecs, setStaleSecs] = useState(0);

  // Update stale seconds counter
  useEffect(() => {
    if (!lastSyncTimestamp || isConnected) {
      setStaleSecs(0);
      return;
    }
    const interval = setInterval(() => {
      const diff = Math.floor((Date.now() - new Date(lastSyncTimestamp).getTime()) / 1000);
      setStaleSecs(diff);
    }, 1000);
    return () => clearInterval(interval);
  }, [lastSyncTimestamp, isConnected]);

  // Show/hide banner
  useEffect(() => {
    if (!isConnected) {
      setVisible(true);
      setReconnecting(retryCount > 0);
    } else {
      // Delay hide to show "Reconnected!" briefly
      setReconnecting(false);
      const t = setTimeout(() => setVisible(false), 2000);
      return () => clearTimeout(t);
    }
  }, [isConnected, retryCount]);

  if (!visible) return null;

  const formatStale = (s: number) => {
    if (s < 60)  return `${s}s ago`;
    if (s < 3600) return `${Math.floor(s / 60)}m ago`;
    return `${Math.floor(s / 3600)}h ago`;
  };

  return (
    <div className={`fixed top-0 left-0 right-0 z-[9999] transition-all duration-500 ${
      isConnected
        ? 'bg-emerald-600/90 border-b border-emerald-500'
        : staleSecs > 60
          ? 'bg-red-900/95 border-b border-red-500'
          : 'bg-amber-900/95 border-b border-amber-600'
    } backdrop-blur-sm`}>
      <div className="max-w-7xl mx-auto px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-3">
          {isConnected ? (
            <>
              <RefreshCw className="h-4 w-4 text-emerald-300 animate-spin" />
              <span className="text-emerald-200 text-xs font-semibold">
                ✓ Live connection restored — synchronizing data...
              </span>
            </>
          ) : (
            <>
              <WifiOff className="h-4 w-4 text-amber-300 animate-pulse" />
              <div className="flex items-center gap-4">
                <span className="text-amber-200 text-xs font-semibold">
                  ⚠ Offline Mode
                </span>
                {lastSyncTimestamp && (
                  <span className="flex items-center gap-1 text-amber-300/80 text-[11px]">
                    <Database className="h-3 w-3" />
                    Using cached data from
                    <span className="font-mono font-bold ml-1">
                      {formatStale(staleSecs)}
                    </span>
                  </span>
                )}
                {reconnecting && (
                  <span className="flex items-center gap-1 text-slate-300 text-[11px]">
                    <RefreshCw className="h-3 w-3 animate-spin" />
                    Reconnecting... (attempt {retryCount})
                  </span>
                )}
              </div>
            </>
          )}
        </div>

        {!isConnected && onDismiss && (
          <button
            onClick={onDismiss}
            className="text-slate-400 hover:text-white transition-colors ml-4"
            title="Dismiss"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  );
}
