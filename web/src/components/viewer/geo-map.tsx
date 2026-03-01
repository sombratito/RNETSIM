import { useRef, useEffect, useState } from "react";
import { observer } from "mobx-react-lite";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { createMap } from "../../lib/map-setup";
import { addNodeLayer, addLinkLayer, addRFLinkLayer, addRangeLayer } from "../../lib/map-layers";
import { simulationStore } from "../../state/simulation-store";
import { scenarioStore } from "../../state/scenario-store";
import { NodePopover, type PopoverData } from "./node-popover";
import { RFLegend } from "./rf-legend";
import { ElevationProfile } from "./elevation-profile";
import { analyzeScenarioRF, type RFAnalysis } from "../../lib/rf-propagation";
import { buildRFLinksGeoJSON, buildRangeGeoJSON } from "../../lib/rf-geojson";
import { batchCheckLOS } from "../../lib/terrain-los";
import { fetchLOSProfile, type ElevationSample } from "../../api/terrain";
import { batchFetchRadialRanges } from "../../lib/terrain-los";
import type { NodeStatus, LinkStatus } from "../../schemas/simulation";
import type { ScenarioNode } from "../../schemas/scenario";

const EMPTY_FC: GeoJSON.FeatureCollection = {
  type: "FeatureCollection",
  features: [],
};

function buildNodeGeoJSON(
  nodes: NodeStatus[],
  selectedNodeId: string | null,
): GeoJSON.FeatureCollection {
  return {
    type: "FeatureCollection",
    features: nodes
      .filter((n) => n.lat != null && n.lon != null)
      .map((n) => ({
        type: "Feature" as const,
        geometry: {
          type: "Point" as const,
          coordinates: [n.lon!, n.lat!],
        },
        properties: {
          name: n.name,
          role: n.role,
          status: n.status,
          selected: n.name === selectedNodeId,
        },
      })),
  };
}

/** Build GeoJSON from scenario nodes for idle-state preview. */
function buildPreviewNodeGeoJSON(
  nodes: ScenarioNode[],
): GeoJSON.FeatureCollection {
  return {
    type: "FeatureCollection",
    features: nodes
      .filter((n) => n.lat != null && n.lon != null)
      .map((n) => ({
        type: "Feature" as const,
        geometry: {
          type: "Point" as const,
          coordinates: [n.lon!, n.lat!],
        },
        properties: {
          name: n.name,
          role: n.role ?? "endpoint",
          status: "preview",
          selected: false,
        },
      })),
  };
}

function buildLinkGeoJSON(
  links: LinkStatus[],
  nodes: NodeStatus[],
): GeoJSON.FeatureCollection {
  const nodeMap = new Map(nodes.map((n) => [n.name, n]));

  return {
    type: "FeatureCollection",
    features: links
      .map((link) => {
        const source = nodeMap.get(link.source);
        const target = nodeMap.get(link.target);
        if (
          !source?.lat ||
          !source?.lon ||
          !target?.lat ||
          !target?.lon
        )
          return null;

        return {
          type: "Feature" as const,
          geometry: {
            type: "LineString" as const,
            coordinates: [
              [source.lon!, source.lat!],
              [target.lon!, target.lat!],
            ],
          },
          properties: { medium: link.medium },
        };
      })
      .filter(Boolean) as GeoJSON.Feature[],
  };
}

/** Toggle button used for map overlays. */
function OverlayToggle({
  label,
  active,
  onClick,
  colorClass,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
  colorClass: { border: string; bg: string; text: string };
}) {
  return (
    <button
      onClick={onClick}
      className={`rounded-md px-3 py-1.5 text-xs font-medium shadow-md transition-colors ${
        active
          ? `border ${colorClass.border} ${colorClass.bg} ${colorClass.text}`
          : "border border-gray-600 bg-gray-800/80 text-gray-400 hover:text-gray-200"
      }`}
    >
      {label}
    </button>
  );
}

interface ProfileData {
  profile: ElevationSample[];
  source: string;
  target: string;
  clear: boolean;
}

