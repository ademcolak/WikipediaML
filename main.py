#!/usr/bin/env python3
"""
Wikipedia PathFinder
--------------------
Bir Wikipedia sayfasından diğerine en kısa yolu bulur.

Hybrid sistem:
- Semantic embeddings (anlam bazlı link seçimi)
- Knowledge Graph (öğrenme ve hatırlama)
- Beam Search (multi-path exploration)
- Async/Parallel Processing (3x daha hızlı!) [YENİ!]
- Claude Reasoning (akıllı karar verme) [OPSIYONEL]

Kullanım:
    python main.py <başlangıç> <hedef> [--async] [--claude]

Örnek:
    python main.py Albert_Einstein Physics
    python main.py Potato Pizza --async
    python main.py Python_(programming_language) Machine_learning --async --claude
"""

import sys
import asyncio
from src.semantic_navigator import SemanticNavigator


def print_usage():
    """Kullanım bilgisini göster."""
    print("=" * 70)
    print("🌐 WIKIPEDIA PATHFINDER v4.1.0 (ML Integration)")
    print("=" * 70)
    print("\nKullanım:")
    print("  python main.py <başlangıç> <hedef> [--async] [--claude] [--ml]")
    print("\nÖrnekler:")
    print("  python main.py Albert_Einstein Physics")
    print("  python main.py Potato Pizza --async")
    print("  python main.py Python_(programming_language) Machine_learning --async --ml")
    print("  python main.py Porsche Serik_Akhmetov_Government --async --claude --ml")
    print("\nOpsiyonel Flagler:")
    print("  --async     Async/parallel processing (3x daha hızlı!) [ÖNERİLİR]")
    print("  --claude    Claude reasoning kullan (daha akıllı, ANTHROPIC_API_KEY gerekli)")
    print("  --ml        ML-based link scoring (Phase 2, model gerekli) [YENİ!]")
    print("\nNot:")
    print("  • Sayfa isimleri Wikipedia URL'indeki /wiki/ sonrası kısım")
    print("  • Boşluklar yerine _ kullanın")
    print("  • Parantez içeren isimler: Python_(programming_language)")
    print("  • --async flag'i beam search'te 2-3x hızlanma sağlar")
    print("  • --ml flag'i için önce model train edin: python train_ml_model.py --quick")
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
    use_claude = "--claude" in sys.argv
    use_ml = "--ml" in sys.argv

    # Başlık
    print("\n" + "=" * 70)
    print("🌐 WIKIPEDIA PATHFINDER v4.1.0 (ML Integration)")
    print("=" * 70)
    print(f"\n📍 Başlangıç: {start_page}")
    print(f"🎯 Hedef: {target_page}")
    
    # Mode bilgisi
    mode_parts = []
    if use_async:
        mode_parts.append("⚡ Async")
    if use_claude:
        mode_parts.append("🧠 Claude")
    if use_ml:
        mode_parts.append("🤖 ML")
    if not mode_parts:
        mode_parts.append("🔮 Beam Search")
    
    print(f"🚀 Mode: {' + '.join(mode_parts)}")
    print("\n" + "=" * 70)

    # Navigator oluştur
    try:
        navigator = SemanticNavigator(
            verbose=True,
            use_graph=True,
            use_claude=use_claude,
            use_async=use_async,
            use_ml=use_ml
        )
    except ValueError as e:
        print(f"\n❌ Hata: {e}")
        print("\nClaude mode için:")
        print("  export ANTHROPIC_API_KEY='your-api-key'")
        print("\nML mode için:")
        print("  python train_ml_model.py --quick")
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
        # Sync mode: Hybrid search (Graph + Beam/Claude)
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

    if 'claude' in stats:
        print(f"\nClaude Reasoning:")
        print(f"  API calls: {stats['claude']['total_calls']}")
        print(f"  Total tokens: {stats['claude']['total_tokens']}")
        print(f"  Avg tokens/call: {stats['claude']['avg_tokens_per_call']:.0f}")

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
