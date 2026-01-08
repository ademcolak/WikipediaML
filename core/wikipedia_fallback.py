#!/usr/bin/env python3
"""
Wikipedia API Fallback Mechanism
Fetches live data from Wikipedia API when local graph is outdated or incomplete.
"""

import requests
import time
from typing import List, Optional, Dict, Set
from functools import lru_cache
import json


class WikipediaAPIFallback:
    """
    Fallback mechanism for fetching live Wikipedia data.
    
    Used when:
    - Local graph doesn't have expected links
    - Page is not in local database
    - Links have been updated since graph was built
    """
    
    def __init__(
        self,
        cache_size: int = 1000,
        rate_limit_delay: float = 0.1,
        timeout: int = 5
    ):
        """
        Initialize fallback mechanism.
        
        Args:
            cache_size: Size of LRU cache for API responses
            rate_limit_delay: Delay between API calls (seconds)
            timeout: Request timeout (seconds)
        """
        self.cache_size = cache_size
        self.rate_limit_delay = rate_limit_delay
        self.timeout = timeout
        self.last_request_time = 0
        
        # Statistics
        self.stats = {
            'api_calls': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'errors': 0
        }
    
    def _rate_limit(self):
        """Enforce rate limiting between API calls."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        
        self.last_request_time = time.time()
    
    @lru_cache(maxsize=1000)
    def get_page_links(self, page_title: str) -> Optional[List[str]]:
        """
        Fetch outgoing links from a Wikipedia page.
        
        Args:
            page_title: Wikipedia page title
            
        Returns:
            List of linked page titles, or None if error
        """
        self._rate_limit()
        self.stats['api_calls'] += 1
        
        try:
            # Wikipedia API endpoint
            url = "https://en.wikipedia.org/w/api.php"
            
            params = {
                'action': 'query',
                'titles': page_title,
                'prop': 'links',
                'pllimit': 'max',  # Get maximum links (500)
                'format': 'json',
                'formatversion': 2
            }
            
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract links
            pages = data.get('query', {}).get('pages', [])
            if not pages:
                return None
            
            page = pages[0]
            if 'missing' in page:
                return None
            
            links = page.get('links', [])
            link_titles = [link['title'] for link in links]
            
            return link_titles
            
        except Exception as e:
            self.stats['errors'] += 1
            print(f"✗ API error for '{page_title}': {e}")
            return None
    
    @lru_cache(maxsize=1000)
    def check_link_exists(self, from_title: str, to_title: str) -> bool:
        """
        Check if a link exists between two pages.
        
        Args:
            from_title: Source page title
            to_title: Target page title
            
        Returns:
            True if link exists, False otherwise
        """
        links = self.get_page_links(from_title)
        
        if links is None:
            return False
        
        return to_title in links
    
    def get_page_info(self, page_title: str) -> Optional[Dict]:
        """
        Get basic information about a page.
        
        Args:
            page_title: Wikipedia page title
            
        Returns:
            Dictionary with page info, or None if error
        """
        self._rate_limit()
        self.stats['api_calls'] += 1
        
        try:
            url = "https://en.wikipedia.org/w/api.php"
            
            params = {
                'action': 'query',
                'titles': page_title,
                'prop': 'info|pageprops',
                'format': 'json',
                'formatversion': 2
            }
            
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            pages = data.get('query', {}).get('pages', [])
            
            if not pages:
                return None
            
            page = pages[0]
            
            if 'missing' in page:
                return None
            
            return {
                'pageid': page.get('pageid'),
                'title': page.get('title'),
                'exists': True,
                'is_redirect': 'redirect' in page
            }
            
        except Exception as e:
            self.stats['errors'] += 1
            print(f"✗ API error for page info '{page_title}': {e}")
            return None
    
    def verify_path(self, path: List[str]) -> bool:
        """
        Verify that a path exists by checking each link.
        
        Args:
            path: List of page titles forming a path
            
        Returns:
            True if all links in path exist, False otherwise
        """
        if len(path) < 2:
            return True
        
        for i in range(len(path) - 1):
            from_title = path[i]
            to_title = path[i + 1]
            
            if not self.check_link_exists(from_title, to_title):
                return False
        
        return True
    
    def get_stats(self) -> Dict:
        """Get API usage statistics."""
        return self.stats.copy()
    
    def clear_cache(self):
        """Clear the LRU cache."""
        self.get_page_links.cache_clear()
        self.check_link_exists.cache_clear()


class HybridNavigatorWithFallback:
    """
    Navigator that uses local graph with API fallback.
    
    Combines local graph navigation with live API data when needed.
    """
    
    def __init__(
        self,
        local_navigator,
        fallback: WikipediaAPIFallback,
        fallback_threshold: int = 3
    ):
        """
        Initialize hybrid navigator.
        
        Args:
            local_navigator: Local graph navigator
            fallback: Wikipedia API fallback
            fallback_threshold: Number of failed attempts before using fallback
        """
        self.local_navigator = local_navigator
        self.fallback = fallback
        self.fallback_threshold = fallback_threshold
        
        self.stats = {
            'local_successes': 0,
            'fallback_used': 0,
            'fallback_helped': 0
        }
    
    def search(
        self,
        start_title: str,
        target_title: str,
        verbose: bool = False
    ) -> Optional[List[str]]:
        """
        Search with fallback support.
        
        Args:
            start_title: Starting page title
            target_title: Target page title
            verbose: Print progress
            
        Returns:
            Path as list of titles, or None if not found
        """
        # Try local navigation first
        if hasattr(self.local_navigator, 'pages'):
            # Convert titles to IDs if needed
            start_id = None
            target_id = None
            
            for pid, title in self.local_navigator.pages.items():
                if title == start_title:
                    start_id = pid
                if title == target_title:
                    target_id = pid
            
            if start_id and target_id:
                path_ids = self.local_navigator.search(start_id, target_id, verbose=verbose)
                
                if path_ids:
                    # Convert back to titles
                    path_titles = [self.local_navigator.pages[pid] for pid in path_ids]
                    self.stats['local_successes'] += 1
                    return path_titles
        
        # Local navigation failed, try fallback
        if verbose:
            print("\n⚠ Local navigation failed, trying API fallback...")
        
        self.stats['fallback_used'] += 1
        
        # Check if pages exist via API
        start_info = self.fallback.get_page_info(start_title)
        target_info = self.fallback.get_page_info(target_title)
        
        if not start_info or not target_info:
            if verbose:
                print("✗ One or both pages don't exist")
            return None
        
        # Get links from start page
        start_links = self.fallback.get_page_links(start_title)
        
        if not start_links:
            if verbose:
                print("✗ No links found from start page")
            return None
        
        # Check if target is directly linked
        if target_title in start_links:
            if verbose:
                print(f"✓ Direct link found via API!")
            self.stats['fallback_helped'] += 1
            return [start_title, target_title]
        
        # For deeper search, would need to implement BFS with API
        # This is expensive, so we just check one hop
        if verbose:
            print("✗ Target not found in one hop via API")
        
        return None
    
    def get_stats(self) -> Dict:
        """Get combined statistics."""
        return {
            **self.stats,
            'api_stats': self.fallback.get_stats()
        }


if __name__ == "__main__":
    print("Testing Wikipedia API Fallback...")
    
    # Create fallback
    fallback = WikipediaAPIFallback()
    
    # Test getting links
    print("\nTesting: Get links from 'Python (programming language)'")
    links = fallback.get_page_links("Python (programming language)")
    
    if links:
        print(f"✓ Found {len(links)} links")
        print(f"  First 5: {links[:5]}")
    else:
        print("✗ Failed to get links")
    
    # Test checking link existence
    print("\nTesting: Check if 'Python (programming language)' links to 'Programming language'")
    exists = fallback.check_link_exists("Python (programming language)", "Programming language")
    print(f"  Link exists: {exists}")
    
    # Print stats
    print(f"\nAPI Statistics:")
    stats = fallback.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")