function GeoMap() {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const hasFitPreview = useRef(false);
  const selectedRef = useRef<string | null>(null);
  const losAbortRef = useRef(0); // incremented to cancel stale LOS fetches
  const [popover, setPopover] = useState<PopoverData | null>(null);
  const [showRF, setShowRF] = useState(true);
  const [showTerrain, setShowTerrain] = useState(false);
  const [showBuildings, setShowBuildings] = useState(false);
  const [profileData, setProfileData] = useState<ProfileData | null>(null);
  const [mapReady, setMapReady] = useState(false);
  const { nodes, links, selectedNodeId, isRunning } = simulationStore;

  // Keep ref in sync so MapLibre closures see current value
  selectedRef.current = selectedNodeId;

  // Initialize map
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const scenario = scenarioStore.currentScenario;
    const hasTerrain = scenario?.terrain ?? scenario?.map?.terrain ?? false;

    const map = createMap(containerRef.current, {
      terrain3d: hasTerrain,
      buildings3d: hasTerrain,
      center: scenario?.map?.center as [number, number] | undefined,
      zoom: scenario?.map?.zoom,
    });
    mapRef.current = map;

    // Sync initial toggle states
    if (hasTerrain) {
      setShowTerrain(true);
      setShowBuildings(true);
    }

    map.on("load", () => {
      // Navigation control with pitch for 3D terrain viewing
      map.addControl(
        new maplibregl.NavigationControl({ visualizePitch: true }),
        "top-right",
      );

      // RF overlay sources (added first so they render behind nodes)
      map.addSource("rf-ranges", { type: "geojson", data: EMPTY_FC });
      map.addSource("rf-links", { type: "geojson", data: EMPTY_FC });

      // RF overlay layers (behind node/link layers)
      addRangeLayer(map, "rf-ranges");
      addRFLinkLayer(map, "rf-links");

      // Simulation data sources
      map.addSource("nodes", {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
      });
      map.addSource("links", {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
      });

      addLinkLayer(map, "links");
      addNodeLayer(map, "nodes");

      // Click handler for node selection + popover
      map.on("click", "nodes-circles", (e) => {
        const feature = e.features?.[0];
        if (!feature) return;

        const name = feature.properties?.name;
        if (!name) return;

        simulationStore.selectNode(
          name === selectedRef.current ? null : name,
        );

        setPopover((prev) =>
          prev?.nodeId === name
            ? null
            : { x: e.point.x, y: e.point.y, nodeId: name },
        );
      });

      // RF link click handler — fetch and show elevation profile
      for (const layerId of ["rf-links-clear", "rf-links-blocked"]) {
        map.on("click", layerId, async (e) => {
          const feature = e.features?.[0];
          if (!feature) return;

          const { source, target } = feature.properties as {
            source: string;
            target: string;
          };
          const coords = (feature.geometry as GeoJSON.LineString).coordinates;
          const [fromLon, fromLat] = coords[0] as [number, number];
          const [toLon, toLat] = coords[1] as [number, number];

          try {
            const result = await fetchLOSProfile(fromLat!, fromLon!, toLat!, toLon!);
            setProfileData({
              profile: result.profile ?? [],
              source,
              target,
              clear: result.clear,
            });
          } catch {
            // Terrain API not available
          }
        });

        map.on("mouseenter", layerId, () => {
          map.getCanvas().style.cursor = "pointer";
        });
        map.on("mouseleave", layerId, () => {
          map.getCanvas().style.cursor = "";
        });
      }

      // Close popover on empty-space click
      map.on("click", (e) => {
        const features = map.queryRenderedFeatures(e.point, {
          layers: ["nodes-circles"],
        });
        if (features.length === 0) {
          setPopover(null);
        }
      });

      // Dismiss popover on pan/zoom
      map.on("movestart", () => setPopover(null));

      map.on("mouseenter", "nodes-circles", () => {
        map.getCanvas().style.cursor = "pointer";
      });
      map.on("mouseleave", "nodes-circles", () => {
        map.getCanvas().style.cursor = "";
      });

      // Signal that map sources and layers are ready
      setMapReady(true);
    });

    return () => {
      map.remove();
      mapRef.current = null;
      setMapReady(false);
    };
  }, []);

  // ── Terrain toggle ──────────────────────────────────────────────────
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady) return;

    if (showTerrain) {
      // Ensure terrain source exists (it may have been created at init)
      if (!map.getSource("terrain-dem")) {
        map.addSource("terrain-dem", {
          type: "raster-dem",
          tiles: [
            "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png",
          ],
          tileSize: 256,
          encoding: "terrarium",
          maxzoom: 15,
        });
      }
      if (!map.getLayer("terrain-hillshade")) {
        // Insert hillshade below the first data layer
        const firstLayer = map.getLayer("rf-ranges-fill");
        map.addLayer(
          {
            id: "terrain-hillshade",
            type: "hillshade",
            source: "terrain-dem",
            paint: {
              "hillshade-exaggeration": 0.5,
              "hillshade-shadow-color": "#000000",
              "hillshade-highlight-color": "#ffffff",
              "hillshade-accent-color": "#333333",
              "hillshade-illumination-direction": 315,
            },
          },
          firstLayer ? "rf-ranges-fill" : undefined,
        );
      }
      map.setTerrain({ source: "terrain-dem", exaggeration: 1.3 });
      map.setLayoutProperty("terrain-hillshade", "visibility", "visible");
    } else {
      try {
        map.setTerrain(null as unknown as maplibregl.TerrainSpecification);
      } catch {
        // terrain was never set
      }
      if (map.getLayer("terrain-hillshade")) {
        map.setLayoutProperty("terrain-hillshade", "visibility", "none");
      }
    }
  }, [showTerrain, mapReady]);

  // ── Buildings toggle ────────────────────────────────────────────────
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady) return;

    if (showBuildings) {
      if (!map.getSource("openmaptiles")) {
        map.addSource("openmaptiles", {
          type: "vector",
          tiles: [
            "https://tiles.openfreemap.org/planet/{z}/{x}/{y}.pbf",
          ],
          maxzoom: 14,
        });
      }
      if (!map.getLayer("3d-buildings")) {
        map.addLayer(
          {
            id: "3d-buildings",
            type: "fill-extrusion",
            source: "openmaptiles",
            "source-layer": "building",
            minzoom: 13,
            paint: {
              "fill-extrusion-color": "#1a1a2e",
              "fill-extrusion-height": [
                "interpolate",
                ["linear"],
                ["zoom"],
                13,
                0,
                14,
                ["coalesce", ["get", "render_height"], 10],
              ] as unknown as number,
              "fill-extrusion-base": [
                "coalesce",
                ["get", "render_min_height"],
                0,
              ] as unknown as number,
              "fill-extrusion-opacity": 0.7,
            },
          },
          "rf-ranges-fill", // below RF layers
        );
      }
      map.setLayoutProperty("3d-buildings", "visibility", "visible");
    } else {
      if (map.getLayer("3d-buildings")) {
        map.setLayoutProperty("3d-buildings", "visibility", "none");
      }
    }
  }, [showBuildings, mapReady]);

  // Update node/link data on state changes — live or preview
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady) return;

    const nodesSource = map.getSource("nodes") as maplibregl.GeoJSONSource;
    const linksSource = map.getSource("links") as maplibregl.GeoJSONSource;
    if (!nodesSource || !linksSource) return;

    const isPreview = !isRunning && nodes.length === 0;
    const scenario = scenarioStore.currentScenario;

    if (isPreview && scenario) {
      const previewGeoJSON = buildPreviewNodeGeoJSON(scenario.nodes);
      nodesSource.setData(previewGeoJSON);
      linksSource.setData({ type: "FeatureCollection", features: [] });

      // Fly to scenario's map center once
      if (!hasFitPreview.current && scenario.map) {
        const center = scenario.map.center;
        if (center && center.length === 2) {
          map.flyTo({
            center: center as [number, number],
            zoom: scenario.map.zoom ?? 11,
            duration: 1500,
          });
        }
        hasFitPreview.current = true;
      }
    } else {
      nodesSource.setData(buildNodeGeoJSON(nodes, selectedNodeId));
      linksSource.setData(buildLinkGeoJSON(links, nodes));
      hasFitPreview.current = false;
    }
  }, [nodes, links, selectedNodeId, isRunning, scenarioStore.currentScenario, mapReady]);

  // ── Selection popover — show popover when node selected from list ────
  useEffect(() => {
    const map = mapRef.current;
    if (!selectedNodeId) {
      setPopover((prev) => (prev ? null : prev));
      return;
    }
    if (!map || !mapReady) return;

    setPopover((prev) => {
      if (prev?.nodeId === selectedNodeId) return prev;

      // Find the node's coordinates from live data or scenario preview
      let lat: number | null = null;
      let lon: number | null = null;

      const liveNode = nodes.find((n) => n.name === selectedNodeId);
      if (liveNode?.lat != null && liveNode?.lon != null) {
        lat = liveNode.lat;
        lon = liveNode.lon;
      } else {
        const scenario = scenarioStore.currentScenario;
        const previewNode = scenario?.nodes.find((n) => n.name === selectedNodeId);
        if (previewNode?.lat != null && previewNode?.lon != null) {
          lat = previewNode.lat;
          lon = previewNode.lon;
        }
      }

      if (lat == null || lon == null) return prev;

      const point = map.project([lon, lat]);
      return { x: point.x, y: point.y, nodeId: selectedNodeId };
    });
  }, [selectedNodeId, nodes, mapReady]);

  // ── RF Analysis overlay ─────────────────────────────────────────────
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady) return;

    const rfLinksSource = map.getSource("rf-links") as maplibregl.GeoJSONSource;
    const rfRangesSource = map.getSource("rf-ranges") as maplibregl.GeoJSONSource;
    if (!rfLinksSource || !rfRangesSource) return;

    const scenario = scenarioStore.currentScenario;

    if (!showRF || !scenario) {
      rfLinksSource.setData(EMPTY_FC);
      rfRangesSource.setData(EMPTY_FC);
      return;
    }

    // 1. Instant: compute FSPL link budgets client-side
    const analysis: RFAnalysis = analyzeScenarioRF(scenario);
    rfLinksSource.setData(buildRFLinksGeoJSON(analysis, scenario));
    rfRangesSource.setData(buildRangeGeoJSON(analysis, scenario));

    // 2. Async: batch LOS checks via terrain API
    const generation = ++losAbortRef.current;
    const nodeMap = new Map(
      scenario.nodes
        .filter((n) => n.lat != null && n.lon != null)
        .map((n) => [n.name, n]),
    );

    const pairs = analysis.links
      .map((link) => {
        const a = nodeMap.get(link.source);
        const b = nodeMap.get(link.target);
        if (!a || !b || a.lat == null || a.lon == null || b.lat == null || b.lon == null)
          return null;
        return { fromLat: a.lat, fromLon: a.lon, toLat: b.lat, toLon: b.lon };
      })
      .filter(Boolean) as Array<{
        fromLat: number; fromLon: number; toLat: number; toLon: number;
      }>;

    if (pairs.length > 0) {
      batchCheckLOS(pairs)
        .then((results) => {
          // Abort if a newer generation has started
          if (losAbortRef.current !== generation) return;

          // Update link budgets with LOS results
          let idx = 0;
          for (const link of analysis.links) {
            const a = nodeMap.get(link.source);
            const b = nodeMap.get(link.target);
            if (a && b && a.lat != null && a.lon != null && b.lat != null && b.lon != null) {
              const los = results[idx];
              if (los) {
                link.losStatus = los.clear ? "clear" : "blocked";
              }
              idx++;
            }
          }

          // Refresh the layer with updated LOS data
          rfLinksSource.setData(buildRFLinksGeoJSON(analysis, scenario));
        })
        .catch(() => {
          // Terrain API not available — leave links as "pending" (solid)
        });
    }

    // 3. Async: terrain-shaped ranges (when terrain is enabled)
    if (scenario.terrain) {
      const rangeNodes = analysis.ranges
        .filter((r) => {
          const node = nodeMap.get(r.name);
          return node && node.lat != null && node.lon != null;
        })
        .map((r) => {
          const node = nodeMap.get(r.name)!;
          return {
            name: r.name,
            lat: node.lat!,
            lon: node.lon!,
            alt: node.alt ?? 0,
            max_range_m: r.range_m,
          };
        });

      if (rangeNodes.length > 0) {
        batchFetchRadialRanges(rangeNodes)
          .then((radialRanges) => {
            if (losAbortRef.current !== generation) return;
            rfRangesSource.setData(
              buildRangeGeoJSON(analysis, scenario, radialRanges),
            );
          })
          .catch(() => {
            // Radial range API not available — keep perfect circles
          });
      }
    }
  }, [showRF, scenarioStore.currentScenario, mapReady]);

  return (
    <div className="relative h-full w-full">
      <div ref={containerRef} className="h-full w-full" />

      {/* Map overlay toggles */}
      <div className="absolute left-3 top-3 z-10 flex gap-2">
        <OverlayToggle
          label="RF Analysis"
          active={showRF}
          onClick={() => setShowRF((v) => !v)}
          colorClass={{
            border: "border-green-600",
            bg: "bg-green-900/60",
            text: "text-green-300",
          }}
        />
        <OverlayToggle
          label="Terrain"
          active={showTerrain}
          onClick={() => setShowTerrain((v) => !v)}
          colorClass={{
            border: "border-amber-600",
            bg: "bg-amber-900/60",
            text: "text-amber-300",
          }}
        />
        <OverlayToggle
          label="Buildings"
          active={showBuildings}
          onClick={() => setShowBuildings((v) => !v)}
          colorClass={{
            border: "border-blue-600",
            bg: "bg-blue-900/60",
            text: "text-blue-300",
          }}
        />
      </div>

      {showRF && <RFLegend />}

      {profileData && (
        <ElevationProfile
          profile={profileData.profile}
          sourceName={profileData.source}
          targetName={profileData.target}
          isLOSClear={profileData.clear}
          onClose={() => setProfileData(null)}
        />
      )}

      {popover && (
        <NodePopover data={popover} onClose={() => setPopover(null)} />
      )}
    </div>
  );
}

export default observer(GeoMap);
