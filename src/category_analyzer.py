"""
category_analyzer.py
--------------------
Wikipedia Categories API integration ve category-based analysis.

Bu modül:
- Wikipedia API ile sayfa kategorilerini çeker
- Category similarity hesaplar
- Category-enhanced scoring yapar
- Persistent cache ile performans optimize eder
"""

import requests
import pickle
import os
from collections import OrderedDict
from typing import List, Dict, Set, Optional, Tuple
import time


class WikipediaCategoryAnalyzer:
    """
    Wikipedia Categories analyzer.
    
    Features:
    - Wikipedia API ile category fetching
    - LRU cache (memory + disk)
    - Category similarity (Jaccard, overlap)
    - Category hierarchy analysis
    - Batch operations
    """
    
    def __init__(
        self,
        cache_size: int = 1000,
        cache_file: str = 'category_cache.pkl',
        verbose: bool = False
    ):
        """
        Initialize CategoryAnalyzer.
        
        Args:
            cache_size: Maximum number of pages to cache
            cache_file: Persistent cache file path
            verbose: Print debug information
        """
        self.api_url = "https://en.wikipedia.org/w/api.php"
        self.cache_size = cache_size
        self.cache_file = cache_file
        self.verbose = verbose
        
        # User-Agent header (Wikipedia requires this)
        self.headers = {
            'User-Agent': 'WikipediaML/3.2.0 (Educational Project; Python/requests)'
        }
        
        # Memory cache (LRU)
        self._cache = OrderedDict()
        
        # Statistics
        self.cache_hits = 0
        self.cache_misses = 0
        self.api_calls = 0
        self.total_api_time = 0.0
        
        # Load persistent cache
        self._load_cache()
    
    def _load_cache(self):
        """Load cache from disk."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'rb') as f:
                    self._cache = pickle.load(f)
                if self.verbose:
                    print(f"📦 Loaded {len(self._cache)} cached categories from {self.cache_file}")
            except Exception as e:
                if self.verbose:
                    print(f"⚠️  Failed to load cache: {e}")
                self._cache = OrderedDict()
    
    def save_cache(self):
        """Save cache to disk."""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self._cache, f)
            if self.verbose:
                print(f"💾 Saved {len(self._cache)} categories to {self.cache_file}")
        except Exception as e:
            if self.verbose:
                print(f"⚠️  Failed to save cache: {e}")
    
    def get_categories(self, page_title: str) -> List[str]:
        """
        Get categories for a Wikipedia page.
        
        Args:
            page_title: Wikipedia page title (e.g., "Pizza")
            
        Returns:
            List of category names (without "Category:" prefix)
            
        Example:
            >>> analyzer = WikipediaCategoryAnalyzer()
            >>> categories = analyzer.get_categories("Pizza")
            >>> print(categories)
            ['Italian cuisine', 'Italian-American cuisine', 'Flatbreads', ...]
        """
        # Check cache
        if page_title in self._cache:
            self.cache_hits += 1
            self._cache.move_to_end(page_title)  # Mark as recently used
            return self._cache[page_title]
        
        # Cache miss: fetch from API
        self.cache_misses += 1
        categories = self._fetch_from_api(page_title)
        
        # Add to cache
        self._add_to_cache(page_title, categories)
        
        return categories
    
    def _fetch_from_api(self, page_title: str) -> List[str]:
        """
        Fetch categories from Wikipedia API.
        
        API Documentation:
        https://www.mediawiki.org/wiki/API:Categories
        """
        params = {
            'action': 'query',
            'titles': page_title,
            'prop': 'categories',
            'cllimit': 500,  # Max categories per page
            'format': 'json'
        }
        
        try:
            start_time = time.time()
            response = requests.get(self.api_url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            self.api_calls += 1
            self.total_api_time += time.time() - start_time
            
            data = response.json()
            
            # Extract categories
            pages = data.get('query', {}).get('pages', {})
            page = list(pages.values())[0]
            
            if 'categories' in page:
                # Remove "Category:" prefix
                categories = [
                    cat['title'].replace('Category:', '')
                    for cat in page['categories']
                ]
                return categories
            
            return []
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Error fetching categories for {page_title}: {e}")
            return []
    
    def _add_to_cache(self, page_title: str, categories: List[str]):
        """Add page categories to cache (LRU)."""
        # Remove oldest if cache is full
        if len(self._cache) >= self.cache_size:
            self._cache.popitem(last=False)
        
        self._cache[page_title] = categories
    
    def get_categories_batch(self, page_titles: List[str]) -> Dict[str, List[str]]:
        """
        Get categories for multiple pages.
        
        Args:
            page_titles: List of Wikipedia page titles
            
        Returns:
            Dict mapping page_title → categories
            
        Example:
            >>> categories = analyzer.get_categories_batch(["Pizza", "Pasta", "Italy"])
            >>> print(categories["Pizza"])
            ['Italian cuisine', 'Flatbreads', ...]
        """
        result = {}
        for title in page_titles:
            result[title] = self.get_categories(title)
        return result
    
    def category_similarity(
        self,
        page1: str,
        page2: str,
        method: str = 'jaccard'
    ) -> float:
        """
        Calculate category similarity between two pages.
        
        Args:
            page1: First page title
            page2: Second page title
            method: Similarity method ('jaccard', 'overlap', 'dice')
            
        Returns:
            Similarity score (0.0 to 1.0)
            
        Methods:
            - jaccard: |A ∩ B| / |A ∪ B|
            - overlap: |A ∩ B| / min(|A|, |B|)
            - dice: 2 * |A ∩ B| / (|A| + |B|)
        """
        cats1 = set(self.get_categories(page1))
        cats2 = set(self.get_categories(page2))
        
        if not cats1 or not cats2:
            return 0.0
        
        intersection = len(cats1 & cats2)
        
        if method == 'jaccard':
            union = len(cats1 | cats2)
            return intersection / union if union > 0 else 0.0
        
        elif method == 'overlap':
            min_size = min(len(cats1), len(cats2))
            return intersection / min_size if min_size > 0 else 0.0
        
        elif method == 'dice':
            total = len(cats1) + len(cats2)
            return (2 * intersection) / total if total > 0 else 0.0
        
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def common_categories(self, page1: str, page2: str) -> List[str]:
        """
        Get common categories between two pages.
        
        Args:
            page1: First page title
            page2: Second page title
            
        Returns:
            List of common category names
        """
        cats1 = set(self.get_categories(page1))
        cats2 = set(self.get_categories(page2))
        return list(cats1 & cats2)
    
    def category_overlap_score(
        self,
        link: str,
        target: str,
        current: Optional[str] = None
    ) -> float:
        """
        Calculate category-based score for link selection.
        
        Args:
            link: Candidate link
            target: Target page
            current: Current page (optional, for context)
            
        Returns:
            Score (0.0 to 1.0)
            
        Scoring:
            - Direct overlap with target: 0.7 weight
            - Overlap with current: 0.3 weight (if provided)
        """
        # Link → Target similarity
        link_target_sim = self.category_similarity(link, target, method='jaccard')
        
        if current:
            # Link → Current similarity (context)
            link_current_sim = self.category_similarity(link, current, method='jaccard')
            # Weighted combination
            score = 0.7 * link_target_sim + 0.3 * link_current_sim
        else:
            score = link_target_sim
        
        return score
    
    def is_same_domain(self, page1: str, page2: str, threshold: float = 0.3) -> bool:
        """
        Check if two pages are in the same domain (similar categories).
        
        Args:
            page1: First page title
            page2: Second page title
            threshold: Minimum similarity to consider same domain
            
        Returns:
            True if pages are in same domain
        """
        similarity = self.category_similarity(page1, page2, method='jaccard')
        return similarity >= threshold
    
    def get_category_stats(self, page_title: str) -> Dict:
        """
        Get category statistics for a page.
        
        Args:
            page_title: Wikipedia page title
            
        Returns:
            Dict with category statistics
        """
        categories = self.get_categories(page_title)
        
        return {
            'page': page_title,
            'category_count': len(categories),
            'categories': categories,
            'has_categories': len(categories) > 0
        }
    
    def clear_cache(self):
        """Clear memory cache and reset statistics."""
        self._cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0
        self.api_calls = 0
        self.total_api_time = 0.0
    
    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics.
        
        Returns:
            Dict with cache statistics
        """
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        avg_api_time = (self.total_api_time / self.api_calls * 1000) if self.api_calls > 0 else 0
        
        return {
            'cache_size': len(self._cache),
            'max_size': self.cache_size,
            'hits': self.cache_hits,
            'misses': self.cache_misses,
            'hit_rate': hit_rate,
            'api_calls': self.api_calls,
            'total_api_time': self.total_api_time,
            'avg_api_time_ms': avg_api_time
        }
    
    def __del__(self):
        """Save cache on destruction."""
        self.save_cache()


# Convenience functions
def get_page_categories(page_title: str) -> List[str]:
    """
    Convenience function to get categories for a single page.
    
    Args:
        page_title: Wikipedia page title
        
    Returns:
        List of category names
    """
    analyzer = WikipediaCategoryAnalyzer()
    return analyzer.get_categories(page_title)


def calculate_category_similarity(page1: str, page2: str) -> float:
    """
    Convenience function to calculate category similarity.
    
    Args:
        page1: First page title
        page2: Second page title
        
    Returns:
        Jaccard similarity score (0.0 to 1.0)
    """
    analyzer = WikipediaCategoryAnalyzer()
    return analyzer.category_similarity(page1, page2)