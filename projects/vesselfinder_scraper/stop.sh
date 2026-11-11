#!/usr/bin/env bash
# ==============================================================================
# 🛑 VesselFinder Microservice Stop Script
# ==============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

PORT="${PORT:-8088}"

echo "🛑 Stopping VesselFinder Microservice..."

# 1. Stop Docker container if running
if command -v docker >/dev/null 2>&1 && docker compose ps -q 2>/dev/null | grep -q .; then
  echo "🐳 Stopping Docker container..."
  docker compose down
fi

# 2. Kill any native process listening on target port
PIDS=$(lsof -ti :"$PORT" 2>/dev/null || true)
if [ -n "$PIDS" ]; then
  echo "🔪 Terminating native process on port $PORT (PID: $PIDS)..."
  kill -9 $PIDS 2>/dev/null || true
fi

echo "✅ VesselFinder Microservice stopped successfully."

