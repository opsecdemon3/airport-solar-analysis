# Airport Solar Analyzer - Production Deployment Guide

A production-ready web application for analyzing rooftop solar potential near major US airports using Microsoft Building Footprints and NREL solar data.

## 🚀 Features

### Frontend (Next.js 14)
- **Interactive Map** - Visualize buildings with Leaflet
- **Dynamic Analysis** - Real-time solar calculations
- **Multiple Views** - Single airport, comparison, and aggregate analysis
- **Export Capabilities** - Download results as CSV
- **Responsive Design** - Mobile-friendly UI
- **Error Boundaries** - Graceful error handling
- **Suspense Boundaries** - Optimized loading states

### Backend (FastAPI)
- **High Performance** - <1 second response times with pre-computed caches
- **Health Checks** - `/health`, `/api/status`, `/api/ready` endpoints
- **Rate Limiting** - Sliding window algorithm (100 req/min default)
- **Structured Logging** - JSON logs with request tracking
- **Security Headers** - HSTS, XSS protection, CSP
- **Graceful Shutdown** - Signal handling for clean stops
- **Request Timing** - Performance monitoring headers
- **CORS Configuration** - Flexible origin management

### Production Infrastructure
- **Docker** - Multi-stage builds for optimization
- **Docker Compose** - Orchestrate all services
- **Nginx** - Reverse proxy with SSL/TLS
- **Automated Deployment** - One-command deployment scripts
- **Monitoring** - Request counting, uptime tracking
- **Observability** - Structured logs, health endpoints

## 📋 Prerequisites

- **Docker** >= 20.10
- **Docker Compose** >= 2.0
- **Node.js** >= 18 (for local development)
- **Python** >= 3.11 (for local development)
- **Data Files** - Microsoft Building Footprints GeoJSON files

## 🏗️ Project Structure

```
airport-solar-analysis/
├── api/                      # FastAPI backend
│   ├── main.py              # Main application with all endpoints
│   ├── config.py            # Configuration management
│   ├── logger.py            # Logging setup
│   ├── middleware.py        # Rate limiting, timing, security
│   ├── requirements.txt     # Python dependencies
│   ├── .env                 # Environment variables (local)
│   └── .env.example         # Environment template
├── web/                      # Next.js frontend
│   ├── src/
│   │   ├── app/             # App router pages
│   │   └── components/      # React components
│   ├── public/              # Static assets
│   ├── next.config.js       # Next.js configuration
│   ├── Dockerfile.prod      # Production Dockerfile
│   ├── .env.local           # Environment variables (local)
│   └── .env.example         # Environment template
├── data/                     # Data directory
│   ├── airports/            # Airport metadata
│   ├── buildings/           # Building footprints (GeoJSON)
│   └── airport_cache_v2/    # Pre-computed caches (JSON)
├── nginx/                    # Nginx configuration
│   ├── nginx.conf           # Main config
│   └── ssl/                 # SSL certificates
├── logs/                     # Application logs
├── Dockerfile               # Combined Dockerfile
├── docker-compose.yml       # Service orchestration
├── deploy.sh                # Automated deployment
├── prebuild_cache_v2.py     # Cache generation script
└── README_PRODUCTION.md     # This file
```

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd airport-solar-analysis

# Create required directories
mkdir -p logs data/airport_cache_v2 nginx/ssl
```

### 2. Prepare Data

```bash
# Download Microsoft Building Footprints (GeoJSON format)
# Place in data/buildings/ directory:
# - Arizona.geojson
# - California.geojson
# - Colorado.geojson
# - Florida.geojson
# - Georgia.geojson
# - Illinois.geojson
# - Texas.geojson

# Generate optimized caches
python3 -m venv venv
source venv/bin/activate
pip install -r api/requirements.txt
python prebuild_cache_v2.py
```

### 3. Configure Environment

```bash
# Backend configuration
cp api/.env.example api/.env
# Edit api/.env with your settings

# Frontend configuration
cp web/.env.example web/.env.local
# Edit web/.env.local with your settings
```

### 4. Deploy

```bash
# Development (API + Frontend only)
./deploy.sh dev

# Production (with Nginx reverse proxy)
./deploy.sh prod
```

## 🔧 Configuration

### Backend Environment Variables

```bash
# api/.env
API_HOST=0.0.0.0
API_PORT=8001
API_WORKERS=4
API_RELOAD=false

# CORS (comma-separated)
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Logging
LOG_LEVEL=INFO
LOG_FILE=../logs/api.log

