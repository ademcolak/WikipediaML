#!/usr/bin/env python3
"""
Synthetic Training Data Generator
Generates training data by running BFS on random page pairs
to find actual shortest path distances in the Wikipedia graph.
"""

import json
import pickle
import numpy as np
from pathlib import Path
from scipy.sparse import csr_matrix, load_npz
from collections import deque
from typing import Dict, List, Tuple, Set
from tqdm import tqdm
import sys

class TrainingDataGenerator:
    """Generates synthetic training data using BFS."""
    
    def __init__(self, graph_dir: Path, embeddings_dir: Path):
        """
        Initialize the generator.
        
        Args:
            graph_dir: Directory containing graph data
            embeddings_dir: Directory containing embeddings
        """
        self.graph_dir = graph_dir
        self.embeddings_dir = embeddings_dir
        self.adjacency_matrix: csr_matrix | None = None
        self.embeddings: np.ndarray | None = None
        self.pages: Dict[int, str] = {}
        self.page_id_to_index: Dict[int, int] = {}
        self.index_to_page_id: Dict[int, int] = {}
        
    def load_data(self) -> None:
        """Load graph and embedding data."""
        print(f"\n{'='*80}")
        print("Loading graph and embedding data...")
        print(f"{'='*80}")
        
        # Load adjacency matrix
        matrix_file = self.graph_dir / "adjacency_matrix.npz"
        if not matrix_file.exists():
            raise FileNotFoundError(f"Adjacency matrix not found: {matrix_file}")
        
        self.adjacency_matrix = load_npz(matrix_file)
        n_pages, n_edges = self.adjacency_matrix.shape[0], self.adjacency_matrix.nnz
        
        print(f"✓ Loaded adjacency matrix: {self.adjacency_matrix.shape}")
        print(f"✓ Total edges: {n_edges:,}")
        
        # Critical validation
        if n_edges == 0:
            raise ValueError("Adjacency matrix has 0 edges! Cannot generate training data.")
        
        if n_edges < 1000:
            raise ValueError(f"Too few edges ({n_edges:,}) in graph. Parse likely failed!")
        
        avg_out_degree = n_edges / n_pages if n_pages > 0 else 0
        print(f"✓ Average out-degree: {avg_out_degree:.2f}")
        
        if avg_out_degree < 0.1:
            print("⚠️  WARNING: Very low average out-degree. Training data generation will be slow.")
        
        # Load page mappings
        mappings_file = self.graph_dir / "page_mappings.pkl"
        with open(mappings_file, 'rb') as f:
            mappings = pickle.load(f)
            self.pages = mappings['pages']
            self.page_id_to_index = mappings['page_id_to_index']
            self.index_to_page_id = mappings['index_to_page_id']
        print(f"✓ Loaded {len(self.pages):,} page mappings")
        
        # Load embeddings
        embeddings_file = self.embeddings_dir / "embeddings.npy"
        self.embeddings = np.load(embeddings_file)
        print(f"✓ Loaded embeddings: {self.embeddings.shape}")  # type: ignore
    
    def bfs_shortest_path(self, start_idx: int, target_idx: int, max_depth: int = 10) -> int:
        """
        Find shortest path distance using BFS.
        
        Args:
            start_idx: Starting page index
            target_idx: Target page index
            max_depth: Maximum search depth
            
        Returns:
            Shortest path distance, or -1 if not found within max_depth
        """
        if start_idx == target_idx:
            return 0
        
        visited: Set[int] = {start_idx}
        queue: deque = deque([(start_idx, 0)])
        
        while queue:
            current_idx, depth = queue.popleft()
            
            if depth >= max_depth:
                return -1
            
            # Get neighbors (outgoing links)
            neighbors = self.adjacency_matrix[current_idx].indices  # type: ignore
            
            for neighbor_idx in neighbors:
                if neighbor_idx == target_idx:
                    return depth + 1
                
                if neighbor_idx not in visited:
                    visited.add(neighbor_idx)
                    queue.append((neighbor_idx, depth + 1))
        
        return -1  # No path found
    
    def get_high_degree_pages(self, top_k: int = 1000) -> List[int]:
        """Get pages with highest out-degree (hub pages)."""
        out_degrees = np.array(self.adjacency_matrix.sum(axis=1)).flatten()
        top_indices = np.argsort(out_degrees)[-top_k:][::-1]
        return top_indices.tolist()
    
    def test_graph_connectivity(self, n_tests: int = 100) -> Dict:
        """Test if graph has sufficient connectivity."""
        print(f"\n{'='*80}")
        print("Testing graph connectivity...")
        print(f"{'='*80}")
        
        n_pages = len(self.pages)
        successful_paths = 0
        total_tests = 0
        
        # Test with random pages
        for _ in range(n_tests):
            start_idx = np.random.randint(0, n_pages)
            target_idx = np.random.randint(0, n_pages)
            
            if start_idx == target_idx:
                continue
            
            total_tests += 1
            distance = self.bfs_shortest_path(start_idx, target_idx, max_depth=20)
            if distance > 0:
                successful_paths += 1
        
        success_rate = (successful_paths / total_tests * 100) if total_tests > 0 else 0
        print(f"✓ Random sampling: {successful_paths}/{total_tests} paths found ({success_rate:.2f}%)")
        
        # Test with hub pages
        hub_pages = self.get_high_degree_pages(top_k=100)
        hub_successful = 0
        hub_tests = 0
        
        for _ in range(min(n_tests, len(hub_pages))):
            start_idx = np.random.choice(hub_pages)
            target_idx = np.random.randint(0, n_pages)
            
            if start_idx == target_idx:
                continue
            
            hub_tests += 1
            distance = self.bfs_shortest_path(start_idx, target_idx, max_depth=20)
            if distance > 0:
                hub_successful += 1
        
        hub_success_rate = (hub_successful / hub_tests * 100) if hub_tests > 0 else 0
        print(f"✓ Hub-based sampling: {hub_successful}/{hub_tests} paths found ({hub_success_rate:.2f}%)")
        
        return {
            'random_success_rate': success_rate,
            'hub_success_rate': hub_success_rate,
            'use_hub_sampling': hub_success_rate > success_rate * 1.5
        }
    
    def generate_training_samples(
        self,
        n_samples: int = 100_000,
        max_depth: int = 20,
        min_distance: int = 1,
        max_distance: int = 15
    ) -> List[Dict]:
        """
        Generate training samples using smart sampling strategy.
        
        Args:
            n_samples: Number of samples to generate
            max_depth: Maximum BFS search depth
            min_distance: Minimum path distance to include
            max_distance: Maximum path distance to include
            
        Returns:
            List of training samples
        """
        print(f"\n{'='*80}")
        print(f"Generating {n_samples:,} training samples...")
        print(f"{'='*80}")
        
        # Test connectivity first
        connectivity = self.test_graph_connectivity(n_tests=200)
        use_hub_sampling = connectivity['use_hub_sampling']
        
        if connectivity['random_success_rate'] < 0.1 and connectivity['hub_success_rate'] < 0.1:
            print("\n⚠️  WARNING: Graph connectivity is very low!")
            print("This may indicate:")
            print("  1. Graph is fragmented (multiple disconnected components)")
            print("  2. Links are mostly unidirectional")
            print("  3. Parse process may have missed many links")
            print("\nTrying with relaxed parameters...")
            min_distance = 1
            max_distance = 30  # Allow much longer paths
        
        n_pages = len(self.pages)
        samples = []
        attempts = 0
        max_attempts = n_samples * 20  # Much more attempts
        
        # Get hub pages if using hub sampling
        hub_pages = self.get_high_degree_pages(top_k=5000) if use_hub_sampling else []
        
        print(f"\nUsing {'hub-based' if use_hub_sampling else 'random'} sampling strategy...")
        
        with tqdm(total=n_samples, desc="Generating samples") as pbar:
            while len(samples) < n_samples and attempts < max_attempts:
                attempts += 1
                
                # Smart sampling: prefer hub pages for start
                if use_hub_sampling and len(hub_pages) > 0 and np.random.random() < 0.7:
                    start_idx = np.random.choice(hub_pages)
                else:
                    start_idx = np.random.randint(0, n_pages)
                
                target_idx = np.random.randint(0, n_pages)
                
                # Skip if same page
                if start_idx == target_idx:
                    continue
                
                # Find shortest path distance
                distance = self.bfs_shortest_path(start_idx, target_idx, max_depth)
                
                # Skip if no path found or distance out of range
                if distance < min_distance or distance > max_distance:
                    continue
                
                # Get page IDs and titles
                start_page_id = self.index_to_page_id[start_idx]
                target_page_id = self.index_to_page_id[target_idx]
                
                # Create sample
                sample = {
                    'start_idx': int(start_idx),
                    'target_idx': int(target_idx),
                    'start_page_id': int(start_page_id),
                    'target_page_id': int(target_page_id),
                    'start_title': self.pages[start_page_id],
                    'target_title': self.pages[target_page_id],
                    'distance': int(distance)
                }
                
                samples.append(sample)
                pbar.update(1)
        
        success_rate = (len(samples) / attempts * 100) if attempts > 0 else 0
        print(f"\n✓ Generated {len(samples):,} samples in {attempts:,} attempts")
        print(f"✓ Success rate: {success_rate:.2f}%")
        
        if len(samples) == 0:
            print("\n⚠️  CRITICAL: No samples generated!")
            print("Graph may be too fragmented. Consider:")
            print("  1. Re-parsing Wikipedia dumps")
            print("  2. Using a smaller subset of pages")
            print("  3. Checking if links are being parsed correctly")
        
        return samples
    
    def generate_candidate_samples(
        self,
        samples: List[Dict],
        n_candidates_per_sample: int = 10
    ) -> List[Dict]:
        """
        For each sample, generate candidate links with their distances to target.
        
        Args:
            samples: List of start-target samples
            n_candidates_per_sample: Number of candidate links to sample per start page
            
        Returns:
            List of candidate samples with features
        """
        print(f"\n{'='*80}")
        print("Generating candidate link samples...")
        print(f"{'='*80}")
        
        candidate_samples = []
        
        for sample in tqdm(samples, desc="Processing samples"):
            start_idx = sample['start_idx']
            target_idx = sample['target_idx']
            
            # Get all outgoing links from start page
            neighbors = self.adjacency_matrix[start_idx].indices  # type: ignore
            
            if len(neighbors) == 0:
                continue
            
            # Sample candidates (or use all if fewer than requested)
            n_to_sample = min(n_candidates_per_sample, len(neighbors))
            candidate_indices = np.random.choice(neighbors, n_to_sample, replace=False)
            
            for candidate_idx in candidate_indices:
                # Calculate distance from candidate to target
                distance_to_target = self.bfs_shortest_path(candidate_idx, target_idx, max_depth=20)
                
                if distance_to_target < 0:
                    continue  # Skip if no path found
                
                candidate_page_id = self.index_to_page_id[candidate_idx]
                
                # Create candidate sample with features
                candidate_sample = {
                    'start_idx': int(start_idx),
                    'target_idx': int(target_idx),
                    'candidate_idx': int(candidate_idx),
                    'start_page_id': int(sample['start_page_id']),
                    'target_page_id': int(sample['target_page_id']),
                    'candidate_page_id': int(candidate_page_id),
                    'start_title': sample['start_title'],
                    'target_title': sample['target_title'],
                    'candidate_title': self.pages[candidate_page_id],
                    'distance_to_target': int(distance_to_target),
                    'start_embedding': self.embeddings[start_idx].tolist(),  # type: ignore
                    'target_embedding': self.embeddings[target_idx].tolist(),  # type: ignore
                    'candidate_embedding': self.embeddings[candidate_idx].tolist()  # type: ignore
                }
                
                candidate_samples.append(candidate_sample)
        
        print(f"✓ Generated {len(candidate_samples):,} candidate samples")
        
        return candidate_samples
    
    def analyze_dataset(self, samples: List[Dict]) -> Dict:
        """
        Analyze the generated dataset.
        
        Args:
            samples: List of samples
            
        Returns:
            Dictionary of statistics
        """
        print(f"\n{'='*80}")
        print("Analyzing dataset...")
        print(f"{'='*80}")
        
        distances = [s['distance_to_target'] for s in samples]
        
        # Check if we have any samples
        if len(distances) == 0:
            print("⚠️  Warning: No samples generated!")
            return {
                'total_samples': 0,
                'min_distance': 0,
                'max_distance': 0,
                'mean_distance': 0.0,
                'median_distance': 0.0,
                'distance_distribution': {}
            }
        
        stats = {
            'total_samples': len(samples),
            'min_distance': int(np.min(distances)),
            'max_distance': int(np.max(distances)),
            'mean_distance': float(np.mean(distances)),
            'median_distance': float(np.median(distances)),
            'distance_distribution': {
                str(d): int(np.sum(np.array(distances) == d))
                for d in range(int(np.min(distances)), int(np.max(distances)) + 1)
            }
        }
        
        print(f"✓ Total samples: {stats['total_samples']:,}")
        print(f"✓ Distance range: {stats['min_distance']} - {stats['max_distance']}")
        print(f"✓ Mean distance: {stats['mean_distance']:.2f}")
        print(f"✓ Median distance: {stats['median_distance']:.1f}")
        
        print("\nDistance distribution:")
        for distance, count in sorted(stats['distance_distribution'].items(), key=lambda x: int(x[0])):
            percentage = 100 * count / stats['total_samples']
            print(f"  Distance {distance}: {count:,} samples ({percentage:.1f}%)")
        
        return stats
    
    def save_dataset(self, samples: List[Dict], stats: Dict, output_dir: Path) -> None:
        """
        Save training dataset.
        
        Args:
            samples: List of samples
            stats: Dataset statistics
            output_dir: Directory to save files
        """
        print(f"\n{'='*80}")
        print("Saving training dataset...")
        print(f"{'='*80}")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save samples
        samples_file = output_dir / "training_samples.json"
        with open(samples_file, 'w', encoding='utf-8') as f:
            json.dump(samples, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved {len(samples):,} samples to {samples_file}")
        
        # Save statistics
        stats_file = output_dir / "dataset_statistics.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
        print(f"✓ Saved statistics to {stats_file}")
        
        print(f"\n{'='*80}")
        print("Training Data Generation Complete!")
        print(f"{'='*80}")

def main():
    """Main generation function."""
    graph_dir = Path("data/graph")
    embeddings_dir = Path("data/embeddings")
    output_dir = Path("data/training")
    
    # Check if output already exists (auto-skip)
    samples_file = output_dir / "training_samples.json"
    stats_file = output_dir / "dataset_statistics.json"
    if samples_file.exists() and stats_file.exists():
        print(f"⊘ Training data already exists in {output_dir}")
        print("  Skipping generation step. Delete output files to re-run.")
        return 0
    
    # Check if required data exists
    if not graph_dir.exists():
        print(f"✗ Error: {graph_dir} not found!")
        print("Please run build_adjacency_map.py first.")
        return 1
    
    if not embeddings_dir.exists():
        print(f"✗ Error: {embeddings_dir} not found!")
        print("Please run build_embedding_index.py first.")
        return 1
    
    try:
        generator = TrainingDataGenerator(graph_dir, embeddings_dir)
        generator.load_data()
        
        # Generate start-target pairs
        # Parameters are auto-adjusted based on graph connectivity
        samples = generator.generate_training_samples(
            n_samples=100_000  # Will use smart sampling strategy
        )
        
        # Generate candidate samples with features
        candidate_samples = generator.generate_candidate_samples(
            samples,
            n_candidates_per_sample=10
        )
        
        # Check if we actually generated any samples
        if len(candidate_samples) == 0:
            print("\n✗ ERROR: No training samples generated!")
            print("Possible reasons:")
            print("  1. Graph has insufficient connections")
            print("  2. BFS cannot find paths between pages")
            print("  3. Embeddings not loaded correctly")
            print("\nPlease check:")
            print("  - Graph connectivity: python3 scripts/build_adjacency_map.py")
            print("  - Embeddings: python3 scripts/build_embedding_index.py")
            return 1
        
        # Analyze and save
        stats = generator.analyze_dataset(candidate_samples)
        generator.save_dataset(candidate_samples, stats, output_dir)
        
        print("\n✓ Training data generated successfully!")
        print("\nNext steps:")
        print("1. Design MLP scorer model architecture")
        print("2. Train the model on this dataset")
        print("3. Validate on unseen page pairs")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Error during generation: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())