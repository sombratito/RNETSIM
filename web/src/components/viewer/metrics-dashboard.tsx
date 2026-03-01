import { useState } from "react";
import { observer } from "mobx-react-lite";
import { simulationStore } from "../../state/simulation-store";
import { scenarioStore } from "../../state/scenario-store";

function MetricsDashboard() {
  const { nodes, links, isRunning, scenarioName } = simulationStore;

  const totalPaths = nodes.reduce((sum, n) => sum + n.path_count, 0);
  const totalAnnounces = nodes.reduce((sum, n) => sum + n.announce_count, 0);
  const healthyCount = nodes.filter((n) => n.status === "healthy").length;
  const healthPercent =
    nodes.length > 0 ? Math.round((healthyCount / nodes.length) * 100) : 0;

  if (!isRunning) {
    const preview = scenarioStore.currentScenario;
    if (preview) {
      return <ScenarioPreview name={preview.name} description={preview.description} nodeCount={preview.nodes.length} eventCount={preview.events?.length ?? 0} />;
    }
    return (
      <div className="p-4 text-sm text-rnetsim-muted">
        No simulation running
      </div>
    );
  }

  return (
    <div className="space-y-3 p-4">
      <h3 className="text-sm font-semibold text-gray-300">Metrics</h3>
      <div className="grid grid-cols-2 gap-3">
        <MetricCard label="Nodes" value={nodes.length} />
        <MetricCard label="Links" value={links.length} />
        <MetricCard label="Paths" value={totalPaths} />
        <MetricCard label="Announces" value={totalAnnounces} />
        <MetricCard
          label="Health"
          value={`${healthPercent}%`}
          color={
            healthPercent === 100
              ? "text-rnetsim-success"
              : healthPercent > 50
                ? "text-rnetsim-warning"
                : "text-rnetsim-danger"
          }
        />
        <MetricCard label="Scenario" value={scenarioName ?? "—"} />
      </div>
    </div>
  );
}

function ScenarioPreview({
  name,
  description,
  nodeCount,
  eventCount,
}: {
  name: string;
  description: string;
  nodeCount: number;
  eventCount: number;
}) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="space-y-2 p-4">
      <h2 className="text-xl font-bold text-gray-200">{name}</h2>
      <div className="text-xs text-gray-500">
        {nodeCount} nodes &middot; {eventCount} events
      </div>
      {description && (
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex w-full items-center gap-1.5 text-xs text-gray-500 hover:text-gray-400"
        >
          <svg
            className={`h-3 w-3 transition-transform ${isOpen ? "rotate-90" : ""}`}
            viewBox="0 0 16 16"
            fill="currentColor"
          >
            <path d="M6.22 4.22a.75.75 0 0 1 1.06 0l3.25 3.25a.75.75 0 0 1 0 1.06l-3.25 3.25a.75.75 0 0 1-1.06-1.06L8.94 8 6.22 5.28a.75.75 0 0 1 0-1.06" />
          </svg>
          Description
        </button>
      )}
      {isOpen && description && (
        <p className="text-xs font-medium leading-relaxed text-gray-400">
          {description}
        </p>
      )}
    </div>
  );
}

function MetricCard({
  label,
  value,
  color = "text-gray-100",
}: {
  label: string;
  value: string | number;
  color?: string;
}) {
  return (
    <div className="rounded bg-rnetsim-panel p-3">
      <div className="text-xs text-gray-500">{label}</div>
      <div className={`text-lg font-semibold ${color}`}>{value}</div>
    </div>
  );
}

export default observer(MetricsDashboard);
