#!/usr/bin/env python3

import undetected_chromedriver as uc
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
import time
import csv
import os
import re
import logging
from urllib.parse import urlsplit, parse_qs
from datetime import datetime
from config import Config

# Setup logging
logger = logging.getLogger(__name__)

# Database imports
try:
    from db_operations import save_car_to_database
    DB_ENABLED = True
    logger.info("Database functionality enabled")
except ImportError as e:
    logger.warning(f"Database functionality disabled: {e}")
    DB_ENABLED = False

def setup_headless_driver():
    """Setup Chrome driver for Linux headless operation"""
    logger.info("Setting up headless Chrome driver...")
    
    options = Options()
    
    if Config.HEADLESS_MODE:
        options.add_argument("--headless")
    
    # Essential Chrome options for VPS/Docker
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-logging")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--remote-debugging-port=9222")
    
    # Set binary path if specified
    if Config.CHROME_BINARY_PATH:
        options.binary_location = Config.CHROME_BINARY_PATH
    
    try:
        # Try to use undetected-chromedriver without version specification
        driver = uc.Chrome(options=options, driver_executable_path=Config.CHROMEDRIVER_PATH)
        logger.info("Chrome driver initialized successfully")
        return driver
    except Exception as e:
        logger.error(f"Error initializing Chrome driver: {e}")
        return None

def accept_consent_cookie(driver, timeout=15):
    """Accept Mobile.de consent modal if present"""
    try:
        btn = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.mde-consent-accept-btn"))
        )
        btn.click()
        logger.info("Consent accepted")
        return True
    except TimeoutException:
        logger.info("No consent modal found")
        return False
    except Exception as e:
        logger.warning(f"Error accepting consent: {e}")
        return False

def click_continue_if_enabled(driver, timeout=10):
    """Click pagination Continue button if enabled"""
    locator = (By.CSS_SELECTOR, 'button[data-testid="pagination:next"]')
    
    try:
        btn = WebDriverWait(driver, timeout).until(EC.presence_of_element_located(locator))
        
        # Check if button is enabled
        disabled_attr = btn.get_attribute("disabled")
        aria_disabled = (btn.get_attribute("aria-disabled") or "").lower()
        enabled = btn.is_enabled() and (disabled_attr is None) and (aria_disabled != "true")

        if not enabled:
            logger.info("Continue button is disabled")
            return False

        # Scroll to button and click
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        time.sleep(1)
        
        try:
            btn.click()
        except Exception:
            driver.execute_script("arguments[0].click();", btn)

        logger.info("Continue button clicked")
        return True

    except TimeoutException:
        logger.info("Continue button not found")
        return False
    except Exception as e:
        logger.error(f"Error clicking continue: {e}")
        return False

def get_total_pages(driver, timeout=10):
    """Get total number of pages from pagination UI"""
    try:
        wait = WebDriverWait(driver, timeout)
        ratio_el = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="srp-pagination"] span.XUy1p'))
        )
        txt = (ratio_el.text or "").strip()
        m = re.search(r'(\d+)\s*/\s*(\d+)', txt)
        if m:
            total = int(m.group(2))
            logger.info(f"Total pages: {total}")
            return min(total, Config.MAX_PAGES)  # Respect MAX_PAGES limit
    except Exception as e:
        logger.warning(f"Could not determine total pages: {e}")
    
    return Config.MAX_PAGES  # Default fallback

def scrape_car_details(soup):
    """Extract key features from listing page"""
    car_details = {}
    try:
        key_map = {
            'mileage': 'mileage',
            'power': 'power',
            'fuel': 'fuel_type',
            'transmission': 'transmission',
            'firstRegistration': 'first_registration',
            'numberOfPreviousOwners': 'previous_owners',
            'bodyType': 'body_type',
            'seats': 'number_of_seats',
            'doorCount': 'door_count',
            'cubicCapacity': 'cubic_capacity',
            'driveType': 'drive_type',
        }

        def camel_to_snake(name):
            s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
            return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

        for item in soup.select('[data-testid^="vip-key-features-list-item"]'):
            dtid = item.get('data-testid', '')
            suffix = dtid.split('vip-key-features-list-item-')[-1]
            key = key_map.get(suffix, camel_to_snake(suffix))
            val_div = item.find('div', class_='geJSa')
            if not val_div:
                val_div = item.find('span')
            if val_div:
                value = val_div.get_text(strip=True)
                car_details[key] = value
        
        return car_details
    except Exception as e:
        logger.error(f"Error scraping key features: {e}")
        return {}

