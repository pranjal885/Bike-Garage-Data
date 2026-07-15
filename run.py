import os
import csv
import sys
import logging

from scraper import GoogleMapsScraper
import scraper

print(scraper.__file__)
print(hasattr(GoogleMapsScraper, "search_query"))
print(dir(GoogleMapsScraper))
from locations import MAHARASHTRA
import config

# =====================================================
# Logging
# =====================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# =====================================================
# Load Existing CSV
# =====================================================

def load_existing_data(filepath):

    scraped_urls = set()
    scraped_names = set()
    scraped_phones = set()

    scraped_data_count = 0

    if os.path.exists(filepath):

        try:

            with open(filepath, mode="r", encoding="utf-8") as f:

                reader = csv.DictReader(f)

                for row in reader:

                    url = row.get("Google Maps URL", "").strip()

                    name = row.get("Name", "").strip().lower()

                    phone = row.get("Contact", "").strip()

                    if url:
                        scraped_urls.add(url)

                    if name:
                        scraped_names.add(name)

                    if phone:
                        scraped_phones.add(phone)

                    scraped_data_count += 1

            logger.info(
                f"Loaded {scraped_data_count} records "
                f"({len(scraped_urls)} unique URLs)"
            )

        except Exception as e:

            logger.error(e)

    else:

        logger.info("Starting new dataset.")

    return scraped_urls, scraped_names, scraped_phones

# =====================================================
# Append CSV
# =====================================================

def append_to_csv(filepath, data):

    headers = [
        "Name",
        "Contact",
        "Address",
        "Website",
        "Google Maps URL"
    ]

    file_exists = os.path.exists(filepath)

    try:

        with open(
            filepath,
            mode="a",
            newline="",
            encoding="utf-8"
        ) as f:

            writer = csv.DictWriter(
                f,
                fieldnames=headers
            )

            if not file_exists:
                writer.writeheader()

            writer.writerow({

                "Name": data["name"],

                "Contact": data["phone"],

                "Address": data["address"],

                "Website": data["website"],

                "Google Maps URL": data["url"]

            })

            f.flush()
            os.fsync(f.fileno())

    except Exception as e:

        logger.error(f"CSV Write Error : {e}")


# =====================================================
# Main
# =====================================================

def main():

    logger.info("=" * 70)
    logger.info("MAHARASHTRA BIKE GARAGE SCRAPER")
    logger.info("=" * 70)

    csv_path = config.OUTPUT_CSV

    TARGET = config.TARGET_RECORDS

    scraped_urls, scraped_names, scraped_phones = load_existing_data(csv_path)

    total_scraped = len(scraped_urls)

    if total_scraped >= TARGET:

        logger.info(
            f"Target already achieved ({total_scraped})"
        )

        return

    scraper = GoogleMapsScraper()

    try:

        scraper.start()

    except Exception as e:

        logger.error(f"Browser failed to start : {e}")

        return

    try:

        total_queries = sum(
            len(areas)
            for areas in MAHARASHTRA.values()
        ) * len(config.SEARCH_QUERIES)

        query_number = 0
                # =====================================================
        # Maharashtra Loop
        # =====================================================

        for city, areas in MAHARASHTRA.items():

            logger.info("")
            logger.info("=" * 70)
            logger.info(f"STARTING CITY : {city}")
            logger.info("=" * 70)

            for area in areas:

                if total_scraped >= TARGET:

                    logger.info(
                        f"Reached target of {TARGET} records."
                    )

                    break

                logger.info("")
                logger.info("-" * 60)
                logger.info(f"Area : {area}")
                logger.info("-" * 60)

                for search_term in config.SEARCH_QUERIES:

                    if total_scraped >= TARGET:
                        break

                    query_number += 1

                    query = (
                        f"{search_term} "
                        f"in {area}, {city}, Maharashtra"
                    )

                    logger.info("")
                    logger.info("=" * 60)
                    logger.info(
                        f"Query {query_number}/{total_queries}"
                    )
                    logger.info(f"City      : {city}")
                    logger.info(f"Area      : {area}")
                    logger.info(f"Search    : {search_term}")
                    logger.info(
                        f"Collected : {total_scraped}/{TARGET}"
                    )
                    logger.info("=" * 60)

                    success = scraper.search_query(query)

                    if not success:

                        logger.warning(
                            f"Search failed : {query}"
                        )

                        continue

                    scraper.scroll_results_pane()

                    links = scraper.get_result_links()

                    if not links:

                        logger.info(
                            f"No businesses found for {query}"
                        )

                        continue

                    logger.info(
                        f"Found {len(links)} business links."
                    )

                    new_in_query = 0

                    for link in links:

                        if total_scraped >= TARGET:

                            logger.info(
                                f"Target {TARGET} reached."
                            )

                            break

                        if link in scraped_urls:
                            continue

                        details = scraper.extract_details(link)

                        if details is None:
                           continue

                        name = details["name"].strip().lower()

                        phone = details["phone"].strip()

                        if name in scraped_names:
                           continue

                        if phone and phone in scraped_phones:
                            continue

                        append_to_csv(
                            csv_path,
                            details
                        )

                        scraped_urls.add(link)

                        scraped_names.add(name)

                        if phone:
                          scraped_phones.add(phone)

                        total_scraped += 1
                        if total_scraped % 100 == 0:

                          logger.info("=" * 60)

                          logger.info(f"Collected : {total_scraped}")

                          logger.info(f"Current City : {city}")

                          logger.info(f"Current Area : {area}")

                          logger.info("=" * 60)
                        new_in_query += 1

                        logger.info(
                            f"Total Collected : {total_scraped}"
                        )

                        scraper.random_delay()

                    logger.info(
                        f"Added {new_in_query} new businesses "
                        f"from current search."
                    )
                                # Stop everything if target reached
            if total_scraped >= TARGET:
                break

        logger.info("")
        logger.info("=" * 70)
        logger.info("SCRAPING COMPLETED")
        logger.info("=" * 70)
        logger.info(f"Total Records Collected : {total_scraped}")
        logger.info(f"Output File             : {csv_path}")
        logger.info("=" * 70)

    except KeyboardInterrupt:

        logger.info("")
        logger.info("Scraping interrupted by user.")

    except Exception as e:

        logger.error(f"Unexpected Error : {e}")

    finally:

        try:
            scraper.close()
        except Exception:
            pass

        logger.info("Browser Closed.")


if __name__ == "__main__":
    main()