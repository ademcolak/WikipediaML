#!/usr/bin/env python3
"""
fix_paths_count.py
------------------
Mevcut graph'taki yanlış paths_learned sayısını düzelt.

Bu script:
- Mevcut graph'ı yükler
- paths_learned'ı gerçek edge sayısına göre düzeltir
- Graph'ı tekrar kaydeder
"""

import pickle
from pathlib import Path


def fix_paths_count():
    """Graph'taki paths_learned sayısını düzelt."""
    cache_file = Path("cache/wiki_graph.pkl")
    
    if not cache_file.exists():
        print("❌ Graph dosyası bulunamadı: cache/wiki_graph.pkl")
        return
    
    print("\n" + "=" * 70)
    print("🔧 PATHS_LEARNED SAYACI DÜZELTİLİYOR")
    print("=" * 70)
    
    # Graph'ı yükle
    print("\n📂 Graph yükleniyor...")
    try:
        with open(cache_file, 'rb') as f:
            data = pickle.load(f)
    except Exception as e:
        print(f"❌ Yükleme hatası: {e}")
        return
    
    graph = data.get('graph')
    if not graph:
        print("❌ Graph verisi bulunamadı!")
        return
    
    # Mevcut değerler
    old_paths_learned = data.get('paths_learned', 0)
    nodes = graph.number_of_nodes()
    edges = graph.number_of_edges()
    
    print(f"\n📊 Mevcut Durum:")
    print(f"   Paths learned (YANLIŞ): {old_paths_learned:,}")
    print(f"   Node sayısı: {nodes:,}")
    print(f"   Edge sayısı: {edges:,}")
    
    # Doğru değer = edge sayısı
    # Çünkü her edge bir unique path segment'i temsil eder
    correct_paths_learned = edges
    
    print(f"\n✅ Düzeltilmiş Değer:")
    print(f"   Paths learned (DOĞRU): {correct_paths_learned:,}")
    print(f"   Fark: {old_paths_learned - correct_paths_learned:,}")
    
    # Açıklama
    print(f"\n💡 Açıklama:")
    print(f"   Eski değer ({old_paths_learned:,}) yanlıştı çünkü:")
    print(f"   - Paralel worker'lar aynı path'leri öğrendi")
    print(f"   - Merge sırasında sayılar toplandı (overlap hesaba katılmadı)")
    print(f"   ")
    print(f"   Doğru değer ({correct_paths_learned:,}) çünkü:")
    print(f"   - Her edge bir unique path segment'i (A→B)")
    print(f"   - Graph'ta {edges:,} unique edge var")
    print(f"   - Dolayısıyla {edges:,} unique path öğrenilmiş")
    
    # Backup oluştur
    backup_file = Path("cache/wiki_graph_backup_before_fix.pkl")
    print(f"\n💾 Backup oluşturuluyor: {backup_file}")
    try:
        import shutil
        shutil.copy2(cache_file, backup_file)
        print(f"   ✅ Backup oluşturuldu")
    except Exception as e:
        print(f"   ⚠️ Backup oluşturulamadı: {e}")
    
    # Düzeltilmiş veriyi kaydet
    print(f"\n💾 Düzeltilmiş graph kaydediliyor...")
    data['paths_learned'] = correct_paths_learned
    
    try:
        with open(cache_file, 'wb') as f:
            pickle.dump(data, f)
        print(f"   ✅ Kaydedildi!")
    except Exception as e:
        print(f"   ❌ Kaydetme hatası: {e}")
        return
    
    print("\n" + "=" * 70)
    print("✅ DÜZELTME TAMAMLANDI!")
    print("=" * 70)
    print(f"\n📊 Yeni İstatistikler:")
    print(f"   python kg_stats.py")
    print(f"\n🎨 Görselleştirme:")
    print(f"   python visualize_kg_3d.py")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    fix_paths_count()