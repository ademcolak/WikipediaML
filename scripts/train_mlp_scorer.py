#!/usr/bin/env python3
"""
MLP Scorer Training Script
Trains the MLP model to predict distance-to-target for candidate links.
"""

import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
from tqdm import tqdm
import sys
import os

# Add parent directory to path to import models
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.mlp_scorer import create_mlp_scorer


class WikipediaLinkDataset(Dataset):
    """Dataset for training the MLP scorer."""
    
    def __init__(self, samples: List[Dict]):
        """
        Initialize dataset.
        
        Args:
            samples: List of training samples with embeddings and labels
        """
        self.samples = samples
        
    def __len__(self) -> int:
        return len(self.samples)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        sample = self.samples[idx]
        
        start_emb = torch.tensor(sample['start_embedding'], dtype=torch.float32)
        target_emb = torch.tensor(sample['target_embedding'], dtype=torch.float32)
        candidate_emb = torch.tensor(sample['candidate_embedding'], dtype=torch.float32)
        distance = torch.tensor([sample['distance_to_target']], dtype=torch.float32)
        
        return start_emb, target_emb, candidate_emb, distance


class MLPScorerTrainer:
    """Trainer for MLP Scorer model."""
    
    def __init__(
        self,
        model: nn.Module,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu',
        learning_rate: float = 0.001,
        weight_decay: float = 1e-5
    ):
        """
        Initialize trainer.
        
        Args:
            model: MLP scorer model
            device: Device to train on
            learning_rate: Learning rate for optimizer
            weight_decay: L2 regularization weight
        """
        self.model = model.to(device)
        self.device = device
        self.learning_rate = learning_rate
        self.weight_decay = weight_decay
        
        # Optimizer
        self.optimizer = optim.AdamW(
            self.model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay
        )
        
        # Learning rate scheduler
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer,
            mode='min',
            factor=0.5,
            patience=3,
            verbose=True  # type: ignore
        )
        
        # Loss function (MSE for regression)
        self.criterion = nn.MSELoss()
        
        # Training history
        self.history = {
            'train_loss': [],
            'val_loss': [],
            'train_mae': [],
            'val_mae': []
        }
    
    def train_epoch(self, train_loader: DataLoader) -> Tuple[float, float]:
        """
        Train for one epoch.
        
        Args:
            train_loader: Training data loader
            
        Returns:
            Tuple of (average loss, average MAE)
        """
        self.model.train()
        total_loss = 0.0
        total_mae = 0.0
        n_batches = 0
        
        pbar = tqdm(train_loader, desc="Training")
        for start_emb, target_emb, candidate_emb, distance in pbar:
            # Move to device
            start_emb = start_emb.to(self.device)
            target_emb = target_emb.to(self.device)
            candidate_emb = candidate_emb.to(self.device)
            distance = distance.to(self.device)
            
            # Forward pass
            self.optimizer.zero_grad()
            predictions = self.model(start_emb, target_emb, candidate_emb)
            
            # Compute loss
            loss = self.criterion(predictions, distance)
            
            # Backward pass
            loss.backward()
            
            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            
            self.optimizer.step()
            
            # Metrics
            mae = torch.abs(predictions - distance).mean()
            total_loss += loss.item()
            total_mae += mae.item()
            n_batches += 1
            
            # Update progress bar
            pbar.set_postfix({
                'loss': f'{loss.item():.4f}',
                'mae': f'{mae.item():.4f}'
            })
        
        avg_loss = total_loss / n_batches
        avg_mae = total_mae / n_batches
        
        return avg_loss, avg_mae
    
    def validate(self, val_loader: DataLoader) -> Tuple[float, float]:
        """
        Validate the model.
        
        Args:
            val_loader: Validation data loader
            
        Returns:
            Tuple of (average loss, average MAE)
        """
        self.model.eval()
        total_loss = 0.0
        total_mae = 0.0
        n_batches = 0
        
        with torch.no_grad():
            for start_emb, target_emb, candidate_emb, distance in tqdm(val_loader, desc="Validating"):
                # Move to device
                start_emb = start_emb.to(self.device)
                target_emb = target_emb.to(self.device)
                candidate_emb = candidate_emb.to(self.device)
                distance = distance.to(self.device)
                
                # Forward pass
                predictions = self.model(start_emb, target_emb, candidate_emb)
                
                # Compute metrics
                loss = self.criterion(predictions, distance)
                mae = torch.abs(predictions - distance).mean()
                
                total_loss += loss.item()
                total_mae += mae.item()
                n_batches += 1
        
        avg_loss = total_loss / n_batches
        avg_mae = total_mae / n_batches
        
        return avg_loss, avg_mae
    
    def train(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        n_epochs: int = 50,
        early_stopping_patience: int = 10
    ) -> Dict:
        """
        Train the model.
        
        Args:
            train_loader: Training data loader
            val_loader: Validation data loader
            n_epochs: Number of epochs to train
            early_stopping_patience: Patience for early stopping
            
        Returns:
            Training history
        """
        print(f"\n{'='*80}")
        print("Starting training...")
        print(f"{'='*80}")
        print(f"Device: {self.device}")
        print(f"Model parameters: {sum(p.numel() for p in self.model.parameters()):,}")
        print(f"Training samples: {len(train_loader.dataset):,}")  # type: ignore
        print(f"Validation samples: {len(val_loader.dataset):,}")  # type: ignore
        print(f"Batch size: {train_loader.batch_size}")
        print(f"Epochs: {n_epochs}")
        
        best_val_loss = float('inf')
        patience_counter = 0
        
        for epoch in range(1, n_epochs + 1):
            print(f"\n{'='*80}")
            print(f"Epoch {epoch}/{n_epochs}")
            print(f"{'='*80}")
            
            # Train
            train_loss, train_mae = self.train_epoch(train_loader)
            
            # Validate
            val_loss, val_mae = self.validate(val_loader)
            
            # Update scheduler
            self.scheduler.step(val_loss)
            
            # Save history
            self.history['train_loss'].append(train_loss)
            self.history['val_loss'].append(val_loss)
            self.history['train_mae'].append(train_mae)
            self.history['val_mae'].append(val_mae)
            
            # Print metrics
            print(f"\nEpoch {epoch} Results:")
            print(f"  Train Loss: {train_loss:.4f} | Train MAE: {train_mae:.4f}")
            print(f"  Val Loss:   {val_loss:.4f} | Val MAE:   {val_mae:.4f}")
            
            # Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                print(f"  ✓ New best validation loss!")
            else:
                patience_counter += 1
                print(f"  No improvement ({patience_counter}/{early_stopping_patience})")
                
                if patience_counter >= early_stopping_patience:
                    print(f"\n✓ Early stopping triggered after {epoch} epochs")
                    break
        
        print(f"\n{'='*80}")
        print("Training completed!")
        print(f"{'='*80}")
        print(f"Best validation loss: {best_val_loss:.4f}")
        
        return self.history
    
    def save_model(self, save_path: Path) -> None:
        """
        Save model checkpoint.
        
        Args:
            save_path: Path to save the model
        """
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        checkpoint = {
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict(),
            'history': self.history
        }
        
        torch.save(checkpoint, save_path)
        print(f"✓ Model saved to {save_path}")


