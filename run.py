import os
import csv
import sys
import logging
from scraper import GoogleMapsScraper
import config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_existing_data(filepath):
    """Loads existing unique Google Maps URLs from the CSV file to support resumption."""
    scraped_urls = set()
    scraped_data_count = 0
    if os.path.exists(filepath):
        try:
            with open(filepath, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    url = row.get("Google Maps URL")
                    if url:
                        scraped_urls.add(url)
                    scraped_data_count += 1
            logger.info(f"Loaded {scraped_data_count} existing records from {filepath}. Unique URLs: {len(scraped_urls)}")
        except Exception as e:
            logger.error(f"Error reading existing CSV: {e}")
    else:
        logger.info(f"No existing CSV found at {filepath}. Starting fresh.")
    return scraped_urls

def append_to_csv(filepath, data):
    """Appends a single business record to the CSV file."""
    file_exists = os.path.exists(filepath)
    headers = ["Name", "Contact", "Address", "Website", "Google Maps URL"]
    
    try:
        with open(filepath, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                "Name": data["name"],
                "Contact": data["phone"],
                "Address": data["address"],
                "Website": data["website"],
                "Google Maps URL": data["url"]
            })
    except Exception as e:
        logger.error(f"Failed to write to CSV: {e}")

def main():
    logger.info("=" * 60)
    logger.info("STARTING PUNE BIKE GARAGE GOOGLE MAPS SCRAPER")
    logger.info("=" * 60)

    # 1. Load existing data for resuming progress
    csv_path = config.OUTPUT_CSV
    scraped_urls = load_existing_data(csv_path)
    total_scraped = len(scraped_urls)
    TARGET = 1200

    if total_scraped >= TARGET:
        logger.info(f"Target already met! Already have {total_scraped} unique items. Exiting.")
        return

    # 2. Initialize and start scraper browser
    scraper = GoogleMapsScraper()
    try:
        scraper.start()
    except Exception as e:
        logger.error(f"Failed to start Playwright browser: {e}")
        return

    try:
        # 3. Main search loop
        queries_completed = 0
        total_queries = len(config.PUNE_NEIGHBORHOODS) * len(config.SEARCH_QUERIES)
        
        for n_idx, neighborhood in enumerate(config.PUNE_NEIGHBORHOODS, start=1):
            if total_scraped >= TARGET:
                logger.info("Reached target of 1200+ bike garages!")
                break
                
            for q_idx, search_term in enumerate(config.SEARCH_QUERIES, start=1):
                if total_scraped >= TARGET:
                    break

                queries_completed += 1
                query = f"{search_term} in {neighborhood}, Pune"
                
                logger.info("-" * 50)
                logger.info(f"Query {queries_completed}/{total_queries}: '{query}'")
                logger.info(f"Neighborhood: {neighborhood} ({n_idx}/{len(config.PUNE_NEIGHBORHOODS)})")
                logger.info(f"Current Progress: {total_scraped}/{TARGET} unique records")
                logger.info("-" * 50)

                # Search
                success = scraper.search_query(query)
                if not success:
                    logger.warning(f"Skipping query '{query}' due to navigation error.")
                    continue

                # Scroll to load all result cards
                scraper.scroll_results_pane()

                # Get all links
                links = scraper.get_result_links()
                if not links:
                    logger.info(f"No listings found for query '{query}'.")
                    continue

                # Process each link
                new_in_query = 0
                for link in links:
                    if total_scraped >= TARGET:
                        logger.info("Reached target of {TARGET}+ bike garages!")
                        break

                    # Check if already scraped
                    if link in scraped_urls:
                        continue

                    # Extract details
                    details = scraper.extract_details(link)
                    if details:
                        append_to_csv(csv_path, details)
                        scraped_urls.add(link)
                        total_scraped += 1
                        new_in_query += 1
                        
                        # Short delay between detail extractions to look human
                        scraper.random_delay()

                logger.info(f"Completed query '{query}'. Scraped {new_in_query} new items from {len(links)} total links.")

        logger.info("=" * 60)
        logger.info(f"SCRAPING RUN FINISHED.")
        logger.info(f"Total unique records saved: {total_scraped}")
        logger.info("=" * 60)

    except KeyboardInterrupt:
        logger.info("\nScraping interrupted by user. Saving progress and exiting...")
    except Exception as e:
        logger.error(f"An unexpected error occurred during scraping: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
