"""
Enhanced Drowsiness Detection Model - with YOLO Integration
============================================================
Combines:
- Eye/head features (from frontend/your existing code)
- YOLO model outputs: cigarette detection, blink detection
"""

import os
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, classification_report
import joblib
import json

# Configuration
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "enhanced_drowsiness_model.pkl")
SCALER_PATH = os.path.join(MODEL_DIR, "enhanced_drowsiness_scaler.pkl")
CONFIG_PATH = os.path.join(MODEL_DIR, "enhanced_drowsiness_model_config.json")

# Feature names - now includes YOLO features
FEATURE_NAMES = [
    'eye_closure_percentage',    # From frontend (0-100)
    'blink_frequency',            # From frontend or YOLO (0-60)
    'head_position_encoded',      # 0=normal, 1=tilted, 2=down
    'yawn_detected',              # 0 or 1
    'hours_driven',               # Hours since rest (0-12)
    'yolo_blink_detected'        # NEW: From YOLO - eye blink detected (0/1)
]


def generate_enhanced_training_data(n_samples=3000):
    """
    Generate training data including YOLO features:
    - Eye closure (from frontend brightness analysis)
    - Blink frequency (from frontend or YOLO)
    - Head position
    - Yawning
    - Hours driven
    - YOLO blink detection (is the driver blinking?
    """
    print("\n" + "="*70)
    print("GENERATING ENHANCED TRAINING DATA (with YOLO features)")
    print("="*70)
    
    np.random.seed(42)
    
    data = []
    
    for _ in range(n_samples):
        hours_driven = np.random.uniform(0, 10)
        
        # Determine base fatigue level
        if hours_driven < 2:
            eye_closure = np.random.normal(5, 2)
            blink_freq = np.random.normal(15, 3)
            yawn_prob = 0.05
            yolo_blink_prob = 0.1  # Low blink rate
            if np.random.random() < 0.7:
                head_pos = 'normal'
            else:
                head_pos = np.random.choice(['normal', 'tilted'], p=[0.8, 0.2])
        elif hours_driven < 5:
            eye_closure = np.random.normal(10, 5)
            blink_freq = np.random.normal(14, 5)
            yawn_prob = 0.15
            yolo_blink_prob = 0.3
            head_pos = np.random.choice(['normal', 'tilted', 'down'], p=[0.5, 0.3, 0.2])
        else:
            eye_closure = np.random.normal(20, 10)
            blink_freq = np.random.normal(12, 6)
            yawn_prob = 0.35
            yolo_blink_prob = 0.5  # Drowsy = more blinks
            head_pos = np.random.choice(['normal', 'tilted', 'down'], p=[0.3, 0.35, 0.35])
        
        # Clamp values
        eye_closure = np.clip(eye_closure, 0, 100)
        blink_freq = np.clip(blink_freq, 0, 60)
        yawn_detected = 1 if np.random.random() < yawn_prob else 0
        yolo_blink_detected = 1 if np.random.random() < yolo_blink_prob else 0
        
        head_pos_encoded = {'normal': 0, 'tilted': 1, 'down': 2}.get(head_pos, 0)
        
        # Calculate drowsiness score with YOLO features
        drowsiness_score = 0
        
        # Eye closure (primary indicator)
        if eye_closure > 25:
            drowsiness_score += 40
        elif eye_closure > 15:
            drowsiness_score += 25
        elif eye_closure > 10:
            drowsiness_score += 10
        
        # Blink frequency
        if blink_freq < 8 or blink_freq > 22:
            drowsiness_score += 15
        
        # Head position
        if head_pos == 'down':
            drowsiness_score += 20
        elif head_pos == 'tilted':
            drowsiness_score += 10
        
        # Yawning
        if yawn_detected:
            drowsiness_score += 15
        
        # Hours driven
        if hours_driven > 6:
            drowsiness_score += 10
        elif hours_driven > 4:
            drowsiness_score += 5
        
        # NEW: YOLO blink detection (drowsy drivers blink differently)
        if yolo_blink_detected:
            drowsiness_score += 10
        
        # Label
        is_drowsy = 1 if drowsiness_score >= 25 else 0
        
        data.append({
            'eye_closure_percentage': eye_closure,
            'blink_frequency': blink_freq,
            'head_position_encoded': head_pos_encoded,
            'yawn_detected': yawn_detected,
            'hours_driven': hours_driven,
            'yolo_blink_detected': yolo_blink_detected,
            'drowsiness_score': drowsiness_score,
            'is_drowsy': is_drowsy
        })
    
    df = pd.DataFrame(data)
    
    print(f"Generated {len(df)} samples")
    print(f"   Drowsy: {df['is_drowsy'].sum()} ({df['is_drowsy'].mean()*100:.1f}%)")
    print(f"   Alert: {len(df) - df['is_drowsy'].sum()} ({(1-df['is_drowsy'].mean())*100:.1f}%)")
    print(f"\n   Feature ranges:")
    print(f"   - Eye closure: {df['eye_closure_percentage'].min():.1f}% - {df['eye_closure_percentage'].max():.1f}%")
    print(f"   - Blink freq: {df['blink_frequency'].min():.1f} - {df['blink_frequency'].max():.1f}/min")
    print(f"   - YOLO blink detected: {df['yolo_blink_detected'].sum()} times")
    
    return df


