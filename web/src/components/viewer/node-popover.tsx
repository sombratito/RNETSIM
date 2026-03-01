import { simulationStore } from "../../state/simulation-store";
import { scenarioStore } from "../../state/scenario-store";

const STATUS_COLORS: Record<string, string> = {
  healthy: "#22c55e",
  degraded: "#eab308",
  offline: "#ef4444",
  sleeping: "#6b7280",
  preview: "#4b5563",
};

const MEDIUM_COLORS: Record<string, string> = {
  lora_sf7_125: "#22c55e",
  lora_sf8_125: "#22c55e",
  lora_sf12_125: "#86efac",
  wifi_local: "#3b82f6",
  halow_4mhz: "#a855f7",
  ethernet: "#6b7280",
  internet: "#6b7280",
  packet_radio: "#f97316",
  satellite: "#06b6d4",
  sneakernet: "#d97706",
};

const MEDIUM_LABELS: Record<string, string> = {
  lora_sf7_125: "LoRa SF7/125",
  lora_sf8_125: "LoRa SF8/125",
  lora_sf12_125: "LoRa SF12/125",
  wifi_local: "WiFi",
  halow_4mhz: "HaLow 4 MHz",
  ethernet: "Ethernet",
  internet: "Internet",
  packet_radio: "Packet Radio",
  satellite: "Satellite",
  sneakernet: "Sneakernet",
};

export interface PopoverData {
  x: number;
  y: number;
  nodeId: string;
}

export function NodePopover({
  data,
  onClose,
}: {
  data: PopoverData;
  onClose: () => void;
}) {
  const info = scenarioStore.currentScenario?.nodes.find(
    (n) => n.name === data.nodeId,
  );
  const liveNode = simulationStore.nodes.find((n) => n.name === data.nodeId);

  return (
    <div
      className="absolute z-50 w-56 rounded-lg border border-gray-700 bg-gray-800 p-3 shadow-xl"
      style={{ left: data.x + 12, top: data.y - 8 }}
      onClick={(e) => e.stopPropagation()}
    >
      <div className="mb-2 flex items-center justify-between">
        <span className="text-sm font-semibold text-gray-100">
          {data.nodeId}
        </span>
        <button
          onClick={onClose}
          className="text-xs text-gray-500 hover:text-gray-300"
        >
          x
        </button>
      </div>
      <div className="space-y-1 text-xs text-gray-400">
        {info && (
          <>
            <div>
              <span className="text-gray-500">Role:</span>{" "}
              <span className="text-gray-300">{info.role}</span>
            </div>
            {info.alt != null && (
              <div>
                <span className="text-gray-500">Altitude:</span>{" "}
                <span className="text-gray-300">{info.alt}m</span>
              </div>
            )}
            {info.lat != null && info.lon != null && (
              <div>
                <span className="text-gray-500">Position:</span>{" "}
                <span className="text-gray-300">
                  {info.lat.toFixed(4)}, {info.lon.toFixed(4)}
                </span>
              </div>
            )}
            <div>
              <span className="text-gray-500">Interfaces:</span>
              <div className="mt-1 flex flex-wrap gap-1">
                {info.interfaces.map((m) => (
                  <span
                    key={m}
                    className="inline-block rounded px-1.5 py-0.5 text-[10px]"
                    style={{
                      backgroundColor: (MEDIUM_COLORS[m] ?? "#4b5563") + "20",
                      color: MEDIUM_COLORS[m] ?? "#9ca3af",
                    }}
                  >
                    {MEDIUM_LABELS[m] ?? m}
                  </span>
                ))}
              </div>
            </div>
            {info.sleep_schedule && (
              <div>
                <span className="text-gray-500">Sleep:</span>{" "}
                <span className="text-gray-300">{info.sleep_schedule}</span>
              </div>
            )}
            {info.lxmf_propagation && (
              <div>
                <span className="text-gray-500">LXMF propagation:</span>{" "}
                <span className="text-gray-300">enabled</span>
              </div>
            )}
          </>
        )}
        {liveNode && (
          <>
            <hr className="border-gray-700" />
            <div>
              <span className="text-gray-500">Status:</span>{" "}
              <span
                style={{
                  color: STATUS_COLORS[liveNode.status] ?? "#6b7280",
                }}
              >
                {liveNode.status}
              </span>
            </div>
            <div>
              <span className="text-gray-500">Paths:</span>{" "}
              <span className="text-gray-300">{liveNode.path_count}</span>
            </div>
            <div>
              <span className="text-gray-500">Announces:</span>{" "}
              <span className="text-gray-300">{liveNode.announce_count}</span>
            </div>
            <div>
              <span className="text-gray-500">Uptime:</span>{" "}
              <span className="text-gray-300">{liveNode.uptime}s</span>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
