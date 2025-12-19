"""
beam_search_navigator.py
------------------------
Beam Search algorithm for Wikipedia navigation.

Explores multiple paths simultaneously to find the shortest path.
Video'daki gibi minimum tıklama için optimize edilmiş.
"""

import time
import heapq
from typing import List, Tuple, Optional, Set
from dataclasses import dataclass, field
import numpy as np


@dataclass(order=True)
class BeamPath:
    """
    Beam search için path representation.
    
    Priority queue için comparable olmalı.
    """
    score: float = field(compare=True)  # Lower is better (negative similarity)
    path: List[str] = field(compare=False)
    current: str = field(compare=False)
    depth: int = field(compare=False)
    
    def __repr__(self):
        return f"BeamPath(score={self.score:.4f}, depth={self.depth}, current={self.current})"


class BeamSearchNavigator:
    """
    Beam Search Navigator for Wikipedia.
    
    Explores top-k paths simultaneously to find shortest path to target.
    Video'daki approach: Her adımda en iyi k path'i tut ve explore et.
    
    Advantages:
    - Finds shorter paths than greedy search
    - More robust to local optima
    - Configurable beam width (k)
    
    Disadvantages:
    - Slower than greedy (explores multiple paths)
    - Memory usage increases with beam width
    """
    
    def __init__(
        self,
        embedder,
        scraper,
        beam_width: int = 3,
        max_depth: int = 10,
        verbose: bool = False
    ):
        """
        Initialize Beam Search Navigator.
        
        Args:
            embedder: WikiEmbedder instance
            scraper: WikipediaScraper instance
            beam_width: Number of paths to explore simultaneously (default: 3)
            max_depth: Maximum search depth (default: 10)
            verbose: Print debug information
        """
        self.embedder = embedder
        self.scraper = scraper
        self.beam_width = beam_width
        self.max_depth = max_depth
        self.verbose = verbose
        
        # Statistics
        self.nodes_explored = 0
        self.paths_evaluated = 0
    
    def search(
        self,
        start: str,
        target: str
    ) -> Optional[Tuple[List[str], float]]:
        """
        Beam search from start to target.
        
        Args:
            start: Starting Wikipedia page
            target: Target Wikipedia page
        
        Returns:
            (path, score) if found, None otherwise
            path: List of page names from start to target
            score: Total path score (lower is better)
        """
        if self.verbose:
            print(f"\n🔍 Beam Search: {start} → {target}")
            print(f"   Beam width: {self.beam_width}, Max depth: {self.max_depth}")
        
        start_time = time.time()
        self.nodes_explored = 0
        self.paths_evaluated = 0
        
        # Get target embedding once
        target_emb = self.embedder.get_embedding(target)
        
        # Initialize beam with start path
        # Score is negative similarity (lower is better for min-heap)
        start_score = -self._similarity(start, target_emb)
        beam = [BeamPath(
            score=start_score,
            path=[start],
            current=start,
            depth=0
        )]
        
        # Track visited pages to avoid cycles
        visited: Set[str] = {start}
        
        # Beam search loop
        for depth in range(self.max_depth):
            if self.verbose:
                print(f"\n   Depth {depth}: {len(beam)} paths in beam")
            
            # Check if any path reached target
            for beam_path in beam:
                if beam_path.current == target:
                    elapsed = time.time() - start_time
                    if self.verbose:
                        print(f"\n✅ Found target!")
                        print(f"   Path length: {len(beam_path.path)}")
                        print(f"   Nodes explored: {self.nodes_explored}")
                        print(f"   Time: {elapsed:.2f}s")
                    return beam_path.path, -beam_path.score
            
            # Expand all paths in beam
            candidates = []
            
            for beam_path in beam:
                # Get links from current page
                links = self.scraper.get_links(beam_path.current)
                self.nodes_explored += 1
                
                if not links:
                    continue
                
                # Filter out visited pages
                unvisited_links = [link for link in links if link not in visited]
                
                if not unvisited_links:
                    continue
                
                # Score all links
                link_scores = self._score_links(unvisited_links, target_emb)
                self.paths_evaluated += len(link_scores)
                
                # Create new paths for each link
                for link, similarity in link_scores:
                    new_path = beam_path.path + [link]
                    new_score = beam_path.score - similarity  # Accumulate negative similarity
                    
                    candidates.append(BeamPath(
                        score=new_score,
                        path=new_path,
                        current=link,
                        depth=depth + 1
                    ))
            
            if not candidates:
                if self.verbose:
                    print(f"\n❌ No more candidates to explore")
                return None
            
            # Select top-k candidates for next beam
            # Use heapq for efficient top-k selection
            beam = heapq.nsmallest(self.beam_width, candidates)
            
            # Mark new pages as visited
            for beam_path in beam:
                visited.add(beam_path.current)
            
            if self.verbose:
                print(f"   Top {min(3, len(beam))} paths:")
                for i, bp in enumerate(beam[:3], 1):
                    print(f"   {i}. {bp.current:<30} (score: {-bp.score:.4f}, depth: {bp.depth})")
        
        # Max depth reached
        if self.verbose:
            print(f"\n❌ Max depth ({self.max_depth}) reached")
        
        return None
    
    def _similarity(self, page: str, target_emb: np.ndarray) -> float:
        """
        Calculate similarity between page and target.
        
        Args:
            page: Page name
            target_emb: Target embedding
        
        Returns:
            Similarity score (0-1)
        """
        page_emb = self.embedder.get_embedding(page)
        return self.embedder.cosine_similarity(page_emb, target_emb)
    
    def _score_links(
        self,
        links: List[str],
        target_emb: np.ndarray
    ) -> List[Tuple[str, float]]:
        """
        Score all links by similarity to target.
        
        Args:
            links: List of link names
            target_emb: Target embedding
        
        Returns:
            List of (link, similarity) tuples
        """
        # Batch get embeddings
        link_embeddings = self.embedder.get_embeddings_batch(links, verbose=False)
        
        # Calculate similarities
        scores = []
        for link, link_emb in zip(links, link_embeddings):
            similarity = self.embedder.cosine_similarity(target_emb, link_emb)
            scores.append((link, similarity))
        
        return scores
    
    def get_stats(self) -> dict:
        """
        Get search statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            'nodes_explored': self.nodes_explored,
            'paths_evaluated': self.paths_evaluated,
            'beam_width': self.beam_width,
            'max_depth': self.max_depth
        }


# Convenience function
def beam_search(
    start: str,
    target: str,
    embedder,
    scraper,
    beam_width: int = 3,
    max_depth: int = 10,
    verbose: bool = False
) -> Optional[Tuple[List[str], float]]:
    """
    Convenience function for beam search.
    
    Args:
        start: Starting Wikipedia page
        target: Target Wikipedia page
        embedder: WikiEmbedder instance
        scraper: WikipediaScraper instance
        beam_width: Number of paths to explore simultaneously
        max_depth: Maximum search depth
        verbose: Print debug information
    
    Returns:
        (path, score) if found, None otherwise
    """
    navigator = BeamSearchNavigator(
        embedder=embedder,
        scraper=scraper,
        beam_width=beam_width,
        max_depth=max_depth,
        verbose=verbose
    )
    return navigator.search(start, target)