"""
Preprocessing Pipeline for Driver Monitoring System

Features:
1. MediaPipe-based eye-cropping for face alignment
2. Albumentations augmentations optimized for low-light/nighttime conditions
3. Standardization to 64x64 pixels

Usage:
    # Training transforms (with augmentations)
    train_transform = get_train_transforms()
    
    # Validation transforms (no augmentation)
    val_transform = get_val_transforms()
    
    # For inference
    preprocess = InferencePreprocessor()
"""

import cv2
import numpy as np
import torch
from typing import Tuple, Optional, List, Dict, Any
from dataclasses import dataclass

# Optional dependencies
try:
    import albumentations as A
    from albumentations.pytorch import ToTensorV2
    ALBUMENTATIONS_AVAILABLE = True
except ImportError:
    ALBUMENTATIONS_AVAILABLE = False
    A = None
    ToTensorV2 = None
    print("Warning: Albumentations not installed. Using basic preprocessing.")


# Standard image size for DMS models
DEFAULT_IMAGE_SIZE = (64, 64)


@dataclass
class EyeLandmarks:
    """Container for eye landmarks from MediaPipe"""
    left_eye: np.ndarray  # (2,) array of (x, y)
    right_eye: np.ndarray
    left_iris: Optional[np.ndarray] = None
    right_iris: Optional[np.ndarray] = None


class MediaPipeEyeDetector:
    """
    MediaPipe-based eye detection and cropping.
    
    Uses MediaPipe Face Mesh to detect facial landmarks
    and extract eye regions for DMS tasks.
    
    Usage:
        detector = MediaPipeEyeDetector()
        eye_image, landmarks = detector.detect_and_crop(frame)
    """
    
    # MediaPipe face mesh indices for eyes
    # Left eye: 33, 133, 160, 158, 153, 144, 163, 7
    # Right eye: 362, 263, 387, 385, 380, 373, 390, 249
    LEFT_EYE_INDICES = [33, 133, 160, 158, 153, 144, 163, 7]
    RIGHT_EYE_INDICES = [362, 263, 387, 385, 380, 373, 390, 249]
    
    # Iris indices
    LEFT_IRIS_INDEX = 468
    RIGHT_IRIS_INDEX = 473
    
    def __init__(
        self,
        static_image_mode: bool = False,
        max_num_faces: int = 1,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ):
        """
        Initialize MediaPipe face mesh.
        
        Args:
            static_image_mode: If True, runs face detection on each image
            max_num_faces: Maximum number of faces to detect
            min_detection_confidence: Minimum confidence for face detection
            min_tracking_confidence: Minimum confidence for landmark tracking
        """
        try:
            import mediapipe as mp
            self.mp = mp
            self.mp_face_mesh = mp.solutions.face_mesh
            
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                static_image_mode=static_image_mode,
                max_num_faces=max_num_faces,
                min_detection_confidence=min_detection_confidence,
                min_tracking_confidence=min_tracking_confidence,
            )
            self.mp_drawing = mp.solutions.drawing_utils
            self.mp_styles = mp.solutions.drawing_styles
            self.available = True
            
        except ImportError:
            print("Warning: MediaPipe not installed. Using fallback detection.")
            self.available = False
            
    def detect_faces(self, image: np.ndarray) -> List[Dict]:
        """
        Detect faces and return landmarks.
        
        Args:
            image: Input image in RGB format
            
        Returns:
            List of face dictionaries with landmarks
        """
        if not self.available:
            return []
            
        # Convert to RGB if needed
        if image.shape[-1] == 3 and image.dtype == np.uint8:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = image
            
        results = self.face_mesh.process(image_rgb)
        
        faces = []
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                landmarks = np.array([
                    (lm.x, lm.y, lm.z) 
                    for lm in face_landmarks.landmark
                ])
                faces.append({
                    "landmarks": landmarks,
                    "mediapipe_landmarks": face_landmarks,
                })
                
        return faces
    
    def get_eye_region(
        self, 
        image: np.ndarray, 
        face: Dict,
        eye: str = "both",
        padding: float = 0.3,
    ) -> Tuple[np.ndarray, EyeLandmarks]:
        """
        Extract eye region from detected face.
        
        Args:
            image: Input image (RGB or BGR)
            face: Face dictionary from detect_faces()
            eye: "left", "right", or "both"
            padding: Extra padding around eye region (as fraction)
            
        Returns:
            Tuple of (cropped_eye_image, landmarks)
        """
        landmarks = face["landmarks"]
        h, w = image.shape[:2]
        
        # Get eye regions
        if eye in ["left", "both"]:
            left_eye_center = landmarks[self.LEFT_EYE_INDICES].mean(axis=0)[:2]
            left_eye_points = landmarks[self.LEFT_EYE_INDICES][:, :2]
            left_eye_size = np.max(np.ptp(left_eye_points, axis=0))
            
        if eye in ["right", "both"]:
            right_eye_center = landmarks[self.RIGHT_EYE_INDICES].mean(axis=0)[:2]
            right_eye_points = landmarks[self.RIGHT_EYE_INDICES][:, :2]
            right_eye_size = np.max(np.ptp(right_eye_points, axis=0))
            
        if eye == "left":
            eye_center = left_eye_center
            eye_size = left_eye_size
        elif eye == "right":
            eye_center = right_eye_center
            eye_size = right_eye_size
        else:
            # Combine both eyes
            eye_center = (left_eye_center + right_eye_center) / 2
            eye_size = max(left_eye_size, right_eye_size)
            
        # Compute crop region
        crop_size = int(eye_size * (1 + padding))
        x1 = int(eye_center[0] * w - crop_size / 2)
        y1 = int(eye_center[1] * h - crop_size / 2)
        x2 = x1 + crop_size
        y2 = y1 + crop_size
        
        # Clip to image bounds
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(w, x2)
        y2 = min(h, y2)
        
        # Extract eye region
        eye_image = image[y1:y2, x1:x2]
        
        # Create landmarks object
        eye_landmarks = EyeLandmarks(
            left_eye=left_eye_center * [w, h] if eye in ["left", "both"] else None,
            right_eye=right_eye_center * [w, h] if eye in ["right", "both"] else None,
        )
        
        return eye_image, eye_landmarks
    
    def detect_and_crop(
        self,
        image: np.ndarray,
        target_size: Tuple[int, int] = DEFAULT_IMAGE_SIZE,
    ) -> Tuple[np.ndarray, Optional[EyeLandmarks]]:
        """
        Full pipeline: detect face, crop eye region, resize.
        
        Args:
            image: Input image (RGB or BGR)
            target_size: Target output size (width, height)
            
        Returns:
            Tuple of (processed_image, eye_landmarks)
        """
        # Detect faces
        faces = self.detect_faces(image)
        
        if not faces:
            # Fallback: use center crop
            return self._fallback_crop(image, target_size), None
            
        # Get eye region from first detected face
        eye_image, landmarks = self.get_eye_region(image, faces[0], eye="both")
        
        # Resize to target size
        if eye_image.size > 0:
            eye_image = cv2.resize(eye_image, target_size)
        else:
            # Fallback if eye region is empty
            return self._fallback_crop(image, target_size), None
            
        return eye_image, landmarks
    
    def _fallback_crop(
        self, 
        image: np.ndarray, 
        target_size: Tuple[int, int]
    ) -> np.ndarray:
        """Fallback to center crop if face detection fails"""
        h, w = image.shape[:2]
        target_h, target_w = target_size
        
        # Center crop
        crop_size = min(h, w)
        start_x = (w - crop_size) // 2
        start_y = (h - crop_size) // 2
        
        cropped = image[start_y:start_y+crop_size, start_x:start_x+crop_size]
        resized = cv2.resize(cropped, target_size)
        
        return resized


