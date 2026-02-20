"""
PDF Data Extractor using Gemini AI
Extract road accident data from local PDF files instead of web scraping
"""
import google.generativeai as genai
import os
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OUTPUT_DIR = "extracted_data"
GEMINI_MODEL = "gemini-2.0-flash-lite"

# Data extraction attributes
EXTRACTION_ATTRIBUTES = """
accident_statistics (number of accidents, fatalities, injuries by year/month/location),
black_spots (high-risk locations, roads, intersections),
causes (human factors, vehicle factors, environmental factors, percentages),
temporal_patterns (peak times, seasonal variations, trends, year-over-year changes),
geographic_distribution (regions, counties, urban vs rural, specific roads),
safety_initiatives (government plans, interventions, policies, programs),
recommendations (proposed solutions, infrastructure improvements, policy changes),
target_goals (reduction targets, policy objectives, timeline),
key_findings (important insights, conclusions, research results, statistics),
data_sources (where the data came from, time period covered)
"""


class PDFDataExtractor:
    """
    Extract road accident data from PDF files using Gemini AI
    """
    
    def __init__(self):
        """Initialize the PDF extractor"""
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found. Please set it in your .env file")
        
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(
            GEMINI_MODEL,
            generation_config={"response_mime_type": "application/json"}
        )
        
        # Create output directory
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
    
    def extract_from_pdf(self, pdf_path, output_name=None):
        """
        Extract data from a PDF file using Gemini
        
        Args:
            pdf_path: Path to the PDF file
            output_name: Optional custom name for output file
            
        Returns:
            Extracted data as dictionary
        """
        if not os.path.exists(pdf_path):
            print(f"❌ PDF file not found: {pdf_path}")
            return None
        
        print(f"\n{'='*70}")
        print(f"📄 Processing: {os.path.basename(pdf_path)}")
        print(f"{'='*70}")
        
        # Upload PDF to Gemini
        print("📤 Uploading PDF to Gemini...")
        try:
            uploaded_file = genai.upload_file(pdf_path)
            print(f"✅ Upload complete: {uploaded_file.name}")
        except Exception as e:
            print(f"❌ Upload failed: {e}")
            return None
        
        # Create prompt for data extraction
        prompt = f"""You are an AI assistant specialized in extracting road accident and safety data from Kenyan documents.

Analyze this PDF document and extract comprehensive road accident data.

Focus on:
- Accident statistics (numbers, trends, changes over time)
- Geographic information (locations, roads, regions, black spots)
- Causes and contributing factors with percentages if available
- Temporal patterns and trends
- Safety initiatives and recommendations
- Key findings and insights

Respond with a raw string in JSON format containing the scraped data in the specified attributes:

JSON ATTRIBUTES:
{EXTRACTION_ATTRIBUTES}

IMPORTANT INSTRUCTIONS:
- Extract ALL numerical data (statistics, fatalities, injuries, accident counts, percentages)
- Identify specific locations, roads, counties, and black spots mentioned
- Extract temporal patterns (years, months, dates, time periods, trends)
- Capture causes and contributing factors with their percentages if available
- Include government initiatives, policies, and recommendations
- Extract key findings, conclusions, and research insights
- Note the time period the data covers
- If an attribute is not found in the document, use null
- Be as comprehensive as possible - this data is critical for AI prediction models

Analyze the PDF now and extract all relevant road accident data."""

        # Extract data using Gemini
        print("🤖 Analyzing PDF with Gemini AI...")
        try:
            response = self.model.generate_content([uploaded_file, prompt])
            data = json.loads(response.text)
            
            # Add metadata
            data['_metadata'] = {
                'source_file': os.path.basename(pdf_path),
                'source_path': pdf_path,
                'extracted_at': datetime.now().isoformat(),
                'extraction_method': 'gemini_pdf_analysis'
            }
            
            print("✅ Data extraction successful!")
            
            # Save to file
            if not output_name:
                output_name = Path(pdf_path).stem.replace(' ', '_').lower()
            
            output_file = os.path.join(OUTPUT_DIR, f"{output_name}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            
            print(f"💾 Saved to: {output_file}")
            
            # Print summary
            self._print_summary(data)
            
            return data
            
        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            return None
    
    def extract_from_multiple_pdfs(self, pdf_directory):
        """
        Extract data from all PDFs in a directory
        
        Args:
            pdf_directory: Path to directory containing PDF files
            
        Returns:
            List of all extracted data
        """
        if not os.path.exists(pdf_directory):
            print(f"❌ Directory not found: {pdf_directory}")
            return []
        
        # Find all PDF files
        pdf_files = list(Path(pdf_directory).glob("*.pdf"))
        
        if not pdf_files:
            print(f"❌ No PDF files found in: {pdf_directory}")
            return []
        
        print(f"\n🚀 Found {len(pdf_files)} PDF file(s) to process")
        
        all_data = []
        for i, pdf_path in enumerate(pdf_files, 1):
            print(f"\n[{i}/{len(pdf_files)}]")
            data = self.extract_from_pdf(str(pdf_path))
            if data:
                all_data.append(data)
        
        return all_data
    
    def _print_summary(self, data):
        """Print a quick summary of extracted data"""
        print("\n" + "-"*70)
        print("📊 EXTRACTION SUMMARY")
        print("-"*70)
        
        # Accident statistics
        if data.get('accident_statistics'):
            print(f"✅ Accident Statistics: Found")
        
        # Black spots
        if data.get('black_spots'):
            count = len(data['black_spots']) if isinstance(data['black_spots'], list) else 1
            print(f"✅ Black Spots: {count} identified")
        
        # Causes
        if data.get('causes'):
            count = len(data['causes']) if isinstance(data['causes'], list) else 1
            print(f"✅ Causes: {count} identified")
        
        # Key findings
        if data.get('key_findings'):
            count = len(data['key_findings']) if isinstance(data['key_findings'], list) else 1
            print(f"✅ Key Findings: {count} points")
        
        print("-"*70)


def main():
    """Main execution function"""
    print("\n" + "="*80)
    print("📄 KENYA ROAD ACCIDENT DATA - PDF EXTRACTOR")
    print("="*80)
    print("\nExtract data from local PDF files using Gemini AI")
    print("No web scraping needed - works with downloaded documents!")
    print("\n" + "="*80)
    
    extractor = PDFDataExtractor()
    
    print("\n🔍 Options:")
    print("1. Extract from a single PDF file")
    print("2. Extract from all PDFs in a directory")
    print("3. Process current PDF (Trend analysis... in current folder)")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        pdf_path = input("\nEnter PDF file path: ").strip().strip('"')
        extractor.extract_from_pdf(pdf_path)
    
    elif choice == "2":
        pdf_dir = input("\nEnter directory path: ").strip().strip('"')
        all_data = extractor.extract_from_multiple_pdfs(pdf_dir)
        
        if all_data:
            print(f"\n✅ Successfully extracted data from {len(all_data)} PDF(s)")
            print(f"📁 Output directory: {OUTPUT_DIR}/")
    
    elif choice == "3":
        # Look for the PDF in current directory
        current_dir = os.getcwd()
        pdf_files = list(Path(current_dir).glob("Trend analysis*.pdf"))
        
        if pdf_files:
            pdf_path = pdf_files[0]
            print(f"\n📄 Found: {pdf_path.name}")
            extractor.extract_from_pdf(str(pdf_path), "kenya_road_trends_2015_2020")
        else:
            print("\n❌ PDF file not found in current directory")
            print("Please place your PDF files here or choose option 1 or 2")
    
    else:
        print("❌ Invalid choice")
    
    print("\n" + "="*80)
    print("✅ EXTRACTION COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
