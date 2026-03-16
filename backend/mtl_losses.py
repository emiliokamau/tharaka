"""
Masked Loss Functions for Multi-Task Learning

This module implements loss functions that automatically mask out missing labels
during gradient computation. This ensures that missing labels don't contribute
to the gradient descent during backpropagation.

Key Features:
- Automatic masking based on MISSING_LABEL (-1)
- Supports both classification and regression tasks
- Weighted multi-task loss balancing
- Gradient masking for stable training
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass


# Missing label constant (must match mtl_dataset.py)
MISSING_LABEL = -1


class MaskedCrossEntropyLoss(nn.Module):
    """
    Cross-Entropy Loss with automatic masking for missing labels.
    
    For classification tasks where some samples may not have labels,
    this loss only computes gradients for samples with valid labels.
    """
    
    def __init__(
        self,
        weight: Optional[torch.Tensor] = None,
        ignore_index: int = MISSING_LABEL,
        reduction: str = "mean",
    ):
        super().__init__()
        self.weight = weight
        self.ignore_index = ignore_index
        self.reduction = reduction
        
    def forward(
        self, 
        predictions: torch.Tensor, 
        targets: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Args:
            predictions: Model predictions (B, C) or (B,)
            targets: Ground truth labels (B,) with -1 for missing
            mask: Optional boolean mask (B,) - True for valid labels
            
        Returns:
            Masked loss value
        """
        # Create mask for valid (non-missing) targets
        if mask is None:
            valid_mask = targets != self.ignore_index
        else:
            valid_mask = mask & (targets != self.ignore_index)
            
        # If no valid samples, return zero loss
        if not valid_mask.any():
            return torch.tensor(0.0, device=predictions.device, requires_grad=True)
        
        # Filter predictions and targets
        valid_preds = predictions[valid_mask]
        valid_targets = targets[valid_mask]
        
        # Compute cross-entropy loss
        if predictions.dim() == 2:
            # Multi-class classification
            loss = F.cross_entropy(
                valid_preds, 
                valid_targets,
                weight=self.weight,
                reduction=self.reduction,
            )
        else:
            # Binary classification (squeeze dimension)
            loss = F.binary_cross_entropy_with_logits(
                predictions.squeeze()[valid_mask],
                valid_targets.float(),
                weight=self.weight,
                reduction=self.reduction,
            )
            
        return loss


