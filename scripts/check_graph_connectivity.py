#!/usr/bin/env python3
"""
Graph Connectivity Checker
Diagnoses why training data generation is failing.
"""

import sys
from pathlib import Path
import numpy as np
from scipy.sparse import load_npz
import pickle
from collections import deque
from typing import Set

def bfs_reachable(adjacency_matrix, start_idx: int, max_depth: int = 10) -> Set[int]:
    """Find all reachable nodes from start using BFS."""
    visited: Set[int] = {start_idx}
    queue = deque([(start_idx, 0)])
    
    while queue:
        current_idx, depth = queue.popleft()
        if depth >= max_depth:
            continue
        
        neighbors = adjacency_matrix[current_idx].indices
        for neighbor_idx in neighbors:
            if neighbor_idx not in visited:
                visited.add(neighbor_idx)
                queue.append((neighbor_idx, depth + 1))
    
    return visited

def main():
    """Check graph connectivity."""
    graph_dir = Path("data/graph")
    
    if not graph_dir.exists():
        print("✗ Error: Graph directory not found!")
        print("Please run build_adjacency_map.py first.")
        return 1
    
    print("=" * 80)
    print("Graph Connectivity Diagnostic")
    print("=" * 80)
    
    # Load adjacency matrix
    matrix_file = graph_dir / "adjacency_matrix.npz"
    if not matrix_file.exists():
        print(f"✗ Error: {matrix_file} not found!")
        return 1
    
    print(f"\nLoading adjacency matrix from {matrix_file}...")
    adjacency_matrix = load_npz(matrix_file)
    n_pages = adjacency_matrix.shape[0]
    n_edges = adjacency_matrix.nnz
    
    print(f"✓ Loaded: {n_pages:,} pages, {n_edges:,} edges")
    
    # Critical validation
    if n_edges == 0:
        print("\n❌ CRITICAL ERROR: Graph has 0 edges!")
        print("\nThis means:")
        print("  1. Parse process did not extract any links")
        print("  2. Links.json is empty or corrupted")
        print("  3. Adjacency matrix build failed")
        print("\nRecommended actions:")
        print("  1. Check data/cleaned/links.json file size")
        print("  2. Check data/cleaned/statistics.json for total_links")
        print("  3. Re-run parse_wikipedia_dumps.py")
        print("  4. Re-run build_adjacency_map.py")
        return 1
    
    if n_edges < 1000:
        print(f"\n⚠️  WARNING: Very few edges ({n_edges:,}) in graph!")
        print("This is unusually low for Wikipedia.")
    
    print(f"✓ Average out-degree: {n_edges / n_pages:.2f}")
    
    # Load page mappings
    mappings_file = graph_dir / "page_mappings.pkl"
    with open(mappings_file, 'rb') as f:
        mappings = pickle.load(f)
    
    pages = mappings['pages']
    print(f"✓ Loaded {len(pages):,} page mappings")
    
    # Check connectivity
    print(f"\n{'='*80}")
    print("Connectivity Analysis")
    print(f"{'='*80}")
    
    # Check out-degrees
    out_degrees = np.array(adjacency_matrix.sum(axis=1)).flatten()
    zero_out_degree = np.sum(out_degrees == 0)
    print(f"\nPages with 0 outgoing links: {zero_out_degree:,} ({100*zero_out_degree/n_pages:.2f}%)")
    print(f"Pages with 1+ outgoing links: {n_pages - zero_out_degree:,} ({100*(n_pages-zero_out_degree)/n_pages:.2f}%)")
    
    # Check in-degrees
    in_degrees = np.array(adjacency_matrix.sum(axis=0)).flatten()
    zero_in_degree = np.sum(in_degrees == 0)
    print(f"Pages with 0 incoming links: {zero_in_degree:,} ({100*zero_in_degree/n_pages:.2f}%)")
    print(f"Pages with 1+ incoming links: {n_pages - zero_in_degree:,} ({100*(n_pages-zero_in_degree)/n_pages:.2f}%)")
    
    # Test reachability from random pages
    print(f"\n{'='*80}")
    print("Reachability Test")
    print(f"{'='*80}")
    
    test_pages = []
    for _ in range(10):
        idx = np.random.randint(0, n_pages)
        if out_degrees[idx] > 0:  # Only test pages with outgoing links
            test_pages.append(idx)
    
    if len(test_pages) == 0:
        print("⚠️  WARNING: No pages with outgoing links found!")
        print("This explains why no paths can be found.")
        return 1
    
    total_reachable = 0
    for start_idx in test_pages[:5]:
        reachable = bfs_reachable(adjacency_matrix, start_idx, max_depth=20)
        total_reachable += len(reachable)
        page_id = mappings['index_to_page_id'][start_idx]
        page_title = pages[page_id]
        print(f"From '{page_title[:50]}...': {len(reachable):,} reachable pages")
    
    avg_reachable = total_reachable / min(5, len(test_pages))
    reachability_percent = (avg_reachable / n_pages) * 100
    
    print(f"\nAverage reachability: {avg_reachable:,.0f} pages ({reachability_percent:.2f}% of graph)")
    
    # Diagnosis
    print(f"\n{'='*80}")
    print("Diagnosis")
    print(f"{'='*80}")
    
    if reachability_percent < 0.1:
        print("❌ CRITICAL: Graph is severely fragmented!")
        print("\nPossible causes:")
        print("  1. Parse process missed most links")
        print("  2. Links are stored incorrectly")
        print("  3. Page ID mappings are wrong")
        print("\nRecommended actions:")
        print("  1. Re-run parse_wikipedia_dumps.py")
        print("  2. Check if links.json contains valid data")
        print("  3. Verify page mappings are correct")
        return 1
    elif reachability_percent < 10:
        print("⚠️  WARNING: Graph connectivity is low")
        print("This will make training data generation very slow.")
        print("Consider re-parsing Wikipedia dumps.")
        return 0
    else:
        print("✓ Graph connectivity looks reasonable")
        print("Training data generation should work.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
