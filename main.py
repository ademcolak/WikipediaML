#!/usr/bin/env python3
"""
Wikipedia PathFinder
--------------------
Bir Wikipedia sayfasından diğerine en kısa yolu bulur.

Sistem:
- Semantic embeddings (anlam bazlı link seçimi)
- Knowledge Graph (öğrenme ve hatırlama)
- Hybrid Navigator (KG + Embedding + LLM) - 10K+ edge için
- Async/Parallel Processing (3x daha hızlı!)

Kullanım:
    python main.py <başlangıç> <hedef> [--async] [--hybrid] [--llm]

Örnek:
    python main.py Albert_Einstein Physics
    python main.py Potato Pizza --async
    python main.py Italy Rome --hybrid
    python main.py Italy Rome --hybrid --llm
"""

import sys
import asyncio
from src.semantic_navigator import SemanticNavigator


def print_usage():
    """Kullanım bilgisini göster."""
    print("=" * 70)
    print("🌐 WIKIPEDIA PATHFINDER v5.1.0 (Hybrid Navigator)")
    print("=" * 70)
    print("\nKullanım:")
    print("  python main.py <başlangıç> <hedef> [flags]")
    print("\nÖrnekler:")
    print("  python main.py Albert_Einstein Physics")
    print("  python main.py Potato Pizza --async")
    print("  python main.py Italy Rome --hybrid")
    print("  python main.py Italy Rome --hybrid --llm")
    print("\nOpsiyonel Flagler:")
    print("  --async     Async/parallel processing (3x daha hızlı!)")
    print("  --hybrid    Hybrid Navigator (KG + Embedding) [10K+ edge için]")
    print("  --llm       LLM Navigator (Claude API) [--hybrid ile birlikte]")
    print("\nMod Kombinasyonları:")
    print("  • Varsayılan: Beam Search (semantic only)")
    print("  • --async: Async Bidirectional Beam Search (3x hızlı)")
    print("  • --hybrid: KG + Embedding (%60-70 doğruluk)")
    print("  • --hybrid --llm: KG + Embedding + LLM (%70-80 doğruluk)")
    print("\nNot:")
    print("  • Sayfa isimleri Wikipedia URL'indeki /wiki/ sonrası kısım")
    print("  • Boşluklar yerine _ kullanın")
    print("  • Parantez içeren isimler: Python_(programming_language)")
    print("  • --llm flag'i ANTHROPIC_API_KEY gerektirir (.env dosyası)")
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
    use_hybrid = "--hybrid" in sys.argv
    use_llm = "--llm" in sys.argv

    # Başlık
    print("\n" + "=" * 70)
    print("🌐 WIKIPEDIA PATHFINDER v5.1.0 (Hybrid Navigator)")
    print("=" * 70)
    print(f"\n📍 Başlangıç: {start_page}")
    print(f"🎯 Hedef: {target_page}")
    
    # Mode bilgisi
    modes = []
    if use_async:
        modes.append("⚡ Async")
    if use_hybrid:
        modes.append("🧬 Hybrid")
    if use_llm:
        modes.append("🤖 LLM")
    
    mode_str = " + ".join(modes) if modes else "🔮 Standard"
    print(f"🚀 Mode: {mode_str}")
    
    # LLM uyarısı
    if use_llm and not use_hybrid:
        print("\n⚠️  --llm flag'i --hybrid ile birlikte kullanılmalı")
        print("   --hybrid flag'i otomatik ekleniyor...")
        use_hybrid = True
    
    print("\n" + "=" * 70)

    # Navigator oluştur
    try:
        navigator = SemanticNavigator(
            verbose=True,
            use_graph=True,
            use_async=use_async,
            use_hybrid=use_hybrid,
            use_llm=use_llm
        )
    except ValueError as e:
        print(f"\n❌ Hata: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Initialization error: {e}")
        if use_llm:
            print("\n💡 LLM mode için:")
            print("   1. ANTHROPIC_API_KEY .env dosyasında olmalı")
            print("   2. pip install anthropic")
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
        # Sync mode: Hybrid search (Graph + Beam/Hybrid Navigator)
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
    
    # Hybrid Navigator stats
    if use_hybrid and navigator.hybrid_navigator:
        hybrid_stats = navigator.hybrid_navigator.get_stats()
        print(f"\nHybrid Navigator:")
        print(f"  Total queries: {hybrid_stats.get('total_queries', 0)}")
        print(f"  KG hits: {hybrid_stats.get('kg_hits', 0)}")
        print(f"  Embedding uses: {hybrid_stats.get('embedding_uses', 0)}")
        print(f"  LLM uses: {hybrid_stats.get('llm_uses', 0)}")
        
        if 'llm_stats' in hybrid_stats:
            llm_stats = hybrid_stats['llm_stats']
            print(f"  LLM cost: ${llm_stats.get('total_cost', 0):.4f}")

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