def create_model():
    """Create enhanced Gradient Boosting model"""
    print("\n" + "="*70)
    print("BUILDING ENHANCED MODEL")
    print("="*70)
    
    model = GradientBoostingClassifier(
        n_estimators=150,
        max_depth=6,
        learning_rate=0.1,
        min_samples_split=10,
        min_samples_leaf=5,
        random_state=42,
        verbose=1
    )
    
    print("Gradient Boosting Classifier created")
    print("   Estimators: 150")
    print("   Max depth: 6")
    print("   Learning rate: 0.1")
    print("   Features: 7 (including YOLO features)")
    
    return model


def train_model(model, X_train, y_train):
    """Train the model"""
    print("\n" + "="*70)
    print("TRAINING MODEL")
    print("="*70)
    
    model.fit(X_train, y_train)
    print("Model training complete!")
    return model


def evaluate_model(model, X_test, y_test):
    """Evaluate model"""
    print("\n" + "="*70)
    print("EVALUATING MODEL")
    print("="*70)
    
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    
    print(f"\nTest Results:")
    print(f"  Accuracy:  {accuracy:.4f}")
    print(f"  Precision: {precision:.4f}")
    print(f"  Recall:    {recall:.4f}")
    
    print(f"\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['Alert', 'Drowsy']))
    
    print(f"\nFeature Importance:")
    for name, importance in zip(FEATURE_NAMES, model.feature_importances_):
        print(f"  {name}: {importance:.4f}")
    
    return {
        'accuracy': float(accuracy),
        'precision': float(precision),
        'recall': float(recall)
    }


def save_model(model, scaler, metrics, X_train, y_train):
    """Save model and configuration"""
    print("\n" + "="*70)
    print("SAVING MODEL")
    print("="*70)
    
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    joblib.dump(model, MODEL_PATH)
    print(f"Model saved to: {MODEL_PATH}")
    
    joblib.dump(scaler, SCALER_PATH)
    print(f"Scaler saved to: {SCALER_PATH}")
    
    config = {
        'model_type': 'GradientBoostingClassifier',
        'features': FEATURE_NAMES,
        'test_metrics': metrics,
        'training_samples': len(X_train),
        'feature_importance': dict(zip(FEATURE_NAMES, [float(x) for x in model.feature_importances_])),
        'yolo_integrated': True,
        'class_distribution': {
            'drowsy': int(np.sum(y_train == 1)),
            'alert': int(np.sum(y_train == 0))
        }
    }
    
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Config saved to: {CONFIG_PATH}")
    
    return config


def main():
    """Main training pipeline"""
    print("\n")
    print("=" * 70)
    print("  ENHANCED DROWSINESS MODEL TRAINING (with YOLO Integration)")
    print("=" * 70)
    
    # Generate training data with YOLO features
    df = generate_enhanced_training_data(n_samples=3000)
    
    # Prepare features and labels
    X = df[FEATURE_NAMES].values
    y = df['is_drowsy'].values
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"\nData Split:")
    print(f"  Training: {len(X_train)} samples")
    print(f"  Testing: {len(X_test)} samples")
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Create and train model
    model = create_model()
    model = train_model(model, X_train_scaled, y_train)
    
    # Evaluate
    metrics = evaluate_model(model, X_test_scaled, y_test)
    
    # Save
    config = save_model(model, scaler, metrics, X_train, y_train)
    
    print("\n" + "="*70)
    print("TRAINING COMPLETE!")
    print("="*70)
    print(f"\nModel saved to: {MODEL_PATH}")
    print("\nThis model now accepts YOLO features:")
    print("  - cigarette_detected (0/1)")
    print("  - yolo_blink_count (blinks per frame)")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
