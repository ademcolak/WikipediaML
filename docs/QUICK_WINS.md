# ⚡ Quick Wins: Hızlı Performans İyileştirmeleri

## 🎯 Hedef
En az çaba ile en fazla performans artışı!

Bu dokümanda **1-2 hafta içinde** uygulanabilecek ve **%40-60 performans artışı** sağlayacak optimizasyonları bulacaksınız.

---

## 🏆 Top 3 Quick Wins

### 1. Embedding Cache (En Kolay + En Etkili) ⭐⭐⭐⭐⭐

**Neden?**
- Sentence-BERT embedding hesaplama: ~100ms/sayfa
- Bir search'te 50-100 sayfa işleniyor
- Toplam: 5-10 saniye sadece embedding için!

**Çözüm: LRU Cache**
```python
# src/embedder.py

from functools import lru_cache
import pickle
from pathlib import Path

class WikiEmbedder:
    def __init__(self, cache_size=10000, cache_file='embeddings_cache.pkl'):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.cache_file = Path(cache_file)
        self.cache = self._load_cache()
    
    def _load_cache(self):
        """Load cache from disk."""
        if self.cache_file.exists():
            with open(self.cache_file, 'rb') as f:
                return pickle.load(f)
        return {}
    
    def _save_cache(self):
        """Save cache to disk."""
        with open(self.cache_file, 'wb') as f:
            pickle.dump(self.cache, f)
    
    @lru_cache(maxsize=10000)
    def get_embedding(self, text: str):
        """Get embedding with cache."""
        # Check disk cache first
        if text in self.cache:
            return self.cache[text]
        
        # Compute embedding
        embedding = self.model.encode(text)
        
        # Save to cache
        self.cache[text] = embedding
        
        # Periodic save (every 100 new embeddings)
        if len(self.cache) % 100 == 0:
            self._save_cache()
        
        return embedding
```

**Beklenen İyileşme**: 
- İlk search: Normal hız
- Sonraki search'ler: %70-80 daha hızlı
- Cache hit rate: %60-80 (popüler sayfalar için)

**Uygulama Süresi**: 30 dakika

---

### 2. Batch Link Processing (Kolay + Çok Etkili) ⭐⭐⭐⭐⭐

**Neden?**
- Her link için ayrı API call: Yavaş!
- 100 link = 100 API call = 10+ saniye

**Çözüm: Batch Processing**
```python
# src/scraper.py

class WikiScraper:
    def get_links_batch(self, pages: List[str], batch_size=50):
        """Get links for multiple pages in one API call."""
        all_links = {}
        
        # Process in batches
        for i in range(0, len(pages), batch_size):
            batch = pages[i:i+batch_size]
            
            # Single API call for entire batch
            params = {
                'action': 'query',
                'titles': '|'.join(batch),
                'prop': 'links',
                'pllimit': 'max',
                'format': 'json'
            }
            
            response = requests.get(self.api_url, params=params)
            data = response.json()
            
            # Parse results
            for page_id, page_data in data['query']['pages'].items():
                title = page_data['title']
                links = [link['title'] for link in page_data.get('links', [])]
                all_links[title] = links
        
        return all_links
```

**Kullanım**:
```python
# Önce (yavaş):
for page in pages:
    links = scraper.get_links(page)  # 100 API call

# Sonra (hızlı):
all_links = scraper.get_links_batch(pages)  # 2-3 API call
```

**Beklenen İyileşme**: %80-90 API call süresinde azalma

**Uygulama Süresi**: 1 saat

---

### 3. Smart Link Filtering (Orta + Etkili) ⭐⭐⭐⭐

**Neden?**
- Her sayfada 100-500 link var
- Çoğu alakasız (örn: "Category:", "Help:", "Wikipedia:")
- Gereksiz işlem yapıyoruz

**Çözüm: Aggressive Filtering**
```python
# src/link_filter.py

class LinkFilter:
    def __init__(self):
        # Blacklist patterns
        self.blacklist_patterns = [
            'Category:', 'File:', 'Template:', 'Help:',
            'Wikipedia:', 'Portal:', 'Special:', 'Talk:',
            'User:', 'Draft:', 'Module:', 'MediaWiki:'
        ]
        
        # Blacklist words (low-value pages)
        self.blacklist_words = {
            'disambiguation', 'list_of', 'index_of',
            'timeline', 'glossary', 'bibliography'
        }
    
    def quick_filter(self, links: List[str], target: str) -> List[str]:
        """Fast filtering before expensive operations."""
        filtered = []
        
        target_words = set(target.lower().replace('_', ' ').split())
        
        for link in links:
            # Skip blacklisted patterns
            if any(pattern in link for pattern in self.blacklist_patterns):
                continue
            
            # Skip blacklisted words
            link_lower = link.lower()
            if any(word in link_lower for word in self.blacklist_words):
                continue
            
            # Prioritize links with target words
            link_words = set(link_lower.replace('_', ' ').split())
            if link_words & target_words:
                filtered.insert(0, link)  # Add to front
            else:
                filtered.append(link)
        
        # Limit to top 50 links (enough for most searches)
        return filtered[:50]
```

