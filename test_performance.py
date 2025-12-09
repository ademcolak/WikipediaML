#!/usr/bin/env python3
"""
Performance Test - Önce vs Sonra Karşılaştırması
-------------------------------------------------
İyileştirmelerin etkisini ölçmek için test suite.
"""

import time
from src.semantic_navigator import SemanticNavigator

# Test senaryoları
test_cases = [
    ("France", "Germany", "Kolay - Komşu ülkeler"),
    ("Computer", "Science", "Orta - İlgili konular"),
    ("Basketball", "Michael_Jordan", "Kolay - Direkt ilişki"),
    ("Python_(programming_language)", "Machine_learning", "Orta - Teknoloji"),
]

print("=" * 80)
print("🚀 PERFORMANCE TEST - İyileştirmeler Sonrası")
print("=" * 80)
print("\nİyileştirmeler:")
print("  ✅ Persistent Embedding Cache")
print("  ✅ Pre-filtering (1000+ → 100 links)")
print("  ✅ Hub Page Detection")
print("  ✅ Bidirectional Beam Search")
print()

results = []

for start, target, difficulty in test_cases:
    print("\n" + "─" * 80)
    print(f"📊 Test: {start} → {target}")
    print(f"   Zorluk: {difficulty}")
    print("─" * 80)
    
    # Test
    navigator = SemanticNavigator(verbose=False, use_graph=False)
    
    start_time = time.time()
    result = navigator.bidirectional_beam_search(
        start=start,
        target=target,
        beam_width=4,
        max_depth=10
    )
    elapsed = time.time() - start_time
    
    # Stats
    stats = navigator.get_stats()
    
    if result.found:
        print(f"   ✅ Bulundu!")
        print(f"   📏 Adım: {result.steps}")
        print(f"   🔍 Taranan sayfa: {result.pages_explored}")
        print(f"   ⏱️  Süre: {elapsed:.2f}s")
        print(f"   🧮 Embedding cache hit: {stats['embedder']['hit_rate']:.1f}%")
        print(f"   🧮 Total embeddings: {stats['embedder']['total_embeddings_computed']}")
        print(f"   🛤️  Path: {' → '.join(result.path)}")
        
        results.append({
            'test': f"{start} → {target}",
            'found': True,
            'steps': result.steps,
            'pages': result.pages_explored,
            'time': elapsed,
            'embeddings': stats['embedder']['total_embeddings_computed'],
            'cache_hit': stats['embedder']['hit_rate']
        })
    else:
        print(f"   ❌ Bulunamadı")
        print(f"   🔍 Taranan sayfa: {result.pages_explored}")
        print(f"   ⏱️  Süre: {elapsed:.2f}s")
        
        results.append({
            'test': f"{start} → {target}",
            'found': False,
            'pages': result.pages_explored,
            'time': elapsed
        })

# Özet
print("\n" + "=" * 80)
print("📊 ÖZET")
print("=" * 80)

total_time = sum(r['time'] for r in results)
total_pages = sum(r['pages'] for r in results)
total_embeddings = sum(r.get('embeddings', 0) for r in results)
avg_cache_hit = sum(r.get('cache_hit', 0) for r in results) / len(results)

print(f"\nToplam:")
print(f"  • Test sayısı: {len(results)}")
print(f"  • Başarı oranı: {sum(1 for r in results if r['found'])}/{len(results)} (%{sum(1 for r in results if r['found'])/len(results)*100:.0f})")
print(f"  • Toplam süre: {total_time:.2f}s")
print(f"  • Toplam sayfa: {total_pages}")
print(f"  • Toplam embeddings: {total_embeddings}")
print(f"  • Ortalama cache hit: {avg_cache_hit:.1f}%")

print(f"\nOrtalama (başarılı testler):")
successful = [r for r in results if r['found']]
if successful:
    avg_time = sum(r['time'] for r in successful) / len(successful)
    avg_pages = sum(r['pages'] for r in successful) / len(successful)
    avg_embeddings = sum(r['embeddings'] for r in successful) / len(successful)
    
    print(f"  • Süre: {avg_time:.2f}s")
    print(f"  • Taranan sayfa: {avg_pages:.1f}")
    print(f"  • Embeddings: {avg_embeddings:.0f}")

print("\n" + "=" * 80)
print("✅ Test tamamlandı!")
print("=" * 80)

# Beklenen iyileştirmeler
print("\n📈 Beklenen İyileştirmeler:")
print("  • Persistent Cache: %50-70 daha az embedding computation (2. çalıştırma)")
print("  • Pre-filtering: %80-90 daha az embedding (1000+ → 100 links)")
print("  • Hub Detection: Daha akıllı link seçimi")
print("  • Bidirectional: %80-90 daha az sayfa tarama")
print("\n💡 İkinci çalıştırmada cache hit rate çok daha yüksek olacak!")