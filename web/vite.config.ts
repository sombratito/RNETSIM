import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const apiPort = process.env.RNETSIM_API_PORT ?? "3000";
const vitePort = Number(process.env.RNETSIM_VITE_PORT ?? "5173");

export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: vitePort,
    strictPort: true,
    proxy: {
      "/api": `http://localhost:${apiPort}`,
      "/ws": { target: `ws://localhost:${apiPort}`, ws: true },
    },
  },
});
