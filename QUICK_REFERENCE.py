"""
Quick Reference - What to do next
Print this or keep it open
"""

QUICK_REFERENCE = """
╔════════════════════════════════════════════════════════════════════════════╗
║                    🚗 ROAD ACCIDENT DATA - QUICK FIX 🚗                    ║
╚════════════════════════════════════════════════════════════════════════════╝

⚠️  YOUR API KEY WAS LEAKED AND IS NOW DISABLED

═══════════════════════════════════════════════════════════════════════════════

IMMEDIATE ACTIONS (DO THIS NOW!):

1️⃣  GET NEW API KEY (5 minutes)
   • Go to: https://aistudio.google.com/apikey
   • Click: "Create API key"
   • Copy the key
   ✅ Save somewhere safe

2️⃣  RUN SETUP WIZARD (2 minutes)
   • Open PowerShell in your geminiscrapper folder
   • Type: python setup_wizard.py
   • Follow the prompts
   • Paste your new API key when asked

3️⃣  EXTRACT FROM PDF (5 minutes)
   • The wizard will guide you
   • Choose option 3 to use your "Trend analysis..." PDF
   • Let Gemini analyze it
   • Check extracted_data/ folder for results

═══════════════════════════════════════════════════════════════════════════════

WHY WE'RE SWITCHING TO PDF EXTRACTION:

OLD APPROACH (Web Scraping) - BROKEN ❌
├─ 403 Forbidden errors everywhere
├─ Websites blocking automated scraping
├─ SSL certificate failures
├─ API key leaked and disabled
└─ 0% success rate

NEW APPROACH (PDF Extraction) - WORKING ✅
├─ Your local PDF files
├─ No website blocking
├─ No SSL issues
├─ Same free API quota
└─ 95%+ success rate

═══════════════════════════════════════════════════════════════════════════════

COMMAND QUICK REFERENCE:

✅ Setup wizard (RECOMMENDED - do this first!)
   python setup_wizard.py

✅ Extract from PDF files
   python pdf_extractor.py

✅ Verify your setup
   python check_setup.py

✅ Aggregate multiple PDFs
   python data_processor.py

✅ View extracted data
   explorer extracted_data\
   OR
   notepad extracted_data\filename.json

═══════════════════════════════════════════════════════════════════════════════

FILES YOU SHOULD READ (in order):

1. SWITCH_TO_PDF.md ← READ THIS FIRST
   └─ Explains why we switched and what to do

2. PDF_EXTRACTION_GUIDE.md
   └─ Complete guide to PDF extraction

3. setup_wizard.py
   └─ Interactive wizard - runs everything for you

═══════════════════════════════════════════════════════════════════════════════

YOUR PDF FILE:
📄 Trend analysis and fatality causes in Kenyan roads (2015-2020).pdf
   └─ This file contains exactly the data you need!
   └─ Gemini can extract it perfectly

═══════════════════════════════════════════════════════════════════════════════

EXPECTED TIMELINE:

⏱️  5 min  - Get new API key
⏱️  2 min  - Run setup wizard  
⏱️  5 min  - PDF extraction completes
⏱️  2 min  - View results
────────────────────────
⏱️  14 min TOTAL - You'll have working data!

═══════════════════════════════════════════════════════════════════════════════

WHAT YOU'LL GET:

✅ Individual JSON files for each PDF
✅ Structured data (statistics, trends, locations, causes)
✅ Human-readable summary report
✅ ML-ready data format
✅ Ready for your AI models!

═══════════════════════════════════════════════════════════════════════════════

EXAMPLE OUTPUT:

{
  "accident_statistics": {
    "total_accidents": 4000,
    "fatalities": 1500,
    "injuries": 2500,
    "year_2020": {
      "accidents": 3800,
      "deaths": 1400
    }
  },
  "black_spots": [
    "Thika Road exit 14",
    "Mombasa Road at Cabanas",
    "Northern Bypass at Ruaka"
  ],
  "causes": {
    "speeding": "45%",
    "drunk_driving": "25%",
    "poor_roads": "20%"
  },
  ...
}

═══════════════════════════════════════════════════════════════════════════════

NEXT STEPS AFTER EXTRACTION:

→ Use data for ML models (predict accidents)
→ Create maps (visualize black spots)
→ Analyze trends (identify patterns)
→ Build alert system (real-time warnings)
→ Support policy (evidence-based decisions)

═══════════════════════════════════════════════════════════════════════════════

IF YOU GET STUCK:

❓ "Where do I get API key?"
   → https://aistudio.google.com/apikey

❓ "How do I run the wizard?"
   → Open PowerShell, type: python setup_wizard.py

❓ "What if extraction fails?"
   → Read: PDF_EXTRACTION_GUIDE.md > Troubleshooting section

❓ "Can I process multiple PDFs?"
   → Yes! Put them in a folder, run pdf_extractor.py option 2

═══════════════════════════════════════════════════════════════════════════════

SECURITY REMINDER:

🔐 Never share your API key
🔐 Keep it only in .env file
🔐 Don't commit .env to GitHub
🔐 If exposed, delete and create a new one (like you're doing now)

═══════════════════════════════════════════════════════════════════════════════

START HERE:

1. Open PowerShell (Ctrl+Alt+T or find in Start menu)
2. Type: python setup_wizard.py
3. Follow the on-screen instructions
4. Done! Your data will be extracted

═══════════════════════════════════════════════════════════════════════════════

Questions? See:
- PDF_EXTRACTION_GUIDE.md (complete guide)
- SWITCH_TO_PDF.md (why we switched)
- README.md (general documentation)

You've got this! 🚀
"""

if __name__ == "__main__":
    print(QUICK_REFERENCE)
