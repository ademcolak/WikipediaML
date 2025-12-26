"""
Bidirectional Search - İki yönlü arama (Training Mode)

Strateji:
1. Start'tan forward search (outgoing links)
2. Target'tan reverse search (incoming links - Wikipedia API)
3. Intersection bulunca path'leri birleştir
4. ~50% daha hızlı (ortada buluşuyorlar)

NOT: Sadece training'de kullan! Play mode'da forward-only kullan.
"""

from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
import time
from collections import deque

from .wikipedia import Wikipedia


@dataclass
class BidirectionalResult:
    """Bidirectional search sonucu."""
    found: bool
    path: List[str]
    steps: int
    time_seconds: float
    intersection: Optional[str] = None
    forward_depth: int = 0
    reverse_depth: int = 0
    pages_explored: int = 0


class BidirectionalSearcher:
    """
    İki yönlü BFS arama (Training Mode).
    
    Özellikler:
    - Forward search: start → target (outgoing links)
    - Reverse search: target → start (incoming links via Wikipedia API)
    - Ortada buluşunca path birleştirme
    - ~50% daha hızlı (depth/2 yerine depth)
    
    Örnek:
    Start: Ancient_Egypt
    Target: Cryptocurrency
    
    Forward: Ancient_Egypt → History → Technology → ...
    Reverse: Cryptocurrency ← Bitcoin ← Computer ← ...
    Intersection: Technology (buluşma noktası)
    Final Path: Ancient_Egypt → ... → Technology → ... → Cryptocurrency
    
    NOT: Sadece training'de kullan! Play mode'da forward-only kullan.
    """
    
    def __init__(self, wiki: Wikipedia, max_depth: int = 4, timeout: int = 30, training_mode: bool = False):
        """
        Initialize bidirectional searcher.
        
        Args:
            wiki: Wikipedia instance
            max_depth: Maximum depth for each direction (default: 4)
            timeout: Maximum search time in seconds (default: 30)
            training_mode: If True, use incoming links (training only)
                          If False, forward-only (fair play)
        """
        self.wiki = wiki
        self.max_depth = max_depth
        self.timeout = timeout
        self.training_mode = training_mode
    
    def search(self, start: str, target: str, verbose: bool = True) -> BidirectionalResult:
        """
        Bidirectional BFS search (Training Mode).
        
        Args:
            start: Start page
            target: Target page
            verbose: Print progress
        
        Returns:
            BidirectionalResult with path and metadata
        """
        start_time = time.time()
        
        if verbose:
            print(f"\n🔄 Bidirectional Search: {start} ⇄ {target}")
        
        # Edge case: same page
        if start == target:
            return BidirectionalResult(
                found=True,
                path=[start],
                steps=0,
                time_seconds=time.time() - start_time
            )
        
        # Initialize forward and reverse searches
        # visited: {page: (predecessor, depth)}
        forward_visited: Dict[str, Tuple[Optional[str], int]] = {start: (None, 0)}
        reverse_visited: Dict[str, Tuple[Optional[str], int]] = {target: (None, 0)}
        
        # Queues for BFS
        forward_queue: deque = deque([start])
        reverse_queue: deque = deque([target])
        
        pages_explored = 0
        
        # Alternating search loop
        for depth in range(self.max_depth):
            # Check timeout
            if time.time() - start_time > self.timeout:
                if verbose:
                    print(f"\n⏱️  Timeout ({self.timeout}s) - stopping search")
                break
            
            # Check queue size (prevent memory explosion)
            if len(forward_queue) > 10000 or len(reverse_queue) > 10000:
                if verbose:
                    print(f"\n⚠️  Queue too large (>10k) - stopping search")
                break
            
            if verbose:
                print(f"   Depth {depth + 1}/{self.max_depth} | Forward: {len(forward_queue)}, Reverse: {len(reverse_queue)}")
            
            # Forward search
            if forward_queue:
                intersection = self._forward_bfs(
                    start, target,
                    forward_visited, reverse_visited,
                    forward_queue
                )
                pages_explored += 1
                
                if intersection:
                    # Found intersection!
                    path = self._trace_path(intersection, start, target,
                                          forward_visited, reverse_visited)
                    elapsed = time.time() - start_time
                    
                    if verbose:
                        print(f"\n✅ Intersection found: {intersection}")
                        print(f"   Path: {' → '.join(path)}")
                        print(f"   Steps: {len(path) - 1}")
                        print(f"   Forward depth: {forward_visited[intersection][1]}")
                        print(f"   Reverse depth: {reverse_visited[intersection][1]}")
                        print(f"   Time: {elapsed:.2f}s")
                    
                    return BidirectionalResult(
                        found=True,
                        path=path,
                        steps=len(path) - 1,
                        time_seconds=elapsed,
                        intersection=intersection,
                        forward_depth=forward_visited[intersection][1],
                        reverse_depth=reverse_visited[intersection][1],
                        pages_explored=pages_explored
                    )
            
            # Reverse search
            if reverse_queue:
                intersection = self._reverse_bfs(
                    start, target,
                    forward_visited, reverse_visited,
                    reverse_queue
                )
                pages_explored += 1
                
                if intersection:
                    # Found intersection!
                    path = self._trace_path(intersection, start, target,
                                          forward_visited, reverse_visited)
                    elapsed = time.time() - start_time
                    
                    if verbose:
                        print(f"\n✅ Intersection found: {intersection}")
                        print(f"   Path: {' → '.join(path)}")
                        print(f"   Steps: {len(path) - 1}")
                        print(f"   Forward depth: {forward_visited[intersection][1]}")
                        print(f"   Reverse depth: {reverse_visited[intersection][1]}")
                        print(f"   Time: {elapsed:.2f}s")
                    
                    return BidirectionalResult(
                        found=True,
                        path=path,
                        steps=len(path) - 1,
                        time_seconds=elapsed,
                        intersection=intersection,
                        forward_depth=forward_visited[intersection][1],
                        reverse_depth=reverse_visited[intersection][1],
                        pages_explored=pages_explored
                    )
            
            # Check if both queues are empty
            if not forward_queue and not reverse_queue:
                break
        
        # Not found
        elapsed = time.time() - start_time
        
        if verbose:
            print(f"\n❌ No path found")
            print(f"   Time: {elapsed:.2f}s")
            print(f"   Pages explored: {pages_explored}")
        
        return BidirectionalResult(
            found=False,
            path=[],
            steps=0,
            time_seconds=elapsed,
            pages_explored=pages_explored
        )
    
    def _forward_bfs(
        self,
        start: str,
        target: str,
        forward_visited: Dict[str, Tuple[Optional[str], int]],
        reverse_visited: Dict[str, Tuple[Optional[str], int]],
        queue: deque
    ) -> Optional[str]:
        """
        Forward BFS step.
        
        Args:
            start: Start page
            target: Target page
            forward_visited: Forward visited dict
            reverse_visited: Reverse visited dict
            queue: Forward queue
        
        Returns:
            Intersection page if found, None otherwise
        """
        if not queue:
            return None
        
        # Process one level at a time (all pages at same depth)
        current_depth = forward_visited[queue[0]][1]
        level_size = sum(1 for page in queue if forward_visited[page][1] == current_depth)
        
        for _ in range(level_size):
            if not queue:
                break
            
            current = queue.popleft()
            current_depth = forward_visited[current][1]
            
            # Get links
            links = self.wiki.get_links(current)
            if not links:
                continue
            
            for link in links:
                # Check if reached target directly
                if link == target:
                    forward_visited[link] = (current, current_depth + 1)
                    return link
                
                # Check if reverse search visited this page (intersection!)
                if link in reverse_visited:
                    forward_visited[link] = (current, current_depth + 1)
                    return link
                
                # Add to forward search
                if link not in forward_visited:
                    forward_visited[link] = (current, current_depth + 1)
                    queue.append(link)
        
        return None
    
    def _reverse_bfs(
        self,
        start: str,
        target: str,
        forward_visited: Dict[str, Tuple[Optional[str], int]],
        reverse_visited: Dict[str, Tuple[Optional[str], int]],
        queue: deque
    ) -> Optional[str]:
        """
        Reverse BFS step.
        
        Args:
            start: Start page
            target: Target page
            forward_visited: Forward visited dict
            reverse_visited: Reverse visited dict
            queue: Reverse queue
        
        Returns:
            Intersection page if found, None otherwise
        """
        if not queue:
            return None
        
        # Process one level at a time
        current_depth = reverse_visited[queue[0]][1]
        level_size = sum(1 for page in queue if reverse_visited[page][1] == current_depth)
        
        for _ in range(level_size):
            if not queue:
                break
            
            current = queue.popleft()
            current_depth = reverse_visited[current][1]
            
            # Get incoming links (reverse direction)
            if self.training_mode:
                # Training mode: Use Wikipedia API backlinks (fast but not fair play)
                links = self.wiki.get_incoming_links(current)
            else:
                # Play mode: No reverse search (fair play - forward only)
                links = []
            if not links:
                continue
            
            for link in links:
                # Check if reached start directly
                if link == start:
                    reverse_visited[link] = (current, current_depth + 1)
                    return link
                
                # Check if forward search visited this page (intersection!)
                if link in forward_visited:
                    reverse_visited[link] = (current, current_depth + 1)
                    return link
                
                # Add to reverse search
                if link not in reverse_visited:
                    reverse_visited[link] = (current, current_depth + 1)
                    queue.append(link)
        
        return None
    
    def _trace_path(
        self,
        intersection: str,
        start: str,
        target: str,
        forward_visited: Dict[str, Tuple[Optional[str], int]],
        reverse_visited: Dict[str, Tuple[Optional[str], int]]
    ) -> List[str]:
        """
        Trace path from start to target through intersection.
        
        Args:
            intersection: Intersection page
            start: Start page
            target: Target page
            forward_visited: Forward visited dict
            reverse_visited: Reverse visited dict
        
        Returns:
            Complete path from start to target
        """
        # Trace forward path (start → intersection)
        forward_path = []
        current = intersection
        while current is not None:
            forward_path.append(current)
            current = forward_visited[current][0]
        forward_path.reverse()
        
        # Trace reverse path (intersection → target)
        reverse_path = []
        current = reverse_visited[intersection][0]  # Skip intersection (already in forward)
        while current is not None:
            reverse_path.append(current)
            current = reverse_visited[current][0]
        
        # Combine paths
        return forward_path + reverse_path