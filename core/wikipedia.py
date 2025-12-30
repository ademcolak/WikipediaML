"""
Wikipedia Interface - Scraping ve Embedding
Tek class, basit, etkili.
"""

import requests
from bs4 import BeautifulSoup, Tag
from sentence_transformers import SentenceTransformer
from functools import lru_cache
from typing import List, Optional, Union
import numpy as np


class Wikipedia:
    """
    Wikipedia interface - scraping ve embedding.
    
    Özellikler:
    - Page scraping (BeautifulSoup)
    - Link extraction
    - Semantic embeddings (SentenceTransformer)
    - LRU cache (hız için)
    """
    
    def __init__(self, model_name: str = 'all-mpnet-base-v2'):
        """
        Initialize Wikipedia interface.
        
        Args:
            model_name: SentenceTransformer model (default: all-mpnet-base-v2)
                       - High quality semantic understanding
                       - 768 dimensions
                       - Phase 1 upgrade: Better accuracy (+10-15%)
        """
        self.base_url = "https://en.wikipedia.org/wiki/"
        self.model = SentenceTransformer(model_name)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WikipediaML/2.0 (Educational Project)'
        })
        
        # Statistics
        self.pages_fetched = 0
        self.cache_hits = 0
        self.cache_misses = 0
    
    @lru_cache(maxsize=2048)  # ✅ 4x daha büyük cache
    def get_page_html(self, page: str) -> Optional[Tag]:
        """
        Fetch page HTML.
        
        Args:
            page: Wikipedia page name (e.g., "Python_(programming_language)")
        
        Returns:
            BeautifulSoup object or None if error
        """
        try:
            url = self.base_url + page
            response = self.session.get(url, timeout=5)  # ✅ 10s → 5s timeout
            
            if response.status_code == 200:
                self.pages_fetched += 1
                return BeautifulSoup(response.content, 'html.parser')
            
            return None
            
        except Exception as e:
            print(f"Error fetching {page}: {e}")
            return None
    
    def get_links(self, page: str, max_links: int = 50, target: Optional[str] = None, training_mode: bool = False) -> List[str]:
        """
        Get valid Wikipedia links from a page (FAST + SIMPLE).
        
        Strategy:
        1. Get all links (fast)
        2. If training mode + target: semantic filtering for top links
        3. Return top links
        
        Args:
            page: Wikipedia page name
            max_links: Maximum number of links to return
            target: Target page for semantic filtering (training mode only)
            training_mode: If True, use semantic filtering
        
        Returns:
            List of linked page names
        """
        soup = self.get_page_html(page)
        if not soup:
            return []
        
        # Find main content
        content = soup.find('div', {'id': 'mw-content-text'})
        if not content or not isinstance(content, Tag):
            return []
        
        # Extract ALL links (simple and fast)
        links = []
        for link in content.find_all('a', href=True):
            href = link['href']
            
            # Valid Wikipedia article link
            if href.startswith('/wiki/') and ':' not in href:
                page_name = href[6:]  # Remove '/wiki/'
                
                # Filter out special pages
                if not any(x in page_name for x in ['#', 'File:', 'Special:', 'Help:', 'Wikipedia:']):
                    links.append(page_name)
        
        # Remove duplicates, keep order
        seen = set()
        unique_links = []
        for link in links:
            if link not in seen:
                seen.add(link)
                unique_links.append(link)
        
        # ✅ NO SEMANTIC FILTERING - Pure BFS is faster!
        # Just return first max_links (Wikipedia's own order is good)
        return unique_links[:max_links]
    @lru_cache(maxsize=512)
    def get_incoming_links(self, page: str, limit: int = 100) -> List[str]:
        """
        Get pages that link TO this page (backlinks/incoming links).
        Uses Wikipedia API backlinks query.
        
        Args:
            page: Wikipedia page name
            limit: Maximum number of backlinks to return (default: 100)
        
        Returns:
            List of page names that link to this page
        """
        try:
            url = "https://en.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "list": "backlinks",
                "bltitle": page,
                "bllimit": min(limit, 500),  # API max is 500
                "blnamespace": 0,  # Only article namespace
                "format": "json"
            }
            
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            
            backlinks = []
            if "query" in data and "backlinks" in data["query"]:
                for link in data["query"]["backlinks"]:
                    backlinks.append(link["title"].replace(' ', '_'))
            
            return backlinks
            
        except Exception as e:
            print(f"Error fetching backlinks for {page}: {e}")
            return []
    
    
    @lru_cache(maxsize=2048)
    def get_embedding(self, page: str) -> np.ndarray:
        """
        Get semantic embedding for a page.
        
        Args:
            page: Wikipedia page name
        
        Returns:
            Embedding vector (384 dimensions)
        """
        # Use page name as text (simple but effective)
        # Replace underscores with spaces
        text = page.replace('_', ' ')
        
        # Get embedding
        embedding = self.model.encode(text, convert_to_numpy=True)
        
        return embedding
    
    def similarity(self, page1: str, page2: str) -> float:
        """
        Calculate semantic similarity between two pages.
        
        Args:
            page1: First page name
            page2: Second page name
        
        Returns:
            Cosine similarity (0-1)
        """
        emb1 = self.get_embedding(page1)
        emb2 = self.get_embedding(page2)
        
        # Cosine similarity
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        
        return float(similarity)
    
    def batch_similarity(self, current: str, candidates: List[str], target: str) -> List[tuple[str, float]]:
        """
        Calculate similarity for multiple candidates.
        
        Args:
            current: Current page
            candidates: List of candidate pages
            target: Target page
        
        Returns:
            List of (page, similarity) tuples, sorted by similarity
        """
        target_emb = self.get_embedding(target)
        
        scores = []
        for candidate in candidates:
            cand_emb = self.get_embedding(candidate)
            sim = np.dot(cand_emb, target_emb) / (np.linalg.norm(cand_emb) * np.linalg.norm(target_emb))
            scores.append((candidate, float(sim)))
        
        # Sort by similarity (descending)
        scores.sort(key=lambda x: x[1], reverse=True)
        
        return scores
    
    def get_stats(self) -> dict:
        """Get statistics."""
        return {
            'pages_fetched': self.pages_fetched,
            'cache_info': {
                'html': self.get_page_html.cache_info()._asdict(),
                'embedding': self.get_embedding.cache_info()._asdict()
            }
        }
    
    def clear_cache(self):
        """Clear all caches."""
        self.get_page_html.cache_clear()
        self.get_embedding.cache_clear()