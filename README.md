# 🚗 Kenya Road Accident Data Scraper with Gemini AI

An AI-powered web scraper that uses Google's Gemini to extract road accident statistics and safety information from multiple Kenyan data sources. This tool is designed to support AI-driven solutions for predicting and responding to road accidents in Kenya.

## 🎯 Purpose

This scraper helps gather data to:
- **Predict road accidents** using historical patterns
- **Identify black spots** (high-risk locations)
- **Analyze accident causes** (human, vehicle, environmental factors)
- **Track safety initiatives** and policy effectiveness
- **Enable real-time risk alerts** based on data patterns

## 📊 Data Sources

The scraper targets the following Kenyan road safety sources:
- Tanzania Online Journal (Academic research)
- Varsani Brake Linings (Road Safety Action Plan 2024-2028)
- Streamline Feed (Black spots and safety plans)
- TTC Africa (Northern Corridor accidents)
- Kenya National Bureau of Statistics (KNBS)
- JKUAT Research Repository

## 🚀 Features

✅ **AI-Powered Extraction**: Uses Gemini to intelligently extract structured data  
✅ **Multi-Source Scraping**: Scrapes multiple websites automatically  
✅ **Token Optimization**: Converts HTML to Markdown to reduce API costs by ~95%  
✅ **Anti-Scraping Support**: Optional Web Unlocker integration  
✅ **Data Aggregation**: Combines data from all sources into unified format  
✅ **ML-Ready Output**: Exports data in formats suitable for machine learning  
✅ **Detailed Reports**: Generates human-readable summary reports  

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- Google Gemini API key ([Get one here](https://aistudio.google.com/apikey))

### Step 1: Clone/Setup Project
```powershell
cd C:\Users\DIANNA\Documents\geminiscrapper
```

### Step 2: Activate Virtual Environment
```powershell
.venv\Scripts\activate
```

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Configure API Key
1. Copy `.env.example` to `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```

2. Edit `.env` and add your Gemini API key:
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```

   To get a Gemini API key:
   - Go to [Google AI Studio](https://aistudio.google.com/apikey)
   - Sign in with your Google account
   - Click "Get API Key" → "Create API Key"
   - Copy the key and paste it in your `.env` file

## 🔧 Usage

### Basic Scraping
Run the scraper to extract data from all configured sources:

```powershell
python scraper.py
```

This will:
1. Fetch HTML from each URL
2. Extract main content
3. Convert to Markdown (95% token reduction!)
4. Use Gemini AI to extract structured data
5. Save individual JSON files for each source
6. Generate aggregated data and summary report

### Output Files

All output is saved in the `scraped_data/` directory:

- **Individual source files**: `{source_name}.json`
- **Aggregated data**: `road_accident_data_aggregated.json`
- **Summary report**: `summary_report.txt`
- **ML-ready data**: `ml_ready_data.json`

### Example Output Structure

```json
{
  "accident_statistics": {
    "total_accidents": 4000,
    "fatalities": 1500,
    "injuries": 2500,
    "year": "2024"
  },
  "black_spots": [
    "Thika Road near Exit 14",
    "Mombasa Road at Cabanas Junction",
    "Northern Bypass at Ruaka Roundabout"
  ],
  "causes": [
    "Speeding",
    "Drunk driving",
    "Poor road conditions"
  ],
  "temporal_patterns": [
    "Peak accidents during rush hours (7-9 AM, 5-7 PM)",
    "Higher fatalities on weekends",
    "Increased accidents during rainy season"
  ],
  "geographic_distribution": [
    "Urban areas: 60% of accidents",
    "Northern Corridor: 25% of fatalities"
  ],
  "safety_initiatives": [
    "Road Safety Action Plan 2024-2028",
    "Installation of speed cameras on Thika Road"
  ],
  "recommendations": [
    "Improve lighting at black spots",
    "Stricter enforcement of speed limits"
  ],
  "_metadata": {
    "source": "kenya_road_safety_action_plan_2024_2028",
    "scraped_at": "2026-02-20T10:30:00"
  }
}
```

## 🎛️ Configuration

Edit `config.py` to customize:

### Add More URLs
```python
TARGET_URLS.append({
    "url": "https://example.com/road-safety",
    "name": "example_source",
    "description": "Example road safety data"
})
```

### Change Gemini Model
```python
GEMINI_MODEL = "gemini-2.0-flash-lite"  # Fast and free
# or
GEMINI_MODEL = "gemini-1.5-pro"  # More powerful
```

### Modify Extraction Attributes
```python
EXTRACTION_ATTRIBUTES = """
your_custom_attributes,
another_attribute
"""
```

## 🛡️ Bypassing Anti-Scraping (Optional)

Some websites may block automated requests. To handle this:

1. Get a Web Unlocker API key from [Bright Data](https://brightdata.com/)
2. Add it to your `.env` file:
   ```
   WEB_UNLOCKER_API_KEY=your_web_unlocker_key
   ```
3. Enable it in `scraper.py`:
   ```python
   scraper = RoadAccidentScraper(use_web_unlocker=True)
   ```

## 💰 Cost Optimization

The scraper includes several cost-saving features:

1. **HTML → Markdown Conversion**: Reduces tokens by ~95%
   - Before: ~20,000 tokens per page
   - After: ~765 tokens per page

2. **Content Selection**: Only extracts relevant sections (e.g., `#main`)

3. **Free Tier Model**: Uses `gemini-2.0-flash-lite` by default

**Estimated Cost** (if using paid tier):
- Free tier: $0 (sufficient for this project)
- Paid tier: ~$0.01 per page with optimization

## 📈 Next Steps: AI Model Development

Once you have the scraped data, you can:

### 1. Predictive Modeling
```python
# Use scikit-learn or TensorFlow to build models
- Predict accident likelihood by location and time
- Forecast seasonal trends
- Identify emerging black spots
```

### 2. Real-Time Alert System
```python
# Integrate with:
- SMS/USSD for citizens without smartphones
- Mobile apps for drivers
- Traffic management systems
```

### 3. Dashboard & Visualization
```python
# Create dashboards using:
- Plotly/Dash for interactive maps
- Folium for black spot visualization
- Streamlit for real-time monitoring
```

### 4. NLP Analysis
```python
# Use Gemini or other LLMs to:
- Summarize accident reports
- Extract insights from news articles
- Analyze policy documents
```

## 🔍 Troubleshooting

### Issue: "GEMINI_API_KEY not found"
**Solution**: Make sure you created a `.env` file (not `.env.example`) with your API key

### Issue: "Failed to fetch HTML"
**Solutions**:
- Check internet connection
- Try enabling `use_web_unlocker=True`
- Some sites may block automated requests

### Issue: "No data extracted"
**Solutions**:
- Check if the website structure has changed
- Try different `CONTENT_SELECTORS` in config.py
- Increase request delay in `scraper.scrape_all(delay=5)`

### Issue: Virtual environment activation failed
**Solution**: On Windows, use:
```powershell
.venv\Scripts\activate
```
Not `source venv/bin/activate` (that's for Linux/Mac)

## 📚 What the AI Learns

This data enables AI to:

✅ **Trend Detection**: Peak times, seasonal patterns, year-over-year changes  
✅ **Geospatial Insights**: Hotspot mapping, urban vs rural analysis  
✅ **Cause Analysis**: Human, vehicle, and environmental factors  
✅ **Predictive Modeling**: Risk forecasting, driver profiling  
✅ **Policy Support**: Resource allocation, intervention effectiveness  

## 🤝 Contributing

To add more data sources:
1. Add URL to `TARGET_URLS` in `config.py`
2. Test with `python scraper.py`
3. Verify output in `scraped_data/`

## 📄 License

MIT License - Feel free to use for your road safety AI project!

## 🙏 Acknowledgments

- Google Gemini for AI-powered extraction
- Kenyan road safety organizations for data
- Web scraping tutorial from ScrapingCourse.com

---

**Built with ❤️ to make Kenyan roads safer through AI**
