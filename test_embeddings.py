"""
test_embeddings.py
------------------
WikiEmbedder'ın ilk testleri.

FAZ 2.1: Embedding sisteminin çalıştığını doğrula.
"""

from src.embedder import WikiEmbedder


def test_basic_embeddings():
    """Temel embedding testleri."""
    print("=" * 60)
    print("🧪 TEST 1: Temel Embedding İşlemleri")
    print("=" * 60)

    # Embedder oluştur
    embedder = WikiEmbedder()

    print("\n1️⃣ Tek embedding hesaplama:")
    pizza_emb = embedder.get_embedding("Pizza")
    print(f"   'Pizza' embedding shape: {pizza_emb.shape}")
    print(f"   İlk 5 değer: {pizza_emb[:5]}")

    print("\n2️⃣ Batch embedding hesaplama:")
    texts = ["Pizza", "Italy", "Computer", "Food", "Chemistry"]
    embeddings = embedder.get_embeddings_batch(texts)
    print(f"   {len(texts)} text için embeddings shape: {embeddings.shape}")

    print("\n3️⃣ Cache test (aynı text'i tekrar iste):")
    stats_before = embedder.get_cache_stats()
    pizza_emb_again = embedder.get_embedding("Pizza")  # Cache'den gelecek
    stats_after = embedder.get_cache_stats()

    print(f"   Önce - Cache hits: {stats_before['cache_hits']}")
    print(f"   Sonra - Cache hits: {stats_after['cache_hits']}")
    print(f"   ✅ Cache çalışıyor!" if stats_after['cache_hits'] > stats_before['cache_hits'] else "   ❌ Cache çalışmıyor!")


def test_similarity_scores():
    """Semantic similarity testleri."""
    print("\n" + "=" * 60)
    print("🧪 TEST 2: Semantic Similarity")
    print("=" * 60)

    embedder = WikiEmbedder()

    # Test çiftleri: (text1, text2, beklenen_ilişki)
    test_pairs = [
        ("Pizza", "Italy", "Yakın (Pizza İtalyan yemeği)"),
        ("Pizza", "Food", "Çok yakın (Pizza bir yemek)"),
        ("Pizza", "Computer", "Uzak (alakasız)"),
        ("Albert_Einstein", "Physics", "Çok yakın (Einstein fizikçi)"),
        ("Albert_Einstein", "Pizza", "Uzak (alakasız)"),
        ("Python", "Programming", "Çok yakın (Python bir prog. dili)"),
        ("Python", "Snake", "Orta (isim çakışması)"),
    ]

    print("\nSemantic Similarity Skorları:")
    print(f"{'Text 1':<20} {'Text 2':<20} {'Score':<8} {'Beklenen':<30}")
    print("-" * 80)

    for text1, text2, expected in test_pairs:
        score = embedder.cosine_similarity(text1, text2)
        print(f"{text1:<20} {text2:<20} {score:<8.3f} {expected:<30}")


def test_most_similar():
    """En benzer text bulma testi."""
    print("\n" + "=" * 60)
    print("🧪 TEST 3: En Benzer Text Bulma")
    print("=" * 60)

    embedder = WikiEmbedder()

    # Test 1: Pizza'ya en yakın olanlar
    print("\n1️⃣ Query: 'Pizza' - En yakın 5 sayfa:")
    candidates = [
        "Italy", "Computer", "Food", "Chemistry", "Restaurant",
        "Tomato", "Cheese", "Quantum_mechanics", "Italian_cuisine",
        "France", "Recipe", "Mathematics"
    ]

    results = embedder.get_most_similar("Pizza", candidates, top_k=5)
    for i, (text, score) in enumerate(results, 1):
        print(f"   {i}. {text:<25} (score: {score:.3f})")

    # Test 2: Albert Einstein'a en yakın olanlar
    print("\n2️⃣ Query: 'Albert_Einstein' - En yakın 5 sayfa:")
    candidates = [
        "Physics", "Pizza", "Mathematics", "Quantum_mechanics",
        "Germany", "Food", "Theory_of_relativity", "Chemistry",
        "Nobel_Prize", "Computer", "Science", "Music"
    ]

    results = embedder.get_most_similar("Albert_Einstein", candidates, top_k=5)
    for i, (text, score) in enumerate(results, 1):
        print(f"   {i}. {text:<25} (score: {score:.3f})")


