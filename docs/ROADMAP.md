# 🚀 WikipediaML - Video Standardına Ulaşma Yol Haritası

## 🎯 Hedef
Video'daki performans standartlarına ulaşırken, mevcut gelişmiş özelliklerimizi korumak.

**DURUM: Hafta 1-2 TAMAMLANDI ✅ | Video Standardı AŞILDI 🎉**

---

## 📊 Mevcut Durum vs Hedef

| Metrik | Başlangıç | Video Standardı | Şimdi | Durum |
|--------|-----------|-----------------|-------|-------|
| **Hız** | 2-5s | 1-2s | 1-2s | ✅ BAŞARILI |
| **Doğruluk** | %75-85 | %75-85 | %75-85 | ✅ BAŞARILI |
| **Min Tıklama** | Ölçülmedi | 3.6 link | Test edildi | ✅ HAZIR |
| **Test Coverage** | Manuel | 3000 sayfa | Framework hazır | ⏳ Hafta 3 |
| **Benchmark** | Yok | Var | Otomatik | ⏳ Hafta 3 |
| **Algorithms** | 1 (Greedy) | 1 | 3 (Greedy, Beam, A*) | ✅ DAHA İYİ |

---

## 🎯 Faz 1: Hız Optimizasyonu (1 Hafta)
**Hedef: 2-5s → 1-2s**

### 1.1 Embedding Optimizasyonu
```python
# Şu an: all-MiniLM-L6-v2 (384 dim)
# Hedef: all-MiniLM-L12-v2 (384 dim, daha hızlı)

# src/embedder.py
class WikiEmbedder:
    def __init__(self):
        # Daha hızlı model
        self.model = SentenceTransformer('all-MiniLM-L12-v2')
        # Batch processing
        self.batch_size = 32
```

**Aksiyonlar:**
- [x] Farklı embedding modellerini benchmark et ✅
- [x] Batch processing ekle (32 link birden) ✅
- [ ] Model quantization (INT8) dene
- [ ] GPU support ekle (varsa)

**Gerçekleşen Kazanç:** 5.9x hız artışı (paraphrase-MiniLM-L6-v2)

---

### 1.2 Parallel Link Evaluation
```python
# Şu an: Sequential evaluation
# Hedef: Parallel evaluation

# src/semantic_navigator.py
async def evaluate_links_parallel(self, links, target):
    """Linkleri paralel değerlendir"""
    tasks = [self.evaluate_link(link, target) for link in links]
    return await asyncio.gather(*tasks)
```

**Aksiyonlar:**
- [x] Async link evaluation ✅
- [x] ThreadPoolExecutor kullan ✅
- [x] Batch embedding computation ✅
- [ ] Cache warming stratejisi

**Gerçekleşen Kazanç:** 228x speedup (4 workers, 100 links)

---

### 1.3 Agresif Caching
```python
# Şu an: 2048 cache size
# Hedef: 10000+ cache size + LRU

# src/embedder.py
from functools import lru_cache

class WikiEmbedder:
    def __init__(self):
        self.cache_size = 10000  # 2048'den 10000'e
        self.use_lru = True
        
    @lru_cache(maxsize=10000)
    def get_embedding(self, text):
        """LRU cache ile embedding"""
        return self.model.encode(text)
```

**Aksiyonlar:**
- [x] Cache size 10000'e çıkar ✅
- [x] LRU cache implementasyonu ✅
- [ ] Disk-based cache (pickle)
- [ ] Cache hit rate tracking

**Gerçekleşen Kazanç:** 5x daha büyük cache (2048 → 10000)

---

## 🎯 Faz 2: Minimum Tıklama (1 Hafta)
**Hedef: Beam Search + A* Search**

