"""
Bidirectional BFS Navigator - Wikipedia speedruns reposundan esinlenildi.
İki yönlü BFS ile optimal path bulma.
"""

from typing import List, Dict, Tuple, Optional
import time
from collections import deque

from .knowledge_graph import WikiKnowledgeGraph
from .scraper import WikipediaScraper


class BidirectionalNavigator:
    """
    Bidirectional BFS navigator - hem baştan hem sondan arama yaparak
    optimal path'i daha hızlı bulur.
    
    Wikipedia speedruns reposundan öğrenilen pattern:
    - Batch processing (200 sayfa aynı anda)
    - Depth-based processing (aynı derinlikteki node'ları birlikte işle)
    - İki yönlü arama (forward + reverse)
    """
    
    def __init__(self, knowledge_graph: WikiKnowledgeGraph, scraper: WikipediaScraper):
        self.kg = knowledge_graph
        self.scraper = scraper
        self.batch_size = 200  # Wikipedia speedruns'dan öğrenilen optimal değer
        
    def find_path(self, start: str, end: str, max_depth: int = 6) -> Tuple[List[str], float]:
        """
        İki yönlü BFS ile path bulma.
        
        Args:
            start: Başlangıç makalesi
            end: Hedef makale
            max_depth: Maksimum arama derinliği
            
        Returns:
            (path, time_taken) tuple
        """
        start_time = time.time()
        
        # Aynı makale kontrolü
        if start == end:
            return [start], time.time() - start_time
        
        # KG'de varsa direkt kullan
        path = self.kg.find_path(start, end)
        if path:
            return path, time.time() - start_time
        
        # Bidirectional search
        try:
            path = self._bidirectional_search(start, end, max_depth)
            
            # Başarılı path'i KG'ye ekle
            if path and len(path) > 1:
                self.kg.add_path(path, success=True, path_quality=1.0)
            
            return path, time.time() - start_time
            
        except Exception as e:
            print(f"Bidirectional search failed: {e}")
            return [], time.time() - start_time
    
    def _bidirectional_search(self, start: str, end: str, max_depth: int) -> List[str]:
        """
        İki yönlü BFS implementasyonu.
        Wikipedia speedruns pattern'i kullanılarak optimize edildi.
        """
        # Visited dictionaries: {article: (predecessor, depth)}
        forward_visited: Dict[str, Tuple[Optional[str], int]] = {start: (None, 0)}
        reverse_visited: Dict[str, Tuple[Optional[str], int]] = {end: (None, 0)}
        
        # Queues
        forward_queue = deque([start])
        reverse_queue = deque([end])
        
        # Bidirectional search loop
        while forward_queue or reverse_queue:
            # Forward search
            if forward_queue:
                intersection = self._forward_bfs(
                    start, end, forward_visited, reverse_visited, 
                    forward_queue, max_depth
                )
                if intersection:
                    return self._trace_bidirectional_path(
                        intersection, start, end, 
                        forward_visited, reverse_visited
                    )
            
            # Reverse search
            if reverse_queue:
                intersection = self._reverse_bfs(
                    start, end, forward_visited, reverse_visited,
                    reverse_queue, max_depth
                )
                if intersection:
                    return self._trace_bidirectional_path(
                        intersection, start, end,
                        forward_visited, reverse_visited
                    )
        
        return []
    
    def _forward_bfs(
        self, 
        start: str, 
        end: str,
        forward_visited: Dict[str, Tuple[Optional[str], int]],
        reverse_visited: Dict[str, Tuple[Optional[str], int]],
        queue: deque,
        max_depth: int
    ) -> Optional[str]:
        """Forward BFS - başlangıçtan hedefe doğru arama."""
        
        if not queue:
            return None
        
        # Batch processing - aynı derinlikteki node'ları birlikte işle
        batch = []
        starting_depth = forward_visited[queue[0]][1]
        
        # Max depth kontrolü
        if starting_depth >= max_depth:
            return None
        
        # Batch'i doldur (aynı derinlikteki node'lar)
        while queue and len(batch) < self.batch_size:
            article = queue.popleft()
            
            if forward_visited[article][1] != starting_depth:
                queue.appendleft(article)
                break
            
            batch.append(article)
        
        # Batch'teki tüm article'ların linklerini al
        for article in batch:
            links = self._get_links(article)
            
            for link in links:
                # Hedef bulundu mu?
                if link == end:
                    forward_visited[link] = (article, forward_visited[article][1] + 1)
                    return link
                
                # Intersection bulundu mu?
                if link in reverse_visited:
                    forward_visited[link] = (article, forward_visited[article][1] + 1)
                    return link
                
                # Yeni node, queue'ya ekle
                if link not in forward_visited:
                    forward_visited[link] = (article, forward_visited[article][1] + 1)
                    queue.append(link)
        
        return None
    
    def _reverse_bfs(
        self,
        start: str,
        end: str,
        forward_visited: Dict[str, Tuple[Optional[str], int]],
        reverse_visited: Dict[str, Tuple[Optional[str], int]],
        queue: deque,
        max_depth: int
    ) -> Optional[str]:
        """Reverse BFS - hedeften başlangıca doğru arama."""
        
        if not queue:
            return None
        
        # Batch processing
        batch = []
        starting_depth = reverse_visited[queue[0]][1]
        
        # Max depth kontrolü
        if starting_depth >= max_depth:
            return None
        
        # Batch'i doldur
        while queue and len(batch) < self.batch_size:
            article = queue.popleft()
            
            if reverse_visited[article][1] != starting_depth:
                queue.appendleft(article)
                break
            
            batch.append(article)
        
        # Batch'teki tüm article'ların incoming linklerini al
        # (reverse search için incoming links gerekli)
        for article in batch:
            # Reverse için: hangi sayfalar bu sayfaya link veriyor?
            incoming_links = self._get_incoming_links(article)
            
            for link in incoming_links:
                # Başlangıç bulundu mu?
                if link == start:
                    reverse_visited[link] = (article, reverse_visited[article][1] + 1)
                    return link
                
                # Intersection bulundu mu?
                if link in forward_visited:
                    reverse_visited[link] = (article, reverse_visited[article][1] + 1)
                    return link
                
                # Yeni node, queue'ya ekle
                if link not in reverse_visited:
                    reverse_visited[link] = (article, reverse_visited[article][1] + 1)
                    queue.append(link)
        
        return None
    
    def _trace_bidirectional_path(
        self,
        intersection: str,
        start: str,
        end: str,
        forward_visited: Dict[str, Tuple[Optional[str], int]],
        reverse_visited: Dict[str, Tuple[Optional[str], int]]
    ) -> List[str]:
        """Intersection'dan path'i trace et."""
        
        # Forward path (start -> intersection)
        forward_path = self._trace_path(forward_visited, intersection, start)
        
        # Reverse path (intersection -> end)
        reverse_path = self._trace_path(reverse_visited, intersection, end)
        
        # Birleştir (intersection'ı tekrar ekleme)
        return forward_path + reverse_path[1:]
    
    def _trace_path(
        self,
        visited: Dict[str, Tuple[Optional[str], int]],
        current: str,
        target: str
    ) -> List[str]:
        """Visited dictionary'den path'i trace et."""
        
        path = []
        while current != target:
            path.append(current)
            predecessor = visited[current][0]
            if predecessor is None:
                break
            current = predecessor
        
        path.append(target)
        return list(reversed(path))
    
    def _get_links(self, article: str) -> List[str]:
        """Article'ın outgoing linklerini al."""
        
        # Önce KG'de var mı bak
        if self.kg.graph.has_node(article):
            return list(self.kg.graph.successors(article))
        
        # Yoksa Wikipedia'dan çek
        try:
            soup = self.scraper.get_page_html(article)
            if soup:
                links = self.scraper.get_wiki_links(soup)
                return links[:100]  # İlk 100 link (performans için)
            return []
        except:
            return []
    
    def _get_incoming_links(self, article: str) -> List[str]:
        """Article'a gelen linkleri al (reverse search için)."""
        
        # KG'de predecessors'ları bul
        if self.kg.graph.has_node(article):
            return list(self.kg.graph.predecessors(article))
        
        # Wikipedia API'de incoming links yok, bu yüzden KG'ye güveniyoruz
        # Alternatif: Wikipedia'nın "What links here" özelliğini kullan
        return []


