"""
Kenya Road Accident Data Scraper using Gemini AI
Scrapes road accident statistics and safety information from multiple sources
"""
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify
import json
import os
import time
from datetime import datetime
from config import (
    GEMINI_API_KEY,
    TARGET_URLS,
    EXTRACTION_ATTRIBUTES,
    GEMINI_MODEL,
    GENERATION_CONFIG,
    CONTENT_SELECTORS,
    OUTPUT_DIR,
    WEB_UNLOCKER_API_KEY
)


class RoadAccidentScraper:
    """
    Main scraper class for extracting road accident data using Gemini AI
    """
    
    def __init__(self, use_web_unlocker=False):
        """
        Initialize the scraper with Gemini API configuration
        
        Args:
            use_web_unlocker: Whether to use Web Unlocker API for bypassing anti-scraping
        """
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found. Please set it in your .env file")
        
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(GEMINI_MODEL, generation_config=GENERATION_CONFIG)
        self.use_web_unlocker = use_web_unlocker
        
        # Create output directory if it doesn't exist
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
    
    def fetch_html(self, url):
        """
        Fetch HTML content from the target URL
        
        Args:
            url: Target URL to scrape
            
        Returns:
            HTML content as string
        """
        if self.use_web_unlocker and WEB_UNLOCKER_API_KEY:
            return self._fetch_with_unlocker(url)
        else:
            return self._fetch_with_requests(url)
    
    def _fetch_with_requests(self, url):
        """Fetch HTML using standard requests library"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def _fetch_with_unlocker(self, url):
        """Fetch HTML using Web Unlocker API to bypass anti-scraping"""
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {WEB_UNLOCKER_API_KEY}"
            }
            
            payload = {
                "zone": "unblocker",
                "url": url,
                "format": "raw"
            }
            
            response = requests.post(
                "https://api.brightdata.com/request", 
                json=payload, 
                headers=headers,
                timeout=60
            )
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            print(f"Error with Web Unlocker for {url}: {e}")
            return None
    
    def extract_main_content(self, html):
        """
        Extract main content from HTML using CSS selectors
        
        Args:
            html: Raw HTML content
            
        Returns:
            Extracted HTML content as string
        """
        if not html:
            return None
        
        soup = BeautifulSoup(html, "html.parser")
        
        # Try each selector until we find content
        for selector in CONTENT_SELECTORS:
            element = soup.select_one(selector)
            if element:
                return str(element)
        
        # If no selector works, return body content
        return str(soup.body) if soup.body else str(soup)
    
    def html_to_markdown(self, html):
        """
        Convert HTML to Markdown for more efficient token usage
        
        Args:
            html: HTML content as string
            
        Returns:
            Markdown formatted string
        """
        if not html:
            return None
        
        markdown = markdownify(html)
        return markdown
    
    def extract_data_with_gemini(self, markdown_content, url_name):
        """
        Use Gemini AI to extract structured data from Markdown content
        
        Args:
            markdown_content: Content in Markdown format
            url_name: Name identifier for the source
            
        Returns:
            Extracted data as dictionary
        """
        if not markdown_content:
            return None
        
        prompt = f"""You are an AI assistant specialized in extracting road accident and safety data from Kenyan sources.

Extract comprehensive data from the content below. Focus on road accident statistics, safety initiatives, black spots, causes, and trends.

Respond with a raw string in JSON format containing the scraped data in the specified attributes:

JSON ATTRIBUTES:
{EXTRACTION_ATTRIBUTES}

IMPORTANT INSTRUCTIONS:
- Extract ALL numerical data (statistics, fatalities, injuries, accident counts)
- Identify specific locations, roads, and black spots mentioned
- Extract temporal patterns (years, months, dates, time periods)
- Capture causes and contributing factors
- Include government initiatives and recommendations
- If an attribute is not found in the content, use null
- Ensure all dates and numbers are accurately extracted

CONTENT SOURCE: {url_name}

