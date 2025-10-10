import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/caregivers": "http://127.0.0.1:8000",
      "/users": "http://127.0.0.1:8000",
      "/memories": "http://127.0.0.1:8000",
      "/upload": "http://127.0.0.1:8000",
      "/health": "http://127.0.0.1:8000",
      "/alerts": "http://127.0.0.1:8000",
      "/tasks": "http://127.0.0.1:8000",
      "/checkins": "http://127.0.0.1:8000"
    }
  },
  build: {
    outDir: "dist",
    emptyOutDir: true
  }
});
