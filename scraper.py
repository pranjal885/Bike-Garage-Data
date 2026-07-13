import time
import random
import logging
from urllib.parse import quote
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
import config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def clean_string(s):
    if not s:
        return ""
    # Remove Unicode Private Use Area characters (E000-F8FF) commonly used for icons
    return "".join(c for c in s if not (0xE000 <= ord(c) <= 0xF8FF)).strip()

class GoogleMapsScraper:
    def __init__(self, headless=config.HEADLESS):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def start(self):
        """Starts the browser context with stealth configurations."""
        logger.info("Launching Chromium browser...")
        self.playwright = sync_playwright().start()
        
        # Launch Chromium with anti-bot arguments
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-infobars",
                "--window-size=1280,800",
            ]
        )
        
        self.context = self.browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        self.page = self.context.new_page()
        Stealth().apply_stealth_sync(self.page)
        
        # Set default timeout
        self.page.set_default_timeout(config.PAGE_TIMEOUT)

    def close(self):
        """Safely closes the browser context."""
        logger.info("Closing browser...")
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def random_delay(self):
        """Simulates human interaction delay."""
        delay = random.uniform(*config.DELAY_RANGE)
        time.sleep(delay)

    def search_query(self, query):
        """Navigates to Google Maps search page for a query."""
        encoded_query = quote(query)
        search_url = f"https://www.google.com/maps/search/{encoded_query}"
        logger.info(f"Navigating to: {search_url}")
        
        try:
            self.page.goto(search_url)
            self.page.wait_for_load_state("domcontentloaded")
            self.random_delay()
            return True
        except Exception as e:
            logger.error(f"Error navigating to search page: {e}")
            return False

    def is_single_result_page(self):
        """Checks if the search redirected directly to a single place page."""
        current_url = self.page.url
        return "/maps/place/" in current_url

    def scroll_results_pane(self):
        """Scrolls the left-side search results feed to load all items."""
        logger.info("Scrolling results pane...")
        
        # Check if we are redirected to a single place page directly
        if self.is_single_result_page():
            logger.info("Redirected directly to single business page. Skipping scroll.")
            return True

        # Wait for the feed container to load
        try:
            self.page.wait_for_selector('div[role="feed"]', timeout=8000)
        except Exception:
            logger.warning("Feed container 'div[role=\"feed\"]' not found. It might be a single result or no results page.")
            return False

        scrollable_div = self.page.locator('div[role="feed"]')
        
        last_height = self.page.evaluate('(el) => el.scrollHeight', scrollable_div.element_handle())
        scroll_attempts = 0
        consecutive_same_height = 0
        
        while scroll_attempts < config.MAX_SCROLLS:
            # Scroll to the bottom of the container
            self.page.evaluate('(el) => el.scrollTop = el.scrollHeight', scrollable_div.element_handle())
            time.sleep(config.SCROLL_PAUSE)
            
            # Check new scroll height
            new_height = self.page.evaluate('(el) => el.scrollHeight', scrollable_div.element_handle())
            
            # Check if we reached the bottom or if the height remains the same
            if new_height == last_height:
                consecutive_same_height += 1
                if consecutive_same_height >= 3:
                    logger.info("Reached the bottom of the results feed.")
                    break
            else:
                consecutive_same_height = 0
                last_height = new_height
            
            # Check if Google's "end of list" text is visible
            feed_text = scrollable_div.inner_text()
            if "You've reached the end of the list." in feed_text or "reached the end" in feed_text.lower():
                logger.info("End of list text detected.")
                break
                
            scroll_attempts += 1
            if scroll_attempts % 5 == 0:
                logger.info(f"Scroll attempts: {scroll_attempts}/{config.MAX_SCROLLS}")

        return True

    def get_result_links(self):
        """Extracts the links to all business listings in the results page."""
        if self.is_single_result_page():
            logger.info("Single result URL detected.")
            return [self.page.url]
            
        links = []
        try:
            # Google Maps results list links contain '/maps/place/'
            # We locate these links specifically inside the results cards
            card_elements = self.page.locator('a[href*="/maps/place/"]').all()
            for card in card_elements:
                href = card.get_attribute("href")
                if href and href not in links:
                    links.append(href)
            
            logger.info(f"Found {len(links)} potential business listing links.")
        except Exception as e:
            logger.error(f"Error extracting listing links: {e}")
            
        return links

    def extract_details(self, url):
        """Navigates to a listing URL and extracts Name, Phone, Address, and Website."""
        logger.info(f"Extracting details from: {url.split('/place/')[1][:30]}...")
        
        try:
            # Clear old detail elements from the DOM to prevent SPA race conditions
            try:
                self.page.evaluate("""() => {
                    document.querySelector('h1')?.remove();
                    document.querySelector('button[data-item-id="address"]')?.remove();
                    document.querySelector('button[data-item-id^="phone:tel:"]')?.remove();
                    document.querySelector('a[data-item-id="authority"]')?.remove();
                }""")
            except Exception:
                pass

            # Go directly to the place URL
            self.page.goto(url)
            self.page.wait_for_load_state("domcontentloaded")
            self.random_delay()
            
            # 1. Extract Name (typically the only H1 in the detail pane)
            name = ""
            try:
                # Wait for the heading element to load
                self.page.wait_for_selector('h1', timeout=10000)
                name_element = self.page.locator('h1').first
                name = clean_string(name_element.inner_text())
            except Exception as e:
                logger.warning(f"Could not extract business name: {e}")
                return None  # If we can't get the name, this entry is invalid
            
            # 2. Extract Phone Number
            phone = ""
            try:
                # Phone buttons have data-item-id starting with "phone:tel:"
                phone_locator = self.page.locator('button[data-item-id^="phone:tel:"]')
                if phone_locator.count() > 0:
                    data_item_id = phone_locator.first.get_attribute("data-item-id")
                    if data_item_id:
                        phone = data_item_id.replace("phone:tel:", "").strip()
                    else:
                        phone = phone_locator.first.inner_text()
                phone = clean_string(phone)
            except Exception:
                pass
            
            # 3. Extract Address
            address = ""
            try:
                # Address button has data-item-id="address"
                address_locator = self.page.locator('button[data-item-id="address"]')
                if address_locator.count() > 0:
                    address = clean_string(address_locator.first.inner_text())
            except Exception:
                pass

            # 4. Extract Website
            website = ""
            try:
                # Website link has data-item-id="authority"
                website_locator = self.page.locator('a[data-item-id="authority"]')
                if website_locator.count() > 0:
                    website = website_locator.first.get_attribute("href")
                    if website:
                        # Clean Google's redirect tracking parameters if any
                        website = website.split("?")[0]
                website = clean_string(website)
            except Exception:
                pass

            details = {
                "name": name,
                "phone": phone,
                "address": address,
                "website": website,
                "url": url
            }
            logger.info(f"Successfully scraped: '{name}' | Phone: '{phone}' | Web: '{website}'")
            return details

        except Exception as e:
            logger.error(f"Error extracting details from listing: {e}")
            return None
