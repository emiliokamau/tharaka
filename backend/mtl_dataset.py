"""
Multi-Task Learning Dataset for Driver Monitoring System (DMS)
Handles missing labels using placeholder values (-1)

Dataset Structure:
- Eye State: Binary classification (0=Closed, 1=Open) - Available in ALL datasets
- Gaze Direction: Regression (yaw, pitch) - Available in SOME datasets  
- Distraction Detection: Multi-class classification - Available in SOME datasets

Usage:
    dataset = MultiTaskDataset(
        data_root="path/to/data",
        datasets=["kenyan_night", "nvidia", "youtube_face"],
        transform=train_transform
    )
"""

import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field

import torch
from torch.utils.data import Dataset
from PIL import Image
import cv2


# Constants for missing label placeholder
MISSING_LABEL = -1
DEFAULT_IMAGE_SIZE = (64, 64)


@dataclass
class TaskConfig:
    """Configuration for each task head"""
    name: str
    task_type: str  # "classification" or "regression"
    num_classes: int = 2  # For classification
    loss_weight: float = 1.0  # For weighted loss balancing


class MultiTaskDataset(Dataset):
    """
    Unified Dataset for Multi-Task Learning that handles missing labels.
    
    Key Features:
    - Uses -1 as placeholder for missing labels
    - Supports multiple datasets with different label availability
    - Handles eye state (always present), gaze (optional), distraction (optional)
    """
    
    # Default task configurations
    DEFAULT_TASKS = [
        TaskConfig(name="eye_state", task_type="classification", num_classes=2, loss_weight=1.0),
        TaskConfig(name="gaze_yaw", task_type="regression", num_classes=1, loss_weight=0.5),
        TaskConfig(name="gaze_pitch", task_type="regression", num_classes=1, loss_weight=0.5),
        TaskConfig(name="distraction", task_type="classification", num_classes=5, loss_weight=0.8),
    ]
    
    def __init__(
        self,
        data_root: str,
        datasets: List[str],
        split: str = "train",
        transform: Optional[Callable] = None,
        image_size: Tuple[int, int] = DEFAULT_IMAGE_SIZE,
        tasks: Optional[List[TaskConfig]] = None,
        cache_images: bool = False,
    ):
        """
        Args:
            data_root: Root directory containing dataset folders
            datasets: List of dataset names to load (e.g., ["kenyan_night", "nvidia"])
            split: "train", "val", or "test"
            transform: Albumentations transform pipeline
            image_size: Target image size (H, W)
            tasks: Custom task configurations (uses DEFAULT_TASKS if None)
            cache_images: Whether to cache images in memory
        """
        self.data_root = Path(data_root)
        self.datasets = datasets
        self.split = split
        self.transform = transform
        self.image_size = image_size
        self.tasks = tasks or self.DEFAULT_TASKS
        self.cache_images = cache_images
        self.image_cache = {}
        
        # Build sample index and metadata
        self.samples = self._load_samples()
        
        # Compute class weights for imbalanced datasets
        self.class_weights = self._compute_class_weights()
        
    def _load_samples(self) -> List[Dict[str, Any]]:
        """Load all samples from specified datasets"""
        samples = []
        
        for dataset_name in self.datasets:
            dataset_path = self.data_root / dataset_name
            
            # Try different directory structures
            split_path = dataset_path / self.split
            if not split_path.exists():
                split_path = dataset_path
                
            # Load based on dataset format
            if (dataset_path / "annotations.csv").exists():
                samples.extend(self._load_csv_dataset(dataset_path, dataset_name))
            elif (dataset_path / "annotations.json").exists():
                samples.extend(self._load_json_dataset(dataset_path, dataset_name))
            else:
                # Assume image directory structure
                samples.extend(self._load_image_dir(split_path, dataset_name))
                
        print(f"Loaded {len(samples)} samples from {len(self.datasets)} datasets")
        return samples
    
    def _load_csv_dataset(self, dataset_path: Path, dataset_name: str) -> List[Dict]:
        """Load dataset from CSV annotations"""
        samples = []
        split = self.split if (dataset_path / self.split).exists() else ""
        
        # Try different CSV file names
        for csv_name in [f"{split}_annotations.csv", "annotations.csv", f"{dataset_name}_annotations.csv"]:
            csv_path = dataset_path / csv_name
            if csv_path.exists():
                break
                
        if not csv_path.exists():
            return samples
            
        df = pd.read_csv(csv_path)
        
        for idx, row in df.iterrows():
            sample = {
                "image_path": dataset_path / row.get("image_path", row.get("filename", "")),
                "dataset": dataset_name,
                # Eye state (required) - convert to binary
                "eye_state": int(row.get("eye_state", MISSING_LABEL)),
                # Gaze direction (optional)
                "gaze_yaw": float(row.get("gaze_yaw", row.get("yaw", MISSING_LABEL))),
                "gaze_pitch": float(row.get("gaze_pitch", row.get("pitch", MISSING_LABEL))),
                # Distraction (optional)
                "distraction": int(row.get("distraction", row.get("label", MISSING_LABEL))),
            }
            
            # Validate that at least eye_state is present
            if sample["eye_state"] != MISSING_LABEL:
                samples.append(sample)
                
        return samples
    
    def _load_json_dataset(self, dataset_path: Path, dataset_name: str) -> List[Dict]:
        """Load dataset from JSON annotations"""
        samples = []
        json_path = dataset_path / "annotations.json"
        
        if not json_path.exists():
            return samples
            
        with open(json_path, 'r') as f:
            annotations = json.load(f)
            
        for img_name, labels in annotations.items():
            sample = {
                "image_path": dataset_path / "images" / img_name,
                "dataset": dataset_name,
                "eye_state": labels.get("eye_state", MISSING_LABEL),
                "gaze_yaw": labels.get("gaze_yaw", MISSING_LABEL),
                "gaze_pitch": labels.get("gaze_pitch", MISSING_LABEL),
                "distraction": labels.get("distraction", MISSING_LABEL),
            }
            
            if sample["eye_state"] != MISSING_LABEL:
                samples.append(sample)
                
        return samples
    
    def _load_image_dir(self, dir_path: Path, dataset_name: str) -> List[Dict]:
        """Load dataset from image directory structure"""
        samples = []
        
        if not dir_path.exists():
            return samples
            
        # Assume subdirectories are labels (for eye state)
        for label_dir in dir_path.iterdir():
            if not label_dir.is_dir():
                continue
                
            eye_state = 1 if label_dir.name.lower() == "open" else 0
                
            for img_path in label_dir.glob("*.jpg"):
                samples.append({
                    "image_path": img_path,
                    "dataset": dataset_name,
                    "eye_state": eye_state,
                    "gaze_yaw": MISSING_LABEL,
                    "gaze_pitch": MISSING_LABEL,
                    "distraction": MISSING_LABEL,
                })
                
        return samples
    
    def _compute_class_weights(self) -> Dict[str, torch.Tensor]:
        """Compute class weights for handling imbalanced data"""
        weights = {}
        
        # Eye state class weights
        eye_states = [s["eye_state"] for s in self.samples if s["eye_state"] != MISSING_LABEL]
        if eye_states:
            eye_counts = np.bincount(eye_states, minlength=2)
            weights["eye_state"] = torch.FloatTensor(1.0 / (eye_counts + 1e-6))
            weights["eye_state"] = weights["eye_state"] / weights["eye_state"].sum()
            
        # Distraction class weights
        distractions = [s["distraction"] for s in self.samples if s["distraction"] != MISSING_LABEL]
        if distractions:
            num_classes = max(distractions) + 1
            dist_counts = np.bincount(distractions, minlength=num_classes)
            weights["distraction"] = torch.FloatTensor(1.0 / (dist_counts + 1e-6))
            weights["distraction"] = weights["distraction"] / weights["distraction"].sum()
            
        return weights
    
    def __len__(self) -> int:
        return len(self.samples)
    
    def __getitem__(self, idx: int) -> Dict[str, Any]:
        """Get a single sample with all available labels"""
        sample = self.samples[idx]
        
        # Load and preprocess image
        image = self._load_image(sample["image_path"])
        
        # Apply transforms
        if self.transform:
            transformed = self.transform(image=image)
            image = transformed["image"]
        
        # Convert to tensor
        if isinstance(image, np.ndarray):
            image = torch.from_numpy(image).permute(2, 0, 1).float() / 255.0
        elif isinstance(image, Image.Image):
            image = torch.from_numpy(np.array(image)).permute(2, 0, 1).float() / 255.0
            
        # Prepare labels (use MISSING_LABEL for missing data)
        labels = {
            "eye_state": torch.tensor(sample["eye_state"], dtype=torch.long),
            "gaze_yaw": torch.tensor(sample["gaze_yaw"], dtype=torch.float32),
            "gaze_pitch": torch.tensor(sample["gaze_pitch"], dtype=torch.float32),
            "distraction": torch.tensor(sample["distraction"], dtype=torch.long),
        }
        
        # Create masks for available labels (True = valid, False = missing)
        masks = {
            "eye_state": sample["eye_state"] != MISSING_LABEL,
            "gaze_yaw": sample["gaze_yaw"] != MISSING_LABEL,
            "gaze_pitch": sample["gaze_pitch"] != MISSING_LABEL,
            "distraction": sample["distraction"] != MISSING_LABEL,
        }
        
        return {
            "image": image,
            "labels": labels,
            "masks": masks,
            "dataset": sample["dataset"],
            "image_path": str(sample["image_path"]),
        }
    
    def _load_image(self, path: Path) -> np.ndarray:
        """Load image from disk (handles non-ASCII paths on Windows)"""
        if self.cache_images and str(path) in self.image_cache:
            return self.image_cache[str(path)]
            
        try:
            # Try cv2 first (faster)
            image = cv2.imread(str(path))
            if image is None:
                # Fallback to PIL (handles Unicode paths better on Windows)
                image = np.array(Image.open(path).convert("RGB"))
            else:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                
            # Resize to target size
            image = cv2.resize(image, self.image_size)
            
            if self.cache_images:
                self.image_cache[str(path)] = image
                
            return image
            
        except Exception as e:
            # Return blank image on error
            print(f"Error loading image {path}: {e}")
            return np.zeros((*self.image_size, 3), dtype=np.uint8)
    
    def get_task_stats(self) -> Dict[str, Dict]:
        """Get statistics about available labels for each task"""
        stats = {
            "eye_state": {"available": 0, "missing": 0},
            "gaze_yaw": {"available": 0, "missing": 0},
            "gaze_pitch": {"available": 0, "missing": 0},
            "distraction": {"available": 0, "missing": 0},
        }
        
        for sample in self.samples:
            for task in stats.keys():
                if sample[task] != MISSING_LABEL:
                    stats[task]["available"] += 1
                else:
                    stats[task]["missing"] += 1
                    
        return stats


def create_mtl_dataloader(
    data_root: str,
    datasets: List[str],
    split: str = "train",
    batch_size: int = 32,
    num_workers: int = 4,
    transform: Optional[Callable] = None,
    shuffle: bool = True,
    image_size: Tuple[int, int] = (64, 64),
) -> torch.utils.data.DataLoader:
    """Factory function to create a DataLoader with MTL Dataset"""
    
    dataset = MultiTaskDataset(
        data_root=data_root,
        datasets=datasets,
        split=split,
        transform=transform,
        image_size=image_size,
    )
    
    return torch.utils.data.DataLoader(
        dataset,
        batch_size=batch_size,
        num_workers=num_workers,
        shuffle=shuffle,
        pin_memory=True,
        drop_last=(split == "train"),
    )
