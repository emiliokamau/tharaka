"""
Facial Fatigue Detection Model Training - Simplified Version
============================================================
Uses scikit-learn instead of TensorFlow to avoid Windows long path issues.
Trains a Random Forest classifier on Kaggle fatigue dataset.
"""

import os
import numpy as np
import cv2
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score
import joblib
import kagglehub
import json
from pathlib import Path

# Configuration
DATASET_NAME = "rihabkaci99/fatigue-dataset"
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "fatigue_detection_model.pkl")
SCALER_PATH = os.path.join(MODEL_DIR, "fatigue_scaler.pkl")
CONFIG_PATH = os.path.join(MODEL_DIR, "model_config.json")
IMAGE_SIZE = (128, 128)
BATCH_SIZE = 32
TEST_SPLIT = 0.2

def create_model_directory():
    """Create models directory if it doesn't exist"""
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)
        print(f"✅ Created {MODEL_DIR} directory")

def download_dataset():
    """Download Kaggle fatigue dataset"""
    print("\n" + "="*70)
    print("DOWNLOADING KAGGLE FATIGUE DATASET")
    print("="*70)
    
    try:
        path = kagglehub.dataset_download(DATASET_NAME)
        print(f"✅ Dataset downloaded to: {path}")
        return path
    except Exception as e:
        print(f"❌ Failed to download dataset: {e}")
        print("Make sure you have Kaggle API credentials configured")
        return None

def extract_features_from_image(image_path, size=IMAGE_SIZE):
    """Extract features from an image using histogram and HOG-like features"""
    try:
        # Read image
        img = cv2.imread(str(image_path))
        if img is None:
            return None
        
        # Resize
        img = cv2.resize(img, size)
        
        # Convert to grayscale for feature extraction
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Extract features:
        # 1. Histogram of grayscale values (16 bins)
        hist = cv2.calcHist([gray], [0], None, [16], [0, 256])
        hist = hist.flatten() / (hist.sum() + 1e-6)
        
        # 2. Histogram of color channels (8 bins each)
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
        return features
    
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return None

def load_and_preprocess_images(dataset_path):
    """Load and preprocess images from fatigue/non_fatigue folders"""
    print("\n" + "="*70)
    print("LOADING AND PREPROCESSING IMAGES")
    print("="*70)
    
    images_features = []
    labels = []
    
    # Check for directory structure
    fatigue_dir = os.path.join(dataset_path, "fatigue")
    non_fatigue_dir = os.path.join(dataset_path, "non_fatigue")
    
    # Try alternate names if not found
    if not os.path.exists(fatigue_dir):
        for d in os.listdir(dataset_path):
            if "fatigue" in d.lower():
                fatigue_dir = os.path.join(dataset_path, d)
                break
    
    if not os.path.exists(non_fatigue_dir):
        for d in os.listdir(dataset_path):
            if "non" in d.lower() or "alert" in d.lower():
                non_fatigue_dir = os.path.join(dataset_path, d)
                break
    
    print(f"Fatigue directory: {fatigue_dir}")
    print(f"Non-fatigue directory: {non_fatigue_dir}")
    
    # Load fatigue images (label=1)
    if os.path.exists(fatigue_dir):
        for filename in os.listdir(fatigue_dir)[:100]:  # Limit to 100 per class for faster training
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                filepath = os.path.join(fatigue_dir, filename)
                features = extract_features_from_image(filepath)
                if features is not None:
                    images_features.append(features)
                    labels.append(1)
                    if len(labels) % 20 == 0:
                        print(f"  Loaded {len(labels)} fatigue images...")
    
    # Load non-fatigue images (label=0)
    if os.path.exists(non_fatigue_dir):
        for filename in os.listdir(non_fatigue_dir)[:100]:  # Limit to 100 per class
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                filepath = os.path.join(non_fatigue_dir, filename)
                features = extract_features_from_image(filepath)
                if features is not None:
                    images_features.append(features)
                    labels.append(0)
                    if len(labels) % 20 == 0:
                        print(f"  Loaded {len(labels)} total images...")
    
    if len(images_features) == 0:
        print("❌ No images found! Check dataset structure.")
        return None, None
    
    X = np.array(images_features)
    y = np.array(labels)
    
    print(f"✅ Loaded {len(X)} images")
    print(f"   Shape: {X.shape}")
    print(f"   Fatigue samples: {np.sum(y == 1)}")
    print(f"   Alert samples: {np.sum(y == 0)}")
    
    return X, y

