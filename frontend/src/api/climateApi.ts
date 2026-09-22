/**
 * api/climateApi.ts — Dedicated Climate and ENSO Frontend API Client
 *
 * Centralizes all climate intelligence communication with backend services.
 * Implements Deliverable I:
 *  - getENSO()
 *  - getClimateImpact(location)
 *  - getClimateTimeline()
 *  - simulateClimateScenario(request)
 */

import { API_BASE_URL } from '../lib/api';

export type EnsoPhase = 'EL_NINO' | 'LA_NINA' | 'NEUTRAL' | 'UNKNOWN';
export type EnsoIntensity = 'WEAK' | 'MODERATE' | 'STRONG' | 'UNKNOWN';
export type ImpactLevel = 'LOW' | 'NORMAL' | 'MODERATE' | 'ELEVATED' | 'HIGH' | 'EXTREME' | 'UNKNOWN';

export interface SourceMeta {
  name: string;
  url: string;
}

export interface EnsoResponseData {
  phase: EnsoPhase;
  intensity: EnsoIntensity;
  confidence: number;
  anomaly?: number | null;
  observationPeriod?: string | null;
  forecastPeriod?: string | null;
  source: SourceMeta;
  updatedAt: string;
  soi?: number;
  sstObserved?: number;
}

export type EnsoDataModel = EnsoResponseData;

export interface ImpactSector {
  level: ImpactLevel;
  confidence: number;
  score?: number;
  drivers?: string[];
  explanation?: string;
}

export interface CityImpactResponseData {
  city: string;
  country?: string;
  coordinates?: [number, number];
  enso: {
    phase: EnsoPhase;
    intensity: EnsoIntensity;
  };
  impacts: {
    rainfall: ImpactSector;
    flood: ImpactSector;
    drought: ImpactSector;
    heat: ImpactSector;
    waterStress?: ImpactSector;
    agriculture?: ImpactSector;
    infrastructure?: ImpactSector;
    energy_demand?: ImpactSector;
  };
  drivers: string[];
  climate_dna?: any;
  teleconnection?: any;
  summary_rationale?: string;
}

export interface LocationQuery {
  city?: string;
  latitude?: number;
  lat?: number;
  longitude?: number;
  lng?: number;
  country?: string;
  elevation?: number;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
  };
}

/**
 * Fetch current normalized ENSO status from /api/climate/enso
 */
export async function getENSO(): Promise<ApiResponse<EnsoResponseData>> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/climate/enso`, {
      headers: { Accept: 'application/json' },
    });

    const body = await res.json();
    if (!res.ok || !body.success) {
      return {
        success: false,
        error: body.error || {
          code: 'ENSO_DATA_UNAVAILABLE',
          message: 'ENSO data is temporarily unavailable.',
        },
      };
    }

    return body;
  } catch (err: any) {
    return {
      success: false,
      error: {
        code: 'NETWORK_ERROR',
        message: err.message || 'Unable to connect to climate intelligence service.',
      },
    };
  }
}

/**
 * Fetch city-level climate impact assessment from /api/climate/impact
 */
export async function getClimateImpact(
  location: LocationQuery
): Promise<ApiResponse<CityImpactResponseData>> {
  try {
    const params = new URLSearchParams();
    if (location.city) params.append('city', location.city);
    const lat = location.latitude ?? location.lat;
    const lng = location.longitude ?? location.lng;
    if (lat !== undefined) params.append('lat', lat.toString());
    if (lng !== undefined) params.append('lng', lng.toString());
    if (location.country) params.append('country', location.country);
    if (location.elevation !== undefined) params.append('elevation', location.elevation.toString());

    const res = await fetch(`${API_BASE_URL}/api/climate/impact?${params.toString()}`, {
      headers: { Accept: 'application/json' },
    });

    const body = await res.json();
    if (!res.ok || !body.success) {
      return {
        success: false,
        error: body.error || {
          code: 'IMPACT_DATA_UNAVAILABLE',
          message: 'City climate impact data is temporarily unavailable.',
        },
      };
    }

    return body;
  } catch (err: any) {
    return {
      success: false,
      error: {
        code: 'NETWORK_ERROR',
        message: err.message || 'Unable to fetch city climate impact.',
      },
    };
  }
}

/**
 * Fetch historical timeline and seasonal outlook from /api/climate/timeline
 */
export async function getClimateTimeline(): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/climate/timeline`, {
    headers: { Accept: 'application/json' },
  });
  if (!res.ok) {
    throw new Error('Failed to load climate timeline.');
  }
  return res.json();
}

/**
 * Fetch Pacific Ocean to city teleconnection propagation vector
 */
export async function getTeleconnectionVisuals(params: {
  lat: number;
  lng: number;
  city?: string;
  token?: string;
}): Promise<any> {
  const query = new URLSearchParams({
    lat: params.lat.toString(),
    lng: params.lng.toString(),
    city: params.city || 'Chennai',
  });
  const headers: Record<string, string> = { Accept: 'application/json' };
  if (params.token) headers['Authorization'] = `Bearer ${params.token}`;

  const res = await fetch(`${API_BASE_URL}/api/climate/teleconnection?${query.toString()}`, {
    headers,
  });
  if (!res.ok) {
    throw new Error('Failed to load teleconnection propagation data.');
  }
  return res.json();
}

/**
 * Run counterfactual scenario simulation
 */
export async function simulateClimateScenario(params: {
  city: string;
  lat?: number;
  lng?: number;
  target_phase: string;
  elevation?: number;
  token?: string;
}): Promise<any> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  };
  if (params.token) headers['Authorization'] = `Bearer ${params.token}`;

  const res = await fetch(`${API_BASE_URL}/api/climate/simulate`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      city: params.city,
      lat: params.lat,
      lng: params.lng,
      target_phase: params.target_phase,
      elevation: params.elevation,
    }),
  });
  if (!res.ok) {
    throw new Error('Failed to run climate simulation.');
  }
  return res.json();
}


