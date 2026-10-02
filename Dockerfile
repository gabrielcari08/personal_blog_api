# ==============================================================================
# ETAPA 1: BUILDER
# Preparar y compliar las dependencias
# ==============================================================================

# Se crea la imagen basade en Python 3.13 Slim. 
FROM python:3.13-slim AS builder

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Directorio de trabajo. Se indica que se va a trabajar dentro de /app.
WORKDIR /app

# Herramientas necesarias para compilar algunas dependencias de Python
# y librerías de PostgreSQL.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar las dependencias.
COPY requirements.txt .

RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

# ==============================================================================
# ETAPA 2: RUNNER
# Ejecuta la aplicacion usando las dependencias del BUILDER
# ==============================================================================

# Se crea otra imagen desde 0. 
FROM python:3.13-slim AS runner

# Variables de entorno.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Directorio de trabajo.
WORKDIR /app

# Dependencias necesarias únicamente durante la ejecución.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Se copian las dependencias instaladas desde el builder.
COPY --from=builder /install /usr/local

# Se copia la aplicación.
COPY ./app /app/app

# Puerto.
EXPOSE 8000

# Comando que Docker ejecuta cuando se inicia el contendeor
# Puede modificarse según la estructura del proyecto.
CMD ["uvicorn", "app.entrypoints.api.v1.main:app", "--host", "0.0.0.0", "--port", "8000"]