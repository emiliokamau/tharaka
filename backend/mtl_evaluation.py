"""
Evaluation Metrics for Multi-Task Learning DMS

Tracks:
- Per-Task Accuracy (classification tasks)
- Per-Task MSE/MAE (regression tasks)
- Overall Model Loss
- Learning curves for each task

Usage:
    tracker = MetricsTracker(tasks=["eye_state", "gaze_yaw", "gaze_pitch", "distraction"])
    
    for epoch in range(num_epochs):
        # Training loop
        tracker.update_train(loss, predictions, labels, masks)
        
        # Validation
        tracker.update_val(loss, predictions, labels, masks)
        
        # Log metrics
        metrics = tracker.get_metrics()
        print(f"Epoch {epoch}: {metrics}")
        
        # Save checkpoint
        tracker.save_checkpoint("checkpoint.pth")
"""

import json
import numpy as np
import torch
import torch.nn as nn
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict
import pandas as pd


@dataclass
class TaskMetrics:
    """Metrics for a single task"""
    name: str
    task_type: str  # "classification" or "regression"
    
    # Loss metrics
    total_loss: float = 0.0
    num_samples: int = 0
    
    # Classification metrics
    correct: int = 0
    total: int = 0
    confusion_matrix: Optional[np.ndarray] = None
    
    # Regression metrics
    mse: float = 0.0
    mae: float = 0.0
    
    def compute_accuracy(self) -> float:
        """Compute classification accuracy"""
        if self.total > 0:
            return self.correct / self.total
        return 0.0
    
    def compute_mse(self) -> float:
        """Compute mean squared error"""
        if self.num_samples > 0:
            return self.mse / self.num_samples
        return 0.0
    
    def compute_mae(self) -> float:
        """Compute mean absolute error"""
        if self.num_samples > 0:
            return self.mae / self.num_samples
        return 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        result = {
            "name": self.name,
            "task_type": self.task_type,
            "total_loss": self.total_loss,
            "num_samples": self.num_samples,
        }
        
        if self.task_type == "classification":
            result["accuracy"] = self.compute_accuracy()
            result["correct"] = self.correct
            result["total"] = self.total
        else:
            result["mse"] = self.compute_mse()
            result["mae"] = self.compute_mae()
            
        return result


