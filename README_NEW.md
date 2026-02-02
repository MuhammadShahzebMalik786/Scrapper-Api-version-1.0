# Mobile.de Scraper - Production Ready

Production-ready headless web scraper for mobile.de (German car marketplace) with Docker support and RESTful API.

## Features

- **Production Ready**: Docker containerization with health checks
- **Unified API**: Single API with all endpoints (cars, search, stats, scraping)
- **Auto Scheduling**: Background worker runs every 6 hours
- **Database**: PostgreSQL with proper connection pooling
- **Monitoring**: Comprehensive logging and health checks
- **Configuration**: Environment-based configuration management

## Quick Start

### Docker Deployment (Recommended)

```bash
# Start all services
./manage.sh start

# Check status
./manage.sh status

# View logs
./manage.sh logs

# Test API
./manage.sh test

# Trigger manual scraping
./manage.sh scrape
```

### Manual Setup

```bash
# Install dependencies
pip install -r requirements_new.txt

# Set environment variables
export DB_URL='postgresql://user:pass@localhost/db'
export API_TOKEN='your-secure-token'

# Run API
python api.py

# Run worker (separate terminal)
python worker.py
```

## API Endpoints

### Main API (Port 8080)
- `GET /` - Health check with database status
- `GET /health` - Simple health check
- `GET /stats` - Database statistics
- `POST /populate` - Trigger scraping (requires auth)
- `GET /status` - Scraper status

### Car Data (requires auth)
- `GET /cars` - List cars with pagination
- `GET /cars/{id}` - Get single car details
- `GET /search?q=term` - Search cars by title

## Configuration

Environment variables (see `.env` file):

```bash
# API Security
API_TOKEN=mobile-scraper-2026-secure-token

# Database
DB_URL=postgresql://scraper:scraper123@localhost:5432/mobile_scraper

# Scraper Settings
SCRAPER_DELAY=2
MAX_PAGES=5
HEADLESS_MODE=true
LOG_LEVEL=INFO
```

## Authentication

Protected endpoints require Bearer token:

```bash
curl -H "Authorization: Bearer mobile-scraper-2026-secure-token" \
     -X POST http://localhost:8080/populate
```

## Management Commands

```bash
./manage.sh start     # Start services
./manage.sh stop      # Stop services
./manage.sh restart   # Restart services
./manage.sh status    # Show status
./manage.sh logs      # View logs
./manage.sh test      # Test endpoints
./manage.sh scrape    # Manual scraping
./manage.sh build     # Rebuild images
./manage.sh clean     # Clean up
```

## Production Deployment

1. **Update configuration**:
   - Change `API_TOKEN` to a secure value
   - Update database credentials
   - Set appropriate `MAX_PAGES` limit

2. **Deploy**:
   ```bash
   docker-compose up -d
   ```

3. **Monitor**:
   ```bash
   docker-compose logs -f
   ```

## File Structure

```
├── config.py              # Configuration management
├── database.py            # Database models and connection
├── db_operations.py       # Database operations
├── api.py                 # Main API server
├── scraper.py             # Web scraper logic
├── worker.py              # Background scheduler
├── docker-compose.yml     # Docker services
├── Dockerfile             # Container definition
├── requirements_new.txt   # Python dependencies
├── manage.sh              # Management script
└── .env                   # Environment variables
```

## Legal Notice

Educational use only. Respect mobile.de's terms of service and robots.txt.
