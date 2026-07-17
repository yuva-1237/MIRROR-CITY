import { useEffect, useState, useRef } from 'react';

export interface WeatherState {
  temp: number;
  humidity: number;
  wind_speed: number;
  rain_intensity: number;
  condition: string;
}

export interface TransitVehicle {
  id: string;
  type: string;
  route: string;
  lat: number;
  lng: number;
  speed_kph: number;
  progress: number;
}

export interface CityTelemetry {
  timestamp: string;
  traffic: Record<string, {
    congestion_percentage: number;
    vehicle_count: number;
    average_speed_kph: number;
    incident_reported: boolean;
  }>;
  air_quality: Record<string, {
    aqi: number;
    pm2_5: number;
    pm10: number;
    co2: number;
    no2: number;
  }>;
  flood: Record<string, {
    node_id: string;
    water_level_cm: number;
    flow_rate_m3_s: number;
    alert_status: 'normal' | 'warning' | 'danger';
  }>;
  power: Record<string, {
    node_id: string;
    load_percentage: number;
    voltage_v: number;
    grid_stability: 'stable' | 'critical';
  }>;
  crowd: Record<string, {
    density_people_m2: number;
    total_count: number;
    alert_level: 'normal' | 'crowded';
  }>;
  transit: TransitVehicle[];
  flood_simulation?: {
    node_water_levels: Record<string, number>;
    flooded_roads: any[];
    affected_nodes: any[];
    max_water_level_cm: number;
  };
  crowd_simulation?: {
    total_active_pedestrians: number;
    crowd_distribution: Record<string, any>;
    panic_index: number;
    safety_status: string;
  };
  disaster?: {
    active: boolean;
    disaster_type?: string;
    severity?: number;
    affected_population?: number;
    infrastructure_damage_percentage?: number;
    estimated_recovery_time_hrs?: number;
    economic_loss_millions?: number;
  };
}

export interface AgentOutput {
  name: string;
  domain: string;
  alert_level: 'normal' | 'warning' | 'danger';
  reasoning: string[];
  predictions: Record<string, any>;
  recommendations: any[];
}

export interface MasterRecommendation {
  explanation: string;
  explainability_chain: string[];
  recommendations: Array<{ title: string; description: string; priority: string }>;
  overall_confidence: number;
  alert_level: 'normal' | 'warning' | 'danger';
}

export interface ActiveCityMetadata {
  name: string;
  lat: number;
  lng: number;
  location_type: string;
  hierarchy: string[];
  population: number;
  area_sq_km: number;
  elevation: number;
  timezone: string;
  datasets: Record<string, { status: 'available' | 'estimated' | 'disabled'; source: string }>;
}

export interface CityGraph {
  nodes: Array<{
    id: string;
    lat: number;
    lng: number;
    type: string;
    population_density: number;
    energy_demand: number;
    pollution_level: number;
  }>;
  edges: Array<{
    from_node: string;
    to_node: string;
    name: string;
    length_m: number;
    speed_limit_kph: number;
    lanes: number;
    base_congestion: number;
  }>;
}

export interface BuildingFeature {
  type: string;
  coordinates: number[][];
  height: number;
}

export interface CityStreamPayload {
  tick: number;
  timestamp: string;
  telemetry: CityTelemetry;
  agent_outputs: Record<string, AgentOutput>;
  master_recommendation: MasterRecommendation;
  predictions: Record<string, any>;
  active_elements: any[];
  active_city?: ActiveCityMetadata;
  buildings?: BuildingFeature[];
  city_graph?: CityGraph;
}

// ── Exponential backoff config ──────────────────────────────────────────────
const BACKOFF_INITIAL_MS = 1_000;
const BACKOFF_MAX_MS = 30_000;
const BACKOFF_MULTIPLIER = 2;

// Resolve WS base URL from Vite env var (falls back to 127.0.0.1 — NOT localhost
// to avoid IPv6 issues on Windows where localhost resolves to ::1 first)
const WS_URL: string =
  (import.meta as any).env?.VITE_WS_URL ?? 'ws://127.0.0.1:8000';

export interface CityStreamState {
  data: CityStreamPayload | null;
  connected: boolean;
  connectionError: string | null;
  retryCount: number;
}

export function useCityStream(): CityStreamState {
  const [data, setData] = useState<CityStreamPayload | null>(null);
  const [connected, setConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  const wsRef = useRef<WebSocket | null>(null);
  const retryCountRef = useRef(0);
  const reconnectTimerRef = useRef<number | null>(null);
  const unmountedRef = useRef(false);

  const getBackoffMs = (attempt: number): number =>
    Math.min(BACKOFF_INITIAL_MS * Math.pow(BACKOFF_MULTIPLIER, attempt), BACKOFF_MAX_MS);

  const connect = () => {
    if (unmountedRef.current) return;

    // Clear any lingering timer
    if (reconnectTimerRef.current !== null) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }

    const wsEndpoint = `${WS_URL}/ws/city-stream`;
    console.debug(`[WS] Connecting to ${wsEndpoint} (attempt #${retryCountRef.current + 1})`);

    let ws: WebSocket;
    try {
      ws = new WebSocket(wsEndpoint);
    } catch (e) {
      console.error('[WS] WebSocket construction failed:', e);
      scheduleReconnect();
      return;
    }

    wsRef.current = ws;

    ws.onopen = () => {
      if (unmountedRef.current) { ws.close(); return; }
      setConnected(true);
      setConnectionError(null);
      retryCountRef.current = 0;
      setRetryCount(0);
      console.info('[WS] Connected to Mirror City stream bus.');
    };

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data as string);
        if (payload.type === 'INCIDENT_VERIFIED') {
          console.info('[WS] Live incident verified:', payload);
        } else {
          setData(payload as CityStreamPayload);
        }
      } catch (err) {
        console.error('[WS] Failed to parse message frame:', err);
      }
    };

    ws.onclose = (event) => {
      if (unmountedRef.current) return;
      setConnected(false);
      const reason = event.reason || `code ${event.code}`;
      console.warn(`[WS] Disconnected (${reason}). Scheduling reconnect...`);
      scheduleReconnect();
    };

    ws.onerror = (event) => {
      console.error('[WS] Socket error — closing for reconnect.', event);
      setConnectionError(
        `WebSocket error on attempt #${retryCountRef.current + 1}. ` +
        `Retrying in ${getBackoffMs(retryCountRef.current) / 1000}s…`
      );
      ws.close();
    };
  };

  const scheduleReconnect = () => {
    if (unmountedRef.current) return;
    retryCountRef.current += 1;
    setRetryCount(retryCountRef.current);
    const delayMs = getBackoffMs(retryCountRef.current - 1);
    console.debug(`[WS] Retry #${retryCountRef.current} in ${delayMs}ms`);
    reconnectTimerRef.current = window.setTimeout(connect, delayMs);
  };

  useEffect(() => {
    unmountedRef.current = false;
    connect();

    return () => {
      unmountedRef.current = true;
      if (reconnectTimerRef.current !== null) clearTimeout(reconnectTimerRef.current);
      if (wsRef.current) {
        wsRef.current.onclose = null; // prevent scheduling a reconnect on intentional close
        wsRef.current.close();
      }
    };
  }, []);

  return { data, connected, connectionError, retryCount };
}
