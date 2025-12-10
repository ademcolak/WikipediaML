"""
category_analyzer.py
--------------------
Wikipedia Categories API integration ve category-based analysis.

Bu modül:
- Wikipedia API ile sayfa kategorilerini çeker
- Category similarity hesaplar (Jaccard, overlap, dice)
- Category hierarchy (parent-child) analysis
- Category depth scoring
- Category-enhanced scoring yapar
- Persistent cache ile performans optimize eder

Phase 1 Enhancements:
- Parent category fetching
- Category depth calculation
- Hierarchical similarity
- Weighted category scoring
"""

import requests
import pickle
import os
from collections import OrderedDict, defaultdict
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
        cache_file: str = 'cache/category_cache.pkl',
        verbose: bool = False,
        max_depth: int = 2
    ):
        """
        Initialize CategoryAnalyzer.
        
        Args:
            cache_size: Maximum number of pages to cache
            cache_file: Persistent cache file path
            verbose: Print debug information
            max_depth: Maximum depth for category hierarchy traversal
        """
        self.api_url = "https://en.wikipedia.org/w/api.php"
        self.cache_size = cache_size
        self.cache_file = cache_file
        self.verbose = verbose
        self.max_depth = max_depth
        
        # User-Agent header (Wikipedia requires this)
        self.headers = {
            'User-Agent': 'WikipediaML/3.3.0 (Educational Project; Python/requests)'
        }
        
        # Memory cache (LRU)
        self._cache = OrderedDict()
        
        # Category hierarchy cache
        self._parent_cache = OrderedDict()  # category -> parent categories
        self._depth_cache = {}  # category -> depth level
        
        # Statistics
        self.cache_hits = 0
        self.cache_misses = 0
        self.api_calls = 0
        self.total_api_time = 0.0
        self.hierarchy_queries = 0
        
        # Load persistent cache
        self._load_cache()
    
    def _load_cache(self):
        """Load cache from disk (includes hierarchy cache)."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                
                # Handle both old and new cache formats
                if isinstance(cache_data, dict) and 'categories' in cache_data:
                    # New format (with hierarchy)
                    self._cache = cache_data.get('categories', OrderedDict())
                    self._parent_cache = cache_data.get('parents', OrderedDict())
                    self._depth_cache = cache_data.get('depths', {})
                else:
                    # Old format (categories only)
                    self._cache = cache_data if isinstance(cache_data, OrderedDict) else OrderedDict()
                    self._parent_cache = OrderedDict()
                    self._depth_cache = {}
                
                if self.verbose:
                    print(f"📦 Loaded {len(self._cache)} categories + {len(self._parent_cache)} hierarchy from {self.cache_file}")
            except Exception as e:
                if self.verbose:
                    print(f"⚠️  Failed to load cache: {e}")
                self._cache = OrderedDict()
                self._parent_cache = OrderedDict()
                self._depth_cache = {}
    
    def save_cache(self):
        """Save cache to disk (includes hierarchy cache)."""
        try:
            cache_data = {
                'categories': self._cache,
                'parents': self._parent_cache,
                'depths': self._depth_cache
            }
            with open(self.cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            if self.verbose:
                print(f"💾 Saved {len(self._cache)} categories + {len(self._parent_cache)} hierarchy to {self.cache_file}")
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
    
    def get_parent_categories(self, category: str) -> List[str]:
        """
        Get parent categories for a given category.
        
        Args:
            category: Category name (without "Category:" prefix)
            
        Returns:
            List of parent category names
            
        Example:
            >>> analyzer.get_parent_categories("Italian cuisine")
            ['European cuisine', 'Mediterranean cuisine', ...]
        """
        # Check cache
        if category in self._parent_cache:
            return self._parent_cache[category]
        
        # Fetch from API
        params = {
            'action': 'query',
            'titles': f'Category:{category}',
            'prop': 'categories',
            'cllimit': 500,
            'format': 'json'
        }
        
        try:
            response = requests.get(self.api_url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            self.api_calls += 1
            self.hierarchy_queries += 1
            
            data = response.json()
            pages = data.get('query', {}).get('pages', {})
            page = list(pages.values())[0]
            
            if 'categories' in page:
                parents = [
                    cat['title'].replace('Category:', '')
                    for cat in page['categories']
                ]
                self._parent_cache[category] = parents
                return parents
            
            self._parent_cache[category] = []
            return []
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Error fetching parent categories for {category}: {e}")
            return []
    
    def get_category_depth(self, category: str, max_depth: Optional[int] = None) -> int:
        """
        Calculate category depth (distance from root categories).
        
        Args:
            category: Category name
            max_depth: Maximum depth to traverse (default: self.max_depth)
            
        Returns:
            Depth level (0 = root, higher = more specific)
            
        Logic:
            - Root categories (no parents): depth = 0
            - Has parents: depth = 1 + min(parent_depths)
            - More specific categories have higher depth
        """
        if max_depth is None:
            max_depth = self.max_depth
        
        # Check cache
        if category in self._depth_cache:
            return self._depth_cache[category]
        
        # Get parents
        parents = self.get_parent_categories(category)
        
        if not parents or max_depth <= 0:
            # Root category or max depth reached
            depth = 0
        else:
            # Recursive: depth = 1 + min(parent depths)
            parent_depths = [
                self.get_category_depth(parent, max_depth - 1)
                for parent in parents[:5]  # Limit to 5 parents for performance
            ]
            depth = 1 + min(parent_depths) if parent_depths else 0
        
        self._depth_cache[category] = depth
        return depth
    
    def get_category_tree(self, page_title: str, depth: int = 1) -> Dict:
        """
        Get category tree for a page (categories + their parents).
        
        Args:
            page_title: Wikipedia page title
            depth: How many levels of parents to fetch
            
        Returns:
            Dict with category tree structure
            
        Example:
            >>> tree = analyzer.get_category_tree("Pizza", depth=2)
            >>> print(tree)
            {
                'page': 'Pizza',
                'direct_categories': ['Italian cuisine', 'Flatbreads'],
                'parent_categories': {
                    'Italian cuisine': ['European cuisine', 'Mediterranean cuisine'],
                    'Flatbreads': ['Breads', 'Baked goods']
                },
                'all_categories': ['Italian cuisine', 'Flatbreads', 'European cuisine', ...]
            }
        """
        direct_cats = self.get_categories(page_title)
        
        tree = {
            'page': page_title,
            'direct_categories': direct_cats,
            'parent_categories': {},
            'all_categories': set(direct_cats)
        }
        
        # Fetch parents for each direct category
        if depth > 0:
            for cat in direct_cats:
                parents = self.get_parent_categories(cat)
                tree['parent_categories'][cat] = parents
                tree['all_categories'].update(parents)
                
                # Fetch grandparents if depth > 1
                if depth > 1:
                    for parent in parents[:3]:  # Limit for performance
                        grandparents = self.get_parent_categories(parent)
                        tree['all_categories'].update(grandparents)
        
        tree['all_categories'] = list(tree['all_categories'])
        return tree
    
    def hierarchical_similarity(
        self,
        page1: str,
        page2: str,
        depth: int = 1,
        weight_direct: float = 0.7,
        weight_parent: float = 0.3
    ) -> float:
        """
        Calculate hierarchical category similarity.
        
        Args:
            page1: First page title
            page2: Second page title
            depth: Category tree depth
            weight_direct: Weight for direct category overlap
            weight_parent: Weight for parent category overlap
            
        Returns:
            Similarity score (0.0 to 1.0)
            
        Logic:
            - Direct categories: Higher weight (more specific)
            - Parent categories: Lower weight (more general)
            - Weighted combination
        """
        # Get category trees
        tree1 = self.get_category_tree(page1, depth=depth)
        tree2 = self.get_category_tree(page2, depth=depth)
        
        # Direct category similarity
        direct1 = set(tree1['direct_categories'])
        direct2 = set(tree2['direct_categories'])
        
        if direct1 and direct2:
            direct_sim = len(direct1 & direct2) / len(direct1 | direct2)
        else:
            direct_sim = 0.0
        
        # All categories similarity (includes parents)
        all1 = set(tree1['all_categories'])
        all2 = set(tree2['all_categories'])
        
        if all1 and all2:
            all_sim = len(all1 & all2) / len(all1 | all2)
        else:
            all_sim = 0.0
        
        # Weighted combination
        score = weight_direct * direct_sim + weight_parent * all_sim
        
        return score
    
    def category_depth_score(self, page_title: str, target_title: str) -> float:
        """
        Calculate category depth-based score.
        
        Args:
            page_title: Candidate page
            target_title: Target page
            
        Returns:
            Score (0.0 to 1.0)
            
        Logic:
            - Pages with similar category depths are more related
            - Bonus for shared specific (high-depth) categories
        """
        cats1 = self.get_categories(page_title)
        cats2 = self.get_categories(target_title)
        
        if not cats1 or not cats2:
            return 0.0
        
        # Calculate average depths
        depths1 = [self.get_category_depth(cat) for cat in cats1[:10]]
        depths2 = [self.get_category_depth(cat) for cat in cats2[:10]]
        
        avg_depth1 = sum(depths1) / len(depths1) if depths1 else 0
        avg_depth2 = sum(depths2) / len(depths2) if depths2 else 0
        
        # Depth similarity (closer depths = higher score)
        depth_diff = abs(avg_depth1 - avg_depth2)
        depth_sim = 1.0 / (1.0 + depth_diff)
        
        # Shared specific categories bonus
        shared = set(cats1) & set(cats2)
        if shared:
            shared_depths = [self.get_category_depth(cat) for cat in shared]
            avg_shared_depth = sum(shared_depths) / len(shared_depths)
            # Higher depth = more specific = higher bonus
            specificity_bonus = min(avg_shared_depth / 5.0, 0.3)
        else:
            specificity_bonus = 0.0
        
        return depth_sim * 0.7 + specificity_bonus
    
    def clear_cache(self):
        """Clear memory cache and reset statistics."""
        self._cache.clear()
        self._parent_cache.clear()
        self._depth_cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0
        self.api_calls = 0
        self.total_api_time = 0.0
        self.hierarchy_queries = 0
    
    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics (includes hierarchy stats).
        
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
            'avg_api_time_ms': avg_api_time,
            'hierarchy_cache_size': len(self._parent_cache),
            'depth_cache_size': len(self._depth_cache),
            'hierarchy_queries': self.hierarchy_queries
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