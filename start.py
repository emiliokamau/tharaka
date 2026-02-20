"""
Quick Start CLI - Interactive setup and execution helper
"""
import os
import sys


def print_header():
    """Print welcome header"""
    print("\n" + "="*70)
    print("🚗 KENYA ROAD ACCIDENT DATA SCRAPER - QUICK START 🚗")
    print("="*70)


def check_env_file():
    """Check if .env file exists and has API key"""
    if not os.path.exists(".env"):
        print("\n⚠️  .env file not found!")
        print("\nTo get started:")
        print("1. Copy .env.example to .env")
        print("2. Get your Gemini API key from: https://aistudio.google.com/apikey")
        print("3. Add the key to .env file")
        print("\nRun this command to copy the file:")
        print("   Copy-Item .env.example .env")
        return False
    
    # Check if API key is set
    with open(".env", "r") as f:
        content = f.read()
        if "GEMINI_API_KEY=" not in content or content.count("GEMINI_API_KEY=\n") > 0:
            print("\n⚠️  Gemini API key not configured!")
            print("\nSteps to configure:")
            print("1. Get your API key: https://aistudio.google.com/apikey")
            print("2. Open .env file")
            print("3. Replace 'GEMINI_API_KEY=' with 'GEMINI_API_KEY=your_actual_key'")
            print("\nSee GETTING_API_KEY.md for detailed instructions")
            return False
    
    return True


def main_menu():
    """Display main menu and handle user choice"""
    print("\n" + "-"*70)
    print("What would you like to do?")
    print("-"*70)
    print("\n1. 🔍 Check Setup (verify environment)")
    print("2. 🚀 Start Scraping (scrape all URLs)")
    print("3. 📚 View Examples (see usage patterns)")
    print("4. 📖 View Documentation (open README)")
    print("5. 🔑 API Key Guide (get help with API key)")
    print("6. 📁 View Scraped Data (if available)")
    print("7. ❌ Exit")
    
    choice = input("\nEnter your choice (1-7): ").strip()
    return choice


def run_check_setup():
    """Run setup verification"""
    print("\n" + "="*70)
    print("Running setup verification...")
    print("="*70)
    os.system("python check_setup.py")


def run_scraper():
    """Run the main scraper"""
    print("\n" + "="*70)
    print("Starting web scraper...")
    print("="*70)
    print("\n⏱️  This may take several minutes depending on the number of URLs")
    print("📊 Progress will be shown for each source\n")
    
    confirm = input("Continue? (y/n): ").strip().lower()
    if confirm == 'y':
        os.system("python scraper.py")
    else:
        print("Cancelled.")


def run_examples():
    """Run examples script"""
    print("\n" + "="*70)
    print("Running usage examples...")
    print("="*70)
    os.system("python examples.py")


def view_readme():
    """Display README info"""
    print("\n" + "="*70)
    print("📖 Documentation Files:")
    print("="*70)
    print("\n1. README.md - Main documentation")
    print("2. GETTING_API_KEY.md - API key setup guide")
    print("3. PROJECT_STRUCTURE.md - Project overview")
    print("\nOpen these files in your text editor or run:")
    print("   notepad README.md")


def view_api_guide():
    """Display API key guide"""
    print("\n" + "="*70)
    print("🔑 Getting Your Gemini API Key")
    print("="*70)
    print("\n1. Visit: https://aistudio.google.com/apikey")
    print("2. Sign in with your Google account")
    print("3. Click 'Get API key' → 'Create API key'")
    print("4. Copy the key (starts with 'AIza...')")
    print("5. Add it to your .env file")
    print("\n💡 The key is FREE and gives you:")
    print("   • 1,500 requests per day")
    print("   • 1 million tokens per minute")
    print("\nFor detailed instructions, see: GETTING_API_KEY.md")


def view_scraped_data():
    """Show scraped data directory"""
    if os.path.exists("scraped_data"):
        print("\n" + "="*70)
        print("📁 Scraped Data Files:")
        print("="*70 + "\n")
        
        files = os.listdir("scraped_data")
        if files:
            for i, file in enumerate(files, 1):
                file_path = os.path.join("scraped_data", file)
                size = os.path.getsize(file_path)
                print(f"{i}. {file} ({size:,} bytes)")
            
            print("\n💡 To view a file, open it in your text editor or run:")
            print("   notepad scraped_data\\filename.json")
        else:
            print("No files found. Run the scraper first (option 2).")
    else:
        print("\n⚠️  scraped_data directory not found.")
        print("Run the scraper first (option 2) to generate data.")


def main():
    """Main execution function"""
    print_header()
    
    # Check if .env is configured
    if not check_env_file():
        print("\n" + "="*70)
        input("\nPress Enter to exit...")
        return
    
    while True:
        choice = main_menu()
        
        if choice == "1":
            run_check_setup()
        elif choice == "2":
            run_scraper()
        elif choice == "3":
            run_examples()
        elif choice == "4":
            view_readme()
        elif choice == "5":
            view_api_guide()
        elif choice == "6":
            view_scraped_data()
        elif choice == "7":
            print("\n👋 Thanks for using Kenya Road Accident Scraper!")
            print("🚗 Stay safe on the roads!\n")
            break
        else:
            print("\n❌ Invalid choice. Please enter 1-7.")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
