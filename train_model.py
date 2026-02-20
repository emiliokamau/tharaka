"""
Train ML model on extracted road accident data from Kenya PDFs
Predicts accident probability based on temporal, geographic, and contextual factors
"""
import os
import json
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import warnings
warnings.filterwarnings('ignore')

# ML Libraries
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve
import pickle

# Load environment
load_dotenv()

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
EXTRACTED_DATA_DIR = "extracted_data"
MODEL_DIR = "models"
REPORTS_DIR = "model_reports"

# Create directories
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)


class RoadAccidentModelTrainer:
    """Train ML models on Kenya road accident data"""
    
    def __init__(self):
        """Initialize the trainer"""
        self.data = None
        self.df = None
        self.features = None
        self.target = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.model = None
        self.model_name = None
        
    def load_extracted_data(self):
        """Load all extracted JSON data from PDF extractions"""
        print("\n" + "="*70)
        print("📂 LOADING EXTRACTED DATA")
        print("="*70)
        
        json_files = list(Path(EXTRACTED_DATA_DIR).glob("*.json"))
        
        if not json_files:
            print(f"❌ No extracted JSON files found in {EXTRACTED_DATA_DIR}/")
            print("Please run pdf_extractor.py first to extract data from PDFs")
            return False
        
        print(f"✅ Found {len(json_files)} extracted data file(s):")
        
        self.data = {}
        for json_file in json_files:
            print(f"   • {json_file.name}")
            with open(json_file, 'r', encoding='utf-8') as f:
                self.data[json_file.stem] = json.load(f)
        
        return True
    
    def preprocess_data(self):
        """Convert extracted data to ML-ready format"""
        print("\n" + "="*70)
        print("🔄 DATA PREPROCESSING")
        print("="*70)
        
        records = []
        
        for source_name, data in self.data.items():
            print(f"\nProcessing: {source_name}")
            
            # Extract accident statistics
            stats = data.get('accident_statistics', {})
            
            if isinstance(stats, dict):
                # Stats are aggregated by year/location
                for period, count in stats.items():
                    if isinstance(count, (int, float)) and count > 0:
                        record = {
                            'source': source_name,
                            'period': str(period),
                            'accident_count': int(count) if isinstance(count, (int, float)) else 0,
                            'high_risk': 0  # Will be set based on thresholds
                        }
                        
                        # Add geographic data if available
                        geo_data = data.get('geographic_distribution', {})
                        if isinstance(geo_data, dict):
                            record['regions'] = len(geo_data) if geo_data else 0
                        
                        # Add cause information
                        causes = data.get('causes', [])
                        record['cause_factors'] = len(causes) if isinstance(causes, list) else 1
                        
                        # Add black spots
                        black_spots = data.get('black_spots', [])
                        record['black_spots_identified'] = len(black_spots) if isinstance(black_spots, list) else 0
                        
                        records.append(record)
            
            elif isinstance(stats, list):
                # Stats are in list format
                for stat in stats:
                    if isinstance(stat, dict):
                        record = {
                            'source': source_name,
                            'period': stat.get('period', 'unknown'),
                            'accident_count': int(stat.get('count', 0)) if stat.get('count') else 0,
                            'high_risk': 0
                        }
                        
                        geo_data = data.get('geographic_distribution', {})
                        record['regions'] = len(geo_data) if isinstance(geo_data, dict) else 0
                        
                        causes = data.get('causes', [])
                        record['cause_factors'] = len(causes) if isinstance(causes, list) else 1
                        
                        black_spots = data.get('black_spots', [])
                        record['black_spots_identified'] = len(black_spots) if isinstance(black_spots, list) else 0
                        
                        records.append(record)
        
        if not records:
            print("❌ No accident data found in extracted files")
            return False
        
        # Create DataFrame
        self.df = pd.DataFrame(records)
        
        # Define high-risk areas (top quartile of accidents)
        if len(self.df) > 0:
            threshold = self.df['accident_count'].quantile(0.75)
            self.df['high_risk'] = (self.df['accident_count'] > threshold).astype(int)
        
        print(f"\n✅ Created dataset with {len(self.df)} records")
        print(f"\n📊 Dataset shape: {self.df.shape}")
        print(f"   High-risk areas: {self.df['high_risk'].sum()}")
        print(f"   Safe areas: {(1-self.df['high_risk']).sum()}")
        
        return True
    
    def train_random_forest(self):
        """Train Random Forest model"""
        print("\n" + "="*70)
        print("🌲 TRAINING RANDOM FOREST MODEL")
        print("="*70)
        
        # Prepare features and target
        feature_cols = ['accident_count', 'regions', 'cause_factors', 'black_spots_identified']
        X = self.df[feature_cols].fillna(0)
        y = self.df['high_risk']
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"\n📊 Training set: {len(X_train)} samples")
        print(f"   Test set: {len(X_test)} samples")
        
        # Train model
        print("\n🤖 Training Random Forest...")
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(X_train, y_train)
        self.model_name = "random_forest"
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        
        accuracy = self.model.score(X_test, y_test)
        roc_auc = roc_auc_score(y_test, y_pred_proba)
        
        print(f"\n✅ Model trained successfully!")
        print(f"   Accuracy: {accuracy:.2%}")
        print(f"   ROC-AUC: {roc_auc:.2%}")
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': feature_cols,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print(f"\n🎯 Feature Importance:")
        for idx, row in feature_importance.iterrows():
            print(f"   {row['feature']}: {row['importance']:.2%}")
        
        return y_test, y_pred, y_pred_proba, feature_importance
    
    def train_gradient_boosting(self):
        """Train Gradient Boosting model"""
        print("\n" + "="*70)
        print("📈 TRAINING GRADIENT BOOSTING MODEL")
        print("="*70)
        
        # Prepare features and target
        feature_cols = ['accident_count', 'regions', 'cause_factors', 'black_spots_identified']
        X = self.df[feature_cols].fillna(0)
        y = self.df['high_risk']
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"\n📊 Training set: {len(X_train)} samples")
        print(f"   Test set: {len(X_test)} samples")
        
        # Train model
        print("\n🤖 Training Gradient Boosting...")
        self.model = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        
        self.model.fit(X_train, y_train)
        self.model_name = "gradient_boosting"
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        
        accuracy = self.model.score(X_test, y_test)
        roc_auc = roc_auc_score(y_test, y_pred_proba)
        
        print(f"\n✅ Model trained successfully!")
        print(f"   Accuracy: {accuracy:.2%}")
        print(f"   ROC-AUC: {roc_auc:.2%}")
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': feature_cols,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print(f"\n🎯 Feature Importance:")
        for idx, row in feature_importance.iterrows():
            print(f"   {row['feature']}: {row['importance']:.2%}")
        
        return y_test, y_pred, y_pred_proba, feature_importance
    
    def save_model(self):
        """Save trained model"""
        if self.model is None:
            print("❌ No model to save")
            return False
        
        model_file = os.path.join(MODEL_DIR, f"{self.model_name}_model.pkl")
        scaler_file = os.path.join(MODEL_DIR, f"{self.model_name}_scaler.pkl")
        
        with open(model_file, 'wb') as f:
            pickle.dump(self.model, f)
        
        with open(scaler_file, 'wb') as f:
            pickle.dump(self.scaler, f)
        
        print(f"\n💾 Model saved: {model_file}")
        print(f"💾 Scaler saved: {scaler_file}")
        
        return True
    
    def generate_report(self, y_test, y_pred, y_pred_proba, feature_importance):
        """Generate model evaluation report"""
        report_file = os.path.join(REPORTS_DIR, f"{self.model_name}_report.txt")
        
        try:
            with open(report_file, 'w') as f:
                f.write("="*70 + "\n")
                f.write("ROAD ACCIDENT MODEL EVALUATION REPORT\n")
                f.write("="*70 + "\n\n")
                
                f.write(f"Model Type: {self.model_name.replace('_', ' ').title()}\n")
                f.write(f"Training Date: {datetime.now().isoformat()}\n")
                f.write(f"Data Source: Kenya Road Accident PDFs\n\n")
                
                f.write("PERFORMANCE METRICS\n")
                f.write("-"*70 + "\n")
                f.write(f"Test Set Size: {len(y_test)}\n")
                f.write(f"Accuracy: {self.model.score(np.array(y_test).reshape(-1, 1) if len(np.array(y_test).shape) == 1 else y_test, y_test):.2%}\n")
                f.write(f"ROC-AUC Score: {roc_auc_score(y_test, y_pred_proba):.2%}\n\n")
                
                f.write("CLASSIFICATION REPORT\n")
                f.write("-"*70 + "\n")
                f.write(classification_report(y_test, y_pred, 
                                            target_names=['Safe Area', 'High-Risk Area']) + "\n")
                
                f.write("FEATURE IMPORTANCE\n")
                f.write("-"*70 + "\n")
                for idx, row in feature_importance.iterrows():
                    f.write(f"{row['feature']}: {row['importance']:.2%}\n")
                
                f.write("\n" + "="*70 + "\n")
            
            print(f"\n📄 Report saved: {report_file}")
        except Exception as e:
            print(f"⚠️  Could not generate full report: {e}")


