import { makeAutoObservable, runInAction } from "mobx";
import type { DeviceProfile } from "../schemas/profile";
import {
  fetchProfiles,
  createProfile,
  deleteProfile,
} from "../api/profiles";

class ProfileStore {
  profiles: DeviceProfile[] = [];
  isLoading = false;

  constructor() {
    makeAutoObservable(this);
  }

  async loadProfiles(): Promise<void> {
    this.isLoading = true;
    try {
      const profiles = await fetchProfiles();
      runInAction(() => {
        this.profiles = profiles;
      });
    } finally {
      runInAction(() => {
        this.isLoading = false;
      });
    }
  }

  async create(profile: DeviceProfile): Promise<void> {
    await createProfile(profile);
    await this.loadProfiles();
  }

  async remove(id: string): Promise<void> {
    await deleteProfile(id);
    await this.loadProfiles();
  }

  getById(id: string): DeviceProfile | undefined {
    return this.profiles.find((p) => p.id === id);
  }
}

export const profileStore = new ProfileStore();
