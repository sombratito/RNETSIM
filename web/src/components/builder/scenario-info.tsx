import { observer } from "mobx-react-lite";
import { builderStore } from "../../state/builder-store";
import { createScenario } from "../../api/scenarios";
import { launchSimulation } from "../../api/simulation";
import { profileStore } from "../../state/profile-store";
import type { Scenario } from "../../schemas/scenario";

function ScenarioInfo() {
  const { scenarioName, scenarioDescription, nodes, events } = builderStore;

  const handleSave = async () => {
    if (!scenarioName) return;

    const scenario = buildScenario();
    await createScenario(scenario);
  };

  const handleLaunch = async () => {
    if (!scenarioName) return;

    const scenario = buildScenario();
    await createScenario(scenario);
    await launchSimulation(scenarioName);
  };

  const buildScenario = (): Scenario => {
    return {
      name: scenarioName,
      description: scenarioDescription,
      defaults: { medium: "lora_sf8_125", tx_power: 20, role: "endpoint" },
      terrain: false,
      map: {
        source: "protomaps",
        style: "dark",
        center: [-78.6382, 35.7796],
        zoom: 12,
        terrain: false,
      },
      nodes: nodes.map((n) => {
        const profile = profileStore.getById(n.profileId);
        return {
          name: n.name,
          role: profile?.role ?? "endpoint",
          profile: n.profileId,
          lat: n.lat,
          lon: n.lon,
          alt: n.alt,
          interfaces: [profile?.medium ?? "lora_sf8_125"],
          sleep_schedule: profile?.sleep_schedule ?? undefined,
          lxmf_propagation: false,
        };
      }),
      gateways: builderStore.gatewayNodeName
        ? [{ node: builderStore.gatewayNodeName, host_port: builderStore.gatewayPort }]
        : [],
      events: events.map((e) => ({
        at: e.at,
        action: e.action,
        target: e.target,
        params: e.params,
      })),
    };
  };

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-gray-300">Scenario</h3>

      <div>
        <label className="mb-1 block text-xs text-gray-500">Name</label>
        <input
          type="text"
          value={scenarioName}
          onChange={(e) => (builderStore.scenarioName = e.target.value)}
          placeholder="my-scenario"
          className="w-full rounded bg-rnetsim-panel px-2 py-1 text-sm text-gray-200 placeholder-gray-600"
        />
      </div>

      <div>
        <label className="mb-1 block text-xs text-gray-500">Description</label>
        <textarea
          value={scenarioDescription}
          onChange={(e) => (builderStore.scenarioDescription = e.target.value)}
          rows={2}
          className="w-full rounded bg-rnetsim-panel px-2 py-1 text-sm text-gray-200 placeholder-gray-600"
          placeholder="Describe this scenario..."
        />
      </div>

      {/* Stats */}
      <div className="flex gap-4 text-xs text-gray-500">
        <span>{nodes.length} nodes</span>
        <span>{events.length} events</span>
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <button
          onClick={handleSave}
          disabled={!scenarioName}
          className="rounded bg-rnetsim-panel px-3 py-1.5 text-sm text-gray-300 hover:bg-rnetsim-panel/80 disabled:opacity-50"
        >
          Save
        </button>
        <button
          onClick={handleLaunch}
          disabled={!scenarioName || nodes.length === 0}
          className="rounded bg-rnetsim-accent px-3 py-1.5 text-sm text-white disabled:opacity-50"
        >
          Launch
        </button>
      </div>
    </div>
  );
}

export default observer(ScenarioInfo);
