# ==========================================================
# Google Maps Bike Garage Scraper Configuration
# ==========================================================

TARGET_RECORDS = 50000

OUTPUT_CSV = "maharashtra_bike_garages.csv"

SEARCH_QUERIES = [
    "bike garage",
    "motorcycle garage",
    "motorcycle repair",
    "bike repair",
    "bike service center",
    "bike mechanic",
    "bike workshop",
    "motorcycle workshop",
    "two wheeler garage",
    "two wheeler repair",
    "two wheeler service",
    "scooter repair",
    "scooter service",
    "Hero service center",
    "Honda bike service",
    "TVS service center",
    "Bajaj service center",
    "Royal Enfield service",
    "Yamaha service center",
    "Suzuki bike service"
]

HEADLESS = False

DELAY_RANGE = (1.5, 3.5)

SCROLL_PAUSE = 2.0

MAX_SCROLLS = 80

PAGE_TIMEOUT = 30000