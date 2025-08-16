#!/bin/bash

# Start FastAPI Backend Server for Local Development

set -e

echo "🌐 Starting Cyber Werewolves API Server"
echo "======================================="

# Check if we're in the right directory
if [ ! -f "apps/api/app/main.py" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Load environment variables
if [ -f ".env" ]; then
    echo "📝 Loading environment variables..."
    export $(grep -v '^#' .env | xargs)
    echo "✅ Environment loaded"
else
    echo "⚠️  No .env file found, using defaults"
fi

# Check if infrastructure is running
echo "🔍 Checking infrastructure services..."

# Check PostgreSQL
if ! pg_isready -h localhost -p ${POSTGRES_PORT:-5432} -U ${POSTGRES_USER:-werewolves} >/dev/null 2>&1; then
    echo "❌ PostgreSQL is not running. Please start infrastructure first:"
    echo "   ./scripts/start-infra.sh"
    exit 1
fi
echo "✅ PostgreSQL is running"

# Check Redis
if ! redis-cli -h localhost -p ${REDIS_PORT:-6379} ping >/dev/null 2>&1; then
    echo "❌ Redis is not running. Please start infrastructure first:"
    echo "   ./scripts/start-infra.sh"
    exit 1
fi
echo "✅ Redis is running"

# Navigate to API directory
cd apps/api

# Check if virtual environment exists
if [ ! -d "venv" ] && [ ! -d ".venv" ] && [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  No virtual environment detected. Creating one..."
    python -m venv venv
    source venv/bin/activate
    echo "✅ Virtual environment created and activated"
elif [ -d "venv" ]; then
    echo "🐍 Activating virtual environment..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "🐍 Activating virtual environment..."
    source .venv/bin/activate
else
    echo "✅ Using current Python environment"
fi

# Install dependencies
echo "📦 Installing/updating dependencies..."
pip install -r requirements.txt
echo "✅ Dependencies installed"

# Set up Python path
export PYTHONPATH="../../packages:.:${PYTHONPATH}"

# Run database migrations if needed
echo "🗄️  Checking database..."
python -c "
from app.database import engine, Base
print('Creating database tables...')
Base.metadata.create_all(bind=engine)
print('✅ Database tables ready')
" || echo "⚠️  Database setup skipped"

echo ""
echo "🚀 Starting API server..."
echo "   URL: http://localhost:${API_PORT:-8000}"
echo "   Docs: http://localhost:${API_PORT:-8000}/docs"
echo "   Press Ctrl+C to stop"
echo ""

# Start the API server
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port ${API_PORT:-8000} \
  --reload \
  --reload-exclude "*.pyc" \
  --reload-exclude "__pycache__" \
  --log-level ${LOG_LEVEL:-info}