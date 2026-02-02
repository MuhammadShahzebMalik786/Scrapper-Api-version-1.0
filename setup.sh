#!/bin/bash

echo "Mobile.de Scraper Setup"
echo "======================"

# Update system
sudo apt update

# Install Chrome
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update
sudo apt install -y google-chrome-stable

# Install Python
sudo apt install -y python3 python3-pip python3-venv

# Create venv
python3 -m venv venv
source venv/bin/activate

# Install packages
pip install --upgrade pip
pip install -r requirements.txt

echo "Setup complete!"
echo "Run: source venv/bin/activate && python3 mobile_scraper_linux_headless.py"
