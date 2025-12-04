"""
knowledge_graph.py
------------------
Basit Knowledge Graph - Başarılı path'leri kaydet ve kullan.

Özellikler:
- Başarılı path'leri graph'a ekle
- Graph'ta path ara (daha önce bulundu mu?)
- Partial path matching (A→B→? ve ?→C→D varsa birleştir)
- Graph statistics
"""

import networkx as nx
import pickle
from pathlib import Path
from typing import Optional


class WikiKnowledgeGraph:
    """
    Wikipedia path'leri için basit Knowledge Graph.

    Her başarılı path kaydedilir ve sonraki aramalarda kullanılır.
    """

    def __init__(self, cache_file: str = "wiki_graph.pkl"):
        """
        Knowledge Graph'ı başlat.

        Parametreler:
            cache_file (str): Graph'ın kaydedileceği dosya
        """
        self.graph = nx.DiGraph()  # Directed graph (A→B ≠ B→A)
        self.cache_file = Path(cache_file)

        # Statistics
        self.paths_learned = 0
        self.paths_reused = 0

        # Cache'den yükle (varsa)
        self._load_from_cache()

    def add_path(self, path: list[str], success: bool = True):
        """
        Path'i graph'a ekle.

        Parametreler:
            path (list[str]): Path (örn: ["Potato", "Tomato", "Pizza"])
            success (bool): Başarılı path mi? (şimdilik sadece başarılıları kaydediyoruz)
        """
        if not success or len(path) < 2:
            return

        # Path'i graph'a ekle (ardışık edge'ler)
        for i in range(len(path) - 1):
            source = path[i]
            target = path[i + 1]

            # Edge ekle (varsa weight artır)
            if self.graph.has_edge(source, target):
                self.graph[source][target]['weight'] += 1
                self.graph[source][target]['count'] += 1
            else:
                self.graph.add_edge(source, target, weight=1, count=1)

        self.paths_learned += 1

    def find_path(self, start: str, target: str) -> Optional[list[str]]:
        """
        Graph'ta path ara.

        Parametreler:
            start (str): Başlangıç sayfası
            target (str): Hedef sayfa

        Dönüş:
            list[str] | None: Path (varsa) veya None
        """
        # Graph'ta path var mı?
        if not self.graph.has_node(start) or not self.graph.has_node(target):
            return None

        # Shortest path bul (weight'e göre)
        try:
            path = nx.shortest_path(self.graph, start, target, weight='weight')
            self.paths_reused += 1
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

    def has_path(self, start: str, target: str) -> bool:
        """Graph'ta bu path var mı?"""
        return nx.has_path(self.graph, start, target)

    def get_stats(self) -> dict:
        """Graph istatistiklerini döndür."""
        return {
            'nodes': self.graph.number_of_nodes(),
            'edges': self.graph.number_of_edges(),
            'paths_learned': self.paths_learned,
            'paths_reused': self.paths_reused,
            'density': nx.density(self.graph) if self.graph.number_of_nodes() > 0 else 0
        }

    def save(self):
        """Graph'ı dosyaya kaydet."""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump({
                    'graph': self.graph,
                    'paths_learned': self.paths_learned,
                    'paths_reused': self.paths_reused
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
