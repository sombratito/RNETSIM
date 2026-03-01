import { useEffect, useState } from "react";
import { observer } from "mobx-react-lite";
import NavBar from "./components/layout/nav-bar";
import Sidebar from "./components/layout/sidebar";
import TopologyGraph from "./components/viewer/topology-graph";
import GeoMap from "./components/viewer/geo-map";
import NodeDetail from "./components/viewer/node-detail";
import MetricsDashboard from "./components/viewer/metrics-dashboard";
import NodeList from "./components/viewer/node-list";
import BuilderMap from "./components/builder/builder-map";
import DeviceProfileList from "./components/builder/device-profile-list";
import BulkPlacement from "./components/builder/bulk-placement";
import EventTimeline from "./components/builder/event-timeline";
import ScenarioInfo from "./components/builder/scenario-info";
import GatewayConfig from "./components/builder/gateway-config";
import ProfileManager from "./components/profiles/profile-manager";
import { simulationStore } from "./state/simulation-store";
import { scenarioStore } from "./state/scenario-store";

type Tab = "viewer" | "builder" | "profiles";
type ViewMode = "topology" | "map";

function App() {
  const [activeTab, setActiveTab] = useState<Tab>("viewer");
  const [viewMode, setViewMode] = useState<ViewMode>("topology");

  useEffect(() => {
    simulationStore.connect();
    scenarioStore.loadList();
    return () => simulationStore.disconnect();
  }, []);

  return (
    <div className="flex h-screen flex-col">
      <NavBar activeTab={activeTab} onTabChange={(t) => { setActiveTab(t as Tab); simulationStore.selectNode(null); }} />

      <main className="flex flex-1 overflow-hidden">
        {activeTab === "viewer" && (
          <>
            <Sidebar title="Simulation">
              <div className="flex-shrink-0 border-b border-rnetsim-panel">
                <NodeDetail />
                <MetricsDashboard />
              </div>
              <div className="min-h-0 flex-1 overflow-y-auto p-3">
                <NodeList />
              </div>
            </Sidebar>

            <div className="flex flex-1 flex-col">
              {/* View mode toggle */}
              <div className="flex gap-2 border-b border-rnetsim-panel bg-rnetsim-bg px-4 py-2">
                <button
                  onClick={() => { setViewMode("topology"); simulationStore.selectNode(null); }}
                  className={`rounded px-3 py-1 text-xs ${
                    viewMode === "topology"
                      ? "bg-rnetsim-panel text-gray-200"
                      : "text-gray-500 hover:text-gray-300"
                  }`}
                >
                  Topology
                </button>
                <button
                  onClick={() => { setViewMode("map"); simulationStore.selectNode(null); }}
                  className={`rounded px-3 py-1 text-xs ${
                    viewMode === "map"
                      ? "bg-rnetsim-panel text-gray-200"
                      : "text-gray-500 hover:text-gray-300"
                  }`}
                >
                  Map
                </button>

                {/* Launch controls */}
                <div className="ml-auto flex items-center gap-2">
                  {!simulationStore.isRunning && (
                    <select
                      onChange={(e) => {
                        if (e.target.value) {
                          simulationStore.launch(e.target.value);
                        }
                      }}
                      className="rounded bg-rnetsim-panel px-2 py-1 text-xs text-gray-300"
                      defaultValue=""
                    >
                      <option value="" disabled>
                        Launch scenario...
                      </option>
                      {scenarioStore.scenarios.map((s) => (
                        <option key={s.name} value={s.name}>
                          {s.name} ({s.node_count} nodes)
                        </option>
                      ))}
                    </select>
                  )}
                  {simulationStore.isRunning && (
                    <button
                      onClick={() => simulationStore.stop()}
                      className="rounded bg-rnetsim-danger/20 px-3 py-1 text-xs text-rnetsim-danger hover:bg-rnetsim-danger/30"
                    >
                      Stop
                    </button>
                  )}
                </div>
              </div>

              {/* Main view */}
              <div className="flex-1">
                {viewMode === "topology" && <TopologyGraph />}
                {viewMode === "map" && <GeoMap />}
              </div>
            </div>
          </>
        )}

        {activeTab === "builder" && (
          <>
            <Sidebar title="Builder">
              <div className="flex-1 overflow-y-auto p-3">
                <ScenarioInfo />
                <DeviceProfileList />
                <BulkPlacement />
                <GatewayConfig />
              </div>
            </Sidebar>
            <div className="flex flex-1 flex-col">
              <BuilderMap />
              <EventTimeline />
            </div>
          </>
        )}

        {activeTab === "profiles" && <ProfileManager />}
      </main>
    </div>
  );
}

export default observer(App);
