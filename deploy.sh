#!/bin/bash
# Deployment script for Airport Solar Analyzer
# Usage: ./deploy.sh [dev|prod]

set -e

ENVIRONMENT=${1:-dev}

echo "======================================"
echo "Airport Solar Analyzer Deployment"
echo "Environment: $ENVIRONMENT"
echo "======================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites met${NC}"

# Create necessary directories
echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p logs data/airport_cache_v2 nginx/ssl

# Check for data
if [ ! -d "data/buildings" ] || [ -z "$(ls -A data/buildings)" ]; then
    echo -e "${YELLOW}⚠  Warning: Building data not found in data/buildings/${NC}"
    echo -e "${YELLOW}   The application will work but with limited airport coverage${NC}"
fi

# Check for cache
CACHE_COUNT=$(ls -1 data/airport_cache_v2/*.json 2>/dev/null | wc -l || echo 0)
if [ "$CACHE_COUNT" -eq 0 ]; then
    echo -e "${YELLOW}⚠  Warning: No cached airport data found${NC}"
    echo -e "${YELLOW}   Run 'python prebuild_cache_v2.py' to generate cache for better performance${NC}"
else
    echo -e "${GREEN}✓ Found $CACHE_COUNT cached airports${NC}"
fi

# Environment-specific setup
if [ "$ENVIRONMENT" == "prod" ]; then
    echo -e "${YELLOW}Setting up production environment...${NC}"
    
    # Check for SSL certificates
    if [ ! -f "nginx/ssl/cert.pem" ] || [ ! -f "nginx/ssl/key.pem" ]; then
        echo -e "${YELLOW}⚠  SSL certificates not found${NC}"
        echo -e "${YELLOW}   Generate SSL certificates for production:${NC}"
        echo -e "${YELLOW}   - Self-signed: openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout nginx/ssl/key.pem -out nginx/ssl/cert.pem${NC}"
        echo -e "${YELLOW}   - Let's Encrypt: Use certbot${NC}"
    fi
    
    # Stop and remove existing containers
    echo -e "${YELLOW}Stopping existing containers...${NC}"
    docker-compose --profile production down
    
    # Build images
    echo -e "${YELLOW}Building production images...${NC}"
    docker-compose build --no-cache
    
    # Start services
    echo -e "${YELLOW}Starting production services...${NC}"
    docker-compose --profile production up -d
    
else
    echo -e "${YELLOW}Setting up development environment...${NC}"
    
    # Stop and remove existing containers
    echo -e "${YELLOW}Stopping existing containers...${NC}"
    docker-compose down
    
    # Start services without nginx
    echo -e "${YELLOW}Starting development services...${NC}"
    docker-compose up -d api frontend
fi

# Wait for services to be healthy
echo -e "${YELLOW}Waiting for services to be ready...${NC}"
sleep 10

# Health checks
echo -e "${YELLOW}Performing health checks...${NC}"

API_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health || echo "000")
if [ "$API_HEALTH" == "200" ]; then
    echo -e "${GREEN}✓ API is healthy${NC}"
else
    echo -e "${RED}✗ API health check failed (HTTP $API_HEALTH)${NC}"
fi

FRONTEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 || echo "000")
if [ "$FRONTEND_HEALTH" == "200" ]; then
    echo -e "${GREEN}✓ Frontend is healthy${NC}"
else
    echo -e "${RED}✗ Frontend health check failed (HTTP $FRONTEND_HEALTH)${NC}"
fi

# Show status
echo ""
echo "======================================"
echo -e "${GREEN}Deployment Complete!${NC}"
echo "======================================"
echo ""
echo "Services running:"
echo "  - API:      http://localhost:8001"
echo "  - Frontend: http://localhost:3000"
if [ "$ENVIRONMENT" == "prod" ]; then
    echo "  - Nginx:    https://localhost"
fi
echo ""
echo "Useful commands:"
echo "  - View logs:    docker-compose logs -f"
echo "  - View status:  docker-compose ps"
echo "  - Stop:         docker-compose down"
echo "  - Restart:      docker-compose restart"
echo ""
echo "API Documentation:"
echo "  - Interactive:  http://localhost:8001/api/docs"
echo "  - ReDoc:        http://localhost:8001/api/redoc"
echo ""
