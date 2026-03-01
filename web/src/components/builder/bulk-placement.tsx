import { useState } from "react";
import { observer } from "mobx-react-lite";
import { builderStore } from "../../state/builder-store";
import { profileStore } from "../../state/profile-store";

type PlacementMethod = "random" | "grid" | "cluster";

function BulkPlacement() {
  const [profileId, setProfileId] = useState("");
  const [count, setCount] = useState(10);
  const [method, setMethod] = useState<PlacementMethod>("random");

  const { bbox } = builderStore;
  const { profiles } = profileStore;

  const handlePlace = () => {
    if (!bbox || !profileId) return;

    const [swLat, swLon, neLat, neLon] = bbox;

    if (method === "random") {
      for (let i = 0; i < count; i++) {
        const lat = swLat + Math.random() * (neLat - swLat);
        const lon = swLon + Math.random() * (neLon - swLon);
        builderStore.addNode(lat, lon, profileId);
      }
    } else if (method === "grid") {
      const cols = Math.ceil(Math.sqrt(count));
      const rows = Math.ceil(count / cols);
      let placed = 0;
      for (let r = 0; r < rows && placed < count; r++) {
        for (let c = 0; c < cols && placed < count; c++) {
          const lat = swLat + ((r + 0.5) / rows) * (neLat - swLat);
          const lon = swLon + ((c + 0.5) / cols) * (neLon - swLon);
          builderStore.addNode(lat, lon, profileId);
          placed++;
        }
      }
    } else if (method === "cluster") {
      const clusterCount = Math.ceil(count / 4);
      for (let ci = 0; ci < clusterCount; ci++) {
        const centerLat = swLat + Math.random() * (neLat - swLat);
        const centerLon = swLon + Math.random() * (neLon - swLon);
        const nodesInCluster = Math.min(
          4,
          count - builderStore.nodes.length,
        );
        for (let j = 0; j < nodesInCluster; j++) {
          const lat = centerLat + (Math.random() - 0.5) * 0.005;
          const lon = centerLon + (Math.random() - 0.5) * 0.005;
          builderStore.addNode(lat, lon, profileId);
        }
      }
    }
  };

  return (
    <div className="space-y-3 border-t border-rnetsim-panel pt-3">
      <h3 className="text-sm font-semibold text-gray-300">Bulk Placement</h3>

      {!bbox && (
        <p className="text-xs text-rnetsim-muted">
          Draw an area first (Draw Area mode)
        </p>
      )}

      {bbox && (
        <>
          <div>
            <label className="mb-1 block text-xs text-gray-500">Profile</label>
            <select
              value={profileId}
              onChange={(e) => setProfileId(e.target.value)}
              className="w-full rounded bg-rnetsim-panel px-2 py-1 text-sm text-gray-200"
            >
              <option value="">Select profile...</option>
              {profiles.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-xs text-gray-500">
              Count ({count})
            </label>
            <input
              type="range"
              min={1}
              max={100}
              value={count}
              onChange={(e) => setCount(Number(e.target.value))}
              className="w-full"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs text-gray-500">Method</label>
            <select
              value={method}
              onChange={(e) => setMethod(e.target.value as PlacementMethod)}
              className="w-full rounded bg-rnetsim-panel px-2 py-1 text-sm text-gray-200"
            >
              <option value="random">Random Scatter</option>
              <option value="grid">Grid</option>
              <option value="cluster">Cluster</option>
            </select>
          </div>

          <button
            onClick={handlePlace}
            disabled={!profileId}
            className="w-full rounded bg-rnetsim-accent px-3 py-1.5 text-sm text-white disabled:opacity-50"
          >
            Place {count} Nodes
          </button>
        </>
      )}
    </div>
  );
}

export default observer(BulkPlacement);