def get_train_transforms(
    image_size: Tuple[int, int] = DEFAULT_IMAGE_SIZE,
    enable_low_light: bool = True,
) -> Any:
    """
    Get training transforms with augmentations.
    
    Includes low-light optimizations for Kenyan driving conditions:
    - CLAHE for contrast enhancement
    - Random brightness/contrast
    - Gaussian noise for sensor noise simulation
    
    Args:
        image_size: Target image size (height, width)
        enable_low_light: Include low-light augmentations
        
    Returns:
        Albumentations composition
    """
    if not ALBUMENTATIONS_AVAILABLE:
        raise ImportError("Albumentations is required for transforms. Install with: pip install albumentations")
    
    transforms = []
    
    # Low-light optimizations (for Kenyan nighttime driving)
    if enable_low_light:
        transforms.extend([
            # CLAHE - enhances local contrast (great for low-light)
            A.CLAHE(clip_limit=2.0, tile_grid_size=(8, 8), p=0.5),
            
            # Random brightness/contrast - simulate varying light conditions
            A.RandomBrightnessContrast(
                brightness_limit=0.3,
                contrast_limit=0.3,
                brightness_by_max=True,
                p=0.5,
            ),
            
            # Simulate infrared camera noise
            A.GaussNoise(
                var_limit=(10.0, 50.0),
                mean=0,
                p=0.3,
            ),
            
            # Motion blur (simulates camera movement)
            A.MotionBlur(blur_limit=3, p=0.2),
        ])
    
    # General augmentations
    transforms.extend([
        # Horizontal flip (only if labels are symmetric)
        A.HorizontalFlip(p=0.0),  # Disable for gaze - not symmetric!
        
        # Small rotations (simulates head tilt)
        A.Rotate(limit=(-15, 15), p=0.3),
        
        # Scale variations
        A.RandomScale(scale_limit=0.1, p=0.3),
        
        # Color augmentations
        A.HueSaturationValue(
            hue_shift_limit=10,
            sat_shift_limit=20,
            val_shift_limit=20,
            p=0.3,
        ),
        
        # Normalization (ImageNet stats)
        A.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
            max_pixel_value=255.0,
        ),
    ])
    
    return A.Compose(transforms)


