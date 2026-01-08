#!/usr/bin/env python3
"""
Advanced Navigator with Backtracking and Tabu List
Enhanced navigation with dead-end detection and recovery mechanisms.
"""

from typing import List, Set, Optional, Dict, Tuple
from dataclasses import dataclass
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix, load_npz
import pickle

from core.hybrid_scorer import HybridScorer


@dataclass
class NavigationState:
    """State of navigation at a given point."""
    current_idx: int
    target_idx: int
    path: List[int]
    visited: Set[int]
    tabu_list: Set[int]
    depth: int
    score: float


class AdvancedNavigator:
    """
    Advanced navigator with backtracking and tabu list.
    
    Features:
    - Dead-end detection
    - Backtracking to previous best node
    - Tabu list to prevent revisiting failed paths
    - Adaptive exploration strategy
    """
    
    def __init__(
        self,
        adjacency_matrix: csr_matrix,
        page_mappings: dict,
        hybrid_scorer: HybridScorer,
        max_depth: int = 20,
        tabu_size: int = 100,
        backtrack_limit: int = 5
    ):
        """
        Initialize advanced navigator.
        
        Args:
            adjacency_matrix: Graph adjacency matrix
            page_mappings: Page ID to index mappings
            hybrid_scorer: Hybrid scoring system
            max_depth: Maximum search depth
            tabu_size: Maximum size of tabu list
            backtrack_limit: Maximum number of backtracks allowed
        """
        self.adjacency_matrix = adjacency_matrix
        self.pages = page_mappings['pages']
        self.page_id_to_index = page_mappings['page_id_to_index']
        self.index_to_page_id = page_mappings['index_to_page_id']
        self.hybrid_scorer = hybrid_scorer
        self.max_depth = max_depth
        self.tabu_size = tabu_size
        self.backtrack_limit = backtrack_limit
    
    def get_neighbors(self, page_idx: int) -> List[int]:
        """Get outgoing links from a page."""
        if page_idx < 0 or page_idx >= self.adjacency_matrix.shape[0]:  # type: ignore
            return []
        neighbors = self.adjacency_matrix[page_idx].indices
        return list(neighbors)
    
    def is_dead_end(
        self,
        current_idx: int,
        visited: Set[int],
        tabu_list: Set[int]
    ) -> bool:
        """
        Check if current node is a dead end.
        
        Args:
            current_idx: Current page index
            visited: Set of visited pages
            tabu_list: Set of tabu pages
            
        Returns:
            True if dead end, False otherwise
        """
        neighbors = self.get_neighbors(current_idx)
        
        # Check if all neighbors are either visited or in tabu list
        available_neighbors = [
            n for n in neighbors
            if n not in visited and n not in tabu_list
        ]
        
        return len(available_neighbors) == 0
    
    def find_backtrack_point(
        self,
        path: List[int],
        visited: Set[int],
        tabu_list: Set[int]
    ) -> Optional[int]:
        """
        Find a good point to backtrack to.
        
        Args:
            path: Current path (as page IDs)
            visited: Set of visited page indices
            tabu_list: Set of tabu page indices
            
        Returns:
            Index in path to backtrack to, or None if no valid point
        """
        # Try to backtrack to a node that still has unexplored neighbors
        for i in range(len(path) - 2, -1, -1):
            page_id = path[i]
            page_idx = self.page_id_to_index[page_id]
            
            neighbors = self.get_neighbors(page_idx)
            available = [
                n for n in neighbors
                if n not in visited and n not in tabu_list
            ]
            
            if available:
                return i
        
        return None
    
    def search(
        self,
        start_page_id: int,
        target_page_id: int,
        verbose: bool = False
    ) -> Optional[List[int]]:
        """
        Perform advanced search with backtracking.
        
        Args:
            start_page_id: Starting page ID
            target_page_id: Target page ID
            verbose: Print search progress
            
        Returns:
            Path as list of page IDs, or None if not found
        """
        # Validate inputs
        if start_page_id not in self.page_id_to_index:
            if verbose:
                print(f"✗ Start page {start_page_id} not in graph")
            return None
        
        if target_page_id not in self.page_id_to_index:
            if verbose:
                print(f"✗ Target page {target_page_id} not in graph")
            return None
        
        start_idx = self.page_id_to_index[start_page_id]
        target_idx = self.page_id_to_index[target_page_id]
        
        if start_idx == target_idx:
            return [start_page_id]
        
        if verbose:
            print(f"\n{'='*80}")
            print(f"Advanced Search: {self.pages[start_page_id]} → {self.pages[target_page_id]}")
            print(f"Max depth: {self.max_depth}, Tabu size: {self.tabu_size}")
            print(f"{'='*80}")
        
        # Initialize state
        state = NavigationState(
            current_idx=start_idx,
            target_idx=target_idx,
            path=[start_page_id],
            visited={start_idx},
            tabu_list=set(),
            depth=0,
            score=0.0
        )
        
        backtrack_count = 0
        
        # Search loop
        while state.depth < self.max_depth:
            if verbose:
                current_title = self.pages[self.index_to_page_id[state.current_idx]]
                print(f"\nDepth {state.depth + 1}: {current_title}")
            
            # Get neighbors
            neighbors = self.get_neighbors(state.current_idx)
            
            # Check if target is in neighbors
            if target_idx in neighbors:
                final_path = state.path + [target_page_id]
                if verbose:
                    print(f"\n✓ Target found! Path length: {len(final_path)}")
                    print(f"  Backtracks: {backtrack_count}")
                return final_path
            
            # Filter available neighbors
            available_neighbors = [
                n for n in neighbors
                if n not in state.visited and n not in state.tabu_list
            ]
            
            if verbose:
                print(f"  Total neighbors: {len(neighbors)}")
                print(f"  Available: {len(available_neighbors)}")
            
            # Check for dead end
            if not available_neighbors:
                if verbose:
                    print(f"  ✗ Dead end detected!")
                
                # Add current node to tabu list
                state.tabu_list.add(state.current_idx)
                
                # Limit tabu list size
                if len(state.tabu_list) > self.tabu_size:
                    # Remove oldest entry (FIFO)
                    state.tabu_list.pop()
                
                # Try to backtrack
                if backtrack_count >= self.backtrack_limit:
                    if verbose:
                        print(f"  ✗ Backtrack limit reached")
                    return None
                
                backtrack_point = self.find_backtrack_point(
                    state.path,
                    state.visited,
                    state.tabu_list
                )
                
                if backtrack_point is None:
                    if verbose:
                        print(f"  ✗ No valid backtrack point")
                    return None
                
                # Backtrack
                backtrack_count += 1
                state.path = state.path[:backtrack_point + 1]
                state.current_idx = self.page_id_to_index[state.path[-1]]
                state.depth = len(state.path) - 1
                
                if verbose:
                    backtrack_title = self.pages[self.index_to_page_id[state.current_idx]]
                    print(f"  ↩ Backtracking to: {backtrack_title} (depth {state.depth})")
                
                continue
            
            # Score available neighbors
            scored_neighbors = []
            for neighbor_idx in available_neighbors:
                score = self.hybrid_scorer.score_candidate(
                    start_idx=state.current_idx,
                    target_idx=target_idx,
                    candidate_idx=neighbor_idx,
                    current_depth=state.depth
                )
                scored_neighbors.append((neighbor_idx, score))
            
            # Sort by score (lower is better)
            scored_neighbors.sort(key=lambda x: x[1])
            
            # Choose best neighbor
            best_neighbor_idx, best_score = scored_neighbors[0]
            best_neighbor_id = self.index_to_page_id[best_neighbor_idx]
            
            if verbose:
                best_title = self.pages[best_neighbor_id]
                print(f"  → Moving to: {best_title} (score: {best_score:.4f})")
            
            # Move to best neighbor
            state.current_idx = best_neighbor_idx
            state.path.append(best_neighbor_id)
            state.visited.add(best_neighbor_idx)
            state.depth += 1
            state.score = best_score
        
        if verbose:
            print(f"\n✗ Target not found within {self.max_depth} steps")
        
        return None
    
    def search_with_stats(
        self,
        start_page_id: int,
        target_page_id: int
    ) -> Tuple[Optional[List[int]], Dict]:
        """
        Perform search and return statistics.
        
        Returns:
            Tuple of (path, statistics)
        """
        stats = {
            'success': False,
            'path_length': 0,
            'nodes_visited': 0,
            'backtracks': 0,
            'tabu_list_size': 0,
            'dead_ends_encountered': 0
        }
        
        # Validate
        if start_page_id not in self.page_id_to_index or target_page_id not in self.page_id_to_index:
            return None, stats
        
        start_idx = self.page_id_to_index[start_page_id]
        target_idx = self.page_id_to_index[target_page_id]
        
        if start_idx == target_idx:
            stats['success'] = True
            stats['path_length'] = 1
            return [start_page_id], stats
        
        # Initialize
        state = NavigationState(
            current_idx=start_idx,
            target_idx=target_idx,
            path=[start_page_id],
            visited={start_idx},
            tabu_list=set(),
            depth=0,
            score=0.0
        )
        
        # Search
        while state.depth < self.max_depth:
            neighbors = self.get_neighbors(state.current_idx)
            
            if target_idx in neighbors:
                final_path = state.path + [target_page_id]
                stats['success'] = True
                stats['path_length'] = len(final_path)
                stats['nodes_visited'] = len(state.visited)
                stats['tabu_list_size'] = len(state.tabu_list)
                return final_path, stats
            
            available = [n for n in neighbors if n not in state.visited and n not in state.tabu_list]
            
            if not available:
                stats['dead_ends_encountered'] += 1
                state.tabu_list.add(state.current_idx)
                
                if len(state.tabu_list) > self.tabu_size:
                    state.tabu_list.pop()
                
                if stats['backtracks'] >= self.backtrack_limit:
                    break
                
                backtrack_point = self.find_backtrack_point(state.path, state.visited, state.tabu_list)
                if backtrack_point is None:
                    break
                
                stats['backtracks'] += 1
                state.path = state.path[:backtrack_point + 1]
                state.current_idx = self.page_id_to_index[state.path[-1]]
                state.depth = len(state.path) - 1
                continue
            
            # Score and choose best
            scored = [(n, self.hybrid_scorer.score_candidate(state.current_idx, target_idx, n, state.depth)) for n in available]
            scored.sort(key=lambda x: x[1])
            best_idx, _ = scored[0]
            
            state.current_idx = best_idx
            state.path.append(self.index_to_page_id[best_idx])
            state.visited.add(best_idx)
            state.depth += 1
        
        stats['nodes_visited'] = len(state.visited)
        stats['tabu_list_size'] = len(state.tabu_list)
        return None, stats


