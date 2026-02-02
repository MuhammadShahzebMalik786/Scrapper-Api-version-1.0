#!/usr/bin/env python3

import os
import time
import schedule
import logging
from datetime import datetime
from config import Config

# Setup logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{Config.LOG_DIR}/worker.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Create logs directory
os.makedirs(Config.LOG_DIR, exist_ok=True)

def scraper_job():
    """Run scheduled scraper job"""
    try:
        logger.info("Starting scheduled scraper job")
        
        # Import here to avoid circular imports
        from scraper import main as run_scraper
        run_scraper()
        
        logger.info("Scheduled scraper job completed successfully")
    except Exception as e:
        logger.error(f"Scheduled scraper job failed: {e}")

def main():
    """Main worker function"""
    logger.info("Worker started - scheduling scraper every 6 hours")
    
    # Schedule the job
    schedule.every(6).hours.do(scraper_job)
    
    # Run immediately on startup (optional)
    # scraper_job()
    
    # Keep the worker running
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Worker stopped by user")
            break
        except Exception as e:
            logger.error(f"Worker error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
