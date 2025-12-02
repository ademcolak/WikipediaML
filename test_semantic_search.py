"""
test_semantic_search.py
-----------------------
Greedy Semantic Search testleri - Gerçek Wikipedia'da!
"""

from src.semantic_navigator import SemanticNavigator


def test_semantic_search():
    """Greedy Semantic Search testleri."""
    print("=" * 60)
    print("🤖 GREEDY SEMANTIC SEARCH - GERÇEK TESTLER")
    print("=" * 60)

    navigator = SemanticNavigator(verbose=True)

    # Test senaryoları
    tests = [
        {
            "name": "Test 1: Kolay - Semantically Yakın",
            "start": "Potato",
            "target": "Pizza",
            "description": "İkisi de yemek - semantic olarak yakın olmalı"
        },
        {
            "name": "Test 2: Orta - Bilimsel Bağlantı",
            "start": "Albert_Einstein",
            "target": "Physics",
            "description": "Einstein fizikçi - direkt bağlantı olmalı"
        },
        {
            "name": "Test 3: Zor - Farklı Domainler",
            "start": "Python_(programming_language)",
            "target": "Italy",
            "description": "Programlama → Ülke: semantic olarak uzak"
        }
    ]

    results = []

    for i, test in enumerate(tests, 1):
        print(f"\n{'#'*60}")
        print(f"{test['name']}")
        print(f"{'#'*60}")
        print(f"📝 {test['description']}")
        print(f"📍 {test['start']} → 🎯 {test['target']}\n")

        result = navigator.greedy_semantic_search(
            start=test['start'],
            target=test['target'],
            max_steps=10
        )

        results.append({
            'test_name': test['name'],
            'result': result
        })

        # Test arası bekleme
        if i < len(tests):
            print(f"\n⏳ Sonraki test için 3 saniye bekleniyor...")
            import time
            time.sleep(3)

    # Özet rapor
    print(f"\n{'='*60}")
    print(f"📊 ÖZET RAPOR")
    print(f"{'='*60}")

    for item in results:
        test_name = item['test_name']
        result = item['result']

        print(f"\n{test_name}:")
        if result.found:
            print(f"  ✅ Başarılı!")
            print(f"  📏 Adım: {result.steps}")
            print(f"  🔍 Taranan sayfa: {result.pages_explored}")
            print(f"  ⏱️ Süre: {result.time_seconds:.2f}s")

            if result.similarity_scores:
                avg_sim = sum(result.similarity_scores) / len(result.similarity_scores)
                print(f"  📊 Ortalama similarity: {avg_sim:.3f}")

            print(f"  🛤️ Path: {' → '.join(result.path)}")
        else:
            print(f"  ❌ Başarısız")
            print(f"  📏 Atılan adım: {result.steps}")
            print(f"  🛤️ Son path: {' → '.join(result.path[-3:])}")

    print(f"\n{'='*60}")


def test_single_scenario():
    """Tek bir senaryo detaylı test."""
    print("=" * 60)
    print("🎯 DETAYLI TEST: Potato → Pizza")
    print("=" * 60)

    navigator = SemanticNavigator(verbose=True)

    result = navigator.greedy_semantic_search(
        start="Potato",
        target="Pizza",
        max_steps=10
    )

    print("\n" + "=" * 60)
    print("💡 ANALİZ")
    print("=" * 60)

    if result.found:
        print(f"\n✅ Path bulundu: {len(result.path)} adımda")
        print(f"\nPath detayları:")
        for i, (page, score) in enumerate(zip(result.path[1:], result.similarity_scores), 1):
            print(f"  Adım {i}: {page}")
            print(f"    → Similarity: {score:.3f}")
            if score > 0.7:
                print(f"    → 🟢 Çok yakın - mükemmel seçim!")
            elif score > 0.5:
                print(f"    → 🟡 Yakın - iyi seçim")
            else:
                print(f"    → 🔴 Uzak - suboptimal")

        print(f"\n🎯 Semantically mantıklı bir path mi?")
        print(f"   {' → '.join(result.path)}")
        print(f"   Bu path insan mantığına uygun görünüyor!")

    # Statistics
    stats = navigator.get_stats()
    print(f"\n📊 Cache Statistics:")
    print(f"  Scraper cache hit rate: {stats['scraper']['hit_rate']:.1f}%")
    print(f"  Embedder cache hit rate: {stats['embedder']['hit_rate']:.1f}%")
    print(f"  Total embeddings computed: {stats['embedder']['total_embeddings_computed']}")


def main():
    """Ana test fonksiyonu."""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "single":
        # Tek senaryo test
        test_single_scenario()
    else:
        # Tüm testler
        test_semantic_search()


if __name__ == "__main__":
    main()
