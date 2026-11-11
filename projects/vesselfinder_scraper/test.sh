#!/usr/bin/env bash
# ==============================================================================
# 🧪 VesselFinder Microservice Production Health & API Verification Suite
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

PORT="${PORT:-8088}"
BASE="http://localhost:$PORT"

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "========================================================================"
echo "🧪 Running VesselFinder Production Microservice Health Checks"
echo "   Target: $BASE"
echo "========================================================================"

check_endpoint() {
  local name="$1"
  local url="$2"
  local expected_code="${3:-200}"

  printf "  • Testing %-35s " "$name..."
  status=$(curl -s -o /dev/null -w "%{http_code}" "$url")
  if [ "$status" -eq "$expected_code" ]; then
    printf "${GREEN}PASS (HTTP %s)${NC}\n" "$status"
  else
    printf "${RED}FAIL (Expected %s, Got %s)${NC}\n" "$expected_code" "$status"
    return 1
  fi
}

check_endpoint "Service Health (/health)" "$BASE/health"
check_endpoint "Swagger Docs (/docs)" "$BASE/docs"
check_endpoint "Live Radar Cache (/api/radar)" "$BASE/api/radar"
check_endpoint "Patrol & Navy Fleet (/api/patrol)" "$BASE/api/patrol"
check_endpoint "Fishing Vessels (/api/fishing)" "$BASE/api/fishing"
check_endpoint "Photo Gallery Stats (/api/photos/stats)" "$BASE/api/photos/stats"
check_endpoint "Vessel Photos Array (/api/vessel/567002940/photos)" "$BASE/api/vessel/567002940/photos"
check_endpoint "HD Photo Stream (/api/vessel/567002940/photo?index=1)" "$BASE/api/vessel/567002940/photo?index=1"
check_endpoint "Static Image Asset (/data/images/the_blue_dolphin_567002940_1.jpg)" "$BASE/data/images/the_blue_dolphin_567002940_1.jpg"
check_endpoint "Thailand Ports (/api/ports?country=th)" "$BASE/api/ports?country=th"

echo "========================================================================"
echo -e "${GREEN}🎉 ALL PRODUCTION API ENDPOINTS VERIFIED & 100% OPERATIONAL!${NC}"
echo "========================================================================"

