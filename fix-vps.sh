#!/bin/bash

echo "Fixing VPS deployment issues..."

# Fix virtual environment
cd /opt/mobile-scraper
sudo -u scraper python3 -m venv venv
sudo -u scraper ./venv/bin/pip install --upgrade pip
sudo -u scraper ./venv/bin/pip install -r requirements.txt

# Initialize database
sudo -u scraper bash -c "cd /opt/mobile-scraper && source venv/bin/activate && export DB_URL='postgresql://scraper:scraper123@localhost/mobile_scraper' && python3 -c 'from database import init_database; init_database()'"

# Fix nginx configuration
sudo systemctl stop nginx
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx config
sudo nginx -t

# Start services
sudo systemctl daemon-reload
sudo systemctl start nginx mobile-scraper-api mobile-scraper-db-api mobile-scraper-worker

# Check status
echo "Service Status:"
sudo systemctl status mobile-scraper-api --no-pager -l
sudo systemctl status nginx --no-pager -l

echo "Testing API..."
sleep 3
curl -s http://localhost:8080/health || echo "API not responding yet"

echo ""
echo "Setup complete!"
echo "Main API: http://65.109.145.43:8080"
echo "Database API: http://65.109.145.43:8080/api/"
echo ""
echo "Test commands:"
echo "curl http://65.109.145.43:8080/health"
echo "curl -H 'Authorization: Bearer mobile-scraper-2026-secure-token' -X POST http://65.109.145.43:8080/populate"
