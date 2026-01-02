#!/usr/bin/env python3
"""
WikipediaML Benchmark - Performans Testi
=========================================

Benchmark test - performans ölç.
Parametre yok, sadece çalıştır.

Kullanım:
    python benchmark.py

Özellikler:
- Test dataset (data/benchmark_dataset.json)
- Detaylı metrikler
- Zorluk bazlı analiz
- Sonuçları kaydet
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import statistics

# Add core to path
sys.path.insert(0, str(Path(__file__).parent))

from core import Navigator


class Benchmark:
    """Benchmark runner."""
    
    def __init__(self):
        """Initialize benchmark."""
        self.navigator = Navigator()
        self.results = []
        self.dataset_file = Path("data/benchmark_dataset.json")
    
    def load_dataset(self) -> List[Dict]:
        """Load benchmark dataset."""
        if not self.dataset_file.exists():
            print(f"⚠️  Dataset not found: {self.dataset_file}")
            print("Creating default dataset...")
            return self._create_default_dataset()
        
        with open(self.dataset_file, 'r') as f:
            dataset = json.load(f)
        
        print(f"📂 Loaded {len(dataset)} challenges")
        return dataset
    
    def _create_default_dataset(self) -> List[Dict]:
        """Create default benchmark dataset."""
        dataset = [
            # EASY
            {"id": 1, "start": "Italy", "target": "Rome", "difficulty": "easy"},
            {"id": 2, "start": "France", "target": "Paris", "difficulty": "easy"},
            {"id": 3, "start": "Physics", "target": "Albert_Einstein", "difficulty": "easy"},
            {"id": 4, "start": "Computer_science", "target": "Programming", "difficulty": "easy"},
            {"id": 5, "start": "United_States", "target": "New_York_City", "difficulty": "easy"},
            
            # MEDIUM
            {"id": 6, "start": "Technology", "target": "Philosophy", "difficulty": "medium"},
            {"id": 7, "start": "Biology", "target": "Computer_science", "difficulty": "medium"},
            {"id": 8, "start": "History", "target": "Mathematics", "difficulty": "medium"},
            {"id": 9, "start": "Art", "target": "Science", "difficulty": "medium"},
            {"id": 10, "start": "Music", "target": "Engineering", "difficulty": "medium"},
            
            # HARD
            {"id": 11, "start": "Ancient_Rome", "target": "Quantum_mechanics", "difficulty": "hard"},
            {"id": 12, "start": "Basketball", "target": "Medieval_history", "difficulty": "hard"},
            {"id": 13, "start": "Poetry", "target": "Nuclear_physics", "difficulty": "hard"},
        ]
        
        # Save dataset
        self.dataset_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.dataset_file, 'w') as f:
            json.dump(dataset, f, indent=2)
        
        print(f"✅ Created default dataset: {len(dataset)} challenges")
        return dataset
    
    def run_test(self, challenge: Dict) -> Dict:
        """Run single test."""
        test_id = challenge['id']
        start = challenge['start']
        target = challenge['target']
        difficulty = challenge['difficulty']
        
        print(f"\n{'='*60}")
        print(f"Test #{test_id}: {start} → {target} ({difficulty})")
        print(f"{'='*60}")
        
        # ✅ Measure actual wall-clock time (includes all overhead)
        wall_start = time.time()
        
        # Run test
        result = self.navigator.find_path(start, target, verbose=False)
        
        # Calculate actual elapsed time
        wall_time = time.time() - wall_start
        
        # Create result dict
        test_result = {
            'id': test_id,
            'start': start,
            'target': target,
            'difficulty': difficulty,
            'success': result.found,
            'time': result.time_seconds,  # Internal search time
            'wall_time': wall_time,  # Actual elapsed time
            'steps': result.steps,
            'path': result.path,
            'source': result.source
        }
        
        # Print result
        if result.found:
            print(f"✅ Success! {result.steps} steps")
            print(f"   Search Time: {result.time_seconds:.2f}s | Wall Time: {wall_time:.2f}s")
            print(f"   Source: {result.source}")
            # ✅ Show full path (not truncated)
            print(f"   Path ({len(result.path)} pages):")
            print(f"      {' → '.join(result.path)}")
        else:
            # ✅ Show failure details
            print(f"❌ Failed after {wall_time:.2f}s")
            print(f"   Reason: Timeout or no path found within depth limit")
            print(f"   Pages explored: {result.pages_explored}")
        
        return test_result
    
    def run_benchmark(self):
        """Run full benchmark."""
        print("\n" + "="*60)
        print("🎯 WIKIPEDIAML BENCHMARK")
        print("="*60)
        
        # Load dataset
        dataset = self.load_dataset()
        
        print(f"\nRunning {len(dataset)} tests...")
        print("="*60)
        
        start_time = time.time()
        
        # Run tests
        for challenge in dataset:
            result = self.run_test(challenge)
            self.results.append(result)
            
            # Rate limiting
            time.sleep(1)
        
        total_time = time.time() - start_time
        
        # Analyze results
        self.analyze_results(total_time)
        
        # Save results
        self.save_results()
    
    def analyze_results(self, total_time: float):
        """Analyze and print results."""
        print("\n" + "="*60)
        print("📊 BENCHMARK RESULTS")
        print("="*60)
        
        total = len(self.results)
        successful = [r for r in self.results if r['success']]
        failed = [r for r in self.results if not r['success']]
        
        # Overall stats
        success_rate = len(successful) / total * 100 if total > 0 else 0
        
        print(f"\n✅ Successful: {len(successful)}/{total} ({success_rate:.1f}%)")
        print(f"❌ Failed: {len(failed)}/{total}")
        print(f"⏱️  Total Time: {total_time:.2f}s")
        
        if successful:
            search_times = [r['time'] for r in successful]
            wall_times = [r['wall_time'] for r in successful]
            steps = [r['steps'] for r in successful]
            
            print(f"\n📈 Performance Metrics:")
            print(f"   Search Time (internal):")
            print(f"      Avg: {statistics.mean(search_times):.2f}s (±{statistics.stdev(search_times) if len(search_times) > 1 else 0:.2f}s)")
            print(f"      Median: {statistics.median(search_times):.2f}s")
            print(f"      Min/Max: {min(search_times):.2f}s / {max(search_times):.2f}s")
            
            print(f"\n   Wall Time (actual elapsed):")
            print(f"      Avg: {statistics.mean(wall_times):.2f}s (±{statistics.stdev(wall_times) if len(wall_times) > 1 else 0:.2f}s)")
            print(f"      Median: {statistics.median(wall_times):.2f}s")
            print(f"      Min/Max: {min(wall_times):.2f}s / {max(wall_times):.2f}s")
            
            # Overhead analysis
            overhead = statistics.mean(wall_times) - statistics.mean(search_times)
            print(f"\n   Overhead: {overhead:.2f}s avg ({overhead/statistics.mean(wall_times)*100:.1f}% of wall time)")
            
            print(f"\n🎯 Path Metrics:")
            print(f"   Avg Steps: {statistics.mean(steps):.2f}")
            print(f"   Median Steps: {statistics.median(steps):.1f}")
            print(f"   Min/Max Steps: {min(steps)} / {max(steps)}")
            
            # Source breakdown
            kg_hits = sum(1 for r in successful if r['source'] == 'knowledge_graph')
            print(f"\n💾 Knowledge Graph:")
            print(f"   Cache hits: {kg_hits}/{len(successful)} ({kg_hits/len(successful)*100:.1f}%)")
        
        # Difficulty breakdown
        print(f"\n📊 By Difficulty:")
        for difficulty in ['easy', 'medium', 'hard']:
            diff_results = [r for r in self.results if r['difficulty'] == difficulty]
            if diff_results:
                diff_success = [r for r in diff_results if r['success']]
                diff_failed = [r for r in diff_results if not r['success']]
                rate = len(diff_success) / len(diff_results) * 100
                
                print(f"\n   {difficulty.upper()}:")
                print(f"      Success: {len(diff_success)}/{len(diff_results)} ({rate:.1f}%)")
                
                if diff_success:
                    avg_search_time = statistics.mean([r['time'] for r in diff_success])
                    avg_wall_time = statistics.mean([r['wall_time'] for r in diff_success])
                    avg_steps = statistics.mean([r['steps'] for r in diff_success])
                    print(f"      Avg Search Time: {avg_search_time:.2f}s")
                    print(f"      Avg Wall Time: {avg_wall_time:.2f}s")
                    print(f"      Avg Steps: {avg_steps:.2f}")
                
                if diff_failed:
                    print(f"      Failed tests: {', '.join(f'#{r['id']}' for r in diff_failed)}")
        
        print("\n" + "="*60)
    
    def save_results(self):
        """Save results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path(f"data/benchmark_results_{timestamp}.json")
        
        output_data = {
            'timestamp': timestamp,
            'total_tests': len(self.results),
            'successful': sum(1 for r in self.results if r['success']),
            'results': self.results
        }
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"\n💾 Results saved: {output_file}")


def main():
    """Main entry point."""
    benchmark = Benchmark()
    benchmark.run_benchmark()


if __name__ == '__main__':
    main()