def build_model():
    """Build Random Forest model"""
    print("\n" + "="*70)
    print("BUILDING MODEL")
    print("="*70)
    
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=20,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
        verbose=1
    )
    
    print("✅ Random Forest model created")
    print(f"   Estimators: 100")
    print(f"   Max depth: 20")
    return model

def train_model(model, X_train, y_train):
    """Train the model"""
    print("\n" + "="*70)
    print("TRAINING MODEL")
    print("="*70)
    
    print("Training Random Forest (this may take a few minutes)...")
    model.fit(X_train, y_train)
    
    print("✅ Model training complete!")
    return model

def evaluate_model(model, X_test, y_test):
    """Evaluate model on test set"""
    print("\n" + "="*70)
    print("EVALUATING MODEL")
    print("="*70)
    
    y_pred = model.predict(X_test)
    
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    
    print(f"Test Accuracy:  {accuracy:.4f}")
    print(f"Precision:      {precision:.4f}")
    print(f"Recall:         {recall:.4f}")
    
    return {
        'accuracy': float(accuracy),
        'precision': float(precision),
        'recall': float(recall)
    }

def save_model_config(model, metrics, X_train, y_train):
    """Save model configuration and training info"""
    print("\n" + "="*70)
    print("SAVING MODEL")
    print("="*70)
    
    # Save model
    joblib.dump(model, MODEL_PATH)
    print(f"✅ Model saved to: {MODEL_PATH}")
    
    # Create and save config
    config = {
        'model_type': 'RandomForestClassifier',
        'image_size': IMAGE_SIZE,
        'test_metrics': metrics,
        'dataset': DATASET_NAME,
        'num_features': X_train.shape[1],
        'training_samples': len(X_train),
        'class_distribution': {
            'fatigue': int(np.sum(y_train == 1)),
            'alert': int(np.sum(y_train == 0))
        }
    }
    
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Config saved to: {CONFIG_PATH}")
    print("\nModel Configuration:")
    print(json.dumps(config, indent=2))

def main():
    """Main training pipeline"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " FACIAL FATIGUE DETECTION MODEL TRAINING ".center(68) + "║")
    print("║" + " Using Random Forest (scikit-learn) ".center(68) + "║")
    print("╚" + "="*68 + "╝")
    
    # Create directories
    create_model_directory()
    
    # Download dataset
    dataset_path = download_dataset()
    if dataset_path is None:
        print("\n❌ Training failed - could not download dataset")
        return
    
    # Load and preprocess images
    X, y = load_and_preprocess_images(dataset_path)
    if X is None:
        print("\n❌ Training failed - could not load images")
        return
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SPLIT, random_state=42, stratify=y
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)
    
    # Save scaler
    joblib.dump(scaler, SCALER_PATH)
    print(f"✅ Scaler saved to: {SCALER_PATH}")
    
    # Build model
    model = build_model()
    
    # Train model
    model = train_model(model, X_train, y_train)
    
    # Evaluate
    metrics = evaluate_model(model, X_test, y_test)
    
    # Save
    save_model_config(model, metrics, X_train, y_train)
    
    print("\n" + "="*70)
    print("✅ TRAINING COMPLETE!")
    print("="*70)
    print(f"\nModel saved to: {MODEL_PATH}")
    print(f"Config saved to: {CONFIG_PATH}")
    print("\nNext steps:")
    print("1. Run: python app.py")
    print("2. Test endpoint: POST /api/drowsiness/assess with image data")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
