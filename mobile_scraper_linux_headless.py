#!/usr/bin/env python3

print("Importing libraries...")

import undetected_chromedriver as uc
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

from bs4 import BeautifulSoup
import time
import csv
import os
import re
from urllib.parse import urlsplit, parse_qs, urlunsplit, urlencode
from datetime import datetime

print("Libraries imported successfully")

# Database imports
try:
    from db_operations import save_car_to_database
    print("Database functionality enabled")
    DB_ENABLED = True
except ImportError as e:
    print(f"Database functionality disabled: {e}")
    DB_ENABLED = False

def setup_headless_driver():
    """Setup Chrome driver for Linux headless operation"""
    print("Setting up headless Chrome driver...")
    
    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--no-sandbox")  # Required for Linux
    options.add_argument("--disable-dev-shm-usage")  # Required for Linux
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36")
    options.add_argument("--window-size=1920,1080")
    
    # Use system Chrome driver
    try:
        driver = uc.Chrome(version_main=144, options=options)
        print("Chrome driver initialized successfully")
        return driver
    except Exception as e:
        print(f"Error initializing Chrome driver: {e}")
        print("Make sure Chrome and chromedriver are installed on your system")
        return None

def accept_consent_cookie(driver, timeout=15):
    """Accept Mobile.de consent modal if present"""
    wait = WebDriverWait(driver, timeout)
    try:
        btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.mde-consent-accept-btn"))
        )
        btn.click()
        return True
    except Exception:
        # Try iframes
        for frame in driver.find_elements(By.CSS_SELECTOR, "iframe"):
            driver.switch_to.frame(frame)
            try:
                driver.switch_to.default_content()
                return True
            except Exception:
                driver.switch_to.default_content()
    return False

def click_continue_if_enabled(driver, timeout=10):
    """Click pagination Continue button if enabled"""
    locator = (By.CSS_SELECTOR, 'button[data-testid="pagination:next"]')
    
    try:
        btn = WebDriverWait(driver, timeout).until(EC.presence_of_element_located(locator))
    except TimeoutException:
        print("Continue button not found.")
        return False

    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        
        disabled_attr = btn.get_attribute("disabled")
        aria_disabled = (btn.get_attribute("aria-disabled") or "").lower()
        enabled = btn.is_enabled() and (disabled_attr is None) and (aria_disabled != "true")

        if not enabled:
            print("Continue is disabled.")
            return False

        try:
            btn.click()
        except Exception:
            driver.execute_script("arguments[0].click();", btn)

        print("Continue clicked.")
        return True

    except Exception as e:
        print(f"Could not click Continue: {e}")
        return False

def get_total_pages(driver, timeout=10):
    """Get total number of pages from pagination UI"""
    wait = WebDriverWait(driver, timeout)

    try:
        ratio_el = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="srp-pagination"] span.XUy1p'))
        )
        txt = (ratio_el.text or "").strip()
        m = re.search(r'(\d+)\s*/\s*(\d+)', txt)
        if m:
            total = int(m.group(2))
            print(f"Total pages: {total} (from '{txt}')")
            return total
    except TimeoutException:
        pass
    except Exception as e:
        print(f"Could not read XUy1p ratio: {e}")

    try:
        page_btns = driver.find_elements(By.CSS_SELECTOR, '[data-testid="srp-pagination"] button[aria-label]')
        nums = []
        for b in page_btns:
            al = (b.get_attribute("aria-label") or "").strip()
            m = re.search(r'(?:Page|Seite)\s*(\d+)', al, flags=re.IGNORECASE)
            if m:
                nums.append(int(m.group(1)))
        if nums:
            total = max(nums)
            print(f"Total pages: {total} (from aria-label max)")
            return total
    except Exception as e:
        print(f"Could not read total pages from page buttons: {e}")

    print("Total pages not found.")
    return None

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
        print(f"Error while scraping key features: {e}")
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
            'fahrzeugart': 'category',
            'bodytype': 'category',
            'modelrange': 'model_range',
            'modellreihe': 'model_range',
            'trimline': 'trim_line',
            'ausstattungslinie': 'trim_line',
            'line': 'trim_line',
            'vehiclenumber': 'vehicle_number',
            'fahrzeugnummer': 'vehicle_number',
            'availability': 'availability',
            'verfügbarkeit': 'availability',
            'origin': 'origin',
            'countryversion': 'origin',
            'herkunft': 'origin',
            'mileage': 'mileage',
            'kilometer': 'mileage',
            'kilometerstand': 'mileage',
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

        dts = soup.find_all('dt')
        for dt_tag in dts:
            dd_tag = dt_tag.find_next('dd')
            if dd_tag:
                raw_key = dt_tag.get_text(strip=True)
                norm_key = normalize_label(raw_key)
                key = label_map.get(norm_key, norm_key)
                value = dd_tag.get_text(strip=True)
                car_details[key] = value

        features = []
        for feature_li in soup.find_all('li', class_='FtSYW'):
            feature_name = feature_li.get_text(strip=True)
            features.append(feature_name)
        if features:
            car_details['features'] = features

    except Exception as e:
        print(f"Error extracting technical data: {e}")
        return {}
    return car_details

