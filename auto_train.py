#!/usr/bin/env python3
"""
auto_train.py
-------------
Otomatik Knowledge Graph büyütme sistemi.

Bu script:
- Hazır sayfa çiftlerini kullanır
- Her çifti dener
- Başarılı olanları KG'ye ekler
- İstatistikleri gösterir

Kullanım:
    # 100 çift dene (önerilen)
    python auto_train.py --count 100
    
    # 50 çift dene
    python auto_train.py --count 50
    
    # Tüm çiftleri dene
    python auto_train.py --all
    
    # Sonsuz döngü (Ctrl+C ile dur)
    python auto_train.py --continuous
"""

import sys
import time
import argparse
import asyncio
from src.semantic_navigator import SemanticNavigator


# Hazır sayfa çiftleri (farklı zorluk seviyeleri)
EASY_PAIRS = [
    # Ülke → Başkent
    ("Italy", "Rome"),
    ("France", "Paris"),
    ("Germany", "Berlin"),
    ("Spain", "Madrid"),
    ("Japan", "Tokyo"),
    ("United_Kingdom", "London"),
    ("Turkey", "Ankara"),
    ("United_States", "Washington,_D.C."),
    ("China", "Beijing"),
    ("Russia", "Moscow"),
    
    # Bilim → Bilim insanı
    ("Physics", "Albert_Einstein"),
    ("Chemistry", "Marie_Curie"),
    ("Biology", "Charles_Darwin"),
    ("Mathematics", "Isaac_Newton"),
    
    # Teknoloji → Şirket
    ("Computer", "Apple_Inc."),
    ("Internet", "Google"),
    ("Smartphone", "Samsung"),
]

MEDIUM_PAIRS = [
    # Yemek → Yemek
    ("Pizza", "Pasta"),
    ("Sushi", "Ramen"),
    ("Hamburger", "Hot_dog"),
    ("Coffee", "Tea"),
    ("Chocolate", "Ice_cream"),
    
    # Spor → Spor
    ("Football", "Basketball"),
    ("Tennis", "Golf"),
    ("Swimming", "Running"),
    
    # Müzik → Müzik
    ("Rock_music", "Pop_music"),
    ("Jazz", "Blues"),
    
    # Programlama → Programlama
    ("Python_(programming_language)", "Java_(programming_language)"),
    ("JavaScript", "TypeScript"),
    
    # Hayvan → Hayvan
    ("Dog", "Cat"),
    ("Lion", "Tiger"),
    ("Elephant", "Giraffe"),
]

HARD_PAIRS = [
    # Farklı kategoriler
    ("Pizza", "Computer"),
    ("Football", "Mathematics"),
    ("Music", "Physics"),
    ("Dog", "Internet"),
    ("Coffee", "Programming"),
    ("Italy", "Sushi"),
    ("Albert_Einstein", "Pizza"),
    ("Computer", "Ancient_Rome"),
    ("Basketball", "Philosophy"),
    ("Chocolate", "Quantum_mechanics"),
]


def get_all_pairs():
    """Tüm çiftleri döndür."""
    return EASY_PAIRS + MEDIUM_PAIRS + HARD_PAIRS


def print_header():
    """Başlık yazdır."""
    print("=" * 70)
    print("🤖 OTOMATİK KG BÜYÜTME SİSTEMİ")
    print("=" * 70)


def print_stats(stats):
    """İstatistikleri yazdır."""
    print("\n" + "=" * 70)
    print("📊 İSTATİSTİKLER")
    print("=" * 70)
    
    total = stats['total']
    success = stats['success']
    failed = stats['failed']
    cached = stats['cached']
    
    print(f"\nToplam deneme: {total}")
    print(f"Başarılı: {success} ({success/total*100:.1f}%)")
    print(f"Başarısız: {failed} ({failed/total*100:.1f}%)")
    print(f"Cache hit: {cached} ({cached/total*100:.1f}%)")
    
    if success > 0:
        print(f"Ortalama adım: {stats['avg_steps']:.1f}")
        print(f"Ortalama süre: {stats['total_time']/total:.2f}s")
    
    print("=" * 70)


