import { useState } from "react";
import { observer } from "mobx-react-lite";
import { profileStore } from "../../state/profile-store";
import type { DeviceProfile } from "../../schemas/profile";

interface ProfileEditorProps {
  onClose: () => void;
}

const MEDIUMS = [
  "lora_sf7_125",
  "lora_sf8_125",
  "lora_sf12_125",
  "wifi_local",
  "halow_4mhz",
  "ethernet",
  "internet",
  "packet_radio",
  "satellite",
  "sneakernet",
];

function DeviceProfileEditor({ onClose }: ProfileEditorProps) {
  const [form, setForm] = useState({
    id: "",
    name: "",
    abbreviation: "",
    color: "#3b82f6",
    cpu: "",
    ram: "",
    radio: "",
    bandwidth_display: "",
    medium: "lora_sf8_125",
    role: "endpoint",
    sleep_schedule: "",
  });

  const handleSubmit = async () => {
    if (!form.id || !form.name) return;

    const profile: DeviceProfile = {
      ...form,
      sleep_schedule: form.sleep_schedule || null,
      built_in: false,
    };

    await profileStore.create(profile);
    onClose();
  };

  return (
    <div className="space-y-3 p-4">
      <h3 className="text-sm font-semibold text-gray-300">
        Create Custom Profile
      </h3>

      <Input label="ID" value={form.id} onChange={(v) => setForm({ ...form, id: v })} placeholder="my-device" />
      <Input label="Name" value={form.name} onChange={(v) => setForm({ ...form, name: v })} placeholder="My Device" />
      <Input label="Abbreviation" value={form.abbreviation} onChange={(v) => setForm({ ...form, abbreviation: v })} placeholder="MD" />
      <Input label="CPU" value={form.cpu} onChange={(v) => setForm({ ...form, cpu: v })} placeholder="4x A76" />
      <Input label="RAM" value={form.ram} onChange={(v) => setForm({ ...form, ram: v })} placeholder="4 GB" />
      <Input label="Radio" value={form.radio} onChange={(v) => setForm({ ...form, radio: v })} placeholder="LoRa SF8" />
      <Input label="Bandwidth" value={form.bandwidth_display} onChange={(v) => setForm({ ...form, bandwidth_display: v })} placeholder="3.1 kbps" />

      <div>
        <label className="mb-1 block text-xs text-gray-500">Medium</label>
        <select
          value={form.medium}
          onChange={(e) => setForm({ ...form, medium: e.target.value })}
          className="w-full rounded bg-rnetsim-panel px-2 py-1 text-sm text-gray-200"
        >
          {MEDIUMS.map((m) => (
            <option key={m} value={m}>{m}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="mb-1 block text-xs text-gray-500">Role</label>
        <select
          value={form.role}
          onChange={(e) => setForm({ ...form, role: e.target.value })}
          className="w-full rounded bg-rnetsim-panel px-2 py-1 text-sm text-gray-200"
        >
          <option value="endpoint">Endpoint</option>
          <option value="transport">Transport</option>
        </select>
      </div>

      <Input label="Sleep Schedule" value={form.sleep_schedule} onChange={(v) => setForm({ ...form, sleep_schedule: v })} placeholder="5/55 (optional)" />

      <div className="flex gap-2 pt-2">
        <button onClick={handleSubmit} className="rounded bg-rnetsim-accent px-3 py-1 text-sm text-white">
          Create
        </button>
        <button onClick={onClose} className="rounded bg-rnetsim-panel px-3 py-1 text-sm text-gray-400">
          Cancel
        </button>
      </div>
    </div>
  );
}

function Input({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <div>
      <label className="mb-1 block text-xs text-gray-500">{label}</label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded bg-rnetsim-panel px-2 py-1 text-sm text-gray-200 placeholder-gray-600"
      />
    </div>
  );
}

export default observer(DeviceProfileEditor);