def scrape_car_details_from_element(soup):
    """Extract high-level listing details"""
    car_details = {}
    try:
        title = soup.find('h2', {'class': 'dNpqi'})
        car_details['title'] = title.get_text(strip=True) if title else 'Not found'

        additional_info = soup.find('div', {'class': 'GOIOV fqe3L EevEz'})
        car_details['additional_info'] = additional_info.get_text(strip=True) if additional_info else 'Not found'

        price = soup.find(attrs={'data-testid': 'vip-price-label'})
        if price:
            car_details['price'] = price.get_text(strip=True)
        else:
            price_div = soup.find('div', {'class': 'HBWcC'})
            car_details['price'] = price_div.get_text(strip=True) if price_div else 'Not found'

        dealer_rating = soup.find('span', {'class': 'qHfAA'})
        car_details['dealer_rating'] = dealer_rating.get_text(strip=True) if dealer_rating else 'Not found'

        dealer = soup.find('a', {'class': 'FWtU1 rqVIk lZcLh'})
        car_details['dealer'] = dealer.get_text(strip=True) if dealer else 'Not found'

        vip_rating = soup.find('div', {'class': '_u77E'})
        car_details['rating'] = vip_rating.get_text(strip=True) if vip_rating else 'Not found'

        negotiable_div = soup.find('div', {'class': 'HaBLt ZD2EM'})
        car_details['negotiable'] = negotiable_div.get_text(strip=True) if negotiable_div else 'Not found'

        monthly_rate_block = soup.find(attrs={'data-testid': 'vip-financing-monthly-rate'})
        if monthly_rate_block:
            rate_link = monthly_rate_block.find('a', href=True)
            if rate_link:
                car_details['monthly_rate'] = rate_link.get_text(strip=True)
                car_details['monthly_rate_href'] = rate_link['href']
            else:
                car_details['monthly_rate'] = monthly_rate_block.get_text(strip=True)
                car_details['monthly_rate_href'] = 'Not found'
        else:
            monthly_rate = soup.find('a', {'class': 'cCGm3'})
            car_details['monthly_rate'] = monthly_rate.get_text(strip=True) if monthly_rate else 'Not found'
            car_details['monthly_rate_href'] = monthly_rate['href'] if monthly_rate and monthly_rate.has_attr('href') else 'Not found'

        seller_block = soup.find(attrs={'data-testid': 'seller-title-address'})
        if seller_block:
            seller_type_div = seller_block.find('div', {'class': 'QTTRi'})
            car_details['seller_type'] = seller_type_div.get_text(strip=True) if seller_type_div else 'Not found'

            loc_div = seller_block.find('div', {'class': 'olCKS'})
            car_details['location'] = loc_div.get_text(strip=True) if loc_div else 'Not found'

            phone_span = seller_block.find('span', attrs={'aria-live': 'polite'})
            car_details['phone'] = phone_span.get_text(strip=True) if phone_span else 'Not found'
        else:
            loc_div = soup.find('div', {'class': 'olCKS HaBLt'})
            car_details['location'] = loc_div.get_text(strip=True) if loc_div else 'Not found'
            phone_h4 = soup.find('h4', {'class': 'DaDwz fpviJ DyuPj'})
            car_details['phone'] = phone_h4.get_text(strip=True) if phone_h4 else 'Not found'

        if 'monthly_rate_href' in car_details and not car_details.get('financing_link'):
            car_details['financing_link'] = car_details['monthly_rate_href']
        return car_details
    except Exception as e:
        print(f"Error extracting car details: {e}")
        return {}

