@echo off
chcp 65001 >nul
title AI Trading Agent Pro v2 - Installation

echo ==========================================
echo   AI Trading Agent Pro v2 - Installer
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

echo [OK] Python found
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH
    echo Please install Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
)

echo [OK] Node.js found
echo.

REM Create virtual environment
echo Creating Python virtual environment...
cd ..
if exist venv (
    echo Virtual environment already exists. Removing old environment...
    rmdir /s /q venv
)
python -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment created
echo.

REM Activate virtual environment and install backend dependencies
echo Installing backend dependencies...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r backend\requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install backend dependencies
    pause
    exit /b 1
)
echo [OK] Backend dependencies installed
echo.

REM Install Playwright browsers
echo Installing Playwright browsers...
playwright install chromium
if errorlevel 1 (
    echo [WARNING] Playwright browser installation may have issues
)
echo [OK] Playwright browsers installed
echo.

REM Install frontend dependencies
echo Installing frontend dependencies...
cd frontend
npm install
if errorlevel 1 (
    echo [ERROR] Failed to install frontend dependencies
    pause
    exit /b 1
)
echo [OK] Frontend dependencies installed
echo.

cd ..

REM Create .env file if not exists
echo Setting up environment configuration...
if not exist .env (
    copy .env.example .env >nul 2>&1
    if errorlevel 1 (
        echo # AI Trading Agent Pro v2 Configuration > .env
        echo. >> .env
        echo # AI Providers >> .env
        echo OPENROUTER_API_KEY= >> .env
        echo GEMINI_API_KEY= >> .env
        echo GROQ_API_KEY= >> .env
        echo ANTHROPIC_API_KEY= >> .env
        echo. >> .env
        echo # Trading APIs >> .env
        echo BINANCE_API_KEY= >> .env
        echo BINANCE_SECRET_KEY= >> .env
        echo ALPHA_VANTAGE_API_KEY= >> .env
        echo. >> .env
        echo # Telegram >> .env
        echo TELEGRAM_API_ID= >> .env
        echo TELEGRAM_API_HASH= >> .env
        echo. >> .env
        echo # MT5 >> .env
        echo MT5_ENABLED=false >> .env
        echo. >> .env
        echo # RSS Feeds >> .env
        echo RSS_FEEDS= >> .env
    )
    echo [OK] Created .env file - Please configure your API keys
) else (
    echo [OK] .env file already exists
)
echo.

REM Create necessary directories
echo Creating directories...
if not exist data mkdir data
if not exist logs mkdir logs
if not exist screenshots mkdir screenshots
echo [OK] Directories created
echo.

echo ==========================================
echo   Installation Complete!
echo ==========================================
echo.
echo To start the application:
echo.
echo 1. Start Backend:  start_backend.bat
echo 2. Start Frontend: start_frontend.bat
echo 3. Or use:        start_all.bat
echo.
echo Make sure to configure your API keys in .env file!
echo.
pause
