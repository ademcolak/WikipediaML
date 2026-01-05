"""
Wikipedia Interface - Scraping ve Embedding
Tek class, basit, etkili.
"""

import requests
import aiohttp
import asyncio
from bs4 import BeautifulSoup, Tag
from sentence_transformers import SentenceTransformer
import diskcache
from typing import List, Optional, Union
import numpy as np
from pathlib import Path


class Wikipedia:
    """
    Wikipedia interface - scraping ve embedding.
    
    Özellikler:
    - Page scraping (BeautifulSoup)
    - Link extraction
    - Semantic embeddings (SentenceTransformer)
    - LRU cache (hız için)
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', cache_dir: str = 'data/cache'):
        """
        Initialize Wikipedia interface.
        
        Args:
            model_name: SentenceTransformer model (default: all-MiniLM-L6-v2)
                       - Fast and efficient (2-3x faster than all-mpnet-base-v2)
                       - 384 dimensions (vs 768)
                       - ~80MB model size (vs ~420MB)
                       - Minimal accuracy loss (~2-3%)
            cache_dir: Directory for disk cache (default: data/cache)
        """
        self.base_url = "https://en.wikipedia.org/wiki/"
        self.model = SentenceTransformer(model_name)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WikipediaML/2.0 (Educational Project)'
        })
        
        # Async session (created on demand)
        self._async_session: Optional[aiohttp.ClientSession] = None
        
        # Disk cache setup (10GB limit, 7 days expiry)
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        self.html_cache = diskcache.Cache(f'{cache_dir}/html', size_limit=5 * 1024**3)  # 5GB
        self.embedding_cache = diskcache.Cache(f'{cache_dir}/embeddings', size_limit=5 * 1024**3)  # 5GB
        
        # Statistics
        self.pages_fetched = 0
        self.cache_hits = 0
        self.cache_misses = 0
    
    def get_page_html(self, page: str) -> Optional[Tag]:
        """
        Fetch page HTML with disk cache.
        
        Args:
            page: Wikipedia page name (e.g., "Python_(programming_language)")
        
        Returns:
            BeautifulSoup object or None if error
        """
        # Check disk cache first
        cache_key = f"html:{page}"
        cached_html = self.html_cache.get(cache_key, default=None)
        if cached_html is not None and isinstance(cached_html, bytes):
            self.cache_hits += 1
            return BeautifulSoup(cached_html, 'html.parser')
        
        self.cache_misses += 1
        
        try:
            url = self.base_url + page
            response = self.session.get(url, timeout=5)
            
            if response.status_code == 200:
                self.pages_fetched += 1
                # Cache HTML content (expires in 7 days)
                self.html_cache.set(cache_key, response.content, expire=86400 * 7)
                return BeautifulSoup(response.content, 'html.parser')
            
            return None
            
        except Exception as e:
            # Silent error handling
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
    
    
    def get_embedding(self, page: str) -> np.ndarray:
        """
        Get semantic embedding for a page with disk cache.
        
        Args:
            page: Wikipedia page name
        
        Returns:
            Embedding vector (384 dimensions)
        """
        # Check disk cache first
        cache_key = f"emb:{page}"
        cached = self.embedding_cache.get(cache_key)
        if cached is not None:
            return np.array(cached)
        
        # Use page name as text (simple but effective)
        text = page.replace('_', ' ')
        
        # Get embedding
        embedding = self.model.encode(text, convert_to_numpy=True)
        
        # Cache embedding as list (expires in 30 days)
        self.embedding_cache.set(cache_key, embedding.tolist(), expire=86400 * 30)
        
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
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_hit_rate': (self.cache_hits / (self.cache_hits + self.cache_misses) * 100) if (self.cache_hits + self.cache_misses) > 0 else 0,
            'disk_cache': {
                'html_items': self.html_cache.volume(),
                'embedding_items': self.embedding_cache.volume()
            }
        }
    
    async def _get_async_session(self) -> aiohttp.ClientSession:
        """Get or create async session."""
        if self._async_session is None or self._async_session.closed:
            self._async_session = aiohttp.ClientSession(
                headers={'User-Agent': 'WikipediaML/2.0 (Educational Project)'},
                timeout=aiohttp.ClientTimeout(total=5)
            )
        return self._async_session
    
    async def async_get_page_html(self, page: str) -> Optional[Tag]:
        """
        Async fetch page HTML with disk cache.
        
        Args:
            page: Wikipedia page name
        
        Returns:
            BeautifulSoup object or None if error
        """
        # Check disk cache first (synchronous, but fast)
        cache_key = f"html:{page}"
        cached_html = self.html_cache.get(cache_key, default=None)
        if cached_html is not None and isinstance(cached_html, bytes):
            self.cache_hits += 1
            return BeautifulSoup(cached_html, 'html.parser')
        
        self.cache_misses += 1
        
        try:
            session = await self._get_async_session()
            url = self.base_url + page
            
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    self.pages_fetched += 1
                    # Cache HTML content (expires in 7 days)
                    self.html_cache.set(cache_key, content, expire=86400 * 7)
                    return BeautifulSoup(content, 'html.parser')
            
            return None
            
        except Exception as e:
            # Silent error handling
            return None
    
    async def async_get_links(self, page: str, max_links: int = 50) -> List[str]:
        """
        Async get valid Wikipedia links from a page.
        
        Args:
            page: Wikipedia page name
            max_links: Maximum number of links to return
        
        Returns:
            List of linked page names
        """
        soup = await self.async_get_page_html(page)
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
        
        return unique_links[:max_links]
    
    async def async_batch_fetch(self, pages: List[str], max_concurrent: int = 10) -> dict[str, Optional[Tag]]:
        """
        Fetch multiple pages concurrently (FAST!).
        
        This is the main benefit of async - fetch 10 pages at once instead of sequentially.
        
        Args:
            pages: List of page names to fetch
            max_concurrent: Maximum concurrent requests (default: 10)
        
        Returns:
            Dictionary mapping page names to BeautifulSoup objects
        """
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def fetch_with_semaphore(page: str) -> tuple[str, Optional[Tag]]:
            async with semaphore:
                soup = await self.async_get_page_html(page)
                return page, soup
        
        # Fetch all pages concurrently
        tasks = [fetch_with_semaphore(page) for page in pages]
        results = await asyncio.gather(*tasks)
        
        # Convert to dictionary
        return {page: soup for page, soup in results}
    
    async def close_async_session(self):
        """Close async session."""
        if self._async_session and not self._async_session.closed:
            await self._async_session.close()
    
    def clear_cache(self):
        """Clear all disk caches."""
        self.html_cache.clear()
        self.embedding_cache.clear()
        print("🧹 Disk caches cleared")