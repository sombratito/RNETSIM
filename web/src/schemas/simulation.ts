import { z } from "zod";

export const NodeStatusSchema = z.object({
  name: z.string(),
  identity_hash: z.string().default(""),
  role: z.string().default("endpoint"),
  status: z.string().default("offline"),
  lat: z.number().nullable().optional(),
  lon: z.number().nullable().optional(),
  path_count: z.number().default(0),
  announce_count: z.number().default(0),
  link_count: z.number().default(0),
  uptime: z.number().default(0),
});

export const LinkStatusSchema = z.object({
  source: z.string(),
  target: z.string(),
  medium: z.string(),
});

export const SimulationStatusSchema = z.object({
  running: z.boolean().default(false),
  scenario_name: z.string().nullable().optional(),
  node_count: z.number().default(0),
  nodes: z.array(NodeStatusSchema).default([]),
  links: z.array(LinkStatusSchema).default([]),
});

export type NodeStatus = z.infer<typeof NodeStatusSchema>;
export type LinkStatus = z.infer<typeof LinkStatusSchema>;
export type SimulationStatus = z.infer<typeof SimulationStatusSchema>;
