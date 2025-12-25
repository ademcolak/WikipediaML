"""
Navigator - Path Finding
Beam search ile optimal path bulma.
"""

from typing import List, Optional, Tuple
from dataclasses import dataclass
import time

from .wikipedia import Wikipedia
from .knowledge import KnowledgeSystem


@dataclass
class PathResult:
    """Path finding sonucu."""
    found: bool
    path: List[str]
    steps: int
    time_seconds: float
    source: str  # 'knowledge_graph' or 'search'
    pages_explored: int = 0


class Navigator:
    """
    Path finder - Wikipedia oyunu için.
    
    Strateji:
    1. Knowledge Graph'te var mı? (instant)
    2. Beam search (semantic similarity)
    3. Başarılı path'i KG'ye kaydet
    
    Beam Search:
    - Width: 5 (5 alternatif path paralel)
    - Depth: 6 (max 6 adım)
    - Greedy değil, exploration var
    """
    
    def __init__(self):
        """Initialize navigator."""
        print("🚀 Initializing Navigator...")
        
        self.wiki = Wikipedia()
        self.knowledge = KnowledgeSystem()
        
        # Beam search parameters
        self.beam_width = 5
        self.max_depth = 6
        
        # Statistics
        self.searches_performed = 0
        self.kg_hits = 0
        self.search_hits = 0
        
        print(f"✅ Navigator ready!")
        print(f"   Knowledge Graph: {self.knowledge.graph.number_of_nodes()} nodes, {self.knowledge.graph.number_of_edges()} edges")
    
    def find_path(self, start: str, target: str, verbose: bool = True) -> PathResult:
        """
        Find path from start to target.
        
        Args:
            start: Start page
            target: Target page
            verbose: Print progress
        
        Returns:
            PathResult with path and metadata
        """
        start_time = time.time()
        self.searches_performed += 1
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"🔍 Finding path: {start} → {target}")
            print(f"{'='*60}")
        
        # Edge case: same page
        if start == target:
            return PathResult(
                found=True,
                path=[start],
                steps=0,
                time_seconds=time.time() - start_time,
                source='trivial'
            )
        
        # Tier 1: Knowledge Graph lookup
        if verbose:
            print("📚 Checking Knowledge Graph...")
        
        kg_path = self.knowledge.find_path(start, target)
        if kg_path:
            self.kg_hits += 1
            elapsed = time.time() - start_time
            
            if verbose:
                print(f"✅ Found in Knowledge Graph!")
                print(f"   Path: {' → '.join(kg_path)}")
                print(f"   Steps: {len(kg_path) - 1}")
                print(f"   Time: {elapsed:.2f}s")
            
            return PathResult(
                found=True,
                path=kg_path,
                steps=len(kg_path) - 1,
                time_seconds=elapsed,
                source='knowledge_graph'
            )
        
        if verbose:
            print("❌ Not in Knowledge Graph")
            print(f"🔎 Starting Beam Search (width={self.beam_width}, depth={self.max_depth})...")
        
        # Tier 2: Beam Search
        search_result = self._beam_search(start, target, verbose)
        
        # Tier 3: Save to Knowledge Graph
        if search_result.found:
            self.search_hits += 1
            quality = 1.0 / len(search_result.path)  # Shorter = better
            self.knowledge.add_path(search_result.path, quality)
            
            if verbose:
                print(f"💾 Saved to Knowledge Graph")
        
        return search_result
    
    def _beam_search(self, start: str, target: str, verbose: bool = True) -> PathResult:
        """
        Beam search implementation.
        
        Args:
            start: Start page
            target: Target page
            verbose: Print progress
        
        Returns:
            PathResult
        """
        start_time = time.time()
        pages_explored = 0
        
        # Beam: [(current_page, path, score)]
        beam = [(start, [start], 0.0)]
        visited = {start}
        
        # Search loop
        for depth in range(self.max_depth):
            if verbose:
                print(f"\n   Depth {depth + 1}/{self.max_depth} | Beam size: {len(beam)}")
            
            candidates = []
            
            # Expand each path in beam
            for current, path, score in beam:
                # Get links
                links = self.wiki.get_links(current)
                pages_explored += 1
                
                if not links:
                    continue
                
                # Check if target in links
                if target in links:
                    final_path = path + [target]
                    elapsed = time.time() - start_time
                    
                    if verbose:
                        print(f"\n✅ Path found!")
                        print(f"   Path: {' → '.join(final_path)}")
                        print(f"   Steps: {len(final_path) - 1}")
                        print(f"   Time: {elapsed:.2f}s")
                        print(f"   Pages explored: {pages_explored}")
                    
                    return PathResult(
                        found=True,
                        path=final_path,
                        steps=len(final_path) - 1,
                        time_seconds=elapsed,
                        source='search',
                        pages_explored=pages_explored
                    )
                
                # Score links by similarity to target
                scored_links = self.wiki.batch_similarity(current, links, target)
                
                # Add top candidates
                for link, similarity in scored_links[:self.beam_width]:
                    if link not in visited:
                        new_path = path + [link]
                        new_score = score + similarity
                        candidates.append((link, new_path, new_score))
                        visited.add(link)
            
            if not candidates:
                break
            
            # Select top beam_width candidates
            candidates.sort(key=lambda x: x[2], reverse=True)
            beam = candidates[:self.beam_width]
            
            if verbose and beam:
                best = beam[0]
                print(f"   Best: {best[0]} (score: {best[2]:.3f})")
        
        # Not found
        elapsed = time.time() - start_time
        
        if verbose:
            print(f"\n❌ Path not found")
            print(f"   Time: {elapsed:.2f}s")
            print(f"   Pages explored: {pages_explored}")
        
        return PathResult(
            found=False,
            path=[],
            steps=0,
            time_seconds=elapsed,
            source='search',
            pages_explored=pages_explored
        )
    
    def get_stats(self) -> dict:
        """Get navigator statistics."""
        return {
            'searches_performed': self.searches_performed,
            'kg_hits': self.kg_hits,
            'search_hits': self.search_hits,
            'kg_hit_rate': (self.kg_hits / self.searches_performed * 100) if self.searches_performed > 0 else 0,
            'knowledge': self.knowledge.get_stats(),
            'wikipedia': self.wiki.get_stats()
        }
    
    def save(self):
        """Save knowledge graph."""
        self.knowledge.save()
        print("💾 Knowledge Graph saved")