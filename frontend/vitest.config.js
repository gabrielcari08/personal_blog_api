import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

// Configuración de Vitest: jsdom + React Testing Library, con el archivo de
// setup compartido que integra los matchers de jest-dom y el servidor MSW.
export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./tests/setup.js"],
    include: ["tests/**/*.test.{js,jsx}"],
    css: false,
  },
});
