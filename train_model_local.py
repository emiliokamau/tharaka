"""
Facial Fatigue Detection Model Training - Local Dataset Version
Uses local dataset from facial datasets folder.
Trains a Random Forest classifier on local fatigue dataset.
"""

import os
import numpy as np
import cv2
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score
import joblib
import json
from pathlib import Path

# Configuration
LOCAL_DATASET_PATH = r"C:\Users\DIANNA\Documents\facial datasets\Data"
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "fatigue_detection_model.pkl")
SCALER_PATH = os.path.join(MODEL_DIR, "fatigue_scaler.pkl")
CONFIG_PATH = os.path.join(MODEL_DIR, "model_config.json")
IMAGE_SIZE = (128, 128)
TEST_SPLIT = 0.2

def create_model_directory():
    """Create models directory if it doesn't exist"""
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)
        print(f"✅ Created {MODEL_DIR} directory")

def verify_dataset():
    """Verify local dataset exists"""
    print("\n" + "="*70)
    print("VERIFYING LOCAL DATASET")
    print("="*70)
    
    if not os.path.exists(LOCAL_DATASET_PATH):
        print(f"❌ Dataset path not found: {LOCAL_DATASET_PATH}")
        return False
    
    fatigue_dir = os.path.join(LOCAL_DATASET_PATH, "Fatigue")
    non_fatigue_dir = os.path.join(LOCAL_DATASET_PATH, "NonFatigue")
    
    print(f"Dataset location: {LOCAL_DATASET_PATH}")
    print(f"Fatigue folder: {fatigue_dir}")
    print(f"NonFatigue folder: {non_fatigue_dir}")
    
    if not os.path.exists(fatigue_dir):
        print(f"❌ Fatigue directory not found")
        return False
    
    if not os.path.exists(non_fatigue_dir):
        print(f"❌ NonFatigue directory not found")
        return False
    
    # Count images
    fatigue_count = len([f for f in os.listdir(fatigue_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))])
    non_fatigue_count = len([f for f in os.listdir(non_fatigue_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))])
    
    print(f"✅ Fatigue images: {fatigue_count}")
    print(f"✅ NonFatigue images: {non_fatigue_count}")
    
    if fatigue_count == 0 or non_fatigue_count == 0:
        print("❌ No images found in dataset folders")
        return False
    
    return True

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
    """Load and preprocess images from Fatigue/NonFatigue folders"""
    print("\n" + "="*70)
    print("LOADING AND PREPROCESSING IMAGES")
    print("="*70)
    
    images_features = []
    labels = []
    
    fatigue_dir = os.path.join(dataset_path, "Fatigue")
    non_fatigue_dir = os.path.join(dataset_path, "NonFatigue")
    
    # Load fatigue images (label=1)
    print("\n📁 Loading Fatigue images...")
    if os.path.exists(fatigue_dir):
        fatigue_files = [f for f in os.listdir(fatigue_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
        for i, filename in enumerate(fatigue_files):
            filepath = os.path.join(fatigue_dir, filename)
            features = extract_features_from_image(filepath)
            if features is not None:
                images_features.append(features)
                labels.append(1)
                if (i + 1) % 50 == 0:
                    print(f"  ✓ Loaded {i + 1} fatigue images...")
        print(f"✅ Total fatigue images: {np.sum(np.array(labels) == 1)}")
    
    # Load non-fatigue images (label=0)
    print("\n📁 Loading NonFatigue images...")
    if os.path.exists(non_fatigue_dir):
        non_fatigue_files = [f for f in os.listdir(non_fatigue_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
        for i, filename in enumerate(non_fatigue_files):
            filepath = os.path.join(non_fatigue_dir, filename)
            features = extract_features_from_image(filepath)
            if features is not None:
                images_features.append(features)
                labels.append(0)
                if (i + 1) % 50 == 0:
                    print(f"  ✓ Loaded {i + 1} non-fatigue images...")
        print(f"✅ Total non-fatigue images: {np.sum(np.array(labels) == 0)}")
    
    if len(images_features) == 0:
        print("❌ No images found! Check dataset structure.")
        return None, None
    
    X = np.array(images_features)
    y = np.array(labels)
    
    print(f"\n✅ Total images loaded: {len(X)}")
    print(f"   Feature shape: {X.shape}")
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
    
    print("Training Random Forest (this may take several minutes)...")
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
        'dataset': LOCAL_DATASET_PATH,
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
    print("\n📊 Model Configuration:")
    print(json.dumps(config, indent=2))

def main():
    """Main training pipeline"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " FACIAL FATIGUE DETECTION MODEL TRAINING ".center(68) + "║")
    print("║" + " Using Random Forest + Local Dataset ".center(68) + "║")
    print("╚" + "="*68 + "╝")
    
    # Create directories
    create_model_directory()
    
    # Verify dataset
    if not verify_dataset():
        print("\n❌ Training failed - dataset not found")
        return
    
    # Load and preprocess images
    X, y = load_and_preprocess_images(LOCAL_DATASET_PATH)
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
