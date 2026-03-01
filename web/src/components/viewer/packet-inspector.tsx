import { observer } from "mobx-react-lite";

function PacketInspector() {
  return (
    <div className="p-4">
      <h3 className="mb-2 text-sm font-semibold text-gray-300">
        Packet Inspector
      </h3>
      <div className="text-sm text-rnetsim-muted">
        Packet capture will be available in a future update.
      </div>
    </div>
  );
}

export default observer(PacketInspector);
