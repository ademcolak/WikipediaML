#!/usr/bin/env python3
"""
kg_stats.py
-----------
Knowledge Graph istatistiklerini gösterir.

WikipediaML v6.0.0 - Performance & Algorithms Update

Bu script:
- KG büyümesini gösterir
- Cache hit rate ve performans
- Node/Edge sayıları ve analiz
- Popüler sayfalar ve yollar
- Sistem önerileri

Kullanım:
    python kg_stats.py                    # Temel istatistikler
    python kg_stats.py --detailed         # Detaylı analiz
    python kg_stats.py --export stats.txt # Dosyaya kaydet
"""

import argparse
from pathlib import Path
from src.knowledge_graph import WikiKnowledgeGraph
import sys


def print_header():
    """Başlık yazdır."""
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "📊 KNOWLEDGE GRAPH İSTATİSTİKLERİ" + " " * 16 + "║")
    print("║" + " " * 20 + "WikipediaML v6.0.0" + " " * 29 + "║")
    print("╚" + "═" * 68 + "╝")


def print_section_header(title, emoji=""):
    """Bölüm başlığı."""
    print(f"\n{emoji} {title}")
    print("─" * 70)


def format_number(num):
    """Sayıyı formatla."""
    if num >= 1_000_000:
        return f"{num/1_000_000:.2f}M"
    elif num >= 1_000:
        return f"{num/1_000:.2f}K"
    return str(num)


def get_progress_bar(percentage, width=30):
    """İlerleme çubuğu oluştur."""
    filled = int(width * percentage / 100)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {percentage:.1f}%"


def print_basic_stats(kg):
    """Temel istatistikler."""
    print_section_header("GENEL BİLGİLER", "📈")
    
    nodes = kg.graph.number_of_nodes()
    edges = kg.graph.number_of_edges()
    paths_learned = kg.paths_learned
    paths_reused = kg.paths_reused
    
    print(f"{'Öğrenilen yol sayısı:':<30} {paths_learned:>10,}")
    print(f"{'Tekrar kullanılan yol:':<30} {paths_reused:>10,}")
    print(f"{'Node sayısı (sayfalar):':<30} {nodes:>10,}")
    print(f"{'Edge sayısı (bağlantılar):':<30} {edges:>10,}")
    
    # Ortalama bağlantı
    if nodes > 0:
        avg_connections = edges / nodes
        print(f"{'Ortalama bağlantı/sayfa:':<30} {avg_connections:>10.2f}")
    
    # Cache hit rate hesapla
    total_queries = paths_learned + paths_reused
    if total_queries > 0:
        hit_rate = (paths_reused / total_queries) * 100
        
        print_section_header("CACHE PERFORMANSI", "💾")
        print(f"{'Toplam sorgu:':<30} {total_queries:>10,}")
        print(f"{'Cache hit:':<30} {paths_reused:>10,} ({hit_rate:.1f}%)")
        print(f"{'Cache miss:':<30} {paths_learned:>10,} ({100-hit_rate:.1f}%)")
        print(f"\n{get_progress_bar(hit_rate)}")
        
        # Hit rate değerlendirmesi
        if hit_rate < 30:
            print("   ⚠️  Düşük - Daha fazla arama yapın")
        elif hit_rate < 60:
            print("   ✅ Orta - İyi gidiyor")
        else:
            print("   🎉 Yüksek - Mükemmel!")


def print_detailed_stats(kg):
    """Detaylı istatistikler."""
    print_section_header("DETAYLI ANALİZ", "🔍")
    
    # En çok kullanılan node'lar
    if kg.graph.number_of_nodes() > 0:
        print("\n📍 En Popüler Sayfalar (Top 15):")
        node_degrees = dict(kg.graph.degree())
        top_nodes = sorted(node_degrees.items(), key=lambda x: x[1], reverse=True)[:15]
        
        max_degree = top_nodes[0][1] if top_nodes else 1
        
        for i, (node, degree) in enumerate(top_nodes, 1):
            # İlerleme çubuğu
            bar_width = int(30 * degree / max_degree)
            bar = "█" * bar_width + "░" * (30 - bar_width)
            
            # Node ismini kısalt
            display_name = node[:35] + "..." if len(node) > 35 else node
            print(f"   {i:2d}. {display_name:<40} [{bar}] {degree:>4}")
    
    # En çok kullanılan edge'ler
    if kg.graph.number_of_edges() > 0:
        print("\n🔗 En Çok Kullanılan Yollar (Top 10):")
        edges_with_weight = []
        for u, v, data in kg.graph.edges(data=True):
            count = data.get('count', 1)
            edges_with_weight.append(((u, v), count))
        
        top_edges = sorted(edges_with_weight, key=lambda x: x[1], reverse=True)[:10]
        max_count = top_edges[0][1] if top_edges else 1
        
        for i, ((u, v), count) in enumerate(top_edges, 1):
            # İlerleme çubuğu
            bar_width = int(20 * count / max_count)
            bar = "█" * bar_width + "░" * (20 - bar_width)
            
            # İsimleri kısalt
            u_short = u[:20] + "..." if len(u) > 20 else u
            v_short = v[:20] + "..." if len(v) > 20 else v
            
            print(f"   {i:2d}. {u_short:<23} → {v_short:<23} [{bar}] {count:>3}x")
    
    # Graph yoğunluğu ve metrikleri
    if kg.graph.number_of_nodes() > 1:
        nodes = kg.graph.number_of_nodes()
        edges = kg.graph.number_of_edges()
        max_edges = nodes * (nodes - 1)  # Directed graph
        density = (edges / max_edges) * 100 if max_edges > 0 else 0
        
        print_section_header("GRAPH METRİKLERİ", "📊")
        print(f"{'Mevcut edge:':<30} {format_number(edges):>10}")
        print(f"{'Maksimum edge:':<30} {format_number(max_edges):>10}")
        print(f"{'Yoğunluk:':<30} {density:>9.4f}%")
        print(f"\n{get_progress_bar(density)}")
        
        # Kapsama tahmini (Wikipedia'da ~6M sayfa var)
        wikipedia_pages = 6_000_000
        coverage = (nodes / wikipedia_pages) * 100
        print(f"\n{'Wikipedia kapsamı:':<30} {coverage:>9.4f}%")
        print(f"{'Kapsanan sayfa:':<30} {format_number(nodes):>10} / {format_number(wikipedia_pages)}")


