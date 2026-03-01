import { observer } from "mobx-react-lite";
import { builderStore } from "../../state/builder-store";

function GatewayConfig() {
  const { nodes, gatewayNodeName, gatewayPort } = builderStore;

  return (
    <div className="space-y-3 border-t border-rnetsim-panel pt-3">
      <h3 className="text-sm font-semibold text-gray-300">Gateway</h3>

      <div>
        <label className="mb-1 block text-xs text-gray-500">Gateway Node</label>
        <select
          value={gatewayNodeName ?? ""}
          onChange={(e) =>
            (builderStore.gatewayNodeName = e.target.value || null)
          }
          className="w-full rounded bg-rnetsim-panel px-2 py-1 text-sm text-gray-200"
        >
          <option value="">None</option>
          {nodes.map((n) => (
            <option key={n.id} value={n.name}>
              {n.name}
            </option>
          ))}
        </select>
      </div>

      {gatewayNodeName && (
        <>
          <div>
            <label className="mb-1 block text-xs text-gray-500">Host Port</label>
            <input
              type="number"
              value={gatewayPort}
              onChange={(e) =>
                (builderStore.gatewayPort = Number(e.target.value))
              }
              className="w-full rounded bg-rnetsim-panel px-2 py-1 text-sm text-gray-200"
            />
          </div>

          <div className="rounded bg-rnetsim-bg p-2">
            <div className="mb-1 text-xs text-gray-500">
              Add to your Reticulum config:
            </div>
            <pre className="text-xs text-gray-300">
              {`[[RNETSIM Gateway]]\n  type = TCPClientInterface\n  target_host = localhost\n  target_port = ${gatewayPort}`}
            </pre>
          </div>
        </>
      )}
    </div>
  );
}

export default observer(GatewayConfig);
