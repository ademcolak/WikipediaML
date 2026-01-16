#!/usr/bin/env python3
"""
Binary Adjacency Map Builder
Builds a memory-efficient Compressed Sparse Row (CSR) format graph
from the cleaned Wikipedia link data.
"""

import json
import numpy as np
import pickle
from pathlib import Path
from scipy.sparse import csr_matrix
from typing import Dict, List, Set
import sys

class AdjacencyMapBuilder:
    """Builds CSR format adjacency map for Wikipedia graph."""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.pages: Dict[int, str] = {}
        self.links: Dict[int, Set[int]] = {}
        self.page_id_to_index: Dict[int, int] = {}
        self.index_to_page_id: Dict[int, int] = {}
        
    def load_cleaned_data(self) -> None:
        """Load cleaned data from JSON files."""
        print(f"\n{'='*80}")
        print("Loading cleaned data...")
        print(f"{'='*80}")
        
        # Load pages
        pages_file = self.data_dir / "pages.json"
        if not pages_file.exists():
            raise FileNotFoundError(f"Pages file not found: {pages_file}")
        
        with open(pages_file, 'r', encoding='utf-8') as f:
            # Convert string keys back to integers
            self.pages = {int(k): v for k, v in json.load(f).items()}
        
        if len(self.pages) == 0:
            raise ValueError("Pages file is empty!")
        
        print(f"✓ Loaded {len(self.pages):,} pages")
        
        # Load links
        links_file = self.data_dir / "links.json"
        if not links_file.exists():
            raise FileNotFoundError(f"Links file not found: {links_file}")
        
        file_size = links_file.stat().st_size
        if file_size < 1000:
            raise ValueError(f"Links file is suspiciously small ({file_size} bytes). Parse may have failed!")
        
        with open(links_file, 'r', encoding='utf-8') as f:
            links_data = json.load(f)
            self.links = {
                int(k): set(v) for k, v in links_data.items()
            }
        
        if len(self.links) == 0:
            raise ValueError("Links file is empty! Parse may have failed.")
        
        total_links = sum(len(to_ids) for to_ids in self.links.values())
        if total_links == 0:
            raise ValueError("Total links count is 0! Cannot build graph.")
        
        print(f"✓ Loaded {len(self.links):,} link entries")
        print(f"✓ Total links: {total_links:,}")
        print(f"✓ Links file size: {file_size / (1024*1024):.2f} MB")
        
        # Create bidirectional mapping between page IDs and matrix indices
        sorted_page_ids = sorted(self.pages.keys())
        self.page_id_to_index = {pid: idx for idx, pid in enumerate(sorted_page_ids)}
        self.index_to_page_id = {idx: pid for pid, idx in self.page_id_to_index.items()}
        print(f"✓ Created index mappings for {len(sorted_page_ids):,} pages")
    
    def build_csr_matrix(self) -> csr_matrix:
        """
        Build CSR (Compressed Sparse Row) adjacency matrix.
        
        Returns:
            Sparse adjacency matrix in CSR format
        """
        print(f"\n{'='*80}")
        print("Building CSR adjacency matrix...")
        print(f"{'='*80}")
        
        n_pages = len(self.pages)
        
        # Prepare data for CSR matrix construction
        row_indices = []
        col_indices = []
        
        total_links = 0
        for from_id, to_ids in self.links.items():
            if from_id not in self.page_id_to_index:
                continue
                
            from_idx = self.page_id_to_index[from_id]
            
            for to_id in to_ids:
                if to_id not in self.page_id_to_index:
                    continue
                    
                to_idx = self.page_id_to_index[to_id]
                row_indices.append(from_idx)
                col_indices.append(to_idx)
                total_links += 1
        
        # Validation before building matrix
        if total_links == 0:
            raise ValueError("No links to build adjacency matrix! Graph will be empty.")
        
        if len(row_indices) == 0:
            raise ValueError("No edges found after processing links! Check page ID mappings.")
        
        # Create sparse matrix (values are all 1s for unweighted graph)
        data = np.ones(len(row_indices), dtype=np.int8)
        adjacency_matrix = csr_matrix(
            (data, (row_indices, col_indices)),
            shape=(n_pages, n_pages),
            dtype=np.int8
        )
        
        # Verify matrix was built correctly
        actual_edges = adjacency_matrix.nnz
        if actual_edges == 0:
            raise ValueError("Adjacency matrix has 0 edges! Build failed.")
        
        if actual_edges != total_links:
            print(f"⚠️  WARNING: Expected {total_links:,} edges but matrix has {actual_edges:,}")
        
        print(f"✓ Built CSR matrix: {n_pages:,} × {n_pages:,}")
        print(f"✓ Total edges: {actual_edges:,}")
        print(f"✓ Sparsity: {100 * (1 - actual_edges / (n_pages * n_pages)):.6f}%")
        
        # Calculate memory usage
        memory_mb = (
            adjacency_matrix.data.nbytes +
            adjacency_matrix.indices.nbytes +
            adjacency_matrix.indptr.nbytes
        ) / (1024 * 1024)
        print(f"✓ Memory usage: {memory_mb:.2f} MB")
        
        # Final validation
        if actual_edges < 1000:
            raise ValueError(f"Too few edges in graph ({actual_edges:,}). Graph build likely failed!")
        
        return adjacency_matrix
    
    def calculate_statistics(self, adjacency_matrix: csr_matrix) -> dict:
        """
        Calculate graph statistics.
        
        Args:
            adjacency_matrix: The CSR adjacency matrix
            
        Returns:
            Dictionary of statistics
        """
        print(f"\n{'='*80}")
        print("Calculating graph statistics...")
        print(f"{'='*80}")
        
        n_pages = adjacency_matrix.shape[0]  # type: ignore
        
        # Out-degree (number of outgoing links per page)
        out_degrees = np.array(adjacency_matrix.sum(axis=1)).flatten()
        
        # In-degree (number of incoming links per page)
        in_degrees = np.array(adjacency_matrix.sum(axis=0)).flatten()
        
        stats = {
            "total_pages": n_pages,
            "total_edges": int(adjacency_matrix.nnz),
            "avg_out_degree": float(np.mean(out_degrees)),
            "max_out_degree": int(np.max(out_degrees)),
            "min_out_degree": int(np.min(out_degrees)),
            "avg_in_degree": float(np.mean(in_degrees)),
            "max_in_degree": int(np.max(in_degrees)),
            "min_in_degree": int(np.min(in_degrees)),
            "sparsity": float(1 - adjacency_matrix.nnz / (n_pages * n_pages))
        }
        
        # Find hub pages (highest in-degree)
        top_hubs_indices = np.argsort(in_degrees)[-10:][::-1]
        stats["top_10_hubs"] = [
            {
                "page_id": int(self.index_to_page_id[idx]),
                "title": self.pages[self.index_to_page_id[idx]],
                "in_degree": int(in_degrees[idx])
            }
            for idx in top_hubs_indices
        ]
        
        print(f"✓ Total pages: {stats['total_pages']:,}")
        print(f"✓ Total edges: {stats['total_edges']:,}")
        print(f"✓ Average out-degree: {stats['avg_out_degree']:.2f}")
        print(f"✓ Average in-degree: {stats['avg_in_degree']:.2f}")
        print(f"✓ Max in-degree: {stats['max_in_degree']:,}")
        
        print(f"\nTop 10 Hub Pages (by in-degree):")
        for i, hub in enumerate(stats["top_10_hubs"], 1):
            print(f"  {i}. {hub['title']} ({hub['in_degree']:,} incoming links)")
        
        return stats
    
    def save_adjacency_map(self, adjacency_matrix: csr_matrix, stats: dict, output_dir: Path) -> None:
        """
        Save adjacency map and metadata.
        
        Args:
            adjacency_matrix: The CSR adjacency matrix
            stats: Graph statistics
            output_dir: Directory to save files
        """
        print(f"\n{'='*80}")
        print("Saving adjacency map...")
        print(f"{'='*80}")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save CSR matrix
        matrix_file = output_dir / "adjacency_matrix.npz"
        from scipy.sparse import save_npz
        save_npz(matrix_file, adjacency_matrix)
        print(f"✓ Saved adjacency matrix to {matrix_file}")
        
        # Save page mappings
        mappings_file = output_dir / "page_mappings.pkl"
        mappings = {
            "pages": self.pages,
            "page_id_to_index": self.page_id_to_index,
            "index_to_page_id": self.index_to_page_id
        }
        with open(mappings_file, 'wb') as f:
            pickle.dump(mappings, f)
        print(f"✓ Saved page mappings to {mappings_file}")
        
        # Save statistics
        stats_file = output_dir / "graph_statistics.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved statistics to {stats_file}")
        
        print(f"\n{'='*80}")
        print("Adjacency Map Build Complete!")
        print(f"{'='*80}")

def main():
    """Main build function."""
    data_dir = Path("data/cleaned")
    output_dir = Path("data/graph")
    
    # Check if output already exists (auto-skip)
    matrix_file = output_dir / "adjacency_matrix.npz"
    mappings_file = output_dir / "page_mappings.pkl"
    if matrix_file.exists() and mappings_file.exists():
        print(f"⊘ Adjacency map already exists in {output_dir}")
        print("  Skipping build step. Delete output files to re-run.")
        return 0
    
    # Check if cleaned data exists
    if not data_dir.exists():
        print(f"✗ Error: {data_dir} not found!")
        print("Please run parse_wikipedia_dumps.py first.")
        return 1
    
    try:
        builder = AdjacencyMapBuilder(data_dir)
        builder.load_cleaned_data()
        adjacency_matrix = builder.build_csr_matrix()
        stats = builder.calculate_statistics(adjacency_matrix)
        builder.save_adjacency_map(adjacency_matrix, stats, output_dir)
        
        print("\n✓ Binary adjacency map built successfully!")
        print("\nNext steps:")
        print("1. Generate embeddings for all pages")
        print("2. Build FAISS index for similarity search")
        print("3. Start training the MLP scorer model")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Error during build: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())