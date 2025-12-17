#!/usr/bin/env python3
"""
merge_graphs.py
---------------
Paralel worker'ların oluşturduğu graph dosyalarını birleştirir.

Kullanım:
    # Tüm worker graph'larını birleştir
    python merge_graphs.py
    
    # Belirli worker'ları birleştir
    python merge_graphs.py --workers 1 2 3
    
    # Çıktı dosyasını belirt
    python merge_graphs.py --output cache/wiki_graph_merged.pkl
"""

import argparse
import pickle
import networkx as nx
from pathlib import Path
from collections import defaultdict


def find_worker_graphs(cache_dir: str = "cache") -> list[Path]:
    """Cache dizinindeki tüm worker graph dosyalarını bul."""
    cache_path = Path(cache_dir)
    if not cache_path.exists():
        return []
    
    # wiki_graph_worker_*.pkl dosyalarını bul
    worker_files = list(cache_path.glob("wiki_graph_worker_*.pkl"))
    worker_files.sort()  # Sıralı listele
    
    return worker_files


def load_graph(file_path: Path) -> dict | None:
    """Graph dosyasını yükle."""
    try:
        with open(file_path, 'rb') as f:
            data = pickle.load(f)
            return data
    except Exception as e:
        print(f"⚠️ {file_path} yüklenemedi: {e}")
        return None


