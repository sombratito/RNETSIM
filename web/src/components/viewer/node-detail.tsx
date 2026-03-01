import { observer } from "mobx-react-lite";
import { simulationStore } from "../../state/simulation-store";

const STATUS_COLORS: Record<string, string> = {
  healthy: "text-rnetsim-success",
  degraded: "text-rnetsim-warning",
  offline: "text-rnetsim-danger",
  sleeping: "text-rnetsim-muted",
};

function NodeDetail() {
  const node = simulationStore.selectedNode;

  if (!node) {
    return null;
  }

  return (
    <div className="space-y-3 p-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">{node.name}</h3>
        <button
          onClick={() => simulationStore.selectNode(null)}
          className="text-gray-500 hover:text-gray-300"
        >
          x
        </button>
      </div>

      <div className="space-y-2 text-sm">
        <Row label="Status">
          <span className={STATUS_COLORS[node.status] ?? "text-gray-400"}>
            {node.status}
          </span>
        </Row>
        <Row label="Role">{node.role}</Row>
        <Row label="Identity">{node.identity_hash || "—"}</Row>
        <Row label="Paths">{node.path_count}</Row>
        <Row label="Announces">{node.announce_count}</Row>
        <Row label="Links">{node.link_count}</Row>
        <Row label="Uptime">{formatUptime(node.uptime)}</Row>
        {node.lat != null && node.lon != null && (
          <Row label="Position">
            {node.lat.toFixed(4)}, {node.lon.toFixed(4)}
          </Row>
        )}
      </div>

      <div className="flex gap-2 pt-2">
        <button
          onClick={() => simulationStore.inject("kill_node", node.name)}
          className="rounded bg-rnetsim-danger/20 px-3 py-1 text-xs text-rnetsim-danger hover:bg-rnetsim-danger/30"
        >
          Kill
        </button>
        <button
          onClick={() => simulationStore.inject("revive_node", node.name)}
          className="rounded bg-rnetsim-success/20 px-3 py-1 text-xs text-rnetsim-success hover:bg-rnetsim-success/30"
        >
          Revive
        </button>
      </div>
    </div>
  );
}

function Row({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex justify-between">
      <span className="text-gray-500">{label}</span>
      <span className="text-gray-200">{children}</span>
    </div>
  );
}

function formatUptime(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
  return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
}

export default observer(NodeDetail);
