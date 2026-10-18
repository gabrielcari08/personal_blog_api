# ==============================================================================
# FRONTEND (desarrollo) — Vite + React + Tailwind CSS v4
# Contenedor orientado a desarrollo con recarga en caliente (hot reload).
# ==============================================================================

FROM node:22-alpine

# Directorio de trabajo.
WORKDIR /app

# Dependencias: se copian primero para aprovechar la caché de capas.
COPY package.json package-lock.json ./

# Instalación reproducible de dependencias.
RUN npm ci

# Código fuente. En compose se sobreescribe con un bind mount.
COPY . .

# Puerto del servidor de desarrollo de Vite.
EXPOSE 5173

# --host 0.0.0.0 expone el servidor fuera del contenedor.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
