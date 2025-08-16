@echo off
REM Start FastAPI Backend Server for Local Development (Windows)

echo 🌐 Starting Cyber Werewolves API Server
echo =======================================

REM Check if we're in the right directory
if not exist "apps\api\app\main.py" (
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
if not defined POSTGRES_PORT set POSTGRES_PORT=5432
if not defined REDIS_PORT set REDIS_PORT=6379
if not defined API_PORT set API_PORT=8000
if not defined LOG_LEVEL set LOG_LEVEL=info

echo 🔍 Checking infrastructure services...

REM Check PostgreSQL (simplified check)
echo Checking PostgreSQL...
netstat -an | find ":%POSTGRES_PORT%" >nul
if errorlevel 1 (
    echo ❌ PostgreSQL port %POSTGRES_PORT% is not listening
    echo    Please start infrastructure first: scripts\start-infra.bat
    pause
    exit /b 1
)
echo ✅ PostgreSQL appears to be running

REM Navigate to API directory
cd apps\api

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

REM Run database setup
echo 🗄️  Setting up database...
python -c "from app.database import engine, Base; Base.metadata.create_all(bind=engine); print('✅ Database tables ready')" 2>nul || echo ⚠️  Database setup skipped

echo.
echo 🚀 Starting API server...
echo    URL: http://localhost:%API_PORT%
echo    Docs: http://localhost:%API_PORT%/docs
echo    Press Ctrl+C to stop
echo.

REM Start the API server
uvicorn app.main:app --host 0.0.0.0 --port %API_PORT% --reload --log-level %LOG_LEVEL%