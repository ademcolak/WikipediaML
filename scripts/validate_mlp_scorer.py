#!/usr/bin/env python3
"""
MLP Scorer Validation Script
Validates the trained model on completely unseen page pairs to ensure no data leakage.
"""

import json
import torch
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
from tqdm import tqdm
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.mlp_scorer import create_mlp_scorer
from scripts.generate_training_data import TrainingDataGenerator


class ModelValidator:
    """Validator for MLP Scorer model."""
    
    def __init__(
        self,
        model_path: Path,
        graph_dir: Path,
        embeddings_dir: Path,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu'
    ):
        """
        Initialize validator.
        
        Args:
            model_path: Path to trained model checkpoint
            graph_dir: Directory containing graph data
            embeddings_dir: Directory containing embeddings
            device: Device to run validation on
        """
        self.device = device
        self.graph_dir = graph_dir
        self.embeddings_dir = embeddings_dir
        
        # Load model
        print(f"\n{'='*80}")
        print("Loading trained model...")
        print(f"{'='*80}")
        
        self.model = create_mlp_scorer(
            model_type="basic",
            embedding_dim=384,
            hidden_dims=(512, 256, 128),
            dropout=0.2
        )
        
        checkpoint = torch.load(model_path, map_location=device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.to(device)
        self.model.eval()
        
        print(f"✓ Model loaded from {model_path}")
        print(f"✓ Device: {device}")
        
        # Load data generator for creating test samples
        self.generator = TrainingDataGenerator(graph_dir, embeddings_dir)
        self.generator.load_data()
    
    def generate_test_samples(
        self,
        n_samples: int = 10_000,
        exclude_page_ids: set | None = None
    ) -> List[Dict]:
        """
        Generate test samples from unseen page pairs.
        
        Args:
            n_samples: Number of test samples to generate
            exclude_page_ids: Set of page IDs to exclude (from training set)
            
        Returns:
            List of test samples
        """
        print(f"\n{'='*80}")
        print(f"Generating {n_samples:,} test samples from unseen page pairs...")
        print(f"{'='*80}")
        
        if exclude_page_ids is None:
            exclude_page_ids = set()
        
        # Generate samples ensuring they're from unseen pages
        samples = []
        attempts = 0
        max_attempts = n_samples * 5
        
        n_pages = len(self.generator.pages)
        
        with tqdm(total=n_samples, desc="Generating test samples") as pbar:
            while len(samples) < n_samples and attempts < max_attempts:
                attempts += 1
                
                # Sample random pages
                start_idx = np.random.randint(0, n_pages)
                target_idx = np.random.randint(0, n_pages)
                
                start_page_id = self.generator.index_to_page_id[start_idx]
                target_page_id = self.generator.index_to_page_id[target_idx]
                
                # Skip if pages were in training set
                if start_page_id in exclude_page_ids or target_page_id in exclude_page_ids:
                    continue
                
                # Skip if same page
                if start_idx == target_idx:
                    continue
                
                # Find shortest path
                distance = self.generator.bfs_shortest_path(start_idx, target_idx, max_depth=10)
                
                if distance < 2 or distance > 8:
                    continue
                
                # Get neighbors and sample candidates
                neighbors = self.generator.adjacency_matrix[start_idx].indices  # type: ignore
                if len(neighbors) == 0:
                    continue
                
                n_candidates = min(5, len(neighbors))
                candidate_indices = np.random.choice(neighbors, n_candidates, replace=False)
                
                for candidate_idx in candidate_indices:
                    candidate_page_id = self.generator.index_to_page_id[candidate_idx]
                    
                    # Skip if candidate was in training set
                    if candidate_page_id in exclude_page_ids:
                        continue
                    
                    # Calculate distance from candidate to target
                    distance_to_target = self.generator.bfs_shortest_path(
                        candidate_idx, target_idx, max_depth=10
                    )
                    
                    if distance_to_target < 0:
                        continue
                    
                    sample = {
                        'start_idx': int(start_idx),
                        'target_idx': int(target_idx),
                        'candidate_idx': int(candidate_idx),
                        'distance_to_target': int(distance_to_target)
                    }
                    
                    samples.append(sample)
                    pbar.update(1)
                    
                    if len(samples) >= n_samples:
                        break
        
        print(f"✓ Generated {len(samples):,} test samples in {attempts:,} attempts")
        return samples
    
    def validate(self, test_samples: List[Dict]) -> Dict:
        """
        Validate model on test samples.
        
        Args:
            test_samples: List of test samples
            
        Returns:
            Dictionary of validation metrics
        """
        print(f"\n{'='*80}")
        print("Validating model...")
        print(f"{'='*80}")
        
        predictions = []
        ground_truths = []
        
        with torch.no_grad():
            for sample in tqdm(test_samples, desc="Validating"):
                start_idx = sample['start_idx']
                target_idx = sample['target_idx']
                candidate_idx = sample['candidate_idx']
                true_distance = sample['distance_to_target']
                
                # Get embeddings
                start_emb = torch.tensor(
                    self.generator.embeddings[start_idx],  # type: ignore
                    dtype=torch.float32
                ).unsqueeze(0).to(self.device)
                
                target_emb = torch.tensor(
                    self.generator.embeddings[target_idx],  # type: ignore
                    dtype=torch.float32
                ).unsqueeze(0).to(self.device)
                
                candidate_emb = torch.tensor(
                    self.generator.embeddings[candidate_idx],  # type: ignore
                    dtype=torch.float32
                ).unsqueeze(0).to(self.device)
                
                # Predict
                pred_distance = self.model(start_emb, target_emb, candidate_emb)
                pred_distance = pred_distance.cpu().item()
                
                predictions.append(pred_distance)
                ground_truths.append(true_distance)
        
        # Calculate metrics
        predictions = np.array(predictions)
        ground_truths = np.array(ground_truths)
        
        mae = np.mean(np.abs(predictions - ground_truths))
        mse = np.mean((predictions - ground_truths) ** 2)
        rmse = np.sqrt(mse)
        
        # Accuracy within tolerance
        tolerance_1 = np.mean(np.abs(predictions - ground_truths) <= 1)
        tolerance_2 = np.mean(np.abs(predictions - ground_truths) <= 2)
        
        # Correlation
        correlation = np.corrcoef(predictions, ground_truths)[0, 1]
        
        metrics = {
            'mae': float(mae),
            'mse': float(mse),
            'rmse': float(rmse),
            'accuracy_within_1': float(tolerance_1),
            'accuracy_within_2': float(tolerance_2),
            'correlation': float(correlation),
            'n_samples': len(test_samples)
        }
        
        # Print results
        print(f"\n{'='*80}")
        print("Validation Results:")
        print(f"{'='*80}")
        print(f"Test samples: {metrics['n_samples']:,}")
        print(f"MAE: {metrics['mae']:.4f}")
        print(f"RMSE: {metrics['rmse']:.4f}")
        print(f"Accuracy (±1): {metrics['accuracy_within_1']*100:.2f}%")
        print(f"Accuracy (±2): {metrics['accuracy_within_2']*100:.2f}%")
        print(f"Correlation: {metrics['correlation']:.4f}")
        
        # Distance distribution analysis
        print(f"\n{'='*80}")
        print("Distance Distribution Analysis:")
        print(f"{'='*80}")
        
        for dist in range(int(ground_truths.min()), int(ground_truths.max()) + 1):
            mask = ground_truths == dist
            if mask.sum() > 0:
                dist_mae = np.mean(np.abs(predictions[mask] - ground_truths[mask]))
                count = mask.sum()
                print(f"Distance {dist}: {count:,} samples, MAE: {dist_mae:.4f}")
        
        return metrics
    
    def save_results(self, metrics: Dict, output_path: Path) -> None:
        """
        Save validation results.
        
        Args:
            metrics: Validation metrics
            output_path: Path to save results
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        print(f"\n✓ Validation results saved to {output_path}")


def load_training_page_ids(training_dir: Path) -> set:
    """Load page IDs from training set to exclude from validation."""
    samples_file = training_dir / "training_samples.json"
    
    if not samples_file.exists():
        return set()
    
    print(f"Loading training page IDs from {samples_file}...")
    with open(samples_file, 'r', encoding='utf-8') as f:
        samples = json.load(f)
    
    page_ids = set()
    for sample in samples:
        page_ids.add(sample['start_page_id'])
        page_ids.add(sample['target_page_id'])
        page_ids.add(sample['candidate_page_id'])
    
    print(f"✓ Loaded {len(page_ids):,} unique page IDs from training set")
    return page_ids


def main():
    """Main validation function."""
    # Paths
    model_path = Path("models/checkpoints/mlp_scorer_best.pt")
    graph_dir = Path("data/graph")
    embeddings_dir = Path("data/embeddings")
    training_dir = Path("data/training")
    output_dir = Path("models/validation")
    
    # Check if model exists
    if not model_path.exists():
        print(f"✗ Error: {model_path} not found!")
        print("Please run train_mlp_scorer.py first.")
        return 1
    
    try:
        # Load training page IDs to exclude
        training_page_ids = load_training_page_ids(training_dir)
        
        # Create validator
        validator = ModelValidator(
            model_path=model_path,
            graph_dir=graph_dir,
            embeddings_dir=embeddings_dir
        )
        
        # Generate test samples from unseen pages
        test_samples = validator.generate_test_samples(
            n_samples=10_000,
            exclude_page_ids=training_page_ids
        )
        
        # Validate
        metrics = validator.validate(test_samples)
        
        # Save results
        validator.save_results(metrics, output_dir / "validation_results.json")
        
        print("\n✓ Validation completed successfully!")
        print("\nNext steps:")
        print("1. Integrate model into navigation system")
        print("2. Update search algorithm with MLP scorer")
        print("3. Implement beam search and hub prioritization")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Error during validation: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())