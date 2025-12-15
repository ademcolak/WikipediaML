#!/usr/bin/env python3
"""
auto_train_dynamic.py
---------------------
Dinamik olarak Wikipedia'dan rastgele sayfalar çekip eğitir.

Kullanım:
    # 1000 rastgele çift
    python auto_train_dynamic.py --count 1000
    
    # Sonsuz döngü
    python auto_train_dynamic.py --continuous
"""

import sys
import time
import argparse
import asyncio
import random
from src.semantic_navigator import SemanticNavigator
from src.scraper import WikipediaScraper


def get_random_wikipedia_pages(count=2, max_attempts=50):
    """Wikipedia'dan rastgele sayfalar al - agresif mod."""
    import requests
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    pages = []
    
    def fetch_one():
        """Tek bir rastgele sayfa çek."""
        try:
            response = requests.get(
                'https://en.wikipedia.org/wiki/Special:Random',
                timeout=3,
                allow_redirects=True,
                headers={'User-Agent': 'WikipediaML/1.0'}
            )
            
            if response.status_code == 200:
                page_title = response.url.split('/wiki/')[-1]
                
                # Özel sayfaları filtrele
                if (not page_title.startswith(('Special:', 'Wikipedia:', 'Help:',
                                               'Category:', 'Template:', 'File:',
                                               'Talk:', 'User:', 'Portal:', 'Draft:'))
                    and len(page_title) > 2
                    and ':' not in page_title):  # Tüm özel namespace'leri engelle
                    return page_title
        except:
            pass
        return None
    
    # Paralel olarak daha fazla sayfa çek
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_one) for _ in range(max_attempts)]
        
        for future in as_completed(futures):
            result = future.result()
            if result and result not in pages:
                pages.append(result)
                if len(pages) >= count:
                    break
    
    return pages


def print_stats(stats):
    """İstatistikleri yazdır."""
    print("\n" + "=" * 70)
    print("📊 İSTATİSTİKLER")
    print("=" * 70)
    
    total = stats['total']
    success = stats['success']
    failed = stats['failed']
    
    print(f"\nToplam deneme: {total}")
    print(f"Başarılı: {success} ({success/total*100:.1f}%)")
    print(f"Başarısız: {failed} ({failed/total*100:.1f}%)")
    
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
                path_length = len(result.path) - 1
                path_quality = max(0.2, 1.0 - (path_length - 2) * 0.2)
                
                navigator.knowledge_graph.add_path(
                    result.path,
                    success=True,
                    path_quality=path_quality
                )
                navigator.knowledge_graph.save()
            
            stats['avg_steps'] = (stats['avg_steps'] * (stats['success']-1) + result.steps) / stats['success']
            print(f"   ✅ Bulundu: {result.steps} adım, {elapsed:.3f}s")
            print(f"   Path: {' → '.join(result.path[:5])}{'...' if len(result.path) > 5 else ''}")
        else:
            stats['failed'] += 1
            print(f"   ❌ Bulunamadı: {elapsed:.3f}s")
        
        stats['total'] += 1
        
        # Her 10 denemede bir ilerleme göster
        if stats['total'] % 10 == 0:
            print("\n" + "─" * 70)
            print(f"📊 İlerleme: {stats['total']}/{total if total != '∞' else '∞'}")
            print(f"   Başarı: {stats['success']}/{stats['total']} ({stats['success']/stats['total']*100:.1f}%)")
            print("─" * 70)
    
    except Exception as e:
        print(f"   ⚠️ Hata: {e}")
        stats['failed'] += 1
        stats['total'] += 1


async def auto_train_dynamic(count=None, continuous=False):
    """Dinamik otomatik eğitim."""
    print("\n" + "=" * 70)
    print("🤖 DİNAMİK OTOMATİK KG BÜYÜTME SİSTEMİ")
    print("=" * 70)
    
    if continuous:
        print("\n🔄 Sonsuz döngü modu (Ctrl+C ile dur)")
        print("   Rastgele Wikipedia sayfaları kullanılacak")
    else:
        count = count if count else 100
        print(f"\n📦 {count} rastgele çift kullanılacak")
    
    print("=" * 70)
    
    # Navigator oluştur
    print("\n🔧 Navigator başlatılıyor...")
    navigator = SemanticNavigator(
        verbose=False,
        use_graph=True,
        use_async=True
    )
    print("✅ Navigator hazır!")
    
    # İstatistikler
    stats = {
        'total': 0,
        'success': 0,
        'failed': 0,
        'avg_steps': 0,
        'total_time': 0
    }
    
    # Ana döngü
    iteration = 0
    target_count = count if count is not None else 100
    
    while True:
        # Continuous değilse ve count'a ulaştıysa dur
        if not continuous and iteration >= target_count:
            break
        
        # Rastgele 2 sayfa al - retry mekanizması
        pages = []
        retry = 0
        max_retries = 3
        
        while len(pages) < 2 and retry < max_retries:
            print(f"\n🎲 Rastgele sayfalar çekiliyor... (deneme {retry + 1}/{max_retries})")
            pages = get_random_wikipedia_pages(count=2, max_attempts=50)
            
            if len(pages) < 2:
                retry += 1
                print(f"   ⚠️ Sadece {len(pages)} sayfa alındı, tekrar deneniyor...")
                await asyncio.sleep(2)
        
        if len(pages) < 2:
            print("   ❌ Yeterli sayfa alınamadı, bu iterasyon atlanıyor...")
            continue
        
        start, target = pages[0], pages[1]
        
        # Dene
        await train_pair(
            navigator, 
            start, 
            target, 
            stats, 
            iteration + 1, 
            count if not continuous else "∞"
        )
        
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
    parser = argparse.ArgumentParser(description='Dinamik otomatik KG büyütme')
    parser.add_argument('--count', type=int, help='Kaç çift denenecek (default: 100)')
    parser.add_argument('--continuous', action='store_true', help='Sonsuz döngü')
    
    args = parser.parse_args()
    
    try:
        asyncio.run(auto_train_dynamic(
            count=args.count,
            continuous=args.continuous
        ))
    except KeyboardInterrupt:
        print("\n\n⚠️  İşlem kullanıcı tarafından durduruldu.")
        sys.exit(0)


if __name__ == "__main__":
    main()