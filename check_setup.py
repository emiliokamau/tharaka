"""
Quick start script to test the setup
"""
import os
from dotenv import load_dotenv

def check_setup():
    """Check if the environment is properly configured"""
    
    print("\n" + "="*60)
    print("🔍 CHECKING SETUP")
    print("="*60 + "\n")
    
    # Check if .env exists
    if os.path.exists(".env"):
        print("✅ .env file found")
    else:
        print("❌ .env file not found - please create it from .env.example")
        return False
    
    # Load environment variables
    load_dotenv()
    
    # Check Gemini API key
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key and api_key.strip() and api_key != "your_gemini_api_key_here":
        print(f"✅ Gemini API key configured (kept private for security)")
    else:
        print("❌ Gemini API key not configured")
        print("   Please add your API key to the .env file")
        print("   Get one at: https://aistudio.google.com/apikey")
        return False
    
    # Check required modules
    try:
        import google.generativeai as genai
        print("✅ google-generativeai installed")
    except ImportError:
        print("❌ google-generativeai not installed")
        return False
    
    try:
        import requests
        print("✅ requests installed")
    except ImportError:
        print("❌ requests not installed")
        return False
    
    try:
        from bs4 import BeautifulSoup
        print("✅ beautifulsoup4 installed")
    except ImportError:
        print("❌ beautifulsoup4 not installed")
        return False
    
    try:
        from markdownify import markdownify
        print("✅ markdownify installed")
    except ImportError:
        print("❌ markdownify not installed")
        return False
    
    # Test Gemini connection
    print("\n🔗 Testing Gemini API connection...")
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        response = model.generate_content("Say 'Hello, I'm ready for web scraping!'")
        print(f"✅ Gemini API working! Response: {response.text[:50]}...")
    except Exception as e:
        print(f"❌ Gemini API error: {e}")
        return False
    
    print("\n" + "="*60)
    print("✅ ALL CHECKS PASSED - READY TO SCRAPE!")
    print("="*60)
    print("\nNext steps:")
    print("1. Run: python scraper.py")
    print("2. Check output in scraped_data/ folder")
    print("\n")
    
    return True

if __name__ == "__main__":
    check_setup()
