import { useEffect, useState, useMemo } from 'react';
import DeckGL from '@deck.gl/react';
import { PolygonLayer, ArcLayer, ColumnLayer } from '@deck.gl/layers';
import { Map } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';
import { FlyToInterpolator } from '@deck.gl/core';
import { useLocationStore } from '../store/locationStore';
import { SAN_FRANCISCO_3D_BUILDINGS, Building3D } from '../data/sanFrancisco3DBuildings';
import { Compass, Building2, Flame, Navigation, Waves } from 'lucide-react';

interface LiveMap3DProps {
  telemetry: any;
  onSelectCoordinates?: (lat: number, lng: number) => void;
  activeCity?: any;
  buildings?: any[];
  graph?: any;
}

export default function LiveMap3D({ telemetry, onSelectCoordinates, activeCity, buildings, graph }: LiveMap3DProps) {
  if (!telemetry) return null;

  const { activeLocation } = useLocationStore();
  const currentCity = activeCity || activeLocation;

  // Center coordinates (Default: San Francisco Financial District)
  const centerLng = currentCity?.lng ?? -122.4042;
  const centerLat = currentCity?.lat ?? 37.7895;

  const [viewState, setViewState] = useState<any>({
    longitude: centerLng,
    latitude: centerLat,
    zoom: 14.2,
    pitch: 58,
    bearing: -22,
    maxZoom: 18,
    minZoom: 9,
  });

  // Layer Visibility Toggles
  const [showBuildings, setShowBuildings] = useState(true);
  const [showCongestionPillars, setShowCongestionPillars] = useState(true);
  const [showTransitArcs, setShowTransitArcs] = useState(true);
  const [showFloodPlane, setShowFloodPlane] = useState(true);
  const [hoveredObject, setHoveredObject] = useState<any>(null);

  // Camera Presets
  const setCameraPreset = (pitch: number, bearing: number, zoom: number) => {
    setViewState((vs: any) => ({
      ...vs,
      pitch,
      bearing,
      zoom,
      transitionDuration: 1200,
      transitionInterpolator: new FlyToInterpolator({ speed: 1.4 })
    }));
  };

  // Fly to new city when currentCity changes
  useEffect(() => {
    if (currentCity?.lat && currentCity?.lng) {
      setViewState((vs: any) => ({
        ...vs,
        longitude: currentCity.lng,
        latitude: currentCity.lat,
        zoom: 14.2,
        pitch: 58,
        transitionDuration: 1500,
        transitionInterpolator: new FlyToInterpolator({ speed: 1.5 })
      }));
    }
  }, [currentCity?.lat, currentCity?.lng]);

  // ── 1. 3D Buildings Layer ──────────────────────────────────────────────────
  const buildingPolygons = useMemo(() => {
    // If backend provided buildings for a dynamically loaded city, use them
    if (buildings && buildings.length > 0) {
      return buildings.map((b: any) => {
        let polygon = b.coordinates;
        if (!polygon && b.bbox) {
          const [minLng, minLat, maxLng, maxLat] = b.bbox;
          polygon = [
            [minLng, minLat],
            [maxLng, minLat],
            [maxLng, maxLat],
            [minLng, maxLat],
            [minLng, minLat]
          ];
        }
        return {
          id: b.id || Math.random().toString(),
          name: b.name || `${b.type || 'Urban'} Building`,
          type: b.type || 'commercial',
          polygon: polygon || [],
          elevation: b.height || (b.floors ? b.floors * 3.5 : 30),
          floors: b.floors || Math.round((b.height || 30) / 3.5),
          power_load_mw: b.power_load_mw || 2.4,
          occupancy: b.occupancy || 600,
          fillColor: b.type === 'hospital'
            ? [239, 68, 68, 220]
            : b.type === 'park'
            ? [16, 185, 129, 180]
            : b.type === 'skyscraper'
            ? [147, 51, 234, 210]
            : [59, 130, 246, 190]
        };
      }).filter((b: any) => b.polygon.length >= 3);
    }

    // Default: High-Fidelity San Francisco Downtown 3D Dataset
    return SAN_FRANCISCO_3D_BUILDINGS.map((b: Building3D) => {
      let color: [number, number, number, number];
      switch (b.type) {
        case 'skyscraper':
          color = [168, 85, 247, 230]; // Vibrant Purple Neon
          break;
        case 'hospital':
          color = [239, 68, 68, 240];  // Warning Coral Red
          break;
        case 'park':
          color = [16, 185, 129, 190]; // Emerald Green
          break;
        case 'civic':
          color = [245, 158, 11, 220]; // Amber Gold
          break;
        case 'residential':
          color = [99, 102, 241, 180]; // Indigo Blue
          break;
        default:
          color = [6, 182, 212, 190];  // Cyan Blue
      }
      return {
        id: b.id,
        name: b.name,
        type: b.type,
        polygon: b.coordinates,
        elevation: b.height,
        floors: b.floors,
        power_load_mw: b.power_load_mw,
        occupancy: b.occupancy,
        address: b.address,
        fillColor: color
      };
    });
  }, [buildings]);

  // ── 2. 3D Real-Time Congestion Pillars (ColumnLayer) ───────────────────────
  const congestionPillars = useMemo(() => {
    const trafficData = telemetry.traffic || {};
    const pillars: any[] = [];

    if (graph?.nodes) {
      for (const n of graph.nodes) {
        const nodeTraffic = trafficData[n.id];
        const congestion = nodeTraffic?.congestion_percentage ?? 35.0;
        
        let color: [number, number, number, number];
        if (congestion > 75) {
          color = [239, 68, 68, 220]; // Danger Red
        } else if (congestion > 50) {
          color = [249, 115, 22, 210]; // Warning Orange
        } else {
          color = [16, 185, 129, 180]; // Free Flow Green
        }

        pillars.push({
          id: n.id,
          name: n.name || `Node ${n.id}`,
          position: [n.lng, n.lat],
          elevation: (congestion / 100.0) * 280, // Height up to 280 meters
          congestion,
          color
        });
      }
    }
    return pillars;
  }, [graph?.nodes, telemetry.traffic]);

  // ── 3. 3D Flow Arcs Layer (ArcLayer) ──────────────────────────────────────
  const transitArcs = useMemo(() => {
    const arcs: any[] = [];
    if (graph?.edges && graph?.nodes) {
      const nodeMap: Record<string, [number, number]> = {};
      for (const n of graph.nodes) {
        nodeMap[n.id] = [n.lng, n.lat];
      }
      // Sample edge pairs to render high-speed transit flow trajectories
      for (let i = 0; i < graph.edges.length; i += 2) {
        const e = graph.edges[i];
        const from = nodeMap[e.from_node ?? e.from];
        const to = nodeMap[e.to_node ?? e.to];
        if (from && to) {
          const isCongested = (e.base_congestion ?? 0.2) > 0.6;
          arcs.push({
            id: `arc-${i}`,
            source: from,
            target: to,
            sourceColor: isCongested ? [239, 68, 68, 180] : [6, 182, 212, 180],
            targetColor: isCongested ? [249, 115, 22, 180] : [168, 85, 247, 180],
            name: e.road_name || 'Express Corridor'
          });
        }
      }
    }
    return arcs;
  }, [graph?.edges, graph?.nodes]);

  // ── 4. 3D Flood Inundation Layer ──────────────────────────────────────────
  const floodWaterPlane = useMemo(() => {
    const rainIntensity = telemetry.weather?.rain_intensity ?? 0.0;
    const floodTelemetry = telemetry.flood || {};
    const maxWater = Math.max(
      ...Object.values(floodTelemetry).map((f: any) => f.water_level_cm ?? 0),
      0
    );

    if (rainIntensity > 0.2 || maxWater > 10.0) {
      // Bay area low-lying coastal flood polygon for San Francisco
      return [
        {
          polygon: [
            [-122.3960, 37.7965],
            [-122.3850, 37.7965],
            [-122.3850, 37.7800],
            [-122.3920, 37.7800],
            [-122.3960, 37.7965]
          ],
          elevation: Math.min(25, 4 + maxWater * 0.8),
          color: [14, 165, 233, 140] // Translucent deep cyan flood water
        }
      ];
    }
    return [];
  }, [telemetry.weather, telemetry.flood]);

  // ── 5. Deck.gl Layers Assemble ────────────────────────────────────────────
  const layers = [
    // 3D Buildings Layer
    showBuildings && buildingPolygons.length > 0 && new PolygonLayer({
      id: 'buildings-3d',
      data: buildingPolygons,
      extruded: true,
      wireframe: true,
      getPolygon: (d: any) => d.polygon,
      getElevation: (d: any) => d.elevation,
      getFillColor: (d: any) => d.fillColor,
      getLineColor: [30, 41, 59, 120],
      lineWidthMinPixels: 1,
      pickable: true,
      onHover: (info: any) => setHoveredObject(info.object || null),
      onClick: (info: any) => {
        if (info.coordinate && onSelectCoordinates) {
          onSelectCoordinates(info.coordinate[1], info.coordinate[0]);
        }
      },
      material: {
        ambient: 0.4,
        diffuse: 0.6,
        shininess: 32,
        specularColor: [200, 200, 255]
      },
      updateTriggers: {
        getFillColor: [buildingPolygons]
      }
    }),

    // 3D Congestion Pillars
    showCongestionPillars && congestionPillars.length > 0 && new ColumnLayer({
      id: 'congestion-pillars',
      data: congestionPillars,
      diskResolution: 12,
      radius: 35,
      extruded: true,
      pickable: true,
      getPosition: (d: any) => d.position,
      getElevation: (d: any) => d.elevation,
      getFillColor: (d: any) => d.color,
      getLineColor: [255, 255, 255, 100],
      lineWidthMinPixels: 1,
      onHover: (info: any) => setHoveredObject(info.object || null),
      onClick: (info: any) => {
        if (info.object?.position && onSelectCoordinates) {
          onSelectCoordinates(info.object.position[1], info.object.position[0]);
        }
      },
      material: {
        ambient: 0.6,
        diffuse: 0.8
      }
    }),

    // 3D Transit & Flow Arcs
    showTransitArcs && transitArcs.length > 0 && new ArcLayer({
      id: 'transit-flow-arcs',
      data: transitArcs,
      getSourcePosition: (d: any) => d.source,
      getTargetPosition: (d: any) => d.target,
      getSourceColor: (d: any) => d.sourceColor,
      getTargetColor: (d: any) => d.targetColor,
      getWidth: 3,
      getHeight: 0.4,
      pickable: false
    }),

    // 3D Flood Inundation Plane
    showFloodPlane && floodWaterPlane.length > 0 && new PolygonLayer({
      id: 'flood-water-plane',
      data: floodWaterPlane,
      extruded: true,
      getPolygon: (d: any) => d.polygon,
      getElevation: (d: any) => d.elevation,
      getFillColor: (d: any) => d.color,
      getLineColor: [56, 189, 248, 160],
      lineWidthMinPixels: 1,
      pickable: false
    })
  ].filter(Boolean);

  return (
    <div className="w-full h-full relative map-container-isolate select-none">
      <DeckGL
        viewState={viewState}
        onViewStateChange={({ viewState: vs }: any) => setViewState(vs)}
        controller={{ doubleClickZoom: false, touchRotate: true }}
        layers={layers}
        getCursor={({ isHovering }: any) => (isHovering ? 'pointer' : 'default')}
      >
        <Map
          mapStyle="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
          reuseMaps
        />
      </DeckGL>

      {/* Top Left: 3D Camera Controls & View Angle Presets */}
      <div className="absolute top-3 left-3 z-[1000] flex flex-wrap gap-1.5 bg-slate-900/85 backdrop-blur-md border border-brand-border/60 p-1.5 rounded-xl shadow-xl font-mono text-[10px]">
        <span className="text-slate-400 font-bold uppercase flex items-center gap-1 px-2 py-1">
          <Compass className="h-3 w-3 text-brand-neonCyan" /> View:
        </span>
        <button
          onClick={() => setCameraPreset(60, -25, 14.2)}
          className={`px-2 py-1 rounded transition ${viewState.pitch > 50 ? 'bg-brand-neonPurple/20 text-brand-neonPurple font-bold border border-brand-neonPurple/40' : 'text-slate-400 hover:text-white'}`}
          title="3D High-Rise Perspective"
        >
          Perspective (60°)
        </button>
        <button
          onClick={() => setCameraPreset(45, 0, 13.8)}
          className={`px-2 py-1 rounded transition ${viewState.pitch === 45 ? 'bg-brand-neonPurple/20 text-brand-neonPurple font-bold border border-brand-neonPurple/40' : 'text-slate-400 hover:text-white'}`}
          title="Isometric Urban View"
        >
          Isometric (45°)
        </button>
        <button
          onClick={() => setCameraPreset(72, -40, 15.4)}
          className="px-2 py-1 rounded text-slate-400 hover:text-white transition"
          title="Street Canyon View"
        >
          Canyon (72°)
        </button>
        <button
          onClick={() => setCameraPreset(0, 0, 13.5)}
          className={`px-2 py-1 rounded transition ${viewState.pitch === 0 ? 'bg-brand-neonPurple/20 text-brand-neonPurple font-bold border border-brand-neonPurple/40' : 'text-slate-400 hover:text-white'}`}
          title="Top-Down 2D Map"
        >
          Top-Down (0°)
        </button>
      </div>

      {/* Top Right: Layer Visibility Toggles */}
      <div className="absolute top-3 right-3 z-[1000] flex gap-1.5 bg-slate-900/85 backdrop-blur-md border border-brand-border/60 p-1.5 rounded-xl shadow-xl text-[10px] font-mono">
        <button
          onClick={() => setShowBuildings(!showBuildings)}
          className={`px-2 py-1 rounded flex items-center gap-1 border transition ${showBuildings ? 'bg-brand-accent/20 border-brand-accent text-white font-bold' : 'border-brand-border/40 text-slate-500'}`}
          title="Toggle 3D Buildings"
        >
          <Building2 className="h-3 w-3 text-brand-neonCyan" /> Buildings
        </button>
        <button
          onClick={() => setShowCongestionPillars(!showCongestionPillars)}
          className={`px-2 py-1 rounded flex items-center gap-1 border transition ${showCongestionPillars ? 'bg-brand-neonOrange/20 border-brand-neonOrange text-white font-bold' : 'border-brand-border/40 text-slate-500'}`}
          title="Toggle Congestion Pillars"
        >
          <Flame className="h-3 w-3 text-brand-neonOrange" /> Telemetry
        </button>
        <button
          onClick={() => setShowTransitArcs(!showTransitArcs)}
          className={`px-2 py-1 rounded flex items-center gap-1 border transition ${showTransitArcs ? 'bg-brand-neonPurple/20 border-brand-neonPurple text-white font-bold' : 'border-brand-border/40 text-slate-500'}`}
          title="Toggle Flow Arcs"
        >
          <Navigation className="h-3 w-3 text-brand-neonPurple" /> Arcs
        </button>
        {floodWaterPlane.length > 0 && (
          <button
            onClick={() => setShowFloodPlane(!showFloodPlane)}
            className={`px-2 py-1 rounded flex items-center gap-1 border transition ${showFloodPlane ? 'bg-sky-500/20 border-sky-400 text-white font-bold' : 'border-brand-border/40 text-slate-500'}`}
            title="Toggle Flood Plane"
          >
            <Waves className="h-3 w-3 text-sky-400" /> Flood
          </button>
        )}
      </div>

      {/* Interactive Hover Tooltip */}
      {hoveredObject && (
        <div className="absolute top-16 left-3 z-[1001] bg-slate-900/95 backdrop-blur-md border border-brand-neonCyan/40 p-3 rounded-xl shadow-2xl font-mono text-xs max-w-xs animate-fadeIn pointer-events-none">
          <div className="flex items-center justify-between border-b border-brand-border/60 pb-1.5 mb-1.5">
            <span className="font-bold text-brand-neonCyan tracking-wide truncate">{hoveredObject.name}</span>
            {hoveredObject.type && (
              <span className="text-[9px] uppercase px-1.5 py-0.5 bg-white/10 rounded text-slate-300 font-bold ml-2">
                {hoveredObject.type}
              </span>
            )}
          </div>
          
          {hoveredObject.elevation !== undefined && (
            <div className="grid grid-cols-2 gap-2 text-[10px] text-slate-300">
              {hoveredObject.elevation && (
                <div>
                  <span className="text-slate-500 block">Height:</span>
                  <span className="font-bold text-white">{Math.round(hoveredObject.elevation)} m</span>
                </div>
              )}
              {hoveredObject.floors && (
                <div>
                  <span className="text-slate-500 block">Floors:</span>
                  <span className="font-bold text-white">{hoveredObject.floors} Levels</span>
                </div>
              )}
              {hoveredObject.power_load_mw && (
                <div>
                  <span className="text-slate-500 block">Power Demand:</span>
                  <span className="font-bold text-amber-400">{hoveredObject.power_load_mw} MW</span>
                </div>
              )}
              {hoveredObject.congestion !== undefined && (
                <div>
                  <span className="text-slate-500 block">Congestion:</span>
                  <span className={`font-bold ${hoveredObject.congestion > 75 ? 'text-red-400' : 'text-emerald-400'}`}>
                    {Math.round(hoveredObject.congestion)}%
                  </span>
                </div>
              )}
              {hoveredObject.occupancy && (
                <div>
                  <span className="text-slate-500 block">Occupancy:</span>
                  <span className="font-bold text-slate-200">{hoveredObject.occupancy.toLocaleString()}</span>
                </div>
              )}
            </div>
          )}

          {hoveredObject.address && (
            <p className="text-[9px] text-slate-400 mt-2 border-t border-brand-border/40 pt-1">
              📍 {hoveredObject.address}
            </p>
          )}
        </div>
      )}

      {/* Bottom Right: High-Fidelity 3D Twin Legend */}
      <div className="absolute bottom-3 right-3 z-[1000] bg-slate-900/90 backdrop-blur-md border border-brand-border/80 p-3 rounded-xl text-[10px] font-mono space-y-1.5 shadow-2xl">
        <div className="flex items-center justify-between border-b border-brand-border/40 pb-1 mb-1">
          <span className="text-slate-200 font-bold uppercase tracking-wider">SF Financial District 3D Twin</span>
          <span className="text-[9px] bg-brand-neonPurple/20 text-brand-neonPurple px-1.5 py-0.2 rounded font-bold">deck.gl</span>
        </div>
        <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-slate-400 text-[9px]">
          <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-sm bg-purple-500" /> Skyscraper</div>
          <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-sm bg-cyan-500" /> Commercial</div>
          <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-sm bg-red-500" /> Hospital/Trauma</div>
          <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-sm bg-emerald-500" /> Urban Park</div>
          <div className="flex items-center gap-1.5"><span className="w-2.5 h-1.5 rounded-sm bg-orange-500" /> Congestion Pillar</div>
          <div className="flex items-center gap-1.5"><span className="w-2.5 h-0.5 rounded-sm bg-cyan-400" /> 3D Flow Arc</div>
        </div>
      </div>
    </div>
  );
}
