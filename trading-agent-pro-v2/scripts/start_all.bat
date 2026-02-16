@echo off
chcp 65001 >nul
title AI Trading Agent Pro v2 - Starting All Services
cd ..

echo Starting AI Trading Agent Pro v2...
echo.

REM Check if virtual environment exists
if not exist venv (
    echo [ERROR] Virtual environment not found. Please run install.bat first.
    pause
    exit /b 1
)

echo Starting Backend Server...
start "AI Trading Agent - Backend" cmd /k "call venv\Scripts\activate.bat && cd backend && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 3 >nul

echo Starting Frontend...
start "AI Trading Agent - Frontend" cmd /k "cd frontend && npm run dev"

timeout /t 3 >nul

echo.
echo ==========================================
echo   All services started!
echo ==========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo API Docs: http://localhost:8000/docs
echo.
echo Press any key to exit this window...
pause >nul
