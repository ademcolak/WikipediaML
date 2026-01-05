"""
Knowledge System - Graph ve ML Model
Başarılı path'leri sakla, pattern'leri öğren.
"""

import networkx as nx
try:
    import igraph as ig
    IGRAPH_AVAILABLE = True
except ImportError:
    IGRAPH_AVAILABLE = False
    ig = None  # type: ignore

import pickle
from pathlib import Path
from typing import List, Optional, Dict, TYPE_CHECKING, Any
from collections import defaultdict
import time

if TYPE_CHECKING and IGRAPH_AVAILABLE:
    from igraph import Graph as IGraph


class KnowledgeSystem:
    """
    Knowledge Graph + ML Model (future).
    
    Özellikler:
    - Directed graph (A→B ≠ B→A)
    - Weighted edges (usage count)
    - Path caching
    - Auto-save
    """
    
    def __init__(self, cache_file: str = "data/knowledge_graph.pkl", use_igraph: bool = True):
        """
        Initialize knowledge system.
        
        Args:
            cache_file: Path to save/load graph
            use_igraph: Use igraph for faster operations (default: True)
        """
        self.graph = nx.DiGraph()
        self.cache_file = Path(cache_file)
        
        # igraph support (10-50x faster for large graphs)
        self.use_igraph = use_igraph and IGRAPH_AVAILABLE
        self.igraph: Optional[Any] = None  # igraph.Graph when available
        self.igraph_dirty = True
        self.node_to_id: Dict[str, int] = {}  # page name -> igraph vertex id
        self.id_to_node: Dict[int, str] = {}  # igraph vertex id -> page name
        
        if self.use_igraph:
            print("   🚀 igraph enabled (10-50x faster for large graphs)")
        elif use_igraph and not IGRAPH_AVAILABLE:
            print("   ⚠️  igraph not available, using NetworkX (slower)")
        
        # Statistics
        self.paths_learned = 0
        self.paths_reused = 0
        self.total_queries = 0
        
        # Edge metadata
        self.edge_usage = defaultdict(int)  # (source, target) -> count
        self.edge_last_used = defaultdict(float)  # (source, target) -> timestamp
        
        # PageRank cache
        self.pagerank = {}
        self.pagerank_dirty = True
        
        # Load existing graph
        self._load()
    
    def add_path(self, path: List[str], quality: float = 1.0):
        """
        Add successful path to knowledge graph.
        
        Args:
            path: List of pages (e.g., ["Italy", "Rome", "Vatican"])
            quality: Path quality score (0-1, shorter = better)
        """
        if len(path) < 2:
            return
        
        current_time = time.time()
        self.paths_learned += 1
        
        # Add edges
        for i in range(len(path) - 1):
            source = path[i]
            target = path[i + 1]
            
            # Add or update edge
            if self.graph.has_edge(source, target):
                # Increment weight
                self.graph[source][target]['weight'] += quality
                self.graph[source][target]['count'] += 1
            else:
                # New edge
                self.graph.add_edge(
                    source, target,
                    weight=quality,
                    count=1,
                    created=current_time
                )
            
            # Update metadata
            self.edge_usage[(source, target)] += 1
            self.edge_last_used[(source, target)] = current_time
        
        # Mark caches as dirty
        self.pagerank_dirty = True
        self.igraph_dirty = True
    
    def _sync_to_igraph(self):
        """Sync NetworkX graph to igraph (for fast operations)."""
        if not self.use_igraph or not self.igraph_dirty:
            return
        
        # Create igraph from NetworkX
        nodes = list(self.graph.nodes())
        self.node_to_id = {node: i for i, node in enumerate(nodes)}
        self.id_to_node = {i: node for i, node in enumerate(nodes)}
        
        # Create igraph
        self.igraph = ig.Graph(directed=True)  # type: ignore
        self.igraph.add_vertices(len(nodes))  # type: ignore
        
        # Add edges with weights
        edges = []
        weights = []
        for source, target, data in self.graph.edges(data=True):
            source_id = self.node_to_id[source]
            target_id = self.node_to_id[target]
            edges.append((source_id, target_id))
            # igraph uses inverse weights for shortest path (lower = better)
            # NetworkX weight is usage count (higher = better)
            # So we use 1/weight for igraph
            weight = data.get('weight', 1.0)
            weights.append(1.0 / weight if weight > 0 else 1.0)
        
        self.igraph.add_edges(edges)  # type: ignore
        self.igraph.es['weight'] = weights  # type: ignore
        
        self.igraph_dirty = False
    
    def find_path(self, start: str, target: str) -> Optional[List[str]]:
        """
        Find path in knowledge graph.
        
        Uses igraph for 10-50x speedup on large graphs.
        
        Args:
            start: Start page
            target: Target page
        
        Returns:
            Path if exists, None otherwise
        """
        self.total_queries += 1
        
        # Check if nodes exist
        if not self.graph.has_node(start) or not self.graph.has_node(target):
            return None
        
        try:
            # Use igraph if available (much faster!)
            if self.use_igraph:
                self._sync_to_igraph()
                
                start_id = self.node_to_id[start]
                target_id = self.node_to_id[target]
                
                # Get shortest path (Dijkstra with weights)
                path_ids = self.igraph.get_shortest_paths(  # type: ignore
                    start_id,
                    target_id,
                    weights='weight',
                    output='vpath'
                )[0]
                
                if not path_ids:
                    return None
                
                # Convert IDs back to node names
                path = [self.id_to_node[vid] for vid in path_ids]
            else:
                # Fallback to NetworkX
                path = nx.shortest_path(
                    self.graph,
                    start,
                    target,
                    weight='weight'
                )
            
            self.paths_reused += 1
            
            # Update last_used for edges in path
            current_time = time.time()
            for i in range(len(path) - 1):
                s, t = path[i], path[i + 1]
                if self.graph.has_edge(s, t):
                    self.graph[s][t]['last_used'] = current_time
                    self.edge_last_used[(s, t)] = current_time
            
            return path
            
        except (nx.NetworkXNoPath, IndexError):
            return None
    
    def get_next_suggestions(self, current: str, target: str, top_k: int = 5) -> List[tuple[str, float]]:
        """
        Get best next pages from current page.
        
        Args:
            current: Current page
            target: Target page (for future ML model)
            top_k: Number of suggestions
        
        Returns:
            List of (page, score) tuples
        """
        if not self.graph.has_node(current):
            return []
        
        # Get successors with weights
        suggestions = []
        for neighbor in self.graph.successors(current):
            weight = self.graph[current][neighbor]['weight']
            suggestions.append((neighbor, weight))
        
        # Sort by weight (descending)
        suggestions.sort(key=lambda x: x[1], reverse=True)
        
        return suggestions[:top_k]
    
    def compute_pagerank(self, force: bool = False):
        """
        Compute PageRank for all nodes.
        
        Uses igraph for 10-50x speedup on large graphs.
        
        Args:
            force: Force recomputation even if cache is valid
        """
        if not self.pagerank_dirty and not force and self.pagerank:
            return
        
        if self.graph.number_of_nodes() == 0:
            self.pagerank = {}
            return
        
        try:
            # Use igraph if available (much faster!)
            if self.use_igraph:
                self._sync_to_igraph()
                
                # Compute PageRank with weights
                pagerank_scores = self.igraph.pagerank(weights='weight')  # type: ignore
                
                # Convert back to node names
                self.pagerank = {
                    self.id_to_node[i]: score
                    for i, score in enumerate(pagerank_scores)
                }
            else:
                # Fallback to NetworkX
                self.pagerank = nx.pagerank(self.graph, weight='weight', max_iter=100)
            
            self.pagerank_dirty = False
        except Exception as e:
            # Fallback to unweighted NetworkX if error
            try:
                self.pagerank = nx.pagerank(self.graph, max_iter=100)
                self.pagerank_dirty = False
            except:
                self.pagerank = {}
    
    def get_hub_pages(self, top_k: int = 20) -> List[tuple[str, float]]:
        """
        Get top hub pages by PageRank.
        
        Args:
            top_k: Number of top pages to return
        
        Returns:
            List of (page, pagerank_score) tuples
        """
        self.compute_pagerank()
        
        if not self.pagerank:
            return []
        
        sorted_pages = sorted(self.pagerank.items(), key=lambda x: x[1], reverse=True)
        return sorted_pages[:top_k]
    
    def prune(self, min_weight: float = 2.0, max_age_days: int = 30):
        """
        Remove low-quality or old edges.
        
        Args:
            min_weight: Minimum weight to keep
            max_age_days: Maximum age in days
        """
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 3600
        
        edges_to_remove = []
        
        for source, target, data in self.graph.edges(data=True):
            weight = data.get('weight', 0)
            last_used = data.get('last_used', data.get('created', 0))
            
            # Remove if:
            # 1. Weight too low
            # 2. Not used recently
            if weight < min_weight or (current_time - last_used) > max_age_seconds:
                edges_to_remove.append((source, target))
        
        # Remove edges
        for source, target in edges_to_remove:
            self.graph.remove_edge(source, target)
        
        # Remove isolated nodes
        isolated = list(nx.isolates(self.graph))
        self.graph.remove_nodes_from(isolated)
        
        # Mark igraph as dirty
        if edges_to_remove or isolated:
            self.igraph_dirty = True
            self.pagerank_dirty = True
        
        if edges_to_remove:
            print(f"🧹 Pruned {len(edges_to_remove)} edges, {len(isolated)} nodes")
    
    def get_stats(self) -> Dict:
        """Get knowledge system statistics."""
        return {
            'nodes': self.graph.number_of_nodes(),
            'edges': self.graph.number_of_edges(),
            'paths_learned': self.paths_learned,
            'paths_reused': self.paths_reused,
            'total_queries': self.total_queries,
            'cache_hit_rate': (self.paths_reused / self.total_queries * 100) if self.total_queries > 0 else 0,
            'pagerank_computed': len(self.pagerank) > 0,
            'using_igraph': self.use_igraph
        }
    
    def save(self):
        """Save graph to disk."""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.cache_file, 'wb') as f:
            pickle.dump({
                'graph': self.graph,
                'paths_learned': self.paths_learned,
                'paths_reused': self.paths_reused,
                'total_queries': self.total_queries,
                'edge_usage': dict(self.edge_usage),
                'edge_last_used': dict(self.edge_last_used),
                'pagerank': self.pagerank
            }, f)
    
    def _load(self):
        """Load graph from disk."""
        if not self.cache_file.exists():
            return
        
        try:
            with open(self.cache_file, 'rb') as f:
                data = pickle.load(f)
            
            self.graph = data.get('graph', nx.DiGraph())
            self.paths_learned = data.get('paths_learned', 0)
            self.paths_reused = data.get('paths_reused', 0)
            self.total_queries = data.get('total_queries', 0)
            self.edge_usage = defaultdict(int, data.get('edge_usage', {}))
            self.edge_last_used = defaultdict(float, data.get('edge_last_used', {}))
            self.pagerank = data.get('pagerank', {})
            self.pagerank_dirty = len(self.pagerank) == 0
            
            print(f"📚 Loaded knowledge graph: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
            if self.pagerank:
                print(f"   PageRank: {len(self.pagerank)} nodes ranked")
            
        except Exception as e:
            print(f"⚠️  Error loading graph: {e}")
            self.graph = nx.DiGraph()