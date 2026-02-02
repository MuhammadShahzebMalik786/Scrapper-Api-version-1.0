#!/bin/bash

echo "Mobile.de Scraper - VPS Production Setup"
echo "========================================"

# Update system
echo "Updating system..."
sudo apt update && sudo apt upgrade -y

# Install Chrome
echo "Installing Chrome..."
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update
sudo apt install -y google-chrome-stable

# Install system dependencies
echo "Installing system dependencies..."
sudo apt install -y python3 python3-pip python3-venv nginx supervisor postgresql postgresql-contrib

# Create app user
echo "Creating app user..."
sudo useradd -m -s /bin/bash scraper || true
sudo usermod -aG www-data scraper

# Setup app directory
echo "Setting up application..."
sudo mkdir -p /opt/mobile-scraper
sudo cp -r . /opt/mobile-scraper/
sudo chown -R scraper:scraper /opt/mobile-scraper
cd /opt/mobile-scraper

# Create virtual environment
echo "Creating virtual environment..."
sudo -u scraper python3 -m venv /opt/mobile-scraper/venv
sudo -u scraper /opt/mobile-scraper/venv/bin/pip install --upgrade pip
sudo -u scraper /opt/mobile-scraper/venv/bin/pip install -r /opt/mobile-scraper/requirements.txt

# Setup PostgreSQL
echo "Setting up PostgreSQL..."
sudo -u postgres createuser scraper || true
sudo -u postgres createdb mobile_scraper -O scraper || true
sudo -u postgres psql -c "ALTER USER scraper PASSWORD 'scraper123';" || true

# Initialize database
echo "Initializing database..."
sudo -u scraper bash -c "cd /opt/mobile-scraper && source venv/bin/activate && export DB_URL='postgresql://scraper:scraper123@localhost/mobile_scraper' && python3 -c 'from database import init_database; init_database()'"

# Setup systemd services
echo "Setting up systemd services..."
sudo tee /etc/systemd/system/mobile-scraper-api.service > /dev/null << 'EOF'
[Unit]
Description=Mobile Scraper API
After=network.target postgresql.service

[Service]
Type=simple
User=scraper
WorkingDirectory=/opt/mobile-scraper
Environment=DB_URL=postgresql://scraper:scraper123@localhost/mobile_scraper
ExecStart=/opt/mobile-scraper/venv/bin/uvicorn api:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/mobile-scraper-db-api.service > /dev/null << 'EOF'
[Unit]
Description=Mobile Scraper Database API
After=network.target postgresql.service

[Service]
Type=simple
User=scraper
WorkingDirectory=/opt/mobile-scraper
Environment=DB_URL=postgresql://scraper:scraper123@localhost/mobile_scraper
ExecStart=/opt/mobile-scraper/venv/bin/uvicorn db_api:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/mobile-scraper-worker.service > /dev/null << 'EOF'
[Unit]
Description=Mobile Scraper Worker
After=network.target postgresql.service

[Service]
Type=simple
User=scraper
WorkingDirectory=/opt/mobile-scraper
Environment=DB_URL=postgresql://scraper:scraper123@localhost/mobile_scraper
ExecStart=/opt/mobile-scraper/venv/bin/python3 worker.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF

# Setup nginx
echo "Setting up nginx..."
sudo tee /etc/nginx/sites-available/mobile-scraper > /dev/null << 'EOF'
server {
    listen 8080;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /api/ {
        rewrite ^/api/(.*) /$1 break;
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/mobile-scraper /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t

# Setup log rotation
echo "Setting up log rotation..."
sudo tee /etc/logrotate.d/mobile-scraper > /dev/null << 'EOF'
/opt/mobile-scraper/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    copytruncate
}
EOF

# Create logs directory
sudo mkdir -p /opt/mobile-scraper/logs
sudo chown scraper:scraper /opt/mobile-scraper/logs

# Enable and start services
echo "Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable postgresql nginx mobile-scraper-api mobile-scraper-worker mobile-scraper-db-api
sudo systemctl start postgresql nginx mobile-scraper-api mobile-scraper-worker mobile-scraper-db-api

# Setup firewall (skip if ufw not available)
echo "Configuring firewall..."
if command -v ufw >/dev/null 2>&1; then
    sudo ufw allow 22/tcp
    sudo ufw allow 8080/tcp
    sudo ufw allow 443/tcp
    sudo ufw --force enable
else
    echo "UFW not available, skipping firewall configuration"
fi

echo ""
echo "VPS Setup Complete!"
echo "==================="
echo "Main API: http://$(curl -s ifconfig.me):8080"
echo "Database API: http://$(curl -s ifconfig.me):8080/api/"
echo "Status: systemctl status mobile-scraper-api mobile-scraper-db-api"
echo "Logs: journalctl -u mobile-scraper-api -f"
echo ""
echo "Test APIs:"
echo "curl http://localhost:8080/populate"
echo "curl http://localhost:8080/api/cars?limit=5"
