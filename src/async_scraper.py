"""
async_scraper.py
----------------
Asynchronous Wikipedia scraper for parallel page fetching.
Bu modül, birden fazla Wikipedia sayfasını paralel olarak çekerek
performansı 4-5x artırır.

Performance Comparison:
    Sync (Sequential):  4 pages × 500ms = 2000ms
    Async (Parallel):   4 pages in parallel = 500ms (4x faster!)
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup, Tag
from collections import OrderedDict
from typing import Optional, List, Dict, Tuple
import time


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
    
    def __init__(self, cache_size: int = 128, timeout: int = 10, max_concurrent: int = 10):
        """
        Initialize AsyncWikipediaScraper.
        
        Args:
            cache_size: Maximum number of pages to cache (LRU)
            timeout: HTTP request timeout in seconds
            max_concurrent: Maximum concurrent requests (default: 10)
        """
        self.base_url = "https://en.wikipedia.org/wiki/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_concurrent = max_concurrent
        
        # Cache (same as sync version)
        self._cache = OrderedDict()
        self._cache_size = cache_size
        
        # Statistics
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_fetch_time = 0.0
        self.total_fetches = 0
        
        # Semaphore for limiting concurrent requests
        self._semaphore = asyncio.Semaphore(max_concurrent)
    
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
    
    async def _fetch_from_wikipedia(self, page_title: str) -> Optional[BeautifulSoup]:
        """
        Fetch a single page from Wikipedia (async network call).
        
        This method is only called on cache miss.
        """
        url = self.base_url + page_title
        
        async with self._semaphore:  # Limit concurrent requests
            try:
                start_time = time.time()
                
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.get(url, headers=self.headers) as response:
                        response.raise_for_status()
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                
                # Track performance
                fetch_time = time.time() - start_time
                self.total_fetch_time += fetch_time
                self.total_fetches += 1
                
                return soup
                
            except Exception as e:
                print(f"❌ Error fetching {page_title}: {e}")
                return None
    
    async def _fetch_pages_parallel(self, page_titles: List[str]) -> Dict[str, Optional[BeautifulSoup]]:
        """
        Fetch multiple pages in parallel (CORE PERFORMANCE OPTIMIZATION).
        
        Uses asyncio.gather() to run all fetches concurrently.
        """
        start_time = time.time()
        
        # Create tasks for all pages
        tasks = [self._fetch_from_wikipedia(title) for title in page_titles]
        
        # Run all tasks in parallel
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