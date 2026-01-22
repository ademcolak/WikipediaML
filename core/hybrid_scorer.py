#!/usr/bin/env python3
"""
Hybrid Scorer for Wikipedia Navigation
Combines MLP predictions, cosine similarity, and hub scores for optimal navigation.
"""

import torch
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional
import pickle

from models.mlp_scorer import create_mlp_scorer


class HybridScorer:
    """
    Hybrid scoring system that combines multiple heuristics:
    - MLP neural network predictions
    - Cosine similarity between embeddings
    - Hub scores (in-degree) for distant targets
    """
    
    def __init__(
        self,
        model_path: Path,
        embeddings: np.ndarray,
        graph_stats: dict,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu',
        alpha: float = 0.6,  # Weight for MLP score
        beta: float = 0.3,   # Weight for cosine similarity
        gamma: float = 0.1   # Weight for hub score
    ):
        """
        Initialize hybrid scorer.
        
        Args:
            model_path: Path to trained MLP model
            embeddings: Page embeddings array
            graph_stats: Graph statistics including in-degrees
            device: Device for model inference
            alpha: Weight for MLP distance prediction
            beta: Weight for cosine similarity
            gamma: Weight for hub score
        """
        self.device = device
        self.embeddings = embeddings
        self.graph_stats = graph_stats
        
        # Weights for hybrid scoring
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        
        # Load trained MLP model
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
        
        # Precompute normalized hub scores if available
        self.hub_scores = None
        if 'in_degrees' in graph_stats:
            in_degrees = np.array(graph_stats['in_degrees'])
            # Normalize to [0, 1]
            max_degree = in_degrees.max()
            self.hub_scores = in_degrees / max_degree if max_degree > 0 else in_degrees
    
    def cosine_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Cosine similarity score [0, 1]
        """
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        # Convert from [-1, 1] to [0, 1]
        return (similarity + 1) / 2
    
    def predict_mlp_distance(
        self,
        start_idx: int,
        target_idx: int,
        candidate_idx: int
    ) -> float:
        """
        Predict distance using MLP model.
        
        Args:
            start_idx: Current page index
            target_idx: Target page index
            candidate_idx: Candidate link index
            
        Returns:
            Predicted distance
        """
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
            
            distance = self.model(start_emb, target_emb, candidate_emb)
            return distance.cpu().item()
    
    def get_hub_score(self, page_idx: int) -> float:
        """
        Get normalized hub score for a page.
        
        Args:
            page_idx: Page index
            
        Returns:
            Hub score [0, 1]
        """
        if self.hub_scores is None:
            return 0.0
        
        if page_idx < 0 or page_idx >= len(self.hub_scores):
            return 0.0
        
        return float(self.hub_scores[page_idx])
    
    def score_candidate(
        self,
        start_idx: int,
        target_idx: int,
        candidate_idx: int,
        current_depth: int = 0,
        max_depth: int = 10
    ) -> float:
        """
        Score a candidate link using hybrid heuristic.
        
        Args:
            start_idx: Current page index
            target_idx: Target page index
            candidate_idx: Candidate link index
            current_depth: Current search depth
            max_depth: Maximum expected depth
            
        Returns:
            Hybrid score (lower is better for A* search)
        """
        # 1. MLP distance prediction
        mlp_distance = self.predict_mlp_distance(start_idx, target_idx, candidate_idx)
        
        # 2. Cosine similarity (convert to distance: 1 - similarity)
        candidate_emb = self.embeddings[candidate_idx]
        target_emb = self.embeddings[target_idx]
        similarity = self.cosine_similarity(candidate_emb, target_emb)
        cosine_distance = 1.0 - similarity
        
        # 3. Hub score (for distant targets, prefer hubs)
        hub_score = self.get_hub_score(candidate_idx)
        
        # Adjust hub weight based on estimated distance
        # If target seems far, increase hub importance
        if mlp_distance > 5:
            gamma_adjusted = self.gamma * 2.0
        else:
            gamma_adjusted = self.gamma
        
        # Combine scores (lower is better)
        # Hub score is inverted (1 - hub) because we want to prefer hubs
        hybrid_score = (
            self.alpha * mlp_distance +
            self.beta * cosine_distance +
            gamma_adjusted * (1.0 - hub_score)
        )
        
        return hybrid_score
    
    def score_candidates_batch(
        self,
        start_idx: int,
        target_idx: int,
        candidate_indices: List[int],
        current_depth: int = 0
    ) -> List[Tuple[int, float]]:
        """
        Score multiple candidates efficiently.
        
        Args:
            start_idx: Current page index
            target_idx: Target page index
            candidate_indices: List of candidate indices
            current_depth: Current search depth
            
        Returns:
            List of (candidate_idx, score) tuples sorted by score
        """
        scores = []
        
        for candidate_idx in candidate_indices:
            score = self.score_candidate(
                start_idx,
                target_idx,
                candidate_idx,
                current_depth
            )
            scores.append((candidate_idx, score))
        
        # Sort by score (lower is better)
        scores.sort(key=lambda x: x[1])
        
        return scores
    
    def get_best_candidates(
        self,
        start_idx: int,
        target_idx: int,
        candidate_indices: List[int],
        top_k: int = 10,
        current_depth: int = 0
    ) -> List[int]:
        """
        Get top-k best candidates.
        
        Args:
            start_idx: Current page index
            target_idx: Target page index
            candidate_indices: List of candidate indices
            top_k: Number of top candidates to return
            current_depth: Current search depth
            
        Returns:
            List of top-k candidate indices
        """
        scored_candidates = self.score_candidates_batch(
            start_idx,
            target_idx,
            candidate_indices,
            current_depth
        )
        
        # Return top-k candidates
        return [idx for idx, _ in scored_candidates[:top_k]]


def load_hybrid_scorer(
    model_path: Path,
    embeddings_dir: Path,
    graph_dir: Path,
    **kwargs
) -> HybridScorer:
    """
    Load hybrid scorer with all required data.
    
    Args:
        model_path: Path to trained MLP model
        embeddings_dir: Directory containing embeddings
        graph_dir: Directory containing graph data
        **kwargs: Additional arguments for HybridScorer
        
    Returns:
        Initialized HybridScorer
    """
    # Load embeddings
    embeddings_file = embeddings_dir / "embeddings.npy"
    embeddings = np.load(embeddings_file)
    
    # Load graph statistics
    stats_file = graph_dir / "graph_statistics.json"
    import json
    with open(stats_file, 'r') as f:
        graph_stats = json.load(f)

    # Optional fingerprint check (if metadata exists)
    meta_file = embeddings_dir / "embedding_metadata.pkl"
    if meta_file.exists():
        try:
            with open(meta_file, "rb") as f:
                meta = pickle.load(f)
            graph_fp = graph_stats.get("pages_fingerprint")
            embed_fp = meta.get("pages_fingerprint")
            if graph_fp and embed_fp and graph_fp != embed_fp:
                print("⚠️  WARNING: Embeddings/graph fingerprint mismatch detected.")
        except Exception as e:
            print(f"⚠️  Warning: Could not read embedding metadata ({e})")
    
    # Create scorer
    scorer = HybridScorer(
        model_path=model_path,
        embeddings=embeddings,
        graph_stats=graph_stats,
        **kwargs
    )
    
    return scorer


if __name__ == "__main__":
    # Test the hybrid scorer
    print("Testing Hybrid Scorer...")
    
    model_path = Path("models/checkpoints/mlp_scorer_best.pt")
    embeddings_dir = Path("data/embeddings")
    graph_dir = Path("data/graph")
    
    if model_path.exists() and embeddings_dir.exists() and graph_dir.exists():
        scorer = load_hybrid_scorer(model_path, embeddings_dir, graph_dir)
        print(f"✓ Hybrid scorer loaded successfully")
        print(f"✓ Weights: α={scorer.alpha}, β={scorer.beta}, γ={scorer.gamma}")
        
        # Test scoring
        test_candidates = [0, 1, 2, 3, 4]
        scores = scorer.score_candidates_batch(0, 100, test_candidates)
        print(f"\nTest scores for candidates {test_candidates}:")
        for idx, score in scores:
            print(f"  Candidate {idx}: {score:.4f}")
    else:
        print("✗ Required files not found. Run training pipeline first.")