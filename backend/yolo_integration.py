"""
YOLO Model Integration for Driver Drowsiness Detection
======================================================
This module integrates the YOLO model with the drowsiness detection system.

YOLO Model Classes:
- 0: Open Eye
- 1: Closed Eye
- 2: Cigarette
- 3: Phone
- 4: Seatbelt
"""

import os
import cv2
import numpy as np
from collections import deque
import joblib
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import ultralytics
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logger.warning("Ultralytics not installed. YOLO features will be simulated.")

# YOLO model path - must be set via environment variable
YOLO_MODEL_PATH = os.environ.get(
    'YOLO_MODEL_PATH',
    None  # Must be set - no default path
)

# Class names
YOLO_CLASSES = {
    0: 'Open Eye',
    1: 'Closed Eye',
    2: 'Cigarette',
    3: 'Phone',
    4: 'Seatbelt'
}

# Global YOLO model (lazy loading)
_yolo_model = None


def get_yolo_model():
    """Load and return YOLO model"""
    global _yolo_model
    
    if _yolo_model is None:
        if YOLO_AVAILABLE and os.path.exists(YOLO_MODEL_PATH):
            try:
                _yolo_model = YOLO(YOLO_MODEL_PATH)
                logger.info(f"YOLO model loaded successfully from {YOLO_MODEL_PATH}")
            except Exception as e:
                logger.error(f"Failed to load YOLO model: {e}")
        else:
            if not YOLO_AVAILABLE:
                logger.debug("YOLO not available - ultralytics not installed")
            else:
                logger.warning(f"YOLO model not found at {YOLO_MODEL_PATH}")
            
    return _yolo_model


class YOLODetector:
    """
    YOLO-based driver behavior detector.
    Tracks eye state, cigarette, phone, and seatbelt usage.
    """
    
    def __init__(self, history_size=30, fps: float = 30.0):
        """
        Initialize YOLO detector.
        
        Args:
            history_size: Number of frames to track for eye closure calculation
            fps: Frames per second for timing calculations (default: 30.0)
        """
        self.model = get_yolo_model()
        self.history_size = history_size
        self.fps = fps
        
        # Tracking history
        self.eye_history = deque(maxlen=history_size)  # True = closed, False = open
        self.cigarette_detected = False
        self.phone_detected = False
        self.seatbelt_detected = True  # Assume seatbelt by default
        
        # Stats
        self.total_frames = 0
        self.closed_eye_frames = 0
        
    def process_frame(self, frame):
        """
        Process a single frame and update detection state.
        
        Args:
            frame: Image frame from webcam (numpy array)
            
        Returns:
            dict with detection results
        """
        self.total_frames += 1
        
        if self.model is None:
            # Return simulated data if model not available
            return self._simulate_detection()
        
        try:
            # Run YOLO inference
            results = self.model(frame, verbose=False)
            
            # Get detected classes
            detected_classes = []
            if len(results) > 0 and results[0].boxes is not None:
                boxes = results[0].boxes
                for cls_id in boxes.cls.cpu().numpy():
                    detected_classes.append(int(cls_id))
            
            # Update state based on detections
            eye_closed = 1 in detected_classes  # Closed eye detected
            self.eye_history.append(eye_closed)
            
            if eye_closed:
                self.closed_eye_frames += 1
            
            # Update other detections
            self.cigarette_detected = 2 in detected_classes
            self.phone_detected = 3 in detected_classes
            self.seatbelt_detected = 4 in detected_classes
            
            return {
                'detections': detected_classes,
                'eye_closed': eye_closed,
                'eye_history': list(self.eye_history),
                'cigarette_detected': self.cigarette_detected,
                'phone_detected': self.phone_detected,
                'seatbelt_detected': self.seatbelt_detected,
                'eye_closure_percentage': self.get_eye_closure_percentage()
            }
            
        except Exception as e:
            print(f"YOLO detection error: {e}")
            return self._simulate_detection()
    
    def _simulate_detection(self):
        """Return simulated detection when YOLO not available"""
        return {
            'detections': [],
            'eye_closed': False,
            'eye_history': [False] * self.history_size,
            'cigarette_detected': False,
            'phone_detected': False,
            'seatbelt_detected': True,
            'eye_closure_percentage': 0.0
        }
    
    def get_eye_closure_percentage(self):
        """Calculate percentage of frames where eyes were closed"""
        if len(self.eye_history) == 0:
            return 0.0
        
        closed_count = sum(1 for closed in self.eye_history if closed)
        return (closed_count / len(self.eye_history)) * 100
    
    def get_summary(self):
        """Get summary of detections"""
        return {
            'eye_closure_percentage': self.get_eye_closure_percentage(),
            'cigarette_detected': self.cigarette_detected,
            'phone_detected': self.phone_detected,
            'seatbelt_detected': self.seatbelt_detected,
            'total_frames': self.total_frames,
            'is_drowsy': self.get_eye_closure_percentage() > 15,
            'is_distracted': self.phone_detected or self.cigarette_detected
        }
    
    def reset(self):
        """Reset detection state"""
        self.eye_history.clear()
        self.cigarette_detected = False
        self.phone_detected = False
        self.seatbelt_detected = True
        self.total_frames = 0
        self.closed_eye_frames = 0


def get_features_for_model(yolo_detector):
    """
    Get features from YOLO detector to feed into the drowsiness model.
    
    Returns dict with features compatible with enhanced_drowsiness_model
    """
    summary = yolo_detector.get_summary()
    
    return {
        'eye_closure_percentage': summary['eye_closure_percentage'],
        'blink_frequency': calculate_blink_frequency(yolo_detector, fps=yolo_detector.fps),
        'head_position_encoded': 0,  # YOLO doesn't detect head position
        'yawn_detected': 0,  # YOLO doesn't detect yawning
        'hours_driven': 0,  # Need to be set separately
        'yolo_blink_detected': 1 if summary['eye_closure_percentage'] > 10 else 0
    }


def calculate_blink_frequency(detector, fps: float = 30.0):
    """
    Calculate blinks per minute based on eye state changes.
    
    A blink is detected when eye goes from closed to open.
    
    Args:
        detector: YOLODetector instance with eye_history
        fps: Frames per second (default: 30.0)
    
    Returns:
        Blinks per minute (clamped to realistic range 0-60)
    """
    eye_history = list(detector.eye_history)
    
    if len(eye_history) < 10:
        return 15.0  # Default typical blink rate
    
    # Count transitions from closed to open
    blinks = 0
    for i in range(1, len(eye_history)):
        if eye_history[i-1] == True and eye_history[i] == False:
            blinks += 1
    
    # Estimate blinks per minute based on history size
    duration_seconds = len(eye_history) / fps
    duration_minutes = duration_seconds / 60
    
    if duration_minutes > 0:
        blinks_per_minute = blinks / duration_minutes
    else:
        blinks_per_minute = 15.0
    
    return max(0, min(60, blinks_per_minute))  # Clamp to realistic range


# Example usage
if __name__ == "__main__":
    print("YOLO Driver Detection Integration")
    print("=" * 50)
    print(f"YOLO available: {YOLO_AVAILABLE}")
    print(f"Model path: {YOLO_MODEL_PATH}")
    print(f"YOLO classes: {YOLO_CLASSES}")
    print("\nDetected classes:")
    for cls_id, name in YOLO_CLASSES.items():
        print(f"  {cls_id}: {name}")