CONTENT:
{markdown_content}
"""
        
        try:
            response = self.model.generate_content(prompt)
            data = json.loads(response.text)
            
            # Add metadata
            data['_metadata'] = {
                'source': url_name,
                'scraped_at': datetime.now().isoformat(),
                'content_length': len(markdown_content)
            }
            
            return data
        except Exception as e:
            print(f"Error extracting data with Gemini for {url_name}: {e}")
            return None
    
    def scrape_url(self, url_config):
        """
        Scrape a single URL and extract road accident data
        
        Args:
            url_config: Dictionary containing url, name, and description
            
        Returns:
            Extracted data dictionary
        """
        url = url_config['url']
        name = url_config['name']
        description = url_config['description']
        
        print(f"\n{'='*60}")
        print(f"Scraping: {description}")
        print(f"URL: {url}")
        print(f"{'='*60}")
        
        # Step 1: Fetch HTML
        print("📥 Fetching HTML...")
        html = self.fetch_html(url)
        if not html:
            print("❌ Failed to fetch HTML")
            return None
        
        # Step 2: Extract main content
        print("🔍 Extracting main content...")
        main_html = self.extract_main_content(html)
        if not main_html:
            print("❌ Failed to extract content")
            return None
        
        # Step 3: Convert to Markdown
        print("📝 Converting to Markdown...")
        markdown = self.html_to_markdown(main_html)
        if not markdown:
            print("❌ Failed to convert to Markdown")
            return None
        
        print(f"📊 Content size: {len(markdown)} characters")
        
        # Step 4: Extract data with Gemini
        print("🤖 Extracting data with Gemini AI...")
        data = self.extract_data_with_gemini(markdown, name)
        
        if data:
            print("✅ Data extracted successfully")
            # Save individual file
            output_file = os.path.join(OUTPUT_DIR, f"{name}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print(f"💾 Saved to: {output_file}")
        else:
            print("❌ Failed to extract data")
        
        return data
    
    def scrape_all(self, delay=2):
        """
        Scrape all configured URLs
        
        Args:
            delay: Delay between requests in seconds
            
        Returns:
            List of all extracted data
        """
        all_data = []
        
        print(f"\n🚀 Starting scraping of {len(TARGET_URLS)} sources...")
        print(f"⏱️  Delay between requests: {delay} seconds\n")
        
        for i, url_config in enumerate(TARGET_URLS, 1):
            print(f"\n[{i}/{len(TARGET_URLS)}]")
            
            data = self.scrape_url(url_config)
            if data:
                all_data.append(data)
            
            # Delay between requests (except for last one)
            if i < len(TARGET_URLS):
                print(f"\n⏳ Waiting {delay} seconds before next request...")
                time.sleep(delay)
        
        return all_data


def main():
    """
    Main execution function
    """
    print("\n" + "="*80)
    print("🚗 KENYA ROAD ACCIDENT DATA SCRAPER 🚗")
    print("="*80)
    print("\nUsing Gemini AI to extract road accident statistics and safety information")
    print("\n" + "="*80)
    
    # Initialize scraper
    # Set use_web_unlocker=True if you have a Web Unlocker API key
    scraper = RoadAccidentScraper(use_web_unlocker=False)
    
    # Scrape all URLs
    all_data = scraper.scrape_all(delay=3)
    
    # Summary
    print("\n" + "="*80)
    print("📊 SCRAPING SUMMARY")
    print("="*80)
    print(f"✅ Successfully scraped: {len(all_data)} out of {len(TARGET_URLS)} sources")
    print(f"📁 Output directory: {OUTPUT_DIR}/")
    print("\n" + "="*80)
    
    # Save aggregated data
    if all_data:
        from data_processor import DataProcessor
        processor = DataProcessor()
        processor.aggregate_data(all_data)
        print("\n✨ Data aggregation complete! Check the output directory for results.")
    else:
        print("\n⚠️  No data was successfully scraped. Check your API key and internet connection.")


if __name__ == "__main__":
    main()