def reveal_full_phone(driver, timeout=10):
    """Reveal full phone number on listing page"""
    try:
        wait = WebDriverWait(driver, timeout)
        show_btn = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'button[data-testid="seller-phone-button"]')
            )
        )
        driver.execute_script("arguments[0].click();", show_btn)

        def full_number_loaded(drv):
            span = drv.find_element(
                By.CSS_SELECTOR,
                "[data-testid='phone-reveal-details'] span[aria-live='polite']"
            )
            return span if "..." not in span.text and "…" not in span.text else False

        phone_span = wait.until(full_number_loaded)
        return phone_span.text.strip()

    except Exception:
        return None

def extract_image_urls(html):
    """Extract image URLs from HTML"""
    soup = BeautifulSoup(html, "html.parser")
    urls = set()
    for img in soup.find_all("img"):
        src = img.get("src")
        if src:
            urls.add(src)
        srcset = img.get("srcset")
        if srcset:
            for part in srcset.split(","):
                url = part.strip().split()[0]
                urls.add(url)
    return list(urls)

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
                    "Cubic Capacity", "Drive Type", "Energy Consumption", "CO2 Emissions",
                    "CO2 Class", "Fuel Consumption", "Features", "Image URLS"
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
                car_details.get('energy_consumption', ''),
                car_details.get('co2_emissions', ''),
                car_details.get('co2_class', ''),
                car_details.get('fuel_consumption', ''),
                ", ".join(car_details.get('features', [])),
                ", ".join(car_details.get('img_urls', []))
            ])
    except Exception as e:
        print(f"Error writing to CSV: {e}")

def save_car_data(car_details, output_file):
    """Save car data to both CSV and database"""
    # Save to CSV (existing functionality)
    write_car_details_to_csv(car_details, output_file)
    
    # Save to database (new functionality)
    if DB_ENABLED:
        save_car_to_database(car_details.copy())

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

    with open(file_path, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader, None)  # skip header
        for row in reader:
            if len(row) > col_no and row[col_no].strip():
                links.append(row[col_no].strip())
    return links

