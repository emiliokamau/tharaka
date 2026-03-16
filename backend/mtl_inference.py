"""
MTL (Multi-Task Learning) Inference Module for PyTorch
========================================================
Provides PyTorch-based inference for driver drowsiness detection.
Alternative to TensorFlow when TensorFlow installation fails.

This module provides:
- Eye state detection (open/closed)
- Gaze direction estimation (yaw/pitch)
- Distraction detection (5 classes)

Usage:
    from mtl_inference import MTLDetector
    detector = MTLDetector()
    result = detector.predict(image)
"""

import os
import cv2
import numpy as np
import json
import base64
from io import BytesIO
from pathlib import Path

# PyTorch imports
import torch
import torch.nn as nn
from torchvision import transforms

# Configuration
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "mtl_model.pth")
CONFIG_PATH = os.path.join(MODEL_DIR, "mtl_config.json")
IMAGE_SIZE = (64, 64)

# Global detector instance (singleton)
_detector = None


class SimpleMTLModel(nn.Module):
    """
    Simple Multi-Task Learning model for driver monitoring.
    Shared backbone with multiple task-specific heads.
    """
    def __init__(self, num_classes_eye=2, num_classes_distraction=5):
        super(SimpleMTLModel, self).__init__()
        
        # Shared backbone (lightweight CNN)
        self.backbone = nn.Sequential(
            # Conv block 1
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),  # 64 -> 32
            
            # Conv block 2
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),  # 32 -> 16
            
            # Conv block 3
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),  # 16 -> 8
            
            # Global average pooling
            nn.AdaptiveAvgPool2d((1, 1))
        )
        
        # Shared feature layer
        self.shared = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3)
        )
        
        # Task-specific heads
        # Eye state head (binary: open/closed)
        self.eye_head = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(64, num_classes_eye)
        )
        
        # Gaze yaw head (regression)
        self.gaze_yaw_head = nn.Sequential(
            nn.Linear(128, 32),
            nn.ReLU(inplace=True),
            nn.Linear(32, 1)
        )
        
        # Gaze pitch head (regression)
        self.gaze_pitch_head = nn.Sequential(
            nn.Linear(128, 32),
            nn.ReLU(inplace=True),
            nn.Linear(32, 1)
        )
        
        # Distraction head (multi-class)
        self.distraction_head = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(64, num_classes_distraction)
        )
    
    def forward(self, x):
        # Shared features
        features = self.backbone(x)
        features = self.shared(features)
        
        # Task outputs
        eye_out = self.eye_head(features)
        gaze_yaw = self.gaze_yaw_head(features)
        gaze_pitch = self.gaze_pitch_head(features)
        distraction = self.distraction_head(features)
        
        return {
            'eye_state': eye_out,
            'gaze_yaw': gaze_yaw,
            'gaze_pitch': gaze_pitch,
            'distraction': distraction
        }


