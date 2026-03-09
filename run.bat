@echo off
setlocal

echo ==============================================================
echo       Starting Guardianize Enterprise Architecture
echo ==============================================================

cd /d "%~dp0"

echo [1/3] Checking for Virtual Environment...
if not exist "backend\venv\Scripts\activate.bat" (
    echo Creating virtual environment in backend\venv...
    python -m venv backend\venv
) else (
    echo Virtual environment found!
)

echo [2/3] Activating venv and checking dependencies...
call "backend\venv\Scripts\activate.bat"

echo Installing/Verifying requirements from backend\requirements.txt...
python -m pip install --upgrade pip
pip install -r backend\requirements.txt

echo.
echo [3/3] Starting the Servers...
python run_project.py

endlocal
pause