def print_file_info(kg):
    """Dosya bilgileri."""
    cache_file = Path(kg.cache_file)
    
    print_section_header("DOSYA BİLGİLERİ", "💾")
    print(f"{'Dosya:':<30} {cache_file}")
    
    if cache_file.exists():
        size_bytes = cache_file.stat().st_size
        size_kb = size_bytes / 1024
        size_mb = size_kb / 1024
        
        if size_mb >= 1:
            print(f"{'Boyut:':<30} {size_mb:>10.2f} MB")
        else:
            print(f"{'Boyut:':<30} {size_kb:>10.2f} KB")
        
        print(f"{'Durum:':<30} {'✅ Mevcut':>10}")
    else:
        print(f"{'Durum:':<30} {'❌ Yok':>10}")
        print(f"\n💡 İlk kullanım:")
        print(f"   python main.py Potato Pizza")
        print(f"   python main.py Italy Rome --beam")


def print_recommendations(kg):
    """Öneriler ve hedefler."""
    print_section_header("ÖNERİLER VE HEDEFLER", "💡")
    
    paths_learned = kg.paths_learned
    nodes = kg.graph.number_of_nodes()
    edges = kg.graph.number_of_edges()
    
    # Eğitim durumu
    if paths_learned == 0:
        print("❗ Henüz hiç yol öğrenilmemiş!")
        print("\n🚀 Başlamak için:")
        print("   # Basit kullanım")
        print("   python main.py Potato Pizza")
        print("   python main.py Italy Rome --beam")
        print("\n   # Eğitim (önerilen)")
        print("   python train.py --strategy strategic --iterations 50")
    elif paths_learned < 100:
        print(f"📈 İyi başlangıç! ({paths_learned:,} yol)")
        print("\n🎯 Hedef: 100 yol")
        remaining = 100 - paths_learned
        print(f"   Kalan: {remaining} yol")
        print("\n🚀 Devam etmek için:")
        print("   python train.py --strategy strategic --iterations 50")
    elif paths_learned < 500:
        print(f"✅ Güzel ilerleme! ({paths_learned:,} yol)")
        print("\n🎯 Hedef: 500 yol")
        remaining = 500 - paths_learned
        print(f"   Kalan: {remaining} yol")
        print("\n🚀 Daha da büyütmek için:")
        print("   python train.py --strategy strategic --workers 2 --iterations 200")
    elif paths_learned < 1000:
        print(f"🎉 Harika! ({paths_learned:,} yol)")
        print("\n🎯 Hedef: 1,000 yol")
        remaining = 1000 - paths_learned
        print(f"   Kalan: {remaining} yol")
        print("\n🚀 Sürekli büyütmek için:")
        print("   python train.py --strategy strategic --workers 3 --iterations 500")
    elif paths_learned < 5000:
        print(f"🎉 Harika! ({paths_learned:,} yol)")
        print("\n🎯 Hedef: 5,000 yol")
        remaining = 5000 - paths_learned
        print(f"   Kalan: {remaining} yol")
        print("\n🚀 Sürekli büyütmek için:")
        print("   python train.py --strategy strategic --workers 3 --iterations 1000")
    elif paths_learned < 10000:
        print(f"🏆 Mükemmel! ({paths_learned:,} yol)")
        print("\n🎯 Hedef: 10,000 yol")
        remaining = 10000 - paths_learned
        print(f"   Kalan: {remaining} yol")
        print("\n🚀 Paralel eğitim için:")
        print("   python train.py --strategy strategic --workers 4 --iterations 2000")
    else:
        print(f"🏆🏆🏆 OLAĞANÜSTÜ! ({paths_learned:,} yol)")
        print("\n🎉 10,000+ yol - Profesyonel seviye!")
        print("\n💡 Sistem artık çok güçlü:")
        print("   • Yüksek cache hit rate")
        print("   • Hızlı path bulma")
        print("   • Geniş Wikipedia kapsamı")
        print("\n🚀 Devam etmek için:")
        print("   python train.py --strategy strategic --workers 5 --iterations 5000")
    
    # Performans tahmini
    print("\n📊 Sistem Performansı:")
    if edges < 1000:
        print(f"   KG Cache Hit Rate: ~{(edges/1000)*10:.0f}%")
        print(f"   Semantic Search: %75-85 doğruluk")
        print(f"   Hedef: 1,000 edge için daha fazla eğitim")
    elif edges < 5000:
        hit_rate = 10 + (edges / 5000) * 20
        print(f"   KG Cache Hit Rate: ~{hit_rate:.0f}%")
        print(f"   Semantic Search: %75-85 doğruluk")
        print(f"   Hedef: 5,000 edge için daha fazla eğitim")
    elif edges < 10000:
        hit_rate = 30 + (edges / 10000) * 30
        print(f"   KG Cache Hit Rate: ~{hit_rate:.0f}%")
        print(f"   Hybrid Navigator: Aktif")
        print(f"   Hedef: 10,000 edge (Hybrid threshold)")
    else:
        hit_rate = min(80, 60 + (edges / 50000) * 20)
        print(f"   KG Cache Hit Rate: ~{hit_rate:.0f}%")
        print(f"   Hybrid Navigator: Optimize")
        print(f"   🎉 Mükemmel kapsama!")
    
    # Algoritma önerileri
    print("\n🎯 Algoritma Önerileri:")
    print("   • Greedy Search: Hızlı, iyi doğruluk")
    print("   • Beam Search: Multi-path, daha az tıklama")
    print("   • A* Search: Optimal path, garantili en kısa")
    if edges >= 10000:
        print("   • Hybrid Navigator: KG + Embedding (önerilen)")
    
    # Görselleştirme önerisi
    if nodes >= 10:
        print("\n🎨 Görselleştirme:")
        print("   python visualize_kg_3d.py")
        if nodes > 100:
            print("   python visualize_kg_3d.py --max-nodes 100")


