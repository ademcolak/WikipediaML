"""
parallel_evaluator.py
--------------------
Parallel link evaluation for faster Wikipedia navigation.

Uses ThreadPoolExecutor to evaluate multiple links simultaneously.
"""

import time
import numpy as np
from typing import List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass


@dataclass
class LinkScore:
    """Link ve similarity score'u."""
    link: str
    score: float
    index: int  # Original index


class ParallelLinkEvaluator:
    """
    Parallel link evaluation using ThreadPoolExecutor.
    
    Evaluates multiple links simultaneously for faster processing.
    Especially useful when dealing with pages that have 50+ links.
    """
    
    def __init__(self, max_workers: int = 4, verbose: bool = False):
        """
        Initialize Parallel Link Evaluator.
        
        Args:
            max_workers: Maximum number of parallel workers (default: 4)
            verbose: Print debug information
        """
        self.max_workers = max_workers
        self.verbose = verbose
        self.total_evaluations = 0
        self.total_time = 0.0
    
    def evaluate_links_parallel(
        self,
        links: List[str],
        target_embedding: np.ndarray,
        embedder,
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Evaluate links in parallel and return top-k by similarity.
        
        Args:
            links: List of candidate links
            target_embedding: Target page embedding
            embedder: WikiEmbedder instance
            top_k: Number of top links to return
        
        Returns:
            List of (link, score) tuples, sorted by score (descending)
        """
        if not links:
            return []
        
        if len(links) <= top_k:
            # Too few links, no need for parallel processing
            return self._evaluate_sequential(links, target_embedding, embedder)
        
        start_time = time.time()
        
        # Split links into chunks for parallel processing
        chunk_size = max(1, len(links) // self.max_workers)
        chunks = [links[i:i + chunk_size] for i in range(0, len(links), chunk_size)]
        
        if self.verbose:
            print(f"   🔀 Parallel evaluation: {len(links)} links, {len(chunks)} chunks, {self.max_workers} workers")
        
        # Process chunks in parallel
        all_scores = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all chunks
            future_to_chunk = {
                executor.submit(
                    self._evaluate_chunk,
                    chunk,
                    target_embedding,
                    embedder,
                    i * chunk_size
                ): i for i, chunk in enumerate(chunks)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_chunk):
                chunk_scores = future.result()
                all_scores.extend(chunk_scores)
        
        # Sort by score (descending)
        all_scores.sort(key=lambda x: x.score, reverse=True)
        
        # Get top-k
        top_scores = all_scores[:top_k]
        
        elapsed = time.time() - start_time
        self.total_evaluations += len(links)
        self.total_time += elapsed
        
        if self.verbose:
            print(f"   ✅ Evaluated {len(links)} links in {elapsed:.3f}s ({len(links)/elapsed:.1f} links/sec)")
        
        # Convert to list of tuples
        return [(score.link, score.score) for score in top_scores]
    
    def _evaluate_chunk(
        self,
        chunk: List[str],
        target_embedding: np.ndarray,
        embedder,
        start_index: int
    ) -> List[LinkScore]:
        """
        Evaluate a chunk of links.
        
        Args:
            chunk: List of links to evaluate
            target_embedding: Target page embedding
            embedder: WikiEmbedder instance
            start_index: Starting index for this chunk
        
        Returns:
            List of LinkScore objects
        """
        # Get embeddings for all links in chunk (batch processing)
        link_embeddings = embedder.get_embeddings_batch(chunk, verbose=False)
        
        # Calculate similarities
        scores = []
        for i, (link, link_emb) in enumerate(zip(chunk, link_embeddings)):
            similarity = self._cosine_similarity(target_embedding, link_emb)
            scores.append(LinkScore(
                link=link,
                score=similarity,
                index=start_index + i
            ))
        
        return scores
    
    def _evaluate_sequential(
        self,
        links: List[str],
        target_embedding: np.ndarray,
        embedder
    ) -> List[Tuple[str, float]]:
        """
        Fallback: Sequential evaluation for small link lists.
        
        Args:
            links: List of links to evaluate
            target_embedding: Target page embedding
            embedder: WikiEmbedder instance
        
        Returns:
            List of (link, score) tuples
        """
        # Get all embeddings at once (batch processing)
        link_embeddings = embedder.get_embeddings_batch(links, verbose=False)
        
        # Calculate similarities
        scores = []
        for link, link_emb in zip(links, link_embeddings):
            similarity = self._cosine_similarity(target_embedding, link_emb)
            scores.append((link, similarity))
        
        # Sort by score (descending)
        scores.sort(key=lambda x: x[1], reverse=True)
        
        return scores
    
    def _cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            emb1: First embedding
            emb2: Second embedding
        
        Returns:
            Cosine similarity score
        """
        dot_product = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def get_stats(self) -> dict:
        """
        Get evaluation statistics.
        
        Returns:
            Dictionary with statistics
        """
        avg_time = self.total_time / self.total_evaluations if self.total_evaluations > 0 else 0
        throughput = self.total_evaluations / self.total_time if self.total_time > 0 else 0
        
        return {
            'total_evaluations': self.total_evaluations,
            'total_time': self.total_time,
            'avg_time_per_evaluation': avg_time,
            'throughput': throughput
        }
    
    def reset_stats(self):
        """Reset statistics."""
        self.total_evaluations = 0
        self.total_time = 0.0


# Convenience function
def evaluate_links_parallel(
    links: List[str],
    target_embedding: np.ndarray,
    embedder,
    top_k: int = 5,
    max_workers: int = 4,
    verbose: bool = False
) -> List[Tuple[str, float]]:
    """
    Convenience function for parallel link evaluation.
    
    Args:
        links: List of candidate links
        target_embedding: Target page embedding
        embedder: WikiEmbedder instance
        top_k: Number of top links to return
        max_workers: Maximum number of parallel workers
        verbose: Print debug information
    
    Returns:
        List of (link, score) tuples, sorted by score (descending)
    """
    evaluator = ParallelLinkEvaluator(max_workers=max_workers, verbose=verbose)
    return evaluator.evaluate_links_parallel(links, target_embedding, embedder, top_k)