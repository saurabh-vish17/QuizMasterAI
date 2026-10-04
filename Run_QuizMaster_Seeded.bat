@echo off
TITLE QuizMaster AI Launcher (Seeded Data)
:: QuizMaster AI - One-Click Application Launcher for Windows (Force Seed)

cd /d "%~dp0"

:: Check if virtual environment Python exists
if exist "venv\Scripts\python.exe" (
    set PYTHON_EXEC=venv\Scripts\python.exe
) else (
    set PYTHON_EXEC=python
)

echo Initializing and Seeding QuizMaster AI Database...
"%PYTHON_EXEC%" seed_data.py

echo.
echo Starting QuizMaster AI...
start "" "%PYTHON_EXEC%" main.py
