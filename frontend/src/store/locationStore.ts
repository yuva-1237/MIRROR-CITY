import { create } from 'zustand';
import { apiFetch, apiPost } from '../lib/api';

export interface LocationObject {
  name: string;
  lat: number;
  lng: number;
  location_type: string;
  hierarchy: string[];
  population: number;
  area_sq_km: number;
  elevation: number;
  timezone: string;
  confidence?: 'preset' | 'geocoded' | 'synthetic';
  bounding_box?: [number, number, number, number];
  datasets?: Record<string, { status: string; source: string }>;
  error?: string;
}

interface LocationState {
  activeLocation: LocationObject | null;
  searchResults: LocationObject[];
  searchQuery: string;
  isSearching: boolean;
  isLoadingTwin: boolean;
  searchError: string | null;
  loadError: string | null;
  
  setSearchQuery: (query: string) => void;
  clearSearch: () => void;
  setActiveLocation: (loc: LocationObject | null) => void;
  search: (query: string, token: string) => Promise<void>;
  loadTwin: (location: LocationObject, token: string) => Promise<void>;
  initActiveLocation: (token: string) => Promise<void>;
}

let searchAbortController: AbortController | null = null;

export const useLocationStore = create<LocationState>((set, get) => ({
  activeLocation: null,
  searchResults: [],
  searchQuery: '',
  isSearching: false,
  isLoadingTwin: false,
  searchError: null,
  loadError: null,

  setSearchQuery: (query: string) => set({ searchQuery: query }),
  
  clearSearch: () => set({ searchResults: [], searchError: null, isSearching: false }),

  setActiveLocation: (loc: LocationObject | null) => set({ activeLocation: loc }),

  search: async (query: string, token: string) => {
    const cleanQuery = query.trim();
    set({ searchQuery: query, searchError: null });
    
    if (!cleanQuery) {
      set({ searchResults: [], isSearching: false });
      return;
    }

    // Cancel in-flight search request
    if (searchAbortController) {
      searchAbortController.abort();
    }
    searchAbortController = new AbortController();
    const currentController = searchAbortController;

    set({ isSearching: true });

    try {
      const data = await apiFetch<LocationObject[]>(
        `/api/geospatial/search?query=${encodeURIComponent(cleanQuery)}`,
        {
          token,
          signal: currentController.signal,
        } as any
      );

      if (get().searchQuery === query) {
        set({ searchResults: data, isSearching: false, searchError: null });
      }
    } catch (err: any) {
      if (err.name === 'AbortError' || (err instanceof Error && err.name === 'AbortError')) {
        return;
      }
      if (get().searchQuery === query) {
        const errMsg = err?.message ?? 'Failed to search location.';
        const results = err?.status === 404 && err?.detail?.results ? err.detail.results : [];
        set({
          searchResults: results,
          isSearching: false,
          searchError: err?.status === 404 && err?.detail?.message ? err.detail.message : errMsg,
        });
      }
    }
  },

  loadTwin: async (location: LocationObject, token: string) => {
    set({ isLoadingTwin: true, loadError: null });
    try {
      const res = await apiPost<any>(
        '/api/geospatial/load',
        location,
        { token }
      );
      
      const activeLoc = res.active_city || location;
      set({
        activeLocation: activeLoc,
        isLoadingTwin: false,
        searchResults: [],
        searchQuery: '',
      });
    } catch (err: any) {
      console.error('[LocationStore] loadTwin failed:', err);
      set({
        isLoadingTwin: false,
        loadError: err?.message ?? 'Failed to load Digital Twin.',
      });
      throw err;
    }
  },

  initActiveLocation: async (token: string) => {
    try {
      const data = await apiFetch<{ active_city: LocationObject | null }>('/api/geospatial/active', { token });
      if (data && data.active_city) {
        set({ activeLocation: data.active_city });
      }
    } catch (err) {
      console.error('[LocationStore] initActiveLocation failed:', err);
    }
  }
}));
