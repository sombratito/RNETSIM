import { makeAutoObservable, runInAction } from "mobx";
import type { Scenario, ScenarioSummary } from "../schemas/scenario";
import {
  fetchScenarios,
  fetchScenario,
  createScenario,
  deleteScenario,
  duplicateScenario,
} from "../api/scenarios";

class ScenarioStore {
  scenarios: ScenarioSummary[] = [];
  currentScenario: Scenario | null = null;
  isLoading = false;

  constructor() {
    makeAutoObservable(this);
  }

  async loadList(): Promise<void> {
    this.isLoading = true;
    try {
      const list = await fetchScenarios();
      runInAction(() => {
        this.scenarios = list;
      });

      // Auto-load the featured scenario for idle-state preview
      const featured = list.find((s) => s.featured);
      if (featured && !this.currentScenario) {
        await this.loadScenario(featured.name);
      }
    } finally {
      runInAction(() => {
        this.isLoading = false;
      });
    }
  }

  async loadScenario(name: string): Promise<void> {
    const scenario = await fetchScenario(name);
    runInAction(() => {
      this.currentScenario = scenario;
    });
  }

  async create(scenario: Scenario): Promise<void> {
    await createScenario(scenario);
    await this.loadList();
  }

  async remove(name: string): Promise<void> {
    await deleteScenario(name);
    await this.loadList();
  }

  async duplicate(name: string): Promise<string> {
    const newName = await duplicateScenario(name);
    await this.loadList();
    return newName;
  }
}

export const scenarioStore = new ScenarioStore();
