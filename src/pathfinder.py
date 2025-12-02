"""
pathfinder_refactored.py
------------------------
Wikipedia sayfaları arasında path finding (refactored version).

Improvements:
- Helper metodlar ile kod tekrarı azaltıldı
- Dataclass ile type-safe results
- Cache statistics tracking
- Daha temiz ve okunabilir kod
"""

import time
from collections import deque
from dataclasses import dataclass
from typing import Optional
from src.scraper import WikipediaScraper


@dataclass
class SearchResult:
    """
    Search sonuçlarını tutan dataclass (type-safe).
    """
    found: bool
    path: list[str]
    steps: int
    pages_explored: int
    time_seconds: float
    max_queue_size: int
    algorithm: str  # "BFS" veya "Bidirectional BFS"


class PathFinder:
    """
    Wikipedia sayfaları arasında en kısa yolu bulan sınıf (refactored).

    Algorithms:
    - BFS (Breadth-First Search)
    - Bidirectional BFS (İki yönlü arama)

    Features:
    - Verbose mode
    - Performance metrics
    - Cache support (WikipediaScraper'dan)
    """

    def __init__(self, verbose: bool = True, cache_size: int = 128):
        """
        PathFinder'ı başlat.

        Parametreler:
            verbose (bool): Detaylı log çıktısı
            cache_size (int): WikipediaScraper cache boyutu
        """
        self.scraper = WikipediaScraper(cache_size=cache_size)
        self.verbose = verbose

        # Metrics (her search'te sıfırlanır)
        self.pages_explored = 0
        self.max_queue_size = 0
        self.start_time = 0

    # ==================== HELPER METODLAR ====================

    def _initialize_search(self):
        """Search metriklerini sıfırla ve timer başlat."""
        self.pages_explored = 0
        self.max_queue_size = 0
        self.start_time = time.time()

    def _elapsed_time(self) -> float:
        """Başlangıçtan şimdiye kadar geçen süre (saniye)."""
        return time.time() - self.start_time

    def _print_header(self, algorithm: str, start: str, target: str):
        """Search başlangıç header'ını yazdır."""
        if not self.verbose:
            return

        print(f"\n{'='*60}")
        print(f"🔍 {algorithm}")
        print(f"{'='*60}")
        print(f"📍 Başlangıç: {start}")
        print(f"🎯 Hedef: {target}")
        print(f"🚀 Arama başlıyor...\n")

    def _get_page_links(self, page: str) -> list[str]:
        """
        Sayfanın linklerini al ve metrics güncelle.

        Bu helper metod:
        1. Sayfayı çek (cache'den veya Wikipedia'dan)
        2. Linkleri extract et
        3. pages_explored sayacını artır
        4. Linkleri döndür
        """
        self.pages_explored += 1

        soup = self.scraper.get_page_html(page)
        if not soup:
            return []

        links = self.scraper.get_wiki_links(soup)

        if self.verbose:
            print(f"    → {page} ({len(links)} link)")

        return links

    def _create_result(self, found: bool, path: list[str], algorithm: str) -> SearchResult:
        """
        SearchResult objesi oluştur.

        DRY principle: Her search metodu bu helper'ı kullanır.
        """
        return SearchResult(
            found=found,
            path=path,
            steps=len(path) - 1 if found else 0,
            pages_explored=self.pages_explored,
            time_seconds=self._elapsed_time(),
            max_queue_size=self.max_queue_size,
            algorithm=algorithm
        )

    def _print_result(self, result: SearchResult):
        """Search sonucunu güzel bir şekilde yazdır."""
        if not self.verbose:
            return

        print(f"\n{'='*60}")
        if result.found:
            print(f"✅ HEDEF BULUNDU!")
        else:
            print(f"❌ HEDEF BULUNAMADI")
        print(f"{'='*60}")

        if result.found:
            print(f"\n🛤️ Bulunan Path:")
            print(f"{'─'*60}")
            for i, page in enumerate(result.path):
                if i == 0:
                    print(f"  🏁 {page}")
                elif i == len(result.path) - 1:
                    print(f"  🎯 {page}")
                else:
                    print(f"  {i}. {page}")

        print(f"\n📊 İstatistikler:")
        print(f"  • Algoritma: {result.algorithm}")
        print(f"  • Adım sayısı: {result.steps}")
        print(f"  • Taranan sayfa: {result.pages_explored}")
        print(f"  • Toplam süre: {result.time_seconds:.2f}s")
        if result.pages_explored > 0:
            print(f"  • Sayfa/saniye: {result.pages_explored / result.time_seconds:.2f}")
        print(f"  • Max queue boyutu: {result.max_queue_size}")

        # Cache statistics
        cache_stats = self.scraper.get_cache_stats()
        if cache_stats['hits'] + cache_stats['misses'] > 0:
            print(f"\n💾 Cache İstatistikleri:")
            print(f"  • Hit rate: {cache_stats['hit_rate']:.1f}%")
            print(f"  • Hits: {cache_stats['hits']}")
            print(f"  • Misses: {cache_stats['misses']}")
            print(f"  • Cache size: {cache_stats['size']}/{cache_stats['max_size']}")

    def _merge_bidirectional_paths(
        self,
        forward_path: list[str],
        backward_path: list[str]
    ) -> list[str]:
        """
        Forward ve backward path'leri birleştir.

        Örnek:
            forward_path = [A, B, C, X]
            backward_path = [Z, Y, X]
            result = [A, B, C, X, Y, Z]

        NOT: X kesişme noktası, tekrar eklenmemeli!
        """
        # backward_path'i ters çevir ve son elemanı atla (kesişme noktası)
        return forward_path + backward_path[-2::-1]

    # ==================== SEARCH ALGORITMALARI ====================

    def bfs_search(
        self,
        start: str,
        target: str,
        max_depth: int = 6
    ) -> SearchResult:
        """
        BFS (Breadth-First Search) algoritması.

        En kısa path'i garanti eder.
        Complexity: O(k^d) - k=avg links, d=depth
        """
        self._initialize_search()
        self._print_header("BFS SEARCH", start, target)

        # Edge case
        if start == target:
            result = self._create_result(True, [start], "BFS")
            self._print_result(result)
            return result

        # BFS setup
        queue = deque([(start, [start])])
        visited = {start}
        current_depth = 0

        # Main loop
        while queue:
            self.max_queue_size = max(self.max_queue_size, len(queue))

            if self.verbose:
                print(f"\n📊 Seviye {current_depth}: {len(queue)} sayfa")

            if current_depth > max_depth:
                break

            level_size = len(queue)

            for _ in range(level_size):
                current_page, path = queue.popleft()

                # Get links
                links = self._get_page_links(current_page)

                for link in links:
                    if link in visited:
                        continue

                    visited.add(link)
                    new_path = path + [link]

                    # Target bulundu mu?
                    if link == target:
                        result = self._create_result(True, new_path, "BFS")
                        self._print_result(result)
                        return result

                    queue.append((link, new_path))

            current_depth += 1
            time.sleep(0.3)  # Rate limiting

        # Bulunamadı
        result = self._create_result(False, [], "BFS")
        self._print_result(result)
        return result

    def bidirectional_bfs_search(
        self,
        start: str,
        target: str,
        max_depth: int = 6
    ) -> SearchResult:
        """
        Bidirectional BFS - İki yönlü arama.

        Hem baştan hem sondan aynı anda arar.
        Complexity: O(2 * k^(d/2)) - Çok daha hızlı!
        """
        self._initialize_search()
        self._print_header("BIDIRECTIONAL BFS SEARCH", start, target)

        # Edge case
        if start == target:
            result = self._create_result(True, [start], "Bidirectional BFS")
            self._print_result(result)
            return result

        # Two-way BFS setup
        forward_queue = deque([(start, [start])])
        backward_queue = deque([(target, [target])])
        forward_visited = {start: [start]}
        backward_visited = {target: [target]}
        forward_depth = 0
        backward_depth = 0

        # Main loop
        while forward_queue and backward_queue:
            total_queue = len(forward_queue) + len(backward_queue)
            self.max_queue_size = max(self.max_queue_size, total_queue)

            if self.verbose:
                print(f"\n📊 Depth: F{forward_depth} / B{backward_depth}")
                print(f"   Queue: F{len(forward_queue)} / B{len(backward_queue)}")

            if forward_depth > max_depth and backward_depth > max_depth:
                break

            # FORWARD SEARCH
            if forward_queue and forward_depth <= max_depth:
                intersection = self._bfs_step(
                    queue=forward_queue,
                    visited=forward_visited,
                    other_visited=backward_visited,
                    direction="forward"
                )

                if intersection:
                    # Kesişme bulundu!
                    complete_path = self._merge_bidirectional_paths(
                        forward_visited[intersection],
                        backward_visited[intersection]
                    )
                    result = self._create_result(True, complete_path, "Bidirectional BFS")

                    if self.verbose:
                        print(f"\n🔗 Kesişme noktası: {intersection}")

                    self._print_result(result)
                    return result

                forward_depth += 1
                time.sleep(0.3)

            # BACKWARD SEARCH
            if backward_queue and backward_depth <= max_depth:
                intersection = self._bfs_step(
                    queue=backward_queue,
                    visited=backward_visited,
                    other_visited=forward_visited,
                    direction="backward"
                )

                if intersection:
                    # Kesişme bulundu!
                    complete_path = self._merge_bidirectional_paths(
                        forward_visited[intersection],
                        backward_visited[intersection]
                    )
                    result = self._create_result(True, complete_path, "Bidirectional BFS")

                    if self.verbose:
                        print(f"\n🔗 Kesişme noktası: {intersection}")

                    self._print_result(result)
                    return result

                backward_depth += 1
                time.sleep(0.3)

        # Bulunamadı
        result = self._create_result(False, [], "Bidirectional BFS")
        self._print_result(result)
        return result

    def _bfs_step(
        self,
        queue: deque,
        visited: dict,
        other_visited: dict,
        direction: str
    ) -> Optional[str]:
        """
        Bidirectional BFS için bir seviye işle.

        Returns:
            Kesişme noktası (varsa), yoksa None
        """
        level_size = len(queue)
        symbol = "🔵" if direction == "forward" else "🔴"

        if self.verbose:
            print(f"  {symbol} {direction.capitalize()}: {level_size} sayfa")

        for _ in range(level_size):
            current_page, path = queue.popleft()

            # Get links
            links = self._get_page_links(current_page)

            for link in links:
                if link in visited:
                    continue

                new_path = path + [link]
                visited[link] = new_path

                # Kesişme kontrolü
                if link in other_visited:
                    return link  # KESIŞME BULUNDU!

                queue.append((link, new_path))

        return None  # Kesişme yok

    def get_scraper_stats(self) -> dict:
        """WikipediaScraper cache istatistiklerini döndür."""
        return self.scraper.get_cache_stats()
