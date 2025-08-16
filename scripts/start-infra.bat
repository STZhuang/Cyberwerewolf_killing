@echo off
REM Start Infrastructure Services for Local Development (Windows)
REM This script starts only PostgreSQL, Redis, and optional NATS via Docker

echo 🐺 Starting Cyber Werewolves Infrastructure
echo ===========================================

REM Check if docker-compose is available
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ docker-compose is not installed
    exit /b 1
)

REM Check .env file
if not exist ".env" (
    echo ⚠️  .env file not found!
    echo 📝 Please copy .env to .env and edit the values
    echo    Example: copy .env .env
    pause
    exit /b 1
) else (
    echo ✅ Using existing .env file
)

echo 🚀 Starting infrastructure services...

REM Start basic infrastructure (PostgreSQL + Redis)
docker-compose -f docker-compose.infra.yml up -d postgres redis

echo ⏳ Waiting for services to be ready...

REM Wait for PostgreSQL
echo Waiting for PostgreSQL...
:wait_postgres
docker-compose -f docker-compose.infra.yml exec -T postgres pg_isready -U werewolves -d cyber_werewolves >nul 2>&1
if errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto wait_postgres
)
echo PostgreSQL is ready ✅

REM Wait for Redis
echo Waiting for Redis...
:wait_redis
docker-compose -f docker-compose.infra.yml exec -T redis redis-cli ping >nul 2>&1
if errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto wait_redis
)
echo Redis is ready ✅

echo.
echo 🎉 Infrastructure services are ready!
echo.
echo 📊 Service Status:
docker-compose -f docker-compose.infra.yml ps
echo.
echo 🔗 Connection URLs:
echo    PostgreSQL: postgresql://werewolves:dev_password_123@localhost:5432/cyber_werewolves
echo    Redis:      redis://localhost:6379
echo.
echo 🛠️  Optional services:
echo    Start PgAdmin:     docker-compose -f docker-compose.infra.yml --profile with-pgadmin up -d pgadmin
echo    Start Redis GUI:   docker-compose -f docker-compose.infra.yml --profile with-redis-gui up -d redis-commander
echo    Start NATS:        docker-compose -f docker-compose.infra.yml --profile with-nats up -d nats
echo.
echo 🚦 Next steps:
echo    1. Start API:      cd apps/api ^&^& uvicorn app.main:app --reload --port 8000
echo    2. Start Agents:   cd apps/agents ^&^& uvicorn main:app --reload --port 8001
echo    3. Start Frontend: cd apps/web ^&^& npm run dev
echo.
echo 🛑 To stop: docker-compose -f docker-compose.infra.yml down
pause