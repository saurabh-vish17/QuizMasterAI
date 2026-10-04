@echo off
TITLE QuizMaster AI Launcher
:: QuizMaster AI - One-Click Application Launcher for Windows

cd /d "%~dp0"

:: Check if virtual environment Python exists
if exist "venv\Scripts\python.exe" (
    set PYTHON_EXEC=venv\Scripts\python.exe
) else (
    set PYTHON_EXEC=python
)

:: Ensure database is initialized/seeded if quiz.db doesn't exist
if not exist "data\quiz.db" (
    echo Initializing QuizMaster AI Database...
    "%PYTHON_EXEC%" seed_data.py
)

:: Launch QuizMaster AI GUI Application
echo Starting QuizMaster AI...
start "" "%PYTHON_EXEC%" main.py
