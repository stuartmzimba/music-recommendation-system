@echo off
REM Music Recommendation System Launcher (Windows)
REM Double-click this file to start both frontend and backend

echo.
echo ========================================
echo   Music Recommendation System
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if database exists
if not exist "music_recommender.db" (
    echo ❌ Database file not found: music_recommender.db
    echo Please ensure the database is in the current directory
    pause
    exit /b 1
)

echo ✅ Starting Music Recommendation System...
echo.

REM Run the Python launcher
python run_app.py

echo.
echo 👋 Music Recommendation System stopped
pause