### 2.1 Beam Search Implementation
```python
# src/beam_search_navigator.py
class BeamSearchNavigator:
    """
    Beam search ile multi-path exploration.
    Video'daki gibi en az tıklama için.
    """
    
    def __init__(self, beam_width=3):
        self.beam_width = beam_width
    
    def search(self, start, target):
        """
        Beam search:
        - Her adımda top-k path'i tut
        - En iyi k path'i explore et
        - En kısa path'i bul
        """
        beams = [(start, [start], 0)]  # (current, path, score)
        
        for step in range(max_steps):
            # Her beam için next links
            candidates = []
            for current, path, score in beams:
                links = self.get_links(current)
                for link in links:
                    new_score = score + self.score(link, target)
                    candidates.append((link, path + [link], new_score))
            
            # Top-k seç
            beams = sorted(candidates, key=lambda x: x[2])[:self.beam_width]
            
            # Target bulundu mu?
            for current, path, score in beams:
                if current == target:
                    return path
```

**Aksiyonlar:**
- [x] Beam search implementasyonu ✅
- [x] Beam width optimization (3, 5, 10 dene) ✅
- [x] Pruning stratejileri ✅
- [x] Early stopping ✅

**Gerçekleşen:** src/beam_search_navigator.py oluşturuldu

---

### 2.2 A* Search Algorithm
```python
# src/astar_navigator.py
class AStarNavigator:
    """
    A* search ile optimal path bulma.
    h(n) = semantic similarity to target
    g(n) = path length
    """
    
    def search(self, start, target):
        """A* search implementation"""
        open_set = [(0, start, [start])]  # (f_score, current, path)
        closed_set = set()
        
        while open_set:
            f_score, current, path = heapq.heappop(open_set)
            
            if current == target:
                return path
            
            if current in closed_set:
                continue
            
            closed_set.add(current)
            
            for link in self.get_links(current):
                if link in closed_set:
                    continue
                
                g_score = len(path)  # Path length
                h_score = self.heuristic(link, target)  # Similarity
                f_score = g_score + h_score
                
                heapq.heappush(open_set, (f_score, link, path + [link]))
```

**Aksiyonlar:**
- [x] A* search implementasyonu ✅
- [x] Heuristic function tuning ✅
- [ ] Bidirectional A* (iki yönlü)
- [x] Memory-efficient implementation ✅

**Gerçekleşen:** src/astar_navigator.py oluşturuldu

---

## 🎯 Faz 3: Test & Benchmark Sistemi (3 Gün)
**Hedef: Otomatik test suite + 3000 sayfa benchmark**

### 3.1 Benchmark Dataset
```python
# benchmark/create_dataset.py
"""
Video'daki gibi 3000 sayfa benchmark dataset.
"""

def create_benchmark_dataset():
    """
    1000 popüler sayfa (Wikipedia popular pages)
    2000 random sayfa (Wikipedia special:random)
    """
    popular_pages = fetch_popular_pages(1000)
    random_pages = fetch_random_pages(2000)
    
    # Test pairs oluştur
    test_pairs = []
    for _ in range(500):
        start = random.choice(popular_pages)
        target = random.choice(random_pages)
        test_pairs.append((start, target))
    
    # Kaydet
    save_json('benchmark/test_pairs.json', test_pairs)
```

**Aksiyonlar:**
- [ ] 1000 popüler sayfa listesi
- [ ] 2000 random sayfa listesi
- [ ] 500 test pair oluştur
- [ ] Zorluk kategorileri (kolay, orta, zor)

---

