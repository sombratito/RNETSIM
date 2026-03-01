import { useEffect } from "react";
import { observer } from "mobx-react-lite";
import { profileStore } from "../../state/profile-store";
import { builderStore } from "../../state/builder-store";

function DeviceProfileList() {
  const { profiles } = profileStore;
  const { selectedProfileId } = builderStore;

  useEffect(() => {
    profileStore.loadProfiles();
  }, []);

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-gray-300">Device Profiles</h3>
      {profiles.map((profile) => (
        <button
          key={profile.id}
          onClick={() => {
            builderStore.selectProfile(profile.id);
            builderStore.setMode("place_node");
          }}
          className={`flex w-full items-start gap-3 rounded p-2 text-left transition-colors ${
            selectedProfileId === profile.id
              ? "ring-2 border border-rnetsim-accent bg-rnetsim-accent/10"
              : "border border-transparent hover:bg-rnetsim-panel"
          }`}
        >
          {/* Icon circle */}
          <div
            className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full text-xs font-bold text-white"
            style={{ backgroundColor: profile.color }}
          >
            {profile.abbreviation}
          </div>

          {/* Profile info */}
          <div className="min-w-0 flex-1">
            <div className="text-sm font-medium text-gray-200">
              {profile.name}
            </div>
            <div className="text-xs text-gray-500">
              {profile.cpu} · {profile.ram} · {profile.radio}
            </div>
            <div className="text-xs text-gray-500">
              {profile.bandwidth_display} · {profile.role}
              {profile.sleep_schedule && ` · ${profile.sleep_schedule} duty`}
            </div>
          </div>
        </button>
      ))}
    </div>
  );
}

export default observer(DeviceProfileList);