def get_val_transforms(
    image_size: Tuple[int, int] = DEFAULT_IMAGE_SIZE,
    enable_low_light: bool = True,
) -> Any:
    """
    Get validation/test transforms (minimal augmentation).
    
    Only applies normalization and low-light preprocessing
    that would be applied at inference time.
    
    Args:
        image_size: Target image size
        enable_low_light: Include CLAHE preprocessing
        
    Returns:
        Albumentations composition
    """
    if not ALBUMENTATIONS_AVAILABLE:
        raise ImportError("Albumentations is required for transforms. Install with: pip install albumentations")
    
    transforms = []
    
    if enable_low_light:
        transforms.append(
            A.CLAHE(clip_limit=2.0, tile_grid_size=(8, 8), p=1.0)
        )
    
    transforms.append(
        A.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
            max_pixel_value=255.0,
        )
    )
    
    return A.Compose(transforms)


def get_inference_transforms(
    image_size: Tuple[int, int] = DEFAULT_IMAGE_SIZE,
) -> Any:
    """
    Get transforms for inference (exactly what you'd use at runtime).
    
    Returns:
        Albumentations composition
    """
    if not ALBUMENTATIONS_AVAILABLE:
        raise ImportError("Albumentations is required for transforms. Install with: pip install albumentations")
    
    return A.Compose([
        A.CLAHE(clip_limit=2.0, tile_grid_size=(8, 8), p=1.0),
        A.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
            max_pixel_value=255.0,
        ),
    ])


class InferencePreprocessor:
    """
    Preprocessing pipeline for inference.
    
    Handles:
    1. MediaPipe eye detection and cropping
    2. CLAHE enhancement for low-light
    3. Resize to model input size
    4. Normalization
    """
    
    def __init__(
        self,
        target_size: Tuple[int, int] = DEFAULT_IMAGE_SIZE,
        use_mediapipe: bool = True,
        enhance_low_light: bool = True,
    ):
        self.target_size = target_size
        self.use_mediapipe = use_mediapipe and MediaPipeEyeDetector.available
        
        if self.use_mediapipe:
            self.eye_detector = MediaPipeEyeDetector()
            
        if enhance_low_light:
            self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        else:
            self.clahe = None
            
    def __call__(self, image: np.ndarray) -> torch.Tensor:
        """
        Preprocess a single image for inference.
        
        Args:
            image: Input image (H, W, 3) in RGB format
            
        Returns:
            Preprocessed tensor (1, 3, H, W)
        """
        # Convert to uint8 if needed
        if image.dtype != np.uint8:
            image = (image * 255).astype(np.uint8)
            
        # Eye detection and cropping
        if self.use_mediapipe:
            processed, _ = self.eye_detector.detect_and_crop(image, self.target_size)
        else:
            # Simple center crop
            h, w = image.shape[:2]
            crop_size = min(h, w)
            start_x = (w - crop_size) // 2
            start_y = (h - crop_size) // 2
            processed = image[start_y:start_y+crop_size, start_x:start_x+crop_size]
            processed = cv2.resize(processed, self.target_size)
            
        # CLAHE for low-light
        if self.clahe is not None:
            lab = cv2.cvtColor(processed, cv2.COLOR_RGB2LAB)
            lab[:, :, 0] = self.clahe.apply(lab[:, :, 0])
            processed = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
            
        # Convert to tensor
        tensor = torch.from_numpy(processed).permute(2, 0, 1).float() / 255.0
        
        # Normalize
        mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
        std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
        tensor = (tensor - mean) / std
        
        return tensor.unsqueeze(0)  # Add batch dimension


def create_preprocessing_config() -> Dict[str, Any]:
    """Create a configuration dict for preprocessing (useful for metadata)"""
    return {
        "image_size": DEFAULT_IMAGE_SIZE,
        "normalization": {
            "mean": [0.485, 0.456, 0.406],
            "std": [0.229, 0.224, 0.225],
        },
        "low_light": {
            "clahe_clip_limit": 2.0,
            "clahe_tile_grid_size": [8, 8],
        },
        "augmentations": {
            "train": [
                "CLAHE (p=0.5)",
                "RandomBrightnessContrast (p=0.5)",
                "GaussNoise (p=0.3)",
                "MotionBlur (p=0.2)",
                "Rotate (limit=±15°, p=0.3)",
                "RandomScale (p=0.3)",
                "HueSaturationValue (p=0.3)",
            ],
            "val": [
                "CLAHE (p=1.0)",
                "Normalize",
            ],
        },
    }
