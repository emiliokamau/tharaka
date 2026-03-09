"""
Facial Fatigue Detection Model Training Script
==============================================
Trains a CNN model on Kaggle fatigue dataset to predict driver fatigue levels (0-100 scale)
Dataset: https://www.kaggle.com/datasets/rihabkaci99/fatigue-dataset
"""

import os
import numpy as np
import pandas as pd
import cv2
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.model_selection import train_test_split
import pickle
import kagglehub
import json
from pathlib import Path

# Configuration
DATASET_NAME = "rihabkaci99/fatigue-dataset"
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "fatigue_detection_model.h5")
SCALER_PATH = os.path.join(MODEL_DIR, "fatigue_scaler.pkl")
CONFIG_PATH = os.path.join(MODEL_DIR, "model_config.json")
IMAGE_SIZE = (128, 128)
BATCH_SIZE = 32
EPOCHS = 30
VALIDATION_SPLIT = 0.2
TEST_SPLIT = 0.1

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
        print(f"❌ Error downloading dataset: {e}")
        print("Make sure you have:")
        print("  1. Kaggle API key configured (~/.kaggle/kaggle.json)")
        print("  2. Dataset access permission on Kaggle")
        return None

def load_and_preprocess_images(dataset_path, max_samples=None):
    """
    Load images and labels from dataset
    Expected structure: dataset/
        ├── fatigue/ (images labeled as fatigued)
        └── non_fatigue/ (images labeled as not fatigued)
    """
    print("\n" + "="*70)
    print("LOADING AND PREPROCESSING IMAGES")
    print("="*70)
    
    images = []
    labels = []  # 0 = not fatigued, 1 = fatigued
    
    # Check for common directory structures
    possible_paths = [
        (os.path.join(dataset_path, "fatigue"), 1),
        (os.path.join(dataset_path, "Fatigue"), 1),
        (os.path.join(dataset_path, "FATIGUE"), 1),
        (os.path.join(dataset_path, "non_fatigue"), 0),
        (os.path.join(dataset_path, "NonFatigue"), 0),
        (os.path.join(dataset_path, "NON_FATIGUE"), 0),
    ]
    
    fatigue_dir = None
    non_fatigue_dir = None
    
    for path, label in possible_paths:
        if os.path.exists(path):
            if label == 1:
                fatigue_dir = path
                print(f"✅ Found fatigue images at: {path}")
            else:
                non_fatigue_dir = path
                print(f"✅ Found non-fatigue images at: {path}")
    
    # If standard structure not found, check raw dataset structure
    if not fatigue_dir or not non_fatigue_dir:
        print("⚠️  Standard directory structure not found. Listing dataset contents:")
        for root, dirs, files in os.walk(dataset_path):
            level = root.replace(dataset_path, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            for file in files[:3]:  # Show first 3 files
                print(f"{indent}  {file}")
            if level > 2:  # Don't go too deep
                break
    
    # Load fatigue images
    if fatigue_dir:
        count = 0
        for filename in os.listdir(fatigue_dir):
            if max_samples and count >= max_samples:
                break
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                try:
                    img_path = os.path.join(fatigue_dir, filename)
                    img = cv2.imread(img_path)
                    if img is not None:
                        img = cv2.resize(img, IMAGE_SIZE)
                        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        images.append(img)
                        labels.append(1)  # Fatigued = 1
                        count += 1
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
        
        print(f"✅ Loaded {count} fatigue images")
    
    # Load non-fatigue images
    if non_fatigue_dir:
        count = 0
        for filename in os.listdir(non_fatigue_dir):
            if max_samples and count >= max_samples:
                break
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                try:
                    img_path = os.path.join(non_fatigue_dir, filename)
                    img = cv2.imread(img_path)
                    if img is not None:
                        img = cv2.resize(img, IMAGE_SIZE)
                        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        images.append(img)
                        labels.append(0)  # Not fatigued = 0
                        count += 1
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
        
        print(f"✅ Loaded {count} non-fatigue images")
    
    if not images:
        print("❌ No images loaded. Check dataset structure.")
        return None, None
    
    # Convert to numpy arrays and normalize
    images = np.array(images, dtype=np.float32) / 255.0
    labels = np.array(labels)
    
    print(f"📊 Dataset shape: {images.shape}")
    print(f"📊 Labels distribution: Fatigue={np.sum(labels)}, Non-Fatigue={len(labels)-np.sum(labels)}")
    
    return images, labels

def build_cnn_model(input_shape=(128, 128, 3)):
    """
    Build CNN model for binary fatigue classification
    Input: Image (128x128x3)
    Output: Fatigue probability (0-1, converted to 0-100 scale)
    """
    print("\n" + "="*70)
    print("BUILDING CNN MODEL")
    print("="*70)
    
    model = models.Sequential([
        # Block 1
        layers.Conv2D(32, (3, 3), activation='relu', padding='same', input_shape=input_shape),
        layers.BatchNormalization(),
        layers.Conv2D(32, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),
        
        # Block 2
        layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),
        
        # Block 3
        layers.Conv2D(128, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.Conv2D(128, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),
        
        # Block 4
        layers.Conv2D(256, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.Conv2D(256, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),
        
        # Global average pooling
        layers.GlobalAveragePooling2D(),
        
        # Dense layers
        layers.Dense(256, activation='relu'),
        layers.BatchNormalization(),
        layers.Dropout(0.5),
        
        layers.Dense(128, activation='relu'),
        layers.BatchNormalization(),
        layers.Dropout(0.5),
        
        # Output layer (binary classification)
        layers.Dense(1, activation='sigmoid')
    ])
    
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss='binary_crossentropy',
        metrics=['accuracy', keras.metrics.Precision(), keras.metrics.Recall()]
    )
    
    print("✅ Model architecture:")
    model.summary()
    
    return model

def train_model(model, X_train, y_train, X_val, y_val):
    """Train the CNN model"""
    print("\n" + "="*70)
    print("TRAINING MODEL")
    print("="*70)
    
    # Data augmentation for better generalization
    train_datagen = ImageDataGenerator(
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        horizontal_flip=True,
        zoom_range=0.2,
        shear_range=0.2,
        fill_mode='nearest'
    )
    
    # Callbacks
    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=5,
            restore_best_weights=True,
            verbose=1
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=3,
            min_lr=1e-7,
            verbose=1
        ),
        keras.callbacks.ModelCheckpoint(
            MODEL_PATH,
            monitor='val_accuracy',
            save_best_only=True,
            verbose=1
        )
    ]
    
    # Train with data augmentation
    history = model.fit(
        train_datagen.flow(X_train, y_train, batch_size=BATCH_SIZE),
        epochs=EPOCHS,
        validation_data=(X_val, y_val),
        callbacks=callbacks,
        verbose=1
    )
    
    print(f"✅ Model training complete!")
    print(f"   Final train accuracy: {history.history['accuracy'][-1]:.4f}")
    print(f"   Final val accuracy: {history.history['val_accuracy'][-1]:.4f}")
    
    return history

