#!/usr/bin/env python3
"""
Benchmark Script for Wikipedia Navigator (Optimized)
Tests different navigation strategies using multiprocessing for speed.
"""

import argparse
import json
import time
import random
from pathlib import Path
from typing import List, Dict, Tuple, Optional
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

def init_worker(
    navigator_type: str,
    graph_dir: Path,
    model_path: Path,
    embeddings_dir: Path,
    beam_width: int,
    max_depth: int,
    scorer_kwargs: Dict
):
    """Initialize worker process with navigator instance."""
    global NAVIGATOR
    
    print(f"[Worker {multiprocessing.current_process().name}] Initializing (loading graph & embeddings)...")
    sys.stdout.flush()
    
    if navigator_type == "beam":
        NAVIGATOR = load_beam_search_navigator(
            graph_dir=graph_dir,
            model_path=model_path,
            embeddings_dir=embeddings_dir,
            beam_width=beam_width,
            max_depth=max_depth,
            **scorer_kwargs
        )
    elif navigator_type == "advanced":
        NAVIGATOR = load_advanced_navigator(
            graph_dir=graph_dir,
            model_path=model_path,
            embeddings_dir=embeddings_dir,
            max_depth=max_depth,
            tabu_size=50,
            backtrack_limit=3,
            **scorer_kwargs
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
            self.page_id_to_index = mappings.get('page_id_to_index', {})
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
            
            if len(samples) == 0:
                print("⚠️  Training data is empty! Falling back to random pairs.")
                return self._generate_random_pairs(n_pairs)

            print(f"✓ Loaded {len(samples):,} raw training samples")
            has_distance = any('distance' in s for s in samples)
            has_candidate_dist = any('candidate_dist' in s for s in samples)
            if not has_distance and has_candidate_dist:
                print("⚠️  Only 'candidate_dist' found; start-target distance is unknown.")
            
            # Validate samples against current graph mappings
            pairs_by_key: Dict[Tuple[int, int], Optional[int]] = {}
            invalid_count = 0
            non_mappable = 0
            candidate_samples = 0
            for s in samples:
                start_id = s.get('start_page_id')
                target_id = s.get('target_page_id')
                if start_id is None or target_id is None:
                    invalid_count += 1
                    continue
                if self.pages and (start_id not in self.pages or target_id not in self.pages):
                    non_mappable += 1
                    continue

                if 'candidate_idx' in s or 'candidate_page_id' in s:
                    candidate_samples += 1

                distance = None
                if 'distance' in s:
                    distance = s.get('distance')
                elif 'candidate_dist' in s:
                    distance = s.get('candidate_dist')

                if distance is not None:
                    try:
                        distance = int(distance)
                    except (TypeError, ValueError):
                        distance = None

                key = (start_id, target_id)
                if key not in pairs_by_key:
                    pairs_by_key[key] = distance
                else:
                    existing = pairs_by_key[key]
                    if existing is None and distance is not None:
                        pairs_by_key[key] = distance
                    elif existing is not None and distance is not None and distance < existing:
                        pairs_by_key[key] = distance
            
            if invalid_count > 0:
                print(f"⚠️  Dropped {invalid_count:,} samples with missing IDs.")
            if non_mappable > 0:
                print(f"⚠️  Dropped {non_mappable:,} samples not compatible with current graph.")

            if candidate_samples > 0:
                print(f"ℹ️  Candidate-format samples detected: {candidate_samples:,}")

            if len(pairs_by_key) == 0:
                print("⚠️  No valid samples after filtering. Falling back to random pairs.")
                return self._generate_random_pairs(n_pairs)
            
            # Filter for short paths (max 3 hops) to test basic capability first
            short_pairs = []
            all_pairs = []
            for (start_id, target_id), distance in pairs_by_key.items():
                if distance is not None:
                    optimal_len = distance + 1
                else:
                    optimal_len = 0

                all_pairs.append((start_id, target_id, optimal_len))

                # path includes start and end, so len <= 4 means max 3 hops
                if optimal_len > 0 and optimal_len <= 4:
                    short_pairs.append((start_id, target_id, optimal_len))
            
            if short_pairs:
                print(f"Found {len(short_pairs)} short paths (<= 3 hops) out of {len(all_pairs)} unique pairs.")
            else:
                print("⚠️  No short paths found; using all available pairs.")
            
            # If we have enough short paths, use them. Otherwise use random samples.
            source_pairs = short_pairs if len(short_pairs) >= n_pairs else all_pairs
            selected_pairs = random.sample(source_pairs, min(n_pairs, len(source_pairs)))
            
            print(f"✓ Loaded {len(selected_pairs)} test pairs")
            return selected_pairs
            
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
        n_workers: int,
        beam_width: int,
        max_depth: int,
        scorer_kwargs: Dict
    ) -> Dict:
        """Run benchmark using multiple processes."""
        print(f"\n{'='*80}")
        print(f"Benchmarking: {navigator_type.upper()} Navigator with {n_workers} workers")
        print(f"Beam width: {beam_width}, Max depth: {max_depth}")
        if scorer_kwargs:
            print(f"Scorer overrides: {scorer_kwargs}")
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
            initargs=(
                navigator_type,
                self.graph_dir,
                self.model_path,
                self.embeddings_dir,
                beam_width,
                max_depth,
                scorer_kwargs
            )
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
    parser = argparse.ArgumentParser(
        description="Benchmark Wikipedia navigator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--graph-dir", type=str, default="data/graph")
    parser.add_argument("--embeddings-dir", type=str, default="data/embeddings")
    parser.add_argument("--model-path", type=str, default="models/checkpoints/mlp_scorer_best.pt")
    parser.add_argument("--navigator", type=str, default="beam", choices=["beam", "advanced"])
    parser.add_argument("--n-pairs", type=int, default=50)
    parser.add_argument("--n-workers", type=int, default=2)
    parser.add_argument("--beam-width", type=int, default=10)
    parser.add_argument("--max-depth", type=int, default=20)
    parser.add_argument("--alpha", type=float, default=None)
    parser.add_argument("--beta", type=float, default=None)
    parser.add_argument("--gamma", type=float, default=None)

    args = parser.parse_args()

    graph_dir = Path(args.graph_dir)
    model_path = Path(args.model_path)
    embeddings_dir = Path(args.embeddings_dir)

    # Check if files exist
    if not all(p.exists() for p in [graph_dir, model_path, embeddings_dir]):
        print("Required files not found.")
        return

    scorer_kwargs: Dict = {}
    if args.alpha is not None:
        scorer_kwargs["alpha"] = args.alpha
    if args.beta is not None:
        scorer_kwargs["beta"] = args.beta
    if args.gamma is not None:
        scorer_kwargs["gamma"] = args.gamma

    benchmark = NavigatorBenchmark(graph_dir, model_path, embeddings_dir)
    test_pairs = benchmark.generate_test_pairs(n_pairs=args.n_pairs)

    benchmark.run_parallel_benchmark(
        args.navigator,
        test_pairs,
        n_workers=args.n_workers,
        beam_width=args.beam_width,
        max_depth=args.max_depth,
        scorer_kwargs=scorer_kwargs
    )

if __name__ == "__main__":
    main()
