import { makeAutoObservable, runInAction } from "mobx";
import type { NodeStatus, LinkStatus } from "../schemas/simulation";
import {
  launchSimulation,
  stopSimulation,
  injectEvent,
  fetchSimulationStatus,
} from "../api/simulation";

class SimulationStore {
  isRunning = false;
  isConnected = false;
  scenarioName: string | null = null;
  nodes: NodeStatus[] = [];
  links: LinkStatus[] = [];
  selectedNodeId: string | null = null;

  private ws: WebSocket | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private reconnectDelay = 1000;
  private pollTimer: ReturnType<typeof setInterval> | null = null;

  constructor() {
    makeAutoObservable(this);
  }

  get selectedNode(): NodeStatus | undefined {
    return this.nodes.find((n) => n.name === this.selectedNodeId);
  }

  get healthyCount(): number {
    return this.nodes.filter((n) => n.status === "healthy").length;
  }

  selectNode(name: string | null): void {
    this.selectedNodeId = name;
  }

  async launch(scenario: string): Promise<void> {
    await launchSimulation(scenario);
  }

  async stop(): Promise<void> {
    await stopSimulation();
  }

  async inject(
    action: string,
    target?: string,
    params?: Record<string, unknown>,
  ): Promise<void> {
    await injectEvent(action, target, params);
  }

  async fetchStatus(): Promise<void> {
    try {
      const data = await fetchSimulationStatus();
      runInAction(() => {
        this.isRunning = data.running ?? false;
        this.scenarioName = data.scenario_name ?? null;
        this.nodes = data.nodes ?? [];
        this.links = data.links ?? [];
      });
    } catch {
      // Ignore fetch errors
    }
  }

  connect(): void {
    if (this.ws) return;

    if (!this.pollTimer) {
      this.fetchStatus();
      this.pollTimer = setInterval(() => this.fetchStatus(), 3000);
    }

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const url = `${protocol}//${window.location.host}/ws`;
    const ws = new WebSocket(url);

    ws.onopen = () => {
      runInAction(() => {
        this.isConnected = true;
        this.reconnectDelay = 1000;
      });
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        runInAction(() => {
          this.isRunning = data.running ?? false;
          this.scenarioName = data.scenario_name ?? null;
          this.nodes = data.nodes ?? [];
          this.links = data.links ?? [];
        });
      } catch {
        // Ignore malformed messages
      }
    };

    ws.onclose = () => {
      runInAction(() => {
        this.isConnected = false;
        this.ws = null;
      });
      this.scheduleReconnect();
    };

    ws.onerror = () => {
      ws.close();
    };

    this.ws = ws;
  }

  disconnect(): void {
    if (this.pollTimer) {
      clearInterval(this.pollTimer);
      this.pollTimer = null;
    }
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  private scheduleReconnect(): void {
    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, this.reconnectDelay);
    this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
  }
}

export const simulationStore = new SimulationStore();
