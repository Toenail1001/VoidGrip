@echo off
REM VoidGrip Gesture Control System Launcher
REM Starts the application with proper environment setup

echo.
echo ╔════════════════════════════════════════════════════════════════════╗
echo ║                 VoidGrip - Gesture Control System                  ║
echo ╚════════════════════════════════════════════════════════════════════╝
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ✗ Python not found. Please install Python 3.8+ from https://www.python.org
    pause
    exit /b 1
)

echo ✓ Python found
echo ✓ Starting VoidGrip...
echo.

REM Run the main application
python main.py

if errorlevel 1 (
    echo.
    echo ✗ Application error occurred
    echo For help, run: python setup.py
    pause
)
