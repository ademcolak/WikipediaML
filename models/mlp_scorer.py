#!/usr/bin/env python3
"""
MLP Scorer Model
Neural network that predicts the distance from a candidate link to the target page.
Takes embeddings of current page, target page, and candidate link as input.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple

class MLPScorer(nn.Module):
    """
    Multi-Layer Perceptron for scoring candidate links.
    
    Predicts the graph distance from a candidate link to the target page.
    """
    
    def __init__(
        self,
        embedding_dim: int = 384,
        hidden_dims: Tuple[int, ...] = (512, 256, 128),
        dropout: float = 0.2
    ):
        """
        Initialize the MLP Scorer.
        
        Args:
            embedding_dim: Dimension of input embeddings (384 for all-MiniLM-L6-v2)
            hidden_dims: Tuple of hidden layer dimensions
            dropout: Dropout probability for regularization
        """
        super().__init__()
        
        self.embedding_dim = embedding_dim
        self.hidden_dims = hidden_dims
        self.dropout = dropout
        
        # Input: concatenation of 3 embeddings (start, target, candidate)
        input_dim = embedding_dim * 3
        
        # Build layers
        layers = []
        prev_dim = input_dim
        
        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.BatchNorm1d(hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout)
            ])
            prev_dim = hidden_dim
        
        # Output layer: single value (predicted distance)
        layers.append(nn.Linear(prev_dim, 1))
        
        self.network = nn.Sequential(*layers)
        
        # Initialize weights
        self._init_weights()
    
    def _init_weights(self):
        """Initialize network weights using Xavier initialization."""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
    
    def forward(
        self,
        start_embedding: torch.Tensor,
        target_embedding: torch.Tensor,
        candidate_embedding: torch.Tensor
    ) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            start_embedding: Embedding of current page (batch_size, embedding_dim)
            target_embedding: Embedding of target page (batch_size, embedding_dim)
            candidate_embedding: Embedding of candidate link (batch_size, embedding_dim)
            
        Returns:
            Predicted distance (batch_size, 1)
        """
        # Concatenate embeddings
        x = torch.cat([start_embedding, target_embedding, candidate_embedding], dim=1)
        
        # Pass through network
        distance = self.network(x)
        
        # Apply ReLU to ensure non-negative distances
        distance = F.relu(distance)
        
        return distance
    
    def predict_distance(
        self,
        start_embedding: torch.Tensor,
        target_embedding: torch.Tensor,
        candidate_embedding: torch.Tensor
    ) -> torch.Tensor:
        """
        Predict distance (inference mode).
        
        Args:
            start_embedding: Embedding of current page
            target_embedding: Embedding of target page
            candidate_embedding: Embedding of candidate link
            
        Returns:
            Predicted distance
        """
        self.eval()
        with torch.no_grad():
            distance = self.forward(start_embedding, target_embedding, candidate_embedding)
        return distance


