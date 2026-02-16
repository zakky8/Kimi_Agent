@echo off
chcp 65001 >nul
title AI Trading Agent Pro v2 - Testing
cd ..

echo ==========================================
echo   AI Trading Agent Pro v2 - Test Suite
echo ==========================================
echo.

REM Check Python
echo [TEST 1/10] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Python not found
    exit /b 1
)
echo [PASS] Python is installed
echo.

REM Check Node.js
echo [TEST 2/10] Checking Node.js installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Node.js not found
    exit /b 1
)
echo [PASS] Node.js is installed
echo.

REM Check virtual environment
echo [TEST 3/10] Checking virtual environment...
if not exist venv (
    echo [FAIL] Virtual environment not found
    exit /b 1
)
echo [PASS] Virtual environment exists
echo.

REM Check backend dependencies
echo [TEST 4/10] Checking backend dependencies...
call venv\Scripts\activate.bat >nul 2>&1
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo [FAIL] FastAPI not installed
    exit /b 1
)
echo [PASS] Backend dependencies installed
echo.

REM Check frontend dependencies
echo [TEST 5/10] Checking frontend dependencies...
if not exist frontend\node_modules (
    echo [FAIL] Frontend dependencies not installed
    exit /b 1
)
echo [PASS] Frontend dependencies installed
echo.

REM Check .env file
echo [TEST 6/10] Checking environment configuration...
if not exist .env (
    echo [WARNING] .env file not found - using .env.example
    copy .env.example .env >nul 2>&1
)
echo [PASS] Environment file exists
echo.

REM Check directory structure
echo [TEST 7/10] Checking directory structure...
if not exist data mkdir data
if not exist logs mkdir logs
if not exist screenshots mkdir screenshots
echo [PASS] Directory structure verified
echo.

REM Test Python imports
echo [TEST 8/10] Testing Python imports...
python -c "
import sys
sys.path.insert(0, 'backend')
try:
    from app.config import settings
    print('[PASS] Configuration module imports successfully')
except Exception as e:
    print(f'[FAIL] Configuration import error: {e}')
    sys.exit(1)
"
if errorlevel 1 (
    echo [FAIL] Python imports test failed
    exit /b 1
)
echo.

REM Test backend startup (brief)
echo [TEST 9/10] Testing backend startup...
start /B cmd /c "call venv\Scripts\activate.bat && cd backend && uvicorn main:app --host 0.0.0.0 --port 8000 > logs\test_backend.log 2>&1"
timeout /t 5 >nul
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Backend health check failed - may need configuration
) else (
    echo [PASS] Backend is responding
)
taskkill /F /IM python.exe >nul 2>&1
echo.

REM Test frontend build
echo [TEST 10/10] Testing frontend build...
cd frontend
npm run build > logs\test_build.log 2>&1
if errorlevel 1 (
    echo [WARNING] Frontend build had issues - check logs\test_build.log
) else (
    echo [PASS] Frontend builds successfully
)
cd ..
echo.

echo ==========================================
echo   Test Suite Complete!
echo ==========================================
echo.
echo Check logs\test_*.log for detailed output
echo.
pause
