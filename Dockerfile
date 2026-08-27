# ============================================================
# Stage 1: Build Frontend Dashboard (React + Vite + TypeScript)
# ============================================================
FROM node:24-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install --no-audit --legacy-peer-deps

COPY frontend/ ./
RUN npm run build

# ============================================================
# Stage 2: Production Python Backend (FastAPI + Uvicorn)
# Phase 3: Now uses .dockerignore to exclude evaluation/, docs/, scripts/
# ============================================================
FROM python:3.12-slim-bookworm AS runner
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/backend \
    PORT=8000 \
    APP_MODE=demo \
    DRY_RUN=true

# Install system dependencies (curl for health check probe)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Install Python backend dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code only
# NOTE: .dockerignore excludes evaluation/, scripts/, docs/, *.md from the build context.
COPY backend/ /app/backend/

# Copy built frontend assets to static distribution folder
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Expose container port
EXPOSE 8000

# Health check probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# ── Production CMD (single-worker demo / Render free tier) ────────────────
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

# ── Multi-worker CMD (uncomment for Render paid tier / self-hosted) ────────
# CMD ["gunicorn", "app.main:app", \
#      "--worker-class", "uvicorn.workers.UvicornWorker", \
#      "--workers", "4", "--timeout", "60", \
#      "--bind", "0.0.0.0:8000", \
#      "--access-logfile", "-", "--error-logfile", "-"]
