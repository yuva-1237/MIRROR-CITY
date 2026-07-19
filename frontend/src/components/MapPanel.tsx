import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, Polyline, useMapEvents, useMap } from 'react-leaflet';
import L from 'leaflet';
import { X, Activity, Eye, EyeOff } from 'lucide-react';
import { useLocationStore } from '../store/locationStore';


interface Element {
  id?: number;
  type: string;
  name: string;
  location_geojson: string;
  radius: number;
  cost: number;
  status?: string;
}

interface MapPanelProps {
  elements: Element[];
  onAddElement?: (type: string, name: string, coords: [number, number]) => void;
  onRemoveElement?: (id: number) => void;
  selectedTool?: string | null;
  setSelectedTool?: (tool: string | null) => void;
  trafficData?: any;
  // Extended props used by CommandCenter live-twin view
  scenarioId?: number;
  authToken?: string;
  onSelectCoordinates?: (lat: number, lng: number) => void;
  activeCity?: any;
  graph?: any;
}


// Custom markers using CSS to avoid missing Leaflet asset issues
const getMarkerIcon = (type: string) => {
  let color = '#2563eb'; // blue
  let symbol = '🚇';
  if (type === 'hospital') { color = '#ef4444'; symbol = '🏥'; }
  else if (type === 'green_space') { color = '#10b981'; symbol = '🌳'; }
  else if (type === 'road_widening') { color = '#eab308'; symbol = '↔️'; }
  else if (type === 'flyover') { color = '#a855f7'; symbol = '🌉'; }
  else if (type === 'closure') { color = '#6b7280'; symbol = '🚫'; }

  return L.divIcon({
    html: `
      <div style="
        width: 34px;
        height: 34px;
        background-color: ${color};
        border: 2px solid white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        box-shadow: 0 0 12px ${color};
        transform: translate(-17px, -17px);
        cursor: pointer;
      " class="transition-transform hover:scale-110">
        ${symbol}
      </div>
    `,
    className: 'custom-neon-icon',
    iconSize: [0, 0],
    iconAnchor: [0, 0]
  });
};

