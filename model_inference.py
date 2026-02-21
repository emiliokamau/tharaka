"""
Facial Fatigue Detection - Model Inference Module
================================================
Load trained model and make predictions on image data
Converts binary classification (0-1) to fatigue scale (0-100)
"""

import os
import numpy as np
import cv2
import tensorflow as tf
from tensorflow import keras
import json
from pathlib import Path
import base64
from io import BytesIO
from PIL import Image

# Configuration
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "fatigue_detection_model.h5")
CONFIG_PATH = os.path.join(MODEL_DIR, "model_config.json")
IMAGE_SIZE = (128, 128)

class FatigueDetector:
    """
    Load and use trained fatigue detection model
    Converts image input → fatigue probability (0-1) → fatigue level (0-100)
    """
    
    def __init__(self, model_path=MODEL_PATH):
        """Initialize detector by loading trained model"""
        self.model = None
        self.config = None
        self.model_path = model_path
        self.load_model()
        self.load_config()
    
    def load_model(self):
        """Load trained model from disk"""
        try:
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Model not found at {self.model_path}")
            
            self.model = keras.models.load_model(self.model_path)
            print(f"✅ Model loaded from {self.model_path}")
            return True
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            print(f"   Make sure to run train_model.py first to train and save the model")
            return False
    
    def load_config(self):
        """Load model configuration"""
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, 'r') as f:
                    self.config = json.load(f)
                print(f"✅ Config loaded from {CONFIG_PATH}")
            else:
                print(f"⚠️  Config file not found at {CONFIG_PATH}")
        except Exception as e:
            print(f"⚠️  Error loading config: {e}")
    
    def preprocess_image(self, image_input):
        """
        Preprocess image for model inference
        Accepts: file path, numpy array, or base64 string
        """
        try:
            # Load from file path
            if isinstance(image_input, str):
                if image_input.startswith(('http://', 'https://', '/')):
                    # File path
                    img = cv2.imread(image_input)
                    if img is None:
                        raise ValueError(f"Could not read image from {image_input}")
                else:
                    # Base64 string
                    try:
                        img_data = base64.b64decode(image_input)
                        img = Image.open(BytesIO(img_data))
                        img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                    except:
                        raise ValueError("Invalid base64 string")
            
            # Already numpy array
            elif isinstance(image_input, np.ndarray):
                img = image_input
                if img.dtype == np.uint8 and img.max() > 1:
                    # Already in 0-255 range
                    pass
                elif img.max() <= 1:
                    # In 0-1 range, convert to 0-255
                    img = (img * 255).astype(np.uint8)
            
            else:
                raise ValueError(f"Unsupported image input type: {type(image_input)}")
            
            # Ensure BGR format
            if len(img.shape) == 2:
                # Grayscale, convert to RGB
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            elif img.shape[2] == 4:
                # RGBA, convert to BGR
                img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
            elif img.shape[2] != 3:
                raise ValueError(f"Invalid image shape: {img.shape}")
            
            # Resize to model input size
            img_resized = cv2.resize(img, IMAGE_SIZE)
            
            # Normalize to 0-1 range
            img_normalized = img_resized.astype(np.float32) / 255.0
            
            # Convert BGR to RGB for model
            img_rgb = cv2.cvtColor(img_normalized, cv2.COLOR_BGR2RGB)
            
            # Add batch dimension
            img_batch = np.expand_dims(img_rgb, axis=0)
            
            return img_batch
        
        except Exception as e:
            print(f"❌ Error preprocessing image: {e}")
            return None
    
    def predict(self, image_input):
        """
        Predict fatigue level from image
        Returns: dict with fatigue_level (0-100), confidence, and recommendation
        """
        if self.model is None:
            return {
                'success': False,
                'error': 'Model not loaded. Run train_model.py first.'
            }
        
        try:
            # Preprocess image
            img_batch = self.preprocess_image(image_input)
            if img_batch is None:
                return {
                    'success': False,
                    'error': 'Failed to preprocess image'
                }
            
            # Get prediction (probability of fatigue: 0-1)
            fatigue_prob = self.model.predict(img_batch, verbose=0)[0][0]
            
            # Convert to 0-100 scale
            fatigue_level = float(fatigue_prob * 100)
            
            # Determine alert level and recommendation
            if fatigue_level >= 80:
                alert_level = 'critical'
                recommendation = '🚨 CRITICAL: Pull over IMMEDIATELY and rest 15-20 minutes!'
            elif fatigue_level >= 60:
                alert_level = 'warning'
                recommendation = '⚠️ WARNING: Take a break soon. Find a safe place to rest.'
            elif fatigue_level >= 40:
                alert_level = 'caution'
                recommendation = '⚠️ CAUTION: Monitor fatigue. Maintain safe driving.'
            elif fatigue_level >= 20:
                alert_level = 'info'
                recommendation = '✓ You appear alert. Continue safe driving.'
            else:
                alert_level = 'safe'
                recommendation = '✓ SAFE: You are well-rested. Keep up good driving!'
            
            return {
                'success': True,
                'fatigue_level': round(fatigue_level, 2),
                'fatigue_probability': round(float(fatigue_prob), 4),
                'alert_level': alert_level,
                'recommendation': recommendation,
                'model_version': self.config.get('model_name', 'Unknown') if self.config else 'Unknown'
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Prediction failed: {str(e)}'
            }
    
    def predict_batch(self, image_list):
        """
        Predict fatigue levels for multiple images
        Returns: list of prediction results
        """
        results = []
        for image in image_list:
            result = self.predict(image)
            results.append(result)
        return results
    
    def get_model_info(self):
        """Get information about the loaded model"""
        if self.config:
            return {
                'success': True,
                'config': self.config
            }
        else:
            return {
                'success': False,
                'error': 'Config not available'
            }


# Global detector instance
_detector = None

def get_detector():
    """Get or create global detector instance"""
    global _detector
    if _detector is None:
        _detector = FatigueDetector()
    return _detector

def predict_fatigue(image_input):
    """Convenience function for making predictions"""
    detector = get_detector()
    return detector.predict(image_input)


if __name__ == "__main__":
    """Test the inference module"""
    print("\n" + "="*70)
    print("FACIAL FATIGUE DETECTION - INFERENCE TEST")
    print("="*70 + "\n")
    
    # Initialize detector
    detector = FatigueDetector()
    
    # Display model info
    info = detector.get_model_info()
    if info['success']:
        print("✅ Model Information:")
        print(json.dumps(info['config'], indent=2))
    else:
        print(f"❌ {info['error']}")
    
    print("\n" + "="*70)
    print("Example Usage:")
    print("="*70)
    print("""
# Predict from image file
result = detector.predict('/path/to/image.jpg')

# Predict from numpy array
image_array = cv2.imread('image.jpg')
result = detector.predict(image_array)

# Get prediction
print(f"Fatigue Level: {result['fatigue_level']}")
print(f"Alert Level: {result['alert_level']}")
print(f"Recommendation: {result['recommendation']}")
    """)
    print("="*70 + "\n")
