#!/usr/bin/env python3
"""
visualize_kg_3d.py
------------------
Knowledge Graph'ı 3D olarak görselleştir ve otomatik olarak tarayıcıda aç.

Kullanım:
    python visualize_kg_3d.py                    # Otomatik: En önemli 300 node
    python visualize_kg_3d.py --preset small     # 100 node (hızlı)
    python visualize_kg_3d.py --preset medium    # 300 node (dengeli)
    python visualize_kg_3d.py --preset large     # 500 node (detaylı)
    python visualize_kg_3d.py --preset full      # Tüm graph (yavaş!)
    python visualize_kg_3d.py --max-nodes 100    # Özel node sayısı
    python visualize_kg_3d.py --min-weight 2.0   # Minimum edge weight
    python visualize_kg_3d.py --no-browser       # Tarayıcıda açma
"""

import argparse
import pickle
import networkx as nx
import plotly.graph_objects as go
import numpy as np
from pathlib import Path
import webbrowser
import http.server
import socketserver
import threading
import time
import sys


def load_knowledge_graph():
    """KG'yi yükle."""
    kg_path = Path("cache/wiki_graph.pkl")
    
    if not kg_path.exists():
        print("❌ Knowledge Graph bulunamadı!")
        print("   Önce eğitim yapmalısınız:")
        print("   python train.py --strategy strategic --iterations 50")
        return None
    
    with open(kg_path, 'rb') as f:
        data = pickle.load(f)
    
    return data['graph']


def filter_graph(graph, max_nodes=None, min_weight=None):
    """Graph'ı filtrele."""
    G = graph.copy()
    
    # Min weight filtresi
    if min_weight:
        edges_to_remove = []
        for u, v, data in G.edges(data=True):
            if data.get('weight', 0) < min_weight:
                edges_to_remove.append((u, v))
        G.remove_edges_from(edges_to_remove)
    
    # İzole node'ları temizle
    isolated = list(nx.isolates(G))
    G.remove_nodes_from(isolated)
    
    # Max nodes filtresi (en yüksek degree'li node'ları al)
    if max_nodes and G.number_of_nodes() > max_nodes:
        # Node degree'lerini hesapla
        degrees = dict(G.degree())
        # En yüksek degree'li node'ları al
        top_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:max_nodes]
        top_node_names = [node for node, _ in top_nodes]
        # Subgraph oluştur
        G = G.subgraph(top_node_names).copy()
    
    return G