**Beklenen İyileşme**: 
- %60-80 daha az link işleme
- %40-50 daha hızlı search

**Uygulama Süresi**: 45 dakika

---

## 🚀 Bonus Quick Wins

### 4. Parallel Embedding Calculation ⭐⭐⭐⭐

```python
# src/embedder.py

from concurrent.futures import ThreadPoolExecutor
import numpy as np

class WikiEmbedder:
    def get_embeddings_parallel(self, texts: List[str], max_workers=4):
        """Calculate embeddings in parallel."""
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            embeddings = list(executor.map(self.get_embedding, texts))
        return np.array(embeddings)
```

**Beklenen İyileşme**: %50-70 embedding hesaplama hızı

**Uygulama Süresi**: 20 dakika

---

### 5. Category Cache ⭐⭐⭐⭐

```python
# src/category_analyzer.py

class WikipediaCategoryAnalyzer:
    def __init__(self, cache_file='category_cache.pkl'):
        self.cache_file = Path(cache_file)
        self.category_cache = self._load_cache()
    
    def get_categories_cached(self, page: str):
        """Get categories with cache."""
        if page in self.category_cache:
            return self.category_cache[page]
        
        categories = self.get_categories(page)
        self.category_cache[page] = categories
        
        # Save periodically
        if len(self.category_cache) % 100 == 0:
            self._save_cache()
        
        return categories
```

**Beklenen İyileşme**: %80-90 category lookup hızı

**Uygulama Süresi**: 30 dakika

---

### 6. Early Stopping ⭐⭐⭐

```python
# src/semantic_navigator.py

class SemanticNavigator:
    def search_with_early_stopping(self, start, target, confidence_threshold=0.9):
        """Stop search if we find a very good link."""
        visited = set()
        queue = [(start, [start])]
        
        while queue:
            current, path = queue.pop(0)
            
            if current == target:
                return SearchResult(found=True, path=path)
            
            links = self.get_links(current)
            scored_links = self.score_links(links, target)
            
            # Early stopping: if best link has very high score
            if scored_links and scored_links[0][1] > confidence_threshold:
                best_link = scored_links[0][0]
                if best_link == target:
                    return SearchResult(found=True, path=path + [best_link])
            
            # Continue normal search...
```