class MLPScorerWithAttention(nn.Module):
    """
    Enhanced MLP Scorer with attention mechanism.
    
    Uses attention to focus on relevant parts of the embeddings.
    """
    
    def __init__(
        self,
        embedding_dim: int = 384,
        hidden_dims: Tuple[int, ...] = (512, 256, 128),
        attention_heads: int = 4,
        dropout: float = 0.2
    ):
        """
        Initialize the enhanced MLP Scorer.
        
        Args:
            embedding_dim: Dimension of input embeddings
            hidden_dims: Tuple of hidden layer dimensions
            attention_heads: Number of attention heads
            dropout: Dropout probability
        """
        super().__init__()
        
        self.embedding_dim = embedding_dim
        self.hidden_dims = hidden_dims
        self.attention_heads = attention_heads
        self.dropout = dropout
        
        # Multi-head attention for embedding interaction
        self.attention = nn.MultiheadAttention(
            embed_dim=embedding_dim,
            num_heads=attention_heads,
            dropout=dropout,
            batch_first=True
        )
        
        # Layer norm after attention
        self.layer_norm = nn.LayerNorm(embedding_dim)
        
        # MLP layers
        input_dim = embedding_dim * 3
        layers = []
        prev_dim = input_dim
        
        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.BatchNorm1d(hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout)
            ])
            prev_dim = hidden_dim
        
        layers.append(nn.Linear(prev_dim, 1))
        self.network = nn.Sequential(*layers)
        
        self._init_weights()
    
    def _init_weights(self):
        """Initialize network weights."""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
    
    def forward(
        self,
        start_embedding: torch.Tensor,
        target_embedding: torch.Tensor,
        candidate_embedding: torch.Tensor
    ) -> torch.Tensor:
        """
        Forward pass with attention.
        
        Args:
            start_embedding: Embedding of current page (batch_size, embedding_dim)
            target_embedding: Embedding of target page (batch_size, embedding_dim)
            candidate_embedding: Embedding of candidate link (batch_size, embedding_dim)
            
        Returns:
            Predicted distance (batch_size, 1)
        """
        batch_size = start_embedding.size(0)
        
        # Stack embeddings for attention: (batch_size, 3, embedding_dim)
        embeddings = torch.stack([start_embedding, target_embedding, candidate_embedding], dim=1)
        
        # Apply self-attention
        attended, _ = self.attention(embeddings, embeddings, embeddings)
        
        # Residual connection and layer norm
        embeddings = self.layer_norm(embeddings + attended)
        
        # Flatten for MLP: (batch_size, 3 * embedding_dim)
        x = embeddings.view(batch_size, -1)
        
        # Pass through network
        distance = self.network(x)
        distance = F.relu(distance)
        
        return distance
    
    def predict_distance(
        self,
        start_embedding: torch.Tensor,
        target_embedding: torch.Tensor,
        candidate_embedding: torch.Tensor
    ) -> torch.Tensor:
        """Predict distance (inference mode)."""
        self.eval()
        with torch.no_grad():
            distance = self.forward(start_embedding, target_embedding, candidate_embedding)
        return distance


def create_mlp_scorer(
    model_type: str = "basic",
    embedding_dim: int = 384,
    **kwargs
) -> nn.Module:
    """
    Factory function to create MLP scorer models.
    
    Args:
        model_type: Type of model ("basic" or "attention")
        embedding_dim: Dimension of input embeddings
        **kwargs: Additional model-specific arguments
        
    Returns:
        MLP scorer model
    """
    if model_type == "basic":
        return MLPScorer(embedding_dim=embedding_dim, **kwargs)
    elif model_type == "attention":
        return MLPScorerWithAttention(embedding_dim=embedding_dim, **kwargs)
    else:
        raise ValueError(f"Unknown model type: {model_type}")


if __name__ == "__main__":
    # Test the models
    print("Testing MLP Scorer models...")
    
    batch_size = 32
    embedding_dim = 384
    
    # Create dummy data
    start_emb = torch.randn(batch_size, embedding_dim)
    target_emb = torch.randn(batch_size, embedding_dim)
    candidate_emb = torch.randn(batch_size, embedding_dim)
    
    # Test basic model
    print("\n1. Basic MLP Scorer:")
    basic_model = create_mlp_scorer("basic", embedding_dim)
    print(f"   Parameters: {sum(p.numel() for p in basic_model.parameters()):,}")
    output = basic_model(start_emb, target_emb, candidate_emb)
    print(f"   Output shape: {output.shape}")
    print(f"   Sample predictions: {output[:5].squeeze().tolist()}")
    
    # Test attention model
    print("\n2. MLP Scorer with Attention:")
    attention_model = create_mlp_scorer("attention", embedding_dim)
    print(f"   Parameters: {sum(p.numel() for p in attention_model.parameters()):,}")
    output = attention_model(start_emb, target_emb, candidate_emb)
    print(f"   Output shape: {output.shape}")
    print(f"   Sample predictions: {output[:5].squeeze().tolist()}")
    
    print("\n✓ Model tests completed successfully!")