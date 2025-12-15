#!/usr/bin/env python3
"""
visualize_kg_3d.py
------------------
Knowledge Graph'ı 3D olarak görselleştir.

Kullanım:
    python visualize_kg_3d.py
    python visualize_kg_3d.py --max-nodes 100
    python visualize_kg_3d.py --min-weight 2.0
"""

import argparse
import pickle
import networkx as nx
import plotly.graph_objects as go
import numpy as np
from pathlib import Path


def load_knowledge_graph():
    """KG'yi yükle."""
    kg_path = Path("cache/wiki_graph.pkl")
    
    if not kg_path.exists():
        print("❌ Knowledge Graph bulunamadı!")
        print("   Önce eğitim yapmalısınız:")
        print("   python auto_train.py")
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


def create_3d_visualization(graph, title="Knowledge Graph 3D"):
    """3D görselleştirme oluştur."""
    
    # Spring layout ile 3D pozisyonlar
    print("🎨 3D layout hesaplanıyor...")
    pos = nx.spring_layout(graph, dim=3, k=0.5, iterations=50)
    
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
            neighbor_text += f"... (+{len(neighbors)-5} more)"
        
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
    
    # Node trace
    node_trace = go.Scatter3d(
        x=node_x, y=node_y, z=node_z,
        mode='markers+text',
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
        text=[node[:15] for node in graph.nodes()],  # Kısa isimler
        textposition="top center",
        textfont=dict(size=8, color='white'),
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
    
    print(f"\n📍 Node sayısı: {graph.number_of_nodes()}")
    print(f"🔗 Edge sayısı: {graph.number_of_edges()}")
    
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
            print(f"   {i}. {node}: {degree} bağlantı")
        
        # Weight istatistikleri
        weights = [data.get('weight', 1.0) for _, _, data in graph.edges(data=True)]
        if weights:
            print(f"\n⚖️  Weight İstatistikleri:")
            print(f"   Ortalama: {np.mean(weights):.2f}")
            print(f"   Maksimum: {max(weights):.2f}")
            print(f"   Minimum: {min(weights):.2f}")
    
    print("="*70)


def main():
    """Ana fonksiyon."""
    parser = argparse.ArgumentParser(description='KG 3D Görselleştirme')
    parser.add_argument('--max-nodes', type=int, help='Maksimum node sayısı (default: tümü)')
    parser.add_argument('--min-weight', type=float, help='Minimum edge weight (default: 0)')
    parser.add_argument('--output', type=str, default='kg_3d.html', help='Çıktı dosyası')
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("🎨 KNOWLEDGE GRAPH 3D GÖRSELLEŞTİRME")
    print("="*70)
    
    # KG'yi yükle
    print("\n📂 Knowledge Graph yükleniyor...")
    graph = load_knowledge_graph()
    
    if graph is None:
        return
    
    print(f"✅ {graph.number_of_nodes()} node, {graph.number_of_edges()} edge yüklendi")
    
    # Filtrele
    if args.max_nodes or args.min_weight:
        print("\n🔍 Graph filtreleniyor...")
        graph = filter_graph(graph, args.max_nodes, args.min_weight)
        print(f"✅ {graph.number_of_nodes()} node, {graph.number_of_edges()} edge kaldı")
    
    # İstatistikleri göster
    print_graph_stats(graph)
    
    # 3D görselleştirme
    print("\n🎨 3D görselleştirme oluşturuluyor...")
    
    title = "Knowledge Graph 3D"
    if args.max_nodes:
        title += f" (Top {args.max_nodes} nodes)"
    if args.min_weight:
        title += f" (min weight: {args.min_weight})"
    
    fig = create_3d_visualization(graph, title)
    
    # Kaydet
    output_path = args.output
    fig.write_html(output_path)
    
    print(f"\n✅ Görselleştirme kaydedildi: {output_path}")
    print(f"   Tarayıcıda açmak için: open {output_path}")
    print("\n💡 İpuçları:")
    print("   - Fare ile döndürebilirsiniz")
    print("   - Scroll ile zoom yapabilirsiniz")
    print("   - Node'ların üzerine gelin detay görmek için")
    print("="*70)


if __name__ == "__main__":
    main()