"""
MTL (Multi-Task Learning) Model Training Script
================================================
Trains the PyTorch MTL model for driver drowsiness detection.
Generates synthetic training data if no real data is available.

Tasks:
- Eye State Detection (binary: open/closed)
- Gaze Estimation (regression: yaw, pitch)  
- Distraction Detection (5-class classification)

Usage:
    python train_mtl_model.py
"""

import os
import sys
import json
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image
import random
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from mtl_inference import SimpleMTLModel

# Configuration
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "mtl_model.pth")
CONFIG_PATH = os.path.join(MODEL_DIR, "mtl_config.json")
IMAGE_SIZE = (64, 64)
NUM_EPOCHS = 50
BATCH_SIZE = 32
LEARNING_RATE = 0.001
TRAIN_SAMPLES = 1000  # Synthetic training samples
VAL_SAMPLES = 200     # Synthetic validation samples

# Create models directory if it doesn't exist
os.makedirs(MODEL_DIR, exist_ok=True)


class SyntheticDriverDataset(Dataset):
    """
    Synthetic dataset for driver monitoring.
    Generates realistic-looking face images with various eye states,
    gaze directions, and distraction levels.
    """
    
    def __init__(self, num_samples, image_size=(64, 64), split='train'):
        self.num_samples = num_samples
        self.image_size = image_size
        self.split = split
        
        # Task configurations
        self.num_classes_eye = 2  # open/closed
        self.num_classes_distraction = 5  # 5 distraction levels
        
    def __len__(self):
        return self.num_samples
    
    def generate_face_image(self):
        """Generate a synthetic grayscale face-like image"""
        # Create base image (grayscale face-like shape)
        img = np.zeros((self.image_size[0], self.image_size[1], 3), dtype=np.uint8)
        
        # Fill with skin-like color (varies slightly)
        skin_tone = random.randint(180, 220)
        img[:, :] = [skin_tone, skin_tone - 20, skin_tone - 40]  # BGR format
        
        # Add some noise for realism
        noise = np.random.randint(-20, 20, img.shape, dtype=np.int16)
        img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        # Add ellipse for face outline (darker)
        center = (self.image_size[1] // 2, self.image_size[0] // 2)
        y, x = np.ogrid[:self.image_size[0], :self.image_size[1]]
        mask = ((x - center[0])**2 / 400 + (y - center[1])**2 / 500) > 1
        img[mask] = np.clip(img[mask].astype(np.int16) - 40, 0, 255).astype(np.uint8)
        
        return img
    
    def __getitem__(self, idx):
        # Generate synthetic image
        img = self.generate_face_image()
        
        # Convert to tensor
        img_pil = Image.fromarray(img)
        
        # Define transforms
        transform = transforms.Compose([
            transforms.Resize(self.image_size),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        img_tensor = transform(img_pil)
        
        # Generate synthetic labels
        # Eye state: 0=closed, 1=open
        eye_state = random.randint(0, 1)
        
        # Gaze: yaw and pitch angles (in radians, normalized to -1 to 1)
        gaze_yaw = random.uniform(-1, 1)
        gaze_pitch = random.uniform(-1, 1)
        
        # Distraction: 0-4 (5 classes)
        distraction = random.randint(0, 4)
        
        # Add some correlation: closed eyes more likely with high distraction
        if random.random() < 0.7:
            eye_state = 0  # closed
            distraction = random.randint(3, 4)  # high distraction
        
        # Return as dictionary
        labels = {
            'eye_state': torch.tensor(eye_state, dtype=torch.long),
            'gaze_yaw': torch.tensor(gaze_yaw, dtype=torch.float32),
            'gaze_pitch': torch.tensor(gaze_pitch, dtype=torch.float32),
            'distraction': torch.tensor(distraction, dtype=torch.long)
        }
        
        return img_tensor, labels


def train_epoch(model, dataloader, criterion_eye, criterion_gaze, criterion_distraction, 
                optimizer, device):
    """Train for one epoch"""
    model.train()
    total_loss = 0
    correct_eye = 0
    correct_distraction = 0
    total = 0
    
    for batch_idx, (images, labels) in enumerate(dataloader):
        images = images.to(device)
        
        eye_labels = labels['eye_state'].to(device)
        gaze_yaw_labels = labels['gaze_yaw'].to(device)
        gaze_pitch_labels = labels['gaze_pitch'].to(device)
        distraction_labels = labels['distraction'].to(device)
        
        optimizer.zero_grad()
        
        # Forward pass - model returns a dictionary
        outputs = model(images)
        eye_output = outputs['eye_state']
        gaze_output = torch.cat([outputs['gaze_yaw'], outputs['gaze_pitch']], dim=1)
        distraction_output = outputs['distraction']
        
        # Calculate losses
        loss_eye = criterion_eye(eye_output, eye_labels)
        loss_gaze_yaw = criterion_gaze(gaze_output[:, 0], gaze_yaw_labels)
        loss_gaze_pitch = criterion_gaze(gaze_output[:, 1], gaze_pitch_labels)
        loss_distraction = criterion_distraction(distraction_output, distraction_labels)
        
        # Combined loss (weighted)
        loss = loss_eye + 0.5 * (loss_gaze_yaw + loss_gaze_pitch) + 0.8 * loss_distraction
        
        # Backward pass
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        
        # Calculate accuracy
        _, predicted_eye = torch.max(eye_output.data, 1)
        total += eye_labels.size(0)
        correct_eye += (predicted_eye == eye_labels).sum().item()
        
        _, predicted_dist = torch.max(distraction_output.data, 1)
        correct_distraction += (predicted_dist == distraction_labels).sum().item()
    
    avg_loss = total_loss / len(dataloader)
    eye_acc = 100.0 * correct_eye / total
    dist_acc = 100.0 * correct_distraction / total
    
    return avg_loss, eye_acc, dist_acc


def validate(model, dataloader, criterion_eye, criterion_gaze, criterion_distraction, device):
    """Validate the model"""
    model.eval()
    total_loss = 0
    correct_eye = 0
    correct_distraction = 0
    total = 0
    
    with torch.no_grad():
        for images, labels in dataloader:
            images = images.to(device)
            
            eye_labels = labels['eye_state'].to(device)
            gaze_yaw_labels = labels['gaze_yaw'].to(device)
            gaze_pitch_labels = labels['gaze_pitch'].to(device)
            distraction_labels = labels['distraction'].to(device)
            
            # Forward pass - model returns a dictionary
            outputs = model(images)
            eye_output = outputs['eye_state']
            gaze_output = torch.cat([outputs['gaze_yaw'], outputs['gaze_pitch']], dim=1)
            distraction_output = outputs['distraction']
            
            # Calculate losses
            loss_eye = criterion_eye(eye_output, eye_labels)
            loss_gaze_yaw = criterion_gaze(gaze_output[:, 0], gaze_yaw_labels)
            loss_gaze_pitch = criterion_gaze(gaze_output[:, 1], gaze_pitch_labels)
            loss_distraction = criterion_distraction(distraction_output, distraction_labels)
            
            loss = loss_eye + 0.5 * (loss_gaze_yaw + loss_gaze_pitch) + 0.8 * loss_distraction
            
            total_loss += loss.item()
            
            # Calculate accuracy
            _, predicted_eye = torch.max(eye_output.data, 1)
            total += eye_labels.size(0)
            correct_eye += (predicted_eye == eye_labels).sum().item()
            
            _, predicted_dist = torch.max(distraction_output.data, 1)
            correct_distraction += (predicted_dist == distraction_labels).sum().item()
    
    avg_loss = total_loss / len(dataloader)
    eye_acc = 100.0 * correct_eye / total
    dist_acc = 100.0 * correct_distraction / total
    
    return avg_loss, eye_acc, dist_acc


def collate_fn(batch):
    """Custom collate function for the dataset"""
    images = torch.stack([item[0] for item in batch])
    labels = {
        'eye_state': torch.stack([item[1]['eye_state'] for item in batch]),
        'gaze_yaw': torch.stack([item[1]['gaze_yaw'] for item in batch]),
        'gaze_pitch': torch.stack([item[1]['gaze_pitch'] for item in batch]),
        'distraction': torch.stack([item[1]['distraction'] for item in batch])
    }
    return images, labels


def main():
    print("=" * 60)
    print("MTL Model Training - Driver Drowsiness Detection")
    print("=" * 60)
    
    # Set device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"\nUsing device: {device}")
    
    # Create datasets
    print(f"\nGenerating synthetic training data ({TRAIN_SAMPLES} samples)...")
    train_dataset = SyntheticDriverDataset(TRAIN_SAMPLES, IMAGE_SIZE, 'train')
    val_dataset = SyntheticDriverDataset(VAL_SAMPLES, IMAGE_SIZE, 'val')
    
    # Create data loaders
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, collate_fn=collate_fn)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, collate_fn=collate_fn)
    
    print(f"Training batches: {len(train_loader)}")
    print(f"Validation batches: {len(val_loader)}")
    
    # Create model
    print("\nInitializing MTL model...")
    model = SimpleMTLModel(num_classes_eye=2, num_classes_distraction=5)
    model = model.to(device)
    
    # Print model summary
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Total parameters: {total_params:,}")
    print(f"Trainable parameters: {trainable_params:,}")
    
    # Define loss functions
    criterion_eye = nn.CrossEntropyLoss()
    criterion_gaze = nn.MSELoss()
    criterion_distraction = nn.CrossEntropyLoss()
    
    # Define optimizer
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    
    # Learning rate scheduler
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=15, gamma=0.5)
    
    # Training history
    history = {
        'train_loss': [],
        'val_loss': [],
        'train_eye_acc': [],
        'val_eye_acc': [],
        'train_dist_acc': [],
        'val_dist_acc': []
    }
    
    best_val_loss = float('inf')
    
    # Training loop
    print("\n" + "=" * 60)
    print("Starting training...")
    print("=" * 60)
    
    for epoch in range(NUM_EPOCHS):
        # Train
        train_loss, train_eye_acc, train_dist_acc = train_epoch(
            model, train_loader, criterion_eye, criterion_gaze, 
            criterion_distraction, optimizer, device
        )
        
        # Validate
        val_loss, val_eye_acc, val_dist_acc = validate(
            model, val_loader, criterion_eye, criterion_gaze, 
            criterion_distraction, device
        )
        
        # Update scheduler
        scheduler.step()
        
        # Save history
        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_loss)
        history['train_eye_acc'].append(train_eye_acc)
        history['val_eye_acc'].append(val_eye_acc)
        history['train_dist_acc'].append(train_dist_acc)
        history['val_dist_acc'].append(val_dist_acc)
        
        # Print progress
        print(f"Epoch [{epoch+1:2d}/{NUM_EPOCHS}] "
              f"Train Loss: {train_loss:.4f} | "
              f"Val Loss: {val_loss:.4f} | "
              f"Eye Acc: {val_eye_acc:.1f}% | "
              f"Dist Acc: {val_dist_acc:.1f}%")
        
        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_loss': val_loss,
                'val_eye_acc': val_eye_acc,
                'val_dist_acc': val_dist_acc,
            }, MODEL_PATH)
            print(f"  [*] Saved best model (val_loss: {val_loss:.4f})")
    
    # Save training history
    history_path = os.path.join(MODEL_DIR, "mtl_training_history.json")
    with open(history_path, 'w') as f:
        json.dump(history, f, indent=2)
    
    # Save config
    config = {
        'model_type': 'SimpleMTLModel',
        'image_size': IMAGE_SIZE,
        'num_classes_eye': 2,
        'num_classes_distraction': 5,
        'num_epochs': NUM_EPOCHS,
        'batch_size': BATCH_SIZE,
        'learning_rate': LEARNING_RATE,
        'train_samples': TRAIN_SAMPLES,
        'val_samples': VAL_SAMPLES,
        'best_val_loss': best_val_loss,
        'final_val_eye_acc': history['val_eye_acc'][-1],
        'final_val_dist_acc': history['val_dist_acc'][-1],
        'trained_at': datetime.now().isoformat()
    }
    
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("\n" + "=" * 60)
    print("Training Complete!")
    print("=" * 60)
    print(f"\nModel saved to: {MODEL_PATH}")
    print(f"Config saved to: {CONFIG_PATH}")
    print(f"History saved to: {history_path}")
    print(f"\nBest validation loss: {best_val_loss:.4f}")
    print(f"Final eye detection accuracy: {history['val_eye_acc'][-1]:.1f}%")
    print(f"Final distraction detection accuracy: {history['val_dist_acc'][-1]:.1f}%")
    
    return model, history


if __name__ == "__main__":
    main()