def main():
    """Main training pipeline"""
    print("\n" + "="*80)
    print("🚀 KENYA ROAD ACCIDENT MODEL TRAINER")
    print("="*80)
    print("\nTrain ML models to predict high-risk accident areas")
    print("Using data extracted from Kenyan road safety PDFs\n")
    
    # Initialize trainer
    trainer = RoadAccidentModelTrainer()
    
    # Load data
    if not trainer.load_extracted_data():
        print("\n❌ Failed to load data. Please extract PDFs first:")
        print("   python pdf_extractor.py")
        return
    
    # Preprocess
    if not trainer.preprocess_data():
        print("\n❌ Failed to preprocess data")
        return
    
    # Train models
    print("\n" + "="*70)
    print("🤖 MODEL TRAINING")
    print("="*70)
    
    models_trained = []
    
    # Random Forest
    print("\n[1/2] Random Forest Model")
    try:
        y_test1, y_pred1, y_pred_proba1, imp1 = trainer.train_random_forest()
        trainer.save_model()
        trainer.generate_report(y_test1, y_pred1, y_pred_proba1, imp1)
        models_trained.append("Random Forest")
    except Exception as e:
        print(f"❌ Random Forest training failed: {e}")
    
    # Gradient Boosting
    print("\n[2/2] Gradient Boosting Model")
    try:
        y_test2, y_pred2, y_pred_proba2, imp2 = trainer.train_gradient_boosting()
        trainer.save_model()
        trainer.generate_report(y_test2, y_pred2, y_pred_proba2, imp2)
        models_trained.append("Gradient Boosting")
    except Exception as e:
        print(f"❌ Gradient Boosting training failed: {e}")
    
    # Summary
    print("\n" + "="*80)
    print("✅ TRAINING COMPLETE")
    print("="*80)
    
    if models_trained:
        print(f"\n✅ Successfully trained {len(models_trained)} model(s):")
        for model in models_trained:
            print(f"   • {model}")
        
        print(f"\n📁 Models saved to: {MODEL_DIR}/")
        print(f"📁 Reports saved to: {REPORTS_DIR}/")
        
        print("\n📊 Next Steps:")
        print("   1. Review model reports in model_reports/")
        print("   2. Use trained models for predictions")
        print("   3. Fine-tune hyperparameters if needed")
        print("   4. Deploy best model for real-time accident prediction")
    else:
        print("\n❌ No models were successfully trained")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
