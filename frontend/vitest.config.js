import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

// Vitest configuration. jsdom + React Testing Library, with the shared setup
// file that wires jest-dom matchers and the MSW server.
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
