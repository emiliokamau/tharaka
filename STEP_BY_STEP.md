# ✅ STEP-BY-STEP INSTRUCTIONS

## 🎯 Your Goal: Extract Road Accident Data from PDF

### Current Status:
- ❌ Web scraping broken (403 errors)
- ❌ API key disabled (leaked)
- ✅ PDF with data ready
- ✅ Project fully set up

---

## 📋 STEP 1: Get a New API Key (5 minutes)

### Why This Step?
Your old API key was exposed and Google disabled it. You need a fresh one.

### How to Do It:

**Option A: Quick (Browser)**
1. Open this link in your browser:
   ```
   https://aistudio.google.com/apikey
   ```

2. You'll see Google AI Studio. Sign in if needed.

3. Click the **"Create API key"** or **"Get API key"** button

4. Select **"Create API key in new Google Cloud project"**

5. Your new key appears. It looks like: `AIzaSyD1a2b3c4d5e6...`

6. **Copy the entire key** (Ctrl+C or right-click)

7. **Keep it safe** - you'll need it in Step 2

**Option B: Visual Steps**
```
Google AI Studio
    ↓
[Create API key] button
    ↓
[Create API key in new project]
    ↓
Copy shown key
    ↓
✅ Done!
```

### What You Should Have:
- A long text string starting with `AIza...`
- Save this! You'll paste it in the next step.

---

## 🔧 STEP 2: Run the Setup Wizard (2 minutes)

### Why This Step?
The wizard will automatically:
- Verify your environment
- Update your .env file with the new key
- Test the API connection
- Prepare for PDF extraction

### How to Do It:

**On Windows (PowerShell):**

1. Open PowerShell
   - Press: `Windows Key + R`
   - Type: `powershell`
   - Press: Enter

2. Navigate to your project:
   ```powershell
   cd C:\Users\DIANNA\Documents\geminiscrapper
   ```

3. Run the wizard:
   ```powershell
   python setup_wizard.py
   ```

4. Follow the prompts:
   ```
   Step 1: Get a NEW Gemini API Key
   → Browser will open
   → Create key and copy it
   → Paste it when prompted
   
   Step 2: Update Your .env File
   → Automatic - wizard updates it
   
   Step 3: Verify Your Setup
   → Wizard checks everything
   
   Step 4: Choose Your PDF
   → Select option 3 (your current PDF)
   
   Step 5: Extract Data
   → Wizard runs extraction
   
   Step 6: View Results
   → Shows where data is saved
   ```

### What You Should See:
```
✅ .env file updated
✅ API key configured
✅ google-generativeai installed
✅ requests installed
✅ beautifulsoup4 installed
✅ markdownify installed
✅ ALL CHECKS PASSED
```

---

## 📄 STEP 3: Extract Data from PDF (5 minutes)

### Why This Step?
Extracts structured data from your PDF using Gemini AI.

### What the Wizard Will Do:

1. **Upload PDF to Gemini**
   - Your "Trend analysis..." PDF
   - Sent securely to Google
   - Processed by AI

2. **Analyze Content**
   - Identifies accident statistics
   - Extracts black spots
   - Finds causes and trends
   - Locates recommendations

3. **Generate JSON**
   - Structured data format
   - Ready for analysis
   - Saved to `extracted_data/` folder

### The Wizard Handles Everything
Just follow the on-screen prompts. The wizard will:
- ✅ Ask for your new API key
- ✅ Update your configuration
- ✅ Verify setup
- ✅ Extract from your PDF
- ✅ Show results

---

## 📊 STEP 4: Check Your Results (2 minutes)

### Where to Find Results:
```
Your Project Folder
└── extracted_data/
    ├── kenya_road_trends_2015_2020.json ← Your extracted data
    ├── summary_report.txt                  ← Human-readable summary
    └── ml_ready_data.json                  ← For ML models
```

### How to View the Data:

**Option 1: File Explorer**
1. Open File Explorer
2. Navigate to: `C:\Users\DIANNA\Documents\geminiscrapper\extracted_data\`
3. Double-click any `.json` file
4. Opens in your default text editor

**Option 2: Command Line**
```powershell
# View all extracted files
explorer extracted_data\