class MaskedMSELoss(nn.Module):
    """
    Mean Squared Error Loss with automatic masking for missing labels.
    
    For regression tasks (like gaze direction) where some samples may not have labels.
    """
    
    def __init__(self, reduction: str = "mean"):
        super().__init__()
        self.reduction = reduction
        
    def forward(
        self,
        predictions: torch.Tensor,
        targets: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Args:
            predictions: Model predictions (B, ...) 
            targets: Ground truth values (B, ...) with -1 for missing
            mask: Optional boolean mask (B,) - True for valid labels
            
        Returns:
            Masked MSE loss
        """
        # Create mask for valid (non-missing) targets
        if mask is None:
            valid_mask = targets != MISSING_LABEL
        else:
            valid_mask = mask & (targets != MISSING_LABEL)
            
        # If no valid samples, return zero loss
        if not valid_mask.any():
            return torch.tensor(0.0, device=predictions.device, requires_grad=True)
        
        # Compute MSE loss only on valid samples
        valid_preds = predictions[valid_mask]
        valid_targets = targets[valid_mask]
        
        loss = F.mse_loss(valid_preds, valid_targets, reduction=self.reduction)
        
        return loss


class MaskedL1Loss(nn.Module):
    """
    L1 Loss (Mean Absolute Error) with automatic masking for missing labels.
    
    Useful for gaze regression when you want less sensitivity to outliers.
    """
    
    def __init__(self, reduction: str = "mean"):
        super().__init__()
        self.reduction = reduction
        
    def forward(
        self,
        predictions: torch.Tensor,
        targets: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """Masked L1 loss forward pass"""
        if mask is None:
            valid_mask = targets != MISSING_LABEL
        else:
            valid_mask = mask & (targets != MISSING_LABEL)
            
        if not valid_mask.any():
            return torch.tensor(0.0, device=predictions.device, requires_grad=True)
        
        valid_preds = predictions[valid_mask]
        valid_targets = targets[valid_mask]
        
        loss = F.l1_loss(valid_preds, valid_targets, reduction=self.reduction)
        
        return loss


@dataclass
class TaskLossConfig:
    """Configuration for a single task's loss"""
    name: str
    loss_fn: nn.Module
    weight: float = 1.0  # Task-specific weight in multi-task loss
    enabled: bool = True


class MaskedMultiTaskLoss(nn.Module):
    """
    Multi-Task Loss that combines multiple task-specific losses with masking.
    
    This is the main loss module for the MTL model. It:
    1. Computes loss for each task independently
    2. Masks out missing labels automatically
    3. Combines losses with configurable weights
    4. Supports dynamic weight balancing
    
    Usage:
        loss_fn = MaskedMultiTaskLoss([
            TaskLossConfig("eye_state", MaskedCrossEntropyLoss(), weight=1.0),
            TaskLossConfig("gaze_yaw", MaskedMSELoss(), weight=0.5),
            TaskLossConfig("gaze_pitch", MaskedMSELoss(), weight=0.5),
            TaskLossConfig("distraction", MaskedCrossEntropyLoss(), weight=0.8),
        ])
        
        losses = loss_fn(predictions, labels, masks)
    """
    
    def __init__(
        self,
        task_configs: List[TaskLossConfig],
        loss_type: str = "weighted_sum",
        normalize_by_active_tasks: bool = True,
    ):
        """
        Args:
            task_configs: List of TaskLossConfig for each task
            loss_type: "weighted_sum", "dynamic_weighting", or "uncertainty_weighting"
            normalize_by_active_tasks: Whether to divide by number of active tasks
        """
        super().__init__()
        self.task_configs = task_configs
        self.loss_type = loss_type
        self.normalize_by_active_tasks = normalize_by_active_tasks
        
        # Create task name to config mapping
        self.task_dict = {cfg.name: cfg for cfg in task_configs}
        
        # For uncertainty-based weighting (learnable log variances)
        if loss_type == "uncertainty_weighting":
            self.log_vars = nn.Parameter(torch.zeros(len(task_configs)))
            
    def forward(
        self,
        predictions: Dict[str, torch.Tensor],
        labels: Dict[str, torch.Tensor],
        masks: Dict[str, torch.Tensor],
    ) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        """
        Compute multi-task loss with masking.
        
        Args:
            predictions: Dict of model predictions for each task
            labels: Dict of ground truth labels for each task
            masks: Dict of boolean masks for each task (True = valid)
            
        Returns:
            Tuple of (total_loss, dict of individual task losses)
        """
        task_losses = {}
        total_loss = 0.0
        active_tasks = 0
        
        for task_name, pred in predictions.items():
            if task_name not in self.task_dict:
                continue
                
            cfg = self.task_dict[task_name]
            if not cfg.enabled:
                continue
                
            # Get labels and mask for this task
            target = labels.get(task_name)
            mask = masks.get(task_name)
            
            if target is None:
                continue
                
            # Compute task-specific loss
            try:
                loss = cfg.loss_fn(pred, target, mask)
            except Exception as e:
                print(f"Error computing loss for {task_name}: {e}")
                loss = torch.tensor(0.0, device=pred.device)
                
            # Check if loss is valid (has active samples)
            if mask is not None and mask.any():
                task_losses[task_name] = loss
                active_tasks += 1
                
                # Add to total with task weight
                if self.loss_type == "uncertainty_weighting":
                    # Uncertainty weighting: loss * exp(-log_var) + log_var
                    idx = list(self.task_dict.keys()).index(task_name)
                    precision = torch.exp(-self.log_vars[idx])
                    total_loss += precision * loss + self.log_vars[idx]
                else:
                    total_loss += cfg.weight * loss
        
        # Normalize by number of active tasks if enabled
        if self.normalize_by_active_tasks and active_tasks > 0:
            if self.loss_type != "uncertainty_weighting":
                total_loss = total_loss / active_tasks
                
        return total_loss, task_losses
    
    def get_task_weights(self) -> Dict[str, float]:
        """Get current task weights"""
        weights = {}
        for cfg in self.task_configs:
            weights[cfg.name] = cfg.weight
        return weights
    
    def set_task_weight(self, task_name: str, weight: float):
        """Set weight for a specific task"""
        if task_name in self.task_dict:
            self.task_dict[task_name].weight = weight


def create_mtl_loss_fn(
    task_weights: Optional[Dict[str, float]] = None,
    use_uncertainty_weighting: bool = False,
    class_weights: Optional[Dict[str, torch.Tensor]] = None,
) -> MaskedMultiTaskLoss:
    """
    Factory function to create the MTL loss function.
    
    Args:
        task_weights: Dict of task names to loss weights
        use_uncertainty_weighting: Whether to use learnable uncertainty weighting
        class_weights: Dict of class weights for classification tasks
        
    Returns:
        Configured MaskedMultiTaskLoss
    """
    task_configs = []
    
    # Eye state classification
    eye_weight = task_weights.get("eye_state", 1.0) if task_weights else 1.0
    eye_weight_tensor = class_weights.get("eye_state") if class_weights else None
    task_configs.append(TaskLossConfig(
        name="eye_state",
        loss_fn=MaskedCrossEntropyLoss(weight=eye_weight_tensor),
        weight=eye_weight,
    ))
    
    # Gaze regression (yaw)
    gaze_weight = task_weights.get("gaze_yaw", 0.5) if task_weights else 0.5
    task_configs.append(TaskLossConfig(
        name="gaze_yaw",
        loss_fn=MaskedMSELoss(),
        weight=gaze_weight,
    ))
    
    # Gaze regression (pitch)
    pitch_weight = task_weights.get("gaze_pitch", 0.5) if task_weights else 0.5
    task_configs.append(TaskLossConfig(
        name="gaze_pitch",
        loss_fn=MaskedMSELoss(),
        weight=pitch_weight,
    ))
    
    # Distraction classification
    dist_weight = task_weights.get("distraction", 0.8) if task_weights else 0.8
    dist_weight_tensor = class_weights.get("distraction") if class_weights else None
    task_configs.append(TaskLossConfig(
        name="distraction",
        loss_fn=MaskedCrossEntropyLoss(weight=dist_weight_tensor),
        weight=dist_weight,
    ))
    
    loss_type = "uncertainty_weighting" if use_uncertainty_weighting else "weighted_sum"
    
    return MaskedMultiTaskLoss(
        task_configs=task_configs,
        loss_type=loss_type,
    )


class GradientMasker:
    """
    Utility class to manually mask gradients for missing labels.
    
    Sometimes it's useful to also mask gradients at the tensor level
    for additional safety.
    """
    
    @staticmethod
    def mask_gradients(
        tensors: List[torch.Tensor],
        masks: List[torch.Tensor],
    ):
        """
        Zero out gradients for samples with missing labels.
        
        Args:
            tensors: List of tensors to mask gradients for
            masks: List of boolean masks (True = keep gradient)
        """
        for tensor, mask in zip(tensors, masks):
            if tensor.grad is not None and mask is not None:
                # Create inverted mask
                inverted_mask = ~mask
                # Zero out gradients for masked positions
                tensor.grad[inverted_mask] = 0.0
