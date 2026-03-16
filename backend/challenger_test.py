"""
Challenger: Head-to-Head Model Comparison Script

Compares an OLD model vs NEW MTL model on the same test set
(Kenan night driving data) and outputs a side-by-side table of:

- Inference Latency (ms)
- Eye State Accuracy (%)
- Gaze Error (Mean Squared Error)

Usage:
    python challenger_test.py \
        --old-model models/archive/v1.0-basic-eye/model.pth \
        --new-model models/v2.0-mtl-kenyan/model.pth \
        --test-data data/kenyan_night_test \
        --output results/challenger_results.json
        
Or run programmatically:
    results = run_challenger_comparison(old_model, new_model, test_loader)
    print(results.to_string())
"""

import argparse
import json
import time
import numpy as np
import torch
import torch.nn as nn
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import pandas as pd
import sys


@dataclass
class ModelResult:
    """Results from testing a single model"""
    name: str
    inference_latency_ms: float
    eye_state_accuracy: float
    gaze_mse: float
    gaze_mae: float
    distraction_accuracy: float
    num_samples: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "inference_latency_ms": self.inference_latency_ms,
            "eye_state_accuracy_pct": self.eye_state_accuracy * 100,
            "gaze_mse": self.gaze_mse,
            "gaze_mae": self.gaze_mae,
            "distraction_accuracy_pct": self.distraction_accuracy * 100,
            "num_samples": self.num_samples,
        }


