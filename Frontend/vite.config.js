import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Las llamadas a /api se reenvían al backend Flask
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:5000",
    },
  },
});
