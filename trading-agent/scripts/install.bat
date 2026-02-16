@echo off
chcp 65001 >nul
echo ========================================
echo AI Trading Agent - Installation Script
echo ========================================
echo.

setlocal EnableDelayedExpansion

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed. Please install Python 3.9 or higher.
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo [INFO] Found Python %PYTHON_VERSION%

:: Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed. Please install Node.js 18 or higher.
    exit /b 1
)

for /f %%i in ('node --version') do set NODE_VERSION=%%i
echo [INFO] Found Node.js %NODE_VERSION%

:: Check if npm is installed
npm --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm is not installed.
    exit /b 1
)

for /f %%i in ('npm --version') do set NPM_VERSION=%%i
echo [INFO] Found npm %NPM_VERSION%

echo.
echo [INFO] Installing backend dependencies...

cd backend

:: Create virtual environment
if not exist "venv" (
    echo [INFO] Creating Python virtual environment...
    python -m venv venv
)

:: Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate

:: Upgrade pip
echo [INFO] Upgrading pip...
pip install --upgrade pip

:: Install requirements
echo [INFO] Installing Python packages...
pip install -r requirements.txt

:: Install Playwright browsers
echo [INFO] Installing Playwright browsers...
playwright install chromium

:: Create .env file if it doesn't exist
if not exist ".env" (
    echo [INFO] Creating .env file...
    copy .env.example .env
    echo [WARN] Please edit backend\.env and add your API keys
)

cd ..

echo.
echo [INFO] Installing frontend dependencies...

cd frontend

:: Install npm packages
echo [INFO] Installing npm packages...
npm install

:: Create .env file if it doesn't exist
if not exist ".env" (
    echo [INFO] Creating .env file...
    copy .env.example .env
)

cd ..

:: Create necessary directories
echo [INFO] Creating necessary directories...
if not exist "backend\logs" mkdir backend\logs
if not exist "backend\data" mkdir backend\data

echo.
echo ========================================
echo Installation completed successfully!
echo ========================================
echo.
echo To start the application:
echo.
echo 1. Start the backend:
echo    cd backend
echo    venv\Scripts\activate
echo    python main.py
echo.
echo 2. Start the frontend (in a new terminal):
echo    cd frontend
echo    npm run dev
echo.
echo The application will be available at:
echo   - Frontend: http://localhost:3000
echo   - Backend API: http://localhost:8000
echo   - API Docs: http://localhost:8000/docs
echo.
echo Don't forget to:
echo   1. Edit backend\.env with your API keys (all free tiers)
echo   2. Edit frontend\.env if needed
echo.
echo For more information, see README.md

pause