def merge_graphs(graph_files: list[Path], output_file: str = "cache/wiki_graph.pkl") -> dict | None:
    """
    Birden fazla graph'ı birleştir.
    
    Birleştirme kuralları:
    - Aynı edge varsa: weight'leri topla, count'ları topla
    - Farklı edge'ler: Hepsini ekle
    - Node'lar: Tüm unique node'ları ekle
    - Mevcut graph varsa: Onu da dahil et (otomatik koruma)
    """
    print("\n" + "=" * 70)
    print("🔗 GRAPH BİRLEŞTİRME SİSTEMİ")
    print("=" * 70)
    
    # Mevcut graph'ı kontrol et
    output_path = Path(output_file)
    existing_graph = None
    
    if output_path.exists():
        print(f"\n📂 Mevcut graph bulundu: {output_file}")
        print("   🔒 Otomatik koruma aktif - mevcut graph dahil edilecek")
        
        existing_data = load_graph(output_path)
        if existing_data:
            existing_graph = existing_data.get('graph')
            if existing_graph:
                print(f"   ✅ Mevcut graph yüklendi:")
                print(f"      • Nodes: {existing_graph.number_of_nodes()}")
                print(f"      • Edges: {existing_graph.number_of_edges()}")
                print(f"      • Paths learned: {existing_data.get('paths_learned', 0)}")
    
    if not graph_files:
        print("\n❌ Birleştirilecek worker graph dosyası bulunamadı!")
        print("   Worker graph'ları oluşturmak için:")
        print("   python auto_train_parallel.py --worker-id 1 --count 100")
        
        if existing_graph:
            print("\n💡 Mevcut graph korundu, değişiklik yapılmadı.")
        return None
    
    print(f"\n📦 {len(graph_files)} worker graph dosyası bulundu:")
    for gf in graph_files:
        print(f"   • {gf}")
    
    # Merged graph oluştur
    merged_graph = nx.DiGraph()
    
    # İstatistikler
    # NOT: paths_learned'ı toplamıyoruz çünkü worker'lar aynı path'leri öğrenmiş olabilir
    # Bunun yerine merge sonunda unique edge sayısını kullanacağız
    total_stats = {
        'paths_learned': 0,  # Merge sonunda hesaplanacak
        'paths_reused': 0,
        'astar_searches': 0,
        'pruning_count': 0,
        'total_nodes': 0,
        'total_edges': 0
    }
    
    edge_data = defaultdict(lambda: {'weight': 0, 'count': 0, 'last_used': 0})
    
    print("\n🔄 Graph'lar birleştiriliyor...")
    
    # Önce mevcut graph'ı işle (varsa)
    if existing_graph:
        print(f"\n   [0/{len(graph_files)}] Mevcut graph işleniyor...")
        
        # Mevcut graph'ın istatistiklerini topla
        # NOT: paths_learned hariç (çünkü overlap olabilir)
        from src.knowledge_graph import WikiKnowledgeGraph
        existing_data_dict = load_graph(output_path)
        if existing_data_dict:
            # paths_learned'ı toplama - merge sonunda hesaplanacak
            total_stats['paths_reused'] += existing_data_dict.get('paths_reused', 0)
            total_stats['astar_searches'] += existing_data_dict.get('astar_searches', 0)
            total_stats['pruning_count'] += existing_data_dict.get('pruning_count', 0)
        
        # Edge'leri ekle
        for source, target, edge_attrs in existing_graph.edges(data=True):
            key = (source, target)
            edge_data[key]['weight'] += edge_attrs.get('weight', 1.0)
            edge_data[key]['count'] += edge_attrs.get('count', 1)
            last_used = edge_attrs.get('last_used', 0)
            if last_used > edge_data[key]['last_used']:
                edge_data[key]['last_used'] = last_used
        
        print(f"      ✅ Mevcut graph dahil edildi")
    
    # Her worker graph'ı yükle ve birleştir
    for i, graph_file in enumerate(graph_files, 1):
        print(f"\n   [{i}/{len(graph_files)}] {graph_file.name} yükleniyor...")
        
        data = load_graph(graph_file)
        if not data:
            continue
        
        graph = data.get('graph')
        if not graph:
            print(f"      ⚠️ Graph verisi bulunamadı, atlanıyor...")
            continue
        
        # İstatistikleri topla
        # NOT: paths_learned'ı toplama - worker'lar aynı path'leri öğrenmiş olabilir
        total_stats['paths_reused'] += data.get('paths_reused', 0)
        total_stats['astar_searches'] += data.get('astar_searches', 0)
        total_stats['pruning_count'] += data.get('pruning_count', 0)
        
        nodes_before = merged_graph.number_of_nodes()
        edges_before = merged_graph.number_of_edges()
        
        # Edge'leri birleştir
        for source, target, edge_attrs in graph.edges(data=True):
            key = (source, target)
            
            # Weight ve count'ları topla
            edge_data[key]['weight'] += edge_attrs.get('weight', 1.0)
            edge_data[key]['count'] += edge_attrs.get('count', 1)
            
            # En son kullanım zamanını güncelle
            last_used = edge_attrs.get('last_used', 0)
            if last_used > edge_data[key]['last_used']:
                edge_data[key]['last_used'] = last_used
        
        nodes_added = merged_graph.number_of_nodes() - nodes_before
        edges_added = merged_graph.number_of_edges() - edges_before
        
        print(f"      ✅ Nodes: {graph.number_of_nodes()}, Edges: {graph.number_of_edges()}")
        print(f"      📊 Paths learned: {data.get('paths_learned', 0)}")
    
    # Merged graph'a edge'leri ekle
    print("\n   🔗 Edge'ler merged graph'a ekleniyor...")
    for (source, target), attrs in edge_data.items():
        merged_graph.add_edge(
            source,
            target,
            weight=attrs['weight'],
            count=attrs['count'],
            last_used=attrs['last_used']
        )
    
    total_stats['total_nodes'] = merged_graph.number_of_nodes()
    total_stats['total_edges'] = merged_graph.number_of_edges()
    
    # paths_learned'ı gerçek edge sayısından hesapla
    # Her edge bir unique path segment'i temsil eder
    # Toplam unique path sayısı = edge sayısı (çünkü her edge bir A→B path'i)
    total_stats['paths_learned'] = merged_graph.number_of_edges()
    
    print(f"   ✅ Unique path sayısı hesaplandı: {total_stats['paths_learned']:,}")
    
    # Sonuçları kaydet (mevcut dosyanın üzerine yaz)
    print(f"\n💾 Birleştirilmiş graph kaydediliyor: {output_file}")
    
    if existing_graph:
        print(f"   🔒 Mevcut graph korundu ve yeni verilerle birleştirildi")
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(output_path, 'wb') as f:
            pickle.dump({
                'graph': merged_graph,
                'paths_learned': total_stats['paths_learned'],
                'paths_reused': total_stats['paths_reused'],
                'astar_searches': total_stats['astar_searches'],
                'pruning_count': total_stats['pruning_count'],
                'edge_last_used': dict(edge_data)
            }, f)
        
        print(f"   ✅ Kaydedildi!")
    except Exception as e:
        print(f"   ❌ Kaydetme hatası: {e}")
        return None
    
    # Final istatistikler
    print("\n" + "=" * 70)
    print("📊 BİRLEŞTİRME İSTATİSTİKLERİ")
    print("=" * 70)
    print(f"\n📦 Kaynak:")
    if existing_graph:
        print(f"   • Mevcut graph: ✅ Dahil edildi")
    print(f"   • Worker sayısı: {len(graph_files)}")
    print(f"   • Toplam öğrenilen path: {total_stats['paths_learned']}")
    
    print(f"\n📈 Birleştirilmiş Graph:")
    print(f"   • Node sayısı: {total_stats['total_nodes']:,}")
    print(f"   • Edge sayısı: {total_stats['total_edges']:,}")
    print(f"   • Ortalama derece: {total_stats['total_edges']/max(1, total_stats['total_nodes']):.2f}")
    
    # Graph density
    if total_stats['total_nodes'] > 1:
        max_edges = total_stats['total_nodes'] * (total_stats['total_nodes'] - 1)
        density = total_stats['total_edges'] / max_edges
        print(f"   • Graph density: {density:.6f}")
    
    print(f"\n💾 Çıktı dosyası: {output_file}")
    print("=" * 70)
    
    # Top central nodes (PageRank)
    if merged_graph.number_of_nodes() > 0:
        print("\n🌟 En Merkezi Node'lar (PageRank):")
        try:
            pagerank = nx.pagerank(merged_graph, weight='weight')
            top_nodes = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:10]
            
            for i, (node, score) in enumerate(top_nodes, 1):
                print(f"   {i:2d}. {node:<40} (score: {score:.6f})")
        except Exception as e:
            print(f"   ⚠️ PageRank hesaplanamadı: {e}")
    
    print("\n" + "=" * 70)
    print("✅ Birleştirme tamamlandı!")
    print("=" * 70)
    
    return {
        'merged_graph': merged_graph,
        'stats': total_stats,
        'output_file': output_file
    }