def create_3d_visualization(graph, title="Knowledge Graph 3D", fast_mode=False):
    """3D görselleştirme oluştur."""
    
    # Spring layout ile 3D pozisyonlar
    print("🎨 3D layout hesaplanıyor...")
    
    # Node sayısına göre iterasyon sayısını ayarla
    num_nodes = graph.number_of_nodes()
    if fast_mode or num_nodes > 300:
        iterations = 20  # Hızlı mod
    elif num_nodes > 150:
        iterations = 30  # Orta hız
    else:
        iterations = 50  # Yüksek kalite
    
    print(f"   Iterasyon: {iterations}, Node: {num_nodes}")
    pos = nx.spring_layout(graph, dim=3, k=0.5, iterations=iterations)
    
    # Node pozisyonları
    node_x = [pos[node][0] for node in graph.nodes()]
    node_y = [pos[node][1] for node in graph.nodes()]
    node_z = [pos[node][2] for node in graph.nodes()]
    
    # Node boyutları (degree'ye göre)
    node_degrees = dict(graph.degree())
    node_sizes = [min(50, 10 + node_degrees[node] * 3) for node in graph.nodes()]
    
    # Node renkleri (degree'ye göre)
    node_colors = [node_degrees[node] for node in graph.nodes()]
    
    # Node text (hover için)
    node_text = []
    for node in graph.nodes():
        degree = node_degrees[node]
        # Node'un bağlantılarını al
        neighbors = list(graph.neighbors(node))
        neighbor_text = ", ".join(neighbors[:5])
        if len(neighbors) > 5:
            neighbor_text += f"... (+{len(neighbors)-5} daha)"
        
        text = f"<b>{node}</b><br>"
        text += f"Bağlantı sayısı: {degree}<br>"
        text += f"Komşular: {neighbor_text}"
        node_text.append(text)
    
    # Edge pozisyonları
    edge_x = []
    edge_y = []
    edge_z = []
    edge_weights = []
    
    for edge in graph.edges(data=True):
        x0, y0, z0 = pos[edge[0]]
        x1, y1, z1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_z.extend([z0, z1, None])
        edge_weights.append(edge[2].get('weight', 1.0))
    
    # Edge trace
    edge_trace = go.Scatter3d(
        x=edge_x, y=edge_y, z=edge_z,
        mode='lines',
        line=dict(
            color='rgba(125, 125, 125, 0.3)',
            width=1
        ),
        hoverinfo='none',
        name='Bağlantılar'
    )
    
    # Node trace - text rendering'i optimize et
    num_nodes = graph.number_of_nodes()
    
    # Çok fazla node varsa text'leri gösterme (performans için)
    if num_nodes > 200:
        mode = 'markers'
        text_labels = None
        textfont = None
    else:
        mode = 'markers+text'
        text_labels = [node[:15] for node in graph.nodes()]
        textfont = dict(size=8, color='white')
    
    node_trace = go.Scatter3d(
        x=node_x, y=node_y, z=node_z,
        mode=mode,
        marker=dict(
            size=node_sizes,
            color=node_colors,
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(
                title="Bağlantı<br>Sayısı",
                thickness=15,
                len=0.7,
                x=1.02
            ),
            line=dict(color='white', width=0.5)
        ),
        text=text_labels,
        textposition="top center" if text_labels else None,
        textfont=textfont,
        hovertext=node_text,
        hoverinfo='text',
        name='Sayfalar'
    )
    
    # Layout
    layout = go.Layout(
        title=dict(
            text=title,
            x=0.5,
            xanchor='center',
            font=dict(size=20, color='white')
        ),
        showlegend=True,
        hovermode='closest',
        paper_bgcolor='rgb(20, 20, 30)',
        plot_bgcolor='rgb(20, 20, 30)',
        scene=dict(
            xaxis=dict(
                showbackground=False,
                showgrid=True,
                gridcolor='rgba(255, 255, 255, 0.1)',
                showticklabels=False,
                title=''
            ),
            yaxis=dict(
                showbackground=False,
                showgrid=True,
                gridcolor='rgba(255, 255, 255, 0.1)',
                showticklabels=False,
                title=''
            ),
            zaxis=dict(
                showbackground=False,
                showgrid=True,
                gridcolor='rgba(255, 255, 255, 0.1)',
                showticklabels=False,
                title=''
            ),
            bgcolor='rgb(20, 20, 30)'
        ),
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    # Figure oluştur
    fig = go.Figure(data=[edge_trace, node_trace], layout=layout)
    
    return fig


def print_graph_stats(graph):
    """Graph istatistiklerini yazdır."""
    print("\n" + "="*70)
    print("📊 GRAPH İSTATİSTİKLERİ")
    print("="*70)
    
    print(f"\n📍 Node sayısı: {graph.number_of_nodes():,}")
    print(f"🔗 Edge sayısı: {graph.number_of_edges():,}")
    
    if graph.number_of_nodes() > 0:
        # Degree istatistikleri
        degrees = [d for n, d in graph.degree()]
        print(f"\n📈 Bağlantı İstatistikleri:")
        print(f"   Ortalama: {np.mean(degrees):.2f}")
        print(f"   Maksimum: {max(degrees)}")
        print(f"   Minimum: {min(degrees)}")
        
        # En bağlantılı node'lar
        top_nodes = sorted(graph.degree(), key=lambda x: x[1], reverse=True)[:5]
        print(f"\n🌟 En Bağlantılı Sayfalar:")
        for i, (node, degree) in enumerate(top_nodes, 1):
            display_name = node[:50] + "..." if len(node) > 50 else node
            print(f"   {i}. {display_name}: {degree} bağlantı")
        
        # Weight istatistikleri
        weights = [data.get('weight', 1.0) for _, _, data in graph.edges(data=True)]
        if weights:
            print(f"\n⚖️  Weight İstatistikleri:")
            print(f"   Ortalama: {np.mean(weights):.2f}")
            print(f"   Maksimum: {max(weights):.2f}")
            print(f"   Minimum: {min(weights):.2f}")
    
    print("="*70)


class QuietHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Sessiz HTTP handler (log yazdırmaz)."""
    def log_message(self, format, *args):
        pass


def start_server(port=8000):
    """HTTP server başlat."""
    handler = QuietHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(f"🌐 HTTP server başlatıldı: http://localhost:{port}")
            httpd.serve_forever()
    except OSError:
        # Port kullanımda, başka port dene
        return start_server(port + 1)


def open_in_browser(filepath, port=8000, no_browser=False):
    """Dosyayı tarayıcıda aç."""
    if no_browser:
        print(f"\n💡 Görselleştirmeyi görmek için:")
        print(f"   http://localhost:{port}/{filepath}")
        return
    
    # Server'ı thread'de başlat
    server_thread = threading.Thread(target=start_server, args=(port,), daemon=True)
    server_thread.start()
    
    # Server'ın başlamasını bekle
    time.sleep(1)
    
    # Tarayıcıda aç
    url = f"http://localhost:{port}/{filepath}"
    print(f"\n🚀 Tarayıcıda açılıyor: {url}")
    
    try:
        webbrowser.open(url)
        print("\n✅ Görselleştirme tarayıcıda açıldı!")
        print("\n💡 İpuçları:")
        print("   - Fare ile döndürebilirsiniz")
        print("   - Scroll ile zoom yapabilirsiniz")
        print("   - Node'ların üzerine gelin detay görmek için")
        print("\n⚠️  Server çalışıyor. Kapatmak için Ctrl+C")
        
        # Server'ı çalışır tut
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n👋 Server kapatılıyor...")
            sys.exit(0)
            
    except Exception as e:
        print(f"\n⚠️  Tarayıcı açılamadı: {e}")
        print(f"\n💡 Manuel olarak açın:")
        print(f"   {url}")
        print("\n⚠️  Server çalışıyor. Kapatmak için Ctrl+C")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n👋 Server kapatılıyor...")
            sys.exit(0)


def main():
    """Ana fonksiyon."""
    parser = argparse.ArgumentParser(
        description='KG 3D Görselleştirme',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Preset'ler:
  small   : 100 node  (en hızlı, genel bakış)
  medium  : 300 node  (dengeli, önerilen) [DEFAULT]
  large   : 500 node  (detaylı, biraz yavaş)
  full    : Tüm graph (çok yavaş, 10000+ node için önerilmez!)

Örnekler:
  python visualize_kg_3d.py                    # 300 node (medium)
  python visualize_kg_3d.py --preset small     # 100 node
  python visualize_kg_3d.py --preset large     # 500 node
  python visualize_kg_3d.py --max-nodes 150    # Özel sayı
        """
    )
    parser.add_argument('--preset', type=str, choices=['small', 'medium', 'large', 'full'],
                       help='Hazır boyut ayarı (default: medium)')
    parser.add_argument('--max-nodes', type=int, help='Maksimum node sayısı (preset yerine)')
    parser.add_argument('--min-weight', type=float, help='Minimum edge weight (default: 0)')
    parser.add_argument('--output', type=str, default='kg_3d.html', help='Çıktı dosyası')
    parser.add_argument('--port', type=int, default=8000, help='HTTP server portu')
    parser.add_argument('--no-browser', action='store_true', help='Tarayıcıda açma')
    parser.add_argument('--fast', action='store_true', help='Hızlı mod (düşük kalite layout)')
    
    args = parser.parse_args()
    
    # Preset'leri işle
    preset_sizes = {
        'small': 100,
        'medium': 300,
        'large': 500,
        'full': None  # Tümü
    }
    
    # max-nodes belirlenmemişse preset kullan
    if args.max_nodes is None:
        preset = args.preset or 'medium'  # Default: medium
        args.max_nodes = preset_sizes[preset]
        if preset != 'full':
            print(f"\n💡 Preset: {preset} ({args.max_nodes} node)")
    
    print("\n" + "="*70)
    print("🎨 KNOWLEDGE GRAPH 3D GÖRSELLEŞTİRME")
    print("="*70)
    
    # KG'yi yükle
    print("\n📂 Knowledge Graph yükleniyor...")
    graph = load_knowledge_graph()
    
    if graph is None:
        sys.exit(1)
    
    original_nodes = graph.number_of_nodes()
    original_edges = graph.number_of_edges()
    print(f"✅ {original_nodes:,} node, {original_edges:,} edge yüklendi")
    
    # Performans uyarısı
    if original_nodes > 1000 and args.max_nodes is None:
        print("\n⚠️  UYARI: Graph çok büyük!")
        print(f"   {original_nodes:,} node var. Görselleştirme çok yavaş olabilir.")
        print("   Önerilen: --preset small veya --preset medium kullanın")
        print("\n   Devam etmek için Enter'a basın (veya Ctrl+C ile iptal)...")
        try:
            input()
        except KeyboardInterrupt:
            print("\n\n👋 İptal edildi.")
            sys.exit(0)
    
    # Filtrele
    if args.max_nodes or args.min_weight:
        print("\n🔍 Graph filtreleniyor...")
        graph = filter_graph(graph, args.max_nodes, args.min_weight)
        filtered_nodes = graph.number_of_nodes()
        filtered_edges = graph.number_of_edges()
        print(f"✅ {filtered_nodes:,} node, {filtered_edges:,} edge kaldı")
        
        # Filtreleme oranını göster
        if original_nodes > 0:
            node_ratio = (filtered_nodes / original_nodes) * 100
            print(f"   📊 Node'ların %{node_ratio:.1f}'i gösteriliyor")
    
    # İstatistikleri göster
    print_graph_stats(graph)
    
    # 3D görselleştirme
    print("\n🎨 3D görselleştirme oluşturuluyor...")
    
    title = "Knowledge Graph 3D"
    if args.max_nodes:
        title += f" (Top {args.max_nodes} nodes)"
    if args.min_weight:
        title += f" (min weight: {args.min_weight})"
    
    fig = create_3d_visualization(graph, title, fast_mode=args.fast)
    
    # Kaydet
    output_path = args.output
    fig.write_html(output_path)
    
    file_size = Path(output_path).stat().st_size / (1024 * 1024)  # MB
    print(f"\n✅ Görselleştirme kaydedildi: {output_path}")
    print(f"   📦 Dosya boyutu: {file_size:.2f} MB")
    
    # Performans ipuçları
    if file_size > 10:
        print("\n💡 İpucu: Dosya büyük. Daha hızlı yükleme için:")
        print("   python visualize_kg_3d.py --preset small")
    
    print("="*70)
    
    # Tarayıcıda aç
    open_in_browser(output_path, args.port, args.no_browser)


if __name__ == "__main__":
    main()