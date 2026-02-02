#!/usr/bin/env python3

import os
import time
import schedule
import logging
from datetime import datetime
from mobile_scraper_linux_headless import main as run_scraper

# Create logs directory if it doesn't exist
log_dir = '/opt/mobile-scraper/logs' if os.path.exists('/opt/mobile-scraper') else './logs'
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{log_dir}/worker.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def scraper_job():
    try:
        logger.info("Starting scheduled scraper job")
        run_scraper()
        logger.info("Scheduled scraper job completed")
    except Exception as e:
        logger.error(f"Scheduled scraper job failed: {e}")

def main():
    logger.info("Worker started - scheduling scraper every 6 hours")
    schedule.every(6).hours.do(scraper_job)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