async def train_pair(navigator, start, target, stats, index, total):
    """Tek bir çifti dene."""
    print(f"\n[{index}/{total}] {start} → {target}")
    
    start_time = time.time()
    
    try:
        # Path bul
        result = await navigator.async_bidirectional_beam_search(
            start=start,
            target=target,
            beam_width=4,
            max_depth=6
        )
        
        elapsed = time.time() - start_time
        stats['total_time'] += elapsed
        
        if result.found:
            stats['success'] += 1
            
            # KG'ye kaydet
            if navigator.knowledge_graph and result.path:
                # Path quality: Kısa path = yüksek quality
                path_length = len(result.path) - 1
                path_quality = max(0.2, 1.0 - (path_length - 2) * 0.2)
                
                navigator.knowledge_graph.add_path(
                    result.path,
                    success=True,
                    path_quality=path_quality
                )
                navigator.knowledge_graph.save()
            
            # Cache'den mi geldi?
            if elapsed < 0.1:
                stats['cached'] += 1
                print(f"   ✅ Bulundu (CACHE): {result.steps} adım, {elapsed:.3f}s")
            else:
                stats['avg_steps'] = (stats['avg_steps'] * (stats['success']-1) + result.steps) / stats['success']
                print(f"   ✅ Bulundu: {result.steps} adım, {elapsed:.3f}s")
                print(f"   Path: {' → '.join(result.path[:5])}{'...' if len(result.path) > 5 else ''}")
        else:
            stats['failed'] += 1
            print(f"   ❌ Bulunamadı: {elapsed:.3f}s")
    
    except Exception as e:
        stats['failed'] += 1
        print(f"   ❌ Hata: {e}")
    
    stats['total'] += 1
    
    # Her 10 denemede bir özet göster
    if stats['total'] % 10 == 0:
        print("\n" + "─" * 70)
        print(f"📊 İlerleme: {stats['total']}/{total}")
        print(f"   Başarı: {stats['success']}/{stats['total']} ({stats['success']/stats['total']*100:.1f}%)")
        print(f"   Cache: {stats['cached']}/{stats['total']} ({stats['cached']/stats['total']*100:.1f}%)")
        print("─" * 70)


async def auto_train(count=None, continuous=False, use_all=False):
    """Otomatik eğitim."""
    print_header()
    
    # Çiftleri al
    all_pairs = get_all_pairs()
    
    if use_all:
        pairs = all_pairs
        print(f"\n📦 Tüm çiftler kullanılacak: {len(pairs)} çift")
    elif count:
        pairs = all_pairs[:count]
        print(f"\n📦 İlk {count} çift kullanılacak")
    else:
        pairs = all_pairs[:100]
        print(f"\n📦 İlk 100 çift kullanılacak (default - önerilen)")
    
    print(f"   Kolay: {len(EASY_PAIRS)} çift")
    print(f"   Orta: {len(MEDIUM_PAIRS)} çift")
    print(f"   Zor: {len(HARD_PAIRS)} çift")
    print("=" * 70)
    
    # Navigator oluştur
    print("\n🔧 Navigator başlatılıyor...")
    navigator = SemanticNavigator(
        verbose=False,  # Sessiz mod
        use_graph=True,
        use_async=True
    )
    print("✅ Navigator hazır!")
    
    # İstatistikler
    stats = {
        'total': 0,
        'success': 0,
        'failed': 0,
        'cached': 0,
        'avg_steps': 0,
        'total_time': 0
    }
    
    # Ana döngü
    iteration = 0
    while True:
        # Continuous değilse ve tüm çiftler denendiyse dur
        if not continuous and iteration >= len(pairs):
            break
        
        # Çifti al
        if continuous:
            # Sonsuz döngüde rastgele seç
            import random
            pair = random.choice(all_pairs)
        else:
            pair = pairs[iteration]
        
        start, target = pair
        
        # Dene
        await train_pair(navigator, start, target, stats, iteration + 1, len(pairs) if not continuous else "∞")
        
        iteration += 1
        
        # Rate limiting
        await asyncio.sleep(0.5)
    
    # Async scraper'ı kapat
    if navigator.async_scraper:
        await navigator.async_scraper.close()
    
    # Final istatistikler
    print_stats(stats)
    
    # KG istatistikleri
    if navigator.knowledge_graph:
        kg = navigator.knowledge_graph
        print(f"\n📈 KNOWLEDGE GRAPH")
        print(f"   Öğrenilen yol: {kg.paths_learned}")
        print(f"   Node sayısı: {kg.graph.number_of_nodes()}")
        print(f"   Edge sayısı: {kg.graph.number_of_edges()}")
        print(f"   Dosya: cache/wiki_graph.pkl")
        print("=" * 70)


def main():
    """Ana fonksiyon."""
    parser = argparse.ArgumentParser(description='Otomatik KG büyütme sistemi')
    parser.add_argument('--count', type=int, help='Kaç çift denenecek')
    parser.add_argument('--all', action='store_true', help='Tüm çiftleri dene')
    parser.add_argument('--continuous', action='store_true', help='Sonsuz döngü (Ctrl+C ile dur)')
    
    args = parser.parse_args()
    
    try:
        asyncio.run(auto_train(
            count=args.count,
            continuous=args.continuous,
            use_all=args.all
        ))
    except KeyboardInterrupt:
        print("\n\n⚠️  Kullanıcı tarafından durduruldu!")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Hata: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()