def load_advanced_navigator(
    graph_dir: Path,
    model_path: Path,
    embeddings_dir: Path,
    max_depth: int = 20,
    tabu_size: int = 100,
    backtrack_limit: int = 5,
    **scorer_kwargs
) -> AdvancedNavigator:
    """Load advanced navigator with all components."""
    # Load adjacency matrix
    matrix_file = graph_dir / "adjacency_matrix.npz"
    adjacency_matrix = load_npz(matrix_file)
    
    # Load page mappings
    mappings_file = graph_dir / "page_mappings.pkl"
    with open(mappings_file, 'rb') as f:
        page_mappings = pickle.load(f)
    
    # Load hybrid scorer
    from core.hybrid_scorer import load_hybrid_scorer
    hybrid_scorer = load_hybrid_scorer(
        model_path=model_path,
        embeddings_dir=embeddings_dir,
        graph_dir=graph_dir,
        **scorer_kwargs
    )
    
    # Create navigator
    navigator = AdvancedNavigator(
        adjacency_matrix=adjacency_matrix,
        page_mappings=page_mappings,
        hybrid_scorer=hybrid_scorer,
        max_depth=max_depth,
        tabu_size=tabu_size,
        backtrack_limit=backtrack_limit
    )
    
    return navigator


if __name__ == "__main__":
    print("Testing Advanced Navigator...")
    
    graph_dir = Path("data/graph")
    model_path = Path("models/checkpoints/mlp_scorer_best.pt")
    embeddings_dir = Path("data/embeddings")
    
    if all(p.exists() for p in [graph_dir, model_path, embeddings_dir]):
        navigator = load_advanced_navigator(
            graph_dir=graph_dir,
            model_path=model_path,
            embeddings_dir=embeddings_dir
        )
        print(f"✓ Advanced navigator loaded")
        print(f"✓ Max depth: {navigator.max_depth}")
        print(f"✓ Tabu size: {navigator.tabu_size}")
        print(f"✓ Backtrack limit: {navigator.backtrack_limit}")
    else:
        print("✗ Required files not found")