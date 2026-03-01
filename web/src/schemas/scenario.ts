import { z } from "zod";

export const ScenarioNodeSchema = z.object({
  name: z.string(),
  role: z.string().default("endpoint"),
  profile: z.string().nullable().optional(),
  lat: z.number().nullable().optional(),
  lon: z.number().nullable().optional(),
  alt: z.number().nullable().optional(),
  interfaces: z.array(z.string()).default(["lora_sf8_125"]),
  sleep_schedule: z.string().nullable().optional(),
  lxmf_propagation: z.boolean().default(false),
});

export const ScenarioEventSchema = z.object({
  at: z.string(),
  action: z.string(),
  target: z.string().nullable().optional(),
  params: z.record(z.unknown()).nullable().optional(),
});

export const ScenarioGatewaySchema = z.object({
  node: z.string(),
  host_port: z.number().default(4242),
});

export const ScenarioMapSchema = z.object({
  source: z.string().default("protomaps"),
  pmtiles_url: z.string().nullable().optional(),
  style: z.string().default("dark"),
  center: z.array(z.number()).default([-78.6382, 35.7796]),
  zoom: z.number().default(12),
  terrain: z.boolean().default(false),
});

export const ScenarioDefaultsSchema = z.object({
  medium: z.string().default("lora_sf8_125"),
  tx_power: z.number().default(20),
  role: z.string().default("endpoint"),
});

export const ScenarioSchema = z.object({
  name: z.string(),
  description: z.string().default(""),
  defaults: ScenarioDefaultsSchema.default({}),
  terrain: z.boolean().default(false),
  map: ScenarioMapSchema.default({}),
  nodes: z.array(ScenarioNodeSchema),
  gateways: z.array(ScenarioGatewaySchema).default([]),
  events: z.array(ScenarioEventSchema).default([]),
});

export type ScenarioNode = z.infer<typeof ScenarioNodeSchema>;
export type ScenarioEvent = z.infer<typeof ScenarioEventSchema>;
export type ScenarioGateway = z.infer<typeof ScenarioGatewaySchema>;
export type ScenarioMap = z.infer<typeof ScenarioMapSchema>;
export type ScenarioDefaults = z.infer<typeof ScenarioDefaultsSchema>;
export type Scenario = z.infer<typeof ScenarioSchema>;

export interface ScenarioSummary {
  name: string;
  description: string;
  node_count: number;
  built_in: boolean;
  featured: boolean;
}
