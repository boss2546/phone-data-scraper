#!/usr/bin/env bash
# ==============================================================================
# 🚢 VesselFinder Microservice Production Startup Script
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load .env if present
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

PORT="${PORT:-8088}"
MODE="${1:-auto}"

echo "========================================================================"
echo "🚢 Starting VesselFinder Live Maritime Radar Microservice"
echo "   Target Port : $PORT"
echo "   Mode        : $MODE"
echo "========================================================================"

if [ "$MODE" = "docker" ] || ([ "$MODE" = "auto" ] && command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1); then
  echo "🐳 Deploying via Docker Compose..."
  docker compose up -d --build
  echo "✅ Docker container is up and running in background!"
  echo "📖 API Docs: http://localhost:$PORT/docs"
  echo "🌐 Radar UI: http://localhost:$PORT/"
  exit 0
fi

echo "🐍 Starting with Native Python 3..."
# Check Python 3
if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ Error: python3 is not installed on this host."
  exit 1
fi

# Install dependencies if needed
if [ ! -d "venv" ]; then
  echo "📦 Creating virtual environment (venv)..."
  python3 -m venv venv
fi

source venv/bin/activate 2>/dev/null || true
echo "📦 Checking and installing dependencies..."
pip install -q -r requirements.txt

echo "🚀 Launching Microservice on port $PORT..."
python3 run.py api "$PORT"

