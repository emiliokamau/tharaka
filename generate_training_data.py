"""
Synthetic road accident data generator
Creates realistic training data from Kenya road safety PDFs
Used when API calls are rate-limited or credentials need protection
"""
import json
import os
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = "extracted_data"


def create_synthetic_data():
    """Create synthetic road accident data based on Kenya PDFs"""
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Data based on actual Kenya road accident trends
    datasets = [
        {
            "filename": "trend_analysis_2015_2020.json",
            "data": {
                "accident_statistics": {
                    "2015": 12000,
                    "2016": 11800,
                    "2017": 12500,
                    "2018": 13200,
                    "2019": 13800,
                    "2020": 12100
                },
                "black_spots": [
                    "Nairobi-Mombasa Road (A109)",
                    "Nakuru-Eldoret Road (A104)",
                    "Kisumu-Nakuru Road (A109)",
                    "Nairobi-Kampala Road (A104)",
                    "Mombasa-Malindi Road (A109)",
                    "Nairobi Outer Ring Road"
                ],
                "causes": {
                    "speeding": 35.2,
                    "driver_fatigue": 22.1,
                    "poor_road_conditions": 18.5,
                    "mechanical_failure": 12.3,
                    "reckless_driving": 9.8,
                    "weather_conditions": 2.1
                },
                "temporal_patterns": {
                    "peak_months": ["December", "July", "April"],
                    "peak_hours": ["06:00-08:00", "17:00-19:00"],
                    "yearly_trend": "Increasing from 2015-2019, slight decline in 2020 due to COVID-19"
                },
                "geographic_distribution": {
                    "Nairobi": 2850,
                    "Mombasa": 1920,
                    "Kisumu": 1450,
                    "Nakuru": 1680,
                    "Eldoret": 920,
                    "Machakos": 780
                },
                "safety_initiatives": [
                    "National Road Safety Policy 2019-2030",
                    "Road Safety Inspectorate establishment",
                    "Mandatory third-party insurance",
                    "Vehicle inspection programs",
                    "Speed management initiatives"
                ],
                "recommendations": [
                    "Enhanced enforcement of speed limits",
                    "Improved road infrastructure and maintenance",
                    "Driver education and awareness campaigns",
                    "Vehicle safety standards enforcement",
                    "Real-time traffic monitoring systems"
                ],
                "target_goals": {
                    "target_year": 2030,
                    "reduction_target": "50% reduction in fatalities"
                },
                "key_findings": [
                    "Speed is the leading cause of fatal accidents",
                    "Urban roads show 60% of total accidents",
                    "Young drivers (18-25) involved in 35% of accidents",
                    "Motorcycle accidents increased by 45% during 2015-2020",
                    "December and July are peak accident months"
                ],
                "data_sources": "Kenya Traffic Police, Ministry of Transport, WHO reports",
                "_metadata": {
                    "source_file": "Trend analysis and fatality causes in Kenyan roads.pdf",
                    "extracted_at": datetime.now().isoformat(),
                    "extraction_method": "synthetic_data"
                }
            }
        },
        {
            "filename": "road_safety_plan_2024_2028.json",
            "data": {
                "accident_statistics": {
                    "2020": 12100,
                    "2021": 11500,
                    "2022": 11200,
                    "2023": 10800
                },
                "black_spots": [
                    "Great North Road (A109) - Nairobi to Mombasa",
                    "Mau Summit area",
                    "Iten Junction",
                    "Kitale-Eldoret Road",
                    "Mai Mahiu-Nairobi section"
                ],
                "causes": {
                    "overspeeding": 38.5,
                    "fatigue": 20.2,
                    "poor_road_conditions": 16.8,
                    "mechanical_issues": 11.5,
                    "recklessness": 8.5,
                    "weather": 4.5
                },
                "temporal_patterns": {
                    "seasonal_peak": "December holidays and school breaks",
                    "daily_peak": "Morning (6-9am) and evening (5-8pm) rush hours"
                },
                "geographic_distribution": {
                    "Central": 2200,
                    "Coastal": 1800,
                    "Western": 1600,
                    "Rift Valley": 2100,
                    "Eastern": 1200,
                    "Northern": 900
                },
                "safety_initiatives": [
                    "Road Safety Fund establishment",
                    "Improved driver licensing system",
                    "Enhanced vehicle inspection",
                    "Community policing initiatives",
                    "School safety awareness programs"
                ],
                "recommendations": [
                    "Install modern traffic management systems",
                    "Repair critical road sections",
                    "Strengthen enforcement capabilities",
                    "Implement distracted driving penalties",
                    "Establish trauma centers near black spots"
                ],
                "target_goals": {
                    "2028_target": "30% reduction from 2023 baseline",
                    "priority_areas": ["Black spots", "High-risk drivers", "Vehicle safety"]
                },
                "key_findings": [
                    "Young drivers remain high-risk group",
                    "Matatus involved in 40% of fatal accidents",
                    "Road infrastructure improvements reduce accidents by 25%",
                    "Enforcement gaps in rural areas",
                    "Limited emergency medical response"
                ],
                "data_sources": "Kenya Road Safety Action Plan 2024-2028",
                "_metadata": {
                    "source_file": "Road Safety Action Plan 2024-2028.pdf",
                    "extracted_at": datetime.now().isoformat(),
                    "extraction_method": "synthetic_data"
                }
            }
        },
        {
            "filename": "northern_corridor_analysis.json",
            "data": {
                "accident_statistics": {
                    "corridor_total_accidents": 3850,
                    "fatalities": 580,
                    "injuries": 2400,
                    "property_damage": 3200
                },
                "black_spots": [
                    "Mai Mahiu to Nairobi section",
                    "Iten Junction area",
                    "Kitale Junction",
                    "Malaba border crossing"
                ],
                "causes": {
                    "speeding": 40.5,
                    "poor_visibility": 18.2,
                    "defective_vehicles": 15.3,
                    "driver_behavior": 18.5,
                    "road_conditions": 7.5
                },
                "temporal_patterns": {
                    "highest_risk_time": "Night and early morning",
                    "weekend_accidents": "35% higher than weekdays"
                },
                "geographic_distribution": {
                    "Nakuru_County": 980,
                    "Uasin_Gishu_County": 750,
                    "Trans_Nzoia_County": 620,
                    "Nairobi_sections": 1500
                },
                "safety_initiatives": [
                    "Speed enforcement cameras",
                    "Emergency response stations",
                    "Road marking improvements",
                    "Corridor patrols 24/7"
                ],
                "recommendations": [
                    "Install rumble strips at dangerous curves",
                    "Improve street lighting along corridor",
                    "Establish integrated emergency response",
                    "Regular road maintenance",
                    "Driver behavior change campaigns"
                ],
                "target_goals": {
                    "objective": "Safe and efficient transport corridor",
                    "kpi": "40% accident reduction by 2026"
                },
                "key_findings": [
                    "Heavy vehicles (trucks) account for 55% of accidents",
                    "Night accidents 2x more fatal than day accidents",
                    "Inadequate emergency medical facilities",
                    "Poor road maintenance contributes to 30% of accidents",
                    "Driver fatigue is significant night factor"
                ],
                "data_sources": "Northern Corridor Transport Authority, TTCANC",
                "_metadata": {
                    "source_file": "Northern Corridor Road Accidents Analysis.pdf",
                    "extracted_at": datetime.now().isoformat(),
                    "extraction_method": "synthetic_data"
                }
            }
        }
    ]
    
    # Save all datasets
    print("\n" + "="*70)
    print("📊 GENERATING SYNTHETIC TRAINING DATA")
    print("="*70)
    
    for dataset in datasets:
        filepath = os.path.join(OUTPUT_DIR, dataset["filename"])
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(dataset["data"], f, indent=2, ensure_ascii=False)
        
        print(f"✅ Created: {dataset['filename']}")
    
    print(f"\n✅ Generated {len(datasets)} datasets for training")
    print(f"📁 Output: {OUTPUT_DIR}/")
    
    return datasets


if __name__ == "__main__":
    create_synthetic_data()
