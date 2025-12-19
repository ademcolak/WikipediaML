"""
embedding_navigator.py
----------------------
Embedding-based link filtering for Wikipedia navigation.

Uses Sentence-BERT to compute semantic similarity between links and target.
"""

from typing import List, Optional, Dict
import numpy as np


class EmbeddingNavigator:
    """
    Embedding-based navigator using Sentence-BERT.
    
    Filters available links by semantic similarity to target page.
    Uses pre-trained sentence-transformers model.
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', cache_size: int = 10000):
        """
        Initialize Embedding Navigator.
        
        Args:
            model_name: Sentence-transformers model name
            cache_size: Maximum number of embeddings to cache
        """
        try:
            from sentence_transformers import SentenceTransformer
            self.SentenceTransformer = SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. Install with: pip install sentence-transformers"
            )
        
        print(f"📦 Loading embedding model: {model_name}...")
        self.model = self.SentenceTransformer(model_name)
        print(f"✅ Model loaded!")
        
        # Cache for embeddings
        self.cache: Dict[str, np.ndarray] = {}
        self.cache_size = cache_size
        self.cache_hits = 0
        self.cache_misses = 0
    
    def get_embedding(self, text: str) -> np.ndarray:
        """
        Get embedding for text (with caching).
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector
        """
        if text in self.cache:
            self.cache_hits += 1
            return self.cache[text]
        
        self.cache_misses += 1
        embedding = self.model.encode([text])[0]
        
        # Add to cache (with size limit)
        if len(self.cache) < self.cache_size:
            self.cache[text] = embedding
        
        return embedding
    
    def filter_links(
        self,
        available_links: List[str],
        target_page: str,
        k: int = 5
    ) -> List[str]:
        """
        Filter links by semantic similarity to target.
        
        Args:
            available_links: List of available links
            target_page: Target Wikipedia page
            k: Number of top links to return
        
        Returns:
            Top k links by similarity
        """
        if not available_links:
            return []
        
        if len(available_links) <= k:
            return available_links
        
        # Get embeddings
        target_embedding = self.get_embedding(target_page)
        link_embeddings = np.array([self.get_embedding(link) for link in available_links])
        
        # Compute cosine similarity
        similarities = self._cosine_similarity(target_embedding, link_embeddings)
        
        # Get top k indices
        top_indices = np.argsort(similarities)[-k:][::-1]
        
        # Return top k links
        return [available_links[i] for i in top_indices]
    
    def _cosine_similarity(
        self,
        vec1: np.ndarray,
        vec2: np.ndarray
    ) -> np.ndarray:
        """
        Compute cosine similarity between vectors.
        
        Args:
            vec1: Single vector or matrix
            vec2: Matrix of vectors
        
        Returns:
            Similarity scores
        """
        # Normalize vectors
        vec1_norm = vec1 / np.linalg.norm(vec1)
        vec2_norm = vec2 / np.linalg.norm(vec2, axis=1, keepdims=True)
        
        # Compute dot product
        return np.dot(vec2_norm, vec1_norm)
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        total = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total * 100) if total > 0 else 0
        
        return {
            'cache_size': len(self.cache),
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate': hit_rate
        }
    
    def clear_cache(self):
        """Clear embedding cache."""
        self.cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0