def evaluate_model(model, X_test, y_test):
    """Evaluate model on test set"""
    print("\n" + "="*70)
    print("EVALUATING MODEL")
    print("="*70)
    
    loss, accuracy, precision, recall = model.evaluate(X_test, y_test, verbose=0)
    
    print(f"✅ Test Results:")
    print(f"   Loss: {loss:.4f}")
    print(f"   Accuracy: {accuracy:.4f}")
    print(f"   Precision: {precision:.4f}")
    print(f"   Recall: {recall:.4f}")
    
    return {'loss': loss, 'accuracy': accuracy, 'precision': precision, 'recall': recall}

def save_model_config(metrics):
    """Save model configuration and metrics"""
    config = {
        'model_name': 'Facial Fatigue Detection CNN',
        'input_shape': IMAGE_SIZE + (3,),
        'output_scale': '0-100 (fatigue percentage)',
        'training_date': pd.Timestamp.now().isoformat(),
        'batch_size': BATCH_SIZE,
        'epochs': EPOCHS,
        'image_size': IMAGE_SIZE,
        'test_metrics': metrics,
        'model_file': MODEL_PATH,
        'scaler_file': SCALER_PATH
    }
    
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Model config saved to {CONFIG_PATH}")
    print(json.dumps(config, indent=2))

def main():
    """Main training pipeline"""
    print("\n" + "🚀 "*35)
    print("FACIAL FATIGUE DETECTION - MODEL TRAINING PIPELINE")
    print("🚀 "*35 + "\n")
    
    # Create model directory
    create_model_directory()
    
    # Download dataset
    dataset_path = download_dataset()
    if not dataset_path:
        print("❌ Failed to download dataset. Exiting.")
        return
    
    # Load and preprocess images
    images, labels = load_and_preprocess_images(dataset_path)
    if images is None or len(images) == 0:
        print("❌ Failed to load images. Exiting.")
        return
    
    # Split data: 70% train, 10% test, 20% val (from train)
    X_temp, X_test, y_temp, y_test = train_test_split(
        images, labels, test_size=TEST_SPLIT, random_state=42, stratify=labels
    )
    
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=VALIDATION_SPLIT, random_state=42, stratify=y_temp
    )
    
    print("\n" + "="*70)
    print("DATA SPLIT")
    print("="*70)
    print(f"Training set: {X_train.shape[0]} images")
    print(f"Validation set: {X_val.shape[0]} images")
    print(f"Test set: {X_test.shape[0]} images")
    
    # Build model
    model = build_cnn_model(input_shape=IMAGE_SIZE + (3,))
    
    # Train model
    history = train_model(model, X_train, y_train, X_val, y_val)
    
    # Evaluate model
    metrics = evaluate_model(model, X_test, y_test)
    
    # Save model config
    save_model_config(metrics)
    
    print("\n" + "="*70)
    print("TRAINING COMPLETE ✅")
    print("="*70)
    print(f"Model saved to: {MODEL_PATH}")
    print(f"Config saved to: {CONFIG_PATH}")
    print("\nNext steps:")
    print("1. Review model_config.json for performance metrics")
    print("2. Run model_inference.py to test predictions")
    print("3. Update app.py to use the trained model")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
