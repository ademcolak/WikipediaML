# 🚀 Performance Optimization Plan

## 📊 Mevcut Durum Analizi

### Şu Anki Performans
- ✅ Bidirectional beam search: %80-90 daha az sayfa
- ✅ Graph cache: 2000x+ hızlanma (0.00s)
- ✅ Embedding cache: %20-30 hit rate
- ✅ Scraper cache: %0-10 hit rate (düşük!)

### Bottleneck'ler
1. **Network I/O**: Wikipedia'dan sayfa çekme (~500ms/sayfa)
2. **Embedding Computation**: 100+ link için embedding (~200-300ms)
3. **HTML Parsing**: BeautifulSoup parsing (~50-100ms)
4. **Sequential Processing**: Tek tek sayfa işleme

---

## 🎯 Öncelikli İyileştirmeler (Hız & Performance)

### 1. 🔥 Parallel/Async Processing (En Büyük Kazanç!)

**Sorun:** Şu anda tüm işlemler sequential (sıralı)
```python
# Şu anki durum (YAVAŞ):
for page in beam:
    soup = scraper.get_page_html(page)  # 500ms bekle
    links = scraper.get_wiki_links(soup)  # 100ms bekle
    embeddings = embedder.get_embeddings_batch(links)  # 300ms bekle
# Toplam: 900ms × beam_size
```

**Çözüm:** Async/parallel processing
```python
# Yeni yaklaşım (HIZLI):
import asyncio
import aiohttp

async def fetch_pages_parallel(pages):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_page(session, page) for page in pages]
        return await asyncio.gather(*tasks)
# Toplam: 900ms (hepsi paralel!)
```

**Beklenen Kazanç:**
- Beam width=4 için: 4x hızlanma
- 13.85s → 3.5s (Minimax → U.S._Route_111)

**Implementasyon:**
- `src/async_scraper.py` - Async Wikipedia fetcher
- `aiohttp` dependency ekle
- `asyncio` ile parallel processing

---

### 2. 🧠 Embedding Batch Optimization

**Sorun:** Her depth'te 100+ link için embedding hesaplanıyor
```python
# Şu anki durum:
links = get_wiki_links(page)  # 500 link
embeddings = embedder.get_embeddings_batch(links)  # 500 embedding!
```

**Çözüm 1: Pre-filtering**
```python
# Link'leri önce basit heuristic'lerle filtrele
def quick_filter(links, target):
    # 1. Ortak kelimeler var mı?
    target_words = set(target.lower().split('_'))
    scored_links = []
    for link in links:
        link_words = set(link.lower().split('_'))
        overlap = len(target_words & link_words)
        if overlap > 0:
            scored_links.append((link, overlap))
    
    # En iyi 50'yi al
    scored_links.sort(key=lambda x: x[1], reverse=True)
    return [link for link, _ in scored_links[:50]]

# Sonra embedding hesapla
filtered = quick_filter(links, target)  # 500 → 50
embeddings = embedder.get_embeddings_batch(filtered)  # 50 embedding
```

**Beklenen Kazanç:**
- Embedding computation: %80-90 azalma
- 300ms → 30-50ms per depth

**Çözüm 2: GPU Acceleration**
```python
# Model'i GPU'ya taşı (eğer varsa)
self.model = SentenceTransformer(model_name, device='cuda')
```

**Beklenen Kazanç:**
- Embedding computation: 5-10x hızlanma
- 300ms → 30-60ms

---

### 3. 📦 Wikipedia Categories Integration

**Sorun:** Semantic similarity bazen yeterli değil
```
Minimax (game theory) → U.S._Route_111 (road)
Semantic similarity: 0.142 (çok düşük!)
```

**Çözüm:** Wikipedia kategorilerini kullan
```python
def get_page_categories(page_title):
    # Wikipedia API kullan (daha hızlı!)
    url = f"https://en.wikipedia.org/w/api.php"
    params = {
        'action': 'query',
        'titles': page_title,
        'prop': 'categories',
        'format': 'json'
    }
    response = requests.get(url, params=params)
    return extract_categories(response.json())

# Kategori overlap'i hesapla
def category_similarity(page1_cats, page2_cats):
    overlap = len(set(page1_cats) & set(page2_cats))
    return overlap / max(len(page1_cats), len(page2_cats))

# Hybrid scoring
final_score = 0.7 * semantic_sim + 0.3 * category_sim
```

**Beklenen Kazanç:**
- Daha akıllı link seçimi
- Başarı oranı artışı: %95 → %98+
- Daha kısa path'ler

---

### 4. 🗄️ Persistent Embedding Cache

**Sorun:** Embedding cache her çalıştırmada sıfırlanıyor
```python
# Her çalıştırmada:
embedder = WikiEmbedder()  # Cache boş!
```

**Çözüm:** Disk'e kaydet
```python
import pickle

class WikiEmbedder:
    def __init__(self, cache_file='embeddings_cache.pkl'):
        self.model = SentenceTransformer(...)
        self._load_cache(cache_file)
    
    def _load_cache(self, cache_file):
        if os.path.exists(cache_file):
            with open(cache_file, 'rb') as f:
                self._embedding_cache = pickle.load(f)
    
    def save_cache(self):
        with open(self.cache_file, 'wb') as f:
            pickle.dump(self._embedding_cache, f)
```

**Beklenen Kazanç:**
- İkinci çalıştırma: %50-70 cache hit rate
- Embedding computation: %50-70 azalma

---

### 5. 🎯 Hub Page Detection & Prioritization

**Sorun:** Hub sayfalar (United_States, Italy) geç keşfediliyor

