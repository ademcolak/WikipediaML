#!/usr/bin/env python3
"""
WikipediaML Real Challenge Benchmark
=====================================

Gerçek dünya challenge'ı - tamamen random Wikipedia sayfaları.
50 challenge (100 random sayfa).

Kullanım:
    python benchmark_real.py

Özellikler:
- 100 random Wikipedia sayfası
- 50 challenge (ilk 50 start, son 50 target)
- Gerçek dünya zorluk seviyesi
- Sonuçlar: data/benchmark_real_results_*.json
"""

import sys
import json
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add core to path
sys.path.insert(0, str(Path(__file__).parent))

from core import Navigator


class RealChallengeBenchmark:
    """Real-world challenge benchmark with completely random start and target."""
    
    def __init__(self):
        """Initialize benchmark."""
        self.navigator = Navigator(use_bidirectional=True, training_mode=False)
        self.results: List[Dict[str, Any]] = []
        
    def get_random_pages(self, count: int = 100) -> List[str]:
        """
        Get multiple random Wikipedia pages using Wikipedia API.
        
        Args:
            count: Number of random pages to fetch
        
        Returns:
            List of page titles
        """
        print(f"🎲 Fetching {count} random Wikipedia pages using API...")
        pages = []
        
        # Wikipedia API endpoint for random pages
        api_url = "https://en.wikipedia.org/w/api.php"
        
        # User-Agent header (required by Wikipedia)
        headers = {
            'User-Agent': 'WikipediaML/1.0 (Educational Project; ademcolak@example.com)'
        }
        
        # Fetch in batches of 10 (API limit)
        batches = (count + 9) // 10  # Round up
        
        for batch in range(batches):
            try:
                params = {
                    'action': 'query',
                    'format': 'json',
                    'list': 'random',
                    'rnnamespace': '0',  # Main namespace only (articles)
                    'rnlimit': min(10, count - len(pages))  # Max 10 per request
                }
                
                response = requests.get(api_url, params=params, headers=headers, timeout=10)
                data = response.json()
                
                if 'query' in data and 'random' in data['query']:
                    for page in data['query']['random']:
                        pages.append(page['title'])
                
                # Progress indicator
                print(f"   Progress: {len(pages)}/{count} pages fetched...")
                
                # Brief pause to avoid rate limiting
                time.sleep(0.2)
                
            except Exception as e:
                print(f"⚠️  Error in batch {batch + 1}: {e}")
                continue
        
        print(f"✅ Fetched {len(pages)} valid pages")
        return pages
    
    def run_challenge(self, challenge_id: int, start: str, target: str) -> Dict[str, Any]:
        """
        Run a single challenge.
        
        Args:
            challenge_id: Challenge number (1-50)
            start: Start page
            target: Target page
        
        Returns:
            Challenge result
        """
        print(f"\n{'='*60}")
        print(f"Challenge #{challenge_id}: {start} → {target}")
        print(f"{'='*60}")
        
        # ✅ Measure actual wall-clock time (includes all overhead)
        wall_start = time.time()
        
        # Find path (verbose=True to see progress)
        result = self.navigator.find_path(start, target, verbose=True)
        
        # Calculate actual elapsed time
        wall_time = time.time() - wall_start
        
        # Print result
        if result.found:
            print(f"\n✅ Success! {result.steps} steps")
            print(f"   Search Time: {result.time_seconds:.2f}s | Wall Time: {wall_time:.2f}s")
            print(f"   Source: {result.source}")
            # ✅ Show full path (not truncated)
            print(f"   Path ({len(result.path)} pages):")
            print(f"      {' → '.join(result.path)}")
        else:
            # ✅ Show failure details
            print(f"\n❌ Failed after {wall_time:.2f}s")
            print(f"   Reason: Timeout or no path found within depth limit")
            print(f"   Pages explored: {result.pages_explored}")
        
        return {
            'id': challenge_id,
            'start': start,
            'target': target,
            'success': result.found,
            'time': result.time_seconds,  # Internal search time
            'wall_time': wall_time,  # Actual elapsed time
            'steps': result.steps if result.found else 0,
            'path': result.path if result.found else [],
            'source': result.source,
            'pages_explored': result.pages_explored
        }
    
    def run(self):
        """Run all 50 challenges."""
        print("="*60)
        print("🎯 WIKIPEDIAML REAL CHALLENGE BENCHMARK")
        print("="*60)
        print(f"📊 50 challenges with random pages")
        print(f"🎲 Using Wikipedia API for random pages")
        print()
        
        # Get 100 random pages upfront
        random_pages = self.get_random_pages(100)
        
        if len(random_pages) < 100:
            print(f"⚠️  Warning: Only got {len(random_pages)} pages, expected 100")
        
        # Create 50 challenges (first 50 as start, last 50 as target)
        print(f"\n📊 Creating 50 challenges from {len(random_pages)} pages...")
        challenges = []
        
        for i in range(50):
            start = random_pages[i]
            target = random_pages[i + 50] if i + 50 < len(random_pages) else random_pages[-(i+1)]
            challenges.append((start, target))
            print(f"   Challenge {i+1}: {start} → {target}")
        
        print(f"\n{'='*60}")
        print("🚀 Starting challenges...")
        print(f"{'='*60}")
        
        # Run challenges
        for i, (start, target) in enumerate(challenges, 1):
            result = self.run_challenge(i, start, target)
            self.results.append(result)
        
        # Calculate statistics
        self.print_statistics()
        self.save_results()
    
    def print_statistics(self):
        """Print benchmark statistics."""
        print("\n" + "="*60)
        print("📊 REAL CHALLENGE RESULTS")
        print("="*60)
        
        # Filter valid results (where target was obtained)
        valid_results = [r for r in self.results if r['target'] is not None]
        successful = [r for r in valid_results if r['success']]
        failed = [r for r in valid_results if not r['success']]
        
        total = len(valid_results)
        success_count = len(successful)
        fail_count = len(failed)
        
        print(f"\n✅ Successful: {success_count}/{total} ({success_count/total*100:.1f}%)")
        print(f"❌ Failed: {fail_count}/{total}")
        
        if successful:
            search_times = [r['time'] for r in successful]
            wall_times = [r['wall_time'] for r in successful]
            steps = [r['steps'] for r in successful]
            
            print(f"\n⏱️  Time Statistics:")
            print(f"   Search Time (internal):")
            print(f"      Avg: {sum(search_times)/len(search_times):.2f}s")
            print(f"      Min: {min(search_times):.2f}s")
            print(f"      Max: {max(search_times):.2f}s")
            
            print(f"\n   Wall Time (actual elapsed):")
            print(f"      Avg: {sum(wall_times)/len(wall_times):.2f}s")
            print(f"      Min: {min(wall_times):.2f}s")
            print(f"      Max: {max(wall_times):.2f}s")
            
            # Overhead analysis
            avg_overhead = sum(wall_times)/len(wall_times) - sum(search_times)/len(search_times)
            overhead_pct = avg_overhead / (sum(wall_times)/len(wall_times)) * 100
            print(f"\n   Overhead: {avg_overhead:.2f}s avg ({overhead_pct:.1f}% of wall time)")
            
            print(f"\n🎯 Path Statistics:")
            print(f"   Avg Steps: {sum(steps)/len(steps):.1f}")
            print(f"   Min Steps: {min(steps)}")
            print(f"   Max Steps: {max(steps)}")
            
            # Source breakdown
            sources = {}
            for r in successful:
                source = r['source']
                sources[source] = sources.get(source, 0) + 1
            
            print(f"\n💾 Source Breakdown:")
            for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
                print(f"   {source}: {count}/{success_count} ({count/success_count*100:.1f}%)")
        
        # Failed challenges details
        if failed:
            print(f"\n❌ Failed Challenges:")
            for r in failed:
                print(f"   #{r['id']}: {r['start']} → {r['target']}")
                print(f"      Wall Time: {r['wall_time']:.2f}s | Pages Explored: {r['pages_explored']}")
        
        # Show some interesting challenges
        if successful:
            print(f"\n🌟 Interesting Challenges:")
            
            # Longest path
            longest = max(successful, key=lambda x: x['steps'])
            print(f"\n   Longest Path ({longest['steps']} steps):")
            print(f"   {longest['start']} → {longest['target']}")
            print(f"   Full Path: {' → '.join(longest['path'])}")
            
            # Fastest (by wall time)
            fastest = min(successful, key=lambda x: x['wall_time'])
            print(f"\n   Fastest ({fastest['wall_time']:.3f}s wall time):")
            print(f"   {fastest['start']} → {fastest['target']}")
            print(f"   Path: {' → '.join(fastest['path'])}")
            
            # Slowest (by wall time)
            slowest = max(successful, key=lambda x: x['wall_time'])
            print(f"\n   Slowest ({slowest['wall_time']:.2f}s wall time):")
            print(f"   {slowest['start']} → {slowest['target']}")
            print(f"   Path: {' → '.join(slowest['path'])}")
        
        print("\n" + "="*60)
    
    def save_results(self):
        """Save results to JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/benchmark_real_results_{timestamp}.json"
        
        # Prepare data
        data = {
            'timestamp': timestamp,
            'total_challenges': len(self.results),
            'valid_challenges': len([r for r in self.results if r['target'] is not None]),
            'successful': len([r for r in self.results if r['success']]),
            'results': self.results
        }
        
        # Save
        Path("data").mkdir(exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved: {filename}")


def main():
    """Main entry point."""
    benchmark = RealChallengeBenchmark()
    benchmark.run()


if __name__ == "__main__":
    main()