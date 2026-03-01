import { observer } from "mobx-react-lite";
import { simulationStore } from "../../state/simulation-store";
import { scenarioStore } from "../../state/scenario-store";
import type { NodeStatus } from "../../schemas/simulation";
import type { ScenarioNode } from "../../schemas/scenario";

const STATUS_DOT: Record<string, string> = {
  healthy: "bg-rnetsim-success",
  degraded: "bg-rnetsim-warning",
  offline: "bg-rnetsim-danger",
  sleeping: "bg-rnetsim-muted",
};

const ROLE_STYLES: Record<string, string> = {
  transport: "bg-rnetsim-accent/20 text-rnetsim-accent",
  endpoint: "bg-rnetsim-panel text-gray-400",
};

function formatUptime(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  if (seconds < 3600)
    return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
  return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
}

function LiveNodeItem({
  node,
  isSelected,
  onSelect,
}: {
  node: NodeStatus;
  isSelected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      onClick={onSelect}
      className={`w-full rounded-lg border p-3 text-left transition-colors ${
        isSelected
          ? "border-rnetsim-accent/50 bg-rnetsim-accent/10"
          : "border-transparent bg-rnetsim-panel/60 hover:bg-rnetsim-panel"
      }`}
    >
      {/* Top row: status dot + name + role badge */}
      <div className="flex items-center gap-2">
        <span
          className={`h-2.5 w-2.5 flex-shrink-0 rounded-full ${STATUS_DOT[node.status] ?? "bg-gray-600"}`}
          title={node.status}
        />
        <span className="truncate text-sm font-medium text-gray-200">
          {node.name}
        </span>
        <span
          className={`ml-auto flex-shrink-0 rounded px-1.5 py-0.5 text-[10px] font-medium uppercase leading-none ${ROLE_STYLES[node.role] ?? ROLE_STYLES.endpoint}`}
        >
          {node.role}
        </span>
      </div>

      {/* Metrics row */}
      <div className="mt-2 flex items-center gap-3 text-[11px] text-gray-500">
        <span title="Links">
          <svg
            className="mr-0.5 inline h-3 w-3"
            viewBox="0 0 16 16"
            fill="currentColor"
          >
            <path d="M4.715 6.542 3.343 7.914a3 3 0 1 0 4.243 4.243l1.828-1.829A3 3 0 0 0 8.586 5.5L8 6.086a1 1 0 0 0-.154.199 2 2 0 0 1 .861 3.337L6.88 11.45a2 2 0 1 1-2.83-2.83l.793-.792a4 4 0 0 1-.128-1.287z" />
            <path d="M6.586 4.672A3 3 0 0 0 7.414 9.5l.775-.776a2 2 0 0 1-.896-3.346L9.12 3.55a2 2 0 1 1 2.83 2.83l-.793.792c.112.42.155.855.128 1.287l1.372-1.372a3 3 0 1 0-4.243-4.243z" />
          </svg>
          {node.link_count}
        </span>
        <span title="Paths">
          <svg
            className="mr-0.5 inline h-3 w-3"
            viewBox="0 0 16 16"
            fill="currentColor"
          >
            <path d="M6 .5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5v3a.5.5 0 0 1-.5.5h-1v1.02a4.5 4.5 0 0 1 2.871 1.358l.723-.723A.5.5 0 0 1 12.5 5h3a.5.5 0 0 1 .5.5v3a.5.5 0 0 1-.5.5h-3a.5.5 0 0 1-.5-.5V7.89l-.723.723A4.5 4.5 0 0 1 9 10.98V12h1a.5.5 0 0 1 .5.5v3a.5.5 0 0 1-.5.5H6.5a.5.5 0 0 1-.5-.5v-3a.5.5 0 0 1 .5-.5H8v-1.02a4.5 4.5 0 0 1-2.371-1.358L4.89 9.5a.5.5 0 0 1 .057.29v.71H3.5a.5.5 0 0 1-.5-.5v-3a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5v.71l.723-.723A4.5 4.5 0 0 1 7 5.02V4h-1a.5.5 0 0 1-.5-.5z" />
          </svg>
          {node.path_count}
        </span>
        <span title="Announces">
          <svg
            className="mr-0.5 inline h-3 w-3"
            viewBox="0 0 16 16"
            fill="currentColor"
          >
            <path d="M8 16a2 2 0 0 0 2-2H6a2 2 0 0 0 2 2m.995-14.901a1 1 0 1 0-1.99 0A5 5 0 0 0 3 6c0 1.098-.5 6-2 7h14c-1.5-1-2-5.902-2-7 0-2.42-1.72-4.44-4.005-4.901" />
          </svg>
          {node.announce_count}
        </span>
        <span className="ml-auto" title="Uptime">
          {formatUptime(node.uptime)}
        </span>
      </div>
    </button>
  );
}

