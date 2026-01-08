#!/usr/bin/env python3
"""
Beam Search Navigator for Wikipedia
Implements beam search algorithm with hybrid scoring for efficient navigation.
"""

import heapq
from typing import List, Set, Tuple, Optional, Dict
from dataclasses import dataclass, field
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix, load_npz
import pickle

from core.hybrid_scorer import HybridScorer


@dataclass(order=True)
class SearchNode:
    """Node in the beam search."""
    score: float
    page_idx: int = field(compare=False)
    path: List[int] = field(compare=False, default_factory=list)
    depth: int = field(compare=False, default=0)


class BeamSearchNavigator:
    """
    Beam Search navigator for Wikipedia.
    Maintains top-k paths at each step to balance exploration and efficiency.
    """
    
    def __init__(
        self,
        adjacency_matrix: csr_matrix,
        page_mappings: dict,
        hybrid_scorer: HybridScorer,
        beam_width: int = 10,
        max_depth: int = 20
    ):
        """
        Initialize beam search navigator.
        
        Args:
            adjacency_matrix: Graph adjacency matrix
            page_mappings: Page ID to index mappings
            hybrid_scorer: Hybrid scoring system
            beam_width: Number of paths to maintain (k)
            max_depth: Maximum search depth
        """
        self.adjacency_matrix = adjacency_matrix
        self.pages = page_mappings['pages']
        self.page_id_to_index = page_mappings['page_id_to_index']
        self.index_to_page_id = page_mappings['index_to_page_id']
        self.hybrid_scorer = hybrid_scorer
        self.beam_width = beam_width
        self.max_depth = max_depth
        
    def get_neighbors(self, page_idx: int) -> List[int]:
        """
        Get outgoing links from a page.
        
        Args:
            page_idx: Page index
            
        Returns:
            List of neighbor indices
        """
        if page_idx < 0 or page_idx >= self.adjacency_matrix.shape[0]:  # type: ignore
            return []
        
        neighbors = self.adjacency_matrix[page_idx].indices
        return list(neighbors)
    
    def search(
        self,
        start_page_id: int,
        target_page_id: int,
        verbose: bool = False
    ) -> Optional[List[int]]:
        """
        Perform beam search from start to target.
        
        Args:
            start_page_id: Starting page ID
            target_page_id: Target page ID
            verbose: Print search progress
            
        Returns:
            Path as list of page IDs, or None if not found
        """
        # Convert to indices
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
            print(f"Beam Search: {self.pages[start_page_id]} → {self.pages[target_page_id]}")
            print(f"Beam width: {self.beam_width}, Max depth: {self.max_depth}")
            print(f"{'='*80}")
        
        # Initialize beam with start node
        beam: List[SearchNode] = [
            SearchNode(
                score=0.0,
                page_idx=start_idx,
                path=[start_page_id],
                depth=0
            )
        ]
        
        # Track visited pages globally to avoid cycles
        visited: Set[int] = {start_idx}
        
        # Search
        for depth in range(self.max_depth):
            if verbose:
                print(f"\nDepth {depth + 1}:")
                print(f"  Beam size: {len(beam)}")
            
            # Expand all nodes in current beam
            candidates: List[SearchNode] = []
            
            for node in beam:
                current_idx = node.page_idx
                
                # Get neighbors
                neighbors = self.get_neighbors(current_idx)
                
                if verbose:
                    print(f"  Expanding {self.pages[self.index_to_page_id[current_idx]]}: {len(neighbors)} neighbors")
                
                # Check if target is in neighbors
                if target_idx in neighbors:
                    final_path = node.path + [target_page_id]
                    if verbose:
                        print(f"\n✓ Target found! Path length: {len(final_path)}")
                        print(f"  Path: {' → '.join([self.pages[pid] for pid in final_path])}")
                    return final_path
                
                # Score each neighbor
                for neighbor_idx in neighbors:
                    # Skip if already visited
                    if neighbor_idx in visited:
                        continue
                    
                    # Score this candidate
                    score = self.hybrid_scorer.score_candidate(
                        start_idx=current_idx,
                        target_idx=target_idx,
                        candidate_idx=neighbor_idx,
                        current_depth=depth
                    )
                    
                    # Create new node
                    neighbor_page_id = self.index_to_page_id[neighbor_idx]
                    new_node = SearchNode(
                        score=score,
                        page_idx=neighbor_idx,
                        path=node.path + [neighbor_page_id],
                        depth=depth + 1
                    )
                    
                    candidates.append(new_node)
            
            if not candidates:
                if verbose:
                    print(f"\n✗ No more candidates to explore")
                return None
            
            # Select top-k candidates for next beam
            candidates.sort(key=lambda x: x.score)
            beam = candidates[:self.beam_width]
            
            # Update visited set
            for node in beam:
                visited.add(node.page_idx)
            
            if verbose:
                print(f"  Top candidate: {self.pages[self.index_to_page_id[beam[0].page_idx]]} (score: {beam[0].score:.4f})")
        
        if verbose:
            print(f"\n✗ Target not found within {self.max_depth} steps")
        
        return None
    
    def search_with_stats(
        self,
        start_page_id: int,
        target_page_id: int,
        verbose: bool = False
    ) -> Tuple[Optional[List[int]], Dict]:
        """
        Perform beam search and return statistics.
        
        Args:
            start_page_id: Starting page ID
            target_page_id: Target page ID
            verbose: Print search progress
            
        Returns:
            Tuple of (path, statistics)
        """
        stats = {
            'nodes_expanded': 0,
            'nodes_visited': 0,
            'max_beam_size': 0,
            'success': False,
            'path_length': 0
        }
        
        # Convert to indices
        if start_page_id not in self.page_id_to_index or target_page_id not in self.page_id_to_index:
            return None, stats
        
        start_idx = self.page_id_to_index[start_page_id]
        target_idx = self.page_id_to_index[target_page_id]
        
        if start_idx == target_idx:
            stats['success'] = True
            stats['path_length'] = 1
            return [start_page_id], stats
        
        # Initialize
        beam = [SearchNode(score=0.0, page_idx=start_idx, path=[start_page_id], depth=0)]
        visited = {start_idx}
        
        # Search
        for depth in range(self.max_depth):
            candidates = []
            
            for node in beam:
                stats['nodes_expanded'] += 1
                current_idx = node.page_idx
                neighbors = self.get_neighbors(current_idx)
                
                # Check for target
                if target_idx in neighbors:
                    final_path = node.path + [target_page_id]
                    stats['success'] = True
                    stats['path_length'] = len(final_path)
                    return final_path, stats
                
                # Score neighbors
                for neighbor_idx in neighbors:
                    if neighbor_idx in visited:
                        continue
                    
                    score = self.hybrid_scorer.score_candidate(
                        current_idx, target_idx, neighbor_idx, depth
                    )
                    
                    neighbor_page_id = self.index_to_page_id[neighbor_idx]
                    candidates.append(SearchNode(
                        score=score,
                        page_idx=neighbor_idx,
                        path=node.path + [neighbor_page_id],
                        depth=depth + 1
                    ))
            
            if not candidates:
                return None, stats
            
            # Select top-k
            candidates.sort(key=lambda x: x.score)
            beam = candidates[:self.beam_width]
            stats['max_beam_size'] = max(stats['max_beam_size'], len(beam))
            
            # Update visited
            for node in beam:
                visited.add(node.page_idx)
            
            stats['nodes_visited'] = len(visited)
        
        return None, stats


