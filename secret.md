# Mobile.de Scraper - Complete Command Reference & Secrets

## 🔐 API Token
```
API_TOKEN=mobile-scraper-2026-secure-token
```

## 🚀 Quick Start Commands

### Docker Management
```bash
# Start all services
./manage.sh start

# Stop all services
./manage.sh stop

# Restart services
./manage.sh restart

# Check status
./manage.sh status

# View logs
./manage.sh logs
./manage.sh logs app
./manage.sh logs worker
./manage.sh logs db-api

# Test APIs
./manage.sh test

# Trigger scraping
./manage.sh scrape

# Build images
./manage.sh build

# Clean everything
./manage.sh clean
```

### Manual Docker Commands
```bash
# Start with build
docker-compose up --build -d

# View all logs
docker-compose logs -f

# Scale services
docker-compose up -d --scale worker=2

# Execute commands in container
docker-compose exec app bash
docker-compose exec db psql -U scraper -d mobile_scraper
```

## 🌐 API Endpoints

### Main API (Port 8000)
```bash
# Health check (no auth)
curl http://localhost:8000/health

# System status (no auth)
curl http://localhost:8000/

# Scraper status (no auth)
curl http://localhost:8000/status

# Start scraping (requires token)
curl -X POST -H "Authorization: Bearer mobile-scraper-2026-secure-token" \
  http://localhost:8000/populate
```

### Database API (Port 8001)
```bash
# List cars
curl -H "Authorization: Bearer mobile-scraper-2026-secure-token" \
  "http://localhost:8001/cars?skip=0&limit=10"

# Get specific car
curl -H "Authorization: Bearer mobile-scraper-2026-secure-token" \
  http://localhost:8001/cars/1

# Database stats
curl -H "Authorization: Bearer mobile-scraper-2026-secure-token" \
  http://localhost:8001/stats

# Search cars
curl -H "Authorization: Bearer mobile-scraper-2026-secure-token" \
  "http://localhost:8001/search?q=BMW&limit=5"
```

### Nginx Proxy (Port 8080)
```bash
# Access via proxy
curl http://localhost:8080/health
curl http://localhost:8080/api/cars
```

## 🗄️ Database Commands

### PostgreSQL Access
```bash
# Connect to database
docker-compose exec db psql -U scraper -d mobile_scraper

# Database queries
SELECT COUNT(*) FROM cars;
SELECT * FROM cars LIMIT 5;
SELECT DISTINCT fuel_type FROM cars;
SELECT price, location FROM cars WHERE price LIKE '%€%';
```

### Database Backup/Restore
```bash
# Backup
docker-compose exec db pg_dump -U scraper mobile_scraper > backup.sql

# Restore
docker-compose exec -T db psql -U scraper mobile_scraper < backup.sql
```

## 🔧 Environment Variables

### Production Settings
```bash
export DB_URL='postgresql://user:pass@host:5432/db'
export API_TOKEN='your-secure-token-here'
```

### Development Settings
```bash
export DB_URL='sqlite:///mobile_scraper.db'
export API_TOKEN='mobile-scraper-2026-secure-token'
```

## 📊 Monitoring Commands

### Service Health
```bash
# Check all services
docker-compose ps

# Check specific service
docker-compose ps app

# Service logs
docker-compose logs --tail=50 app
docker-compose logs --tail=50 worker
docker-compose logs --tail=50 db-api

# Follow logs in real-time
docker-compose logs -f app
```

### System Resources
```bash
# Container stats
docker stats

# Disk usage
docker system df

# Network info
docker network ls
docker network inspect test-for-now_default
```

## 🚨 Troubleshooting Commands

### Service Issues
```bash
# Restart specific service
docker-compose restart app
docker-compose restart worker
docker-compose restart db

# Rebuild and restart
docker-compose down
docker-compose up --build -d

# Check service health
curl http://localhost:8000/health
curl http://localhost:8001/
```

