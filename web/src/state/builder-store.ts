import { makeAutoObservable } from "mobx";

export type BuilderMode = "select" | "draw_rect" | "place_node" | "delete";

export interface BuilderNode {
  id: string;
  name: string;
  profileId: string;
  lat: number;
  lon: number;
  alt: number;
}

export interface BuilderEvent {
  id: string;
  at: string;
  action: string;
  target: string | null;
  params: Record<string, unknown> | null;
}

class BuilderStore {
  mode: BuilderMode = "select";
  bbox: [number, number, number, number] | null = null; // [sw_lat, sw_lon, ne_lat, ne_lon]
  nodes: BuilderNode[] = [];
  events: BuilderEvent[] = [];
  selectedProfileId: string | null = null;
  selectedNodeId: string | null = null;
  scenarioName = "";
  scenarioDescription = "";
  gatewayNodeName: string | null = null;
  gatewayPort = 4242;

  private nodeCounter = 0;

  constructor() {
    makeAutoObservable(this);
  }

  setMode(mode: BuilderMode): void {
    this.mode = mode;
  }

  setBbox(bbox: [number, number, number, number]): void {
    this.bbox = bbox;
  }

  selectProfile(profileId: string): void {
    this.selectedProfileId = profileId;
  }

  addNode(lat: number, lon: number, profileId: string, alt = 0): void {
    this.nodeCounter++;
    const id = `node-${this.nodeCounter}`;
    const name = `${profileId}-${String(this.nodeCounter).padStart(2, "0")}`;
    this.nodes.push({ id, name, profileId, lat, lon, alt });
  }

  removeNode(id: string): void {
    this.nodes = this.nodes.filter((n) => n.id !== id);
    if (this.selectedNodeId === id) {
      this.selectedNodeId = null;
    }
  }

  moveNode(id: string, lat: number, lon: number): void {
    const node = this.nodes.find((n) => n.id === id);
    if (node) {
      node.lat = lat;
      node.lon = lon;
    }
  }

  selectNode(id: string | null): void {
    this.selectedNodeId = id;
  }

  addEvent(event: Omit<BuilderEvent, "id">): void {
    const id = `event-${Date.now()}`;
    this.events.push({ id, ...event });
  }

  removeEvent(id: string): void {
    this.events = this.events.filter((e) => e.id !== id);
  }

  updateEventTime(id: string, at: string): void {
    const event = this.events.find((e) => e.id === id);
    if (event) event.at = at;
  }

  reset(): void {
    this.mode = "select";
    this.bbox = null;
    this.nodes = [];
    this.events = [];
    this.selectedProfileId = null;
    this.selectedNodeId = null;
    this.scenarioName = "";
    this.scenarioDescription = "";
    this.gatewayNodeName = null;
    this.gatewayPort = 4242;
    this.nodeCounter = 0;
  }
}

export const builderStore = new BuilderStore();
