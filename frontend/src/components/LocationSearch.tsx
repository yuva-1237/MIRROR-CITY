import React, { useEffect, useState, useRef } from 'react';
import { Search, RefreshCw, AlertCircle, History, MapPin, X } from 'lucide-react';
import { useLocationStore, LocationObject } from '../store/locationStore';

interface LocationSearchProps {
  authToken: string;
}

export default function LocationSearch({ authToken }: LocationSearchProps) {
  const {
    searchResults,
    searchQuery,
    isSearching,
    isLoadingTwin,
    searchError,
    search,
    loadTwin,
    clearSearch,
    setSearchQuery,
  } = useLocationStore();

  const [showDropdown, setShowDropdown] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const [recentSearches, setRecentSearches] = useState<LocationObject[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);
  const debounceTimerRef = useRef<number | null>(null);

  // Load recent searches from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem('mc_recent_searches');
      if (stored) {
        setRecentSearches(JSON.parse(stored));
      }
    } catch (e) {
      console.warn('[LocationSearch] Failed to load search history:', e);
    }
  }, []);

  // Save to recent searches
  const saveToRecent = (location: LocationObject) => {
    const filtered = recentSearches.filter(
      (item) => item.name !== location.name || item.lat !== location.lat || item.lng !== location.lng
    );
    const updated = [location, ...filtered].slice(0, 5);
    setRecentSearches(updated);
    try {
      localStorage.setItem('mc_recent_searches', JSON.stringify(updated));
    } catch (e) {
      console.warn('[LocationSearch] Failed to save search history:', e);
    }
  };

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Handle Input Changes with Debounce
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchQuery(value);
    setHighlightedIndex(-1);

    if (debounceTimerRef.current !== null) {
      window.clearTimeout(debounceTimerRef.current);
    }

    if (value.trim()) {
      setShowDropdown(true);
      debounceTimerRef.current = window.setTimeout(() => {
        search(value, authToken);
      }, 300);
    } else {
      clearSearch();
      setShowDropdown(true);
    }
  };

  // Handle Form Submit
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    if (debounceTimerRef.current !== null) {
      window.clearTimeout(debounceTimerRef.current);
    }
    
    setShowDropdown(true);
    search(searchQuery, authToken);
  };

  // Select a location and load twin
  const handleSelectLocation = async (location: LocationObject) => {
    try {
      setShowDropdown(false);
      saveToRecent(location);
      await loadTwin(location, authToken);
    } catch (err) {
      console.error('[LocationSearch] Failed to load twin:', err);
    }
  };

  // Keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    const listLength = searchResults.length > 0 ? searchResults.length : recentSearches.length;
    const items = searchResults.length > 0 ? searchResults : recentSearches;

    if (!showDropdown || listLength === 0) {
      if (e.key === 'ArrowDown') {
        setShowDropdown(true);
      }
      return;
    }

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHighlightedIndex((prev) => (prev + 1 >= listLength ? 0 : prev + 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHighlightedIndex((prev) => (prev - 1 < 0 ? listLength - 1 : prev - 1));
    } else if (e.key === 'Enter') {
      if (highlightedIndex >= 0 && highlightedIndex < listLength) {
        e.preventDefault();
        handleSelectLocation(items[highlightedIndex]);
      }
    } else if (e.key === 'Escape') {
      e.preventDefault();
      setShowDropdown(false);
      setHighlightedIndex(-1);
    }
  };

  const hasResults = searchResults.length > 0;
  const hasHistory = recentSearches.length > 0;

  return (
    <div ref={containerRef} className="relative w-full z-[100]">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search global town, village, city..."
            value={searchQuery}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            onFocus={() => setShowDropdown(true)}
            className="w-full bg-[#0a0f1d] border border-brand-border rounded-lg pl-9 pr-8 py-2 text-xs text-white placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-brand-neonCyan focus:border-brand-neonCyan shadow-inner"
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => {
                setSearchQuery('');
                clearSearch();
                setShowDropdown(true);
              }}
              className="absolute right-3 top-2.5 text-slate-400 hover:text-white transition"
            >
              <X size={14} />
            </button>
          )}
        </div>
        <button
          type="submit"
          disabled={isSearching || isLoadingTwin}
          className="bg-brand-accent hover:bg-brand-accent/80 text-white font-bold text-xs px-4 py-2 rounded-lg transition-all disabled:opacity-50 flex items-center gap-1.5 shrink-0 shadow-md"
        >
          {(isSearching || isLoadingTwin) ? (
            <RefreshCw className="h-3.5 w-3.5 animate-spin" />
          ) : null}
          RESOLVE
        </button>
      </form>

      {/* Screen Reader Announcements */}
      <div className="sr-only" aria-live="polite">
        {isSearching && 'Searching locations...'}
        {!isSearching && hasResults && `${searchResults.length} location results found.`}
        {searchError && `Error: ${searchError}`}
      </div>

      {/* Dropdown Options List - Solid opaque dark background */}
      {showDropdown && (
        <div className="absolute top-full left-0 right-0 mt-2 z-[9999] bg-[#090d16] border border-brand-border/80 rounded-xl shadow-[0_20px_50px_rgba(0,0,0,0.98)] p-3 max-h-[350px] overflow-y-auto animate-fadeIn opacity-100">
          {/* Active Error state */}
          {searchError && (
            <div className="p-3 text-brand-neonOrange text-xs flex gap-2 items-start bg-slate-950 border border-brand-neonOrange/40 rounded-lg mb-2">
              <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
              <div>
                <p className="font-bold">Search Unresolved</p>
                <p className="text-[10px] text-slate-400 mt-1">{searchError}</p>
              </div>
            </div>
          )}

          {/* Autocomplete Results */}
          {isSearching ? (
            <div className="flex items-center gap-2.5 px-3 py-4 text-xs text-slate-300 font-mono">
              <RefreshCw className="h-4 w-4 animate-spin text-brand-neonCyan" />
              RESOLVING SPATIAL COORDINATES...
            </div>
          ) : hasResults ? (
            <div>
              <div className="flex justify-between items-center px-2 pb-2 border-b border-brand-border/60 mb-2">
                <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider font-mono">Resolved Places</span>
                <span className="text-[8px] text-slate-400 font-mono">Use arrow keys to navigate | Enter to select</span>
              </div>
              <div className="space-y-1.5">
                {searchResults.map((city, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleSelectLocation(city)}
                    onMouseEnter={() => setHighlightedIndex(idx)}
                    className={`w-full text-left p-2.5 rounded-lg border transition flex justify-between items-center group font-sans ${
                      highlightedIndex === idx
                        ? 'bg-blue-600/50 border-blue-400 text-white shadow-md'
                        : 'bg-[#111726] border-brand-border/60 hover:bg-[#1a2338] hover:border-brand-border text-slate-200'
                    }`}
                  >
                    <div className="flex-1 pr-2 min-w-0">
                      <h5 className="text-xs font-bold text-slate-200 group-hover:text-brand-neonCyan flex items-center gap-1.5 truncate">
                        <MapPin size={12} className="text-slate-400 group-hover:text-brand-neonCyan shrink-0" />
                        <span className="truncate">{city.name}</span>
                      </h5>
                      <p className="text-[9px] text-slate-400 mt-0.5 truncate">
                        {Array.isArray(city.hierarchy) && city.hierarchy.length > 0 ? city.hierarchy.join(' > ') : 'Global Coordinate'}
                      </p>
                      <p className="text-[8px] text-slate-500 mt-0.5 font-mono">
                        Coordinates: {city.lat.toFixed(4)}, {city.lng.toFixed(4)}
                      </p>
                    </div>
                    <span className="text-[9px] font-mono text-slate-300 uppercase bg-[#060912] px-2 py-0.5 rounded border border-brand-border/60 shrink-0 font-semibold">
                      {city.location_type || 'PLACE'}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          ) : !searchQuery.trim() && hasHistory ? (
            /* Recent Searches when search box is empty */
            <div>
              <div className="flex justify-between items-center px-2 pb-2 border-b border-brand-border/60 mb-2">
                <span className="text-[10px] font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5 font-mono">
                  <History size={12} className="text-brand-neonCyan" /> Recent Searches
                </span>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    localStorage.removeItem('mc_recent_searches');
                    setRecentSearches([]);
                  }}
                  className="text-[9px] text-red-400 hover:text-red-300 uppercase font-mono font-semibold px-2 py-0.5 rounded bg-red-950/40 hover:bg-red-900/60 border border-red-800/40 transition"
                >
                  Clear History
                </button>
              </div>
              <div className="space-y-1.5">
                {recentSearches.map((city, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleSelectLocation(city)}
                    onMouseEnter={() => setHighlightedIndex(idx)}
                    className={`w-full text-left p-2.5 rounded-lg border transition flex justify-between items-center group font-sans ${
                      highlightedIndex === idx
                        ? 'bg-blue-600/50 border-blue-400 text-white shadow-md'
                        : 'bg-[#111726] border-brand-border/60 hover:bg-[#1a2338] hover:border-brand-border text-slate-200'
                    }`}
                  >
                    <div className="flex-1 pr-3 min-w-0">
                      <h5 className="text-xs font-bold text-slate-100 group-hover:text-brand-neonCyan flex items-center gap-1.5 truncate">
                        <History size={12} className="text-slate-400 group-hover:text-brand-neonCyan shrink-0" />
                        <span className="truncate">{city.name}</span>
                      </h5>
                      <p className="text-[9px] text-slate-400 mt-0.5 truncate">
                        {Array.isArray(city.hierarchy) && city.hierarchy.length > 0
                          ? city.hierarchy.join(' > ')
                          : city.name || 'Global Coordinate'}
                      </p>
                      <p className="text-[8px] text-slate-500 mt-0.5 font-mono">
                        Coordinates: {city.lat.toFixed(4)}, {city.lng.toFixed(4)}
                      </p>
                    </div>
                    <span className="text-[9px] font-mono text-brand-neonCyan uppercase bg-[#060912] px-2 py-0.5 rounded border border-brand-border/60 shrink-0 font-semibold shadow-sm">
                      {city.location_type || 'PLACE'}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          ) : searchQuery.trim() && !isSearching ? (
            /* Empty state when query yields no results */
            <div className="p-4 text-slate-400 text-xs text-center font-mono">
              NO GEOGRAPHIC ENTITIES MATCHED
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}
