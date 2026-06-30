@echo off
setlocal

cd /d "%~dp0"

set "PY_CMD="
where python >nul 2>&1
if not errorlevel 1 (
    set "PY_CMD=python"
) else (
    where py >nul 2>&1
    if not errorlevel 1 (
        set "PY_CMD=py"
    )
)

if "%PY_CMD%"=="" (
    echo.
    echo Python was not found.
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure "Add Python to PATH" is selected during installation.
    pause
    exit /b 1
)

if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment...
    %PY_CMD% -m venv venv
    if errorlevel 1 (
        echo.
        echo Could not create the virtual environment.
        echo Try installing Python again and selecting "Add Python to PATH".
        pause
        exit /b 1
    )
)

if exist "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" --version >nul 2>&1
    if errorlevel 1 (
        echo Existing virtual environment is not working. Recreating it...
        rmdir /s /q venv
        %PY_CMD% -m venv venv
        if errorlevel 1 (
            echo.
            echo Could not recreate the virtual environment.
            echo Try deleting the venv folder manually, then run this file again.
            pause
            exit /b 1
        )
    )
)

if not exist "venv\Scripts\python.exe" (
    echo.
    echo Could not create the virtual environment.
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure "Add Python to PATH" is selected during installation.
    pause
    exit /b 1
)

call "venv\Scripts\activate.bat"

echo Installing required packages...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo Starting Q-Rescue AI Dashboard...
python -m streamlit run Home.py

pause
