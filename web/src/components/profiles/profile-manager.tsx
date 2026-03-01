import { useEffect, useState } from "react";
import { observer } from "mobx-react-lite";
import { profileStore } from "../../state/profile-store";
import DeviceProfileEditor from "../builder/device-profile-editor";

function ProfileManager() {
  const { profiles, isLoading } = profileStore;
  const [isCreating, setIsCreating] = useState(false);

  useEffect(() => {
    profileStore.loadProfiles();
  }, []);

  return (
    <div className="mx-auto max-w-screen-2xl p-6">
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-xl font-semibold">Device Profiles</h2>
        <button
          onClick={() => setIsCreating(true)}
          className="rounded bg-rnetsim-accent px-4 py-2 text-sm text-white"
        >
          Create Profile
        </button>
      </div>

      {isCreating && (
        <div className="mb-6 rounded border border-rnetsim-panel bg-rnetsim-sidebar">
          <DeviceProfileEditor onClose={() => setIsCreating(false)} />
        </div>
      )}

      {isLoading && <p className="text-rnetsim-muted">Loading...</p>}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5">
        {profiles.map((profile) => (
          <div
            key={profile.id}
            className="rounded border border-rnetsim-panel bg-rnetsim-sidebar p-4"
          >
            <div className="mb-2 flex items-center gap-3">
              <div
                className="flex h-10 w-10 items-center justify-center rounded-full text-sm font-bold text-white"
                style={{ backgroundColor: profile.color }}
              >
                {profile.abbreviation}
              </div>
              <div>
                <div className="font-medium">{profile.name}</div>
                <div className="text-xs text-gray-500">
                  {profile.built_in ? "Built-in" : "Custom"}
                </div>
              </div>
            </div>

            <div className="space-y-1 text-sm text-gray-400">
              <div>
                {profile.cpu} · {profile.ram}
              </div>
              <div>
                {profile.radio} · {profile.bandwidth_display}
              </div>
              <div>
                {profile.role}
                {profile.sleep_schedule && ` · ${profile.sleep_schedule} duty cycle`}
              </div>
            </div>

            {!profile.built_in && (
              <button
                onClick={() => profileStore.remove(profile.id)}
                className="mt-3 text-xs text-rnetsim-danger hover:underline"
              >
                Delete
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default observer(ProfileManager);
