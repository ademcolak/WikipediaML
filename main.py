from src.pathfinder import PathFinder
from src.semantic_navigator import SemanticNavigator


def test_bfs():
    """
    BFS algoritmasını test et.

    Farklı zorluk seviyelerinde testler:
    1. Kolay: Yakın sayfalar (Potato -> Vegetable)
    2. Orta: Biraz uzak (Potato -> United_States)
    3. Zor: Çok farklı konular (Potato -> Barack_Obama)
    """
    print("\n" + "=" * 60)
    print("🧪 BFS ALGORİTMASI TESTLERİ")
    print("=" * 60)

    pathfinder = PathFinder(verbose=True)

    # Test senaryoları
    tests = [
        {
            "name": "Kolay Test",
            "start": "Potato",
            "target": "Vegetable",
            "description": "Potato ve Vegetable çok yakın sayfalar, muhtemelen 1-2 adımda bulur"
        },
        {
            "name": "Orta Test",
            "start": "Potato",
            "target": "United_States",
            "description": "Biraz daha uzak ama ulaşılabilir olmalı"
        },
        {
            "name": "Zor Test",
            "start": "Potato",
            "target": "Barack_Obama",
            "description": "Çok farklı konular, birkaç adım gerekebilir"
        }
    ]

    results = []

    for i, test in enumerate(tests, 1):
        print(f"\n{'#' * 60}")
        print(f"TEST {i}/{len(tests)}: {test['name']}")
        print(f"{'#' * 60}")
        print(f"📝 Açıklama: {test['description']}\n")

        result = pathfinder.bfs_search(
            start=test['start'],
            target=test['target'],
            max_depth=6  # 6 derece of separation
        )

        results.append({
            'test_name': test['name'],
            'result': result
        })

        # Testler arası bekleme (Wikipedia'yı spam'lememek için)
        if i < len(tests):
            print(f"\n⏳ Sonraki test için 2 saniye bekleniyor...")
            import time
            time.sleep(2)

    # Özet rapor
    print(f"\n{'=' * 60}")
    print(f"📊 ÖZET RAPOR")
    print(f"{'=' * 60}")

    for item in results:
        test_name = item['test_name']
        result = item['result']

        print(f"\n{test_name}:")
        if result['found']:
            print(f"  ✅ Başarılı")
            print(f"  📏 Adım sayısı: {result['steps']}")
            print(f"  🔍 Taranan sayfa: {result['pages_explored']}")
            print(f"  ⏱️ Süre: {result['time']:.2f}s")
        else:
            print(f"  ❌ Başarısız")
            print(f"  🔍 Taranan sayfa: {result['pages_explored']}")
            print(f"  ⏱️ Süre: {result['time']:.2f}s")


