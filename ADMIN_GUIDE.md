# Mobile.de Scraper - Complete Admin Guide

**CONFIDENTIAL - ADMIN ONLY**  
Complete deployment and management instructions for VPS owner/administrator.

---

## 🚀 Quick Start Deployment

### 1. Initial VPS Setup
```bash
# Connect to your VPS
ssh your-username@your-vps-ip

# Clone the repository
git clone https://github.com/MuhammadShahzebMalik786/test-for-now.git
cd test-for-now

# Make scripts executable
chmod +x setup-vps.sh fix-vps.sh manage.sh

# Run initial setup
sudo ./setup-vps.sh
```

### 2. Fix Common Issues (if setup fails)
```bash
sudo ./fix-vps.sh
```

---

## 📡 API Access Points

### Your VPS IP: `65.109.145.43`

**Main API (Port 8000):**
- Health Check: `http://65.109.145.43:8000/health`
- Status: `http://65.109.145.43:8000/`
- Start Scraping: `http://65.109.145.43:8000/populate` (requires auth)

**Database API (Port 8001):**
- Stats: `http://65.109.145.43:8001/stats` (no auth required)
- List Cars: `http://65.109.145.43:8001/cars` (requires auth)
- Search: `http://65.109.145.43:8001/search?q=BMW` (requires auth)

### Database API Authentication Examples:
```bash
# Get database stats (no auth needed)
curl http://65.109.145.43:8001/stats

# Get cars list (with auth)
curl -H "Authorization: Bearer mobile-scraper-2026-secure-token" \
     http://65.109.145.43:8001/cars?limit=10

# Search cars (with auth)
curl -H "Authorization: Bearer mobile-scraper-2026-secure-token" \
     "http://65.109.145.43:8001/search?q=BMW&limit=5"

# Get single car (with auth)
curl -H "Authorization: Bearer mobile-scraper-2026-secure-token" \
     http://65.109.145.43:8001/cars/1
```

---

## 🔐 Authentication

**API Token:** `mobile-scraper-2026-secure-token`

### Usage Examples:
```bash
# Test APIs without authentication
curl http://65.109.145.43:8000/health
curl http://65.109.145.43:8001/stats

# Start scraping (requires auth)
curl -H "Authorization: Bearer mobile-scraper-2026-secure-token" \
     -X POST http://65.109.145.43:8000/populate

# Get cars list (requires auth)
curl -H "Authorization: Bearer mobile-scraper-2026-secure-token" \
     http://65.109.145.43:8001/cars?limit=10

# Search cars (requires auth)
curl -H "Authorization: Bearer mobile-scraper-2026-secure-token" \
     "http://65.109.145.43:8001/search?q=BMW&limit=5"

# Get single car by ID (requires auth)
curl -H "Authorization: Bearer mobile-scraper-2026-secure-token" \
     http://65.109.145.43:8001/cars/1
```

---

## 🛠️ Service Management

### Check Service Status
```bash
# Check all services
sudo systemctl status mobile-scraper-api mobile-scraper-db-api mobile-scraper-worker

# Check individual services
sudo systemctl status mobile-scraper-api
sudo systemctl status mobile-scraper-db-api
sudo systemctl status mobile-scraper-worker
sudo systemctl status postgresql
```

### Start/Stop/Restart Services
```bash
# Start all services
sudo systemctl start mobile-scraper-api mobile-scraper-db-api mobile-scraper-worker

# Stop all services
sudo systemctl stop mobile-scraper-api mobile-scraper-db-api mobile-scraper-worker

# Restart all services
sudo systemctl restart mobile-scraper-api mobile-scraper-db-api mobile-scraper-worker

# Enable auto-start on boot
sudo systemctl enable mobile-scraper-api mobile-scraper-db-api mobile-scraper-worker
```

### View Logs
```bash
# Live logs for main API
sudo journalctl -u mobile-scraper-api -f

# Live logs for database API
sudo journalctl -u mobile-scraper-db-api -f

# Live logs for worker
sudo journalctl -u mobile-scraper-worker -f

# View recent logs
sudo journalctl -u mobile-scraper-api --since "1 hour ago"
```

---

## 🗄️ Database Management

### PostgreSQL Access
```bash
# Connect to database
sudo -u postgres psql mobile_scraper

# Database credentials
# Username: scraper
# Password: scraper123
# Database: mobile_scraper
```

### Database Commands
```sql
-- Check total cars
SELECT COUNT(*) FROM cars;

-- View recent cars
SELECT id, url_title, price, location FROM cars ORDER BY created_at DESC LIMIT 10;

-- Search cars
SELECT * FROM cars WHERE url_title ILIKE '%BMW%' LIMIT 5;

-- Delete old data (if needed)
DELETE FROM cars WHERE created_at < NOW() - INTERVAL '30 days';
```

### Database Backup
```bash
# Create backup
sudo -u postgres pg_dump mobile_scraper > backup_$(date +%Y%m%d).sql

# Restore backup
sudo -u postgres psql mobile_scraper < backup_20260202.sql
```

---

## 📊 Monitoring & Maintenance

