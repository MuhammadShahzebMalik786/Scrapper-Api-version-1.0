#!/bin/bash

echo "Mobile.de Scraper - Production VPS Setup"
echo "========================================"

# Update system
echo "Updating system..."
sudo apt update && sudo apt upgrade -y

# Install Docker and Docker Compose
echo "Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

echo "Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create app directory
echo "Setting up application..."
sudo mkdir -p /opt/mobile-scraper
sudo cp -r . /opt/mobile-scraper/
sudo chown -R $USER:$USER /opt/mobile-scraper
cd /opt/mobile-scraper

# Make scripts executable
chmod +x manage.sh

# Create logs directory
mkdir -p logs

# Setup environment
echo "Setting up environment..."
if [ ! -f .env ]; then
    cp .env.example .env 2>/dev/null || echo "# Configure your environment variables here" > .env
fi

# Setup firewall
echo "Configuring firewall..."
if command -v ufw >/dev/null 2>&1; then
    sudo ufw allow 22/tcp
    sudo ufw allow 8080/tcp
    sudo ufw --force enable
else
    echo "UFW not available, skipping firewall configuration"
fi

# Start services
echo "Starting services..."
docker-compose up -d

# Wait for services to start
echo "Waiting for services to start..."
sleep 30

# Test the deployment
echo "Testing deployment..."
./manage.sh test

echo ""
echo "VPS Setup Complete!"
echo "==================="
echo "API URL: http://$(curl -s ifconfig.me 2>/dev/null || echo 'YOUR_VPS_IP'):8080"
echo ""
echo "Management commands:"
echo "  ./manage.sh status   - Check service status"
echo "  ./manage.sh logs     - View logs"
echo "  ./manage.sh test     - Test API endpoints"
echo "  ./manage.sh scrape   - Trigger manual scraping"
echo ""
echo "Important: Update the API_TOKEN in .env file for production!"