def load_beam_search_navigator(
    graph_dir: Path,
    model_path: Path,
    embeddings_dir: Path,
    beam_width: int = 10,
    max_depth: int = 20,
    **scorer_kwargs
) -> BeamSearchNavigator:
    """
    Load beam search navigator with all required components.
    
    Args:
        graph_dir: Directory containing graph data
        model_path: Path to trained MLP model
        embeddings_dir: Directory containing embeddings
        beam_width: Beam width for search
        max_depth: Maximum search depth
        **scorer_kwargs: Additional arguments for HybridScorer
        
    Returns:
        Initialized BeamSearchNavigator
    """
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
    navigator = BeamSearchNavigator(
        adjacency_matrix=adjacency_matrix,
        page_mappings=page_mappings,
        hybrid_scorer=hybrid_scorer,
        beam_width=beam_width,
        max_depth=max_depth
    )
    
    return navigator


if __name__ == "__main__":
    # Test beam search
    print("Testing Beam Search Navigator...")
    
    graph_dir = Path("data/graph")
    model_path = Path("models/checkpoints/mlp_scorer_best.pt")
    embeddings_dir = Path("data/embeddings")
    
    if all(p.exists() for p in [graph_dir, model_path, embeddings_dir]):
        navigator = load_beam_search_navigator(
            graph_dir=graph_dir,
            model_path=model_path,
            embeddings_dir=embeddings_dir,
            beam_width=10,
            max_depth=15
        )
        
        print(f"✓ Beam search navigator loaded")
        print(f"✓ Graph size: {navigator.adjacency_matrix.shape[0]:,} pages")  # type: ignore
        print(f"✓ Beam width: {navigator.beam_width}")
        print(f"✓ Max depth: {navigator.max_depth}")
    else:
        print("✗ Required files not found. Run full pipeline first.")