def export_stats(kg, filename):
    """İstatistikleri dosyaya kaydet."""
    with open(filename, 'w', encoding='utf-8') as f:
        # Başlık
        f.write("=" * 70 + "\n")
        f.write("KNOWLEDGE GRAPH İSTATİSTİKLERİ\n")
        f.write("=" * 70 + "\n\n")
        
        # Temel bilgiler
        f.write("GENEL BİLGİLER\n")
        f.write("-" * 70 + "\n")
        f.write(f"Öğrenilen yol sayısı: {kg.paths_learned:,}\n")
        f.write(f"Tekrar kullanılan yol: {kg.paths_reused:,}\n")
        f.write(f"Node sayısı: {kg.graph.number_of_nodes():,}\n")
        f.write(f"Edge sayısı: {kg.graph.number_of_edges():,}\n\n")
        
        # Cache performansı
        total_queries = kg.paths_learned + kg.paths_reused
        if total_queries > 0:
            hit_rate = (kg.paths_reused / total_queries) * 100
            f.write("CACHE PERFORMANSI\n")
            f.write("-" * 70 + "\n")
            f.write(f"Toplam sorgu: {total_queries:,}\n")
            f.write(f"Cache hit: {kg.paths_reused:,} ({hit_rate:.1f}%)\n")
            f.write(f"Cache miss: {kg.paths_learned:,} ({100-hit_rate:.1f}%)\n\n")
        
        # Top nodes
        if kg.graph.number_of_nodes() > 0:
            f.write("EN POPÜLER SAYFALAR (Top 20)\n")
            f.write("-" * 70 + "\n")
            node_degrees = dict(kg.graph.degree())
            top_nodes = sorted(node_degrees.items(), key=lambda x: x[1], reverse=True)[:20]
            for i, (node, degree) in enumerate(top_nodes, 1):
                f.write(f"{i:2d}. {node}: {degree} bağlantı\n")
    
    print(f"\n✅ İstatistikler kaydedildi: {filename}")


def main():
    """Ana fonksiyon."""
    parser = argparse.ArgumentParser(description='KG istatistikleri')
    parser.add_argument('--detailed', action='store_true', help='Detaylı istatistikler')
    parser.add_argument('--export', type=str, help='İstatistikleri dosyaya kaydet')
    
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
        
        # Export
        if args.export:
            export_stats(kg, args.export)
        
        print("\n" + "═" * 70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Hata: {e}")
        print("\n💡 KG dosyası bulunamadı veya okunamadı.")
        print("\n🚀 Başlamak için:")
        print("  # Basit kullanım")
        print("  python main.py Potato Pizza")
        print("  python main.py Italy Rome --beam")
        print("\n  # Eğitim (önerilen)")
        print("  python train.py --strategy strategic --iterations 50")
        print("\n📖 Detaylı bilgi:")
        print("  docs/PROJECT_STATUS.md")
        print("  docs/USAGE.md")
        sys.exit(1)


if __name__ == "__main__":
    main()