"""
Interactive setup wizard for PDF extraction
Guides you through the process step-by-step
"""
import os
import json
import webbrowser
from pathlib import Path


def print_banner():
    """Print welcome banner"""
    print("\n" + "="*80)
    print("🚗 KENYA ROAD ACCIDENT DATA - PDF EXTRACTION SETUP WIZARD 🚗")
    print("="*80)


def step1_api_key():
    """Step 1: Get new API key"""
    print("\n" + "-"*80)
    print("STEP 1: GET A NEW GEMINI API KEY")
    print("-"*80)
    
    print("""
⚠️  Your old API key was exposed and disabled by Google.

You need to create a NEW API key immediately.

Steps:
1. Click the link below (or visit: https://aistudio.google.com/apikey)
2. Sign in with your Google account
3. Click "Create API key"
4. Select "Create API key in new Google Cloud project"
5. Copy the NEW key
6. Come back here and paste it
    """)
    
    response = input("\nOpen Google AI Studio now? (y/n): ").strip().lower()
    
    if response == 'y':
        webbrowser.open('https://aistudio.google.com/apikey')
        print("\n✅ Browser opened! Create your key and come back here.")
    
    api_key = input("\nPaste your NEW API key here: ").strip()
    
    if api_key.startswith('AIza'):
        return api_key
    else:
        print("❌ Invalid API key format. Should start with 'AIza'")
        print("Please try again.")
        return step1_api_key()


def step2_update_env(api_key):
    """Step 2: Update .env file"""
    print("\n" + "-"*80)
    print("STEP 2: UPDATE YOUR .env FILE")
    print("-"*80)
    
    env_file = '.env'
    
    # Read current .env
    env_content = ""
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            env_content = f.read()
    
    # Update with new API key (DO NOT PRINT THE FULL KEY!)
    new_content = f"""# IMPORTANT: Replace with your actual API key
# ⚠️ NEVER expose this key - keep it in .env only!
GEMINI_API_KEY={api_key}

# Optional: Only needed if websites block your requests
WEB_UNLOCKER_API_KEY=
"""
    
    # Write updated .env
    with open(env_file, 'w') as f:
        f.write(new_content)
    
    print(f"\n✅ Updated .env file with your new API key")
    print(f"   ⚠️  Key is now stored safely in .env (NOT printed here for security)")


def step3_verify_setup():
    """Step 3: Verify setup"""
    print("\n" + "-"*80)
    print("STEP 3: VERIFY YOUR SETUP")
    print("-"*80)
    
    print("\nChecking your environment...")
    
    checks = []
    
    # Check .env file
    if os.path.exists('.env'):
        print("✅ .env file found")
        checks.append(True)
    else:
        print("❌ .env file not found")
        checks.append(False)
    
    # Check API key is set
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            content = f.read()
            if 'GEMINI_API_KEY=' in content and len(content.split('GEMINI_API_KEY=')[1].split('\n')[0].strip()) > 10:
                print("✅ API key configured")
                checks.append(True)
            else:
                print("❌ API key not configured properly")
                checks.append(False)
    
    # Check required packages
    try:
        import google.generativeai
        print("✅ google-generativeai installed")
        checks.append(True)
    except:
        print("❌ google-generativeai not installed")
        checks.append(False)
    
    try:
        import requests
        print("✅ requests installed")
        checks.append(True)
    except:
        print("❌ requests not installed")
        checks.append(False)
    
    if all(checks):
        print("\n✅ ALL CHECKS PASSED!")
        return True
    else:
        print("\n❌ Some checks failed. Please fix the issues above.")
        return False


