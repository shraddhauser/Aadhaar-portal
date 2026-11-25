@echo off
title Aadhaar Analytics Portal
color 0B

echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║          AADHAAR ANALYTICS PORTAL - LAUNCHER                 ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

:: ── Set project root to the directory where this bat file lives ──
cd /d "%~dp0"
echo [INFO] Project Root: %cd%

:: ── Check Python is available ──
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Python is not installed or not in PATH.
    echo         Please install Python 3.10+ and try again.
    pause
    exit /b 1
)

:: ── Create virtual environment if it doesn't exist ──
if not exist "venv\Scripts\activate.bat" (
    echo.
    echo [SETUP] Virtual environment not found. Creating one...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [SETUP] Virtual environment created successfully.
)

:: ── Activate virtual environment ──
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

:: ── Install / update dependencies ──
echo [INFO] Installing dependencies (this may take a moment on first run)...
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to install dependencies. Check requirements.txt.
    pause
    exit /b 1
)
echo [OK]   Dependencies are up to date.

echo.
echo ═══════════════════════════════════════════════════════════════
echo   Starting Aadhaar Portal...
echo.
echo   Frontend + Backend : http://localhost:8000
echo   API Docs (Swagger) : http://localhost:8000/docs
echo   Login Credentials  : admin / Admin@1234
echo.
echo   Press Ctrl+C to stop the server.
echo ═══════════════════════════════════════════════════════════════
echo.

:: ── Launch the FastAPI server (serves both backend API + frontend) ──
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

:: ── If the server exits, pause so the user can see any errors ──
echo.
echo [INFO] Server has stopped.
pause