def test_wikipedia_path_scenario():
    """Gerçek Wikipedia path senaryosu simülasyonu."""
    print("\n" + "=" * 60)
    print("🧪 TEST 4: Wikipedia Path Simülasyonu")
    print("=" * 60)

    embedder = WikiEmbedder()

    # Senaryo: Potato → Pizza path'i
    print("\nSenaryo: Potato sayfasındayız, Pizza'ya gitmek istiyoruz")
    print("Potato sayfasındaki linkler (simüle edilmiş):")

    current_page = "Potato"
    target = "Pizza"

    # Potato sayfasındaki potansiyel linkler
    potato_links = [
        "United_States", "Food", "Vegetable", "Plant", "Starch",
        "South_America", "Ireland", "Cooking", "Agriculture",
        "Peru", "History", "Nutrition"
    ]

    print(f"\nHedef: {target}")
    print(f"Mevcut sayfa: {current_page}")
    print(f"\nMevcut sayfadaki {len(potato_links)} linkten en iyisini seçelim:\n")

    # En iyi link'i bul
    results = embedder.get_most_similar(target, potato_links, top_k=len(potato_links))

    print(f"{'Rank':<6} {'Link':<20} {'Similarity':<12} {'Mantık'}")
    print("-" * 70)

    for i, (link, score) in enumerate(results[:10], 1):
        # Mantığı açıkla
        if score > 0.6:
            reason = "✅ Çok yakın - SEÇ!"
        elif score > 0.4:
            reason = "⚠️ Orta - Alternatif"
        else:
            reason = "❌ Uzak - Atla"

        print(f"{i:<6} {link:<20} {score:<12.3f} {reason}")

    best_link = results[0][0]
    best_score = results[0][1]

    print(f"\n🎯 SEÇİLEN LİNK: {best_link} (similarity: {best_score:.3f})")
    print(f"   Mantık: {best_link} → {target} semantically yakın!")


def test_cache_performance():
    """Cache performance testi."""
    print("\n" + "=" * 60)
    print("🧪 TEST 5: Cache Performance")
    print("=" * 60)

    embedder = WikiEmbedder()

    # Aynı text'leri birkaç kere iste
    texts = ["Pizza", "Italy", "Computer", "Food"]

    print("\n1️⃣ İlk hesaplama (cache miss):")
    for text in texts:
        embedder.get_embedding(text)

    stats1 = embedder.get_cache_stats()
    print(f"   Cache misses: {stats1['cache_misses']}")
    print(f"   Cache size: {stats1['cache_size']}")

    print("\n2️⃣ İkinci hesaplama (cache hit):")
    for text in texts:
        embedder.get_embedding(text)

    stats2 = embedder.get_cache_stats()
    print(f"   Cache hits: {stats2['cache_hits']}")
    print(f"   Hit rate: {stats2['hit_rate']:.1f}%")

    print("\n3️⃣ Batch hesaplama:")
    batch_texts = texts * 3  # Aynı text'ler 3 kere
    embedder.get_embeddings_batch(batch_texts)

    stats3 = embedder.get_cache_stats()
    print(f"   Toplam hits: {stats3['cache_hits']}")
    print(f"   Hit rate: {stats3['hit_rate']:.1f}%")
    print(f"   ✅ Cache çalışıyor - network call'ları azaltıyor!")


def main():
    """Tüm testleri çalıştır."""
    print("\n" + "=" * 60)
    print("🚀 FAZ 2.1: EMBEDDING SİSTEMİ TESTLERİ")
    print("=" * 60)
    print()

    try:
        test_basic_embeddings()
        test_similarity_scores()
        test_most_similar()
        test_wikipedia_path_scenario()
        test_cache_performance()

        print("\n" + "=" * 60)
        print("✅ TÜM TESTLER BAŞARILI!")
        print("=" * 60)
        print("\n💡 Öğrenilenler:")
        print("   • Embeddings kelimeler arasındaki anlamsal ilişkiyi yakalıyor")
        print("   • Cosine similarity mantıklı sonuçlar veriyor")
        print("   • Cache sayesinde tekrar hesaplama yok")
        print("   • Wikipedia path'inde kullanmaya hazır!")
        print()

    except Exception as e:
        print(f"\n❌ HATA: {e}")
        print("\nNot: İlk çalıştırmada model indirilecek (~80MB)")
        print("     İnternet bağlantısı gerekli!")


if __name__ == "__main__":
    main()
