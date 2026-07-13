# Configuration settings for the Google Maps Bike Garage Scraper

# List of prominent neighborhoods/suburbs in Pune to partition search queries
PUNE_NEIGHBORHOODS = [
    "Kothrud",
    "Baner",
    "Aundh",
    "Wakad",
    "Hinjawadi",
    "Kalyani Nagar",
    "Koregaon Park",
    "Hadapsar",
    "Kharadi",
    "Viman Nagar",
    "Katraj",
    "Kondhwa",
    "Camp",
    "Swargate",
    "Shivaji Nagar",
    "Pimple Saudagar",
    "Chinchwad",
    "Pimpri",
    "Yerwada",
    "Deccan Gymkhana",
    "Karve Nagar",
    "Warje",
    "Sinhagad Road",
    "Balewadi",
    "Bavdhan",
    "Undri",
    "Bibwewadi",
    "Dhankawadi",
    "Lohegaon",
    "Wagholi",
    "Nigdi",
    "Sangvi",
    "Pimple Gurav",
    "Dhanori"
]

# Search terms to combine with neighborhoods
SEARCH_QUERIES = [
    "bike garage",
    "motorcycle repair",
    "bike service center",
    "bike mechanic",
    "scooter repair",
    "royal enfield service",
    "bajaj service center",
    "hero service center",
    "honda bike service",
    "yamaha service center",
    "TVS service center",
    "Suzuki bike service"
]

# Output settings
OUTPUT_CSV = "pune_bike_garages.csv"

# Browser & Scraper behavior settings
HEADLESS = False  # Headed mode is much safer against anti-bot checks and CAPTCHAs
DELAY_RANGE = (1.5, 3.5)  # Random delay range (seconds) between clicks to simulate human behavior
SCROLL_PAUSE = 2.0  # Pause (seconds) after each scroll to let results load
MAX_SCROLLS = 80  # Maximum number of scrolls to try to reach the bottom of the feed
PAGE_TIMEOUT = 30000  # Page load timeout in milliseconds (30 seconds)
