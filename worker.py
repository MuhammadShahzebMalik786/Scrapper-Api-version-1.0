#!/usr/bin/env python3
"""
Background scraper worker with scheduled jobs
Runs scraper at configured intervals
"""

import os
import time
import schedule
import logging
from datetime import datetime

from config_manager import Config

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
    """Run scheduled scraper batch job"""
    try:
        logger.info("Starting scheduled scraper job")
        
        from scraper_unified import scrape_batch
        result = scrape_batch()
        
        logger.info(f"Scraper completed: {result.get('total_cars', 0)} cars scraped")
    except Exception as e:
        logger.error(f"Scheduled scraper failed: {e}")


def main():
    """Main worker - runs scraper on schedule"""
    logger.info(f"Worker started - scheduling scraper every {Config.WORKER_INTERVAL_HOURS} hours")
    
    # Schedule the job
    schedule.every(Config.WORKER_INTERVAL_HOURS).hours.do(scraper_job)
    
    logger.info("Worker running, waiting for next scheduled job...")
    
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