class ChallengerComparison:
    """
    Head-to-head comparison of two models.
    
    Handles different model architectures and output formats:
    - Old models: May only output eye_state
    - New MTL models: Output eye_state, gaze, distraction
    """
    
    def __init__(
        self,
        old_model: nn.Module,
        new_model: nn.Module,
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
    ):
        self.old_model = old_model.to(device).eval()
        self.new_model = new_model.to(device).eval()
        self.device = device
        
    def test_old_model(
        self,
        test_loader: torch.utils.data.DataLoader,
    ) -> ModelResult:
        """Test the old/legacy model"""
        correct_eye = 0
        total_eye = 0
        total_gaze_mse = 0
        total_gaze_mae = 0
        
        latencies = []
        
        with torch.no_grad():
            for batch in test_loader:
                images = batch["image"].to(self.device)
                labels = batch["labels"]
                masks = batch["masks"]
                
                # Time inference
                start_time = time.perf_counter()
                outputs = self.old_model(images)
                latency = (time.perf_counter() - start_time) * 1000  # ms
                latencies.append(latency)
                
                # Extract eye state predictions
                if isinstance(outputs, dict):
                    eye_pred = outputs.get("eye_state", outputs.get("logits"))
                else:
                    eye_pred = outputs
                    
                # Get valid labels
                eye_labels = labels["eye_state"].to(self.device)
                eye_mask = masks["eye_state"].to(self.device)
                
                valid_eye = eye_mask & (eye_labels >= 0)
                if valid_eye.any():
                    # Compute accuracy
                    if eye_pred.dim() > 1:
                        pred_class = torch.argmax(eye_pred, dim=-1)
                    else:
                        pred_class = (torch.sigmoid(eye_pred) > 0.5).long()
                        
                    correct = (pred_class == eye_labels).sum().item()
                    correct_eye += correct
                    total_eye += valid_eye.sum().item()
                    
        # Calculate metrics
        avg_latency = np.mean(latencies)
        eye_accuracy = correct_eye / max(1, total_eye)
        gaze_mse = 0  # Old model doesn't have gaze
        gaze_mae = 0
        
        return ModelResult(
            name="Old Model (Legacy)",
            inference_latency_ms=avg_latency,
            eye_state_accuracy=eye_accuracy,
            gaze_mse=gaze_mse,
            gaze_mae=gaze_mae,
            distraction_accuracy=0.0,
            num_samples=len(test_loader.dataset),
        )
        
    def test_new_model(
        self,
        test_loader: torch.utils.data.DataLoader,
    ) -> ModelResult:
        """Test the new MTL model"""
        correct_eye = 0
        total_eye = 0
        total_gaze_mse = 0
        total_gaze_mae = 0
        correct_dist = 0
        total_dist = 0
        
        latencies = []
        
        with torch.no_grad():
            for batch in test_loader:
                images = batch["image"].to(self.device)
                labels = batch["labels"]
                masks = batch["masks"]
                
                # Time inference
                start_time = time.perf_counter()
                outputs = self.new_model(images)
                latency = (time.perf_counter() - start_time) * 1000
                latencies.append(latency)
                
                # Extract predictions
                eye_pred = outputs.get("eye_state")
                gaze_pred = outputs.get("gaze")
                dist_pred = outputs.get("distraction")
                
                # Eye state accuracy
                eye_labels = labels["eye_state"].to(self.device)
                eye_mask = masks["eye_state"].to(self.device)
                
                valid_eye = eye_mask & (eye_labels >= 0)
                if valid_eye.any() and eye_pred is not None:
                    if eye_pred.dim() > 1:
                        pred_class = torch.argmax(eye_pred, dim=-1)
                    else:
                        pred_class = (torch.sigmoid(eye_pred) > 0.5).long()
                        
                    correct = (pred_class == eye_labels).sum().item()
                    correct_eye += correct
                    total_eye += valid_eye.sum().item()
                    
                # Gaze MSE
                if gaze_pred is not None:
                    gaze_labels_yaw = labels["gaze_yaw"].to(self.device)
                    gaze_labels_pitch = labels["gaze_pitch"].to(self.device)
                    gaze_mask = masks["gaze_yaw"].to(self.device)
                    
                    valid_gaze = gaze_mask & (gaze_labels_yaw >= 0)
                    if valid_gaze.any():
                        pred_yaw = gaze_pred[:, 0]
                        pred_pitch = gaze_pred[:, 1]
                        
                        mse = ((pred_yaw - gaze_labels_yaw) ** 2).mean().item()
                        mae = torch.abs(pred_yaw - gaze_labels_yaw).mean().item()
                        
                        total_gaze_mse += mse
                        total_gaze_mae += mae
                        
                # Distraction accuracy
                if dist_pred is not None:
                    dist_labels = labels["distraction"].to(self.device)
                    dist_mask = masks["distraction"].to(self.device)
                    
                    valid_dist = dist_mask & (dist_labels >= 0)
                    if valid_dist.any():
                        if dist_pred.dim() > 1:
                            pred_class = torch.argmax(dist_pred, dim=-1)
                        else:
                            pred_class = (torch.sigmoid(dist_pred) > 0.5).long()
                            
                        correct = (pred_class == dist_labels).sum().item()
                        correct_dist += correct
                        total_dist += valid_dist.sum().item()
                        
        # Calculate metrics
        avg_latency = np.mean(latencies)
        eye_accuracy = correct_eye / max(1, total_eye)
        gaze_mse = total_gaze_mse / max(1, len(test_loader))
        gaze_mae = total_gaze_mae / max(1, len(test_loader))
        dist_accuracy = correct_dist / max(1, total_dist)
        
        return ModelResult(
            name="New Model (MTL)",
            inference_latency_ms=avg_latency,
            eye_state_accuracy=eye_accuracy,
            gaze_mse=gaze_mse,
            gaze_mae=gaze_mae,
            distraction_accuracy=dist_accuracy,
            num_samples=len(test_loader.dataset),
        )
        
    def run_comparison(
        self,
        test_loader: torch.utils.data.DataLoader,
    ) -> Tuple[ModelResult, ModelResult]:
        """Run full comparison"""
        print("Testing Old Model (Legacy)...")
        old_result = self.test_old_model(test_loader)
        
        print("Testing New Model (MTL)...")
        new_result = self.test_new_model(test_loader)
        
        return old_result, new_result
        
    def print_comparison(self, old_result: ModelResult, new_result: ModelResult):
        """Print side-by-side comparison table"""
        print("\n" + "="*70)
        print("CHALLENGER MODEL COMPARISON RESULTS")
        print("="*70)
        
        # Create comparison table
        comparison = pd.DataFrame([
            {
                "Metric": "Inference Latency (ms)",
                "Old Model": f"{old_result.inference_latency_ms:.2f}",
                "New Model": f"{new_result.inference_latency_ms:.2f}",
                "Winner": self._get_winner(
                    old_result.inference_latency_ms,
                    new_result.inference_latency_ms,
                    lower_better=True,
                ),
            },
            {
                "Metric": "Eye State Accuracy (%)",
                "Old Model": f"{old_result.eye_state_accuracy*100:.1f}%",
                "New Model": f"{new_result.eye_state_accuracy*100:.1f}%",
                "Winner": self._get_winner(
                    old_result.eye_state_accuracy,
                    new_result.eye_state_accuracy,
                    lower_better=False,
                ),
            },
            {
                "Metric": "Gaze Direction MSE",
                "Old Model": "N/A",
                "New Model": f"{new_result.gaze_mse:.4f}",
                "Winner": "N/A" if old_result.gaze_mse == 0 else "",
            },
            {
                "Metric": "Gaze Direction MAE",
                "Old Model": "N/A",
                "New Model": f"{new_result.gaze_mae:.4f}",
                "Winner": "N/A" if old_result.gaze_mae == 0 else "",
            },
            {
                "Metric": "Distraction Detection (%)",
                "Old Model": "N/A",
                "New Model": f"{new_result.distraction_accuracy*100:.1f}%",
                "Winner": "N/A" if old_result.distraction_accuracy == 0 else "",
            },
        ])
        
        print(comparison.to_string(index=False))
        print("="*70)
        
        # Summary
        print("\nSUMMARY:")
        if new_result.eye_state_accuracy > old_result.eye_state_accuracy:
            improvement = (new_result.eye_state_accuracy - old_result.eye_state_accuracy) * 100
            print(f"✓ New model improves eye accuracy by {improvement:.1f}%")
        elif new_result.eye_state_accuracy < old_result.eye_state_accuracy:
            degradation = (old_result.eye_state_accuracy - new_result.eye_state_accuracy) * 100
            print(f"✗ New model degrades eye accuracy by {degradation:.1f}%")
        else:
            print("= Eye accuracy is the same")
            
        if new_result.inference_latency_ms < old_result.inference_latency_ms:
            speedup = old_result.inference_latency_ms / new_result.inference_latency_ms
            print(f"✓ New model is {speedup:.1f}x faster")
        elif new_result.inference_latency_ms > old_result.inference_latency_ms:
            slowdown = new_result.inference_latency_ms / old_result.inference_latency_ms
            print(f"✗ New model is {slowdown:.1f}x slower")
            
    def _get_winner(
        self, 
        old_val: float, 
        new_val: float, 
        lower_better: bool = False
    ) -> str:
        """Determine winner for a metric"""
        if lower_better:
            if new_val < old_val:
                return "← New"
            elif new_val > old_val:
                return "→ Old"
            else:
                return "="
        else:
            if new_val > old_val:
                return "← New"
            elif new_val < old_val:
                return "→ Old"
            else:
                return "="
                
    def save_results(
        self,
        old_result: ModelResult,
        new_result: ModelResult,
        output_path: str,
    ):
        """Save results to JSON"""
        results = {
            "old_model": old_result.to_dict(),
            "new_model": new_result.to_dict(),
            "comparison": {
                "eye_accuracy_improvement": (
                    new_result.eye_state_accuracy - old_result.eye_state_accuracy
                ) * 100,
                "latency_change_ms": (
                    new_result.inference_latency_ms - old_result.inference_latency_ms
                ),
            },
        }
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
            
        print(f"\nResults saved to: {output_path}")


