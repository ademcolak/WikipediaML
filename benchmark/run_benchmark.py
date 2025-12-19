#!/usr/bin/env python3
"""
run_benchmark.py
----------------
Otomatik benchmark sistemi.

Özellikler:
- Test dataset'i çalıştır
- Detaylı metrikler topla
- Sonuçları kaydet
- Karşılaştırma yap

Kullanım:
    python benchmark/run_benchmark.py
    python benchmark/run_benchmark.py --dataset benchmark/test_dataset.json
    python benchmark/run_benchmark.py --algorithm beam --beam-width 3
    python benchmark/run_benchmark.py --max-tests 50
"""

import argparse
import json
import time
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import statistics

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.semantic_navigator import SemanticNavigator


class BenchmarkRunner:
    """Benchmark test runner."""
    
    def __init__(
        self,
        algorithm: str = "greedy",
        beam_width: int = 3,
        use_async: bool = True,
        timeout: int = 30
    ):
        """
        Benchmark runner'ı başlat.
        
        Parametreler:
            algorithm: "greedy", "beam", "astar"
            beam_width: Beam search için width
            use_async: Async mode kullan
            timeout: Her test için timeout (saniye)
        """
        self.algorithm = algorithm
        self.beam_width = beam_width
        self.use_async = use_async
        self.timeout = timeout
        
        # Navigator oluştur
        print(f"\n🚀 Navigator başlatılıyor (algorithm: {algorithm})...")
        self.navigator = SemanticNavigator()
        
        # Results
        self.results = []
        self.start_time = None
        self.end_time = None
    
    def load_dataset(self, dataset_file: str) -> List[Dict]:
        """Dataset'i yükle."""
        print(f"\n📂 Dataset yükleniyor: {dataset_file}")
        
        with open(dataset_file, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        
        print(f"✅ {len(dataset)} test pair yüklendi")
        return dataset
    
    def run_single_test(self, test: Dict) -> Dict:
        """Tek bir test çalıştır."""
        test_id = test["id"]
        start = test["start"]
        target = test["target"]
        difficulty = test["difficulty"]
        
        print(f"\n🧪 Test #{test_id}: {start} → {target} ({difficulty})")
        
        result = {
            "id": test_id,
            "start": start,
            "target": target,
            "difficulty": difficulty,
            "success": False,
            "time": 0,
            "clicks": 0,
            "path": [],
            "error": None,
            "kg_hit": False,
            "algorithm": self.algorithm
        }
        
        try:
            start_time = time.time()
            
            # Algorithm'a göre çalıştır
            if self.algorithm == "beam":
                search_result = self.navigator.beam_search(
                    start, target,
                    beam_width=self.beam_width
                )
            elif self.algorithm == "astar":
                # A* search henüz implement edilmemiş, greedy kullan
                print("⚠️  A* search henüz mevcut değil, greedy kullanılıyor")
                search_result = self.navigator.beam_search(
                    start, target,
                    beam_width=1  # Greedy = beam width 1
                )
            else:  # greedy
                search_result = self.navigator.beam_search(
                    start, target,
                    beam_width=1  # Greedy = beam width 1
                )
            
            elapsed = time.time() - start_time
            
            if search_result.found:
                result["success"] = True
                result["time"] = elapsed
                result["clicks"] = search_result.steps
                result["path"] = search_result.path
                result["kg_hit"] = self.navigator.knowledge_graph.paths_reused > 0 if self.navigator.knowledge_graph else False
                
                print(f"✅ Başarılı! {search_result.steps} tıklama, {elapsed:.2f}s")
                print(f"   Path: {' → '.join(search_result.path[:3])}{'...' if len(search_result.path) > 3 else ''}")
            else:
                result["error"] = "Path not found"
                print(f"❌ Path bulunamadı")
                
        except Exception as e:
            result["error"] = str(e)
            print(f"❌ Hata: {e}")
        
        return result
    
    def run_benchmark(
        self,
        dataset: List[Dict],
        max_tests: Optional[int] = None
    ) -> List[Dict]:
        """Tüm benchmark'ı çalıştır."""
        print("\n" + "="*70)
        print("🎯 BENCHMARK BAŞLIYOR")
        print("="*70)
        print(f"Algorithm: {self.algorithm}")
        print(f"Test sayısı: {len(dataset) if not max_tests else min(max_tests, len(dataset))}")
        print(f"Async: {self.use_async}")
        print("="*70)
        
        self.start_time = time.time()
        
        # Test'leri çalıştır
        test_count = min(max_tests, len(dataset)) if max_tests else len(dataset)
        
        for i, test in enumerate(dataset[:test_count], 1):
            print(f"\n[{i}/{test_count}]", end=" ")
            result = self.run_single_test(test)
            self.results.append(result)
            
            # Progress
            if i % 10 == 0:
                success_rate = sum(1 for r in self.results if r["success"]) / len(self.results) * 100
                avg_time = statistics.mean([r["time"] for r in self.results if r["success"]])
                print(f"\n📊 İlerleme: {i}/{test_count} | Başarı: %{success_rate:.1f} | Ort. Süre: {avg_time:.2f}s")
        
        self.end_time = time.time()
        
        return self.results
    
    def analyze_results(self) -> Dict:
        """Sonuçları analiz et."""
        print("\n" + "="*70)
        print("📊 SONUÇ ANALİZİ")
        print("="*70)
        
        total_tests = len(self.results)
        successful_tests = [r for r in self.results if r["success"]]
        failed_tests = [r for r in self.results if not r["success"]]
        
        # Genel metrikler
        success_rate = len(successful_tests) / total_tests * 100 if total_tests > 0 else 0
        
        analysis = {
            "total_tests": total_tests,
            "successful": len(successful_tests),
            "failed": len(failed_tests),
            "success_rate": success_rate,
            "total_time": (self.end_time - self.start_time) if (self.end_time and self.start_time) else 0,
            "algorithm": self.algorithm
        }
        
        if successful_tests:
            times = [r["time"] for r in successful_tests]
            clicks = [r["clicks"] for r in successful_tests]
            kg_hits = sum(1 for r in successful_tests if r["kg_hit"])
            
            analysis.update({
                "avg_time": statistics.mean(times),
                "median_time": statistics.median(times),
                "min_time": min(times),
                "max_time": max(times),
                "std_time": statistics.stdev(times) if len(times) > 1 else 0,
                "avg_clicks": statistics.mean(clicks),
                "median_clicks": statistics.median(clicks),
                "min_clicks": min(clicks),
                "max_clicks": max(clicks),
                "kg_hit_rate": kg_hits / len(successful_tests) * 100
            })
        
        # Zorluk bazlı analiz
        difficulty_stats = {}
        for difficulty in ["easy", "medium", "hard"]:
            diff_results = [r for r in self.results if r["difficulty"] == difficulty]
            if diff_results:
                diff_success = [r for r in diff_results if r["success"]]
                difficulty_stats[difficulty] = {
                    "total": len(diff_results),
                    "successful": len(diff_success),
                    "success_rate": len(diff_success) / len(diff_results) * 100,
                    "avg_time": statistics.mean([r["time"] for r in diff_success]) if diff_success else 0,
                    "avg_clicks": statistics.mean([r["clicks"] for r in diff_success]) if diff_success else 0
                }
        
        analysis["by_difficulty"] = difficulty_stats
        
        # Yazdır
        print(f"\n✅ Başarılı: {analysis['successful']}/{total_tests} (%{success_rate:.1f})")
        print(f"❌ Başarısız: {analysis['failed']}/{total_tests}")
        print(f"⏱️  Toplam Süre: {analysis['total_time']:.2f}s")
        
        if successful_tests:
            print(f"\n📈 Performans Metrikleri:")
            print(f"   Ortalama Süre: {analysis['avg_time']:.2f}s (±{analysis['std_time']:.2f}s)")
            print(f"   Medyan Süre: {analysis['median_time']:.2f}s")
            print(f"   Min/Max Süre: {analysis['min_time']:.2f}s / {analysis['max_time']:.2f}s")
            print(f"\n🎯 Tıklama Metrikleri:")
            print(f"   Ortalama Tıklama: {analysis['avg_clicks']:.2f}")
            print(f"   Medyan Tıklama: {analysis['median_clicks']:.1f}")
            print(f"   Min/Max Tıklama: {analysis['min_clicks']} / {analysis['max_clicks']}")
            print(f"\n💾 KG Cache Hit Rate: %{analysis['kg_hit_rate']:.1f}")
        
        if difficulty_stats:
            print(f"\n📊 Zorluk Bazlı Analiz:")
            for difficulty, stats in difficulty_stats.items():
                print(f"\n   {difficulty.upper()}:")
                print(f"      Başarı: {stats['successful']}/{stats['total']} (%{stats['success_rate']:.1f})")
                if stats['successful'] > 0:
                    print(f"      Ort. Süre: {stats['avg_time']:.2f}s")
                    print(f"      Ort. Tıklama: {stats['avg_clicks']:.2f}")
        
        print("="*70)
        
        return analysis
    
    def save_results(self, output_file: str):
        """Sonuçları kaydet."""
        print(f"\n💾 Sonuçlar kaydediliyor: {output_file}")
        
        # Analysis ekle
        analysis = self.analyze_results()
        
        output_data = {
            "metadata": {
                "algorithm": self.algorithm,
                "beam_width": self.beam_width if self.algorithm == "beam" else None,
                "use_async": self.use_async,
                "timestamp": datetime.now().isoformat(),
                "total_time": (self.end_time - self.start_time) if (self.end_time and self.start_time) else 0
            },
            "analysis": analysis,
            "results": self.results
        }
        
        # Kaydet
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Sonuçlar kaydedildi")


def main():
    """Ana fonksiyon."""
    parser = argparse.ArgumentParser(description='Benchmark Runner')
    parser.add_argument('--dataset', type=str, default='benchmark/test_dataset.json',
                       help='Test dataset dosyası')
    parser.add_argument('--algorithm', type=str, default='greedy',
                       choices=['greedy', 'beam', 'astar'],
                       help='Kullanılacak algoritma')
    parser.add_argument('--beam-width', type=int, default=3,
                       help='Beam search width (default: 3)')
    parser.add_argument('--no-async', action='store_true',
                       help='Async mode kullanma')
    parser.add_argument('--max-tests', type=int,
                       help='Maksimum test sayısı (default: tümü)')
    parser.add_argument('--output', type=str,
                       help='Çıktı dosyası (default: benchmark/results_<algorithm>_<timestamp>.json)')
    parser.add_argument('--timeout', type=int, default=30,
                       help='Her test için timeout (saniye)')
    
    args = parser.parse_args()
    
    # Output file
    if not args.output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"benchmark/results_{args.algorithm}_{timestamp}.json"
    
    # Runner oluştur
    runner = BenchmarkRunner(
        algorithm=args.algorithm,
        beam_width=args.beam_width,
        use_async=not args.no_async,
        timeout=args.timeout
    )
    
    # Dataset yükle
    dataset = runner.load_dataset(args.dataset)
    
    # Benchmark çalıştır
    results = runner.run_benchmark(dataset, args.max_tests)
    
    # Analiz et
    analysis = runner.analyze_results()
    
    # Kaydet
    runner.save_results(args.output)
    
    print("\n✅ BENCHMARK TAMAMLANDI")
    print(f"📊 Sonuçlar: {args.output}")


if __name__ == "__main__":
    main()