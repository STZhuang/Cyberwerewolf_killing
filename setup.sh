#!/bin/bash

# Cyber Werewolves Project Setup Script
# This script sets up the project for development

set -e  # Exit on any error

echo "🐺 Cyber Werewolves Setup Script"
echo "================================"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check required dependencies
echo "📋 Checking dependencies..."

if ! command_exists docker; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command_exists docker-compose; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.template .env
    echo "⚠️  Please edit .env file and add your API keys and configuration"
    echo "   Required: OPENAI_API_KEY, ANTHROPIC_API_KEY, JWT_SECRET"
else
    echo "✅ .env file already exists"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p infra/deploy/ssl
mkdir -p infra/monitoring/grafana/provisioning/dashboards
mkdir -p infra/monitoring/grafana/provisioning/datasources
mkdir -p logs
echo "✅ Directories created"

# Check if API keys are configured
echo "🔑 Checking API key configuration..."
if [ -f ".env" ]; then
    source .env
    
    if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "sk-your-openai-api-key-here" ]; then
        echo "⚠️  OPENAI_API_KEY not configured in .env"
    else
        echo "✅ OpenAI API key configured"
    fi
    
    if [ -z "$JWT_SECRET" ] || [ "$JWT_SECRET" = "your_very_long_and_secure_jwt_secret_key_here_at_least_32_chars" ]; then
        echo "⚠️  JWT_SECRET not configured in .env - generating one..."
        # Generate a secure JWT secret
        JWT_SECRET=$(openssl rand -base64 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || head -c 32 /dev/urandom | base64)
        sed -i.bak "s/JWT_SECRET=.*/JWT_SECRET=$JWT_SECRET/" .env
        echo "✅ Generated JWT secret"
    else
        echo "✅ JWT secret configured"
    fi
fi

# Pull Docker images
echo "📦 Pulling Docker images..."
docker-compose pull postgres redis nats prometheus grafana nginx

# Build application images
echo "🔨 Building application images..."
docker-compose build

# Start infrastructure services first
echo "🚀 Starting infrastructure services..."
docker-compose up -d postgres redis nats

# Wait for services to be ready
echo "⏳ Waiting for database to be ready..."
timeout=60
while ! docker-compose exec -T postgres pg_isready -U "${POSTGRES_USER:-werewolves}" -d "${POSTGRES_DB:-cyber_werewolves}" >/dev/null 2>&1; do
    timeout=$((timeout - 1))
    if [ $timeout -le 0 ]; then
        echo "❌ Database failed to start within 60 seconds"
        exit 1
    fi
    sleep 1
    echo -n "."
done
echo " ✅ Database is ready"

# Run database initialization
echo "🗄️  Initializing database..."
docker-compose exec -T postgres psql -U "${POSTGRES_USER:-werewolves}" -d "${POSTGRES_DB:-cyber_werewolves}" -f /docker-entrypoint-initdb.d/init_database.sql >/dev/null 2>&1 || echo "Database already initialized"

# Start all services
echo "🚀 Starting all services..."
docker-compose up -d

# Check service health
echo "🏥 Checking service health..."
sleep 10

services=("postgres" "redis" "nats" "api" "agents" "websocket-gateway" "web")
for service in "${services[@]}"; do
    if docker-compose ps "$service" | grep -q "Up"; then
        echo "✅ $service is running"
    else
        echo "❌ $service failed to start"
    fi
done

echo ""
echo "🎉 Setup complete!"
echo ""
echo "🌐 Application URLs:"
echo "   Frontend:     http://localhost:${WEB_PORT:-3000}"
echo "   API:          http://localhost:${API_PORT:-8000}"
echo "   API Docs:     http://localhost:${API_PORT:-8000}/docs"
echo "   Agents:       http://localhost:${AGENT_PORT:-8001}"
echo "   WebSocket:    ws://localhost:${WS_GATEWAY_PORT:-8002}"
echo ""
echo "📊 Monitoring (if enabled):"
echo "   Prometheus:   http://localhost:${PROMETHEUS_PORT:-9090}"
echo "   Grafana:      http://localhost:${GRAFANA_PORT:-3001}"
echo ""
echo "🔧 Useful commands:"
echo "   View logs:    docker-compose logs -f [service_name]"
echo "   Restart:      docker-compose restart [service_name]"
echo "   Stop all:     docker-compose down"
echo "   Clean reset:  docker-compose down -v && docker-compose up -d"
echo ""
echo "📝 Next steps:"
echo "   1. Configure your API keys in .env file"
echo "   2. Visit http://localhost:${WEB_PORT:-3000} to start playing"
echo "   3. Check the README.md for detailed usage instructions"
echo ""

# Check for common issues
echo "🔍 Checking for common issues..."

# Check if ports are available
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠️  Port $1 is already in use. You may need to change the port in .env"
    fi
}

check_port ${WEB_PORT:-3000}
check_port ${API_PORT:-8000}
check_port ${AGENT_PORT:-8001}

echo "✅ Setup verification complete"

# Offer to show logs
echo ""
read -p "👀 Would you like to view the application logs? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📋 Showing logs (Ctrl+C to exit)..."
    docker-compose logs -f
fi