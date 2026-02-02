# Quick Setup Guide

## 📋 Pre-requisites

- Docker & Docker Compose installed
- Git (optional)
- Bash shell (Linux/Mac) or PowerShell (Windows)

## 🚀 5-Minute Setup

### 1. Clone/Download Project
```bash
cd /path/to/mobile-scraper
```

### 2. Create Configuration
```bash
cp .env.example .env

# Edit .env - IMPORTANT settings:
# - API_TOKEN: Set a strong token
# - DB_PASSWORD: Set a strong database password
# - ENVIRONMENT: Set to 'production' if deploying
nano .env
```

### 3. Make Script Executable
```bash
chmod +x deploy.sh
```

### 4. Start Services
```bash
./deploy.sh start
```

### 5. Verify It Works
```bash
# Check status
./deploy.sh status

# Test API
./deploy.sh test-api

# View logs
./deploy.sh logs app
```

## 🔗 Access API

**Base URL**: `http://localhost:8000`

**Get Status**
```bash
curl http://localhost:8000/health
```

**Start Scraper**
```bash
curl -X POST -H "Authorization: Bearer YOUR_API_TOKEN" \
  http://localhost:8000/populate
```

## 📚 Common Commands

```bash
./deploy.sh start              # Start all
./deploy.sh stop               # Stop all
./deploy.sh status             # Check status
./deploy.sh logs app           # View logs
./deploy.sh test-scraper       # Test scraper
./deploy.sh backup             # Backup data
./deploy.sh help               # Show all commands
```

## 🛠️ Troubleshooting

**API not responding?**
```bash
./deploy.sh logs app
# Check if port 8000 is in use
```

**Database connection failed?**
```bash
./deploy.sh logs db
./deploy.sh db-shell  # Access PostgreSQL
```

**Want to reset everything?**
```bash
./deploy.sh clean
./deploy.sh start
```

## 📖 For More Information

- See `README.md` for full documentation
- See `CONSOLIDATION_REPORT.md` for changes made
- Check `.env.example` for all configuration options

---

**Now you're ready to scrape mobile.de!** 🚗
