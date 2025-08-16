#!/bin/bash

# Quick Start Script for Local Development
# This script helps you quickly set up and start the development environment

set -e

echo "🐺 Cyber Werewolves - Quick Start for Local Development"
echo "======================================================"

# Check dependencies
echo "🔍 Checking dependencies..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not installed"
    echo "   Please install Docker from https://docker.com"
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is required but not installed"
    echo "   Please install Docker Compose"
    exit 1
fi

# Check Python
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "❌ Python is required but not installed"
    echo "   Please install Python 3.8+ from https://python.org"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed"
    echo "   Please install Node.js from https://nodejs.org"
    exit 1
fi

echo "✅ All dependencies are installed"

# Setup environment
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.local .env
    echo "✅ Created .env file"
    echo "⚠️  Please edit .env and add your API keys:"
    echo "   - OPENAI_API_KEY (required)"
    echo "   - ANTHROPIC_API_KEY (optional)"
    echo ""
    read -p "   Press Enter to continue after editing .env file..."
else
    echo "✅ Found existing .env file"
fi

# Start infrastructure
echo "🚀 Starting infrastructure services..."
./scripts/start-infra.sh

echo ""
echo "🎯 Infrastructure is ready! Now you can start the application services:"
echo ""
echo "   Terminal 1 (API):     ./scripts/start-api.sh"
echo "   Terminal 2 (Agents):  ./scripts/start-agents.sh"
echo "   Terminal 3 (Web):     ./scripts/start-web.sh"
echo ""
echo "🌐 After starting all services, access:"
echo "   Frontend:  http://localhost:3000"
echo "   API Docs:  http://localhost:8000/docs"
echo ""
echo "📖 For detailed instructions, see LOCAL_DEVELOPMENT.md"
echo ""

# Ask if user wants to open new terminals (on supported systems)
if command -v gnome-terminal &> /dev/null; then
    read -p "🖥️  Open new terminals for services? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        gnome-terminal --title="API Service" -- bash -c "./scripts/start-api.sh; bash"
        gnome-terminal --title="Agents Service" -- bash -c "./scripts/start-agents.sh; bash"
        gnome-terminal --title="Web Frontend" -- bash -c "./scripts/start-web.sh; bash"
        echo "✅ Opened terminals for all services"
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    read -p "🖥️  Open new terminals for services? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        osascript -e 'tell application "Terminal" to do script "./scripts/start-api.sh"'
        osascript -e 'tell application "Terminal" to do script "./scripts/start-agents.sh"' 
        osascript -e 'tell application "Terminal" to do script "./scripts/start-web.sh"'
        echo "✅ Opened terminals for all services"
    fi
fi

echo "🎉 Quick start complete! Happy coding! 🐺"