"""
astar_navigator.py
------------------
A* Search algorithm for Wikipedia navigation.

Finds optimal (shortest) path using heuristic-guided search.
Video'daki approach: g(n) + h(n) optimization.
"""

import time
import heapq
from typing import List, Tuple, Optional, Set, Dict
from dataclasses import dataclass, field
import numpy as np


@dataclass(order=True)
class AStarNode:
    """
    A* search için node representation.
    
    f(n) = g(n) + h(n)
    - g(n): Cost from start to current node (path length)
    - h(n): Heuristic cost from current to goal (1 - similarity)
    """
    f_score: float = field(compare=True)  # f(n) = g(n) + h(n)
    g_score: int = field(compare=False)   # Path length from start
    h_score: float = field(compare=False) # Heuristic to goal
    current: str = field(compare=False)
    path: List[str] = field(compare=False)
    
    def __repr__(self):
        return f"AStarNode(f={self.f_score:.4f}, g={self.g_score}, h={self.h_score:.4f}, current={self.current})"


class AStarNavigator:
    """
    A* Search Navigator for Wikipedia.
    
    Finds optimal (shortest) path using informed search.
    
    Algorithm:
    1. f(n) = g(n) + h(n)
       - g(n) = path length (number of clicks)
       - h(n) = 1 - cosine_similarity(current, target)
    2. Always expand node with lowest f(n)
    3. Guaranteed to find shortest path (if heuristic is admissible)
    
    Advantages:
    - Finds optimal (shortest) path
    - More efficient than uninformed search
    - Guaranteed optimality with admissible heuristic
    
    Disadvantages:
    - Slower than greedy (explores more nodes)
    - Memory intensive (stores all nodes)
    """
    
    def __init__(
        self,
        embedder,
        scraper,
        max_depth: int = 10,
        heuristic_weight: float = 1.0,
        verbose: bool = False
    ):
        """
        Initialize A* Navigator.
        
        Args:
            embedder: WikiEmbedder instance
            scraper: WikipediaScraper instance
            max_depth: Maximum search depth (default: 10)
            heuristic_weight: Weight for heuristic (default: 1.0)
                            > 1.0: Weighted A* (faster, less optimal)
                            = 1.0: Standard A* (optimal)
                            < 1.0: More like Dijkstra (slower, still optimal)
            verbose: Print debug information
        """
        self.embedder = embedder
        self.scraper = scraper
        self.max_depth = max_depth
        self.heuristic_weight = heuristic_weight
        self.verbose = verbose
        
        # Statistics
        self.nodes_explored = 0
        self.nodes_generated = 0
    
    def search(
        self,
        start: str,
        target: str
    ) -> Optional[Tuple[List[str], float]]:
        """
        A* search from start to target.
        
        Args:
            start: Starting Wikipedia page
            target: Target Wikipedia page
        
        Returns:
            (path, cost) if found, None otherwise
            path: List of page names from start to target
            cost: Total path cost (g_score)
        """
        if self.verbose:
            print(f"\n🔍 A* Search: {start} → {target}")
            print(f"   Max depth: {self.max_depth}, Heuristic weight: {self.heuristic_weight}")
        
        start_time = time.time()
        self.nodes_explored = 0
        self.nodes_generated = 0
        
        # Get target embedding once
        target_emb = self.embedder.get_embedding(target)
        
        # Initialize
        start_h = self._heuristic(start, target_emb)
        start_node = AStarNode(
            f_score=start_h * self.heuristic_weight,
            g_score=0,
            h_score=start_h,
            current=start,
            path=[start]
        )
        
        # Priority queue (min-heap by f_score)
        open_set = [start_node]
        
        # Track best g_score for each node
        g_scores: Dict[str, int] = {start: 0}
        
        # Track visited nodes
        closed_set: Set[str] = set()
        
        # A* search loop
        while open_set:
            # Get node with lowest f_score
            current_node = heapq.heappop(open_set)
            
            # Check if reached target
            if current_node.current == target:
                elapsed = time.time() - start_time
                if self.verbose:
                    print(f"\n✅ Found optimal path!")
                    print(f"   Path length: {len(current_node.path)} ({current_node.g_score} clicks)")
                    print(f"   Nodes explored: {self.nodes_explored}")
                    print(f"   Nodes generated: {self.nodes_generated}")
                    print(f"   Time: {elapsed:.2f}s")
                return current_node.path, current_node.g_score
            
            # Skip if already visited with better path
            if current_node.current in closed_set:
                continue
            
            # Mark as visited
            closed_set.add(current_node.current)
            self.nodes_explored += 1
            
            # Check depth limit
            if current_node.g_score >= self.max_depth:
                continue
            
            if self.verbose and self.nodes_explored % 10 == 0:
                print(f"   Explored: {self.nodes_explored}, Queue: {len(open_set)}, "
                      f"Current: {current_node.current} (f={current_node.f_score:.4f})")
            
            # Get neighbors
            links = self.scraper.get_links(current_node.current)
            
            if not links:
                continue
            
            # Expand neighbors
            for link in links:
                # Skip if already visited
                if link in closed_set:
                    continue
                
                # Calculate scores
                tentative_g = current_node.g_score + 1
                
                # Skip if we've seen this node with better g_score
                if link in g_scores and tentative_g >= g_scores[link]:
                    continue
                
                # This is the best path to this node so far
                g_scores[link] = tentative_g
                
                # Calculate heuristic
                h = self._heuristic(link, target_emb)
                f = tentative_g + (h * self.heuristic_weight)
                
                # Create new node
                new_node = AStarNode(
                    f_score=f,
                    g_score=tentative_g,
                    h_score=h,
                    current=link,
                    path=current_node.path + [link]
                )
                
                heapq.heappush(open_set, new_node)
                self.nodes_generated += 1
        
        # No path found
        if self.verbose:
            print(f"\n❌ No path found")
            print(f"   Nodes explored: {self.nodes_explored}")
        
        return None
    
    def _heuristic(self, page: str, target_emb: np.ndarray) -> float:
        """
        Heuristic function: h(n) = 1 - similarity
        
        This is admissible because:
        - similarity ∈ [0, 1]
        - h(n) ∈ [0, 1]
        - h(n) = 0 when page == target (goal)
        - h(n) never overestimates (admissible)
        
        Args:
            page: Current page name
            target_emb: Target embedding
        
        Returns:
            Heuristic cost (0-1, lower is better)
        """
        page_emb = self.embedder.get_embedding(page)
        similarity = self.embedder.cosine_similarity(page_emb, target_emb)
        return 1.0 - similarity
    
    def get_stats(self) -> dict:
        """
        Get search statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            'nodes_explored': self.nodes_explored,
            'nodes_generated': self.nodes_generated,
            'max_depth': self.max_depth,
            'heuristic_weight': self.heuristic_weight
        }


# Convenience function
def astar_search(
    start: str,
    target: str,
    embedder,
    scraper,
    max_depth: int = 10,
    heuristic_weight: float = 1.0,
    verbose: bool = False
) -> Optional[Tuple[List[str], float]]:
    """
    Convenience function for A* search.
    
    Args:
        start: Starting Wikipedia page
        target: Target Wikipedia page
        embedder: WikiEmbedder instance
        scraper: WikipediaScraper instance
        max_depth: Maximum search depth
        heuristic_weight: Weight for heuristic (1.0 = standard A*)
        verbose: Print debug information
    
    Returns:
        (path, cost) if found, None otherwise
    """
    navigator = AStarNavigator(
        embedder=embedder,
        scraper=scraper,
        max_depth=max_depth,
        heuristic_weight=heuristic_weight,
        verbose=verbose
    )
    return navigator.search(start, target)