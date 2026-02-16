# Multi-stage Dockerfile for AI Trading Agent

# Stage 1: Backend
FROM python:3.11-slim as backend

WORKDIR /app/backend

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Expose backend port
EXPOSE 8000

# Stage 2: Frontend Builder
FROM node:20-alpine as frontend-builder

WORKDIR /app/frontend

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci

# Copy frontend code
COPY frontend/ .

# Build frontend
RUN npm run build

# Stage 3: Production
FROM python:3.11-slim as production

WORKDIR /app

# Install nginx for serving frontend
RUN apt-get update && apt-get install -y \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Copy backend from backend stage
COPY --from=backend /app/backend /app/backend
COPY --from=backend /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend /usr/local/bin /usr/local/bin

# Copy built frontend
COPY --from=frontend-builder /app/frontend/dist /var/www/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy startup script
COPY scripts/start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Expose ports
EXPOSE 80 8000

# Start both services
CMD ["/app/start.sh"]