**Çözüm:** Popüler sayfaları önceliklendir
```python
# Popüler hub sayfalar listesi
HUB_PAGES = {
    'United_States': 1.5,
    'United_Kingdom': 1.5,
    'Europe': 1.4,
    'Asia': 1.4,
    'World_War_II': 1.3,
    'Computer': 1.3,
    # ... daha fazla
}

def score_link(link, semantic_sim):
    # Hub bonus
    hub_bonus = HUB_PAGES.get(link, 1.0)
    return semantic_sim * hub_bonus
```

**Beklenen Kazanç:**
- Daha hızlı kesişme
- Taranan sayfa: %20-30 azalma

---

### 6. 🔄 Adaptive Beam Width

**Sorun:** Sabit beam width her durumda optimal değil

**Çözüm:** Dinamik beam width
```python
def adaptive_beam_width(depth, similarity_scores):
    # Başlangıçta geniş, sonra daralt
    if depth <= 2:
        return 5  # Geniş exploration
    elif max(similarity_scores) > 0.7:
        return 2  # Yüksek confidence, dar beam
    else:
        return 4  # Orta confidence, orta beam
```

**Beklenen Kazanç:**
- Daha az gereksiz exploration
- %10-20 hızlanma

---

### 7. 📊 Smart Caching Strategy

**Sorun:** Scraper cache hit rate çok düşük (%0-10)

**Çözüm:** Predictive caching
```python
def prefetch_likely_pages(current_page, target):
    # Muhtemel sonraki sayfaları önceden çek
    likely_pages = predict_next_pages(current_page, target)
    
    # Background'da çek (async)
    asyncio.create_task(prefetch_pages(likely_pages))
```

**Beklenen Kazanç:**
- Cache hit rate: %10 → %40-50
- Network wait time: %40-50 azalma

---

## 📈 Implementasyon Önceliği

### Faz 1: Quick Wins (1-2 gün)
1. ✅ **Pre-filtering** (link sayısını azalt)
2. ✅ **Persistent embedding cache** (disk'e kaydet)
3. ✅ **Hub page detection** (popüler sayfaları önceliklendir)

**Beklenen Toplam Kazanç:** %40-50 hızlanma

### Faz 2: Major Improvements (3-5 gün)
4. ✅ **Async/parallel processing** (en büyük kazanç!)
5. ✅ **Wikipedia Categories** (daha akıllı seçim)
6. ✅ **Adaptive beam width** (dinamik optimization)

**Beklenen Toplam Kazanç:** %70-80 hızlanma

### Faz 3: Advanced (1 hafta+)
7. ✅ **GPU acceleration** (eğer GPU varsa)
8. ✅ **Neo4j integration** (production-ready graph)
9. ✅ **Predictive caching** (smart prefetch)

**Beklenen Toplam Kazanç:** %85-90 hızlanma

---

## 🎯 Hedef Performans

### Şu Anki Durum
| Senaryo | Süre | Taranan Sayfa |
|---------|------|---------------|
| Basit (Potato → Pizza) | 2.47s | 3 |
| Orta (Python → ML) | 9.72s | 15 |
| Kompleks (Minimax → Route) | 13.85s | 21 |

### Hedef (Tüm İyileştirmeler Sonrası)
| Senaryo | Süre | Taranan Sayfa | İyileştirme |
|---------|------|---------------|-------------|
| Basit | **0.5-1.0s** | 2-3 | %60-80 |
| Orta | **2-3s** | 8-12 | %70-80 |
| Kompleks | **3-5s** | 10-15 | %70-80 |

---

## 🔧 Teknik Stack Güncellemeleri

### Yeni Dependencies
```txt
# Async processing
aiohttp>=3.9.0
asyncio>=3.4.3

# GPU acceleration (opsiyonel)
torch>=2.0.0+cu118  # CUDA version

# Neo4j (opsiyonel)
neo4j>=5.0.0

# Performance monitoring
memory_profiler>=0.61.0
line_profiler>=4.0.0
```

### Yeni Modüller
```
src/
├── async_scraper.py      # Async Wikipedia fetcher
├── category_analyzer.py  # Wikipedia categories
├── hub_detector.py       # Hub page detection
├── performance_monitor.py # Performance tracking
└── cache_manager.py      # Advanced caching
```

---

## 📊 Monitoring & Profiling

### Performance Metrics
```python
class PerformanceMonitor:
    def track_metrics(self):
        return {
            'network_time': self.network_time,
            'embedding_time': self.embedding_time,
            'parsing_time': self.parsing_time,
            'cache_hit_rate': self.cache_hits / self.total_requests,
            'pages_per_second': self.pages_explored / self.total_time
        }
```

### Profiling Tools
```bash
# Memory profiling
python -m memory_profiler main.py Potato Pizza

# Line profiling
kernprof -l -v main.py Potato Pizza

# cProfile
python -m cProfile -o profile.stats main.py Potato Pizza
```

---

## 🎉 Sonuç

**En Büyük Kazançlar:**
1. 🔥 **Async/Parallel Processing**: 4-5x hızlanma
2. 🧠 **Pre-filtering**: 3-4x daha az embedding
3. 📦 **Categories**: Daha akıllı seçim
4. 🗄️ **Persistent Cache**: %50-70 cache hit

**Toplam Beklenen İyileştirme:**
- **Hız**: %70-85 daha hızlı
- **Başarı Oranı**: %95 → %98+
- **Kaynak Kullanımı**: %60-70 daha az

**Sonraki Adım:** Hangi iyileştirmeyle başlamak istersin?