# ============================================================
# Stage 1: Build Frontend Dashboard (React + Vite + TypeScript)
# ============================================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ============================================================
# Stage 2: Production Python Backend (FastAPI + Uvicorn)
# ============================================================
FROM python:3.12-slim AS runner
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/backend \
    PORT=8000 \
    APP_MODE=demo \
    DRY_RUN=true

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python backend dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application, evaluation datasets, and scripts
COPY backend/ /app/backend/
COPY evaluation/ /app/evaluation/
COPY scripts/ /app/scripts/

# Copy built frontend assets to static distribution folder
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Expose container port
EXPOSE 8000

# Health check probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run FastAPI gateway
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
