@echo off
setlocal

:: ============================================================================
:: AI Code Remediation Microservice Setup Script
:: ============================================================================
:: This script automates the complete setup for the project, including
:: dependency installation, Ollama model check, and application launch.
:: ============================================================================

:: --- Change to the script's directory ---
:: This ensures that all paths are relative to the script location,
:: even when "Run as administrator".
cd /d "%~dp0"

:: --- Configuration ---
set VENV_NAME=venv
set PYTHON_CMD=python
set REQUIRED_MODEL=gemma3:1b

:: --- 1. Check for Python ---
echo.
echo Checking for Python installation...
where %PYTHON_CMD% >nul 2>nul
if %errorlevel% neq 0 (
    echo --------------------------------------------------------------------
    echo ^> ERROR: Python is not found in your system's PATH.
    echo ^> Please install Python 3.8+ and ensure it's added to your PATH.
    echo ^> Download from: https://www.python.org/downloads/
    echo --------------------------------------------------------------------
    pause
    goto :eof
)
echo Python found.

:: --- 2. Check for Ollama ---
echo.
echo Checking for Ollama server...
curl http://localhost:11434 >nul 2>nul
if %errorlevel% neq 0 (
    echo --------------------------------------------------------------------
    echo ^> WARNING: Ollama server is not running at http://localhost:11434.
    echo ^> Please ensure the Ollama application is installed and running.
    echo ^> Download from: https://ollama.com/
    echo --------------------------------------------------------------------
    pause
    goto :eof
)
echo Ollama server is running.

:: --- 3. Check for and Pull Ollama Model ---
echo.
echo Checking for Ollama model '%REQUIRED_MODEL%'...
ollama show %REQUIRED_MODEL% >nul 2>nul
if %errorlevel% neq 0 (
    echo Model not found. Pulling '%REQUIRED_MODEL%' from Ollama...
    ollama pull %REQUIRED_MODEL%
    if %errorlevel% neq 0 (
        echo --------------------------------------------------------------------
        echo ^> ERROR: Failed to pull '%REQUIRED_MODEL%'.
        echo ^> Please check your Ollama installation and network connection.
        echo --------------------------------------------------------------------
        pause
        goto :eof
    )
    echo Model pulled successfully.
) else (
    echo Model '%REQUIRED_MODEL%' is already available.
)

:: --- 4. Create Virtual Environment ---
echo.
if not exist "%VENV_NAME%\" (
    echo Creating virtual environment in '%VENV_NAME%'...
    %PYTHON_CMD% -m venv %VENV_NAME%
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment.
        goto :eof
    )
    echo Virtual environment created.
) else (
    echo Virtual environment already exists.
)

:: --- 5. Install Dependencies ---
echo.
echo Activating virtual environment and installing dependencies...
call "%VENV_NAME%\Scripts\activate.bat"
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies from requirements.txt.
    goto :eof
)
echo Dependencies installed successfully.

:: --- 6. Start FastAPI Server ---
echo.
echo Starting the FastAPI server in a new window...
start "FastAPI Server" cmd /c "call "%VENV_NAME%\Scripts\activate.bat" && uvicorn api:app --reload"

:: Give the server a moment to start
echo Waiting for server to initialize...
timeout /t 5 /nobreak >nul

:: --- 7. Launch Streamlit UI ---
echo.
echo Launching the Streamlit UI...
streamlit run streamlit_app.py

:: --- End ---
echo.
echo Setup complete. The FastAPI server is running in a separate window.
endlocal
