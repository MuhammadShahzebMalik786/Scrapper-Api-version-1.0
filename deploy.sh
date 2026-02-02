#!/bin/bash

# Deploy to VPS Script
VPS_USER="duseca"
VPS_IP="65.109.145.43"
VPS_HOST="$VPS_USER@$VPS_IP"

echo "Deploying Mobile Scraper to VPS: $VPS_HOST"
echo "============================================"

# Upload files to VPS
echo "Uploading files..."
rsync -avz --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='venv' --exclude='test_venv' . $VPS_HOST:/tmp/mobile-scraper/

# Run setup on VPS
echo "Running setup on VPS..."
ssh $VPS_HOST << 'EOF'
cd /tmp/mobile-scraper
chmod +x setup-vps.sh manage.sh
sudo ./setup-vps.sh
EOF

echo ""
echo "Deployment Complete!"
echo "==================="
echo "Main API: http://$VPS_IP"
echo "Database API: http://$VPS_IP/api/"
echo ""
echo "SSH to VPS: ssh $VPS_HOST"
echo "Check status: ssh $VPS_HOST 'cd /opt/mobile-scraper && ./manage.sh status'"
