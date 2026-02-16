#!/bin/bash

# AI Trading Agent Pro v2 - Installation Script
# Supports: macOS, Linux, Windows (WSL/Git Bash)

set -e

echo "========================================"
echo "AI Trading Agent Pro v2 - Installation"
echo "========================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() { echo -e "${GREEN}[INFO]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check Python
print_status "Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    print_error "Python not installed. Please install Python 3.9+."
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
print_status "Found Python $PYTHON_VERSION"

# Check Node.js
print_status "Checking Node.js..."
if ! command -v node &> /dev/null; then
    print_error "Node.js not installed. Please install Node.js 18+."
    exit 1
fi
NODE_VERSION=$(node --version)
print_status "Found Node.js $NODE_VERSION"

# Backend Setup
print_status "Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
fi

print_status "Activating virtual environment..."
source venv/bin/activate

print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

print_status "Installing Playwright browsers..."
playwright install chromium

if [ ! -f ".env" ]; then
    print_status "Creating .env file..."
    cp .env.example .env
    print_warning "Please edit backend/.env and add your API keys"
fi

cd ..

# Frontend Setup
print_status "Setting up frontend..."
cd frontend

print_status "Installing npm packages..."
npm install

if [ ! -f ".env" ]; then
    print_status "Creating .env file..."
    cp .env.example .env
fi

cd ..

# Create directories
mkdir -p backend/logs
mkdir -p backend/data/uploads
mkdir -p backend/data/cache

print_status "Installation complete!"
echo ""
echo "========================================"
echo "Next Steps:"
echo "========================================"
echo ""
echo "1. Configure API keys in backend/.env"
echo "   - OpenRouter (recommended): https://openrouter.ai/keys"
echo "   - Binance: https://www.binance.com/en/support/faq/how-to-create-api-keys-360002502072"
echo "   - Telegram: https://my.telegram.org/apps"
echo ""
echo "2. Start the backend:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
echo "3. Start the frontend (new terminal):"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "4. Open http://localhost:3000 in your browser"
echo ""