### Check System Resources
```bash
# Check disk space
df -h

# Check memory usage
free -h

# Check CPU usage
top

# Check running processes
ps aux | grep python3
```

### Check Open Ports
```bash
# View all open ports
sudo netstat -tlnp

# Check specific ports
sudo netstat -tlnp | grep :8000
sudo netstat -tlnp | grep :8001
```

### Log Files Location
```bash
# Application logs
ls -la /opt/mobile-scraper/logs/

# System logs
sudo journalctl -u mobile-scraper-api --since today
```

---

## 🔧 Troubleshooting

### Common Issues & Solutions

**1. API Not Responding**
```bash
# Check if services are running
sudo systemctl status mobile-scraper-api

# Restart services
sudo systemctl restart mobile-scraper-api mobile-scraper-db-api

# Check logs for errors
sudo journalctl -u mobile-scraper-api -n 50
```

**2. Database Connection Issues**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Restart PostgreSQL
sudo systemctl restart postgresql

# Test database connection
sudo -u postgres psql -c "SELECT 1;"
```

**3. Scraper Not Working**
```bash
# Check worker service
sudo systemctl status mobile-scraper-worker

# Restart worker
sudo systemctl restart mobile-scraper-worker

# Manual scraper test
cd /opt/mobile-scraper
sudo -u scraper bash -c "source venv/bin/activate && python3 mobile_scraper_linux_headless.py"
```

**4. Port Already in Use**
```bash
# Find what's using the port
sudo netstat -tlnp | grep :8000

# Kill process if needed
sudo kill -9 PID_NUMBER
```

---

## 🔄 Updates & Maintenance

### Update Application
```bash
cd /opt/mobile-scraper
sudo git pull origin main
sudo systemctl restart mobile-scraper-api mobile-scraper-db-api mobile-scraper-worker
```

### Update System
```bash
sudo apt update && sudo apt upgrade -y
sudo reboot  # if kernel updates
```

### Clean Up Logs
```bash
# Clean old logs (older than 7 days)
sudo find /opt/mobile-scraper/logs/ -name "*.log" -mtime +7 -delete

# Clean system logs
sudo journalctl --vacuum-time=7d
```

---

## 🚨 Emergency Commands

### Complete Service Restart
```bash
sudo systemctl stop mobile-scraper-api mobile-scraper-db-api mobile-scraper-worker
sudo systemctl start postgresql
sleep 5
sudo systemctl start mobile-scraper-api mobile-scraper-db-api mobile-scraper-worker
```

### Reset Database (DANGER - Deletes All Data)
```bash
sudo -u postgres psql -c "DROP DATABASE mobile_scraper;"
sudo -u postgres psql -c "CREATE DATABASE mobile_scraper OWNER scraper;"
cd /opt/mobile-scraper
sudo -u scraper bash -c "source venv/bin/activate && python3 -c 'from database import init_database; init_database()'"
```

### Complete Reinstall
```bash
cd ~/test-for-now
sudo ./setup-vps.sh
```

---

## 📈 Performance Optimization

### Increase Worker Frequency
```bash
# Edit worker service
sudo nano /etc/systemd/system/mobile-scraper-worker.service

# Change schedule in worker.py
sudo nano /opt/mobile-scraper/worker.py
# Change: schedule.every(6).hours.do(scraper_job)
# To: schedule.every(3).hours.do(scraper_job)

sudo systemctl daemon-reload
sudo systemctl restart mobile-scraper-worker
```

### Database Optimization
```sql
-- Connect to database
sudo -u postgres psql mobile_scraper

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_cars_created_at ON cars(created_at);
CREATE INDEX IF NOT EXISTS idx_cars_price ON cars(price);
CREATE INDEX IF NOT EXISTS idx_cars_location ON cars(location);
```

---

## 🔒 Security Notes

- **API Token**: Change `mobile-scraper-2026-secure-token` in production
- **Database Password**: Change `scraper123` for production use
- **Firewall**: Only ports 22, 8000, 8001 should be open
- **SSL**: Consider adding HTTPS for production

### Change API Token
```bash
# Update environment variable
echo 'export API_TOKEN="your-new-secure-token"' >> ~/.bashrc
source ~/.bashrc

# Update systemd services
sudo systemctl edit mobile-scraper-api
# Add: Environment=API_TOKEN=your-new-secure-token

sudo systemctl daemon-reload
sudo systemctl restart mobile-scraper-api mobile-scraper-db-api
```

---

## 📞 Quick Reference

**Service Names:**
- `mobile-scraper-api` - Main API service
- `mobile-scraper-db-api` - Database API service  
- `mobile-scraper-worker` - Background scraper
- `postgresql` - Database service

**Important Paths:**
- Application: `/opt/mobile-scraper/`
- Logs: `/opt/mobile-scraper/logs/`
- Config: `/etc/systemd/system/mobile-scraper-*.service`

**Default Credentials:**
- DB User: `scraper`
- DB Password: `scraper123`
- DB Name: `mobile_scraper`
- API Token: `mobile-scraper-2026-secure-token`

---

*Last Updated: February 2, 2026*  
*Keep this document secure and confidential*
