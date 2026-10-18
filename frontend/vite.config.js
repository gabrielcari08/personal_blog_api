import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Vite config for the Personal Blog SPA.
// The dev server proxies /api to the FastAPI backend so the client can use the
// relative base URL VITE_API_BASE_URL=/api/v1 without CORS concerns.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  // Dentro de Docker el backend responde en el servicio "api"; en el host, en localhost.
  const apiProxyTarget = env.VITE_API_PROXY_TARGET || "http://localhost:8000";
  // Un bind mount de Windows en un contenedor Linux puede no disparar el watcher.
  const usePolling = env.VITE_USE_POLLING === "true";

  const server = {
    port: 5173,
    proxy: {
      "/api": {
        target: apiProxyTarget,
        changeOrigin: true,
      },
    },
  };

  if (usePolling) {
    server.watch = { usePolling: true };
  }

  return {
    plugins: [react(), tailwindcss()],
    server,
  };
});
