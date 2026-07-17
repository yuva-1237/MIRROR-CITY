import { useEffect, useState } from 'react';
import DeckGL from '@deck.gl/react';
import { ScatterplotLayer, PathLayer, PolygonLayer } from '@deck.gl/layers';
import { Map } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';

interface LiveMap3DProps {
  telemetry: any;
  onSelectCoordinates?: (lat: number, lng: number) => void;
  activeCity?: any;
  buildings?: any[];
  graph?: any;
}

export default function LiveMap3D({ telemetry, onSelectCoordinates, activeCity, buildings, graph }: LiveMap3DProps) {
  if (!telemetry) return null;

  // Dynamic viewport — re-derives when activeCity changes
  const centerLng = activeCity?.lng ?? -122.4194;
  const centerLat = activeCity?.lat ?? 37.7749;
  const locType   = activeCity?.location_type ?? 'city';
  const zoomByType: Record<string, number> = {
    village: 13,
    town: 12.5,
    city: 13,
    metro: 11.5,
    coastal: 12,
    mountain: 12,
    desert: 12,
    industrial: 12,
  };

  const [viewState, setViewState] = useState({
    longitude: centerLng,
    latitude: centerLat,
    zoom: zoomByType[locType] ?? 13,
    pitch: 45,
    bearing: 0,
    maxZoom: 18,
    minZoom: 9,
  });

  // Fly to new city when activeCity changes
  useEffect(() => {
    if (activeCity?.lat && activeCity?.lng) {
      setViewState(vs => ({
        ...vs,
        longitude: activeCity.lng,
        latitude: activeCity.lat,
        zoom: zoomByType[activeCity.location_type ?? 'city'] ?? 13,
      }));
    }
  }, [activeCity?.lat, activeCity?.lng, activeCity?.location_type]);

  // ── 1. Transit vehicles ──────────────────────────────────────────────────
  const vehicles = (telemetry.transit || []).map((v: any) => ({
    position: [v.lng, v.lat],
    color: v.type === 'metro' ? [139, 92, 246] : [6, 182, 212],
    radius: 40,
    name: `${v.route} (${v.id})`,
  }));

  // ── 2. Road network edges from dynamic graph ──────────────────────────────
  const roadPaths: any[] = [];
  if (graph?.nodes && graph?.edges) {
    const nodeMap: Record<string, [number, number]> = {};
    for (const n of graph.nodes) {
      nodeMap[n.id] = [n.lng, n.lat];
    }
    for (const e of graph.edges) {
      // Backend sends from_node/to_node; fallback to from/to for synthetic graphs
      const fromId = e.from_node ?? e.from;
      const toId   = e.to_node   ?? e.to;
      const from   = nodeMap[fromId];
      const to     = nodeMap[toId];
      if (from && to) {
        const congestion = e.congestion ?? e.base_congestion ?? 0.2;
        let color: [number, number, number, number] = [59, 130, 246, 200];
        if (congestion > 0.75) color = [239, 68, 68, 220];
        else if (congestion > 0.4) color = [249, 115, 22, 210];
        else color = [16, 185, 129, 200];
        roadPaths.push({ path: [from, to], color });
      }
    }
  }

  // ── 3. Building footprint polygons from dynamic buildings list ────────────
  const buildingPolygons: any[] = [];
  if (buildings && buildings.length) {
    for (const b of buildings) {
      // buildings have a bbox: [minLng, minLat, maxLng, maxLat] or coordinates array
      let polygon: [number, number][] | null = null;
      if (b.coordinates && b.coordinates.length >= 3) {
        polygon = b.coordinates;
      } else if (b.bbox) {
        const [minLng, minLat, maxLng, maxLat] = b.bbox;
        polygon = [
          [minLng, minLat],
          [maxLng, minLat],
          [maxLng, maxLat],
          [minLng, maxLat],
        ];
      }
      if (polygon) {
        const elevation = b.floors ? b.floors * 3 : 12;
        buildingPolygons.push({
          polygon,
          elevation,
          fillColor: b.type === 'hospital'
            ? [239, 68, 68, 160]
            : b.type === 'school'
            ? [234, 179, 8, 160]
            : b.type === 'park'
            ? [16, 185, 129, 120]
            : [99, 102, 241, 140],
        });
      }
    }
  }

  // ── 4. Layers ─────────────────────────────────────────────────────────────
  const layers = [
    // Building extrusion
    buildingPolygons.length > 0 && new PolygonLayer({
      id: 'buildings',
      data: buildingPolygons,
      extruded: true,
      wireframe: false,
      getPolygon: (d: any) => d.polygon,
      getElevation: (d: any) => d.elevation,
      getFillColor: (d: any) => d.fillColor,
      getLineColor: [80, 80, 120],
      lineWidthMinPixels: 1,
      pickable: false,
    }),

    // Road network
    roadPaths.length > 0 && new PathLayer({
      id: 'road-graph',
      data: roadPaths,
      getPath: (d: any) => d.path,
      getColor: (d: any) => d.color,
      getWidth: 5,
      widthMinPixels: 2,
      pickable: false,
      opacity: 0.85,
    }),

    // Transit vehicles
    new ScatterplotLayer({
      id: 'transit-dots',
      data: vehicles,
      getPosition: (d: any) => d.position,
      getFillColor: (d: any) => d.color,
      getRadius: (d: any) => d.radius,
      pickable: true,
      onClick: (info: any) => {
        if (info.object && onSelectCoordinates) {
          const [lng, lat] = info.object.position;
          onSelectCoordinates(lat, lng);
        }
      },
    }),
  ].filter(Boolean) as any[];

  return (
    <div className="w-full h-full relative map-container-isolate">
      <DeckGL
        viewState={viewState}
        onViewStateChange={({ viewState: vs }: any) => setViewState(vs)}
        controller={true}
        layers={layers}
        getCursor={({ isHovering }: any) => (isHovering ? 'pointer' : 'default')}
      >
        <Map
          mapStyle="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
          reuseMaps
        />
      </DeckGL>

      {/* Legend overlay */}
      <div className="absolute bottom-2 right-2 z-[1000] bg-slate-900/85 border border-brand-border p-2.5 rounded-lg text-[10px] font-mono space-y-1">
        <div className="text-slate-300 font-bold uppercase tracking-wide mb-1">3D Deck.gl Twin</div>
        {activeCity && (
          <div className="text-brand-neonCyan font-bold">{activeCity.name}</div>
        )}
        <div className="flex items-center gap-1.5 text-slate-400"><span className="w-3 h-1 inline-block bg-red-500 rounded" /> Congested</div>
        <div className="flex items-center gap-1.5 text-slate-400"><span className="w-3 h-1 inline-block bg-orange-500 rounded" /> Moderate</div>
        <div className="flex items-center gap-1.5 text-slate-400"><span className="w-3 h-1 inline-block bg-emerald-500 rounded" /> Free Flow</div>
        <div className="flex items-center gap-1.5 text-slate-400"><span className="w-3 h-3 inline-block bg-indigo-400/60 rounded-sm" /> Buildings</div>
        <div className="flex items-center gap-1.5 text-slate-400"><span className="w-2 h-2 inline-block rounded-full bg-cyan-400" /> Bus</div>
        <div className="flex items-center gap-1.5 text-slate-400"><span className="w-2 h-2 inline-block rounded-full bg-purple-500" /> Metro</div>
      </div>
    </div>
  );
}
