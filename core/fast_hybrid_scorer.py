#!/usr/bin/env python3
"""
Fast Hybrid Scorer with Two-Stage Filtering
Stage 1: Fast cosine similarity filtering
Stage 2: MLP scoring on top candidates only
"""

import torch
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional
import pickle

from models.mlp_scorer import create_mlp_scorer


class FastHybridScorer:
    """
    Two-stage hybrid scorer for speed optimization.
    
    Stage 1: Fast cosine similarity to filter candidates (cheap)
    Stage 2: MLP scoring on top-k candidates only (expensive)
    
    This reduces MLP inference calls by 80-90% while maintaining accuracy.
    """
    
    def __init__(
        self,
        model_path: Path,
        embeddings: np.ndarray,
        graph_stats: dict,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu',
        stage1_top_k: int = 20,  # Keep top 20 after cosine filtering
        alpha: float = 0.6,
        beta: float = 0.3,
        gamma: float = 0.1
    ):
        """
        Initialize fast hybrid scorer.
        
        Args:
            model_path: Path to trained MLP model
            embeddings: Page embeddings array
            graph_stats: Graph statistics
            device: Device for model inference
            stage1_top_k: Number of candidates to keep after stage 1
            alpha: Weight for MLP score
            beta: Weight for cosine similarity
            gamma: Weight for hub score
        """
        self.device = device
        self.embeddings = embeddings
        self.graph_stats = graph_stats
        self.stage1_top_k = stage1_top_k
        
        # Weights
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        
        # Load MLP model
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
        
        # Hub scores
        self.hub_scores = None
        if 'in_degrees' in graph_stats:
            in_degrees = np.array(graph_stats['in_degrees'])
            max_degree = in_degrees.max()
            self.hub_scores = in_degrees / max_degree if max_degree > 0 else in_degrees
        
        # Statistics
        self.stats = {
            'total_candidates_evaluated': 0,
            'stage1_evaluations': 0,
            'stage2_evaluations': 0,
            'mlp_calls_saved': 0
        }
    
    def cosine_similarity_batch(
        self,
        embeddings1: np.ndarray,
        embedding2: np.ndarray
    ) -> np.ndarray:
        """
        Calculate cosine similarity for multiple embeddings at once.
        
        Args:
            embeddings1: Array of embeddings (n, dim)
            embedding2: Single embedding (dim,)
            
        Returns:
            Array of similarities (n,)
        """
        # Normalize
        norms1 = np.linalg.norm(embeddings1, axis=1, keepdims=True)
        norms1[norms1 == 0] = 1  # Avoid division by zero
        embeddings1_norm = embeddings1 / norms1
        
        norm2 = np.linalg.norm(embedding2)
        if norm2 == 0:
            return np.zeros(len(embeddings1))
        embedding2_norm = embedding2 / norm2
        
        # Dot product
        similarities = np.dot(embeddings1_norm, embedding2_norm)
        
        # Convert from [-1, 1] to [0, 1]
        return (similarities + 1) / 2
    
    def stage1_filter(
        self,
        candidate_indices: List[int],
        target_idx: int
    ) -> List[int]:
        """
        Stage 1: Fast cosine similarity filtering.
        
        Args:
            candidate_indices: List of candidate indices
            target_idx: Target page index
            
        Returns:
            Top-k candidate indices after filtering
        """
        self.stats['stage1_evaluations'] += len(candidate_indices)
        
        if len(candidate_indices) <= self.stage1_top_k:
            return candidate_indices
        
        # Get embeddings
        candidate_embeddings = self.embeddings[candidate_indices]
        target_embedding = self.embeddings[target_idx]
        
        # Calculate similarities
        similarities = self.cosine_similarity_batch(candidate_embeddings, target_embedding)
        
        # Get top-k indices
        top_k_local_indices = np.argsort(similarities)[-self.stage1_top_k:][::-1]
        top_k_candidates = [candidate_indices[i] for i in top_k_local_indices]
        
        # Track savings
        self.stats['mlp_calls_saved'] += len(candidate_indices) - self.stage1_top_k
        
        return top_k_candidates
    
    def stage2_score(
        self,
        start_idx: int,
        target_idx: int,
        candidate_indices: List[int],
        current_depth: int = 0
    ) -> List[Tuple[int, float]]:
        """
        Stage 2: MLP scoring on filtered candidates.
        
        Args:
            start_idx: Current page index
            target_idx: Target page index
            candidate_indices: Filtered candidate indices
            current_depth: Current search depth
            
        Returns:
            List of (candidate_idx, score) tuples sorted by score
        """
        self.stats['stage2_evaluations'] += len(candidate_indices)
        
        scored_candidates = []
        
        for candidate_idx in candidate_indices:
            # MLP prediction
            with torch.no_grad():
                start_emb = torch.tensor(
                    self.embeddings[start_idx],
                    dtype=torch.float32
                ).unsqueeze(0).to(self.device)
                
                target_emb = torch.tensor(
                    self.embeddings[target_idx],
                    dtype=torch.float32
                ).unsqueeze(0).to(self.device)
                
                candidate_emb = torch.tensor(
                    self.embeddings[candidate_idx],
                    dtype=torch.float32
                ).unsqueeze(0).to(self.device)
                
                mlp_distance = self.model(start_emb, target_emb, candidate_emb).cpu().item()
            
            # Cosine similarity
            candidate_embedding = self.embeddings[candidate_idx]
            target_embedding = self.embeddings[target_idx]
            similarity = self.cosine_similarity_batch(
                candidate_embedding.reshape(1, -1),
                target_embedding
            )[0]
            cosine_distance = 1.0 - similarity
            
            # Hub score
            hub_score = 0.0
            if self.hub_scores is not None and 0 <= candidate_idx < len(self.hub_scores):
                hub_score = float(self.hub_scores[candidate_idx])
            
            # Adjust hub weight for distant targets
            gamma_adjusted = self.gamma * 2.0 if mlp_distance > 5 else self.gamma
            
            # Hybrid score
            score = (
                self.alpha * mlp_distance +
                self.beta * cosine_distance +
                gamma_adjusted * (1.0 - hub_score)
            )
            
            scored_candidates.append((candidate_idx, score))
        
        # Sort by score (lower is better)
        scored_candidates.sort(key=lambda x: x[1])
        
        return scored_candidates
    
    def score_candidates_fast(
        self,
        start_idx: int,
        target_idx: int,
        candidate_indices: List[int],
        current_depth: int = 0
    ) -> List[Tuple[int, float]]:
        """
        Two-stage scoring: fast filter then accurate score.
        
        Args:
            start_idx: Current page index
            target_idx: Target page index
            candidate_indices: List of candidate indices
            current_depth: Current search depth
            
        Returns:
            List of (candidate_idx, score) tuples sorted by score
        """
        self.stats['total_candidates_evaluated'] += len(candidate_indices)
        
        # Stage 1: Fast cosine filtering
        filtered_candidates = self.stage1_filter(candidate_indices, target_idx)
        
        # Stage 2: MLP scoring on filtered candidates
        scored_candidates = self.stage2_score(
            start_idx,
            target_idx,
            filtered_candidates,
            current_depth
        )
        
        return scored_candidates
    
    def get_best_candidates(
        self,
        start_idx: int,
        target_idx: int,
        candidate_indices: List[int],
        top_k: int = 10,
        current_depth: int = 0
    ) -> List[int]:
        """
        Get top-k best candidates using fast two-stage scoring.
        
        Args:
            start_idx: Current page index
            target_idx: Target page index
            candidate_indices: List of candidate indices
            top_k: Number of top candidates to return
            current_depth: Current search depth
            
        Returns:
            List of top-k candidate indices
        """
        scored_candidates = self.score_candidates_fast(
            start_idx,
            target_idx,
            candidate_indices,
            current_depth
        )
        
        return [idx for idx, _ in scored_candidates[:top_k]]
    
    def get_stats(self) -> dict:
        """Get performance statistics."""
        total = self.stats['total_candidates_evaluated']
        stage2 = self.stats['stage2_evaluations']
        
        if total > 0:
            reduction = (1 - stage2 / total) * 100
        else:
            reduction = 0
        
        return {
            **self.stats,
            'mlp_reduction_percentage': reduction
        }
    
    def reset_stats(self):
        """Reset statistics."""
        self.stats = {
            'total_candidates_evaluated': 0,
            'stage1_evaluations': 0,
            'stage2_evaluations': 0,
            'mlp_calls_saved': 0
        }


