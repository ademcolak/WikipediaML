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
    
    print(f"[Worker {multiprocessing.current_process().name}] Initializing (loading graph & embeddings)...")
    sys.stdout.flush()
    
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
    
    print(f"[Worker {multiprocessing.current_process().name}] Ready!")
    sys.stdout.flush()

def run_single_test(args):
    """Run a single navigation test."""
    start_id, target_id, optimal_len = args
    global NAVIGATOR
    
    if NAVIGATOR is None:
        return None
        
    start_time = time.time()
    try:
        path = None
        visited_titles = [] # To track where it went
        
        # We need to access visited nodes to debug, but simple search only returns path
        # Let's trust the return path or empty list
        
        path = NAVIGATOR.search(start_id, target_id, verbose=False)
        
        # If path is found, it's a list of IDs. If not, it's None.
        # But we want to know where it went if it failed. 
        # Since we can't easily get internal state without changing core code, 
        # we will just report success/fail for now.
            
        duration = time.time() - start_time
        
        return {
            'success': path is not None,
            'path_length': len(path) if path else 0,
            'optimal_length': optimal_len,
            'duration': duration,
            'start': start_id,
            'target': target_id,
            'path': path if path else []
        }
        
    except Exception as e:
        return {
            'success': False,
            'path_length': 0,
            'optimal_length': 0,
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
        """
        Generate test pairs using known paths from training data (Ground Truth).
        This ensures paths definitely exist and are solvable.
        """
        print(f"\n{'='*80}")
        print(f"Loading {n_pairs} test pairs from training data...")
        print(f"{'='*80}")
        
        training_file = Path("data/training/training_samples.json")
        if not training_file.exists():
            print("⚠️  Training data not found! Falling back to random pairs.")
            return self._generate_random_pairs(n_pairs)
            
        try:
            with open(training_file, 'r', encoding='utf-8') as f:
                samples = json.load(f)
            
            if len(samples) < n_pairs:
                print(f"⚠️  Not enough training samples ({len(samples)} < {n_pairs}). Using all.")
                n_pairs = len(samples)
            
            # Filter for short paths (max 3 hops) to test basic capability first
            short_paths = []
            for s in samples:
                if 'path' in s and isinstance(s['path'], list):
                    # path includes start and end, so len <= 4 means max 3 hops
                    if len(s['path']) <= 4: 
                        short_paths.append(s)
            
            print(f"Found {len(short_paths)} short paths (<= 3 hops) out of {len(samples)} samples.")
            
            # If we have enough short paths, use them. Otherwise use random samples.
            source_samples = short_paths if len(short_paths) >= n_pairs else samples
            
            # Select random samples
            selected_samples = random.sample(source_samples, min(n_pairs, len(source_samples)))
            
            pairs = []
            for s in selected_samples:
                start_id = s['start_page_id']
                if 'target_page_id' in s:
                    target_id = s['target_page_id']
                else:
                    continue
                
                # Store the optimal path length for comparison
                optimal_len = len(s['path']) if 'path' in s else 0
                pairs.append((start_id, target_id, optimal_len))
            
            print(f"✓ Loaded {len(pairs)} test pairs (Ground Truth available)")
            return pairs
            
        except Exception as e:
            print(f"⚠️  Error reading training data: {e}. Falling back to random.")
            return self._generate_random_pairs(n_pairs)

    def _generate_random_pairs(self, n_pairs: int) -> List[Tuple[int, int, int]]:
        """Generate completely random pairs (Hard mode)."""
        page_ids = list(self.pages.keys())
        pairs = []
        for _ in range(n_pairs):
            start_id = random.choice(page_ids)
            target_id = random.choice(page_ids)
            while target_id == start_id:
                target_id = random.choice(page_ids)
            pairs.append((start_id, target_id, 0)) # 0 means unknown optimal length
        return pairs
    
    def run_parallel_benchmark(
        self,
        navigator_type: str,
        test_pairs: List[Tuple[int, int, int]],
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
                
                start_title = self.pages.get(res['start'], f"ID:{res['start']}")
                target_title = self.pages.get(res['target'], f"ID:{res['target']}")
                opt_len = res.get('optimal_length', '?')
                
                if res['success']:
                    results['successful'] += 1
                    results['path_lengths'].append(res['path_length'])
                    results['execution_times'].append(res['duration'])
                    
                    print(f"\n✓ Found: {start_title} -> {target_title} (Len: {res['path_length']} vs Opt: {opt_len}, Time: {res['duration']:.2f}s)")
                else:
                    results['failed'] += 1
                    if results['failed'] % 1 == 0: # Log every failure for debug
                        print(f"\n✗ Failed: {start_title} -> {target_title} (Opt Len: {opt_len})")

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
    # Use fewer workers to avoid OOM (Out Of Memory)
    # Each worker needs significant RAM for graph + embeddings.
    n_workers = 2
    
    benchmark.run_parallel_benchmark("beam", test_pairs, n_workers=n_workers)
    
    # Uncomment to test Advanced Navigator
    # benchmark.run_parallel_benchmark("advanced", test_pairs, n_workers=n_workers)

if __name__ == "__main__":
    main()
