"""
knowledge_graph.py
------------------
Optimized Knowledge Graph - Başarılı path'leri kaydet ve akıllıca kullan.

Özellikler:
- Başarılı path'leri graph'a ekle (weighted edges)
- A* search ile heuristic-based path bulma
- Graph pruning - Nadiren kullanılan edge'leri temizle
- Partial path matching (A→B→? ve ?→C→D varsa birleştir)
- Graph statistics ve analytics
"""

import networkx as nx
import pickle
from pathlib import Path
from typing import Optional, Callable
from collections import defaultdict
import time


class WikiKnowledgeGraph:
    """
    Wikipedia path'leri için optimize edilmiş Knowledge Graph.

    Her başarılı path kaydedilir ve sonraki aramalarda kullanılır.
    A* search ile heuristic-based path bulma.
    Otomatik pruning ile graph temiz tutulur.
    """

    def __init__(
        self,
        cache_file: str = "cache/wiki_graph.pkl",
        prune_threshold: int = 2,
        max_edges: int = 10000
    ):
        """
        Knowledge Graph'ı başlat.

        Parametreler:
            cache_file (str): Graph'ın kaydedileceği dosya
            prune_threshold (int): Bu değerin altındaki edge'ler pruning'de silinir
            max_edges (int): Maximum edge sayısı (aşarsa otomatik prune)
        """
        self.graph = nx.DiGraph()  # Directed graph (A→B ≠ B→A)
        self.cache_file = Path(cache_file)
        self.prune_threshold = prune_threshold
        self.max_edges = max_edges

        # Statistics
        self.paths_learned = 0
        self.paths_reused = 0
        self.astar_searches = 0
        self.pruning_count = 0
        
        # Edge usage tracking (for pruning)
        self.edge_last_used = defaultdict(float)  # (source, target) -> timestamp

        # Cache'den yükle (varsa)
        self._load_from_cache()

    def add_path(self, path: list[str], success: bool = True, path_quality: float = 1.0):
        """
        Path'i graph'a ekle.

        Parametreler:
            path (list[str]): Path (örn: ["Potato", "Tomato", "Pizza"])
            success (bool): Başarılı path mi? (şimdilik sadece başarılıları kaydediyoruz)
            path_quality (float): Path kalitesi (0-1, kısa path = yüksek quality)
        """
        if not success or len(path) < 2:
            return

        current_time = time.time()
        
        # Path'i graph'a ekle (ardışık edge'ler)
        for i in range(len(path) - 1):
            source = path[i]
            target = path[i + 1]

            # Edge ekle (varsa weight artır)
            if self.graph.has_edge(source, target):
                # Weight artır (quality ile çarp)
                self.graph[source][target]['weight'] += path_quality
                self.graph[source][target]['count'] += 1
                self.graph[source][target]['last_used'] = current_time
            else:
                self.graph.add_edge(
                    source, target,
                    weight=path_quality,
                    count=1,
                    last_used=current_time
                )
            
            # Track usage
            self.edge_last_used[(source, target)] = current_time

        self.paths_learned += 1
        
        # Auto-prune if too many edges
        if self.graph.number_of_edges() > self.max_edges:
            self.prune_graph()

    def find_path(
        self,
        start: str,
        target: str,
        heuristic: Optional[Callable[[str, str], float]] = None
    ) -> Optional[list[str]]:
        """
        Graph'ta path ara (A* search ile).

        Parametreler:
            start (str): Başlangıç sayfası
            target (str): Hedef sayfa
            heuristic (Callable): Heuristic fonksiyonu (node, target) -> float
                                 Örn: semantic similarity

        Dönüş:
            list[str] | None: Path (varsa) veya None
        """
        # Graph'ta path var mı?
        if not self.graph.has_node(start) or not self.graph.has_node(target):
            return None

        try:
            if heuristic:
                # A* search with heuristic
                path = nx.astar_path(
                    self.graph,
                    start,
                    target,
                    heuristic=heuristic,
                    weight='weight'
                )
                self.astar_searches += 1
            else:
                # Dijkstra (shortest path with weights)
                path = nx.shortest_path(self.graph, start, target, weight='weight')
            
            self.paths_reused += 1
            
            # Update last_used for edges in path
            current_time = time.time()
            for i in range(len(path) - 1):
                source, target_node = path[i], path[i + 1]
                if self.graph.has_edge(source, target_node):
                    self.graph[source][target_node]['last_used'] = current_time
                    self.edge_last_used[(source, target_node)] = current_time
            
            return path
        except nx.NetworkXNoPath:
            return None

    def get_next_nodes(self, current: str, top_k: int = 5) -> list[tuple[str, float]]:
        """
        Mevcut node'dan gidilebilecek en iyi k node'u döndür.

        Parametreler:
            current (str): Mevcut sayfa
            top_k (int): Kaç tane döndürülsün

        Dönüş:
            list[tuple[str, float]]: (node, weight) çiftleri
        """
        if not self.graph.has_node(current):
            return []

        # Successors ve weight'lerini al
        successors = []
        for neighbor in self.graph.successors(current):
            weight = self.graph[current][neighbor]['weight']
            successors.append((neighbor, weight))

        # Weight'e göre sırala (yüksek weight = daha çok kullanılmış)
        successors.sort(key=lambda x: x[1], reverse=True)

        return successors[:top_k]

    def prune_graph(self, min_weight: Optional[float] = None):
        """
        Graph'ı temizle - Nadiren kullanılan edge'leri sil.
        
        Parametreler:
            min_weight (float): Bu değerin altındaki edge'ler silinir
                               None ise self.prune_threshold kullanılır
        """
        if min_weight is None:
            min_weight = self.prune_threshold
        
        edges_to_remove = []
        current_time = time.time()
        
        for source, target, data in self.graph.edges(data=True):
            weight = data.get('weight', 0)
            last_used = data.get('last_used', 0)
            
            # Remove if:
            # 1. Weight too low (rarely used)
            # 2. Not used in last 30 days
            if weight < min_weight or (current_time - last_used) > 30 * 24 * 3600:
                edges_to_remove.append((source, target))
        
        # Remove edges
        for source, target in edges_to_remove:
            self.graph.remove_edge(source, target)
        
        # Remove isolated nodes
        isolated = list(nx.isolates(self.graph))
        self.graph.remove_nodes_from(isolated)
        
        self.pruning_count += 1
        
        if len(edges_to_remove) > 0:
            print(f"🧹 Graph pruned: {len(edges_to_remove)} edges, {len(isolated)} nodes removed")

    def get_centrality_scores(self, top_k: int = 10) -> list[tuple[str, float]]:
        """
        En merkezi node'ları döndür (PageRank ile).
        
        Parametreler:
            top_k (int): Kaç tane döndürülsün
            
        Dönüş:
            list[tuple[str, float]]: (node, centrality_score) çiftleri
        """
        if self.graph.number_of_nodes() == 0:
            return []
        
        try:
            # PageRank (Google'ın algoritması)
            pagerank = nx.pagerank(self.graph, weight='weight')
            
            # Sort by score
            sorted_nodes = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)
            
            return sorted_nodes[:top_k]
        except:
            return []

    def has_path(self, start: str, target: str) -> bool:
        """Graph'ta bu path var mı?"""
        return nx.has_path(self.graph, start, target)

    def get_stats(self) -> dict:
        """Graph istatistiklerini döndür."""
        stats = {
            'nodes': self.graph.number_of_nodes(),
            'edges': self.graph.number_of_edges(),
            'paths_learned': self.paths_learned,
            'paths_reused': self.paths_reused,
            'astar_searches': self.astar_searches,
            'pruning_count': self.pruning_count,
            'density': nx.density(self.graph) if self.graph.number_of_nodes() > 0 else 0
        }
        
        # Add centrality info
        if self.graph.number_of_nodes() > 0:
            top_nodes = self.get_centrality_scores(top_k=5)
            stats['top_central_nodes'] = [node for node, _ in top_nodes]
        
        return stats

    def save(self):
        """Graph'ı dosyaya kaydet."""
        try:
            # Cache klasörünü oluştur
            import os
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            
            with open(self.cache_file, 'wb') as f:
                pickle.dump({
                    'graph': self.graph,
                    'paths_learned': self.paths_learned,
                    'paths_reused': self.paths_reused,
                    'astar_searches': self.astar_searches,
                    'pruning_count': self.pruning_count,
                    'edge_last_used': dict(self.edge_last_used)
                }, f)
        except Exception as e:
            print(f"⚠️ Graph kaydetme hatası: {e}")

    def _load_from_cache(self):
        """Cache'den graph'ı yükle."""
        if not self.cache_file.exists():
            return

        try:
            with open(self.cache_file, 'rb') as f:
                data = pickle.load(f)
                self.graph = data['graph']
                self.paths_learned = data.get('paths_learned', 0)
                self.paths_reused = data.get('paths_reused', 0)
                self.astar_searches = data.get('astar_searches', 0)
                self.pruning_count = data.get('pruning_count', 0)
                self.edge_last_used = defaultdict(float, data.get('edge_last_used', {}))
        except Exception as e:
            print(f"⚠️ Graph yükleme hatası: {e}")

    def clear(self):
        """Graph'ı temizle."""
        self.graph.clear()
        self.paths_learned = 0
        self.paths_reused = 0
        if self.cache_file.exists():
            self.cache_file.unlink()

    def __repr__(self):
        stats = self.get_stats()
        return f"WikiKnowledgeGraph(nodes={stats['nodes']}, edges={stats['edges']}, learned={stats['paths_learned']})"
