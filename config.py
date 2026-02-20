"""
Configuration file for Kenya Road Accident Data Scraper
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WEB_UNLOCKER_API_KEY = os.getenv("WEB_UNLOCKER_API_KEY")

# Target URLs for scraping road accident data
TARGET_URLS = [
    {
        "url": "https://www.tandfonline.com/doi/full/10.1080/23311916.2020.1797981#d1e234",
        "name": "tandfonline_road_safety_study",
        "description": "Academic study on road accidents"
    },
    {
        "url": "https://varsanibrakelinings.com/inside-kenyas-road-safety-action-plan-2024-2028-what-drivers-need-to-know/",
        "name": "kenya_road_safety_action_plan_2024_2028",
        "description": "Kenya Road Safety Action Plan 2024-2028"
    },
    {
        "url": "https://streamlinefeed.co.ke/news/kenya-confronts-deadly-black-spots-with-new-national-road-safety-plan",
        "name": "kenya_deadly_black_spots",
        "description": "Kenya deadly black spots and road safety plan"
    },
    {
        "url": "https://www.ttcanc.org/road-accidents-along-northern-corridor-rethinking-road-user-behaviour-system-design-and-road",
        "name": "northern_corridor_accidents",
        "description": "Road accidents along Northern Corridor"
    },
    {
        "url": "https://www.knbs.or.ke/",
        "name": "kenya_national_bureau_statistics",
        "description": "Kenya National Bureau of Statistics"
    },
    {
        "url": "http://ir.jkuat.ac.ke/handle/123456789/5174?show=full",
        "name": "jkuat_road_accident_research",
        "description": "JKUAT research on road accidents in Kenya"
    }
]

# Data extraction attributes for road accident data
EXTRACTION_ATTRIBUTES = """
accident_statistics (number of accidents, fatalities, injuries by year/month),
black_spots (high-risk locations, roads, intersections),
causes (human factors, vehicle factors, environmental factors),
temporal_patterns (peak times, seasonal variations, trends),
geographic_distribution (regions, urban vs rural, specific roads),
safety_initiatives (government plans, interventions, policies),
recommendations (proposed solutions, infrastructure improvements),
target_goals (reduction targets, policy objectives),
key_findings (important insights, conclusions, research results)
"""

# Gemini model configuration
GEMINI_MODEL = "gemini-2.0-flash-lite"
GENERATION_CONFIG = {
    "response_mime_type": "application/json"
}

# CSS selectors for main content (common patterns)
CONTENT_SELECTORS = [
    "#main",
    "main",
    "article",
    ".article-content",
    ".post-content",
    ".content",
    "#content",
    "body"  # Fallback
]

# Output configuration
OUTPUT_DIR = "scraped_data"
AGGREGATED_OUTPUT = "road_accident_data_aggregated.json"
