#!/usr/bin/env python3
"""
kg_stats.py
-----------
Knowledge Graph istatistiklerini gösterir.

Bu script:
- KG büyümesini gösterir
- Cache hit rate
- Performans metrikleri
- Node/Edge sayıları

Kullanım:
    python kg_stats.py
    python kg_stats.py --detailed
"""

import argparse
from pathlib import Path
from src.knowledge_graph import WikiKnowledgeGraph


def print_header():
    """Başlık yazdır."""
    print("=" * 70)
    print("📊 KNOWLEDGE GRAPH İSTATİSTİKLERİ")
    print("=" * 70)


def print_basic_stats(kg):
    """Temel istatistikler."""
    print("\n📈 GENEL BİLGİLER")
    print("─" * 70)
    print(f"Öğrenilen yol sayısı: {kg.paths_learned}")
    print(f"Tekrar kullanılan yol: {kg.paths_reused}")
    print(f"Node sayısı: {kg.graph.number_of_nodes()}")
    print(f"Edge sayısı: {kg.graph.number_of_edges()}")
    
    # Cache hit rate hesapla
    total_queries = kg.paths_learned + kg.paths_reused
    if total_queries > 0:
        hit_rate = (kg.paths_reused / total_queries) * 100
        print(f"\n💾 CACHE PERFORMANSI")
        print("─" * 70)
        print(f"Toplam sorgu: {total_queries}")
        print(f"Cache hit: {kg.paths_reused} ({hit_rate:.1f}%)")
        print(f"Cache miss: {kg.paths_learned} ({100-hit_rate:.1f}%)")


def print_detailed_stats(kg):
    """Detaylı istatistikler."""
    print("\n🔍 DETAYLI ANALİZ")
    print("─" * 70)
    
    # En çok kullanılan node'lar
    if kg.graph.number_of_nodes() > 0:
        print("\n📍 En Popüler Sayfalar (Top 10):")
        node_degrees = dict(kg.graph.degree())
        top_nodes = sorted(node_degrees.items(), key=lambda x: x[1], reverse=True)[:10]
        
        for i, (node, degree) in enumerate(top_nodes, 1):
            print(f"   {i}. {node}: {degree} bağlantı")
    
    # En çok kullanılan edge'ler
    if kg.graph.number_of_edges() > 0:
        print("\n🔗 En Çok Kullanılan Yollar (Top 10):")
        edges_with_weight = []
        for u, v, data in kg.graph.edges(data=True):
            weight = data.get('weight', 1)
            count = data.get('count', 1)
            edges_with_weight.append(((u, v), count))
        
        top_edges = sorted(edges_with_weight, key=lambda x: x[1], reverse=True)[:10]
        
        for i, ((u, v), count) in enumerate(top_edges, 1):
            print(f"   {i}. {u} → {v}: {count} kez kullanıldı")
    
    # Graph yoğunluğu
    if kg.graph.number_of_nodes() > 1:
        nodes = kg.graph.number_of_nodes()
        edges = kg.graph.number_of_edges()
        max_edges = nodes * (nodes - 1)  # Directed graph
        density = (edges / max_edges) * 100 if max_edges > 0 else 0
        
        print(f"\n📊 GRAPH YOĞUNLUĞU")
        print("─" * 70)
        print(f"Mevcut edge: {edges}")
        print(f"Maksimum edge: {max_edges}")
        print(f"Yoğunluk: {density:.2f}%")


def print_file_info(kg):
    """Dosya bilgileri."""
    cache_file = Path(kg.cache_file)
    
    print(f"\n💾 DOSYA BİLGİLERİ")
    print("─" * 70)
    print(f"Dosya: {cache_file}")
    
    if cache_file.exists():
        size_bytes = cache_file.stat().st_size
        size_kb = size_bytes / 1024
        size_mb = size_kb / 1024
        
        if size_mb >= 1:
            print(f"Boyut: {size_mb:.2f} MB")
        else:
            print(f"Boyut: {size_kb:.2f} KB")
        
        print(f"Durum: ✅ Mevcut")
    else:
        print(f"Durum: ❌ Henüz oluşturulmamış")
        print(f"\nİlk aramayı yapın:")
        print(f"  python main.py Italy Rome --async")


def print_recommendations(kg):
    """Öneriler."""
    print(f"\n💡 ÖNERİLER")
    print("─" * 70)
    
    paths_learned = kg.paths_learned
    
    if paths_learned == 0:
        print("❗ Henüz hiç yol öğrenilmemiş!")
        print("\n🚀 Başlamak için:")
        print("   python auto_train.py --count 10")
    elif paths_learned < 50:
        print(f"📈 İyi başlangıç! ({paths_learned} yol)")
        print("\n🚀 Daha fazla öğrenmek için:")
        print("   python auto_train.py --count 50")
    elif paths_learned < 200:
        print(f"✅ Güzel ilerleme! ({paths_learned} yol)")
        print("\n🚀 Daha da büyütmek için:")
        print("   python auto_train.py --count 100")
    else:
        print(f"🎉 Harika! ({paths_learned} yol)")
        print("\n🚀 Sürekli büyütmek için:")
        print("   python auto_train.py --continuous")
    
    # Cache hit rate önerisi
    total_queries = kg.paths_learned + kg.paths_reused
    if total_queries > 0:
        hit_rate = (kg.paths_reused / total_queries) * 100
        
        if hit_rate < 30:
            print(f"\n💾 Cache hit rate düşük ({hit_rate:.1f}%)")
            print("   Daha fazla arama yapın, hit rate artacak!")
        elif hit_rate < 60:
            print(f"\n💾 Cache hit rate orta ({hit_rate:.1f}%)")
            print("   İyi gidiyor, devam edin!")
        else:
            print(f"\n💾 Cache hit rate yüksek ({hit_rate:.1f}%)")
            print("   Mükemmel! Sistem çok verimli çalışıyor!")


def main():
    """Ana fonksiyon."""
    parser = argparse.ArgumentParser(description='KG istatistikleri')
    parser.add_argument('--detailed', action='store_true', help='Detaylı istatistikler')
    
    args = parser.parse_args()
    
    print_header()
    
    # KG yükle
    try:
        kg = WikiKnowledgeGraph()
        
        # Temel istatistikler
        print_basic_stats(kg)
        
        # Detaylı istatistikler
        if args.detailed:
            print_detailed_stats(kg)
        
        # Dosya bilgileri
        print_file_info(kg)
        
        # Öneriler
        print_recommendations(kg)
        
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"\n❌ Hata: {e}")
        print("\nKG dosyası bulunamadı veya okunamadı.")
        print("İlk aramayı yapın:")
        print("  python main.py Italy Rome --async")
        print("\nVeya otomatik eğitim başlatın:")
        print("  python auto_train.py --count 10")


if __name__ == "__main__":
    main()