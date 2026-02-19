#!/bin/bash
# Airport Solar Analyzer - Monitoring Dashboard
# Real-time monitoring and health checks

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

API_URL="${API_URL:-http://localhost:8001}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"

echo "======================================"
echo "Airport Solar Analyzer - Monitor"
echo "======================================"
echo ""

# Function to check endpoint
check_endpoint() {
    local url=$1
    local name=$2
    local response=$(curl -s -o /dev/null -w "%{http_code}:%{time_total}" "$url" 2>/dev/null || echo "000:0")
    local code=$(echo $response | cut -d: -f1)
    local time=$(echo $response | cut -d: -f2)
    
    if [ "$code" == "200" ]; then
        echo -e "${GREEN}✓${NC} $name: ${GREEN}UP${NC} (${time}s)"
        return 0
    elif [ "$code" == "000" ]; then
        echo -e "${RED}✗${NC} $name: ${RED}DOWN${NC} (connection failed)"
        return 1
    else
        echo -e "${YELLOW}⚠${NC} $name: ${YELLOW}WARN${NC} (HTTP $code)"
        return 1
    fi
}

# Check services
echo -e "${BLUE}Service Health:${NC}"
check_endpoint "$API_URL/health" "API"
check_endpoint "$FRONTEND_URL" "Frontend"
echo ""

# Get detailed status
echo -e "${BLUE}API Status:${NC}"
status=$(curl -s "$API_URL/api/status" 2>/dev/null || echo '{}')

if [ "$status" != "{}" ]; then
    # Parse JSON without jq (basic parsing)
    uptime=$(echo "$status" | grep -o '"uptime_seconds":[0-9.]*' | cut -d: -f2)
    requests=$(echo "$status" | grep -o '"requests_handled":[0-9]*' | cut -d: -f2)
    cached=$(echo "$status" | grep -o '"cached_airports":[0-9]*' | cut -d: -f2)
    
    if [ -n "$uptime" ]; then
        uptime_min=$(echo "$uptime / 60" | bc 2>/dev/null || echo "0")
        echo "  Uptime: ${uptime_min} minutes"
    fi
    
    if [ -n "$requests" ]; then
        echo "  Requests: $requests"
    fi
    
    if [ -n "$cached" ]; then
        echo "  Cached Airports: $cached/30"
    fi
else
    echo -e "${RED}  Unable to fetch status${NC}"
fi

echo ""

# Test performance
echo -e "${BLUE}Performance Test:${NC}"
echo -n "  ATL query: "
atl_time=$(curl -s -o /dev/null -w "%{time_total}" "$API_URL/api/buildings/ATL?radius=5&min_size=1000" 2>/dev/null || echo "0")
if [ "$atl_time" != "0" ]; then
    echo "${atl_time}s"
else
    echo -e "${RED}FAILED${NC}"
fi

echo ""

# Docker status (if applicable)
if command -v docker &> /dev/null; then
    echo -e "${BLUE}Docker Containers:${NC}"
    if docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -q "airport-solar"; then
        docker ps --format "  {{.Names}}: {{.Status}}" | grep "airport-solar"
    else
        echo "  No Docker containers running"
    fi
    echo ""
fi

# Log summary
echo -e "${BLUE}Recent Activity:${NC}"
if [ -f "../logs/api.log" ]; then
    echo "  Last 5 API requests:"
    tail -5 ../logs/api.log | while read line; do
        # Extract key info from JSON log
        endpoint=$(echo "$line" | grep -o '"endpoint":"[^"]*"' | cut -d'"' -f4)
        status=$(echo "$line" | grep -o '"status_code":[0-9]*' | cut -d: -f2)
        duration=$(echo "$line" | grep -o '"duration_ms":[0-9.]*' | cut -d: -f2)
        
        if [ -n "$endpoint" ]; then
            echo "    $endpoint -> HTTP $status (${duration}ms)"
        fi
    done
else
    echo "  No log file found"
fi

echo ""
echo "======================================"
echo "Last updated: $(date)"
echo "======================================"
