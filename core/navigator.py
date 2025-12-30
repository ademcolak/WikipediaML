"""
Navigator - Path Finding
Smart BFS with semantic filtering for optimal path finding.

Strategy 1: Pure KG + Smart BFS
- Knowledge Graph for instant lookups
- Smart BFS with always-on semantic filtering
- Quality control: only save short paths (≤4 steps)
"""

from typing import List, Optional, Tuple
from dataclasses import dataclass
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from .wikipedia import Wikipedia
from .knowledge import KnowledgeSystem
from .bidirectional_search import BidirectionalSearcher


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
    Path finder - Wikipedia game with Strategy 1: Pure KG + Smart BFS.
    
    Architecture:
    1. Knowledge Graph check (instant, <0.01s)
    2. Smart BFS with semantic filtering (1-10s)
    3. Beam search fallback (5-20s)
    4. Quality control: only save short paths (≤4 steps)
    
    Key Features:
    - Semantic filtering ALWAYS active (consistent performance)
    - No metadata complexity (simpler, faster)
    - Quality-focused KG (only efficient routes)
    """
    
    def __init__(self, use_bidirectional: bool = True, training_mode: bool = False):
        """
        Initialize navigator with Strategy 1.
        
        Args:
            use_bidirectional: Use bidirectional search (faster)
            training_mode: If True, use bidirectional with incoming links (training only)
                          If False, use forward-only (fair play for actual games)
        """
        print("🚀 Initializing Navigator (Strategy 1: Pure KG + Smart BFS)...")
        
        self.wiki = Wikipedia()
        self.knowledge = KnowledgeSystem()
        self.use_bidirectional = use_bidirectional
        self.training_mode = training_mode
        
        # Initialize bidirectional searcher WITHOUT metadata (simpler)
        if use_bidirectional:
            self.bidirectional = BidirectionalSearcher(
                self.wiki,
                metadata_system=None,  # ✅ No metadata complexity
                max_depth=4,
                timeout=15,  # ✅ Reduced timeout for speed (was 30)
                training_mode=training_mode
            )
            if training_mode:
                print("   🔄 Bidirectional search: ENABLED (training mode)")
                print("   🧠 Semantic filtering: ALWAYS ACTIVE")
            else:
                print("   ➡️  Forward BFS search: ENABLED (fair play mode)")
                print("   🧠 Semantic filtering: ALWAYS ACTIVE")
        
        # Beam search parameters (fallback only)
        self.beam_width = 5
        self.max_depth = 6
        
        # Statistics
        self.searches_performed = 0
        self.kg_hits = 0
        self.search_hits = 0
        self.bidirectional_hits = 0
        
        print(f"✅ Navigator ready!")
        print(f"   Knowledge Graph: {self.knowledge.graph.number_of_nodes()} nodes, {self.knowledge.graph.number_of_edges()} edges")
        print(f"   Quality Control: Only paths ≤6 steps saved to KG")
    
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
        
        # Tier 2: Try Bidirectional/Forward BFS Search first (faster than beam search)
        if self.use_bidirectional:
            if verbose:
                if self.training_mode:
                    print(f"🔄 Starting Bidirectional Search (max_depth={self.max_depth})...")
                else:
                    print(f"➡️  Starting Forward BFS Search (max_depth={self.max_depth})...")
            
            bi_result = self.bidirectional.search(start, target, verbose)
            
            if bi_result.found:
                self.bidirectional_hits += 1
                
                # Convert to PathResult
                search_result = PathResult(
                    found=True,
                    path=bi_result.path,
                    steps=bi_result.steps,
                    time_seconds=bi_result.time_seconds,
                    source='bidirectional_search' if self.training_mode else 'forward_bfs_search',
                    pages_explored=bi_result.pages_explored
                )
                
                # ✅ STRATEGY 1: Quality control - save reasonable paths
                # Bidirectional can find paths up to 2*max_depth = 8, but we save up to 6
                if len(search_result.path) <= 6:
                    quality = 1.0 / len(search_result.path)
                    self.knowledge.add_path(search_result.path, quality)
                    if verbose:
                        print(f"💾 Saved to Knowledge Graph (quality: {quality:.2f})")
                elif verbose:
                    print(f"⚠️  Path too long ({len(search_result.path)} steps), not saved to KG")
                
                return search_result
            
            # BFS failed, try beam search as fallback
            if verbose:
                print(f"⚠️  BFS search failed, trying Beam Search...")
        
        # Tier 3: Beam Search (fallback or primary if bidirectional disabled)
        if verbose:
            print(f"🔎 Starting Beam Search (width={self.beam_width}, depth={self.max_depth})...")
        
        search_result = self._beam_search(start, target, verbose)
        
        # Tier 4: Save to Knowledge Graph
        if search_result.found:
            self.search_hits += 1
            
            # ✅ STRATEGY 1: Quality control - save reasonable paths
            if len(search_result.path) <= 6:
                quality = 1.0 / len(search_result.path)  # Shorter = better
                self.knowledge.add_path(search_result.path, quality)
                if verbose:
                    print(f"💾 Saved to Knowledge Graph (quality: {quality:.2f})")
            elif verbose:
                print(f"⚠️  Path too long ({len(search_result.path)} steps), not saved to KG")
        
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
            
            # Parallel beam expansion
            def expand_beam_path(beam_item):
                """Expand a single beam path (for parallel processing)."""
                current, path, score = beam_item
                local_candidates = []
                
                # Get links
                links = self.wiki.get_links(current)
                if not links:
                    return None, local_candidates
                
                # Check if target in links (early termination)
                if target in links:
                    final_path = path + [target]
                    return final_path, []
                
                # Score links by similarity to target
                scored_links = self.wiki.batch_similarity(current, links, target)
                
                # Add top candidates
                for link, similarity in scored_links[:self.beam_width]:
                    if link not in visited:
                        new_path = path + [link]
                        new_score = score + similarity
                        local_candidates.append((link, new_path, new_score))
                
                return None, local_candidates
            
            # Process beam paths in parallel
            with ThreadPoolExecutor(max_workers=min(len(beam), 5)) as executor:
                futures = {executor.submit(expand_beam_path, item): item for item in beam}
                
                for future in as_completed(futures):
                    pages_explored += 1
                    final_path, local_candidates = future.result()
                    
                    # Early termination if path found
                    if final_path:
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
                    
                    # Add candidates and mark as visited
                    for link, new_path, new_score in local_candidates:
                        if link not in visited:
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
            'bidirectional_hits': self.bidirectional_hits,
            'kg_hits': self.kg_hits,
            'search_hits': self.search_hits,
            'kg_hit_rate': (self.kg_hits / self.searches_performed * 100) if self.searches_performed > 0 else 0,
            'knowledge': self.knowledge.get_stats(),
            'wikipedia': self.wiki.get_stats()
        }
    
    def save(self):
        """Save knowledge graph (Strategy 1: no metadata)."""
        self.knowledge.save()
        print("💾 Knowledge Graph saved")