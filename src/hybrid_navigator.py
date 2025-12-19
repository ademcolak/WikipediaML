"""
hybrid_navigator.py
-------------------
Hybrid navigation system combining KG, Embedding, and LLM.

Three-tier system:
1. KG (fastest, free) - Use if path exists
2. Embedding (medium speed) - Filter candidates
3. LLM (slowest, costs money) - Select best from filtered candidates
"""

from typing import List, Optional
from src.knowledge_graph import WikiKnowledgeGraph
from src.embedding_navigator import EmbeddingNavigator
from src.llm_navigator import LLMNavigator


class HybridNavigator:
    """
    Hybrid navigation system.
    
    Combines three approaches:
    - KG: Fast lookup if path exists
    - Embedding: Semantic filtering of candidates
    - LLM: Intelligent selection from top candidates
    """
    
    def __init__(
        self,
        kg: WikiKnowledgeGraph,
        embedding_nav: Optional[EmbeddingNavigator] = None,
        llm_nav: Optional[LLMNavigator] = None,
        use_embedding: bool = True,
        use_llm: bool = True
    ):
        """
        Initialize Hybrid Navigator.
        
        Args:
            kg: Knowledge Graph instance
            embedding_nav: Embedding navigator (optional, will create if None)
            llm_nav: LLM navigator (optional, will create if None)
            use_embedding: Whether to use embedding filtering
            use_llm: Whether to use LLM selection
        """
        self.kg = kg
        self.use_embedding = use_embedding
        self.use_llm = use_llm
        
        # Initialize embedding navigator
        if use_embedding:
            self.embedding_nav = embedding_nav or EmbeddingNavigator()
        else:
            self.embedding_nav = None
        
        # Initialize LLM navigator
        if use_llm:
            self.llm_nav = llm_nav or LLMNavigator()
        else:
            self.llm_nav = None
        
        # Statistics
        self.kg_hits = 0
        self.embedding_uses = 0
        self.llm_uses = 0
        self.fallback_uses = 0
    
    def find_next_step(
        self,
        current_page: str,
        target_page: str,
        available_links: List[str],
        embedding_k: int = 5
    ) -> str:
        """
        Find next step using hybrid approach.
        
        Args:
            current_page: Current Wikipedia page
            target_page: Target Wikipedia page
            available_links: List of available links from current page
            embedding_k: Number of candidates to pass to LLM
        
        Returns:
            Selected link name
        """
        if not available_links:
            raise ValueError("No available links")
        
        # Tier 1: Check KG
        if self.kg.has_path(current_page, target_page):
            next_step = self._get_kg_next_step(current_page, target_page, available_links)
            if next_step:
                self.kg_hits += 1
                return next_step
        
        # Tier 2: Use Embedding to filter
        if self.use_embedding and self.embedding_nav:
            filtered_links = self.embedding_nav.filter_links(
                available_links,
                target_page,
                k=embedding_k
            )
            self.embedding_uses += 1
        else:
            # No embedding, use all links (or first N)
            filtered_links = available_links[:embedding_k]
        
        # Tier 3: Use LLM to select from filtered
        if self.use_llm and self.llm_nav:
            selected = self.llm_nav.select_link(
                current_page,
                target_page,
                filtered_links
            )
            self.llm_uses += 1
            return selected
        
        # Fallback: Return first filtered link
        self.fallback_uses += 1
        return filtered_links[0]
    
    def _get_kg_next_step(
        self,
        current_page: str,
        target_page: str,
        available_links: List[str]
    ) -> Optional[str]:
        """
        Get next step from KG if it exists in available links.
        
        Args:
            current_page: Current page
            target_page: Target page
            available_links: Available links
        
        Returns:
            Next step if found in available links, None otherwise
        """
        try:
            # Get shortest path from KG
            import networkx as nx
            path = nx.shortest_path(self.kg.graph, current_page, target_page)
            
            if len(path) > 1:
                next_step = path[1]
                
                # Check if next step is in available links
                if next_step in available_links:
                    return next_step
        except:
            pass
        
        return None
    
    def get_stats(self) -> dict:
        """Get usage statistics."""
        total = self.kg_hits + self.embedding_uses + self.llm_uses + self.fallback_uses
        
        stats: dict = {
            'total_queries': total,
            'kg_hits': self.kg_hits,
            'embedding_uses': self.embedding_uses,
            'llm_uses': self.llm_uses,
            'fallback_uses': self.fallback_uses
        }
        
        if total > 0:
            stats['kg_hit_rate'] = float((self.kg_hits / total) * 100)
            stats['llm_usage_rate'] = float((self.llm_uses / total) * 100)
        
        # Add sub-navigator stats
        if self.embedding_nav:
            stats['embedding_stats'] = self.embedding_nav.get_stats()
        
        if self.llm_nav:
            stats['llm_stats'] = self.llm_nav.get_stats()
        
        return stats
    
    def reset_stats(self):
        """Reset all statistics."""
        self.kg_hits = 0
        self.embedding_uses = 0
        self.llm_uses = 0
        self.fallback_uses = 0
        
        if self.embedding_nav:
            self.embedding_nav.clear_cache()
        
        if self.llm_nav:
            self.llm_nav.reset_stats()