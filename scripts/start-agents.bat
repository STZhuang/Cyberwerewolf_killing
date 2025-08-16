@echo off
REM Start Agno Agents Server for Local Development (Windows)

echo 🤖 Starting Cyber Werewolves Agents Server
echo ==========================================

REM Check if we're in the right directory
if not exist "apps\agents\main.py" (
    echo ❌ Please run this script from the project root directory
    pause
    exit /b 1
)

REM Load environment variables if .env exists
if exist ".env" (
    echo 📝 Loading environment variables...
    for /f "usebackq tokens=*" %%i in (".env") do (
        set "%%i" 2>nul
    )
    echo ✅ Environment loaded
) else (
    echo ⚠️  No .env file found, using defaults
)

REM Set default ports if not set
if not defined API_PORT set API_PORT=8000
if not defined AGENT_PORT set AGENT_PORT=8001
if not defined LOG_LEVEL set LOG_LEVEL=info

echo 🔍 Checking API server...
REM Simple check if API port is listening
netstat -an | find ":%API_PORT%" >nul
if errorlevel 1 (
    echo ⚠️  API server port %API_PORT% is not listening
    echo    The agents service will start but may not work properly
    echo    Start API server first: scripts\start-api.bat
) else (
    echo ✅ API server appears to be running
)

REM Navigate to Agents directory  
cd apps\agents

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" if not exist ".venv" if not defined VIRTUAL_ENV (
    echo ⚠️  No virtual environment detected. Creating one...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo ✅ Virtual environment created and activated
) else if exist "venv" (
    echo 🐍 Activating virtual environment...
    call venv\Scripts\activate.bat
) else if exist ".venv" (
    echo 🐍 Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo ✅ Using current Python environment
)

REM Install dependencies
echo 📦 Installing/updating dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)
echo ✅ Dependencies installed

REM Set up Python path
set PYTHONPATH=..\..\packages;.;%PYTHONPATH%

REM Check API keys
echo 🔑 Checking API keys...
if "%OPENAI_API_KEY%"=="" (
    echo ⚠️  OPENAI_API_KEY not configured
    echo    Agents may not work properly without API keys
) else if "%OPENAI_API_KEY%"=="sk-your-openai-api-key-here" (
    echo ⚠️  OPENAI_API_KEY not configured (using placeholder)
) else (
    echo ✅ OpenAI API key configured
)

if not "%ANTHROPIC_API_KEY%"=="" if not "%ANTHROPIC_API_KEY%"=="sk-ant-your-anthropic-key-here" (
    echo ✅ Anthropic API key configured
)

echo.
echo 🚀 Starting Agents server...
echo    URL: http://localhost:%AGENT_PORT%
echo    Press Ctrl+C to stop
echo.

REM Start the Agents server
uvicorn main:app --host 0.0.0.0 --port %AGENT_PORT% --reload --log-level %LOG_LEVEL%