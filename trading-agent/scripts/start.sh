#!/bin/bash

# Startup script for Docker deployment

set -e

echo "Starting AI Trading Agent..."

# Start nginx in background
echo "Starting nginx..."
nginx

# Start backend
echo "Starting backend server..."
cd /app/backend
python main.py &

# Wait for backend to start
sleep 5

echo "AI Trading Agent is running!"
echo "- Frontend: http://localhost"
echo "- Backend API: http://localhost:8000"
echo "- API Docs: http://localhost:8000/docs"

# Keep container running
tail -f /dev/null
