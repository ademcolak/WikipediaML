"""
Knowledge System - Graph ve ML Model
Başarılı path'leri sakla, pattern'leri öğren.
"""

import networkx as nx
import pickle
from pathlib import Path
from typing import List, Optional, Dict
from collections import defaultdict
import time


class KnowledgeSystem:
    """
    Knowledge Graph + ML Model (future).
    
    Özellikler:
    - Directed graph (A→B ≠ B→A)
    - Weighted edges (usage count)
    - Path caching
    - Auto-save
    """
    
    def __init__(self, cache_file: str = "data/knowledge_graph.pkl"):
        """
        Initialize knowledge system.
        
        Args:
            cache_file: Path to save/load graph
        """
        self.graph = nx.DiGraph()
        self.cache_file = Path(cache_file)
        
        # Statistics
        self.paths_learned = 0
        self.paths_reused = 0
        self.total_queries = 0
        
        # Edge metadata
        self.edge_usage = defaultdict(int)  # (source, target) -> count
        self.edge_last_used = defaultdict(float)  # (source, target) -> timestamp
        
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
    
    def find_path(self, start: str, target: str) -> Optional[List[str]]:
        """
        Find path in knowledge graph.
        
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
            # Dijkstra's shortest path (weighted)
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
            
        except nx.NetworkXNoPath:
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
            'cache_hit_rate': (self.paths_reused / self.total_queries * 100) if self.total_queries > 0 else 0
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
                'edge_last_used': dict(self.edge_last_used)
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
            
            print(f"📚 Loaded knowledge graph: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
            
        except Exception as e:
            print(f"⚠️  Error loading graph: {e}")
            self.graph = nx.DiGraph()