# Or open a specific file
notepad extracted_data\kenya_road_trends_2015_2020.json
```

### What You'll See:
```json
{
  "accident_statistics": {
    "total_accidents": 4000,
    "fatalities": 1500,
    "injuries": 2500,
    "years": {
      "2015": {...},
      "2016": {...},
      ...
    }
  },
  "black_spots": [
    "Thika Road near Exit 14",
    "Mombasa Road at Cabanas Junction",
    ...
  ],
  "causes": {
    "speeding": "45%",
    "drunk_driving": "25%",
    "poor_road_conditions": "20%",
    ...
  },
  "temporal_patterns": [
    "Peak accidents on weekends",
    "Higher fatalities during rainy season",
    ...
  ],
  "geographic_distribution": [
    "Urban areas: 60% of accidents",
    "Northern Corridor: 25% of fatalities",
    ...
  ],
  ...
}
```

---

## 🎓 STEP 5: Use the Data (Optional - Next Project Phase)

### What You Can Do With This Data:

**Build ML Models**
```python
import json

# Load your data
with open('extracted_data/kenya_road_trends_2015_2020.json') as f:
    data = json.load(f)

# Use for:
# - Predict accident risk by location/time
# - Classify high-risk areas
# - Forecast trends
```

**Create Visualizations**
```python
# Map black spots
# Plot accident trends
# Create heatmaps
# Generate reports
```

**Develop Applications**
```python
# Real-time alert system
# Mobile app for drivers
# Dashboard for authorities
# Data analytics platform
```

---

## 🆘 TROUBLESHOOTING

### Problem: "Failed to open PowerShell"
**Solution:**
1. Click Start menu
2. Search for "PowerShell"
3. Click "Windows PowerShell"
4. Paste command: `cd C:\Users\DIANNA\Documents\geminiscrapper`

### Problem: "python: command not found"
**Solution:**
Python might not be in PATH. Try:
```powershell
C:\Users\DIANNA\AppData\Local\Microsoft\WindowsApps\python3.11.exe setup_wizard.py
```

### Problem: "No such file or directory"
**Solution:**
Make sure you're in the right folder:
```powershell
# Check current location
Get-Location

# Navigate to correct folder
cd C:\Users\DIANNA\Documents\geminiscrapper

# Verify files exist
ls
```

### Problem: "Invalid API key"
**Solution:**
- Make sure you copied the ENTIRE key
- Check for extra spaces
- Try creating a new key again

### Problem: "PDF upload failed"
**Solution:**
- Check internet connection
- Try a smaller PDF first
- Wait a moment and try again

---

## ⏱️ TIMELINE

| Step | Action | Time |
|------|--------|------|
| 1 | Get new API key | 5 min |
| 2 | Run setup wizard | 2 min |
| 3 | Extract data | 5 min |
| 4 | Check results | 2 min |
| **Total** | **Complete setup** | **~14 min** |

---

## 📝 CHECKLIST

Before you start:
- [ ] You're in the correct folder
- [ ] PowerShell is open
- [ ] You have internet connection

While you're at Step 1:
- [ ] API key link opened
- [ ] Signed into Google account
- [ ] New key created
- [ ] Key copied to clipboard

After wizard completes:
- [ ] Check PowerShell shows ✅ messages
- [ ] `extracted_data/` folder exists
- [ ] JSON files were created
- [ ] Data looks reasonable

---

## 🚀 READY TO START?

### Run This Command:
```powershell
python setup_wizard.py
```

### Then:
1. Click the link when prompted (or go to https://aistudio.google.com/apikey)
2. Create your new API key
3. Copy it
4. Paste it in PowerShell when asked
5. Follow the remaining prompts
6. **Done!** Your data will be extracted

---

## 📞 HELP & SUPPORT

- **Can't open PowerShell?** → Google "how to open PowerShell on Windows"
- **Can't find the folder?** → Look in Documents > geminiscrapper
- **Key creation failed?** → Try in a different browser
- **Extraction failed?** → Check internet connection, try again
- **Need more help?** → Read `PDF_EXTRACTION_GUIDE.md` or `SWITCH_TO_PDF.md`

---

## ✨ YOU'VE GOT THIS!

This is the final piece to get your road accident data extracted and ready for your AI project.

**Start with:**
```powershell
python setup_wizard.py
```

**Good luck! 🚗💨**