def scrape_technical_data_from_element(soup):
    """Extract technical data from listing page"""
    car_details = {}
    try:
        label_map = {
            'vehiclecondition': 'vehicle_condition',
            'fahrzeugzustand': 'vehicle_condition',
            'category': 'category',
            'fahrzeugtyp': 'category',
            'modelrange': 'model_range',
            'modellreihe': 'model_range',
            'trimline': 'trim_line',
            'ausstattungslinie': 'trim_line',
            'vehiclenumber': 'vehicle_number',
            'fahrzeugnummer': 'vehicle_number',
            'origin': 'origin',
            'herkunft': 'origin',
            'mileage': 'mileage',
            'kilometer': 'mileage',
            'cubiccapacity': 'cubic_capacity',
            'hubraum': 'cubic_capacity',
            'power': 'power',
            'leistung': 'power',
            'drivetype': 'drive_type',
            'antriebsart': 'drive_type',
            'fuel': 'fuel_type',
            'kraftstoff': 'fuel_type',
        }

        def normalize_label(label):
            return re.sub(r'[^a-z0-9]', '', label.lower())

        # Extract technical data from dt/dd pairs
        dts = soup.find_all('dt')
        for dt_tag in dts:
            dd_tag = dt_tag.find_next('dd')
            if dd_tag:
                raw_key = dt_tag.get_text(strip=True)
                norm_key = normalize_label(raw_key)
                key = label_map.get(norm_key, norm_key)
                value = dd_tag.get_text(strip=True)
                car_details[key] = value

        # Extract features
        features = []
        for feature_li in soup.find_all('li', class_='FtSYW'):
            feature_name = feature_li.get_text(strip=True)
            if feature_name:
                features.append(feature_name)
        
        if features:
            car_details['features'] = features

    except Exception as e:
        logger.error(f"Error extracting technical data: {e}")
    
    return car_details

def scrape_car_details_from_element(soup):
    """Extract high-level listing details"""
    car_details = {}
    try:
        # Title
        title = soup.find('h2', {'class': 'dNpqi'})
        car_details['title'] = title.get_text(strip=True) if title else 'Not found'

        # Additional info
        additional_info = soup.find('div', {'class': 'GOIOV fqe3L EevEz'})
        car_details['additional_info'] = additional_info.get_text(strip=True) if additional_info else 'Not found'

        # Price
        price = soup.find(attrs={'data-testid': 'vip-price-label'})
        if price:
            car_details['price'] = price.get_text(strip=True)
        else:
            price_div = soup.find('div', {'class': 'HBWcC'})
            car_details['price'] = price_div.get_text(strip=True) if price_div else 'Not found'

        # Dealer rating
        dealer_rating = soup.find('span', {'class': 'qHfAA'})
        car_details['dealer_rating'] = dealer_rating.get_text(strip=True) if dealer_rating else 'Not found'

        # Dealer
        dealer = soup.find('a', {'class': 'FWtU1 rqVIk lZcLh'})
        car_details['dealer'] = dealer.get_text(strip=True) if dealer else 'Not found'

        # Rating
        vip_rating = soup.find('div', {'class': '_u77E'})
        car_details['rating'] = vip_rating.get_text(strip=True) if vip_rating else 'Not found'

        # Negotiable
        negotiable_div = soup.find('div', {'class': 'HaBLt ZD2EM'})
        car_details['negotiable'] = negotiable_div.get_text(strip=True) if negotiable_div else 'Not found'

        # Monthly rate
        monthly_rate_block = soup.find(attrs={'data-testid': 'vip-financing-monthly-rate'})
        if monthly_rate_block:
            rate_link = monthly_rate_block.find('a', href=True)
            if rate_link:
                car_details['monthly_rate'] = rate_link.get_text(strip=True)
                car_details['monthly_rate_href'] = rate_link['href']
            else:
                car_details['monthly_rate'] = monthly_rate_block.get_text(strip=True)
        else:
            monthly_rate = soup.find('a', {'class': 'cCGm3'})
            if monthly_rate:
                car_details['monthly_rate'] = monthly_rate.get_text(strip=True)
                car_details['monthly_rate_href'] = monthly_rate.get('href', 'Not found')

        # Seller information
        seller_block = soup.find(attrs={'data-testid': 'seller-title-address'})
        if seller_block:
            seller_type_div = seller_block.find('div', {'class': 'QTTRi'})
            car_details['seller_type'] = seller_type_div.get_text(strip=True) if seller_type_div else 'Not found'

            loc_div = seller_block.find('div', {'class': 'olCKS'})
            car_details['location'] = loc_div.get_text(strip=True) if loc_div else 'Not found'

            phone_span = seller_block.find('span', attrs={'aria-live': 'polite'})
            car_details['phone'] = phone_span.get_text(strip=True) if phone_span else 'Not found'

        return car_details
    except Exception as e:
        logger.error(f"Error extracting car details: {e}")
        return {}