def load_training_data(data_dir: Path) -> List[Dict]:
    """Load training data from JSON file."""
    samples_file = data_dir / "training_samples.json"
    
    print(f"Loading training data from {samples_file}...")
    with open(samples_file, 'r', encoding='utf-8') as f:
        samples = json.load(f)
    
    print(f"✓ Loaded {len(samples):,} samples")
    return samples


def split_data(samples: List[Dict], train_ratio: float = 0.8) -> Tuple[List[Dict], List[Dict]]:
    """Split data into train and validation sets."""
    n_train = int(len(samples) * train_ratio)
    
    # Shuffle samples
    np.random.shuffle(samples)  # type: ignore
    
    train_samples = samples[:n_train]
    val_samples = samples[n_train:]
    
    print(f"✓ Train samples: {len(train_samples):,}")
    print(f"✓ Validation samples: {len(val_samples):,}")
    
    return train_samples, val_samples


def main():
    """Main training function."""
    # Paths
    data_dir = Path("data/training")
    output_dir = Path("models/checkpoints")
    
    # Check if training data exists
    if not data_dir.exists():
        print(f"✗ Error: {data_dir} not found!")
        print("Please run generate_training_data.py first.")
        return 1
    
    try:
        # Load data
        samples = load_training_data(data_dir)
        train_samples, val_samples = split_data(samples, train_ratio=0.8)
        
        # Create datasets
        train_dataset = WikipediaLinkDataset(train_samples)
        val_dataset = WikipediaLinkDataset(val_samples)
        
        # Create data loaders
        train_loader = DataLoader(
            train_dataset,
            batch_size=256,
            shuffle=True,
            num_workers=4,
            pin_memory=True
        )
        val_loader = DataLoader(
            val_dataset,
            batch_size=256,
            shuffle=False,
            num_workers=4,
            pin_memory=True
        )
        
        # Create model
        model = create_mlp_scorer(
            model_type="basic",
            embedding_dim=384,
            hidden_dims=(512, 256, 128),
            dropout=0.2
        )
        
        # Create trainer
        trainer = MLPScorerTrainer(
            model=model,
            learning_rate=0.001,
            weight_decay=1e-5
        )
        
        # Train
        history = trainer.train(
            train_loader=train_loader,
            val_loader=val_loader,
            n_epochs=50,
            early_stopping_patience=10
        )
        
        # Save model
        trainer.save_model(output_dir / "mlp_scorer_best.pt")
        
        # Save history
        history_file = output_dir / "training_history.json"
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
        print(f"✓ Training history saved to {history_file}")
        
        print("\n✓ Training completed successfully!")
        print("\nNext steps:")
        print("1. Validate model on unseen page pairs")
        print("2. Integrate model into navigation system")
        print("3. Test with real Wikipedia navigation tasks")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Error during training: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())