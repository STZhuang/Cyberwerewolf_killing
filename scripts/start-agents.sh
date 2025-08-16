#!/bin/bash

# Start Agno Agents Server for Local Development

set -e

echo "🤖 Starting Cyber Werewolves Agents Server"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "apps/agents/main.py" ]; then
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

# Check if API server is running
echo "🔍 Checking API server..."
if ! curl -s "http://localhost:${API_PORT:-8000}/health" >/dev/null 2>&1; then
    echo "⚠️  API server not responding at http://localhost:${API_PORT:-8000}"
    echo "   The agents service will start but may not work properly"
    echo "   Start API server first: ./scripts/start-api.sh"
else
    echo "✅ API server is running"
fi

# Navigate to Agents directory
cd apps/agents

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

# Check API keys
echo "🔑 Checking API keys..."
if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "sk-your-openai-api-key-here" ]; then
    echo "⚠️  OPENAI_API_KEY not configured"
    echo "   Agents may not work properly without API keys"
fi

if [ -n "$OPENAI_API_KEY" ] && [ "$OPENAI_API_KEY" != "sk-your-openai-api-key-here" ]; then
    echo "✅ OpenAI API key configured"
fi

if [ -n "$ANTHROPIC_API_KEY" ] && [ "$ANTHROPIC_API_KEY" != "sk-ant-your-anthropic-key-here" ]; then
    echo "✅ Anthropic API key configured"
fi

echo ""
echo "🚀 Starting Agents server..."
echo "   URL: http://localhost:${AGENT_PORT:-8001}"
echo "   Press Ctrl+C to stop"
echo ""

# Start the Agents server
uvicorn main:app \
  --host 0.0.0.0 \
  --port ${AGENT_PORT:-8001} \
  --reload \
  --reload-exclude "*.pyc" \
  --reload-exclude "__pycache__" \
  --log-level ${LOG_LEVEL:-info}