def load_model_from_checkpoint(
    checkpoint_path: str,
    model_class: Optional[nn.Module] = None,
    device: str = "cuda" if torch.cuda.is_available() else "cpu",
) -> nn.Module:
    """
    Load a model from checkpoint.
    
    Handles different checkpoint formats:
    - PyTorch checkpoint (.pth)
    - Legacy pickle (.pkl)
    """
    checkpoint_path = Path(checkpoint_path)
    
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Model not found: {checkpoint_path}")
        
    # Try PyTorch format first
    try:
        checkpoint = torch.load(checkpoint_path, map_location=device)
        
        if isinstance(checkpoint, nn.Module):
            return checkpoint
        elif isinstance(checkpoint, dict):
            if "model_state_dict" in checkpoint:
                # Need to create model instance
                if model_class is None:
                    raise ValueError("model_class required for loading state_dict")
                model = model_class()
                model.load_state_dict(checkpoint["model_state_dict"])
                return model
            else:
                # Just state dict
                if model_class is None:
                    raise ValueError("model_class required for loading state_dict")
                model = model_class()
                model.load_state_dict(checkpoint)
                return model
                
    except Exception as e:
        print(f"PyTorch load failed: {e}")
        
    # Try pickle (legacy .pkl models)
    if checkpoint_path.suffix == ".pkl":
        try:
            import pickle
            with open(checkpoint_path, 'rb') as f:
                model = pickle.load(f)
            return model
        except Exception as e:
            raise RuntimeError(f"Failed to load pickle model: {e}")
            
    raise ValueError(f"Unknown model format: {checkpoint_path}")


def run_challenger_comparison(
    old_model: nn.Module,
    new_model: nn.Module,
    test_loader: torch.utils.data.DataLoader,
    output_path: Optional[str] = None,
) -> pd.DataFrame:
    """
    Run challenger comparison programmatically.
    
    Args:
        old_model: Legacy model to compare
        new_model: New MTL model to compare
        test_loader: DataLoader for test data
        output_path: Optional path to save JSON results
        
    Returns:
        DataFrame with comparison results
    """
    challenger = ChallengerComparison(old_model, new_model)
    old_result, new_result = challenger.run_comparison(test_loader)
    challenger.print_comparison(old_result, new_result)
    
    if output_path:
        challenger.save_results(old_result, new_result, output_path)
        
    # Return as DataFrame
    return pd.DataFrame([
        old_result.to_dict(),
        new_result.to_dict(),
    ])


