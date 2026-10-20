import { setupServer } from "msw/node";
import { handlers } from "./handlers.js";

// Servidor MSW compartido por los tests de componente e integración.
export const server = setupServer(...handlers);