def load_fast_hybrid_scorer(
    model_path: Path,
    embeddings_dir: Path,
    graph_dir: Path,
    stage1_top_k: int = 20,
    **kwargs
) -> FastHybridScorer:
    """
    Load fast hybrid scorer with all required data.
    
    Args:
        model_path: Path to trained MLP model
        embeddings_dir: Directory containing embeddings
        graph_dir: Directory containing graph data
        stage1_top_k: Number of candidates to keep after stage 1
        **kwargs: Additional arguments for FastHybridScorer
        
    Returns:
        Initialized FastHybridScorer
    """
    # Load embeddings
    embeddings_file = embeddings_dir / "embeddings.npy"
    embeddings = np.load(embeddings_file)
    
    # Load graph statistics
    stats_file = graph_dir / "graph_statistics.json"
    import json
    with open(stats_file, 'r') as f:
        graph_stats = json.load(f)
    
    # Create scorer
    scorer = FastHybridScorer(
        model_path=model_path,
        embeddings=embeddings,
        graph_stats=graph_stats,
        stage1_top_k=stage1_top_k,
        **kwargs
    )
    
    return scorer


if __name__ == "__main__":
    print("Testing Fast Hybrid Scorer...")
    
    model_path = Path("models/checkpoints/mlp_scorer_best.pt")
    embeddings_dir = Path("data/embeddings")
    graph_dir = Path("data/graph")
    
    if all(p.exists() for p in [model_path, embeddings_dir, graph_dir]):
        scorer = load_fast_hybrid_scorer(
            model_path, embeddings_dir, graph_dir, stage1_top_k=20
        )
        print(f"✓ Fast hybrid scorer loaded")
        print(f"✓ Stage 1 top-k: {scorer.stage1_top_k}")
        
        # Test with dummy candidates
        test_candidates = list(range(100))
        scored = scorer.score_candidates_fast(0, 50, test_candidates)
        
        stats = scorer.get_stats()
        print(f"\nPerformance stats:")
        print(f"  Total candidates: {stats['total_candidates_evaluated']}")
        print(f"  MLP calls: {stats['stage2_evaluations']}")
        print(f"  MLP reduction: {stats['mlp_reduction_percentage']:.1f}%")
    else:
        print("✗ Required files not found")