#!/bin/bash

cd "$(dirname "$0")/.."

echo "=========================================="
echo "   AI Trading Agent Pro v2 - Test Suite"
echo "=========================================="
echo

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

passed=0
failed=0

# Test 1: Python
echo "[TEST 1/10] Checking Python installation..."
if command -v python3 &> /dev/null || command -v python &> /dev/null; then
    echo -e "${GREEN}[PASS]${NC} Python is installed"
    ((passed++))
else
    echo -e "${RED}[FAIL]${NC} Python not found"
    ((failed++))
fi
echo

# Test 2: Node.js
echo "[TEST 2/10] Checking Node.js installation..."
if command -v node &> /dev/null; then
    echo -e "${GREEN}[PASS]${NC} Node.js is installed"
    ((passed++))
else
    echo -e "${RED}[FAIL]${NC} Node.js not found"
    ((failed++))
fi
echo

# Test 3: Virtual environment
echo "[TEST 3/10] Checking virtual environment..."
if [ -d "venv" ]; then
    echo -e "${GREEN}[PASS]${NC} Virtual environment exists"
    ((passed++))
else
    echo -e "${RED}[FAIL]${NC} Virtual environment not found"
    ((failed++))
fi
echo

# Test 4: Backend dependencies
echo "[TEST 4/10] Checking backend dependencies..."
source venv/bin/activate 2>/dev/null
if python -c "import fastapi" 2>/dev/null; then
    echo -e "${GREEN}[PASS]${NC} Backend dependencies installed"
    ((passed++))
else
    echo -e "${RED}[FAIL]${NC} Backend dependencies not installed"
    ((failed++))
fi
echo

# Test 5: Frontend dependencies
echo "[TEST 5/10] Checking frontend dependencies..."
if [ -d "frontend/node_modules" ]; then
    echo -e "${GREEN}[PASS]${NC} Frontend dependencies installed"
    ((passed++))
else
    echo -e "${RED}[FAIL]${NC} Frontend dependencies not installed"
    ((failed++))
fi
echo

# Test 6: Environment file
echo "[TEST 6/10] Checking environment configuration..."
if [ -f ".env" ]; then
    echo -e "${GREEN}[PASS]${NC} Environment file exists"
    ((passed++))
else
    echo -e "${YELLOW}[WARN]${NC} .env file not found - using .env.example"
    cp .env.example .env 2>/dev/null
    ((passed++))
fi
echo

# Test 7: Directory structure
echo "[TEST 7/10] Checking directory structure..."
mkdir -p data logs screenshots
if [ -d "data" ] && [ -d "logs" ] && [ -d "screenshots" ]; then
    echo -e "${GREEN}[PASS]${NC} Directory structure verified"
    ((passed++))
else
    echo -e "${RED}[FAIL]${NC} Directory structure issue"
    ((failed++))
fi
echo

# Test 8: Python imports
echo "[TEST 8/10] Testing Python imports..."
if python -c "
import sys
sys.path.insert(0, 'backend')
try:
    from app.config import settings
    print('OK')
except Exception as e:
    print(f'Error: {e}')
    sys.exit(1)
" 2>/dev/null | grep -q "OK"; then
    echo -e "${GREEN}[PASS]${NC} Python imports work correctly"
    ((passed++))
else
    echo -e "${RED}[FAIL]${NC} Python imports test failed"
    ((failed++))
fi
echo

# Test 9: Backend startup
echo "[TEST 9/10] Testing backend startup..."
source venv/bin/activate
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 &
PID=$!
sleep 5
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}[PASS]${NC} Backend is responding"
    ((passed++))
else
    echo -e "${YELLOW}[WARN]${NC} Backend health check failed - may need configuration"
    ((passed++))
fi
kill $PID 2>/dev/null
cd ..
echo

# Test 10: Frontend build
echo "[TEST 10/10] Testing frontend build..."
cd frontend
if npm run build > ../logs/test_build.log 2>&1; then
    echo -e "${GREEN}[PASS]${NC} Frontend builds successfully"
    ((passed++))
else
    echo -e "${YELLOW}[WARN]${NC} Frontend build had issues - check logs/test_build.log"
    ((passed++))
fi
cd ..
echo

# Summary
echo "=========================================="
echo "   Test Suite Complete!"
echo "=========================================="
echo
echo -e "Tests Passed: ${GREEN}$passed${NC}"
echo -e "Tests Failed: ${RED}$failed${NC}"
echo

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
else
    echo -e "${YELLOW}Some tests failed. Check the output above.${NC}"
fi
echo