### Database Issues
```bash
# Check database connection
docker-compose exec db pg_isready -U scraper

# Reset database
docker-compose down -v
docker-compose up -d db
# Wait for db to start
docker-compose up -d
```

### Chrome/Scraper Issues
```bash
# Check Chrome in container
docker-compose exec app google-chrome --version

# Test scraper manually
docker-compose exec app python3 mobile_scraper_linux_headless.py

# Check logs for errors
docker-compose logs app | grep -i error
```

## 🔒 Security Commands

### Token Management
```bash
# Generate new token
openssl rand -hex 32

# Update token in environment
export API_TOKEN='new-token-here'
docker-compose down
docker-compose up -d
```

### SSL/HTTPS (Production)
```bash
# Generate SSL certificate
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365

# Update nginx config for HTTPS
# Add SSL configuration to nginx.conf
```

## 📈 Performance Optimization

### Database Optimization
```sql
-- Create indexes for better performance
CREATE INDEX idx_cars_price ON cars(price);
CREATE INDEX idx_cars_location ON cars(location);
CREATE INDEX idx_cars_fuel_type ON cars(fuel_type);
CREATE INDEX idx_cars_created_at ON cars(created_at);
```

### Container Optimization
```bash
# Limit container resources
docker-compose up -d --scale worker=1
docker update --memory=512m --cpus=0.5 container_name
```

## 🌍 Production Deployment

### VPS Setup
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone and setup
git clone <repository>
cd mobile-scraper
chmod +x manage.sh
./manage.sh start
```

### Production Environment
```bash
# Set production variables
export DB_URL='postgresql://prod_user:secure_pass@localhost:5432/mobile_scraper_prod'
export API_TOKEN='super-secure-production-token-2026'

# Update docker-compose for production
# Change nginx port to 80
# Add SSL certificates
# Set up proper logging
```

## 📝 Maintenance Commands

### Log Management
```bash
# Rotate logs
docker-compose exec app logrotate /etc/logrotate.conf

# Clear old logs
docker-compose exec app find /app/logs -name "*.log" -mtime +7 -delete

# Archive logs
tar -czf logs-$(date +%Y%m%d).tar.gz logs/
```

### Data Management
```bash
# Export data
docker-compose exec db pg_dump -U scraper mobile_scraper > export-$(date +%Y%m%d).sql

# Clean old data
docker-compose exec db psql -U scraper -d mobile_scraper -c "DELETE FROM cars WHERE created_at < NOW() - INTERVAL '30 days';"
```

## 🔍 Advanced Usage

### Custom Scraping
```bash
# Run scraper with custom parameters
docker-compose exec app python3 -c "
from mobile_scraper_linux_headless import main
main(max_pages=5, delay=2)
"
```

### API Testing
```bash
# Load testing
for i in {1..100}; do
  curl -s -H "Authorization: Bearer mobile-scraper-2026-secure-token" \
    http://localhost:8000/status &
done
wait
```

### Data Analysis
```sql
-- Top locations
SELECT location, COUNT(*) as count FROM cars GROUP BY location ORDER BY count DESC LIMIT 10;

-- Price analysis
SELECT AVG(CAST(REPLACE(REPLACE(price, '€', ''), '.', '') AS INTEGER)) as avg_price FROM cars WHERE price LIKE '%€%';

-- Daily scraping stats
SELECT DATE(created_at) as date, COUNT(*) as cars_scraped FROM cars GROUP BY DATE(created_at) ORDER BY date DESC;
```

---

## ⚠️ Important Notes

1. **Always use HTTPS in production**
2. **Change default API token before deployment**
3. **Set up proper database backups**
4. **Monitor disk space and logs**
5. **Use strong passwords for database**
6. **Keep Docker images updated**
7. **Set up monitoring and alerts**

## 🆘 Emergency Commands

```bash
# Stop everything immediately
docker-compose kill

# Remove all containers and data
docker-compose down -v
docker system prune -a -f

# Restore from backup
docker-compose up -d db
docker-compose exec -T db psql -U scraper mobile_scraper < backup.sql
docker-compose up -d
```