# Performance
MAX_BUILDINGS_RETURN=500
CACHE_TTL=3600
```

### Frontend Environment Variables

```bash
# web/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_APP_NAME=Airport Solar Analyzer
NEXT_PUBLIC_ENABLE_EXPORT=true
NEXT_PUBLIC_ENABLE_COMPARE=true
NEXT_PUBLIC_ENABLE_AGGREGATE=true
```

## 📊 API Endpoints

### Health & Monitoring

- `GET /health` - Basic health check
- `GET /api/health` - API health check
- `GET /api/status` - Detailed status with metrics
- `GET /api/ready` - Readiness probe for K8s

### Data Endpoints

- `GET /api/airports` - List all airports
- `GET /api/buildings/{code}` - Get buildings for airport
- `GET /api/compare` - Compare multiple airports
- `GET /api/aggregate` - Aggregate statistics

### Documentation

- `GET /api/docs` - Interactive API documentation (Swagger)
- `GET /api/redoc` - Alternative documentation (ReDoc)

## 🔐 Security

### Implemented Features

- ✅ Rate limiting (sliding window)
- ✅ CORS configuration
- ✅ Security headers (HSTS, XSS, CSP)
- ✅ Request timing monitoring
- ✅ Structured logging
- ✅ Health checks
- ✅ Graceful shutdown

### SSL/TLS Setup

For production with HTTPS:

```bash
# Option 1: Self-signed certificate (development)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem

# Option 2: Let's Encrypt (production)
# Use certbot to generate certificates
# Place cert.pem and key.pem in nginx/ssl/

# Update nginx.conf to uncomment SSL certificate paths
```

## 🐳 Docker Commands

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f api
docker-compose logs -f frontend

# Stop services
docker-compose down

# Restart specific service
docker-compose restart api

# View status
docker-compose ps

# Execute command in container
docker-compose exec api python -c "print('Hello')"

# View resource usage
docker stats
```

## 📈 Monitoring & Observability

### Logs

```bash
# API logs (JSON format)
tail -f logs/api.log | jq

# Docker logs
docker-compose logs -f --tail=100

# Nginx logs (when using reverse proxy)
docker-compose exec nginx tail -f /var/log/nginx/access.log
```

### Metrics

Access `/api/status` for:
- Uptime
- Request count
- Data availability
- Configuration status

### Health Checks

```bash
# API health
curl http://localhost:8001/health

# Frontend health
curl http://localhost:3000

# Detailed status
curl http://localhost:8001/api/status | jq
```

## 🚀 Performance Optimization

### Current Performance

- **API Response Time**: <1 second for cached airports
- **Cache Hits**: Near 100% for pre-built caches
- **Concurrent Requests**: Supports 100+ req/min with rate limiting

### Optimization Tips

1. **Pre-build Caches**: Run `prebuild_cache_v2.py` for all airports
2. **Adjust Workers**: Set `API_WORKERS` based on CPU cores
3. **Enable Caching**: Ensure cache directory is mounted correctly
4. **Monitor Logs**: Check for slow queries
5. **CDN**: Use CDN for static assets in production

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to production
        run: ./deploy.sh prod
```

## 🛠️ Troubleshooting

### API not responding

```bash
# Check if container is running
docker-compose ps

# Check logs
docker-compose logs api

# Restart service
docker-compose restart api
```

### Frontend shows "Failed to load data"

```bash
# Check API connectivity
curl http://localhost:8001/api/airports

# Check CORS configuration
# Verify CORS_ORIGINS in api/.env

# Check browser console for errors
```

### Cache performance issues

```bash
# Verify cache exists
ls -lh data/airport_cache_v2/

# Regenerate cache
python prebuild_cache_v2.py

# Check cache directory mounting
docker-compose exec api ls -la /app/data/airport_cache_v2/
```

## 📦 Data Requirements

### Minimum Data (15 airports)

States needed for core functionality:
- Arizona, California, Colorado, Florida
- Georgia, Illinois, Texas

### Full Coverage (30 airports)

Additional states for complete coverage:
- Hawaii, Maryland, Massachusetts, Michigan
- Minnesota, Nevada, New Jersey, New York
- North Carolina, Ohio, Pennsylvania, Tennessee
- Virginia, Washington

Download from: [Microsoft Building Footprints](https://github.com/Microsoft/USBuildingFootprints)

## 🌐 Production Deployment

### Recommended Infrastructure

- **Cloud Provider**: AWS, GCP, Azure, DigitalOcean
- **Instance Size**: 2 vCPU, 4GB RAM minimum
- **Storage**: 100GB for data + logs
- **Network**: Load balancer with SSL termination

### Scaling Considerations

- Use container orchestration (Kubernetes, ECS)
- Add Redis for distributed caching
- Use CDN for static assets
- Implement auto-scaling based on CPU/memory
- Add database for user management (if needed)

## 📝 License & Attribution

Data sources:
- **Building Footprints**: Microsoft Building Footprints
- **Solar Data**: NREL 2023 ATB Capacity Factors

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📞 Support

For issues or questions:
- Check logs in `logs/api.log`
- Review `/api/status` endpoint
- Check Docker logs: `docker-compose logs`

---

**Built with ❤️ using FastAPI, Next.js, and modern DevOps practices**
