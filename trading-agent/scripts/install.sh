#!/bin/bash

# AI Trading Agent Installation Script
# Supports: macOS, Linux, Windows (WSL/Git Bash)

set -e

echo "========================================"
echo "AI Trading Agent - Installation Script"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detect OS
OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    OS="windows"
fi

print_status "Detected OS: $OS"

# Check Python version
check_python() {
    print_status "Checking Python installation..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_error "Python is not installed. Please install Python 3.9 or higher."
        exit 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    print_status "Found Python $PYTHON_VERSION"
    
    # Check if version is 3.9 or higher
    REQUIRED_VERSION="3.9"
    if [ "$($PYTHON_CMD -c "import sys; print(sys.version_info >= (3, 9))")" != "True" ]; then
        print_error "Python 3.9 or higher is required. Found: $PYTHON_VERSION"
        exit 1
    fi
}

# Check Node.js version
check_node() {
    print_status "Checking Node.js installation..."
    
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed. Please install Node.js 18 or higher."
        exit 1
    fi
    
    NODE_VERSION=$(node --version | cut -d'v' -f2)
    print_status "Found Node.js $NODE_VERSION"
    
    # Check if version is 18 or higher
    MAJOR_VERSION=$(echo $NODE_VERSION | cut -d'.' -f1)
    if [ "$MAJOR_VERSION" -lt 18 ]; then
        print_error "Node.js 18 or higher is required. Found: $NODE_VERSION"
        exit 1
    fi
}

# Check npm
check_npm() {
    print_status "Checking npm installation..."
    
    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed. Please install npm."
        exit 1
    fi
    
    NPM_VERSION=$(npm --version)
    print_status "Found npm $NPM_VERSION"
}

# Install backend dependencies
install_backend() {
    print_status "Installing backend dependencies..."
    
    cd backend
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        print_status "Creating Python virtual environment..."
        $PYTHON_CMD -m venv venv
    fi
    
    # Activate virtual environment
    print_status "Activating virtual environment..."
    if [[ "$OS" == "windows" ]]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
    
    # Upgrade pip
    print_status "Upgrading pip..."
    pip install --upgrade pip
    
    # Install requirements
    print_status "Installing Python packages..."
    pip install -r requirements.txt
    
    # Install Playwright browsers
    print_status "Installing Playwright browsers..."
    playwright install chromium
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        print_status "Creating .env file..."
        cp .env.example .env
        print_warning "Please edit backend/.env and add your API keys"
    fi
    
    cd ..
}

# Install frontend dependencies
install_frontend() {
    print_status "Installing frontend dependencies..."
    
    cd frontend
    
    # Install npm packages
    print_status "Installing npm packages..."
    npm install
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        print_status "Creating .env file..."
        cp .env.example .env
    fi
    
    cd ..
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p backend/logs
    mkdir -p backend/data
    mkdir -p docs
}

# Print success message
print_success() {
    echo ""
    echo "========================================"
    echo -e "${GREEN}Installation completed successfully!${NC}"
    echo "========================================"
    echo ""
    echo "To start the application:"
    echo ""
    echo "1. Start the backend:"
    echo "   cd backend"
    if [[ "$OS" == "windows" ]]; then
        echo "   venv\\Scripts\\activate"
    else
        echo "   source venv/bin/activate"
    fi
    echo "   python main.py"
    echo ""
    echo "2. Start the frontend (in a new terminal):"
    echo "   cd frontend"
    echo "   npm run dev"
    echo ""
    echo "The application will be available at:"
    echo "  - Frontend: http://localhost:3000"
    echo "  - Backend API: http://localhost:8000"
    echo "  - API Docs: http://localhost:8000/docs"
    echo ""
    echo "Don't forget to:"
    echo "  1. Edit backend/.env with your API keys (all free tiers)"
    echo "  2. Edit frontend/.env if needed"
    echo ""
    echo "For more information, see README.md"
}

# Main installation process
main() {
    print_status "Starting installation..."
    
    # Check prerequisites
    check_python
    check_node
    check_npm
    
    # Create directories
    create_directories
    
    # Install dependencies
    install_backend
    install_frontend
    
    # Print success message
    print_success
}

# Run main function
main
