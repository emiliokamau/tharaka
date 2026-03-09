"""
Complete end-to-end pipeline for Kenya road accident AI system
1. Extract data from PDFs using Gemini
2. Process and prepare data
3. Train ML models
4. Generate predictions
"""
import os
import subprocess
import sys
from pathlib import Path

def run_script(script_name, description):
    """Run a Python script and report results"""
    print(f"\n{'='*80}")
    print(f"▶️  {description}")
    print(f"{'='*80}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            cwd=os.getcwd(),
            capture_output=False
        )
        
        if result.returncode == 0:
            print(f"\n✅ {script_name} completed successfully")
            return True
        else:
            print(f"\n❌ {script_name} failed with code {result.returncode}")
            return False
    except Exception as e:
        print(f"\n❌ Error running {script_name}: {e}")
        return False


def main():
    """Main pipeline"""
    print("\n" + "="*80)
    print("🚀 KENYA ROAD ACCIDENT AI SYSTEM")
    print("Complete Pipeline: PDF → Data → Model → Predictions")
    print("="*80)
    
    # Check if PDFs exist
    pdf_files = list(Path('.').glob('*.pdf'))
    if not pdf_files:
        print("\n❌ No PDF files found in current directory")
        print("Please download Kenyan road safety PDFs to this folder")
        return
    
    print(f"\n📄 Found {len(pdf_files)} PDF file(s):")
    for pdf in pdf_files:
        print(f"   • {pdf.name}")
    
    # Step 1: Extract data
    steps = [
        ('pdf_extractor.py', '📄 STEP 1: Extract Data from PDFs'),
        ('data_processor.py', '🔄 STEP 2: Process and Aggregate Data'),
        ('train_model.py', '🤖 STEP 3: Train ML Models'),
    ]
    
    completed = 0
    
    for script, desc in steps:
        if run_script(script, desc):
            completed += 1
        else:
            print(f"\n⚠️  Pipeline stopped at {script}")
            break
    
    # Summary
    print(f"\n{'='*80}")
    print("✅ PIPELINE SUMMARY")
    print(f"{'='*80}")
    print(f"Completed: {completed}/{len(steps)} steps")
    
    if completed == len(steps):
        print("\n🎉 Full pipeline completed successfully!")
        print("\nNext steps:")
        print("1. Review model reports in model_reports/")
        print("2. Make predictions: python predict_risk.py")
        print("3. Deploy models for real-time accident prediction")
    else:
        print("\n⚠️  Some steps did not complete. Check the output above for errors.")
    
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()