# CLI Entry Point
def main():
    parser = argparse.ArgumentParser(
        description="Challenger: Head-to-Head Model Comparison"
    )
    parser.add_argument(
        "--old-model",
        type=str,
        required=True,
        help="Path to old/legacy model checkpoint",
    )
    parser.add_argument(
        "--new-model",
        type=str,
        required=True,
        help="Path to new MTL model checkpoint",
    )
    parser.add_argument(
        "--test-data",
        type=str,
        required=True,
        help="Path to test dataset directory",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/challenger_results.json",
        help="Output path for results",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size for testing",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cuda" if torch.cuda.is_available() else "cpu",
        help="Device to use for testing",
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("CHALLENGER MODEL COMPARISON")
    print("=" * 70)
    print(f"Old Model: {args.old_model}")
    print(f"New Model: {args.new_model}")
    print(f"Test Data: {args.test_data}")
    print(f"Device: {args.device}")
    print("=" * 70)
    
    # Check if required modules are available
    try:
        from mtl_dataset import create_mtl_dataloader
        from mtl_preprocessing import get_val_transforms
        DATASET_AVAILABLE = True
    except ImportError as e:
        DATASET_AVAILABLE = False
        print(f"Warning: MTL modules not available: {e}")
    
    if not DATASET_AVAILABLE:
        print("\nError: MTL dataset and preprocessing modules required.")
        print("Please ensure mtl_dataset.py and mtl_preprocessing.py are available.")
        print("\nExpected usage after setup:")
        print(f"  python challenger_test.py \\")
        print(f"    --old-model {args.old_model} \\")
        print(f"    --new-model {args.new_model} \\")
        print(f"    --test-data {args.test_data}")
        return
    
    # Try to load models
    print("\nLoading models...")
    
    try:
        old_model = load_model_from_checkpoint(args.old_model, device=args.device)
        print(f"✓ Old model loaded: {args.old_model}")
    except Exception as e:
        print(f"✗ Failed to load old model: {e}")
        return
    
    try:
        new_model = load_model_from_checkpoint(args.new_model, device=args.device)
        print(f"✓ New model loaded: {args.new_model}")
    except Exception as e:
        print(f"✗ Failed to load new model: {e}")
        return
    
    # Create test dataloader
    print("\nPreparing test data...")
    test_path = Path(args.test_data)
    
    if not test_path.exists():
        print(f"Error: Test data path does not exist: {args.test_data}")
        print("\nNote: The test data directory should contain:")
        print("  - Images in a format supported by mtl_dataset.py")
        print("  - annotations.csv or annotations.json with labels")
        print("\nDummy test run with random data...")
        
        # Create dummy test for demonstration
        import torchvision
        dummy_data = torch.randn(args.batch_size, 3, 64, 64)
        dummy_labels = {
            'eye_state': torch.randint(0, 2, (args.batch_size,)),
            'gaze_yaw': torch.randn(args.batch_size),
            'gaze_pitch': torch.randn(args.batch_size),
            'distraction': torch.randint(0, 5, (args.batch_size,)),
        }
        dummy_masks = {
            'eye_state': torch.ones(args.batch_size, dtype=torch.bool),
            'gaze_yaw': torch.ones(args.batch_size, dtype=torch.bool),
            'gaze_pitch': torch.ones(args.batch_size, dtype=torch.bool),
            'distraction': torch.ones(args.batch_size, dtype=torch.bool),
        }
        
        class DummyDataset(torch.utils.data.Dataset):
            def __len__(self):
                return args.batch_size
            def __getitem__(self, idx):
                return {
                    'image': dummy_data[idx],
                    'labels': {k: v[idx] for k, v in dummy_labels.items()},
                    'masks': {k: v[idx] for k, v in dummy_masks.items()},
                }
        
        test_loader = torch.utils.data.DataLoader(
            DummyDataset(),
            batch_size=args.batch_size,
            shuffle=False,
        )
    else:
        try:
            transform = get_val_transforms()
            test_loader = create_mtl_dataloader(
                data_root=args.test_data,
                datasets=[test_path.name],
                split="test",
                batch_size=args.batch_size,
                transform=transform,
                shuffle=False,
            )
        except Exception as e:
            print(f"Error loading test data: {e}")
            return
    
    # Run comparison
    print("\nRunning comparison...")
    challenger = ChallengerComparison(old_model, new_model, device=args.device)
    
    try:
        old_result, new_result = challenger.run_comparison(test_loader)
        challenger.print_comparison(old_result, new_result)
        challenger.save_results(old_result, new_result, args.output)
    except Exception as e:
        print(f"Error during comparison: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n✓ Comparison complete!")


if __name__ == "__main__":
    main()
