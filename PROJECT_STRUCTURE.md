# 📁 Project Structure

```
geminiscrapper/
│
├── 📄 scraper.py                          # Main scraper with Gemini integration
├── 📄 config.py                           # Configuration (URLs, API keys, settings)
├── 📄 data_processor.py                   # Data aggregation and analysis
├── 📄 check_setup.py                      # Setup verification script
├── 📄 examples.py                         # Usage examples
│
├── 📄 requirements.txt                    # Python dependencies
├── 📄 .env                                # Your API keys (DO NOT COMMIT!)
├── 📄 .env.example                        # Template for .env file
├── 📄 .gitignore                          # Git ignore rules
│
├── 📖 README.md                           # Main documentation
├── 📖 GETTING_API_KEY.md                  # API key setup guide
├── 📖 PROJECT_STRUCTURE.md                # This file
│
├── 📁 .venv/                              # Virtual environment (auto-created)
│
└── 📁 scraped_data/                       # Output directory (created on first run)
    ├── tanzania_online_study.json         # Individual source data
    ├── kenya_road_safety_plan.json        # Individual source data
    ├── ...                                # More source files
    ├── road_accident_data_aggregated.json # Combined data from all sources
    ├── summary_report.txt                 # Human-readable summary
    └── ml_ready_data.json                 # ML-formatted data
```

## 📄 File Descriptions

### Core Files

#### `scraper.py`
The main scraping engine. Contains:
- `RoadAccidentScraper` class
- Methods for fetching HTML, converting to Markdown
- Gemini AI integration for data extraction
- Multi-URL scraping with progress tracking

**Key Functions**:
- `fetch_html()` - Downloads web pages
- `extract_main_content()` - Finds relevant content
- `html_to_markdown()` - Converts HTML to Markdown (95% token savings!)
- `extract_data_with_gemini()` - Uses AI to extract structured data
- `scrape_all()` - Scrapes all configured URLs

#### `config.py`
Central configuration file. Contains:
- API keys (loaded from .env)
- Target URLs for scraping
- Data extraction attributes
- Gemini model settings
- CSS selectors for content extraction

**To modify**:
- Add new URLs to `TARGET_URLS` list
- Change extraction attributes in `EXTRACTION_ATTRIBUTES`
- Adjust Gemini model in `GEMINI_MODEL`

#### `data_processor.py`
Processes and aggregates scraped data. Contains:
- `DataProcessor` class
- Data aggregation from multiple sources
- Summary report generation
- ML-ready data export

**Key Functions**:
- `aggregate_data()` - Combines data from all sources
- `generate_summary_report()` - Creates readable summary
- `export_for_ml()` - Exports data for machine learning

### Utility Files

#### `check_setup.py`
Verifies your environment is configured correctly:
- ✅ Checks if .env file exists
- ✅ Validates Gemini API key
- ✅ Tests all dependencies
- ✅ Verifies Gemini API connection

**Run**: `python check_setup.py`

#### `examples.py`
Demonstrates different usage patterns:
- Example 1: Scrape a single URL
- Example 2: Scrape custom URLs
- Example 3: Use Web Unlocker
- Example 4: Process and aggregate data

**Run**: `python examples.py`

### Configuration Files

#### `.env`
Your private configuration file containing:
- `GEMINI_API_KEY` - Your Gemini API key (required)
- `WEB_UNLOCKER_API_KEY` - Optional, for bypassing blocks

**⚠️ NEVER commit this file to Git!**

#### `.env.example`
Template for `.env` file. Copy this to `.env` and add your keys.

#### `.gitignore`
Prevents sensitive files from being committed:
- `.env` (API keys)
- `scraped_data/` (scraped content)
- `__pycache__/` (Python cache)
- `.venv/` (virtual environment)

### Documentation Files

#### `README.md`
Complete guide covering:
- Project purpose and features
- Installation instructions
- Usage examples
- Configuration options
- Troubleshooting

#### `GETTING_API_KEY.md`
Step-by-step guide to:
- Get a free Gemini API key
- Add it to your project
- Verify it works
- Security best practices

## 🔄 Data Flow

```
1. Target URLs (config.py)
   ↓
2. Fetch HTML (scraper.py)
   ↓
3. Extract main content (Beautiful Soup)
   ↓
4. Convert to Markdown (markdownify) → 95% token reduction!
   ↓
5. Extract structured data (Gemini AI)
   ↓
6. Save individual JSON files (scraped_data/)
   ↓
7. Aggregate all data (data_processor.py)
   ↓
8. Generate reports (summary_report.txt)
   ↓
9. Export for ML (ml_ready_data.json)
```

## 🎯 Usage Workflow

### First Time Setup
```bash
1. cd C:\Users\DIANNA\Documents\geminiscrapper
2. Get Gemini API key from https://aistudio.google.com/apikey
3. Add key to .env file
4. python check_setup.py  # Verify everything works
```

### Regular Usage
```bash
1. python scraper.py      # Scrape all URLs
2. Check scraped_data/    # View results
3. Read summary_report.txt # See insights
```

### Custom Scraping
```bash
1. Edit config.py         # Add your URLs
2. python scraper.py      # Run scraper
3. python examples.py     # See usage patterns
```

## 📊 Output Files Explained

### Individual Source Files
Example: `kenya_road_safety_plan.json`
```json
{
  "accident_statistics": {...},
  "black_spots": [...],
  "causes": [...],
  "_metadata": {
    "source": "kenya_road_safety_plan",
    "scraped_at": "2026-02-20T10:30:00"
  }
}
```

### Aggregated Data
`road_accident_data_aggregated.json`
- Combines data from ALL sources
- Includes metadata about sources
- Ready for analysis

### Summary Report
`summary_report.txt`
- Human-readable format
- Key statistics
- Top black spots
- Main causes
- Recommendations

### ML-Ready Data
`ml_ready_data.json`
- Formatted for machine learning
- Organized by feature types
- Clean, structured format

## 🔧 Customization Guide

### Add New URLs
Edit [config.py](config.py):
```python
TARGET_URLS.append({
    "url": "https://example.com/road-data",
    "name": "example_source",
    "description": "Example road data source"
})
```

### Change Extraction Attributes
Edit [config.py](config.py):
```python
EXTRACTION_ATTRIBUTES = """
your_custom_attribute,
another_attribute,
specific_data_point
"""
```

### Adjust Scraping Delay
Edit [scraper.py](scraper.py):
```python
scraper.scrape_all(delay=5)  # 5 seconds between requests
```

### Use Different Gemini Model
Edit [config.py](config.py):
```python
GEMINI_MODEL = "gemini-1.5-pro"  # More powerful
# or
GEMINI_MODEL = "gemini-2.0-flash-lite"  # Fast and free (default)
```

## 🚀 Next Steps

After scraping data, you can:

1. **Build Predictive Models**
   - Use scikit-learn or TensorFlow
   - Predict accident likelihood
   - Identify risk patterns

2. **Create Dashboards**
   - Visualize black spots on maps
   - Track trends over time
   - Monitor safety initiatives

3. **Implement Alert Systems**
   - Real-time risk alerts
   - SMS/USSD notifications
   - Mobile app integration

4. **Policy Analysis**
   - Evaluate intervention effectiveness
   - Resource allocation optimization
   - Evidence-based recommendations

## 📞 Support

- **Setup issues**: Check [README.md](README.md) troubleshooting section
- **API key problems**: See [GETTING_API_KEY.md](GETTING_API_KEY.md)
- **Scraping errors**: Run `python check_setup.py` first

---

**Built to make Kenyan roads safer through AI-powered insights! 🚗💨**
