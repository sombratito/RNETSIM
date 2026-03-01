import { useState } from "react";
import { observer } from "mobx-react-lite";
import { builderStore } from "../../state/builder-store";

const EVENT_COLORS: Record<string, string> = {
  kill_node: "bg-rnetsim-danger",
  revive_node: "bg-rnetsim-success",
  partition: "bg-orange-500",
  heal: "bg-rnetsim-accent",
};

const EVENT_LABELS: Record<string, string> = {
  kill_node: "Kill",
  revive_node: "Revive",
  partition: "Partition",
  heal: "Heal",
};

function EventTimeline() {
  const { events, nodes } = builderStore;
  const [isAdding, setIsAdding] = useState(false);
  const [newAction, setNewAction] = useState("kill_node");
  const [newTarget, setNewTarget] = useState("");
  const [newTime, setNewTime] = useState("5m");

  const handleAdd = () => {
    builderStore.addEvent({
      at: newTime,
      action: newAction,
      target: newTarget || null,
      params: null,
    });
    setIsAdding(false);
    setNewTarget("");
  };

  return (
    <div className="border-t border-rnetsim-panel bg-rnetsim-sidebar p-3">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-300">Event Timeline</h3>
        <button
          onClick={() => setIsAdding(!isAdding)}
          className="rounded bg-rnetsim-panel px-2 py-0.5 text-xs text-gray-400 hover:text-gray-200"
        >
          + Add Event
        </button>
      </div>

      {/* Event pills */}
      <div className="flex flex-wrap gap-2">
        {events.map((event) => (
          <div
            key={event.id}
            className={`flex items-center gap-1 rounded-full px-3 py-1 text-xs text-white ${
              EVENT_COLORS[event.action] ?? "bg-gray-600"
            }`}
          >
            <span>
              T+{event.at}: {EVENT_LABELS[event.action] ?? event.action}
              {event.target && ` ${event.target}`}
            </span>
            <button
              onClick={() => builderStore.removeEvent(event.id)}
              className="ml-1 opacity-60 hover:opacity-100"
            >
              x
            </button>
          </div>
        ))}

        {events.length === 0 && !isAdding && (
          <span className="text-xs text-rnetsim-muted">No events scheduled</span>
        )}
      </div>

      {/* Add event form */}
      {isAdding && (
        <div className="mt-3 flex items-end gap-2">
          <div>
            <label className="mb-1 block text-xs text-gray-500">Action</label>
            <select
              value={newAction}
              onChange={(e) => setNewAction(e.target.value)}
              className="rounded bg-rnetsim-panel px-2 py-1 text-xs text-gray-200"
            >
              <option value="kill_node">Kill Node</option>
              <option value="revive_node">Revive Node</option>
              <option value="partition">Partition</option>
              <option value="heal">Heal</option>
            </select>
          </div>

          <div>
            <label className="mb-1 block text-xs text-gray-500">Target</label>
            <select
              value={newTarget}
              onChange={(e) => setNewTarget(e.target.value)}
              className="rounded bg-rnetsim-panel px-2 py-1 text-xs text-gray-200"
            >
              <option value="">None</option>
              {nodes.map((n) => (
                <option key={n.id} value={n.name}>
                  {n.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-xs text-gray-500">Time</label>
            <input
              type="text"
              value={newTime}
              onChange={(e) => setNewTime(e.target.value)}
              placeholder="5m"
              className="w-16 rounded bg-rnetsim-panel px-2 py-1 text-xs text-gray-200"
            />
          </div>

          <button
            onClick={handleAdd}
            className="rounded bg-rnetsim-accent px-3 py-1 text-xs text-white"
          >
            Add
          </button>
        </div>
      )}
    </div>
  );
}

export default observer(EventTimeline);
