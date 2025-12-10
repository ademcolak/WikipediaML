"""
async_scraper.py
----------------
Asynchronous Wikipedia scraper for parallel page fetching.
Bu modül, birden fazla Wikipedia sayfasını paralel olarak çekerek
performansı 4-5x artırır.

Performance Comparison:
    Sync (Sequential):  4 pages × 500ms = 2000ms
    Async (Parallel):   4 pages in parallel = 500ms (4x faster!)

Optimizations (Phase 1):
    - Adaptive batch sizing (network speed'e göre)
    - Persistent connection pooling
    - Smart rate limiting
    - Performance tracking
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup, Tag
from collections import OrderedDict
from typing import Optional, List, Dict, Tuple
import time
import statistics


class AsyncWikipediaScraper:
    """
    Asynchronous Wikipedia scraper with parallel fetching capability.
    
    Features:
    - Parallel page fetching (4-5x faster than sync)
    - Async/await pattern
    - Connection pooling (aiohttp.ClientSession)
    - LRU Cache (same as sync version)
    - Cache statistics
    - Batch operations
    
    Usage:
        scraper = AsyncWikipediaScraper()
        
        # Single page
        soup = await scraper.get_page_html("Potato")
        
        # Multiple pages (parallel!)
        soups = await scraper.get_pages_batch(["Potato", "Pizza", "Italy"])
    """
    
    def __init__(
        self,
        cache_size: int = 128,
        timeout: int = 10,
        max_concurrent: int = 10,
        adaptive_batching: bool = True
    ):
        """
        Initialize AsyncWikipediaScraper.
        
        Args:
            cache_size: Maximum number of pages to cache (LRU)
            timeout: HTTP request timeout in seconds
            max_concurrent: Maximum concurrent requests (default: 10)
            adaptive_batching: Enable adaptive batch sizing (default: True)
        """
        self.base_url = "https://en.wikipedia.org/wiki/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_concurrent = max_concurrent
        self.adaptive_batching = adaptive_batching
        
        # Cache (same as sync version)
        self._cache = OrderedDict()
        self._cache_size = cache_size
        
        # Statistics
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_fetch_time = 0.0
        self.total_fetches = 0
        
        # Adaptive batching metrics
        self.fetch_times = []  # Track recent fetch times
        self.optimal_batch_size = max_concurrent
        
        # Semaphore for limiting concurrent requests
        self._semaphore = asyncio.Semaphore(max_concurrent)
        
        # Persistent session (connection pooling)
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def get_page_html(self, page_title: str) -> Optional[BeautifulSoup]:
        """
        Fetch a single Wikipedia page (async).
        
        Args:
            page_title: Wikipedia page title (e.g., "Potato")
            
        Returns:
            BeautifulSoup object or None if failed
            
        Cache Logic:
            1. Check cache → Return if found (CACHE HIT)
            2. Fetch from Wikipedia → Add to cache → Return (CACHE MISS)
            3. If cache full → Remove oldest entry (LRU)
        """
        # Check cache
        if page_title in self._cache:
            self.cache_hits += 1
            self._cache.move_to_end(page_title)
            return self._cache[page_title]
        
        # Cache miss: fetch from Wikipedia
        self.cache_misses += 1
        soup = await self._fetch_from_wikipedia(page_title)
        
        if soup:
            self._add_to_cache(page_title, soup)
        
        return soup
    
    async def get_pages_batch(self, page_titles: List[str]) -> Dict[str, Optional[BeautifulSoup]]:
        """
        Fetch multiple Wikipedia pages in parallel (MAIN PERFORMANCE BOOST!).
        
        Args:
            page_titles: List of Wikipedia page titles
            
        Returns:
            Dict mapping page_title → BeautifulSoup (or None if failed)
            
        Performance:
            Sequential: 4 pages × 500ms = 2000ms
            Parallel:   4 pages in parallel = 500ms (4x faster!)
            
        Example:
            pages = await scraper.get_pages_batch(["Potato", "Pizza", "Italy"])
            # pages = {
            #     "Potato": <BeautifulSoup>,
            #     "Pizza": <BeautifulSoup>,
            #     "Italy": <BeautifulSoup>
            # }
        """
        # Separate cached and non-cached pages
        cached_pages = {}
        pages_to_fetch = []
        
        for title in page_titles:
            if title in self._cache:
                self.cache_hits += 1
                self._cache.move_to_end(title)
                cached_pages[title] = self._cache[title]
            else:
                self.cache_misses += 1
                pages_to_fetch.append(title)
        
        # Fetch non-cached pages in parallel
        if pages_to_fetch:
            fetched_pages = await self._fetch_pages_parallel(pages_to_fetch)
            
            # Add to cache
            for title, soup in fetched_pages.items():
                if soup:
                    self._add_to_cache(title, soup)
            
            # Merge results
            cached_pages.update(fetched_pages)
        
        return cached_pages
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """
        Get or create persistent session (connection pooling).
        
        Connection pooling benefits:
        - Reuse TCP connections
        - Faster subsequent requests
        - Lower overhead
        """
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(
                limit=self.max_concurrent,
                limit_per_host=self.max_concurrent,
                ttl_dns_cache=300  # Cache DNS for 5 minutes
            )
            self._session = aiohttp.ClientSession(
                timeout=self.timeout,
                connector=connector,
                headers=self.headers
            )
        return self._session
    
    async def _fetch_from_wikipedia(self, page_title: str) -> Optional[BeautifulSoup]:
        """
        Fetch a single page from Wikipedia (async network call).
        
        This method is only called on cache miss.
        Uses persistent session for connection pooling.
        """
        url = self.base_url + page_title
        
        async with self._semaphore:  # Limit concurrent requests
            try:
                start_time = time.time()
                
                session = await self._get_session()
                async with session.get(url) as response:
                    response.raise_for_status()
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                
                # Track performance
                fetch_time = time.time() - start_time
                self.total_fetch_time += fetch_time
                self.total_fetches += 1
                
                # Track for adaptive batching
                if self.adaptive_batching:
                    self.fetch_times.append(fetch_time)
                    if len(self.fetch_times) > 20:
                        self.fetch_times.pop(0)  # Keep last 20
                
                return soup
                
            except Exception as e:
                print(f"❌ Error fetching {page_title}: {e}")
                return None
    
    def _calculate_optimal_batch_size(self) -> int:
        """
        Calculate optimal batch size based on recent performance.
        
        Logic:
        - Fast network (avg < 0.3s): Increase batch size
        - Slow network (avg > 0.8s): Decrease batch size
        - Medium network: Keep current size
        """
        if not self.adaptive_batching or len(self.fetch_times) < 5:
            return self.optimal_batch_size
        
        avg_time = statistics.mean(self.fetch_times)
        
        if avg_time < 0.3:
            # Fast network: increase batch size
            self.optimal_batch_size = min(self.optimal_batch_size + 2, self.max_concurrent * 2)
        elif avg_time > 0.8:
            # Slow network: decrease batch size
            self.optimal_batch_size = max(self.optimal_batch_size - 2, 5)
        
        return self.optimal_batch_size
    
    async def _fetch_pages_parallel(self, page_titles: List[str]) -> Dict[str, Optional[BeautifulSoup]]:
        """
        Fetch multiple pages in parallel (CORE PERFORMANCE OPTIMIZATION).
        
        Uses asyncio.gather() to run all fetches concurrently.
        Now with adaptive batching for optimal performance.
        """
        start_time = time.time()
        
        # Adaptive batching: Split into optimal-sized chunks
        if self.adaptive_batching and len(page_titles) > self.max_concurrent:
            optimal_size = self._calculate_optimal_batch_size()
            
            # Process in chunks
            all_pages = {}
            for i in range(0, len(page_titles), optimal_size):
                chunk = page_titles[i:i + optimal_size]
                
                # Create tasks for chunk
                tasks = [self._fetch_from_wikipedia(title) for title in chunk]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Map results
                for title, result in zip(chunk, results):
                    if isinstance(result, Exception):
                        print(f"❌ Error fetching {title}: {result}")
                        all_pages[title] = None
                    else:
                        all_pages[title] = result
                
                # Small delay between chunks (rate limiting)
                if i + optimal_size < len(page_titles):
                    await asyncio.sleep(0.1)
            
            elapsed = time.time() - start_time
            print(f"⚡ Fetched {len(page_titles)} pages in {elapsed:.2f}s (adaptive batching: {optimal_size})")
            
            return all_pages
        else:
            # Standard parallel fetch (small batch)
            tasks = [self._fetch_from_wikipedia(title) for title in page_titles]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Map results back to page titles
            pages = {}
            for title, result in zip(page_titles, results):
                if isinstance(result, Exception):
                    print(f"❌ Error fetching {title}: {result}")
                    pages[title] = None
                else:
                    pages[title] = result
            
            elapsed = time.time() - start_time
            print(f"⚡ Fetched {len(page_titles)} pages in {elapsed:.2f}s (parallel)")
            
            return pages
    
    def _add_to_cache(self, page_title: str, soup: BeautifulSoup):
        """
        Add page to cache. Remove oldest entry if cache is full (LRU).
        """
        if len(self._cache) >= self._cache_size:
            self._cache.popitem(last=False)  # Remove oldest
        
        self._cache[page_title] = soup
    
    def get_wiki_links(self, soup: BeautifulSoup) -> List[str]:
        """
        Extract all Wikipedia article links from a page.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            List of Wikipedia page titles (e.g., ["United_States", "Vegetable"])
            
        Filtering:
            - Only /wiki/ links
            - Exclude special pages (File:, Help:, Template:, etc.)
            - Exclude anchor links (#)
            - Remove duplicates
        """
        wiki_links = []
        
        excluded_prefixes = (
            "File:", "Help:", "Wikipedia:", "Template:",
            "Category:", "Special:", "Talk:", "Portal:",
            "User:", "Module:",
        )
        
        # Find main content area
        content_div = soup.find('div', id='mw-content-text')
        if not content_div or not isinstance(content_div, Tag):
            return []
        
        # Extract and filter links
        for link in content_div.find_all('a', href=True):
            href = link['href']
            
            if not href.startswith('/wiki/'):
                continue
            
            page_name = href[6:]  # Remove "/wiki/"
            
            if ('#' in page_name or
                page_name.startswith(excluded_prefixes) or
                page_name in wiki_links):
                continue
            
            wiki_links.append(page_name)
        
        return wiki_links
    
    async def get_links_batch(self, page_titles: List[str]) -> Dict[str, List[str]]:
        """
        Fetch multiple pages and extract their links in parallel.
        
        This is a convenience method that combines:
        1. Parallel page fetching
        2. Link extraction
        
        Args:
            page_titles: List of Wikipedia page titles
            
        Returns:
            Dict mapping page_title → list of links
            
        Example:
            links = await scraper.get_links_batch(["Potato", "Pizza"])
            # links = {
            #     "Potato": ["Vegetable", "Food", ...],
            #     "Pizza": ["Italy", "Cheese", ...]
            # }
        """
        # Fetch all pages in parallel
        pages = await self.get_pages_batch(page_titles)
        
        # Extract links from each page
        all_links = {}
        for title, soup in pages.items():
            if soup:
                all_links[title] = self.get_wiki_links(soup)
            else:
                all_links[title] = []
        
        return all_links
    
    def clear_cache(self):
        """Clear cache and reset statistics."""
        self._cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_fetch_time = 0.0
        self.total_fetches = 0
    
    def get_cache_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            dict: {
                'size': Current cache size,
                'max_size': Maximum cache size,
                'hits': Cache hit count,
                'misses': Cache miss count,
                'hit_rate': Hit rate (%),
                'avg_fetch_time': Average fetch time (ms)
            }
        """
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        avg_fetch_time = (self.total_fetch_time / self.total_fetches * 1000) if self.total_fetches > 0 else 0
        
        return {
            'size': len(self._cache),
            'max_size': self._cache_size,
            'hits': self.cache_hits,
            'misses': self.cache_misses,
            'hit_rate': hit_rate,
            'avg_fetch_time': avg_fetch_time
        }
    
    def get_performance_stats(self) -> dict:
        """
        Get performance statistics.
        
        Returns:
            dict: {
                'total_fetches': Total number of fetches,
                'total_time': Total fetch time (s),
                'avg_time': Average fetch time (ms),
                'pages_per_second': Throughput
            }
        """
        avg_time = (self.total_fetch_time / self.total_fetches * 1000) if self.total_fetches > 0 else 0
        pages_per_sec = self.total_fetches / self.total_fetch_time if self.total_fetch_time > 0 else 0
        
        return {
            'total_fetches': self.total_fetches,
            'total_time': self.total_fetch_time,
            'avg_time': avg_time,
            'pages_per_second': pages_per_sec
        }
    
    async def close(self):
        """
        Close persistent session (cleanup).
        
        Call this when done with scraper to properly close connections.
        """
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def __aenter__(self):
        """Context manager support."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        await self.close()


# Convenience function for sync-like usage
async def fetch_page(page_title: str) -> Optional[BeautifulSoup]:
    """
    Convenience function to fetch a single page.
    
    Usage:
        soup = await fetch_page("Potato")
    """
    scraper = AsyncWikipediaScraper()
    return await scraper.get_page_html(page_title)


async def fetch_pages(page_titles: List[str]) -> Dict[str, Optional[BeautifulSoup]]:
    """
    Convenience function to fetch multiple pages in parallel.
    
    Usage:
        pages = await fetch_pages(["Potato", "Pizza", "Italy"])
    """
    scraper = AsyncWikipediaScraper()
    return await scraper.get_pages_batch(page_titles)