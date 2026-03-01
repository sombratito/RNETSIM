import { z } from "zod";

export const DeviceProfileSchema = z.object({
  id: z.string(),
  name: z.string(),
  abbreviation: z.string(),
  color: z.string(),
  cpu: z.string(),
  ram: z.string(),
  radio: z.string(),
  bandwidth_display: z.string(),
  medium: z.string(),
  role: z.string().default("endpoint"),
  sleep_schedule: z.string().nullable().optional(),
  built_in: z.boolean().default(true),
});

export type DeviceProfile = z.infer<typeof DeviceProfileSchema>;
