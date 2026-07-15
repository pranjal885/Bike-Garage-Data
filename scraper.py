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
      """Starts Chromium browser with stealth settings."""

      logger.info("Launching Chromium browser...")

      self.playwright = sync_playwright().start()

      self.browser = self.playwright.chromium.launch(

        headless=self.headless,

        args=[

            "--disable-blink-features=AutomationControlled",

            "--disable-dev-shm-usage",

            "--no-sandbox",

            "--disable-infobars",

            "--disable-gpu",

            "--disable-extensions",

            "--window-size=1280,800"

        ]

    )

      self.context = self.browser.new_context(

        viewport={

            "width":1280,

            "height":800

        },

        user_agent=(

            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "

            "AppleWebKit/537.36 (KHTML, like Gecko) "

            "Chrome/138.0.0.0 Safari/537.36"

        ),

        locale="en-IN",

        timezone_id="Asia/Kolkata"

    )

      self.page = self.context.new_page()

      Stealth().apply_stealth_sync(self.page)

      self.page.set_default_timeout(config.PAGE_TIMEOUT)

      logger.info("Browser launched successfully.")

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
     """Search Google Maps with retry support."""

     encoded_query = quote(query)
     search_url = f"https://www.google.com/maps/search/{encoded_query}"

     logger.info(f"Searching: {query}")

     for attempt in range(3):

        try:

            self.page.goto(
                search_url,
                wait_until="domcontentloaded"
            )

            # Wait for results feed if available
            try:
                self.page.wait_for_selector(
                    'div[role="feed"]',
                    timeout=10000
                )
            except:
                pass

            # Give Google Maps some time to render
            time.sleep(2)

            self.random_delay()

            # Detect CAPTCHA
            if "sorry" in self.page.url.lower():
                logger.warning("Google CAPTCHA detected.")
                time.sleep(30)
                continue

            return True

        except Exception as e:

            logger.warning(
                f"Search failed (Attempt {attempt + 1}/3): {e}"
            )

            time.sleep(random.randint(3, 7))

     logger.error(f"Skipping query: {query}")

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
     """Extract Name, Phone, Address and Website with retries."""

     logger.info(f"Extracting: {url}")
 
     for attempt in range(3):

        try:

            self.page.goto(
                url,
                wait_until="domcontentloaded"
            )

            time.sleep(3)
            self.random_delay()

            # ---------------- Name ---------------- #

            name = ""

            try:
                self.page.wait_for_selector("h1", timeout=10000)

                name = clean_string(
                    self.page.locator("h1").first.inner_text()
                )

            except Exception:
                logger.warning("Name not found.")
                return None

            # ---------------- Phone ---------------- #

            phone = ""

            phone_selectors = [
                'button[data-item-id^="phone:tel:"]',
                'button[aria-label*="Phone"]',
                'button[aria-label*="Call"]'
            ]

            for selector in phone_selectors:

                try:

                    locator = self.page.locator(selector)

                    if locator.count() > 0:

                        data = locator.first.get_attribute("data-item-id")

                        if data and "phone:tel:" in data:
                            phone = data.replace(
                                "phone:tel:",
                                ""
                            ).strip()
                        else:
                            phone = locator.first.inner_text()

                        phone = clean_string(phone)

                        if phone:
                            break

                except Exception:
                    pass

            # ---------------- Address ---------------- #

            address = ""

            address_selectors = [
                'button[data-item-id="address"]',
                'button[aria-label*="Address"]'
            ]

            for selector in address_selectors:

                try:

                    locator = self.page.locator(selector)

                    if locator.count() > 0:

                        address = clean_string(
                            locator.first.inner_text()
                        )

                        if address:
                            break

                except Exception:
                    pass

            # ---------------- Website ---------------- #

            website = ""

            website_selectors = [
                'a[data-item-id="authority"]',
                'a[aria-label*="Website"]'
            ]

            for selector in website_selectors:

                try:

                    locator = self.page.locator(selector)

                    if locator.count() > 0:

                        website = locator.first.get_attribute("href")

                        if website:
                            website = website.split("?")[0]
                            break

                except Exception:
                    pass

            details = {
                "name": name,
                "phone": phone,
                "address": address,
                "website": website,
                "url": url
            }

            logger.info(f"Scraped: {name}")

            return details

        except Exception as e:

            logger.warning(
                f"Retry {attempt + 1}/3 : {e}"
            )

            time.sleep(random.randint(2, 5))

     logger.error(
        f"Failed after 3 retries : {url}"
     )

     return None