export default function MapPanel({
  elements = [],
  onAddElement,
  onRemoveElement,
  selectedTool,
  setSelectedTool,
  trafficData,
  onSelectCoordinates,
  activeCity,
  graph
}: MapPanelProps) {
  const { activeLocation } = useLocationStore();
  const currentCity = activeCity || activeLocation;

  const [showOverlays, setShowOverlays] = useState(true);
  const [gridNodes, setGridNodes] = useState<any[]>([]);
  const [gridEdges, setGridEdges] = useState<any[]>([]);

  // Helper component to animated fly-to Leaflet dynamically
  function FlyToLocation({ lat, lng, locationType }: { lat: number; lng: number; locationType?: string }) {
    const map = useMap();
    useEffect(() => {
      const zoom = locationType === 'village' ? 13 : locationType === 'metro' ? 11 : 12;
      map.flyTo([lat, lng], zoom, {
        animate: true,
        duration: 1.5
      });
    }, [lat, lng, locationType]);
    return null;
  }

  // Generate grid coordinates centered dynamically on the active city.
  // When the user selects a new city, this effect re-runs immediately.
  // Checks if the incoming graph is actually for the current location; if not, falls back to synthetic grid.
  useEffect(() => {
    const hasValidGraph = () => {
      if (!graph || !graph.nodes || graph.nodes.length === 0 || !currentCity) return false;
      const firstNode = graph.nodes[0];
      const dist = Math.abs(firstNode.lat - currentCity.lat) + Math.abs(firstNode.lng - currentCity.lng);
      return dist < 0.05; // ~5km range check to avoid displaying a stale city's graph
    };

    if (hasValidGraph()) {
      setGridNodes(graph.nodes);
      setGridEdges(graph.edges);
    } else {
      const nodes: any[] = [];
      const edges: any[] = [];
      const centerLat = currentCity?.lat ?? 37.7749;
      const centerLng = currentCity?.lng ?? -122.4194;
      const coordSpacing = 0.005;

      for (let r = 0; r < 6; r++) {
        for (let c = 0; c < 6; c++) {
          const id = `node_${r}_${c}`;
          const lat = centerLat + (r - 2.5) * coordSpacing;
          const lng = centerLng + (c - 2.5) * coordSpacing;
          nodes.push({ id, lat, lng });
        }
      }

      // Horizontal edges
      for (let r = 0; r < 6; r++) {
        for (let c = 0; c < 5; c++) {
          edges.push({
            from: `node_${r}_${c}`,
            to: `node_${r}_${c+1}`,
            r,
            c
          });
        }
      }

      // Vertical edges
      for (let r = 0; r < 5; r++) {
        for (let c = 0; c < 6; c++) {
          edges.push({
            from: `node_${r}_${c}`,
            to: `node_${r+1}_${c}`,
            r,
            c
          });
        }
      }

      setGridNodes(nodes);
      setGridEdges(edges);
    }
  }, [graph, currentCity?.lat, currentCity?.lng]);

  // Map Click handler component
  function MapEvents() {
    useMapEvents({
      click(e) {
        const latlng = e.latlng;
        // Pass coordinates to parent (e.g. IncidentReporter)
        if (onSelectCoordinates) {
          onSelectCoordinates(latlng.lat, latlng.lng);
        }
        if (selectedTool && onAddElement) {
          const name = `Proposed ${selectedTool.replace('_', ' ').toUpperCase()}`;
          onAddElement(selectedTool, name, [latlng.lng, latlng.lat]);
          if (setSelectedTool) setSelectedTool(null);
        }
      },
    });
    return null;
  }

  // Returns color based on simulated congestion
  const getTrafficColor = (edge: any) => {
    if (!showOverlays) return 'rgba(255,255,255,0.15)';
    // Use real congestion value from dynamic graph edges if available
    const congestion = edge.congestion ?? edge.base_congestion;
    if (congestion !== undefined) {
      if (congestion > 0.75) return '#ef4444'; // Red – heavily congested
      if (congestion > 0.4)  return '#f97316'; // Orange – moderate
      return '#10b981';                          // Green – free flow
    }
    // Fallback: derive from position when trafficData overlay is active
    if (trafficData) {
      const factor = ((edge.r ?? 0) + (edge.c ?? 0)) % 3;
      if (factor === 0) return '#ef4444';
      if (factor === 1) return '#f97316';
      return '#10b981';
    }
    return '#3b82f6';
  };

  return (
    <div className="w-full h-full relative border border-brand-border rounded-2xl overflow-hidden bg-brand-dark map-container-isolate">
      {/* Floating Toolbar Controls */}
      <div className="absolute top-4 left-4 z-[1000] flex flex-col gap-2">
        <button
          onClick={() => setShowOverlays(!showOverlays)}
          className={`flex items-center gap-2 px-3 py-2 text-xs font-semibold rounded-lg shadow-lg border transition-all ${
            showOverlays
              ? 'bg-brand-neonCyan/20 text-brand-neonCyan border-brand-neonCyan/40'
              : 'bg-brand-panel text-slate-400 border-brand-border hover:text-white'
          }`}
        >
          {showOverlays ? <Eye size={14} /> : <EyeOff size={14} />}
          {showOverlays ? 'GNN Overlays: ON' : 'GNN Overlays: OFF'}
        </button>
      </div>

      {selectedTool && (
        <div className="absolute top-4 right-4 z-[1000] bg-brand-neonOrange/20 border border-brand-neonOrange/40 text-brand-neonOrange px-4 py-2 rounded-xl text-xs font-bold animate-pulse flex items-center gap-2 shadow-lg">
          <Activity size={14} />
          Click anywhere on the GIS map to deploy a {selectedTool.replace('_', ' ')}.
          <button onClick={() => setSelectedTool && setSelectedTool(null)} className="hover:text-white ml-2">
            <X size={14} />
          </button>
        </div>
      )}

      {/* Map Container */}
      <MapContainer
        center={
          currentCity?.lat && currentCity?.lng
            ? [currentCity.lat, currentCity.lng]
            : [37.7749, -122.4194]
        }
        zoom={currentCity ? (currentCity.location_type === 'village' ? 13 : currentCity.location_type === 'metro' ? 11 : 12) : 14}
        zoomControl={true}
        scrollWheelZoom={true}
        className="w-full h-full"
      >
        <MapEvents />
        {/* Dynamically re-center and animate fly-to on currentCity change */}
        {currentCity?.lat && currentCity?.lng && (
          <FlyToLocation lat={currentCity.lat} lng={currentCity.lng} locationType={currentCity.location_type} />
        )}
        {/* CartoDB Dark Matter base tile layer */}
        <TileLayer
          attribution='&copy; <a href="https://carto.com/">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />

        {/* Draw Simulated Road Infrastructure Graph */}
        {gridEdges.map((edge, idx) => {
          // Support both backend key naming (from_node/to_node) and synthetic (from/to)
          const fromId = edge.from_node ?? edge.from;
          const toId   = edge.to_node   ?? edge.to;
          const fromNode = gridNodes.find(n => n.id === fromId);
          const toNode   = gridNodes.find(n => n.id === toId);
          if (!fromNode || !toNode) return null;

          const polyColor = getTrafficColor(edge);
          const weight = showOverlays ? 4 : 2.5;

          return (
            <Polyline
              key={idx}
              positions={[[fromNode.lat, fromNode.lng], [toNode.lat, toNode.lng]]}
              color={polyColor}
              weight={weight}
              opacity={0.8}
            />
          );
        })}

        {/* Draw placed Elements (Markers & Radius Circles) */}
        {elements.map((elem, idx) => {
          const loc = JSON.parse(elem.location_geojson);
          const [lng, lat] = loc.coordinates;
          
          let circleColor = '#3b82f6';
          if (elem.type === 'hospital') circleColor = '#ef4444';
          else if (elem.type === 'green_space') circleColor = '#10b981';

          return (
            <React.Fragment key={elem.id || idx}>
              <Marker position={[lat, lng]} icon={getMarkerIcon(elem.type)}>
                <Popup>
                  <div className="text-slate-900 text-xs font-semibold p-1">
                    <div className="font-bold text-sm mb-1">{elem.name}</div>
                    <div className="text-slate-500 capitalize">Asset: {elem.type.replace('_', ' ')}</div>
                    <div className="text-blue-600 font-bold mt-1">
                      Cost: {elem.cost > 0 ? `$${elem.cost.toLocaleString()}` : 'Existing'}
                    </div>
                    {elem.id && onRemoveElement && (
                      <button
                        onClick={() => onRemoveElement(elem.id!)}
                        className="mt-2 w-full bg-red-500 text-white rounded px-2 py-1 hover:bg-red-600 font-bold transition-all"
                      >
                        Remove Asset
                      </button>
                    )}
                  </div>
                </Popup>
              </Marker>
              
              {/* Radius Circle overlay */}
              {showOverlays && elem.radius > 0 && (
                <Circle
                  center={[lat, lng]}
                  radius={elem.radius}
                  pathOptions={{
                    color: circleColor,
                    fillColor: circleColor,
                    fillOpacity: 0.08,
                    weight: 1
                  }}
                />
              )}
            </React.Fragment>
          );
        })}
      </MapContainer>
    </div>
  );
}
