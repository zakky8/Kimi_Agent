#!/bin/bash

# AI Trading Agent - Test Script
# Verifies all components are working correctly

set -e

echo "========================================"
echo "AI Trading Agent - Test Script"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

print_success() {
    echo -e "${GREEN}✓${NC} $1"
    ((TESTS_PASSED++))
}

print_error() {
    echo -e "${RED}✗${NC} $1"
    ((TESTS_FAILED++))
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Test Python installation
test_python() {
    print_info "Testing Python installation..."
    if command -v python3 &> /dev/null || command -v python &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 || python --version 2>&1)
        print_success "Python found: $PYTHON_VERSION"
    else
        print_error "Python not found"
    fi
}

# Test Node.js installation
test_node() {
    print_info "Testing Node.js installation..."
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        print_success "Node.js found: $NODE_VERSION"
    else
        print_error "Node.js not found"
    fi
}

# Test backend dependencies
test_backend_deps() {
    print_info "Testing backend dependencies..."
    cd backend
    
    if [ -d "venv" ]; then
        source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null
        
        # Test FastAPI
        if python -c "import fastapi" 2>/dev/null; then
            print_success "FastAPI installed"
        else
            print_error "FastAPI not installed"
        fi
        
        # Test Playwright
        if python -c "import playwright" 2>/dev/null; then
            print_success "Playwright installed"
        else
            print_error "Playwright not installed"
        fi
        
        # Test Binance
        if python -c "import binance" 2>/dev/null; then
            print_success "python-binance installed"
        else
            print_error "python-binance not installed"
        fi
        
        # Test AI providers
        if python -c "import google.generativeai" 2>/dev/null; then
            print_success "Google Generative AI installed"
        else
            print_error "Google Generative AI not installed"
        fi
        
        if python -c "import groq" 2>/dev/null; then
            print_success "Groq installed"
        else
            print_error "Groq not installed"
        fi
    else
        print_error "Virtual environment not found"
    fi
    
    cd ..
}

# Test frontend dependencies
test_frontend_deps() {
    print_info "Testing frontend dependencies..."
    cd frontend
    
    if [ -d "node_modules" ]; then
        print_success "Node modules installed"
        
        # Check key packages
        if [ -d "node_modules/react" ]; then
            print_success "React installed"
        else
            print_error "React not installed"
        fi
        
        if [ -d "node_modules/@tanstack/react-query" ]; then
            print_success "TanStack Query installed"
        else
            print_error "TanStack Query not installed"
        fi
    else
        print_error "Node modules not found"
    fi
    
    cd ..
}

# Test configuration files
test_config() {
    print_info "Testing configuration files..."
    
    if [ -f "backend/.env" ]; then
        print_success "Backend .env exists"
    else
        print_error "Backend .env not found (copy from .env.example)"
    fi
    
    if [ -f "frontend/.env" ]; then
        print_success "Frontend .env exists"
    else
        print_error "Frontend .env not found (copy from .env.example)"
    fi
}

# Test directory structure
test_directories() {
    print_info "Testing directory structure..."
    
    if [ -d "backend/app" ]; then
        print_success "Backend app directory exists"
    else
        print_error "Backend app directory not found"
    fi
    
    if [ -d "frontend/src" ]; then
        print_success "Frontend src directory exists"
    else
        print_error "Frontend src directory not found"
    fi
    
    if [ -d "backend/logs" ]; then
        print_success "Logs directory exists"
    else
        print_error "Logs directory not found"
    fi
}

# Test API endpoints (if server is running)
test_api() {
    print_info "Testing API endpoints..."
    
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_success "Backend API is running"
        
        # Test config endpoint
        if curl -s http://localhost:8000/api/v1/config > /dev/null 2>&1; then
            print_success "Config endpoint accessible"
        else
            print_error "Config endpoint not accessible"
        fi
    else
        print_error "Backend API not running (start with: cd backend && python main.py)"
    fi
}

# Run all tests
main() {
    test_python
    test_node
    test_directories
    test_config
    test_backend_deps
    test_frontend_deps
    test_api
    
    echo ""
    echo "========================================"
    echo "Test Results"
    echo "========================================"
    echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
    echo ""
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}All tests passed!${NC}"
        exit 0
    else
        echo -e "${RED}Some tests failed. Please check the errors above.${NC}"
        exit 1
    fi
}

main
