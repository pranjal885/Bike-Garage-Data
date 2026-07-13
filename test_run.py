import csv
import os
import sys
from scraper import GoogleMapsScraper

def main():
    print("=" * 60)
    print("RUNNING SCRAPER VERIFICATION TEST")
    print("=" * 60)

    # 1. Initialize scraper
    scraper = GoogleMapsScraper(headless=True)  # headless mode for headless terminal environments
    try:
        scraper.start()
    except Exception as e:
        print(f"Error starting scraper: {e}")
        return

    test_csv = "test_output.csv"
    if os.path.exists(test_csv):
        os.remove(test_csv)

    try:
        query = "bike garage in Kalyani Nagar, Pune"
        print(f"Searching for: '{query}'")
        
        success = scraper.search_query(query)
        if not success:
            print("Failed to navigate to search query.")
            return

        # Scroll results pane (do only 2 scrolls for quick test)
        print("Scrolling results panel...")
        scraper.scroll_results_pane()

        # Get business links
        links = scraper.get_result_links()
        if not links:
            print("No links found in search results.")
            return

        # Take only top 2 links to verify extraction
        test_links = links[:2]
        print(f"Testing extraction on {len(test_links)} links:")

        headers = ["Name", "Contact", "Address", "Website", "Google Maps URL"]
        with open(test_csv, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()

            for link in test_links:
                print(f"Scraping: {link}")
                details = scraper.extract_details(link)
                if details:
                    print(f"Found Details:\n - Name: {details['name']}\n - Phone: {details['phone']}\n - Address: {details['address']}\n - Website: {details['website']}\n")
                    writer.writerow({
                        "Name": details["name"],
                        "Contact": details["phone"],
                        "Address": details["address"],
                        "Website": details["website"],
                        "Google Maps URL": details["url"]
                    })
                    scraper.random_delay()
                else:
                    print(f"Failed to scrape details for {link}")

        print("Verification test completed successfully.")
        print(f"Test data written to {test_csv}")
        
    except Exception as e:
        print(f"An error occurred during test: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