class PathValidator:
    """
    Path validation - Wikipedia speedruns'dan öğrenilen pattern.
    Path'in geçerli olup olmadığını kontrol eder.
    """
    
    def __init__(self, scraper: WikipediaScraper):
        self.scraper = scraper
    
    def validate_path(self, path: List[str]) -> Tuple[bool, str]:
        """
        Path'in geçerli olup olmadığını kontrol et.
        
        Returns:
            (is_valid, error_message)
        """
        if len(path) < 2:
            return False, "Path must have at least 2 articles"
        
        # Her adımı kontrol et
        for i in range(len(path) - 1):
            current = path[i]
            next_article = path[i + 1]
            
            # Link var mı kontrol et
            try:
                soup = self.scraper.get_page_html(current)
                if soup:
                    links = self.scraper.get_wiki_links(soup)
                    if next_article not in links:
                        return False, f"No link from '{current}' to '{next_article}'"
                else:
                    return False, f"Could not fetch page: {current}"
            except Exception as e:
                return False, f"Error checking link: {e}"
        
        return True, "Valid path"
    
    def validate_against_wikipedia(self, path: List[str]) -> Tuple[bool, str]:
        """
        Path'i Wikipedia'ya karşı doğrula (daha yavaş ama kesin).
        """
        return self.validate_path(path)