def compare_bfs_algorithms():
    """
    Normal BFS vs Bidirectional BFS karşılaştırması.

    Her iki algoritmayı aynı test senaryolarında çalıştırıp
    performance karşılaştırması yapar.
    """
    print("\n" + "=" * 60)
    print("⚔️ BFS vs BIDIRECTIONAL BFS KARŞILAŞTIRMASI")
    print("=" * 60)

    # Test senaryoları
    tests = [
        {
            "name": "Test 1: Yakın Sayfalar",
            "start": "Potato",
            "target": "Vegetable",
        },
        {
            "name": "Test 2: Orta Mesafe",
            "start": "Python_(programming_language)",
            "target": "Computer",
        },
        {
            "name": "Test 3: Uzak Sayfalar",
            "start": "Albert_Einstein",
            "target": "Pizza",
        }
    ]

    results = []

    for i, test in enumerate(tests, 1):
        print(f"\n{'#' * 60}")
        print(f"{test['name']}")
        print(f"{'#' * 60}")
        print(f"📍 {test['start']} → 🎯 {test['target']}\n")

        # PathFinder objesi (verbose=False ile sadece sonuçları göster)
        pathfinder = PathFinder(verbose=False)

        # Normal BFS
        print("🔵 Normal BFS çalışıyor...")
        bfs_result = pathfinder.bfs_search(
            start=test['start'],
            target=test['target'],
            max_depth=5
        )

        import time
        time.sleep(1)  # Wikipedia rate limiting

        # Bidirectional BFS
        print("🔴 Bidirectional BFS çalışıyor...")
        bi_result = pathfinder.bidirectional_bfs_search(
            start=test['start'],
            target=test['target'],
            max_depth=5
        )

        # Sonuçları kaydet (artık SearchResult dataclass)
        results.append({
            'test_name': test['name'],
            'bfs': bfs_result,
            'bidirectional': bi_result
        })

        # Performance özeti yazdır
        print(f"\n📈 Kısa Özet:")
        print(f"  BFS: {bfs_result.pages_explored} sayfa, {bfs_result.time_seconds:.2f}s")
        print(f"  Bidirectional: {bi_result.pages_explored} sayfa, {bi_result.time_seconds:.2f}s")

        # Test arası bekleme
        if i < len(tests):
            print(f"\n⏳ Sonraki test için 2 saniye bekleniyor...")
            time.sleep(2)

    # KARŞILAŞTIRMA RAPORU
    print(f"\n{'=' * 60}")
    print(f"📊 KARŞILAŞTIRMA RAPORU")
    print(f"{'=' * 60}")

    for item in results:
        test_name = item['test_name']
        bfs = item['bfs']
        bi = item['bidirectional']

        print(f"\n{test_name}:")
        print(f"  {'─' * 56}")

        if bfs.found and bi.found:
            # İkisi de buldu - karşılaştır
            print(f"  {'Metrik':<25} {'Normal BFS':<15} {'Bidirectional':<15}")
            print(f"  {'─' * 56}")
            print(f"  {'✅ Sonuç':<25} {'Bulundu':<15} {'Bulundu':<15}")
            print(f"  {'📏 Adım sayısı':<25} {bfs.steps:<15} {bi.steps:<15}")
            print(f"  {'🔍 Taranan sayfa':<25} {bfs.pages_explored:<15} {bi.pages_explored:<15}")
            print(f"  {'⏱️ Süre (s)':<25} {bfs.time_seconds:<15.2f} {bi.time_seconds:<15.2f}")
            print(f"  {'💾 Max queue':<25} {bfs.max_queue_size:<15} {bi.max_queue_size:<15}")

            # Kazanç hesapla
            page_improvement = ((bfs.pages_explored - bi.pages_explored) / bfs.pages_explored * 100)
            time_improvement = ((bfs.time_seconds - bi.time_seconds) / bfs.time_seconds * 100)

            print(f"\n  🎯 Bidirectional Kazancı:")
            if page_improvement > 0:
                print(f"    • %{page_improvement:.1f} daha az sayfa taradı")
            else:
                print(f"    • %{-page_improvement:.1f} daha fazla sayfa taradı")

            if time_improvement > 0:
                print(f"    • %{time_improvement:.1f} daha hızlı buldu")
            else:
                print(f"    • %{-time_improvement:.1f} daha yavaş buldu")

        elif not bfs.found and not bi.found:
            print(f"  ❌ Her iki algoritma da hedefi bulamadı")
        else:
            print(f"  ⚠️ Sadece {'Normal BFS' if bfs.found else 'Bidirectional BFS'} buldu")

    print(f"\n{'=' * 60}")


def test_semantic_search():
    """Semantic Search testleri - Akıllı link seçimi!"""
    print("\n" + "=" * 60)
    print("🤖 SEMANTIC SEARCH TESTLERİ")
    print("=" * 60)

    navigator = SemanticNavigator(verbose=True)

    tests = [
        {
            "name": "Test 1: Potato → Pizza",
            "start": "Potato",
            "target": "Pizza",
            "description": "İkisi de yemek - semantic olarak yakın"
        },
        {
            "name": "Test 2: Einstein → Physics",
            "start": "Albert_Einstein",
            "target": "Physics",
            "description": "Einstein fizikçi - direkt bağlantı"
        }
    ]

    results = []

    for i, test in enumerate(tests, 1):
        print(f"\n{'#'*60}")
        print(f"{test['name']}")
        print(f"{'#'*60}")
        print(f"📝 {test['description']}")
        print(f"📍 {test['start']} → 🎯 {test['target']}")

        result = navigator.greedy_semantic_search(
            start=test['start'],
            target=test['target'],
            max_steps=10
        )

        results.append({
            'test_name': test['name'],
            'result': result
        })

        if i < len(tests):
            print(f"\n⏳ Sonraki test için 3 saniye bekleniyor...")
            import time
            time.sleep(3)

    # Özet
    print(f"\n{'='*60}")
    print(f"📊 ÖZET")
    print(f"{'='*60}")

    for item in results:
        test_name = item['test_name']
        result = item['result']

        print(f"\n{test_name}:")
        if result.found:
            print(f"  ✅ Başarılı - {result.steps} adımda bulundu")
            print(f"  🛤️ Path: {' → '.join(result.path)}")
            if result.similarity_scores:
                avg_sim = sum(result.similarity_scores) / len(result.similarity_scores)
                print(f"  📊 Avg similarity: {avg_sim:.3f}")
        else:
            print(f"  ❌ Bulunamadı - {result.steps} adım atıldı")


def main():
    """
    Ana fonksiyon - Wikipedia ML testleri.
    """
    print("=" * 60)
    print("Wikipedia ML - Semantic Path Finder")
    print("=" * 60)
    print()
    print("Mevcut testler:")
    print("  1. test_semantic_search() - Semantic search (GÜNCEL!)")
    print("  2. compare_bfs_algorithms() - BFS karşılaştırma (eski)")
    print()

    # Semantic search'ü çalıştır
    test_semantic_search()


if __name__ == "__main__":
    main()