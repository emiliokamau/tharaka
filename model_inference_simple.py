"""
Facial Fatigue Detection - Inference Module
===========================================
Load trained model and make predictions on driver images.
Returns fatigue level (0-100 scale) with alert recommendations.
"""

import os
import cv2
import numpy as np
import joblib
import json
import base64
from io import BytesIO
from pathlib import Path

# Configuration
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "fatigue_detection_model.pkl")
SCALER_PATH = os.path.join(MODEL_DIR, "fatigue_scaler.pkl")
CONFIG_PATH = os.path.join(MODEL_DIR, "model_config.json")
IMAGE_SIZE = (128, 128)

# Global detector instance (singleton)
_detector = None

class FatigueDetector:
    """Load and use trained fatigue detection model"""
    
    def __init__(self):
        """Initialize detector and load model"""
        self.model = None
        self.scaler = None
        self.config = None
        self.model_available = False
        self.load_model()
    
    def load_model(self):
        """Load trained model and scaler from disk"""
        try:
            if not os.path.exists(MODEL_PATH):
                print(f"⚠️  Model not found at: {MODEL_PATH}")
                return
            
            # Load model
            self.model = joblib.load(MODEL_PATH)
            print(f"✅ Model loaded from {MODEL_PATH}")
            
            # Load scaler
            if os.path.exists(SCALER_PATH):
                self.scaler = joblib.load(SCALER_PATH)
                print(f"✅ Scaler loaded from {SCALER_PATH}")
            else:
                print(f"⚠️  Scaler not found, will use unscaled features")
                self.scaler = None
            
            # Load config
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, 'r') as f:
                    self.config = json.load(f)
                print(f"✅ Config loaded from {CONFIG_PATH}")
            
            self.model_available = True
            print("✅ Fatigue detector ready!")
        
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            self.model_available = False
    
    def extract_features(self, image_array):
        """Extract features from image array"""
        try:
            # Ensure correct shape
            if len(image_array.shape) == 3:
                img = image_array
            else:
                return None
            
            # Resize if needed
            if img.shape[:2] != IMAGE_SIZE:
                img = cv2.resize(img, IMAGE_SIZE)
            
            # Convert to grayscale
            if len(img.shape) == 3:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            else:
                gray = img
            
            # Extract features (same as training):
            # 1. Histogram of grayscale values (16 bins)
            hist = cv2.calcHist([gray], [0], None, [16], [0, 256])
            hist = hist.flatten() / (hist.sum() + 1e-6)
            
            # 2. Histogram of color channels (8 bins each)
            if len(img.shape) == 3:
                for i in range(3):
                    h = cv2.calcHist([img], [i], None, [8], [0, 256])
                    hist = np.concatenate([hist, h.flatten() / (h.sum() + 1e-6)])
            
            # 3. Edge detection features (using Sobel)
            sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            magnitude = np.sqrt(sobelx**2 + sobely**2)
            edge_hist = np.histogram(magnitude, bins=8)[0]
            edge_hist = edge_hist / (edge_hist.sum() + 1e-6)
            
            # 4. Basic statistics
            stats = np.array([
                gray.mean(), gray.std(),
                gray.min(), gray.max(),
                magnitude.mean(), magnitude.std()
            ])
            
            # Combine all features
            features = np.concatenate([hist, edge_hist, stats])
            return features.reshape(1, -1)
        
        except Exception as e:
            print(f"Error extracting features: {e}")
            return None
    
    def preprocess_image(self, image_input):
        """
        Preprocess image from various input formats.
        Supports: file path, numpy array, base64 string
        """
        try:
            if isinstance(image_input, str):
                # Check if base64
                if image_input.startswith('data:image'):
                    # Base64 encoded image
                    header, data = image_input.split(',')
                    img_bytes = base64.b64decode(data)
                    nparr = np.frombuffer(img_bytes, np.uint8)
                    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                else:
                    # File path
                    image = cv2.imread(image_input)
                
                if image is None:
                    return None
            
            elif isinstance(image_input, np.ndarray):
                image = image_input
            
            else:
                return None
            
            return image
        
        except Exception as e:
            print(f"Error preprocessing image: {e}")
            return None
    
    def predict(self, image_input):
        """
        Predict fatigue level from image.
        Returns dict with fatigue_level (0-100), alert_level, and recommendation.
        """
        if not self.model_available:
            return {
                'success': False,
                'error': 'Model not available - run train_model_simple.py first',
                'model_available': False
            }
        
        try:
            # Preprocess image
            image = self.preprocess_image(image_input)
            if image is None:
                return {
                    'success': False,
                    'error': 'Could not load image'
                }
            
            # Extract features
            features = self.extract_features(image)
            if features is None:
                return {
                    'success': False,
                    'error': 'Could not extract features from image'
                }
            
            # Scale features if scaler available
            if self.scaler:
                features = self.scaler.transform(features)
            
            # Get prediction probability
            probabilities = self.model.predict_proba(features)[0]
            fatigue_probability = probabilities[1]  # Probability of fatigue class
            
            # Convert to 0-100 scale
            fatigue_level = fatigue_probability * 100
            
            # Determine alert level based on fatigue
            if fatigue_level >= 80:
                alert_level = 'critical'
                recommendation = '🚨 CRITICAL: Pull over IMMEDIATELY and rest 15-20 minutes!'
            elif fatigue_level >= 60:
                alert_level = 'warning'
                recommendation = '⚠️ WARNING: You appear fatigued. Take a break soon.'
            elif fatigue_level >= 40:
                alert_level = 'caution'
                recommendation = '⚠️ CAUTION: Monitor your fatigue level. Maintain safe driving speed.'
            elif fatigue_level >= 20:
                alert_level = 'info'
                recommendation = '✓ INFO: You appear fairly alert. Continue safe driving.'
            else:
                alert_level = 'safe'
                recommendation = '✓ SAFE: You appear well-rested. Great! Drive safely.'
            
            return {
                'success': True,
                'fatigue_level': round(fatigue_level, 1),
                'fatigue_probability': round(float(fatigue_probability), 4),
                'alert_level': alert_level,
                'recommendation': recommendation,
                'model_version': 'Facial Fatigue Detection (Random Forest)',
                'model_available': True
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Prediction failed: {str(e)}',
                'model_available': True
            }
    
    def predict_batch(self, image_list):
        """Predict fatigue for multiple images"""
        results = []
        for img in image_list:
            result = self.predict(img)
            results.append(result)
        return results
    
    def get_model_info(self):
        """Get model configuration and metrics"""
        if not self.config:
            return {'error': 'Config not available'}
        
        return {
            'model_type': self.config.get('model_type'),
            'image_size': self.config.get('image_size'),
            'num_features': self.config.get('num_features'),
            'training_samples': self.config.get('training_samples'),
            'metrics': self.config.get('test_metrics', {}),
            'dataset': self.config.get('dataset')
        }

def get_detector():
    """Get or create detector instance (singleton pattern)"""
    global _detector
    
    if _detector is None:
        print("Initializing Fatigue Detector...")
        _detector = FatigueDetector()
    
    return _detector

def predict_fatigue(image_input):
    """Convenience function to predict fatigue"""
    detector = get_detector()
    return detector.predict(image_input)

if __name__ == "__main__":
    # Test the detector
    print("Testing Fatigue Detector...")
    detector = get_detector()
    
    if detector.model_available:
        print("\n✅ Detector ready!")
        print(f"Model info: {detector.get_model_info()}")
    else:
        print("\n⚠️  Model not available yet. Run train_model_simple.py first.")
