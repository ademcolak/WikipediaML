#!/usr/bin/env python3
"""
Benchmark Script for Wikipedia Navigator
Tests different navigation strategies on random page pairs.
"""

import json
import time
import random
from pathlib import Path
from typing import List, Dict, Tuple
from tqdm import tqdm
import numpy as np
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.beam_search import load_beam_search_navigator
from core.advanced_navigator import load_advanced_navigator


class NavigatorBenchmark:
    """Benchmark suite for Wikipedia navigators."""
    
    def __init__(self, graph_dir: Path, model_path: Path, embeddings_dir: Path):
        """
        Initialize benchmark.
        
        Args:
            graph_dir: Directory containing graph data
            model_path: Path to trained MLP model
            embeddings_dir: Directory containing embeddings
        """
        self.graph_dir = graph_dir
        self.model_path = model_path
        self.embeddings_dir = embeddings_dir
        
        # Load page mappings
        import pickle
        mappings_file = graph_dir / "page_mappings.pkl"
        with open(mappings_file, 'rb') as f:
            mappings = pickle.load(f)
            self.pages = mappings['pages']
            self.page_id_to_index = mappings['page_id_to_index']
            self.index_to_page_id = mappings['index_to_page_id']
    
    def generate_test_pairs(
        self,
        n_pairs: int = 100,
        min_distance: int = 3,
        max_distance: int = 8
    ) -> List[Tuple[int, int]]:
        """
        Generate random test page pairs.
        
        Args:
            n_pairs: Number of pairs to generate
            min_distance: Minimum expected distance
            max_distance: Maximum expected distance
            
        Returns:
            List of (start_page_id, target_page_id) tuples
        """
        print(f"\n{'='*80}")
        print(f"Generating {n_pairs} test pairs...")
        print(f"{'='*80}")
        
        page_ids = list(self.pages.keys())
        pairs = []
        
        # Simple random sampling (in production, use BFS to verify distances)
        for _ in tqdm(range(n_pairs), desc="Generating pairs"):
            start_id = random.choice(page_ids)
            target_id = random.choice(page_ids)
            
            # Ensure different pages
            while target_id == start_id:
                target_id = random.choice(page_ids)
            
            pairs.append((start_id, target_id))
        
        print(f"✓ Generated {len(pairs)} test pairs")
        return pairs
    
    def benchmark_navigator(
        self,
        navigator,
        test_pairs: List[Tuple[int, int]],
        navigator_name: str
    ) -> Dict:
        """
        Benchmark a navigator on test pairs.
        
        Args:
            navigator: Navigator instance
            test_pairs: List of test pairs
            navigator_name: Name for reporting
            
        Returns:
            Dictionary of benchmark results
        """
        print(f"\n{'='*80}")
        print(f"Benchmarking: {navigator_name}")
        print(f"{'='*80}")
        
        results = {
            'navigator_name': navigator_name,
            'total_tests': len(test_pairs),
            'successful': 0,
            'failed': 0,
            'path_lengths': [],
            'execution_times': [],
            'avg_path_length': 0.0,
            'avg_execution_time': 0.0,
            'success_rate': 0.0,
            'median_path_length': 0.0
        }
        
        for start_id, target_id in tqdm(test_pairs, desc=f"Testing {navigator_name}"):
            start_time = time.time()
            
            try:
                if hasattr(navigator, 'search_with_stats'):
                    path, stats = navigator.search_with_stats(start_id, target_id)
                else:
                    path = navigator.search(start_id, target_id, verbose=False)
                    stats = {}
                
                execution_time = time.time() - start_time
                
                if path:
                    results['successful'] += 1
                    results['path_lengths'].append(len(path))
                    results['execution_times'].append(execution_time)
                else:
                    results['failed'] += 1
                    
            except Exception as e:
                print(f"\n✗ Error on pair ({start_id}, {target_id}): {e}")
                results['failed'] += 1
        
        # Calculate statistics
        if results['path_lengths']:
            results['avg_path_length'] = np.mean(results['path_lengths'])
            results['median_path_length'] = np.median(results['path_lengths'])
            results['min_path_length'] = int(np.min(results['path_lengths']))
            results['max_path_length'] = int(np.max(results['path_lengths']))
        
        if results['execution_times']:
            results['avg_execution_time'] = np.mean(results['execution_times'])
            results['median_execution_time'] = np.median(results['execution_times'])
        
        results['success_rate'] = results['successful'] / results['total_tests']
        
        # Print summary
        print(f"\n{'='*80}")
        print(f"Results for {navigator_name}:")
        print(f"{'='*80}")
        print(f"Success rate: {results['success_rate']*100:.2f}%")
        print(f"Successful: {results['successful']}/{results['total_tests']}")
        print(f"Failed: {results['failed']}/{results['total_tests']}")
        
        if results['path_lengths']:
            print(f"\nPath Statistics:")
            print(f"  Average length: {results['avg_path_length']:.2f}")
            print(f"  Median length: {results['median_path_length']:.1f}")
            print(f"  Min length: {results['min_path_length']}")
            print(f"  Max length: {results['max_path_length']}")
        
        if results['execution_times']:
            print(f"\nPerformance:")
            print(f"  Average time: {results['avg_execution_time']:.3f}s")
            print(f"  Median time: {results['median_execution_time']:.3f}s")
        
        return results
    
    def run_comparison(
        self,
        test_pairs: List[Tuple[int, int]]
    ) -> Dict:
        """
        Run comparison between different navigators.
        
        Args:
            test_pairs: List of test pairs
            
        Returns:
            Dictionary of all results
        """
        all_results = {}
        
        # Test Beam Search Navigator
        print("\n" + "="*80)
        print("Loading Beam Search Navigator...")
        print("="*80)
        
        beam_navigator = load_beam_search_navigator(
            graph_dir=self.graph_dir,
            model_path=self.model_path,
            embeddings_dir=self.embeddings_dir,
            beam_width=10,
            max_depth=15
        )
        
        all_results['beam_search'] = self.benchmark_navigator(
            beam_navigator,
            test_pairs,
            "Beam Search (width=10)"
        )
        
        # Test Advanced Navigator
        print("\n" + "="*80)
        print("Loading Advanced Navigator...")
        print("="*80)
        
        advanced_navigator = load_advanced_navigator(
            graph_dir=self.graph_dir,
            model_path=self.model_path,
            embeddings_dir=self.embeddings_dir,
            max_depth=15,
            tabu_size=100,
            backtrack_limit=5
        )
        
        all_results['advanced'] = self.benchmark_navigator(
            advanced_navigator,
            test_pairs,
            "Advanced Navigator (with backtracking)"
        )
        
        return all_results
    
    def print_comparison(self, all_results: Dict) -> None:
        """Print comparison table."""
        print(f"\n{'='*80}")
        print("COMPARISON SUMMARY")
        print(f"{'='*80}")
        
        print(f"\n{'Navigator':<40} {'Success Rate':<15} {'Avg Path':<12} {'Avg Time':<12}")
        print("-" * 80)
        
        for name, results in all_results.items():
            nav_name = results['navigator_name']
            success = f"{results['success_rate']*100:.1f}%"
            avg_path = f"{results['avg_path_length']:.2f}" if results['path_lengths'] else "N/A"
            avg_time = f"{results['avg_execution_time']:.3f}s" if results['execution_times'] else "N/A"
            
            print(f"{nav_name:<40} {success:<15} {avg_path:<12} {avg_time:<12}")
    
    def save_results(self, results: Dict, output_path: Path) -> None:
        """Save benchmark results to JSON."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert numpy types to native Python types
        def convert_types(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_types(item) for item in obj]
            return obj
        
        results_converted = convert_types(results)
        
        with open(output_path, 'w') as f:
            json.dump(results_converted, f, indent=2)
        
        print(f"\n✓ Results saved to {output_path}")


def main():
    """Main benchmark function."""
    graph_dir = Path("data/graph")
    model_path = Path("models/checkpoints/mlp_scorer_best.pt")
    embeddings_dir = Path("data/embeddings")
    output_dir = Path("benchmarks")
    
    # Check if required files exist
    if not all(p.exists() for p in [graph_dir, model_path, embeddings_dir]):
        print("✗ Error: Required files not found!")
        print("Please run the full training pipeline first.")
        return 1
    
    try:
        # Create benchmark
        benchmark = NavigatorBenchmark(graph_dir, model_path, embeddings_dir)
        
        # Generate test pairs
        test_pairs = benchmark.generate_test_pairs(n_pairs=100)
        
        # Run comparison
        all_results = benchmark.run_comparison(test_pairs)
        
        # Print comparison
        benchmark.print_comparison(all_results)
        
        # Save results
        benchmark.save_results(all_results, output_dir / "benchmark_results.json")
        
        print("\n✓ Benchmark completed successfully!")
        print("\nNext steps:")
        print("1. Analyze results and identify bottlenecks")
        print("2. Implement hybrid speed control")
        print("3. Add fallback mechanism for missing data")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Error during benchmark: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())