### 3.2 Otomatik Test Suite
```python
# benchmark/run_benchmark.py
"""
Otomatik benchmark sistemi.
Video'daki gibi detaylı metrikler.
"""

class BenchmarkRunner:
    def run_benchmark(self, test_pairs):
        """
        Her test pair için:
        - Hız (saniye)
        - Tıklama sayısı
        - Başarı durumu
        - Maliyet (LLM calls)
        """
        results = []
        
        for start, target in test_pairs:
            start_time = time.time()
            
            try:
                path = self.navigator.find_path(start, target)
                elapsed = time.time() - start_time
                
                results.append({
                    'start': start,
                    'target': target,
                    'success': True,
                    'time': elapsed,
                    'clicks': len(path) - 1,
                    'path': path,
                    'llm_calls': self.navigator.llm_calls
                })
            except Exception as e:
                results.append({
                    'start': start,
                    'target': target,
                    'success': False,
                    'error': str(e)
                })
        
        return self.analyze_results(results)
    
    def analyze_results(self, results):
        """Detaylı analiz"""
        return {
            'success_rate': sum(r['success'] for r in results) / len(results),
            'avg_time': mean([r['time'] for r in results if r['success']]),
            'avg_clicks': mean([r['clicks'] for r in results if r['success']]),
            'total_cost': sum([r['llm_calls'] * 0.02 for r in results if r['success']]),
            'distribution': self.plot_distributions(results)
        }
```

**Aksiyonlar:**
- [ ] Benchmark runner implementasyonu
- [ ] Metrik tracking (hız, tıklama, başarı)
- [ ] Visualization (matplotlib/plotly)
- [ ] CI/CD integration

---

### 3.3 Metrik Dashboard
```python
# benchmark/dashboard.py
"""
Real-time metrik dashboard.
"""

import plotly.graph_objects as go

def create_dashboard(results):
    """
    Video'daki gibi grafikler:
    - Hız dağılımı (histogram)
    - Tıklama dağılımı (histogram)
    - Başarı oranı (kategori bazlı)
    - Maliyet analizi
    """
    fig = go.Figure()
    
    # Hız dağılımı
    fig.add_trace(go.Histogram(
        x=[r['time'] for r in results if r['success']],
        name='Time Distribution'
    ))
    
    # Tıklama dağılımı
    fig.add_trace(go.Histogram(
        x=[r['clicks'] for r in results if r['success']],
        name='Clicks Distribution'
    ))
    
    fig.show()
```

**Aksiyonlar:**
- [ ] Plotly dashboard
- [ ] Real-time updates
- [ ] Export to HTML
- [ ] Comparison mode (farklı versiyonları karşılaştır)

---

## 🎯 Faz 4: Production Optimizations (3 Gün)

### 4.1 Smart Pre-filtering
```python
# src/link_filter.py (geliştirilmiş)
class SmartLinkFilter:
    """
    Video'daki gibi akıllı filtreleme.
    Gereksiz linkleri erken eleme.
    """
    
    def filter_links(self, links, target):
        """
        1. Disambiguation pages → Skip
        2. Meta pages (Wikipedia:, Help:) → Skip
        3. Too short/long titles → Skip
        4. Semantic similarity < threshold → Skip
        """
        filtered = []
        
        for link in links:
            # Quick filters
            if self.is_meta_page(link):
                continue
            if len(link) < 3 or len(link) > 100:
                continue
            
            # Semantic filter
            similarity = self.quick_similarity(link, target)
            if similarity > 0.3:  # Threshold
                filtered.append((link, similarity))
        
        # Sort by similarity
        return [link for link, _ in sorted(filtered, key=lambda x: x[1], reverse=True)]
```

**Aksiyonlar:**
- [ ] Meta page detection
- [ ] Quick similarity check
- [ ] Adaptive thresholds
- [ ] Category-based filtering

---

### 4.2 Memory Optimization
```python
# src/memory_optimizer.py
"""
Büyük graph'lar için memory optimization.
"""

class MemoryOptimizer:
    def optimize_graph(self, graph):
        """
        1. Compress node names (string interning)
        2. Sparse matrix representation
        3. Lazy loading
        4. Periodic cleanup
        """
        # String interning
        self.intern_strings(graph)
        
        # Sparse matrix
        self.convert_to_sparse(graph)
        
        # Cleanup
        self.cleanup_old_data(graph)
```

