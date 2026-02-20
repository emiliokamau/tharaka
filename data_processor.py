"""
Data Processor for aggregating and analyzing scraped road accident data
"""
import json
import os
from datetime import datetime
from config import OUTPUT_DIR, AGGREGATED_OUTPUT


class DataProcessor:
    """
    Process and aggregate scraped road accident data
    """
    
    def __init__(self):
        self.output_dir = OUTPUT_DIR
    
    def aggregate_data(self, data_list):
        """
        Aggregate data from multiple sources
        
        Args:
            data_list: List of scraped data dictionaries
        """
        aggregated = {
            "metadata": {
                "total_sources": len(data_list),
                "aggregated_at": datetime.now().isoformat(),
                "description": "Aggregated road accident data for Kenya from multiple sources"
            },
            "sources": [],
            "statistics": {
                "total_accidents": None,
                "total_fatalities": None,
                "total_injuries": None
            },
            "black_spots": [],
            "causes": [],
            "temporal_patterns": [],
            "geographic_distribution": [],
            "safety_initiatives": [],
            "recommendations": [],
            "key_findings": []
        }
        
        # Process each source
        for data in data_list:
            if not data:
                continue
            
            source_info = {
                "name": data.get("_metadata", {}).get("source", "unknown"),
                "scraped_at": data.get("_metadata", {}).get("scraped_at", "")
            }
            aggregated["sources"].append(source_info)
            
            # Aggregate statistics
            if data.get("accident_statistics"):
                self._merge_statistics(aggregated["statistics"], data["accident_statistics"])
            
            # Aggregate black spots
            if data.get("black_spots"):
                self._add_to_list(aggregated["black_spots"], data["black_spots"])
            
            # Aggregate causes
            if data.get("causes"):
                self._add_to_list(aggregated["causes"], data["causes"])
            
            # Aggregate temporal patterns
            if data.get("temporal_patterns"):
                self._add_to_list(aggregated["temporal_patterns"], data["temporal_patterns"])
            
            # Aggregate geographic distribution
            if data.get("geographic_distribution"):
                self._add_to_list(aggregated["geographic_distribution"], data["geographic_distribution"])
            
            # Aggregate safety initiatives
            if data.get("safety_initiatives"):
                self._add_to_list(aggregated["safety_initiatives"], data["safety_initiatives"])
            
            # Aggregate recommendations
            if data.get("recommendations"):
                self._add_to_list(aggregated["recommendations"], data["recommendations"])
            
            # Aggregate key findings
            if data.get("key_findings"):
                self._add_to_list(aggregated["key_findings"], data["key_findings"])
        
        # Save aggregated data
        output_file = os.path.join(self.output_dir, AGGREGATED_OUTPUT)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(aggregated, f, indent=4, ensure_ascii=False)
        
        print(f"\n📊 Aggregated data saved to: {output_file}")
        
        # Generate summary report
        self.generate_summary_report(aggregated)
        
        return aggregated
    
    def _merge_statistics(self, target, source):
        """Merge statistical data"""
        if isinstance(source, dict):
            for key, value in source.items():
                if key not in target or target[key] is None:
                    target[key] = value
    
    def _add_to_list(self, target_list, source):
        """Add items to a list, handling different data types"""
        if isinstance(source, list):
            target_list.extend(source)
        elif isinstance(source, str):
            target_list.append(source)
        elif isinstance(source, dict):
            target_list.append(source)
    
    def generate_summary_report(self, aggregated_data):
        """
        Generate a human-readable summary report
        
        Args:
            aggregated_data: Aggregated data dictionary
        """
        report_lines = [
            "\n" + "="*80,
            "📋 KENYA ROAD ACCIDENT DATA - SUMMARY REPORT",
            "="*80,
            f"\n📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"📚 Total Sources: {aggregated_data['metadata']['total_sources']}",
            "\n" + "-"*80,
            "📊 KEY STATISTICS",
            "-"*80
        ]
        
        stats = aggregated_data.get("statistics", {})
        if stats:
            for key, value in stats.items():
                if value is not None:
                    report_lines.append(f"  • {key.replace('_', ' ').title()}: {value}")
        else:
            report_lines.append("  No statistical data available")
        
        # Black Spots
        black_spots = aggregated_data.get("black_spots", [])
        if black_spots:
            report_lines.extend([
                "\n" + "-"*80,
                "⚠️  BLACK SPOTS (HIGH-RISK LOCATIONS)",
                "-"*80
            ])
            for i, spot in enumerate(black_spots[:10], 1):  # Top 10
                if isinstance(spot, str):
                    report_lines.append(f"  {i}. {spot}")
                elif isinstance(spot, dict):
                    report_lines.append(f"  {i}. {json.dumps(spot, ensure_ascii=False)}")
        
        # Causes
        causes = aggregated_data.get("causes", [])
        if causes:
            report_lines.extend([
                "\n" + "-"*80,
                "🚨 ACCIDENT CAUSES",
                "-"*80
            ])
            for i, cause in enumerate(causes[:10], 1):
                if isinstance(cause, str):
                    report_lines.append(f"  {i}. {cause}")
                elif isinstance(cause, dict):
                    report_lines.append(f"  {i}. {json.dumps(cause, ensure_ascii=False)}")
        
        # Safety Initiatives
        initiatives = aggregated_data.get("safety_initiatives", [])
        if initiatives:
            report_lines.extend([
                "\n" + "-"*80,
                "🛡️  SAFETY INITIATIVES",
                "-"*80
            ])
            for i, initiative in enumerate(initiatives[:10], 1):
                if isinstance(initiative, str):
                    report_lines.append(f"  {i}. {initiative}")
                elif isinstance(initiative, dict):
                    report_lines.append(f"  {i}. {json.dumps(initiative, ensure_ascii=False)}")
        
        # Recommendations
        recommendations = aggregated_data.get("recommendations", [])
        if recommendations:
            report_lines.extend([
                "\n" + "-"*80,
                "💡 RECOMMENDATIONS",
                "-"*80
            ])
            for i, rec in enumerate(recommendations[:10], 1):
                if isinstance(rec, str):
                    report_lines.append(f"  {i}. {rec}")
                elif isinstance(rec, dict):
                    report_lines.append(f"  {i}. {json.dumps(rec, ensure_ascii=False)}")
        
        report_lines.extend([
            "\n" + "="*80,
            "✅ REPORT COMPLETE",
            "="*80 + "\n"
        ])
        
        report = "\n".join(report_lines)
        
        # Print to console
        print(report)
        
        # Save to file
        report_file = os.path.join(self.output_dir, "summary_report.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📄 Summary report saved to: {report_file}\n")
    
    def export_for_ml(self, aggregated_data, output_format='json'):
        """
        Export data in a format suitable for machine learning
        
        Args:
            aggregated_data: Aggregated data dictionary
            output_format: 'json' or 'csv'
        """
        ml_data = {
            "features": {
                "black_spots": aggregated_data.get("black_spots", []),
                "causes": aggregated_data.get("causes", []),
                "temporal_patterns": aggregated_data.get("temporal_patterns", []),
                "geographic_distribution": aggregated_data.get("geographic_distribution", [])
            },
            "metadata": aggregated_data.get("metadata", {})
        }
        
        if output_format == 'json':
            output_file = os.path.join(self.output_dir, "ml_ready_data.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(ml_data, f, indent=4, ensure_ascii=False)
            print(f"🤖 ML-ready data exported to: {output_file}")
        
        return ml_data


if __name__ == "__main__":
    # Example usage for testing
    processor = DataProcessor()
    
    # Load all scraped JSON files and aggregate
    data_list = []
    if os.path.exists(OUTPUT_DIR):
        for filename in os.listdir(OUTPUT_DIR):
            if filename.endswith('.json') and filename != AGGREGATED_OUTPUT:
                filepath = os.path.join(OUTPUT_DIR, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data_list.append(json.load(f))
    
    if data_list:
        processor.aggregate_data(data_list)
    else:
        print("No scraped data found. Run scraper.py first.")
