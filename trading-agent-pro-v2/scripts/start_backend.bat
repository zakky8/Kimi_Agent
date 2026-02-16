@echo off
chcp 65001 >nul
title AI Trading Agent - Backend Server
cd ..
call venv\Scripts\activate.bat
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