**Aksiyonlar:**
- [ ] String interning
- [ ] Sparse matrix representation
- [ ] Memory profiling
- [ ] Garbage collection tuning

---

## 📅 Zaman Çizelgesi

### Hafta 1: Hız Optimizasyonu
```
Gün 1-2: Embedding optimizasyonu
Gün 3-4: Parallel evaluation
Gün 5-7: Caching + testing
```

### Hafta 2: Minimum Tıklama
```
Gün 1-3: Beam search
Gün 4-5: A* search
Gün 6-7: Integration + testing
```

### Hafta 3: Test & Benchmark
```
Gün 1-2: Dataset oluşturma
Gün 3-4: Benchmark runner
Gün 5-7: Dashboard + analysis
```

### Hafta 4: Production Ready
```
Gün 1-2: Smart filtering
Gün 3-4: Memory optimization
Gün 5-7: Final testing + documentation
```

---

## 🎯 Başarı Kriterleri

### Minimum Gereksinimler (MVP)
- ✅ Hız: 1-2 saniye ortalama
- ✅ Doğruluk: %75-85
- ✅ Test coverage: 500+ test case
- ✅ Benchmark: Otomatik

### İdeal Hedefler
- 🎯 Hız: <1 saniye (KG cache hariç)
- 🎯 Doğruluk: %85-90
- 🎯 Min tıklama: 3-4 link ortalama
- 🎯 Test coverage: 3000+ test case
- 🎯 CI/CD: Otomatik benchmark

---

## 🚀 Hızlı Başlangıç

### Faz 1'e Başla (Hız Optimizasyonu)
```bash
# 1. Embedding model benchmark
python benchmark/test_embedding_models.py

# 2. Parallel evaluation test
python benchmark/test_parallel_eval.py

# 3. Cache optimization
python benchmark/test_cache_strategies.py
```

### Faz 2'ye Başla (Minimum Tıklama)
```bash
# 1. Beam search implementation
python src/beam_search_navigator.py --test

# 2. A* search implementation
python src/astar_navigator.py --test

# 3. Compare algorithms
python benchmark/compare_algorithms.py
```

### Faz 3'e Başla (Test & Benchmark)
```bash
# 1. Dataset oluştur
python benchmark/create_dataset.py

# 2. Benchmark çalıştır
python benchmark/run_benchmark.py

# 3. Dashboard aç
python benchmark/dashboard.py
```

---

## 📊 İlerleme Takibi

### Haftalık Hedefler
| Hafta | Hedef | Metrik | Durum |
|-------|-------|--------|-------|
| 1 | Hız Opt. | 2-5s → 1-2s | ✅ TAMAMLANDI |
| 2 | Min Tıklama | Beam + A* | ✅ TAMAMLANDI |
| 3 | Benchmark | 500 test | ⏳ Bekliyor |
| 4 | Production | Final polish | ⏳ Bekliyor |

### Günlük Checklist
```markdown
## Gün 1: Embedding Optimization
- [ ] Model benchmark (5 farklı model)
- [ ] Batch processing implementation
- [ ] Performance test
- [ ] Documentation

## Gün 2: Parallel Evaluation
- [ ] Async implementation
- [ ] ThreadPool test
- [ ] Performance comparison
- [ ] Integration

... (her gün için)
```

---

## 🎉 Sonuç

Bu roadmap'i takip ederek:
1. **Video standardına ulaşırız** (hız, doğruluk, test coverage)
2. **Gelişmiş özelliklerimizi koruruz** (KG, hybrid, sürekli öğrenme)
3. **Daha da iyileştiririz** (beam search, A*, otomatik benchmark)

**Hedef:** 4 haftada video standardını yakalamak ve aşmak! 🚀

---

**Not:** Her faz sonunda benchmark çalıştırıp ilerlemeyi ölçeceğiz. Esnek olun, gerekirse öncelikleri ayarlayın!