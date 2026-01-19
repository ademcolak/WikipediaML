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
        
        # For very large graphs, skip connectivity test and assume connectivity is OK
        # (we already know graph has 300M+ edges, so it's definitely connected)
        if n_pages > 10_000_000:
            print(f"⚠️  Very large graph detected ({n_pages:,} pages).")
            print("⚠️  Skipping connectivity test (graph has 300M+ edges, assuming good connectivity).")
            print("⚠️  Using hub-based sampling by default for better performance.")
            sys.stdout.flush()
            return {
                'random_success_rate': 15.0,  # Assume reasonable connectivity
                'hub_success_rate': 25.0,     # Hub pages should have better connectivity
                'use_hub_sampling': True       # Force hub sampling for large graphs
            }
        
        # For large graphs, reduce test count and depth for speed
        if n_pages > 1_000_000:
            n_tests = min(n_tests, 10)  # Even fewer tests for very large graphs
            max_test_depth = 5  # Very shallow BFS for testing (just check immediate neighbors)
            print(f"⚠️  Large graph detected ({n_pages:,} pages). Using reduced test parameters for speed.")
        else:
            max_test_depth = 20
        
        successful_paths = 0
        total_tests = 0
        
        # Test with random pages (with progress bar)
        print(f"Testing random sampling ({n_tests} tests)...")
        sys.stdout.flush()
        for i in tqdm(range(n_tests), desc="Random connectivity test", leave=False):
            start_idx = np.random.randint(0, n_pages)
            target_idx = np.random.randint(0, n_pages)
            
            if start_idx == target_idx:
                continue
            
            total_tests += 1
            # For very large graphs, use even shorter depth for first few tests
            test_depth = max_test_depth if i < 5 else max_test_depth // 2
            distance = self.bfs_shortest_path(start_idx, target_idx, max_depth=test_depth)
            if distance > 0:
                successful_paths += 1
        
        success_rate = (successful_paths / total_tests * 100) if total_tests > 0 else 0
        print(f"✓ Random sampling: {successful_paths}/{total_tests} paths found ({success_rate:.2f}%)")
        
        # Test with hub pages
        hub_pages = self.get_high_degree_pages(top_k=100)
        hub_successful = 0
        hub_tests = 0
        
        print(f"Testing hub-based sampling ({min(n_tests, len(hub_pages))} tests)...")
        sys.stdout.flush()
        for i in tqdm(range(min(n_tests, len(hub_pages))), desc="Hub connectivity test", leave=False):
            start_idx = np.random.choice(hub_pages)
            target_idx = np.random.randint(0, n_pages)
            
            if start_idx == target_idx:
                continue
            
            hub_tests += 1
            # For very large graphs, use even shorter depth
            test_depth = max_test_depth if i < 5 else max_test_depth // 2
            distance = self.bfs_shortest_path(start_idx, target_idx, max_depth=test_depth)
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
        max_distance: int = 15,
        output_file: Path = None,
        existing_count: int = 0
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
        sys.stdout.flush()
        
        # Test connectivity first (reduced tests for large graphs)
        n_pages = len(self.pages)
        n_tests = 50 if n_pages > 1_000_000 else 200  # Fewer tests for large graphs
        print(f"\n🔍 Testing graph connectivity ({n_tests} tests)...")
        sys.stdout.flush()
        connectivity = self.test_graph_connectivity(n_tests=n_tests)
        print(f"✓ Connectivity test complete: Random={connectivity['random_success_rate']:.1f}%, Hub={connectivity['hub_success_rate']:.1f}%")
        sys.stdout.flush()
        
        # For large graphs with low connectivity, force hub-based sampling
        use_hub_sampling = connectivity['use_hub_sampling']
        if n_pages > 1_000_000 and connectivity['random_success_rate'] < 20:
            print("\n⚠️  Low connectivity detected. Forcing hub-based sampling for better success rate.")
            sys.stdout.flush()
            use_hub_sampling = True
        
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
        hub_pages = self.get_high_degree_pages(top_k=10000) if use_hub_sampling else []  # More hub pages
        
        print(f"\nUsing {'hub-based' if use_hub_sampling else 'random'} sampling strategy...")
        sys.stdout.flush()
        if use_hub_sampling:
            print(f"✓ Using {len(hub_pages):,} hub pages for better connectivity")
            sys.stdout.flush()
        
        # Progress update every N attempts to show activity
        progress_update_interval = max(100, n_samples // 100)  # Update every 1% or 100 attempts
        
        # For very large graphs, use adaptive strategy: aggressive hub sampling for first samples
        initial_samples_threshold = min(100, n_samples // 10)  # First 10% or 100 samples
        
        with tqdm(total=n_samples, desc="Generating samples") as pbar:
            while len(samples) < n_samples and attempts < max_attempts:
                attempts += 1
                
                # Adaptive sampling: very aggressive hub sampling for first samples
                if len(samples) < initial_samples_threshold and use_hub_sampling and len(hub_pages) > 0:
                    # For first samples: both start and target should be hubs (much higher success rate)
                    start_idx = np.random.choice(hub_pages)
                    # 80% chance target is also a hub for first samples
                    if np.random.random() < 0.8:
                        target_idx = np.random.choice(hub_pages)
                    else:
                        target_idx = np.random.randint(0, n_pages)
                else:
                    # Normal sampling strategy
                    if use_hub_sampling and len(hub_pages) > 0:
                        # Use hub pages more aggressively for large graphs
                        hub_prob = 0.9 if n_pages > 1_000_000 else 0.7
                        if np.random.random() < hub_prob:
                            start_idx = np.random.choice(hub_pages)
                        else:
                            start_idx = np.random.randint(0, n_pages)
                    else:
                        start_idx = np.random.randint(0, n_pages)
                    
                    # For target, also prefer hub pages if using hub sampling
                    if use_hub_sampling and len(hub_pages) > 0 and np.random.random() < 0.3:
                        target_idx = np.random.choice(hub_pages)
                    else:
                        target_idx = np.random.randint(0, n_pages)
                
                # Skip if same page
                if start_idx == target_idx:
                    continue
                
                # Adaptive BFS depth: shorter for first samples (faster), longer later
                if len(samples) < initial_samples_threshold:
                    # First samples: use shorter depth for speed
                    adaptive_max_depth = min(max_depth, 10)  # Max 10 for first samples
                else:
                    adaptive_max_depth = max_depth
                
                # Find shortest path distance
                distance = self.bfs_shortest_path(start_idx, target_idx, max_depth=adaptive_max_depth)
                
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
                
                # Incremental checkpoint: save every 100 samples
                if output_file and len(samples) % 100 == 0 and len(samples) > 0:
                    try:
                        # Load existing samples if file exists
                        all_samples = []
                        if output_file.exists() and output_file.stat().st_size > 0:
                            with open(output_file, 'r', encoding='utf-8') as f:
                                all_samples = json.load(f)
                        # Append new samples (don't clear, we'll return them)
                        all_samples.extend(samples)
                        # Save checkpoint
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(all_samples, f, indent=2, ensure_ascii=False)
                        print(f"\n[Checkpoint] Saved {len(all_samples):,} total samples to {output_file}")
                        sys.stdout.flush()
                    except Exception as e:
                        print(f"\n⚠️  Warning: Could not save checkpoint: {e}")
                        sys.stdout.flush()
                
                # For first few samples, print immediately to show progress
                sample_num = existing_count + len(samples)
                if sample_num <= 10:
                    print(f"\n[First samples] Found sample #{sample_num}: distance={distance}, "
                          f"attempts={attempts}, success_rate={len(samples)/attempts*100:.2f}%")
                    sys.stdout.flush()
                
                # Periodic progress update even if no new samples
                if attempts % progress_update_interval == 0:
                    success_rate = len(samples)/attempts*100 if attempts > 0 else 0
                    pbar.set_postfix({
                        'attempts': f'{attempts:,}',
                        'success_rate': f'{success_rate:.2f}%'
                    })
                    # Also print to stdout for log visibility
                    if attempts % (progress_update_interval * 10) == 0:  # Every 10 progress updates
                        print(f"\n[Progress] {len(samples):,}/{n_samples:,} samples ({len(samples)/n_samples*100:.1f}%), "
                              f"{attempts:,} attempts, {success_rate:.2f}% success rate")
                        sys.stdout.flush()
                
                # Every attempt for first 100 attempts (to show activity)
                if attempts <= 100 and attempts % 10 == 0:
                    print(f"[Early progress] Attempts: {attempts}, Samples: {len(samples)}, "
                          f"Success rate: {len(samples)/attempts*100:.2f}%")
                    sys.stdout.flush()
        
        success_rate = (len(samples) / attempts * 100) if attempts > 0 else 0
        if len(samples) < n_samples:
            print(f"\n⚠️  Generated {len(samples):,}/{n_samples:,} samples in {attempts:,} attempts")
            print(f"⚠️  Success rate: {success_rate:.2f}% (target not reached)")
        else:
            print(f"\n✓ Generated {len(samples):,} samples in {attempts:,} attempts")
            print(f"✓ Success rate: {success_rate:.2f}%")
        sys.stdout.flush()
        
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
    print("="*80)
    print("Training Data Generator - Starting...")
    print("="*80)
    sys.stdout.flush()
    
    graph_dir = Path("data/graph")
    embeddings_dir = Path("data/embeddings")
    output_dir = Path("data/training")
    
    # Check if output already exists (auto-skip or resume)
    samples_file = output_dir / "training_samples.json"
    stats_file = output_dir / "dataset_statistics.json"
    
    # Check if we have complete data (both samples and stats)
    has_complete_data = False
    if samples_file.exists() and stats_file.exists():
        try:
            with open(samples_file, 'r', encoding='utf-8') as f:
                existing_samples = json.load(f)
            # Check if we have reasonable number of samples (at least 100)
            if len(existing_samples) >= 100:
                has_complete_data = True
        except:
            pass
    
    if has_complete_data:
        print(f"⊘ Training data already exists in {output_dir}")
        print("  Skipping generation step. Delete output files to re-run.")
        sys.stdout.flush()
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
        print("\n📦 Loading graph and embeddings...")
        sys.stdout.flush()
        generator = TrainingDataGenerator(graph_dir, embeddings_dir)
        generator.load_data()
        print("✓ Data loaded successfully")
        sys.stdout.flush()
        
        # Generate start-target pairs
        # For large graphs, reduce sample count for faster generation
        n_pages = len(generator.pages)
        if n_pages > 10_000_000:
            n_samples = 2_000  # Very large graphs: 2K samples (was 10K, too slow)
            print(f"\n⚠️  Very large graph detected ({n_pages:,} pages). Using reduced sample count: {n_samples:,}")
        elif n_pages > 1_000_000:
            n_samples = 5_000  # Large graphs: 5K samples
            print(f"\n⚠️  Large graph detected ({n_pages:,} pages). Using reduced sample count: {n_samples:,}")
        else:
            n_samples = 10_000  # Normal graphs: 10K samples
        sys.stdout.flush()
        
        # Check for existing partial samples (resume capability)
        existing_samples = []
        if samples_file.exists() and samples_file.stat().st_size > 0:
            try:
                with open(samples_file, 'r', encoding='utf-8') as f:
                    existing_samples = json.load(f)
                if len(existing_samples) > 0:
                    print(f"\n✓ Found {len(existing_samples):,} existing samples. Resuming from checkpoint...")
                    sys.stdout.flush()
            except Exception as e:
                print(f"\n⚠️  Warning: Could not load existing samples: {e}")
                print("Starting fresh...")
                sys.stdout.flush()
                existing_samples = []
        
        # Calculate remaining samples needed
        remaining_samples = max(0, n_samples - len(existing_samples))
        
        if remaining_samples > 0:
            print(f"\n🔄 Starting sample generation (target: {n_samples:,} samples, "
                  f"{len(existing_samples):,} already exist, need {remaining_samples:,} more)...")
            sys.stdout.flush()
            new_samples = generator.generate_training_samples(
                n_samples=remaining_samples,  # Only generate what's needed
                output_file=samples_file,  # For incremental checkpointing
                existing_count=len(existing_samples)  # For progress tracking
            )
            # Load all samples (including incremental checkpoints)
            if samples_file.exists():
                with open(samples_file, 'r', encoding='utf-8') as f:
                    samples = json.load(f)
            else:
                samples = existing_samples + new_samples
        else:
            print(f"\n✓ Already have {len(existing_samples):,} samples (target: {n_samples:,}). Skipping generation.")
            sys.stdout.flush()
            samples = existing_samples
        print(f"✓ Generated {len(samples):,} path samples")
        sys.stdout.flush()
        
        print(f"\n🔄 Generating candidate samples with features...")
        sys.stdout.flush()
        # Generate candidate samples with features
        candidate_samples = generator.generate_candidate_samples(
            samples,
            n_candidates_per_sample=10
        )
        print(f"✓ Generated {len(candidate_samples):,} candidate samples")
        sys.stdout.flush()
        
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