def extract_image_urls(html):
    """Extract image URLs from HTML"""
    try:
        soup = BeautifulSoup(html, "html.parser")
        urls = set()
        for img in soup.find_all("img"):
            src = img.get("src")
            if src and "mobile.de" in src:
                urls.add(src)
            srcset = img.get("srcset")
            if srcset:
                for part in srcset.split(","):
                    url = part.strip().split()[0]
                    if "mobile.de" in url:
                        urls.add(url)
        return list(urls)
    except Exception as e:
        logger.error(f"Error extracting images: {e}")
        return []

def save_car_data(car_details, output_file):
    """Save car data to CSV and database"""
    try:
        # Save to CSV
        write_car_details_to_csv(car_details, output_file)
        
        # Save to database if enabled
        if DB_ENABLED:
            save_car_to_database(car_details.copy())
    except Exception as e:
        logger.error(f"Error saving car data: {e}")

def write_car_details_to_csv(car_details, output_file):
    """Write car details to CSV file"""
    try:
        file_exists = os.path.isfile(output_file)
        with open(output_file, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if not file_exists or os.stat(output_file).st_size == 0:
                writer.writerow([
                    "URL", "Title", "Additional Info", "Price", "Dealer Rating", "Dealer",
                    "Seller Type", "Location", "Phone", "Rating", "Negotiable",
                    "Monthly Rate", "Monthly Rate Link", "Financing Link",
                    "Mileage", "Power", "Fuel Type", "Transmission", "First Registration",
                    "Vehicle Condition", "Category", "Model Range", "Trim Line", "Vehicle Number", "Origin",
                    "Cubic Capacity", "Drive Type", "Features", "Image URLS"
                ])
            writer.writerow([
                car_details.get('url', ''),
                car_details.get('title', ''),
                car_details.get('additional_info', ''),
                car_details.get('price', ''),
                car_details.get('dealer_rating', ''),
                car_details.get('dealer', ''),
                car_details.get('seller_type', ''),
                car_details.get('location', ''),
                car_details.get('phone', ''),
                car_details.get('rating', ''),
                car_details.get('negotiable', ''),
                car_details.get('monthly_rate', ''),
                car_details.get('monthly_rate_href', ''),
                car_details.get('financing_link', ''),
                car_details.get('mileage', ''),
                car_details.get('power', ''),
                car_details.get('fuel_type', ''),
                car_details.get('transmission', ''),
                car_details.get('first_registration', ''),
                car_details.get('vehicle_condition', ''),
                car_details.get('category', ''),
                car_details.get('model_range', ''),
                car_details.get('trim_line', ''),
                car_details.get('vehicle_number', ''),
                car_details.get('origin', ''),
                car_details.get('cubic_capacity', ''),
                car_details.get('drive_type', ''),
                ", ".join(car_details.get('features', [])),
                ", ".join(car_details.get('img_urls', []))
            ])
    except Exception as e:
        logger.error(f"Error writing to CSV: {e}")

def extract_mobile_listing_id(url):
    """Extract listing ID from mobile.de URL"""
    if not url:
        return ""
    try:
        qs = parse_qs(urlsplit(url.strip()).query)
        return (qs.get("id") or [""])[0].strip()
    except Exception:
        return ""

def read_links_from_csv(file_path, col_no=0):
    """Read links from CSV file"""
    links = []
    if not os.path.exists(file_path):
        return links

    try:
        with open(file_path, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader, None)  # skip header
            for row in reader:
                if len(row) > col_no and row[col_no].strip():
                    links.append(row[col_no].strip())
    except Exception as e:
        logger.error(f"Error reading CSV: {e}")
    
    return links

def main():
    """Main scraping function"""
    logger.info("Starting Mobile.de scraper")
    
    driver = setup_headless_driver()
    if not driver:
        logger.error("Failed to initialize Chrome driver")
        return

    try:
        logger.info("Opening Mobile.de...")
        driver.get("https://www.mobile.de/?lang=en")
        time.sleep(5)
        
        # Check for access denied
        if "Access denied" in driver.title or "Zugriff verweigert" in driver.title:
            logger.error("❌ Access denied by mobile.de - anti-bot protection active")
            return
        
        logger.info("Checking for consent...")
        accept_consent_cookie(driver)
        
        time.sleep(5)
        
        # Perform search (Mercedes-Benz, specific model, etc.)
        logger.info("Performing search...")
        try:
            # Select make (Mercedes-Benz)
            make_dropdown = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.ID, 'qs-select-make'))
            )
            mercedes_option = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//option[@value='17200']"))
            )
            mercedes_option.click()

            # Select model
            model_dropdown = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, 'qs-select-model'))
            )
            model_option = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//option[@value='126']"))
            )
            model_option.click()

            # Select mileage
            mileage_dropdown = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, 'qs-select-mileage-up-to'))
            )
            mileage_dropdown.click()
            mileage_option = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//option[@value='50000']"))
            )
            mileage_option.click()

            # Select purchase type
            purchase_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@value='purchase']"))
            )
            purchase_button.click()

            # Submit search
            submit_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="qs-submit-button"]'))
            )
            time.sleep(2)
            submit_button.click()
            logger.info("Search submitted")

        except Exception as e:
            logger.error(f"Search setup failed: {e}")
            return

        # Collect article links
        time1 = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        links_file = f'article_links_{time1}.csv'
        
        with open(links_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Link'])

        seen = set()
        page_count = 0
        total_pages = get_total_pages(driver)
        total_links = 0

        logger.info(f"Starting pagination (max {total_pages} pages)...")
        while page_count < total_pages:
            page_count += 1
            logger.info(f"Processing page {page_count}/{total_pages}")

            try:
                articles = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "article a[href]"))
                )
                
                href_links = []
                for article in articles:
                    link = article.get_attribute("href")
                    if link and link not in seen:
                        seen.add(link)
                        href_links.append(link)

                logger.info(f"Found {len(href_links)} new links on this page")

                if href_links:
                    with open(links_file, mode='a', newline='', encoding='utf-8') as file:
                        writer = csv.writer(file)
                        for link in href_links:
                            writer.writerow([link])
                            total_links += 1

                logger.info(f"Total links collected: {total_links}")

                if page_count >= total_pages:
                    break

                if not click_continue_if_enabled(driver):
                    break

                time.sleep(Config.SCRAPER_DELAY)

            except Exception as e:
                logger.error(f"Error on page {page_count}: {e}")
                break

        logger.info(f"Link collection complete. Saved to '{links_file}'")

        # Scrape individual listings
        logger.info("Starting individual listing scraping...")
        links = read_links_from_csv(links_file, 0)
        output_file = 'car_details_output.csv'

        for i, link in enumerate(links, start=1):
            if not link or not link.strip():
                continue

            listing_id = extract_mobile_listing_id(link)
            if not listing_id:
                logger.warning(f"[{i}/{len(links)}] Skipping (no id found) -> {link}")
                continue

            logger.info(f"[{i}/{len(links)}] Processing -> id={listing_id}")

            try:
                driver.get(link)
                time.sleep(Config.SCRAPER_DELAY)

                # Extract images
                try:
                    container = driver.find_element(By.CSS_SELECTOR, "div.mRJ5K")
                    html = container.get_attribute("innerHTML")
                    image_urls = extract_image_urls(html)
                except Exception:
                    image_urls = []

                # Get page source and parse
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')

                # Extract all details
                technical_data = scrape_technical_data_from_element(soup)
                car_details = scrape_car_details(soup)
                car_details_from_element = scrape_car_details_from_element(soup)

                # Combine all data
                combined_car_details = {
                    "url": link,
                    'img_urls': image_urls,
                    **car_details_from_element,
                    **car_details,
                    **technical_data
                }

                if combined_car_details:
                    save_car_data(combined_car_details, output_file)
                    logger.info(f"Successfully scraped listing {listing_id}")
                else:
                    logger.warning(f"No details found for listing {listing_id}")

            except Exception as e:
                logger.error(f"Error processing {link}: {e}")

        logger.info("Data extraction completed!")

    except Exception as e:
        logger.error(f"Main execution error: {e}")
    finally:
        try:
            driver.quit()
            logger.info("Browser closed")
        except Exception:
            pass

if __name__ == "__main__":
    main()