def main():
    """Main scraping function"""
    driver = setup_headless_driver()
    if not driver:
        return

    try:
        print("Opening Mobile.de...")
        driver.get("https://www.mobile.de/?lang=en")
        time.sleep(5)
        
        print("Checking for consent...")
        if accept_consent_cookie(driver):
            print("Cookie consent accepted.")
        else:
            print("Consent button not found.")

        # Check if page loaded properly
        print(f"Page title: {driver.title}")
        if "Access denied" in driver.title or "Zugriff verweigert" in driver.title:
            print("❌ Access denied by mobile.de - anti-bot protection active")
            print("The scraper setup is working, but mobile.de is blocking automated access")
            return
        
        # Wait longer for page to load
        time.sleep(10)
        
        # Select Mercedes-Benz (value='17200')
        print("Selecting make...")
        try:
            make_dropdown = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.ID, 'qs-select-make'))
            )
            mercedes_option = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//option[@value='17200']"))
            )
            mercedes_option.click()
        except Exception as e:
            print(f"Could not find make dropdown: {e}")
            print("This is likely due to anti-bot protection or page structure changes")
            return

        # Select Model (value='126')
        print("Selecting model...")
        model_dropdown = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'qs-select-model'))
        )
        model_option = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//option[@value='126']"))
        )
        model_option.click()

        # Select mileage
        print("Selecting mileage...")
        mileage_dropdown = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'qs-select-mileage-up-to'))
        )
        mileage_dropdown.click()
        mileage_option = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//option[@value='50000']"))
        )
        mileage_option.click()

        # Select purchase type
        print("Selecting purchase type...")
        purchase_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@value='purchase']"))
        )
        purchase_button.click()

        # Click geolocation
        print("Clicking geolocation...")
        geo_input = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'geolocation-autosuggest'))
        )
        geo_input.click()

        # Submit search
        print("Submitting search...")
        submit_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="qs-submit-button"]'))
        )
        time.sleep(2)
        
        button_text = submit_button.text
        print(f"Search button text: {button_text}")
        total_searches = int(button_text.split()[0].replace(",", ""))
        print(f"Total searches: {total_searches}")

        submit_button.click()
        print("Search submitted")

        # Collect all article links
        time1 = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        links_file = f'article_links_{time1}.csv'
        
        with open(links_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Link'])

        seen = set()
        page_count = 0
        total_pages = get_total_pages(driver)
        total_links = 0

        print("Starting pagination...")
        while True:
            page_count += 1
            print(f"Processing page {page_count} of {total_pages or 'unknown'}")

            articles = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "article a[href]"))
            )
            
            WebDriverWait(driver, 30).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )

            href_links = []
            for article in articles:
                link = article.get_attribute("href")
                if link and link not in seen:
                    seen.add(link)
                    href_links.append(link)

            print(f"Found {len(href_links)} new links on this page")

            if href_links:
                with open(links_file, mode='a', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    for link in href_links:
                        writer.writerow([link])
                        total_links += 1

            print(f"Total links collected: {total_links}")

            if page_count == total_pages:
                print("Reached last page")
                break

            clicked = click_continue_if_enabled(driver)
            if not clicked:
                print("Cannot continue pagination")
                break

            time.sleep(2)

        print(f"Link collection complete. Saved to '{links_file}'")

        # Now scrape individual listings
        print("Starting individual listing scraping...")
        links = read_links_from_csv(links_file, 0)
        scraped_links = read_links_from_csv("car_details_output.csv", 0)
        scraped_ids_set = {extract_mobile_listing_id(u) for u in scraped_links if extract_mobile_listing_id(u)}
        output_file = 'car_details_output.csv'

        for i, link in enumerate(links, start=1):
            if not link or not link.strip():
                continue

            listing_id = extract_mobile_listing_id(link)
            if not listing_id:
                print(f"[{i}/{len(links)}] Skipping (no id found) -> {link.strip()}")
                continue

            if listing_id in scraped_ids_set:
                print(f"[{i}/{len(links)}] Already scraped -> id={listing_id}")
                continue

            print(f"[{i}/{len(links)}] Processing -> id={listing_id}")

            try:
                driver.get(link)
                time.sleep(3)

                # Try to reveal phone number
                try:
                    reveal_full_phone(driver)
                except Exception as e:
                    print(f"Could not reveal phone: {e}")

                # Extract images
                try:
                    container = driver.find_element(By.CSS_SELECTOR, "div.mRJ5K")
                    html = container.get_attribute("innerHTML")
                    image_urls = extract_image_urls(html)
                except Exception as e:
                    print(f"Could not extract images: {e}")
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

                # Write to CSV
                if combined_car_details:
                    save_car_data(combined_car_details, output_file)
                    print(f"Successfully scraped listing {listing_id}")
                else:
                    print(f"No details found for listing {listing_id}")

                scraped_ids_set.add(listing_id)

            except Exception as e:
                print(f"Error processing {link}: {e}")

        print("Data extraction completed!")

    except Exception as e:
        print(f"Main execution error: {e}")
    finally:
        driver.quit()
        print("Browser closed")

if __name__ == "__main__":
    main()
def run():
    """API wrapper function for the scraper"""
    return main()
