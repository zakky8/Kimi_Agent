# ================================================================
# Kimi Agent v3.0 — Multi-stage Dockerfile
# ================================================================
# Build:  docker build -t kimi-agent .
# Run:    docker-compose up -d
# ================================================================

# ── Stage 1: Backend ─────────────────────────────────────────────
FROM python:3.11-slim AS backend

# Install system dependencies (needed for Playwright + ML libs)
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    unzip \
    build-essential \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxcb1 \
    libxkbcommon0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (for Docker layer caching)
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright (for browser automation scraper)
RUN playwright install chromium \
    && playwright install-deps chromium

# Copy backend code
COPY backend/ ./backend/

# Copy migrations
COPY backend/migrations/ ./backend/migrations/

# Create data directories
RUN mkdir -p /app/data /app/logs /app/models

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Start Kimi Agent backend
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ── Stage 2: Frontend Build ─────────────────────────────────────
FROM node:18-alpine AS frontend-build

WORKDIR /app/frontend

# Install dependencies first (layer caching)
COPY frontend/package*.json ./
RUN npm ci --production=false

# Copy source and build
COPY frontend/ ./
RUN npm run build

# ── Stage 3: Production (Nginx) ─────────────────────────────────
FROM nginx:alpine AS production

# Copy frontend build output
COPY --from=frontend-build /app/frontend/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
