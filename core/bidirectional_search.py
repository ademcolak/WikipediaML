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
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    
    def __init__(self, wiki: Wikipedia, metadata_system=None, max_depth: int = 4, timeout: int = 15, training_mode: bool = False):
        """
        Initialize bidirectional searcher.
        
        Args:
            wiki: Wikipedia instance
            metadata_system: MetadataSystem instance for smart routing
            max_depth: Maximum depth for each direction (default: 4)
            timeout: Maximum search time in seconds (default: 15, reduced for speed)
            training_mode: If True, use incoming links (training only)
                          If False, forward-only (fair play)
        """
        self.wiki = wiki
        self.metadata = metadata_system
        self.max_depth = max_depth
        self.timeout = timeout
        self.training_mode = training_mode
        self.interrupted = False  # Flag for Ctrl+C detection
    
    def _get_link_limit(self, depth: int) -> int:
        """
        Get adaptive link limit based on search depth.
        Deeper searches use fewer links to prevent exponential growth.
        
        Args:
            depth: Current search depth
        
        Returns:
            Maximum number of links to process at this depth
        """
        # ULTRA AGGRESSIVE limits for maximum speed
        limits = {
            0: 30,   # First step: focused (was 50)
            1: 20,   # Second step: narrower (was 40)
            2: 15,   # Third step: very focused (was 30)
            3: 10,   # Fourth step: minimal (was 20)
        }
        return limits.get(depth, 10)  # Default to 10 for deeper levels
    
    def _process_page_forward(
        self,
        page: str,
        target: str,
        current_depth: int,
        forward_visited_set: Set[str],
        reverse_visited_set: Set[str]
    ) -> Tuple[Optional[str], List[Tuple[str, str, int]]]:
        """
        Process a single page in forward direction (for parallel processing).
        
        Returns:
            (intersection_page, [(link, predecessor, depth)])
        """
        max_links = self._get_link_limit(current_depth)
        all_links = self.wiki.get_links(page, max_links=max_links, target=target, training_mode=self.training_mode)
        
        # Quick checks first
        for link in all_links:
            # Check if reached target (instant win)
            if link == target:
                return (link, [(link, page, current_depth + 1)])
            
            # Check intersection (instant win)
            if link in reverse_visited_set:
                return (link, [(link, page, current_depth + 1)])
        
        # ✅ PURE BFS: No semantic filtering (too slow!)
        # BFS order is good enough, and MUCH faster
        links = all_links[:max_links]
        
        # Add new links
        new_links = []
        for link in links:
            if link not in forward_visited_set:
                new_links.append((link, page, current_depth + 1))
        
        return (None, new_links)
    
    def _process_page_reverse(
        self,
        page: str,
        start: str,
        current_depth: int,
        forward_visited_set: Set[str],
        reverse_visited_set: Set[str]
    ) -> Tuple[Optional[str], List[Tuple[str, str, int]]]:
        """
        Process a single page in reverse direction (for parallel processing).
        
        Returns:
            (intersection_page, [(link, predecessor, depth)])
        """
        max_links = self._get_link_limit(current_depth)
        
        if not self.training_mode:
            return (None, [])
        
        all_links = self.wiki.get_incoming_links(page, limit=max_links)
        
        # Quick checks first
        for link in all_links:
            # Check if reached start (instant win)
            if link == start:
                return (link, [(link, page, current_depth + 1)])
            
            # Check intersection (instant win)
            if link in forward_visited_set:
                return (link, [(link, page, current_depth + 1)])
        
        # ✅ PURE BFS: No semantic filtering (too slow!)
        # BFS order is good enough, and MUCH faster
        links = all_links[:max_links]
        
        # Add new links
        new_links = []
        for link in links:
            if link not in reverse_visited_set:
                new_links.append((link, page, current_depth + 1))
        
        return (None, new_links)
    
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
        
        # Fast lookup sets for O(1) intersection checks
        forward_visited_set: Set[str] = {start}
        reverse_visited_set: Set[str] = {target}
        
        # Queues for BFS
        forward_queue: deque = deque([start])
        reverse_queue: deque = deque([target])
        
        pages_explored = 0
        
        # Alternating search loop
        for depth in range(self.max_depth):
            # Check for interruption (Ctrl+C)
            if self.interrupted:
                if verbose:
                    print(f"\n⚠️  Search interrupted by user")
                break
            
            # Check timeout
            if time.time() - start_time > self.timeout:
                if verbose:
                    print(f"\n⏱️  Timeout ({self.timeout}s) - stopping search")
                break
            
            # Check queue size (prevent memory explosion)
            # If queue too large, keep only most promising paths
            if len(forward_queue) > 2000:
                if verbose:
                    print(f"\n⚠️  Forward queue large ({len(forward_queue)}) - pruning to 1000")
                # Keep first 1000 (BFS order = closest to start)
                forward_queue = deque(list(forward_queue)[:1000])
            
            if len(reverse_queue) > 2000:
                if verbose:
                    print(f"\n⚠️  Reverse queue large ({len(reverse_queue)}) - pruning to 1000")
                # Keep first 1000 (BFS order = closest to target)
                reverse_queue = deque(list(reverse_queue)[:1000])
            
            if verbose:
                print(f"   Depth {depth + 1}/{self.max_depth} | Forward: {len(forward_queue)}, Reverse: {len(reverse_queue)}")
            
            # Forward search
            if forward_queue:
                intersection = self._forward_bfs(
                    start, target,
                    forward_visited, reverse_visited,
                    forward_visited_set, reverse_visited_set,
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
                    forward_visited_set, reverse_visited_set,
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
        forward_visited_set: Set[str],
        reverse_visited_set: Set[str],
        queue: deque
    ) -> Optional[str]:
        """
        Forward BFS step.
        
        Args:
            start: Start page
            target: Target page
            forward_visited: Forward visited dict
            reverse_visited: Reverse visited dict
            forward_visited_set: Fast lookup set for forward visited
            reverse_visited_set: Fast lookup set for reverse visited
            queue: Forward queue
        
        Returns:
            Intersection page if found, None otherwise
        """
        if not queue:
            return None
        
        # ✅ ULTRA FAST: Process pages in SMALL batches with parallel processing
        # Don't wait for entire level - process immediately!
        batch_size = min(len(queue), 20)  # Process up to 20 pages at once
        pages_to_process = []
        
        for _ in range(batch_size):
            if not queue:
                break
            current = queue.popleft()
            current_depth = forward_visited[current][1]
            pages_to_process.append((current, current_depth))
        
        # ALWAYS use parallel processing (even for 1 page - overhead is minimal)
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(
                    self._process_page_forward,
                    page,
                    target,
                    depth,
                    forward_visited_set,
                    reverse_visited_set
                ): (page, depth) for page, depth in pages_to_process
            }
            
            for future in as_completed(futures):
                page, depth = futures[future]
                intersection, new_links = future.result()
                
                # If intersection found, update and return IMMEDIATELY
                if intersection:
                    for link, pred, link_depth in new_links:
                        forward_visited[link] = (pred, link_depth)
                        forward_visited_set.add(link)
                    return intersection
                
                # Add new links to queue
                for link, pred, link_depth in new_links:
                    if link not in forward_visited_set:
                        forward_visited[link] = (pred, link_depth)
                        forward_visited_set.add(link)
                        queue.append(link)
        
        return None
    
    def _reverse_bfs(
        self,
        start: str,
        target: str,
        forward_visited: Dict[str, Tuple[Optional[str], int]],
        reverse_visited: Dict[str, Tuple[Optional[str], int]],
        forward_visited_set: Set[str],
        reverse_visited_set: Set[str],
        queue: deque
    ) -> Optional[str]:
        """
        Reverse BFS step.
        
        Args:
            start: Start page
            target: Target page
            forward_visited: Forward visited dict
            reverse_visited: Reverse visited dict
            forward_visited_set: Fast lookup set for forward visited
            reverse_visited_set: Fast lookup set for reverse visited
            queue: Reverse queue
        
        Returns:
            Intersection page if found, None otherwise
        """
        if not queue:
            return None
        
        # ✅ ULTRA FAST: Process pages in SMALL batches with parallel processing
        # Don't wait for entire level - process immediately!
        batch_size = min(len(queue), 20)  # Process up to 20 pages at once
        pages_to_process = []
        
        for _ in range(batch_size):
            if not queue:
                break
            current = queue.popleft()
            current_depth = reverse_visited[current][1]
            pages_to_process.append((current, current_depth))
        
        # ALWAYS use parallel processing (even for 1 page - overhead is minimal)
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(
                    self._process_page_reverse,
                    page,
                    start,
                    depth,
                    forward_visited_set,
                    reverse_visited_set
                ): (page, depth) for page, depth in pages_to_process
            }
            
            for future in as_completed(futures):
                page, depth = futures[future]
                intersection, new_links = future.result()
                
                # If intersection found, update and return IMMEDIATELY
                if intersection:
                    for link, pred, link_depth in new_links:
                        reverse_visited[link] = (pred, link_depth)
                        reverse_visited_set.add(link)
                    return intersection
                
                # Add new links to queue
                for link, pred, link_depth in new_links:
                    if link not in reverse_visited_set:
                        reverse_visited[link] = (pred, link_depth)
                        reverse_visited_set.add(link)
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