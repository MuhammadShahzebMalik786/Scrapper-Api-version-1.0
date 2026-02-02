#!/usr/bin/env python3
"""
Unified Mobile.de Scraper - Production ready
Consolidates streaming and batch scraping functionality
"""

import asyncio
import logging
import os
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, AsyncGenerator

import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup

from config_manager import Config

logger = logging.getLogger(__name__)

# Try to enable database support
try:
    from db_operations import save_car_to_database
    DB_ENABLED = True
    logger.info("Database functionality enabled")
except ImportError:
    DB_ENABLED = False
    logger.warning("Database functionality disabled")


class MobileDeScraperConfig:
    """Scraper timeouts and settings"""
    CONSENT_TIMEOUT = 15
    PAGINATION_TIMEOUT = 10
    ELEMENT_TIMEOUT = 8
    PAGE_LOAD_TIMEOUT = 20


class MobileDeScraperUnified:
    """Unified scraper combining streaming and batch modes"""
    
    def __init__(self):
        self.driver = None
        self.config = Config()
    
    def setup_driver(self) -> Optional[object]:
        """Initialize optimized headless Chrome driver"""
        logger.info("Initializing Chrome driver...")
        
        options = Options()
        
        if self.config.HEADLESS_MODE:
            options.add_argument("--headless")
        
        # Production-ready options
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-logging")
        options.add_argument("--disable-sync")
        options.add_argument("--no-first-run")
        options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36")
        
        if self.config.CHROME_BINARY_PATH:
            options.binary_location = self.config.CHROME_BINARY_PATH
        
        try:
            self.driver = uc.Chrome(
                options=options,
                driver_executable_path=self.config.CHROMEDRIVER_PATH or None
            )
            logger.info("Chrome driver initialized")
            return self.driver
        except Exception as e:
            logger.error(f"Failed to init driver: {e}")
            return None
    
    def close_driver(self):
        """Safely close driver"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Driver closed")
            except Exception as e:
                logger.warning(f"Error closing driver: {e}")
            self.driver = None
    
    def accept_consent(self, timeout=MobileDeScraperConfig.CONSENT_TIMEOUT) -> bool:
        """Accept consent modal"""
        try:
            btn = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.mde-consent-accept-btn"))
            )
            btn.click()
            logger.info("Consent accepted")
            return True
        except TimeoutException:
            logger.debug("No consent modal")
            return False
        except Exception as e:
            logger.warning(f"Consent error: {e}")
            return False
    
    def next_page(self, timeout=MobileDeScraperConfig.PAGINATION_TIMEOUT) -> bool:
        """Click next page button"""
        try:
            btn = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-testid="pagination:next"]'))
            )
            
            if not btn.is_enabled():
                logger.info("Last page reached")
                return False
            
            self.driver.execute_script("arguments[0].scrollIntoView(true);", btn)
            time.sleep(0.5)
            btn.click()
            time.sleep(2)
            return True
        except Exception as e:
            logger.debug(f"Pagination complete: {e}")
            return False
    
    def extract_car(self, article_element) -> Optional[Dict]:
        """Extract single car from article HTML"""
        try:
            car = {}
            
            title = article_element.find('h2', class_='dNpqi')
            car['title'] = title.get_text(strip=True) if title else None
            
            price = article_element.find(attrs={'data-testid': 'vip-price-label'})
            if not price:
                price = article_element.find('div', class_='HBWcC')
            car['price'] = price.get_text(strip=True) if price else None
            
            mileage = article_element.find('span', string=re.compile(r'km'))
            car['mileage'] = mileage.get_text(strip=True) if mileage else None
            
            link = article_element.find('a', href=True)
            car['url'] = link['href'] if link else None
            
            return car if car.get('url') else None
        except Exception as e:
            logger.debug(f"Extract error: {e}")
            return None
    
    def scrape_page_batch(self) -> List[Dict]:
        """Scrape all cars from current page"""
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            articles = soup.find_all('article')
            cars = []
            
            for article in articles:
                car = self.extract_car(article)
                if car:
                    cars.append(car)
                    if DB_ENABLED:
                        try:
                            save_car_to_database(car)
                        except Exception as e:
                            logger.warning(f"DB save error: {e}")
            
            return cars
        except Exception as e:
            logger.error(f"Page scrape error: {e}")
            return []
    
    async def scrape_streaming(self, url: str, max_pages: Optional[int] = None) -> AsyncGenerator[Dict, None]:
        """
        Stream scrape with real-time progress yields
        Use for API endpoints with live updates
        """
        max_pages = max_pages or self.config.MAX_PAGES
        page_num = 0
        total_cars = 0
        
        try:
            if not self.setup_driver():
                yield {"error": "Driver init failed", "status": "error"}
                return
            
            logger.info(f"Starting stream scrape: {url}")
            self.driver.get(url)
            self.driver.set_page_load_timeout(MobileDeScraperConfig.PAGE_LOAD_TIMEOUT)
            time.sleep(2)
            self.accept_consent()
            
            while page_num < max_pages:
                try:
                    cars = self.scrape_page_batch()
                    total_cars += len(cars)
                    
                    yield {
                        "status": "scraping",
                        "page": page_num + 1,
                        "cars_found": len(cars),
                        "total_cars": total_cars,
                        "cars": cars
                    }
                    
                    if not self.next_page():
                        logger.info("Last page reached")
                        break
                    
                    page_num += 1
                    time.sleep(self.config.SCRAPER_DELAY)
                    
                except Exception as e:
                    logger.error(f"Page {page_num + 1} error: {e}")
                    yield {"status": "error", "page": page_num + 1, "error": str(e)}
                    break
            
            yield {
                "status": "completed",
                "total_pages": page_num + 1,
                "total_cars": total_cars,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield {"status": "error", "error": str(e)}
        finally:
            self.close_driver()
    
    def scrape_batch(self, url: str, max_pages: Optional[int] = None) -> Dict:
        """
        Batch scrape - returns all at once
        Use for background jobs
        """
        max_pages = max_pages or self.config.MAX_PAGES
        all_cars = []
        page_num = 0
        
        try:
            if not self.setup_driver():
                return {"status": "error", "error": "Driver init failed"}
            
            logger.info(f"Starting batch scrape: {url}")
            self.driver.get(url)
            self.driver.set_page_load_timeout(MobileDeScraperConfig.PAGE_LOAD_TIMEOUT)
            time.sleep(2)
            self.accept_consent()
            
            while page_num < max_pages:
                try:
                    cars = self.scrape_page_batch()
                    all_cars.extend(cars)
                    page_num += 1
                    
                    if not self.next_page():
                        break
                    
                    time.sleep(self.config.SCRAPER_DELAY)
                except Exception as e:
                    logger.error(f"Page {page_num + 1} error: {e}")
                    break
            
            return {
                "status": "completed",
                "pages_scraped": page_num,
                "total_cars": len(all_cars),
                "cars": all_cars,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Batch error: {e}")
            return {"status": "error", "error": str(e)}
        finally:
            self.close_driver()


# Convenience functions for backward compatibility
def scrape_batch(url: str = "https://www.mobile.de", max_pages: Optional[int] = None) -> Dict:
    """Batch scraper entry point"""
    scraper = MobileDeScraperUnified()
    return scraper.scrape_batch(url, max_pages)


async def scrape_streaming(url: str = "https://www.mobile.de", max_pages: Optional[int] = None) -> AsyncGenerator[Dict, None]:
    """Streaming scraper entry point"""
    scraper = MobileDeScraperUnified()
    async for event in scraper.scrape_streaming(url, max_pages):
        yield event


def main():
    """Default CLI entry point"""
    result = scrape_batch()
    logger.info(f"Scrape result: {result}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "stream":
        asyncio.run(scrape_streaming())
    else:
        main()