function PreviewNodeItem({
  node,
  isSelected,
  onSelect,
}: {
  node: ScenarioNode;
  isSelected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      onClick={onSelect}
      className={`w-full rounded-lg border p-3 text-left transition-colors ${
        isSelected
          ? "border-rnetsim-accent/50 bg-rnetsim-accent/10"
          : "border-transparent bg-rnetsim-panel/60 hover:bg-rnetsim-panel"
      }`}
    >
      {/* Top row: name + role badge */}
      <div className="flex items-center gap-2">
        <span className="h-2.5 w-2.5 flex-shrink-0 rounded-full bg-gray-600" />
        <span className="truncate text-sm font-medium text-gray-200">
          {node.name}
        </span>
        <span
          className={`ml-auto flex-shrink-0 rounded px-1.5 py-0.5 text-[10px] font-medium uppercase leading-none ${ROLE_STYLES[node.role] ?? ROLE_STYLES.endpoint}`}
        >
          {node.role}
        </span>
      </div>

      {/* Info row */}
      <div className="mt-2 flex items-center gap-3 text-[11px] text-gray-500">
        {node.profile && (
          <span className="truncate" title="Profile">
            {node.profile}
          </span>
        )}
        {node.interfaces.length > 0 && (
          <span className="ml-auto truncate" title="Interface">
            {node.interfaces[0]}
          </span>
        )}
      </div>
    </button>
  );
}

function NodeList() {
  const { nodes, isRunning, selectedNodeId } = simulationStore;

  if (isRunning && nodes.length > 0) {
    return (
      <div className="space-y-1.5">
        <div className="flex items-center justify-between px-1">
          <span className="text-xs font-medium uppercase tracking-wide text-gray-500">
            Nodes
          </span>
          <span className="text-xs tabular-nums text-gray-500">
            {nodes.length}
          </span>
        </div>
        <div className="space-y-1.5">
          {nodes.map((node) => (
            <LiveNodeItem
              key={node.name}
              node={node}
              isSelected={node.name === selectedNodeId}
              onSelect={() =>
                simulationStore.selectNode(
                  node.name === selectedNodeId ? null : node.name,
                )
              }
            />
          ))}
        </div>
      </div>
    );
  }

  const preview = scenarioStore.currentScenario;
  if (!isRunning && preview) {
    return (
      <div className="space-y-1.5">
        <div className="flex items-center justify-between px-1">
          <span className="text-xs font-medium uppercase tracking-wide text-gray-500">
            Nodes
          </span>
          <span className="text-xs tabular-nums text-gray-500">
            {preview.nodes.length}
          </span>
        </div>
        <div className="space-y-1.5">
          {preview.nodes.map((node) => (
            <PreviewNodeItem
              key={node.name}
              node={node}
              isSelected={node.name === selectedNodeId}
              onSelect={() =>
                simulationStore.selectNode(
                  node.name === selectedNodeId ? null : node.name,
                )
              }
            />
          ))}
        </div>
      </div>
    );
  }

  return null;
}

export default observer(NodeList);
