#!/bin/bash

# Start Infrastructure Services for Local Development
# This script starts only PostgreSQL, Redis, and optional NATS via Docker

set -e

echo "🐺 Starting Cyber Werewolves Infrastructure"
echo "==========================================="

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed"
    exit 1
fi

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env from .env.local template..."
    cp .env.local .env
    echo "✅ Created .env file"
else
    echo "✅ Using existing .env file"
fi

echo "🚀 Starting infrastructure services..."

# Start basic infrastructure (PostgreSQL + Redis)
docker-compose -f docker-compose.infra.yml up -d postgres redis

echo "⏳ Waiting for services to be ready..."

# Wait for PostgreSQL
echo -n "Waiting for PostgreSQL"
while ! docker-compose -f docker-compose.infra.yml exec -T postgres pg_isready -U werewolves -d cyber_werewolves >/dev/null 2>&1; do
    echo -n "."
    sleep 1
done
echo " ✅"

# Wait for Redis
echo -n "Waiting for Redis"
while ! docker-compose -f docker-compose.infra.yml exec -T redis redis-cli ping >/dev/null 2>&1; do
    echo -n "."
    sleep 1
done
echo " ✅"

echo ""
echo "🎉 Infrastructure services are ready!"
echo ""
echo "📊 Service Status:"
docker-compose -f docker-compose.infra.yml ps
echo ""
echo "🔗 Connection URLs:"
echo "   PostgreSQL: postgresql://werewolves:dev_password_123@localhost:5432/cyber_werewolves"
echo "   Redis:      redis://localhost:6379"
echo ""
echo "🛠️  Optional services:"
echo "   Start PgAdmin:     docker-compose -f docker-compose.infra.yml --profile with-pgadmin up -d pgadmin"
echo "   Start Redis GUI:   docker-compose -f docker-compose.infra.yml --profile with-redis-gui up -d redis-commander"
echo "   Start NATS:        docker-compose -f docker-compose.infra.yml --profile with-nats up -d nats"
echo ""
echo "🚦 Next steps:"
echo "   1. Start API:      cd apps/api && uvicorn app.main:app --reload --port 8000"
echo "   2. Start Agents:   cd apps/agents && uvicorn main:app --reload --port 8001"  
echo "   3. Start Frontend: cd apps/web && npm run dev"
echo ""
echo "🛑 To stop: docker-compose -f docker-compose.infra.yml down"