**Beklenen İyileşme**: %20-30 daha hızlı (kolay case'lerde)

**Uygulama Süresi**: 15 dakika

---

## 📊 Implementation Checklist

### Week 1: Core Optimizations
- [ ] **Day 1-2**: Embedding Cache
  - [ ] Implement LRU cache
  - [ ] Add disk persistence
  - [ ] Test cache hit rate
  - [ ] Benchmark: Before vs After

- [ ] **Day 3-4**: Batch Link Processing
  - [ ] Implement batch API calls
  - [ ] Update scraper
  - [ ] Test with different batch sizes
  - [ ] Benchmark: API call reduction

- [ ] **Day 5**: Smart Link Filtering
  - [ ] Add blacklist patterns
  - [ ] Implement quick filter
  - [ ] Test filter effectiveness
  - [ ] Benchmark: Link reduction

### Week 2: Bonus Optimizations
- [ ] **Day 1**: Parallel Embedding
  - [ ] Add ThreadPoolExecutor
  - [ ] Test optimal worker count
  - [ ] Benchmark: Speedup

- [ ] **Day 2**: Category Cache
  - [ ] Implement category cache
  - [ ] Add persistence
  - [ ] Benchmark: Lookup speed

- [ ] **Day 3**: Early Stopping
  - [ ] Add confidence threshold
  - [ ] Test different thresholds
  - [ ] Benchmark: Easy case speedup

- [ ] **Day 4-5**: Integration & Testing
  - [ ] Integrate all optimizations
  - [ ] Run comprehensive benchmarks
  - [ ] Document results
  - [ ] Update README

---

## 🧪 Benchmark Script

```python
# benchmark_quick_wins.py

import time
from typing import List, Tuple
import numpy as np

class QuickWinsBenchmark:
    def __init__(self, navigator_old, navigator_new):
        self.old = navigator_old
        self.new = navigator_new
    
    def benchmark_pair(self, start: str, target: str, iterations=5):
        """Benchmark a single pair."""
        old_times = []
        new_times = []
        
        for _ in range(iterations):
            # Old version
            start_time = time.time()
            result_old = self.old.search(start, target)
            old_times.append(time.time() - start_time)
            
            # New version
            start_time = time.time()
            result_new = self.new.search(start, target)
            new_times.append(time.time() - start_time)
        
        old_avg = np.mean(old_times)
        new_avg = np.mean(new_times)
        speedup = (old_avg - new_avg) / old_avg * 100
        
        return {
            'start': start,
            'target': target,
            'old_avg': old_avg,
            'new_avg': new_avg,
            'speedup': speedup
        }
    
    def run_benchmark(self, test_cases: List[Tuple[str, str]]):
        """Run benchmark on multiple test cases."""
        results = []
        
        print("=" * 80)
        print("QUICK WINS BENCHMARK")
        print("=" * 80)
        
        for start, target in test_cases:
            result = self.benchmark_pair(start, target)
            results.append(result)
            
            print(f"\n{start} → {target}")
            print(f"  Old: {result['old_avg']:.2f}s")
            print(f"  New: {result['new_avg']:.2f}s")
            print(f"  Speedup: {result['speedup']:.1f}%")
        
        # Summary
        avg_speedup = np.mean([r['speedup'] for r in results])
        print("\n" + "=" * 80)
        print(f"AVERAGE SPEEDUP: {avg_speedup:.1f}%")
        print("=" * 80)
        
        return results

# Usage
if __name__ == '__main__':
    # Test cases
    test_cases = [
        ('Python_(programming_language)', 'Machine_learning'),
        ('United_States', 'World_War_II'),
        ('Albert_Einstein', 'Physics'),
        ('London', 'United_Kingdom'),
        ('Computer', 'Internet'),
    ]
    
    # Run benchmark
    benchmark = QuickWinsBenchmark(old_navigator, new_navigator)
    results = benchmark.run_benchmark(test_cases)
```

---

## 📈 Expected Results

### Before Optimizations
```
Average Search Time: 15-30 seconds
Cache Hit Rate: 0%
API Calls per Search: 50-100
Links Processed: 500-1000
```

### After Quick Wins
```
Average Search Time: 5-12 seconds (60-70% faster!)
Cache Hit Rate: 60-80%
API Calls per Search: 5-10 (90% reduction!)
Links Processed: 50-100 (90% reduction!)
```

### Breakdown by Optimization
```
Embedding Cache:      -40% time
Batch Processing:     -30% time
Smart Filtering:      -20% time
Parallel Embedding:   -10% time
Category Cache:       -5% time
Early Stopping:       -5% time
-----------------------------------
Total:                -60-70% time
```

---

## 🎯 Success Metrics

### Must Have
- [ ] Average search time < 12 seconds
- [ ] Cache hit rate > 50%
- [ ] API calls reduced by > 80%

### Nice to Have
- [ ] Average search time < 8 seconds
- [ ] Cache hit rate > 70%
- [ ] API calls reduced by > 90%

### Stretch Goals
- [ ] Average search time < 5 seconds
- [ ] Cache hit rate > 80%
- [ ] Zero API calls for popular searches

---

## 🐛 Common Issues & Solutions

### Issue 1: Cache Growing Too Large
**Problem**: Cache file > 1GB
**Solution**: 
```python
# Limit cache size
if len(self.cache) > 50000:
    # Remove least recently used 10%
    items = sorted(self.cache.items(), key=lambda x: x[1]['last_used'])
    for key, _ in items[:5000]:
        del self.cache[key]
```

### Issue 2: Batch API Calls Timing Out
**Problem**: Batch too large, API timeout
**Solution**:
```python
# Reduce batch size
batch_size = 25  # Instead of 50
timeout = 30     # Increase timeout
```

### Issue 3: Parallel Embedding Slower
**Problem**: Too many workers, overhead
**Solution**:
```python
# Optimal worker count = CPU cores
import os
max_workers = os.cpu_count()
```

---

## 🎓 Learning Resources

### Caching
- [Python functools.lru_cache](https://docs.python.org/3/library/functools.html#functools.lru_cache)
- [Caching Strategies](https://aws.amazon.com/caching/best-practices/)

### Parallel Processing
- [concurrent.futures](https://docs.python.org/3/library/concurrent.futures.html)
- [Python Threading vs Multiprocessing](https://realpython.com/python-concurrency/)

### API Optimization
- [Wikipedia API Documentation](https://www.mediawiki.org/wiki/API:Main_page)
- [Batch API Requests](https://www.mediawiki.org/wiki/API:Query)

---

## 🚀 Next Steps

After implementing Quick Wins:
1. **Measure**: Run benchmarks, collect metrics
2. **Analyze**: Identify remaining bottlenecks
3. **Optimize**: Move to Phase 3 (Advanced Optimizations)
4. **Scale**: Implement distributed system (Phase 5)

**Remember**: 
- Start with easiest wins first
- Measure before and after
- Document everything
- Celebrate small victories! 🎉

---

## 📝 Summary

**Quick Wins = Big Impact!**

With just **1-2 weeks** of work, you can achieve:
- ⚡ **60-70% faster** searches
- 💾 **90% fewer** API calls
- 🎯 **Better** user experience
- 📊 **Measurable** improvements

**Start today, see results tomorrow!** 🚀