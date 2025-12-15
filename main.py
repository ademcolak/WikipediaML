#!/usr/bin/env python3
"""
Wikipedia PathFinder
--------------------
Bir Wikipedia sayfasından diğerine en kısa yolu bulur.

Sistem:
- Semantic embeddings (anlam bazlı link seçimi)
- Knowledge Graph (öğrenme ve hatırlama)
- Async/Parallel Processing (3x daha hızlı!)

Kullanım:
    python main.py <başlangıç> <hedef> [--async]

Örnek:
    python main.py Albert_Einstein Physics
    python main.py Potato Pizza --async
    python main.py Python_(programming_language) Machine_learning --async
"""

import sys
import asyncio
from src.semantic_navigator import SemanticNavigator


def print_usage():
    """Kullanım bilgisini göster."""
    print("=" * 70)
    print("🌐 WIKIPEDIA PATHFINDER v5.0.0 (Clean)")
    print("=" * 70)
    print("\nKullanım:")
    print("  python main.py <başlangıç> <hedef> [--async]")
    print("\nÖrnekler:")
    print("  python main.py Albert_Einstein Physics")
    print("  python main.py Potato Pizza --async")
    print("  python main.py Python_(programming_language) Machine_learning --async")
    print("\nOpsiyonel Flagler:")
    print("  --async     Async/parallel processing (3x daha hızlı!) [ÖNERİLİR]")
    print("\nNot:")
    print("  • Sayfa isimleri Wikipedia URL'indeki /wiki/ sonrası kısım")
    print("  • Boşluklar yerine _ kullanın")
    print("  • Parantez içeren isimler: Python_(programming_language)")
    print("  • --async flag'i beam search'te 2-3x hızlanma sağlar")
    print("=" * 70)


async def async_main():
    """Async ana fonksiyon."""
    # Argüman kontrolü
    if len(sys.argv) < 3:
        print_usage()
        sys.exit(1)

    start_page = sys.argv[1]
    target_page = sys.argv[2]
    use_async = "--async" in sys.argv

    # Başlık
    print("\n" + "=" * 70)
    print("🌐 WIKIPEDIA PATHFINDER v5.0.0 (Clean)")
    print("=" * 70)
    print(f"\n📍 Başlangıç: {start_page}")
    print(f"🎯 Hedef: {target_page}")
    
    # Mode bilgisi
    mode = "⚡ Async" if use_async else "🔮 Sync"
    print(f"🚀 Mode: {mode}")
    print("\n" + "=" * 70)

    # Navigator oluştur
    try:
        navigator = SemanticNavigator(
            verbose=True,
            use_graph=True,
            use_async=use_async
        )
    except ValueError as e:
        print(f"\n❌ Hata: {e}")
        sys.exit(1)

    # Async mode ise async bidirectional beam search kullan
    if use_async:
        result = await navigator.async_bidirectional_beam_search(
            start=start_page,
            target=target_page,
            beam_width=4,
            max_depth=6
        )
        # Close async scraper properly
        if navigator.async_scraper:
            await navigator.async_scraper.close()
    else:
        # Sync mode: Hybrid search (Graph + Beam)
        result = navigator.hybrid_search(
            start=start_page,
            target=target_page,
            max_steps=25
        )

    # Sonuç özeti
    print("\n" + "=" * 70)
    print("📊 SONUÇ ÖZETİ")
    print("=" * 70)

    if result.found:
        print(f"\n✅ Path bulundu!")
        print(f"\n🛤️  Path:")
        print(f"   {' → '.join(result.path)}")
        print(f"\n📏 Adım sayısı: {result.steps}")
        print(f"⏱️  Süre: {result.time_seconds:.2f}s")
        print(f"🔍 Taranan sayfa: {result.pages_explored}")
        print(f"🤖 Algoritma: {result.algorithm}")

        # Graph'tan mı geldi?
        if "Graph Reused" in result.algorithm:
            print(f"⚡ Öğrenilmiş path kullanıldı (anında!)")
    else:
        print(f"\n❌ Path bulunamadı")
        print(f"   {result.steps} adım denendi")
        if result.path:
            last_pages = result.path[-3:] if len(result.path) >= 3 else result.path
            print(f"   Son path: {' → '.join(last_pages)}")

    # Sistem istatistikleri
    stats = navigator.get_stats()

    print(f"\n{'─' * 70}")
    print("💾 SİSTEM İSTATİSTİKLERİ")
    print(f"{'─' * 70}")

    print(f"\nScraper Cache:")
    print(f"  Hit rate: {stats['scraper']['hit_rate']:.1f}%")
    print(f"  Cached pages: {stats['scraper']['size']}/{stats['scraper']['max_size']}")

    print(f"\nEmbedder Cache:")
    print(f"  Hit rate: {stats['embedder']['hit_rate']:.1f}%")
    print(f"  Total embeddings: {stats['embedder']['total_embeddings_computed']}")

    if 'graph' in stats:
        print(f"\nKnowledge Graph:")
        print(f"  Nodes: {stats['graph']['nodes']}")
        print(f"  Edges: {stats['graph']['edges']}")
        print(f"  Paths learned: {stats['graph']['paths_learned']}")
        print(f"  Paths reused: {stats['graph']['paths_reused']}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\n\n⚠️  İşlem kullanıcı tarafından durduruldu.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Hata: {e}")
        sys.exit(1)
