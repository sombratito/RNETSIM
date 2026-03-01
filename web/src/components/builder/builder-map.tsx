import { useRef, useEffect } from "react";
import { observer } from "mobx-react-lite";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { createMap } from "../../lib/map-setup";
import { builderStore, type BuilderMode } from "../../state/builder-store";

const MODE_LABELS: Record<BuilderMode, string> = {
  select: "Select",
  draw_rect: "Draw Area",
  place_node: "Place Node",
  delete: "Delete",
};

function BuilderMap() {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const { mode, nodes, bbox, selectedProfileId } = builderStore;

  // Initialize map
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = createMap(containerRef.current, {
      terrain3d: true,
      buildings3d: true,
    });
    mapRef.current = map;

    map.on("load", () => {
      // Node markers source
      map.addSource("builder-nodes", {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
      });

      map.addLayer({
        id: "builder-nodes-circles",
        type: "circle",
        source: "builder-nodes",
        paint: {
          "circle-radius": 8,
          "circle-color": ["get", "color"],
          "circle-stroke-color": "#ffffff",
          "circle-stroke-width": [
            "case",
            ["boolean", ["get", "selected"], false],
            2,
            0,
          ],
        },
      });

      map.addLayer({
        id: "builder-nodes-labels",
        type: "symbol",
        source: "builder-nodes",
        layout: {
          "text-field": ["get", "name"],
          "text-size": 10,
          "text-offset": [0, 1.5],
          "text-anchor": "top",
        },
        paint: {
          "text-color": "#9ca3af",
          "text-halo-color": "#111820",
          "text-halo-width": 1,
        },
      });

      // Bounding box source
      map.addSource("builder-bbox", {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
      });

      map.addLayer({
        id: "builder-bbox-outline",
        type: "line",
        source: "builder-bbox",
        paint: {
          "line-color": "#eab308",
          "line-width": 2,
          "line-dasharray": [4, 4],
        },
      });
    });

    // Map click handler
    map.on("click", (e) => {
      const { lng, lat } = e.lngLat;

      if (builderStore.mode === "place_node" && selectedProfileId) {
        builderStore.addNode(lat, lng, selectedProfileId);
      } else if (builderStore.mode === "delete") {
        // Check if clicked on a node
        const features = map.queryRenderedFeatures(e.point, {
          layers: ["builder-nodes-circles"],
        });
        if (features.length > 0) {
          const nodeId = features[0]?.properties?.id;
          if (nodeId) builderStore.removeNode(nodeId);
        }
      } else if (builderStore.mode === "select") {
        const features = map.queryRenderedFeatures(e.point, {
          layers: ["builder-nodes-circles"],
        });
        if (features.length > 0) {
          builderStore.selectNode(features[0]?.properties?.id ?? null);
        } else {
          builderStore.selectNode(null);
        }
      }
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Update node markers
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;

    const source = map.getSource("builder-nodes") as maplibregl.GeoJSONSource;
    if (source) {
      source.setData({
        type: "FeatureCollection",
        features: nodes.map((n) => ({
          type: "Feature" as const,
          geometry: {
            type: "Point" as const,
            coordinates: [n.lon, n.lat],
          },
          properties: {
            id: n.id,
            name: n.name,
            color: "#3b82f6",
            selected: n.id === builderStore.selectedNodeId,
          },
        })),
      });
    }
  }, [nodes.length, builderStore.selectedNodeId]);

  // Update bbox
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;

    const source = map.getSource("builder-bbox") as maplibregl.GeoJSONSource;
    if (source && bbox) {
      const [swLat, swLon, neLat, neLon] = bbox;
      source.setData({
        type: "FeatureCollection",
        features: [
          {
            type: "Feature",
            geometry: {
              type: "Polygon",
              coordinates: [
                [
                  [swLon, swLat],
                  [neLon, swLat],
                  [neLon, neLat],
                  [swLon, neLat],
                  [swLon, swLat],
                ],
              ],
            },
            properties: {},
          },
        ],
      });
    }
  }, [bbox]);

  return (
    <div className="flex h-full flex-col">
      {/* Toolbar */}
      <div className="flex gap-2 border-b border-rnetsim-panel bg-rnetsim-bg px-4 py-2">
        {(Object.entries(MODE_LABELS) as [BuilderMode, string][]).map(
          ([m, label]) => (
            <button
              key={m}
              onClick={() => builderStore.setMode(m)}
              className={`rounded px-3 py-1 text-xs ${
                mode === m
                  ? "bg-rnetsim-accent text-white"
                  : "bg-rnetsim-panel text-gray-400 hover:text-gray-200"
              }`}
            >
              {label}
            </button>
          ),
        )}
        <span className="ml-4 text-xs text-rnetsim-muted">
          {nodes.length} nodes placed
        </span>
      </div>

      {/* Map */}
      <div ref={containerRef} className="flex-1" />
    </div>
  );
}

export default observer(BuilderMap);
