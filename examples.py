"""
Example usage script showing different ways to use the scraper
"""
from scraper import RoadAccidentScraper
from data_processor import DataProcessor
import json


def example_single_url():
    """Example: Scrape a single URL"""
    print("\n" + "="*60)
    print("Example 1: Scraping a Single URL")
    print("="*60 + "\n")
    
    scraper = RoadAccidentScraper()
    
    # Scrape one URL
    url_config = {
        "url": "https://www.tandfonline.com/doi/full/10.1080/23311916.2020.1797981",
        "name": "test_single_url",
        "description": "Test single URL scraping"
    }
    
    data = scraper.scrape_url(url_config)
    
    if data:
        print(f"\n✅ Success! Data extracted:")
        print(json.dumps(data, indent=2)[:500] + "...")


def example_custom_urls():
    """Example: Scrape custom URLs"""
    print("\n" + "="*60)
    print("Example 2: Scraping Custom URLs")
    print("="*60 + "\n")
    
    scraper = RoadAccidentScraper()
    
    # Define your own URLs
    custom_urls = [
        {
            "url": "https://www.knbs.or.ke/",
            "name": "knbs_statistics",
            "description": "Kenya National Bureau of Statistics"
        }
    ]
    
    all_data = []
    for url_config in custom_urls:
        data = scraper.scrape_url(url_config)
        if data:
            all_data.append(data)
    
    print(f"\n✅ Scraped {len(all_data)} URLs successfully")


def example_with_web_unlocker():
    """Example: Using Web Unlocker for blocked sites"""
    print("\n" + "="*60)
    print("Example 3: Using Web Unlocker")
    print("="*60 + "\n")
    
    # Enable Web Unlocker (requires API key in .env)
    scraper = RoadAccidentScraper(use_web_unlocker=True)
    
    url_config = {
        "url": "https://example.com/blocked-site",
        "name": "blocked_site",
        "description": "Site that blocks regular requests"
    }
    
    data = scraper.scrape_url(url_config)
    
    if data:
        print("\n✅ Successfully bypassed blocking!")


def example_data_processing():
    """Example: Process and aggregate scraped data"""
    print("\n" + "="*60)
    print("Example 4: Data Processing and Aggregation")
    print("="*60 + "\n")
    
    processor = DataProcessor()
    
    # Load all scraped data
    import os
    from config import OUTPUT_DIR
    
    data_list = []
    if os.path.exists(OUTPUT_DIR):
        for filename in os.listdir(OUTPUT_DIR):
            if filename.endswith('.json') and filename != 'road_accident_data_aggregated.json':
                filepath = os.path.join(OUTPUT_DIR, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data_list.append(json.load(f))
    
    if data_list:
        # Aggregate data
        aggregated = processor.aggregate_data(data_list)
        print(f"\n✅ Aggregated data from {len(data_list)} sources")
        
        # Export for ML
        processor.export_for_ml(aggregated)
        print("\n✅ ML-ready data exported")
    else:
        print("\n⚠️  No scraped data found. Run scraper.py first.")


def main():
    """Run all examples"""
    print("\n" + "="*80)
    print("📚 KENYA ROAD ACCIDENT SCRAPER - USAGE EXAMPLES")
    print("="*80)
    
    print("\nChoose an example to run:")
    print("1. Scrape a single URL")
    print("2. Scrape custom URLs")
    print("3. Use Web Unlocker (requires API key)")
    print("4. Process and aggregate data")
    print("5. Run all examples")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    if choice == "1":
        example_single_url()
    elif choice == "2":
        example_custom_urls()
    elif choice == "3":
        example_with_web_unlocker()
    elif choice == "4":
        example_data_processing()
    elif choice == "5":
        example_single_url()
        example_custom_urls()
        example_data_processing()
    else:
        print("Invalid choice. Please run again and select 1-5.")


if __name__ == "__main__":
    main()