def step4_choose_pdf():
    """Step 4: Choose PDF to extract"""
    print("\n" + "-"*80)
    print("STEP 4: CHOOSE YOUR PDF FILE")
    print("-"*80)
    
    print("\nOptions:")
    print("1. Use the 'Trend analysis...' PDF in current directory")
    print("2. Select a different PDF file")
    print("3. Process all PDFs in a folder")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == '1':
        # Look for the Trend analysis PDF
        pdf_files = list(Path('.').glob('Trend analysis*.pdf'))
        if pdf_files:
            print(f"\n✅ Found: {pdf_files[0].name}")
            return str(pdf_files[0])
        else:
            print("❌ PDF not found in current directory")
            return step4_choose_pdf()
    
    elif choice == '2':
        pdf_path = input("\nEnter PDF file path: ").strip().strip('"')
        if os.path.exists(pdf_path):
            print(f"\n✅ Found: {pdf_path}")
            return pdf_path
        else:
            print("❌ File not found")
            return step4_choose_pdf()
    
    elif choice == '3':
        folder_path = input("\nEnter folder path: ").strip().strip('"')
        if os.path.exists(folder_path):
            pdf_files = list(Path(folder_path).glob('*.pdf'))
            print(f"\n✅ Found {len(pdf_files)} PDF file(s)")
            return folder_path
        else:
            print("❌ Folder not found")
            return step4_choose_pdf()
    
    else:
        print("❌ Invalid choice")
        return step4_choose_pdf()


def step5_extract():
    """Step 5: Run extraction"""
    print("\n" + "-"*80)
    print("STEP 5: EXTRACT DATA")
    print("-"*80)
    
    print("""
Ready to extract! This may take a few minutes.

What to expect:
1. PDF will be uploaded to Gemini
2. AI will analyze the content
3. Data will be extracted and organized
4. Results will be saved to 'extracted_data/' folder

⏱️  Large PDFs (200+ pages) may take 30-60 seconds.
    
""")
    
    response = input("Continue with extraction? (y/n): ").strip().lower()
    
    if response == 'y':
        print("\n🚀 Starting extraction...")
        os.system('python pdf_extractor.py')
        return True
    else:
        print("\n⏸️  Extraction cancelled")
        return False


def step6_results():
    """Step 6: Show results"""
    print("\n" + "-"*80)
    print("STEP 6: VIEW RESULTS")
    print("-"*80)
    
    output_dir = 'extracted_data'
    
    if os.path.exists(output_dir):
        files = os.listdir(output_dir)
        json_files = [f for f in files if f.endswith('.json')]
        
        if json_files:
            print(f"\n✅ Extraction successful! Found {len(json_files)} file(s):\n")
            for i, file in enumerate(json_files, 1):
                file_path = os.path.join(output_dir, file)
                size = os.path.getsize(file_path)
                print(f"   {i}. {file} ({size:,} bytes)")
            
            print(f"\n📁 Location: {os.path.abspath(output_dir)}/")
            print("\n💡 Next steps:")
            print("   1. Open a JSON file in your text editor to view the data")
            print("   2. Use data_processor.py to aggregate multiple PDFs")
            print("   3. Use your data for AI/ML models")
        else:
            print("\n⚠️  No JSON files found in extracted_data/")
    else:
        print("\n⚠️  extracted_data/ folder not found")


def main():
    """Main wizard function"""
    print_banner()
    
    print("""
This wizard will help you:
1. Get a new Gemini API key (your old one is disabled)
2. Update your configuration
3. Verify everything works
4. Extract data from your PDF files
    """)
    
    # Step 1: Get API key
    print("\nStarting setup wizard...")
    api_key = step1_api_key()
    
    # Step 2: Update .env
    step2_update_env(api_key)
    
    # Step 3: Verify setup
    if not step3_verify_setup():
        print("\n❌ Setup verification failed. Please fix the issues and try again.")
        return
    
    # Step 4: Choose PDF
    pdf_selection = step4_choose_pdf()
    
    # Step 5: Extract
    if step5_extract():
        # Step 6: Show results
        step6_results()
    
    # Final message
    print("\n" + "="*80)
    print("✅ SETUP WIZARD COMPLETE!")
    print("="*80)
    print("""
What to do next:

1. View your extracted data:
   - Open: extracted_data/
   - Open any .json file in your text editor
   
2. Process multiple PDFs:
   - Put PDFs in a folder
   - Run: python pdf_extractor.py
   - Choose option 2
   
3. Use the data:
   - For ML models
   - For visualization
   - For analysis

4. Need help?
   - Read: PDF_EXTRACTION_GUIDE.md
   - Read: ALTERNATIVE_SOLUTION.md

Good luck with your road safety AI project! 🚗💨
    """)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
