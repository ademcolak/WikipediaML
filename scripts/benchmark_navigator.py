#!/usr/bin/env python3
"""
Benchmark Script for Wikipedia Navigator (Optimized)
Tests different navigation strategies using multiprocessing for speed.
"""

import json
import time
import random
from pathlib import Path
from typing import List, Dict, Tuple
from tqdm import tqdm
import numpy as np
import sys
import multiprocessing
import concurrent.futures
import signal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.beam_search import load_beam_search_navigator
from core.advanced_navigator import load_advanced_navigator


# Global variables for worker processes
NAVIGATOR = None

def init_worker(navigator_type: str, graph_dir: Path, model_path: Path, embeddings_dir: Path):
    """Initialize worker process with navigator instance."""
    global NAVIGATOR
    
    if navigator_type == "beam":
        NAVIGATOR = load_beam_search_navigator(
            graph_dir=graph_dir,
            model_path=model_path,
            embeddings_dir=embeddings_dir,
            beam_width=10,
            max_depth=20
        )
    elif navigator_type == "advanced":
        NAVIGATOR = load_advanced_navigator(
            graph_dir=graph_dir,
            model_path=model_path,
            embeddings_dir=embeddings_dir,
            max_depth=20,
            tabu_size=50,
            backtrack_limit=3
        )

def run_single_test(args):
    """Run a single navigation test."""
    start_id, target_id = args
    global NAVIGATOR
    
    if NAVIGATOR is None:
        return None
        
    start_time = time.time()
    try:
        # Set a timeout for pathfinding to avoid hanging
        # Note: signal.alarm only works on Unix
        # Simple heuristic: if it takes too long, it's likely a fail
        
        path = None
        if hasattr(NAVIGATOR, 'search_with_stats'):
            path, stats = NAVIGATOR.search_with_stats(start_id, target_id)
        else:
            path = NAVIGATOR.search(start_id, target_id, verbose=False)
            
        duration = time.time() - start_time
        
        return {
            'success': path is not None,
            'path_length': len(path) if path else 0,
            'duration': duration,
            'start': start_id,
            'target': target_id,
            'path': path if path else []
        }
        
    except Exception as e:
        return {
            'success': False,
            'path_length': 0,
            'duration': time.time() - start_time,
            'error': str(e),
            'start': start_id,
            'target': target_id
        }

class NavigatorBenchmark:
    """Benchmark suite for Wikipedia navigators."""
    
    def __init__(self, graph_dir: Path, model_path: Path, embeddings_dir: Path):
        self.graph_dir = graph_dir
        self.model_path = model_path
        self.embeddings_dir = embeddings_dir
        
        # Load page mappings
        import pickle
        mappings_file = graph_dir / "page_mappings.pkl"
        with open(mappings_file, 'rb') as f:
            mappings = pickle.load(f)
            self.pages = mappings['pages']
            self.index_to_page_id = mappings['index_to_page_id']
    
    def generate_test_pairs(self, n_pairs: int = 100) -> List[Tuple[int, int]]:
        """Generate random test page pairs."""
        print(f"\n{'='*80}")
        print(f"Generating {n_pairs} test pairs...")
        print(f"{'='*80}")
        
        page_ids = list(self.pages.keys())
        pairs = []
        
        for _ in range(n_pairs):
            start_id = random.choice(page_ids)
            target_id = random.choice(page_ids)
            while target_id == start_id:
                target_id = random.choice(page_ids)
            pairs.append((start_id, target_id))
        
        return pairs
    
    def run_parallel_benchmark(
        self,
        navigator_type: str,
        test_pairs: List[Tuple[int, int]],
        n_workers: int = 4
    ) -> Dict:
        """Run benchmark using multiple processes."""
        print(f"\n{'='*80}")
        print(f"Benchmarking: {navigator_type.upper()} Navigator with {n_workers} workers")
        print(f"{'='*80}")
        
        results = {
            'navigator_name': navigator_type,
            'total_tests': len(test_pairs),
            'successful': 0,
            'failed': 0,
            'path_lengths': [],
            'execution_times': [],
            'avg_path_length': 0.0,
            'avg_execution_time': 0.0,
            'success_rate': 0.0
        }
        
        # Use spawn/fork context
        ctx = multiprocessing.get_context('fork')
        
        with concurrent.futures.ProcessPoolExecutor(
            max_workers=n_workers,
            mp_context=ctx,
            initializer=init_worker,
            initargs=(navigator_type, self.graph_dir, self.model_path, self.embeddings_dir)
        ) as executor:
            
            futures = [executor.submit(run_single_test, pair) for pair in test_pairs]
            
            for future in tqdm(concurrent.futures.as_completed(futures), total=len(test_pairs), desc="Testing"):
                res = future.result()
                
                if res['success']:
                    results['successful'] += 1
                    results['path_lengths'].append(res['path_length'])
                    results['execution_times'].append(res['duration'])
                    
                    # Log success immediately
                    start_title = self.pages.get(res['start'], 'Unknown')
                    target_title = self.pages.get(res['target'], 'Unknown')
                    print(f"\n✓ Found path: {start_title} -> {target_title} (len: {res['path_length']}, time: {res['duration']:.2f}s)")
                else:
                    results['failed'] += 1
                    # Log failure occasionally
                    if results['failed'] % 5 == 0:
                        start_title = self.pages.get(res['start'], 'Unknown')
                        target_title = self.pages.get(res['target'], 'Unknown')
                        print(f"\n✗ No path: {start_title} -> {target_title}")

        # Calculate stats
        if results['path_lengths']:
            results['avg_path_length'] = np.mean(results['path_lengths'])
            results['avg_execution_time'] = np.mean(results['execution_times'])
        
        results['success_rate'] = results['successful'] / results['total_tests']
        
        print(f"\nResults for {navigator_type}:")
        print(f"Success Rate: {results['success_rate']*100:.2f}%")
        print(f"Avg Path Length: {results['avg_path_length']:.2f}")
        print(f"Avg Time: {results['avg_execution_time']:.2f}s")
        
        return results

def main():
    graph_dir = Path("data/graph")
    model_path = Path("models/checkpoints/mlp_scorer_best.pt")
    embeddings_dir = Path("data/embeddings")
    
    # Check if files exist
    if not all(p.exists() for p in [graph_dir, model_path, embeddings_dir]):
        print("Required files not found.")
        return
        
    benchmark = NavigatorBenchmark(graph_dir, model_path, embeddings_dir)
    test_pairs = benchmark.generate_test_pairs(n_pairs=50) # 50 pairs for quick test
    
    # Run Beam Search Benchmark (Parallel)
    # Use fewer workers because each worker loads the FULL graph and embeddings (Heavy RAM usage)
    # With 128GB RAM, we can maybe fit 4-5 workers safely.
    # Graph + Embeddings approx 20GB per process if not shared perfectly.
    # Linux 'fork' should share memory, so we can use more workers.
    
    n_workers = min(multiprocessing.cpu_count(), 8) 
    
    benchmark.run_parallel_benchmark("beam", test_pairs, n_workers=n_workers)
    
    # Uncomment to test Advanced Navigator
    # benchmark.run_parallel_benchmark("advanced", test_pairs, n_workers=n_workers)

if __name__ == "__main__":
    main()