class MetricsTracker:
    """
    Comprehensive metrics tracker for Multi-Task Learning.
    
    Tracks:
    - Overall loss (combined from all tasks)
    - Per-task loss
    - Per-task accuracy (classification)
    - Per-task MSE/MAE (regression)
    - Learning rate
    - Batch timing
    """
    
    def __init__(
        self,
        tasks: List[str],
        task_types: Optional[Dict[str, str]] = None,
        num_classes: Optional[Dict[str, int]] = None,
        save_dir: Optional[str] = None,
    ):
        """
        Args:
            tasks: List of task names
            task_types: Dict mapping task names to "classification" or "regression"
            num_classes: Dict mapping classification task names to number of classes
            save_dir: Directory to save metrics and checkpoints
        """
        self.tasks = tasks
        self.task_types = task_types or {
            "eye_state": "classification",
            "gaze_yaw": "regression",
            "gaze_pitch": "regression",
            "distraction": "classification",
        }
        self.num_classes = num_classes or {
            "eye_state": 2,
            "distraction": 5,
        }
        self.save_dir = Path(save_dir) if save_dir else None
        
        # Initialize metrics storage
        self.reset()
        
    def reset(self):
        """Reset all metrics for a new epoch"""
        # Training metrics
        self.train_metrics = {task: TaskMetrics(task, self.task_types[task]) 
                             for task in self.tasks}
        self.train_total_loss = 0.0
        self.train_num_batches = 0
        
        # Validation metrics
        self.val_metrics = {task: TaskMetrics(task, self.task_types[task]) 
                           for task in self.tasks}
        self.val_total_loss = 0.0
        self.val_num_batches = 0
        
        # Learning rate tracking
        self.learning_rates = []
        
        # Timing
        self.batch_times = []
        
    def update_train(
        self,
        loss: float,
        predictions: Dict[str, torch.Tensor],
        labels: Dict[str, torch.Tensor],
        masks: Dict[str, torch.Tensor],
        batch_size: Optional[int] = None,
    ):
        """Update training metrics with batch results"""
        self.train_total_loss += loss
        self.train_num_batches += 1
        
        # Move to CPU for metric computation
        predictions = {k: v.detach().cpu() for k, v in predictions.items()}
        labels = {k: v.detach().cpu() for k, v in labels.items()}
        masks = {k: v.detach().cpu() if isinstance(v, torch.Tensor) else v 
                for k, v in masks.items()}
        
        # Update per-task metrics
        for task_name in self.tasks:
            if task_name not in predictions:
                continue
                
            pred = predictions[task_name]
            label = labels.get(task_name)
            mask = masks.get(task_name)
            
            if label is None:
                continue
                
            metrics = self.train_metrics[task_name]
            metrics.num_samples += 1
            
            # Get valid indices
            if isinstance(mask, torch.Tensor):
                valid_indices = mask & (label != -1)
            else:
                valid_indices = label != -1
                
            if not valid_indices.any():
                continue
                
            valid_pred = pred[valid_indices]
            valid_label = label[valid_indices]
            
            if self.task_types[task_name] == "classification":
                # Classification metrics
                if pred.dim() > 1:
                    # Multi-class
                    pred_class = torch.argmax(valid_pred, dim=-1)
                else:
                    # Binary
                    pred_class = (torch.sigmoid(valid_pred) > 0.5).long()
                    
                correct = (pred_class == valid_label).sum().item()
                metrics.correct += correct
                metrics.total += len(valid_label)
                
            else:
                # Regression metrics
                mse = ((valid_pred - valid_label) ** 2).sum().item()
                mae = torch.abs(valid_pred - valid_label).sum().item()
                metrics.mse += mse
                metrics.mae += mae
                
    def update_val(
        self,
        loss: float,
        predictions: Dict[str, torch.Tensor],
        labels: Dict[str, torch.Tensor],
        masks: Dict[str, torch.Tensor],
    ):
        """Update validation metrics with batch results"""
        self.val_total_loss += loss
        self.val_num_batches += 1
        
        # Move to CPU
        predictions = {k: v.detach().cpu() for k, v in predictions.items()}
        labels = {k: v.detach().cpu() for k, v in labels.items()}
        masks = {k: v.detach().cpu() if isinstance(v, torch.Tensor) else v
                for k, v in masks.items()}
        
        # Update per-task metrics
        for task_name in self.tasks:
            if task_name not in predictions:
                continue
                
            pred = predictions[task_name]
            label = labels.get(task_name)
            mask = masks.get(task_name)
            
            if label is None:
                continue
                
            metrics = self.val_metrics[task_name]
            metrics.num_samples += 1
            
            # Get valid indices
            if isinstance(mask, torch.Tensor):
                valid_indices = mask & (label != -1)
            else:
                valid_indices = label != -1
                
            if not valid_indices.any():
                continue
                
            valid_pred = pred[valid_indices]
            valid_label = label[valid_indices]
            
            if self.task_types[task_name] == "classification":
                # Classification metrics
                if pred.dim() > 1:
                    pred_class = torch.argmax(valid_pred, dim=-1)
                else:
                    pred_class = (torch.sigmoid(valid_pred) > 0.5).long()
                    
                correct = (pred_class == valid_label).sum().item()
                metrics.correct += correct
                metrics.total += len(valid_label)
                
            else:
                # Regression metrics
                mse = ((valid_pred - valid_label) ** 2).sum().item()
                mae = torch.abs(valid_pred - valid_label).sum().item()
                metrics.mse += mse
                metrics.mae += mae
                
    def update_learning_rate(self, lr: float):
        """Update learning rate tracking"""
        self.learning_rates.append(lr)
        
    def update_batch_time(self, time: float):
        """Update batch timing"""
        self.batch_times.append(time)
        
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get all current metrics as a dictionary.
        
        Returns:
            Dict with train/val metrics
        """
        train_loss = self.train_total_loss / max(1, self.train_num_batches)
        val_loss = self.val_total_loss / max(1, self.val_num_batches)
        
        result = {
            "train": {
                "loss": train_loss,
                "num_batches": self.train_num_batches,
            },
            "val": {
                "loss": val_loss,
                "num_batches": self.val_num_batches,
            },
            "per_task": {},
        }
        
        # Per-task metrics
        for task_name in self.tasks:
            task_result = {}
            
            # Training
            train_m = self.train_metrics[task_name]
            if self.task_types[task_name] == "classification":
                task_result["train_accuracy"] = train_m.compute_accuracy()
            else:
                task_result["train_mse"] = train_m.compute_mse()
                task_result["train_mae"] = train_m.compute_mae()
                
            # Validation
            val_m = self.val_metrics[task_name]
            if self.task_types[task_name] == "classification":
                task_result["val_accuracy"] = val_m.compute_accuracy()
            else:
                task_result["val_mse"] = val_m.compute_mse()
                task_result["val_mae"] = val_m.compute_mae()
                
            result["per_task"][task_name] = task_result
            
        return result
    
    def get_summary(self) -> str:
        """Get a human-readable summary of current metrics"""
        metrics = self.get_metrics()
        
        lines = [
            f"Train Loss: {metrics['train']['loss']:.4f}",
            f"Val Loss: {metrics['val']['loss']:.4f}",
            "--- Per-Task Metrics ---",
        ]
        
        for task_name, task_metrics in metrics["per_task"].items():
            if self.task_types[task_name] == "classification":
                train_acc = task_metrics.get("train_accuracy", 0) * 100
                val_acc = task_metrics.get("val_accuracy", 0) * 100
                lines.append(
                    f"  {task_name}: Train Acc={train_acc:.1f}%, Val Acc={val_acc:.1f}%"
                )
            else:
                train_mse = task_metrics.get("train_mse", 0)
                val_mse = task_metrics.get("val_mse", 0)
                lines.append(
                    f"  {task_name}: Train MSE={train_mse:.4f}, Val MSE={val_mse:.4f}"
                )
                
        return "\n".join(lines)
    
    def save_metrics(self, filepath: Optional[str] = None):
        """Save metrics to JSON file"""
        if filepath is None and self.save_dir:
            filepath = self.save_dir / "metrics.json"
        elif filepath is None:
            return
            
        metrics = self.get_metrics()
        
        # Add metadata
        metrics["learning_rates"] = self.learning_rates[-100:]  # Last 100
        metrics["batch_times"] = self.batch_times[-100:]
        
        with open(filepath, 'w') as f:
            json.dump(metrics, f, indent=2)
            
    def save_checkpoint(self, filepath: str):
        """Save full metrics state for checkpointing"""
        checkpoint = {
            "train_metrics": {k: v.to_dict() for k, v in self.train_metrics.items()},
            "val_metrics": {k: v.to_dict() for k, v in self.val_metrics.items()},
            "train_total_loss": self.train_total_loss,
            "train_num_batches": self.train_num_batches,
            "val_total_loss": self.val_total_loss,
            "val_num_batches": self.val_num_batches,
            "learning_rates": self.learning_rates,
        }
        
        if self.save_dir:
            filepath = self.save_dir / filepath
            
        with open(filepath, 'w') as f:
            json.dump(checkpoint, f, indent=2)
            
    def load_checkpoint(self, filepath: str):
        """Load metrics state from checkpoint"""
        with open(filepath, 'r') as f:
            checkpoint = json.load(f)
            
        # Restore metrics (simplified - would need proper reconstruction)
        self.learning_rates = checkpoint.get("learning_rates", [])


class MetricsLogger:
    """
    Lightweight logger for tensorboard/CSV export.
    
    Usage:
        logger = MetricsLogger("experiments/run1")
        logger.log(epoch, metrics_dict)
        logger.export_csv()
    """
    
    def __init__(self, log_dir: str):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.history = defaultdict(list)
        
    def log(self, step: int, metrics: Dict[str, float]):
        """Log metrics for a single step"""
        for key, value in metrics.items():
            self.history[key].append((step, value))
            
    def export_csv(self, filepath: Optional[str] = None):
        """Export history to CSV"""
        if filepath is None:
            filepath = self.log_dir / "metrics.csv"
            
        # Convert to DataFrame
        data = {}
        for key, values in self.history.items():
            steps, vals = zip(*values)
            data[f"step"] = steps
            data[key] = vals
            
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False)
        
    def plot(self, keys: List[str], title: str = "Metrics"):
        """Simple matplotlib plot (optional)"""
        try:
            import matplotlib.pyplot as plt
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            for key in keys:
                if key in self.history:
                    steps, values = zip(*self.history[key])
                    ax.plot(steps, values, label=key)
                    
            ax.set_xlabel("Step")
            ax.set_ylabel("Value")
            ax.set_title(title)
            ax.legend()
            ax.grid(True)
            
            return fig
            
        except ImportError:
            print("Matplotlib not available for plotting")
            return None


def create_evaluation_table(
    results: Dict[str, Dict],
    metrics: List[str] = ["accuracy", "mse", "mae", "f1"],
) -> pd.DataFrame:
    """
    Create a formatted comparison table for model evaluation.
    
    Args:
        results: Dict of model_name -> metrics_dict
        metrics: List of metrics to include
        
    Returns:
        Pandas DataFrame with formatted results
    """
    rows = []
    
    for model_name, model_metrics in results.items():
        row = {"Model": model_name}
        
        for metric in metrics:
            if metric in model_metrics:
                row[metric.upper()] = model_metrics[metric]
                
        rows.append(row)
        
    df = pd.DataFrame(rows)
    
    # Format percentages
    for col in df.columns:
        if "accuracy" in col.lower():
            df[col] = df[col].apply(lambda x: f"{x*100:.1f}%" if pd.notna(x) else "N/A")
            
    return df
