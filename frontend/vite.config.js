import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Vite config for the Personal Blog SPA.
// The dev server proxies /api to the FastAPI backend so the client can use the
// relative base URL VITE_API_BASE_URL=/api/v1 without CORS concerns.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