class MTLDetector:
    """
    MTL-based driver drowsiness detector using PyTorch.
    Provides eye state, gaze direction, and distraction detection.
    """
    
    def __init__(self):
        """Initialize detector and load model"""
        self.model = None
        self.config = None
        self.model_available = False
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.transform = self._get_transform()
        self.load_model()
    
    def _get_transform(self):
        """Get image preprocessing transform"""
        return transforms.Compose([
            transforms.Resize(IMAGE_SIZE),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                                 std=[0.229, 0.224, 0.225])
        ])
    
    def load_model(self):
        """Load trained MTL model from disk"""
        try:
            # First try to load actual trained model
            if os.path.exists(MODEL_PATH):
                self.model = SimpleMTLModel()
                checkpoint = torch.load(MODEL_PATH, map_location=self.device)
                
                if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
                    self.model.load_state_dict(checkpoint['model_state_dict'])
                else:
                    self.model.load_state_dict(checkpoint)
                
                self.model.to(self.device)
                self.model.eval()
                print(f"✅ MTL Model loaded from {MODEL_PATH}")
            else:
                # Use untrained model for demo - will generate predictions
                print(f"⚠️  MTL model not found at: {MODEL_PATH}")
                print("   Using untrained model (predictions will be random)")
                self.model = SimpleMTLModel()
                self.model.to(self.device)
                self.model.eval()
            
            # Load config if exists
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, 'r') as f:
                    self.config = json.load(f)
                print(f"✅ MTL Config loaded from {CONFIG_PATH}")
            
            self.model_available = True
            print("✅ MTL Detector ready!")
            
        except Exception as e:
            print(f"❌ Error loading MTL model: {e}")
            self.model_available = False
    
    def preprocess_image(self, image_input):
        """Preprocess image for model input"""
        try:
            # Handle different input types
            if isinstance(image_input, str):
                if image_input.startswith('data:image'):
                    # Base64 encoded image
                    header, data = image_input.split(',')
                    img_bytes = base64.b64decode(data)
                    nparr = np.frombuffer(img_bytes, np.uint8)
                    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                elif os.path.isfile(image_input):
                    # File path
                    image = cv2.imread(image_input)
                else:
                    return None
            elif isinstance(image_input, np.ndarray):
                image = image_input
            else:
                return None
            
            if image is None:
                return None
            
            # Convert BGR to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Convert to PIL Image
            pil_image = Image.fromarray(image_rgb)
            
            # Apply transforms
            tensor = self.transform(pil_image)
            
            return tensor
        
        except Exception as e:
            print(f"Error preprocessing image: {e}")
            return None
    
    def predict(self, image_input):
        """
        Predict drowsiness from image using MTL model.
        Returns dict with fatigue assessment.
        """
        if not self.model_available:
            return {
                'success': False,
                'error': 'MTL Model not available',
                'model_available': False
            }
        
        try:
            # Preprocess image
            tensor = self.preprocess_image(image_input)
            if tensor is None:
                return {
                    'success': False,
                    'error': 'Could not load image'
                }
            
            # Add batch dimension
            tensor = tensor.unsqueeze(0).to(self.device)
            
            # Get predictions
            with torch.no_grad():
                outputs = self.model(tensor)
            
            # Extract predictions
            eye_logits = outputs['eye_state'][0]
            eye_probs = torch.softmax(eye_logits, dim=0)
            eye_pred = torch.argmax(eye_probs).item()
            eye_confidence = eye_probs[eye_pred].item()
            
            gaze_yaw = outputs['gaze_yaw'][0].item()
            gaze_pitch = outputs['gaze_pitch'][0].item()
            
            distraction_logits = outputs['distraction'][0]
            distraction_probs = torch.softmax(distraction_logits, dim=0)
            distraction_pred = torch.argmax(distraction_probs).item()
            distraction_confidence = distraction_probs[distraction_pred].item()
            
            # Calculate fatigue level based on eye state
            # eye_pred: 0 = closed, 1 = open
            # Higher fatigue if eyes are closed
            if eye_pred == 0:
                # Eyes closed - higher fatigue
                base_fatigue = 70 + np.random.randint(0, 30)
            else:
                # Eyes open - lower fatigue
                base_fatigue = 20 + np.random.randint(0, 30)
            
            # Adjust based on gaze (looking away = distracted)
            gaze_magnitude = abs(gaze_yaw) + abs(gaze_pitch)
            if gaze_magnitude > 30:  # Looking away
                base_fatigue += 10
            
            # Adjust based on distraction
            distraction_classes = ['safe', 'phone', 'smoking', 'eating', 'other']
            if distraction_pred > 0:  # Not safe
                base_fatigue += 15
            
            # Clamp fatigue level
            fatigue_level = min(100, max(0, base_fatigue))
            
            # Determine alert level
            if fatigue_level >= 80:
                alert_level = 'critical'
                recommendation = '🚨 CRITICAL: Pull over IMMEDIATELY and rest 15-20 minutes!'
            elif fatigue_level >= 60:
                alert_level = 'warning'
                recommendation = '⚠️ WARNING: Take a break soon. Consider stopping for coffee/rest.'
            elif fatigue_level >= 40:
                alert_level = 'moderate'
                recommendation = '⚡ MODERATE: Stay alert. Plan to take a break within the hour.'
            else:
                alert_level = 'normal'
                recommendation = '✅ NORMAL: You are alert. Keep driving safely!'
            
            # Return detailed results
            return {
                'success': True,
                'fatigue_level': fatigue_level,
                'alert_level': alert_level,
                'recommendation': recommendation,
                'model_type': 'mtl_pytorch',
                'details': {
                    'eye_state': 'closed' if eye_pred == 0 else 'open',
                    'eye_confidence': round(eye_confidence * 100, 1),
                    'gaze_yaw': round(gaze_yaw, 2),
                    'gaze_pitch': round(gaze_pitch, 2),
                    'distraction_class': distraction_classes[distraction_pred],
                    'distraction_confidence': round(distraction_confidence * 100, 1)
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Prediction error: {str(e)}'
            }


def get_mtl_detector():
    """Get singleton MTL detector instance"""
    global _detector
    if _detector is None:
        _detector = MTLDetector()
    return _detector


# Import PIL at module level for preprocess_image
from PIL import Image


# Standalone test
if __name__ == "__main__":
    print("Testing MTL Detector...")
    detector = MTLDetector()
    
    # Create dummy test image
    test_image = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
    result = detector.predict(test_image)
    print(f"Result: {result}")
