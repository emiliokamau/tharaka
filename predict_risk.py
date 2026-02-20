"""
Make predictions using trained road accident models
Predict accident risk for specific locations and conditions
"""
import os
import pickle
import json
import numpy as np
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

MODEL_DIR = "models"


class AccidentPredictor:
    """Make predictions using trained models"""
    
    def __init__(self, model_name="random_forest"):
        """Load trained model and scaler"""
        self.model_name = model_name
        self.model = None
        self.scaler = None
        self.feature_names = ['accident_count', 'regions', 'cause_factors', 'black_spots_identified']
        
        self.load_model()
    
    def load_model(self):
        """Load model and scaler from disk"""
        model_file = os.path.join(MODEL_DIR, f"{self.model_name}_model.pkl")
        scaler_file = os.path.join(MODEL_DIR, f"{self.model_name}_scaler.pkl")
        
        if not os.path.exists(model_file):
            print(f"[ERROR] Model file not found: {model_file}")
            print("Please train a model first: python train_model.py")
            return False
        
        try:
            with open(model_file, 'rb') as f:
                self.model = pickle.load(f)
            
            with open(scaler_file, 'rb') as f:
                self.scaler = pickle.load(f)
            
            print(f"[OK] Loaded {self.model_name} model")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to load model: {e}")
            return False
    
    def predict_risk(self, accident_count, regions, cause_factors, black_spots):
        """Predict accident risk for given conditions"""
        if self.model is None:
            return None
        
        # Create feature vector
        features = np.array([[accident_count, regions, cause_factors, black_spots]])
        
        # Scale features
        features_scaled = self.scaler.transform(features)
        
        # Make prediction
        prediction = self.model.predict(features_scaled)[0]
        probability = self.model.predict_proba(features_scaled)[0]
        
        return {
            'risk_level': 'HIGH RISK' if prediction == 1 else 'SAFE',
            'prediction': int(prediction),
            'probability_safe': float(probability[0]),
            'probability_high_risk': float(probability[1]),
            'confidence': float(max(probability))
        }
    
    def batch_predict(self, data_list):
        """Make predictions for multiple locations"""
        results = []
        
        for data in data_list:
            result = self.predict_risk(
                data.get('accident_count', 0),
                data.get('regions', 0),
                data.get('cause_factors', 0),
                data.get('black_spots', 0)
            )
            
            result['location'] = data.get('location', 'Unknown')
            result['period'] = data.get('period', 'Unknown')
            results.append(result)
        
        return results


def main():
    """Interactive prediction interface"""
    print("\n" + "="*80)
    print("🚨 ROAD ACCIDENT RISK PREDICTOR")
    print("="*80)
    print("\nPredicts accident risk for Kenyan locations")
    print("Using trained ML models\n")
    
    # Choose model
    print("Available Models:")
    print("1. Random Forest (recommended)")
    print("2. Gradient Boosting")
    
    choice = input("\nSelect model (1-2): ").strip()
    model_name = "gradient_boosting" if choice == "2" else "random_forest"
    
    # Load predictor
    predictor = AccidentPredictor(model_name)
    
    if predictor.model is None:
        print("\n❌ Could not load model. Train a model first:")
        print("   python train_model.py")
        return
    
    # Interactive predictions
    print("\n" + "="*70)
    print("Enter values for prediction (or 'exit' to quit)")
    print("="*70)
    
    while True:
        print("\n📍 Location Information:")
        
        try:
            location = input("Location name (e.g., 'Nairobi-Mombasa Road'): ").strip()
            if location.lower() == 'exit':
                break
            
            accident_count = float(input("Accident count (last year): "))
            regions = float(input("Number of regions affected: "))
            cause_factors = float(input("Number of contributing factors: "))
            black_spots = float(input("Number of black spots identified: "))
            
            result = predictor.predict_risk(
                int(accident_count),
                int(regions),
                int(cause_factors),
                int(black_spots)
            )
            
            print(f"\n{'='*70}")
            print(f"🎯 PREDICTION RESULT for: {location}")
            print(f"{'='*70}")
            print(f"Risk Level: {result['risk_level']}")
            print(f"Probability (Safe): {result['probability_safe']:.2%}")
            print(f"Probability (High Risk): {result['probability_high_risk']:.2%}")
            print(f"Confidence: {result['confidence']:.2%}")
            print(f"{'='*70}")
        
        except ValueError:
            print("❌ Invalid input. Please enter numbers.")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n✅ Predictor closed")


if __name__ == "__main__":
    main()
