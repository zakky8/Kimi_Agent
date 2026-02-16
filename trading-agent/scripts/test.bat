@echo off
echo ========================================
echo AI Trading Agent - Test Script
echo ========================================
echo.

set TESTS_PASSED=0
set TESTS_FAILED=0

:: Test Python
echo Testing Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Python not found
) else (
    for /f "tokens=2" %%i in ('python --version') do echo [PASS] Python found: %%i
    set /a TESTS_PASSED+=1
)

:: Test Node.js
echo Testing Node.js installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Node.js not found
) else (
    for /f %%i in ('node --version') do echo [PASS] Node.js found: %%i
    set /a TESTS_PASSED+=1
)

:: Test directory structure
echo Testing directory structure...
if exist "backend\app" (
    echo [PASS] Backend app directory exists
    set /a TESTS_PASSED+=1
) else (
    echo [FAIL] Backend app directory not found
    set /a TESTS_FAILED+=1
)

if exist "frontend\src" (
    echo [PASS] Frontend src directory exists
    set /a TESTS_PASSED+=1
) else (
    echo [FAIL] Frontend src directory not found
    set /a TESTS_FAILED+=1
)

:: Test configuration
echo Testing configuration files...
if exist "backend\.env" (
    echo [PASS] Backend .env exists
    set /a TESTS_PASSED+=1
) else (
    echo [WARN] Backend .env not found (copy from .env.example)
)

if exist "frontend\.env" (
    echo [PASS] Frontend .env exists
    set /a TESTS_PASSED+=1
) else (
    echo [WARN] Frontend .env not found (copy from .env.example)
)

:: Test API
echo Testing API endpoints...
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo [WARN] Backend API not running (start with: cd backend && python main.py)
) else (
    echo [PASS] Backend API is running
    set /a TESTS_PASSED+=1
)

echo.
echo ========================================
echo Test Results
echo ========================================
echo Passed: %TESTS_PASSED%
echo Failed: %TESTS_FAILED%
echo.

if %TESTS_FAILED%==0 (
    echo All tests passed!
) else (
    echo Some tests failed. Please check the errors above.
)

pause
