import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// In development Vite forwards /api and /media to Django, so the browser sees a single site (same cookies, no CORS).
const backend = process.env.VITE_API_TARGET || "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Docker on Windows does not report file changes to the container, so Vite checks for them itself.
    watch: process.env.VITE_USE_POLLING ? { usePolling: true, interval: 300 } : undefined,
    proxy: {
      "/api": { target: backend, changeOrigin: false },
      "/media": { target: backend, changeOrigin: false },
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: "./src/test/setup.js",
  },
});
