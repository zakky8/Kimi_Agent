# AI Trading Agent Pro v2 - Dockerfile
FROM python:3.11-slim as backend

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    unzip \
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

# Set working directory
WORKDIR /app

# Copy backend requirements
COPY backend/requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy backend code
COPY backend/ ./backend/
COPY .env ./

# Expose port
EXPOSE 8000

# Start command
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Frontend stage
FROM node:18-alpine as frontend

WORKDIR /app/frontend

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy frontend code
COPY frontend/ ./

# Build
RUN npm run build

# Production stage
FROM nginx:alpine as production

# Copy frontend build
COPY --from=frontend /app/frontend/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
