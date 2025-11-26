@echo off
setlocal

:: --- Configuration ---
set VENV_NAME=venv
set PYTHON_CMD=python

:: --- 1. Check for Python ---
echo Checking for Python...
where %PYTHON_CMD% >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Python is not found in your system's PATH.
    echo Please install Python 3.8+ and ensure it's added to your PATH.
    echo https://www.python.org/downloads/
    goto :eof
)
echo Python found.

:: --- 2. Check for Ollama ---
echo Checking for Ollama server...
curl http://localhost:11434 >nul 2>nul
if %errorlevel% neq 0 (
    echo WARNING: Ollama server is not running at http://localhost:11434.
    echo Please ensure the Ollama application is installed and running.
    echo You can download it from: https://ollama.com/
    echo After starting Ollama, you may need to run this script again.
    pause
) else (
    echo Ollama server is running.
    
    echo Checking for gemma3:1b model...
    ollama list | findstr /C:"gemma3:1b" >nul
    if %errorlevel% neq 0 (
        echo Model not found. Pulling gemma3:1b from Ollama...
        ollama pull gemma3:1b
        if %errorlevel% neq 0 (
            echo ERROR: Failed to pull gemma3:1b model. Please check your Ollama installation and network.
            pause
            goto :eof
        )
        echo Model pulled successfully.
    ) else (
        echo gemma3:1b model is already available.
    )
)

:: --- 3. Create Virtual Environment ---
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

:: --- 4. Install Dependencies ---
echo Activating virtual environment and installing dependencies...
call "%VENV_NAME%\Scripts\activate.bat"
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies from requirements.txt.
    goto :eof
)
echo Dependencies installed successfully.

:: --- 5. Start FastAPI Server ---
echo.
echo Starting the FastAPI server in a new window...
start "FastAPI Server" cmd /c "call "%VENV_NAME%\Scripts\activate.bat" && uvicorn api:app --reload"

:: Give the server a moment to start
timeout /t 5 /nobreak >nul

:: --- 6. Launch Streamlit UI ---
echo.
echo Launching the Streamlit UI...
streamlit run streamlit_app.py

:: --- End ---
echo.
echo Setup complete. The FastAPI server is running in a separate window.
endlocal