def cleanup_worker_files(graph_files: list[Path], keep_backup: bool = True):
    """Worker graph dosyalarını temizle."""
    if not graph_files:
        return
    
    print("\n🧹 Worker dosyaları temizleniyor...")
    
    if keep_backup:
        backup_dir = Path("cache/backup")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"   📦 Backup oluşturuluyor: {backup_dir}")
        
        for gf in graph_files:
            try:
                backup_file = backup_dir / gf.name
                gf.rename(backup_file)
                print(f"      ✅ {gf.name} → backup/")
            except Exception as e:
                print(f"      ⚠️ {gf.name} taşınamadı: {e}")
    else:
        for gf in graph_files:
            try:
                gf.unlink()
                print(f"      ✅ {gf.name} silindi")
            except Exception as e:
                print(f"      ⚠️ {gf.name} silinemedi: {e}")


def main():
    """Ana fonksiyon."""
    parser = argparse.ArgumentParser(description='Worker graph dosyalarını birleştir')
    parser.add_argument('--workers', type=int, nargs='+', help='Belirli worker ID\'leri (örn: 1 2 3)')
    parser.add_argument('--output', type=str, default='cache/wiki_graph.pkl', help='Çıktı dosyası')
    parser.add_argument('--cleanup', action='store_true', help='Worker dosyalarını temizle (backup ile)')
    parser.add_argument('--no-backup', action='store_true', help='Backup olmadan temizle')
    
    args = parser.parse_args()
    
    # Worker graph dosyalarını bul
    if args.workers:
        # Belirli worker'lar
        graph_files = [Path(f"cache/wiki_graph_worker_{wid}.pkl") for wid in args.workers]
        graph_files = [gf for gf in graph_files if gf.exists()]
    else:
        # Tüm worker'lar
        graph_files = find_worker_graphs()
    
    if not graph_files:
        print("\n❌ Birleştirilecek graph dosyası bulunamadı!")
        print("\nWorker graph'ları oluşturmak için:")
        print("   Terminal 1: python auto_train_parallel.py --worker-id 1 --count 100")
        print("   Terminal 2: python auto_train_parallel.py --worker-id 2 --count 100")
        print("   Terminal 3: python auto_train_parallel.py --worker-id 3 --count 100")
        return
    
    # Birleştir
    result = merge_graphs(graph_files, args.output)
    
    if not result:
        return
    
    # Cleanup
    if args.cleanup:
        cleanup_worker_files(graph_files, keep_backup=not args.no_backup)
    else:
        print("\n💡 Worker dosyalarını temizlemek için:")
        print("   python merge_graphs.py --cleanup")


if __name__ == "__main__":
    main()