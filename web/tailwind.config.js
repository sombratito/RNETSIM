/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        rnetsim: {
          bg: "#111820",
          sidebar: "#162040",
          panel: "#1e3050",
          accent: "#3b82f6",
          "accent-dim": "#1e40af",
          success: "#22c55e",
          warning: "#eab308",
          danger: "#ef4444",
          muted: "#64748b",
        },
      },
    },
  },
  plugins: [],
};
