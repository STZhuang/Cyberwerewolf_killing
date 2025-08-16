@echo off
REM Start Vue.js Frontend for Local Development (Windows)

echo 🌐 Starting Cyber Werewolves Frontend
echo =====================================

REM Check if we're in the right directory
if not exist "apps\web\package.json" (
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
if not defined WEB_PORT set WEB_PORT=3000

REM Navigate to Web directory
cd apps\web

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed
    echo    Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

echo 📋 Node.js version:
node --version

echo 📋 npm version:  
npm --version

REM Install dependencies
if not exist "node_modules" (
    echo 📦 Installing dependencies...
    npm install
    if errorlevel 1 (
        echo ❌ Failed to install dependencies
        pause
        exit /b 1
    )
    echo ✅ Dependencies installed
) else (
    echo 📦 Checking for updated dependencies...
    npm install
    echo ✅ Dependencies up to date
)

REM Check if backend services are running
echo 🔍 Checking backend services...

netstat -an | find ":%API_PORT%" >nul
if not errorlevel 1 (
    echo ✅ API server appears to be running at http://localhost:%API_PORT%
) else (
    echo ⚠️  API server not running at http://localhost:%API_PORT%
    echo    Frontend will start but API calls will fail
)

netstat -an | find ":%AGENT_PORT%" >nul
if not errorlevel 1 (
    echo ✅ Agents server appears to be running at http://localhost:%AGENT_PORT%
) else (
    echo ⚠️  Agents server not running at http://localhost:%AGENT_PORT%
    echo    AI agents may not work properly
)

echo.
echo 🚀 Starting development server...
echo    URL: http://localhost:%WEB_PORT%
echo    Press Ctrl+C to stop
echo.

REM Start the development server
npm run dev