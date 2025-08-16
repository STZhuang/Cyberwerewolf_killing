#!/bin/bash

# Start Vue.js Frontend for Local Development

set -e

echo "🌐 Starting Cyber Werewolves Frontend"
echo "====================================="

# Check if we're in the right directory
if [ ! -f "apps/web/package.json" ]; then
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

# Navigate to Web directory
cd apps/web

# Check if Node.js is installed
if ! command -v npm &> /dev/null; then
    echo "❌ Node.js/npm is not installed"
    echo "   Please install Node.js from https://nodejs.org/"
    exit 1
fi

echo "📋 Node.js version: $(node --version)"
echo "📋 npm version: $(npm --version)"

# Install dependencies
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    echo "✅ Dependencies installed"
else
    echo "📦 Checking for updated dependencies..."
    npm install
    echo "✅ Dependencies up to date"
fi

# Check if backend services are running
echo "🔍 Checking backend services..."

if curl -s "http://localhost:${API_PORT:-8000}/health" >/dev/null 2>&1; then
    echo "✅ API server is running at http://localhost:${API_PORT:-8000}"
else
    echo "⚠️  API server not responding at http://localhost:${API_PORT:-8000}"
    echo "   Frontend will start but API calls will fail"
fi

if curl -s "http://localhost:${AGENT_PORT:-8001}/health" >/dev/null 2>&1; then
    echo "✅ Agents server is running at http://localhost:${AGENT_PORT:-8001}"
else
    echo "⚠️  Agents server not responding at http://localhost:${AGENT_PORT:-8001}"
    echo "   AI agents may not work properly"
fi

echo ""
echo "🚀 Starting development server..."
echo "   URL: http://localhost:${WEB_PORT:-3000}"
echo "   Press Ctrl+C to stop"
echo ""

# Start the development server
npm run dev