# 📊 Wikipedia ML - İlerleme Kaydı

Bu döküman projede atılan her adımı, sonuçları ve öğrenilenleri detaylandırır.

---

## 🎯 Proje Hedefi

Wikipedia oyununu oynayan bir AI sistemi: Bir başlangıç sayfasından sadece linklere tıklayarak hedef sayfaya en az adımda ulaşmak.

---

## 📅 Adım 1: Proje Kurulumu ve Temel Yapı

**Tarih**: Başlangıç
**Süre**: ~30 dakika
**Durum**: ✅ Tamamlandı

### Yapılanlar:

1. **WikipediaScraper** (`src/scraper.py`)
   - HTTP requests ile Wikipedia sayfalarını çekme
   - BeautifulSoup ile HTML parsing
   - Link extraction ve filtreleme
   - Özel sayfaları hariç tutma (File:, Help:, Template: vs.)

2. **WikiNavigator** (`src/navigator.py`)
   - Random walk implementasyonu
   - Test amaçlı basit gezinti

3. **Proje Dökümantasyonu**
   - `PROJECT_CONTEXT.md`: Proje bağlamı
   - `ROADMAP.md`: Detaylı yol haritası (5 faz)

### Kod Örneği:

```python
class WikipediaScraper:
    def get_page_html(self, page_title: str) -> BeautifulSoup:
        url = self.base_url + page_title
        response = requests.get(url, headers=self.headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup

    def get_wiki_links(self, soup: BeautifulSoup) -> list[str]:
        # Ana içerik alanındaki linkleri filtrele
        # Özel sayfaları, anchor linkleri, duplicate'leri çıkar
        return wiki_links
```

### Öğrenilenler:

- ✅ Wikipedia HTML yapısı (`mw-content-text` div'i)
- ✅ Link filtreleme teknikleri
- ✅ User-Agent header'ı ile bot algılamadan kaçınma
- ✅ Rate limiting önemli (Wikipedia spam koruması)

### Sonuçlar:

- Ortalama sayfa başına **~500 link** bulunuyor
- Sayfa çekme süresi: **~0.5 saniye** (network + parsing)

---

## 📅 Adım 2: BFS (Breadth-First Search) Algoritması

**Tarih**: İkinci gün
**Süre**: ~1 saat
**Durum**: ✅ Tamamlandı

### Yapılanlar:

1. **PathFinder Class** (`src/pathfinder.py`)
   - BFS algoritması implementasyonu
   - Queue-based level-by-level search
   - Visited tracking (döngülerden kaçınma)
   - Performance metrics tracking

2. **Test Suite** (`main.py`)
   - Farklı zorluk seviyelerinde testler
   - Verbose output (her adımı görme)
   - Metrics reporting

### Algoritma Mantığı:

```python
def bfs_search(start, target):
    queue = deque([(start, [start])])  # (sayfa, path)
    visited = {start}

    while queue:
        current_page, path = queue.popleft()

        # Sayfa linklerini al
        links = get_page_links(current_page)

        for link in links:
            if link == target:
                return path + [link]  # BULUNDU!

            if link not in visited:
                queue.append((link, path + [link]))
                visited.add(link)

    return None  # Bulunamadı
```

### Test Sonuçları:

| Test | Başlangıç | Hedef | Adım | Sayfa Tarandı | Süre |
|------|-----------|-------|------|---------------|------|
| Kolay | Potato | Vegetable | 2 | 5 | 3.55s |
| Orta | Potato | United_States | 1 | 1 | 0.48s |
| Zor | Potato | Barack_Obama | 2 | 21 | 9.57s |

### Öğrenilenler:

- ✅ BFS **garantili** en kısa path'i bulur
- ✅ Complexity: **O(k^d)** - k=avg links, d=depth
- ✅ Wikipedia sayfaları çok bağlantılı (small world network)
- ✅ 6 derece of separation kuralı genelde geçerli

### Keşfedilen İlginç Pathler:

```
Potato → United_States (1 adım!)
  Neden? Potato sayfasında ABD tarihçesi/üretimi var

Potato → Southern_United_States → Barack_Obama (2 adım)
  Patates → Güney ABD → Obama (coğrafi/tarihsel bağlantı)
```

### Sorunlar:

❌ **Yavaş**: Tüm linkleri kör bir şekilde tarıyor
❌ **Memory intensive**: Queue çok büyüyebilir (500+ link)
❌ **No intelligence**: Hedefe yakınlık bilmiyor

---

## 📅 Adım 3: Bidirectional BFS - İki Yönlü Arama

**Tarih**: Üçüncü gün
**Süre**: ~2 saat
**Durum**: ✅ Tamamlandı

### Yapılanlar:

1. **Bidirectional BFS Algoritması**
   - Hem baştan hem sondan arama
   - İki queue, iki visited set
   - Kesişme noktası tespiti
   - Path reconstruction (merge)

2. **Karşılaştırma Test Suite**
   - Normal BFS vs Bidirectional BFS
   - Performance metrics
   - İyileştirme yüzdeleri

### Algoritma Mantığı:

```python
def bidirectional_bfs(start, target):
    forward_queue = deque([(start, [start])])
    backward_queue = deque([(target, [target])])
    forward_visited = {start: [start]}
    backward_visited = {target: [target]}

    while forward_queue and backward_queue:
        # FORWARD: start'tan ilerle
        for ... in forward_queue:
            for link in links:
                if link in backward_visited:
                    # KESİŞME BULUNDU!
                    return merge_paths(forward, backward)

        # BACKWARD: target'tan ilerle
        for ... in backward_queue:
            for link in links:
                if link in forward_visited:
                    # KESİŞME BULUNDU!
                    return merge_paths(forward, backward)
```

### Karşılaştırma Sonuçları:

#### Test 1: Potato → Vegetable
| Metrik | Normal BFS | Bidirectional | İyileştirme |
|--------|------------|---------------|-------------|
| Adım | 2 | 2 | - |
| Taranan sayfa | 5 | 2 | **%60 azalma** |
| Süre | 2.51s | 1.26s | **%50 hızlanma** |
| Max queue | 534 | 2 | **%99.6 azalma** |

#### Test 2: Python → Computer
| Metrik | Normal BFS | Bidirectional | İyileştirme |
|--------|------------|---------------|-------------|
| Adım | 2 | 2 | - |
| Taranan sayfa | 6 | 2 | **%66.7 azalma** |
| Süre | 2.80s | 1.39s | **%50.5 hızlanma** |
| Max queue | 709 | 2 | **%99.7 azalma** |

#### Test 3: Albert_Einstein → Pizza 🚀
| Metrik | Normal BFS | Bidirectional | İyileştirme |
|--------|------------|---------------|-------------|
| Adım | 2 | 2 | - |
| Taranan sayfa | **356** | **2** | **%99.4 azalma** 🔥 |
| Süre | **217.92s** | **1.51s** | **%99.3 hızlanma** ⚡ |
| Max queue | 1094 | 2 | **%99.8 azalma** |

### Neden Bu Kadar Etkili?

**Matematiksel Açıklama:**

Normal BFS'de her seviyede exponential growth var:
```
Seviye 0: 1 sayfa
Seviye 1: k sayfa (k = avg link count)
Seviye 2: k² sayfa
Seviye 3: k³ sayfa
...
Seviye d: k^d sayfa

Toplam: 1 + k + k² + ... + k^d ≈ k^d
```

Bidirectional BFS'de:
```
Forward d/2 seviye: k^(d/2) sayfa
Backward d/2 seviye: k^(d/2) sayfa

Toplam: 2 × k^(d/2) sayfa
```

**Örnek (k=500, d=4):**
- Normal BFS: 500^4 = **62,500,000,000 sayfa** 😱
- Bidirectional: 2 × 500^2 = **500,000 sayfa** (125,000x daha az!)

### Gerçek Hayat Örneği:

**Einstein → Pizza testinde neler oldu?**

1. **Forward Search** (Einstein'dan):
   - Einstein sayfasında "Italy" linki var (doğum yeri)

2. **Backward Search** (Pizza'dan):
   - Pizza sayfasında "Italy" linki var (menşei)

3. **İlk seviyede kesişme!**
   - Italy ortak nokta
   - Toplam 2 sayfa tarandı (Einstein, Pizza)
   - Normal BFS 356 sayfa taradı!

### Öğrenilenler:

- ✅ Exponential growth'u yarıya böler: `k^d → 2×k^(d/2)`
- ✅ Popüler sayfalar (Italy, United_States) hemen kesişme yaratır
- ✅ Wikipedia'nın hub sayfaları var (çok linkli)
- ✅ Bidirectional her zaman daha iyi (memory + speed)

### Detaylı Açıklama:

`BIDIRECTIONAL_BFS_EXPLAINED.md` dosyasında:
- Görsel örnekler
- Kod açıklamaları
- Path merge mantığı
- Kesişme tespiti

---

## 📅 Adım 4: Code Refactoring ve Optimization

**Tarih**: Dördüncü gün
**Süre**: ~2 saat
**Durum**: ✅ Tamamlandı

### Tespit Edilen Sorunlar:

1. **Kod Tekrarı** (DRY ihlali)
   - BFS ve Bidirectional BFS'de aynı kod blokları
   - Metrics initialization tekrar tekrar
   - Print fonksiyonları duplicate

2. **Performance**
   - Her seferinde aynı sayfayı tekrar çekiyoruz
   - Cache yok
   - Network overhead

3. **Type Safety**
   - Results dictionary döndürülüyor (type-safe değil)
   - Runtime error riski

4. **Gereksiz Class**
   - WikiNavigator kullanılmıyor
   - Kod karmaşası

### Yapılan İyileştirmeler:

#### 1. WikipediaScraper - LRU Cache Eklendi

```python
class WikipediaScraper:
    def __init__(self, cache_size=128):
        self._cache = OrderedDict()  # LRU cache
        self.cache_hits = 0
        self.cache_misses = 0

    def get_page_html(self, page_title):
        # Cache'de var mı?
        if page_title in self._cache:
            self.cache_hits += 1
            self._cache.move_to_end(page_title)  # Recently used
            return self._cache[page_title]

        # Yoksa Wikipedia'dan çek
        self.cache_misses += 1
        soup = self._fetch_from_wikipedia(page_title)
        self._add_to_cache(page_title, soup)
        return soup
```

**Cache Mantığı:**
- OrderedDict ile LRU (Least Recently Used)
- Cache dolduğunda en eski entry silinir
- move_to_end() ile recently used tracking
- Hit/miss statistics

**Beklenen Kazanç:**
- Bidirectional BFS'de aynı sayfalar (hub'lar) sık çekiliyor
- Cache hit rate: **%30-50** bekleniyor
- Network call azalması: **%30-50 hızlanma**

#### 2. PathFinder - Helper Metodlar (DRY)

**Öncesi (Kod Tekrarı):**
```python
def bfs_search(...):
    # Metrics init
    self.pages_explored = 0
    self.max_queue_size = 0
    start_time = time.time()

    # Print header
    print("=" * 60)
    print("BFS SEARCH")
    ...

    # Get links
    soup = self.scraper.get_page_html(page)
    links = self.scraper.get_wiki_links(soup)
    self.pages_explored += 1
    ...

def bidirectional_bfs(...):
    # AYNI KOD TEKRAR! 😢
    self.pages_explored = 0
    self.max_queue_size = 0
    start_time = time.time()
    ...
```

**Sonrası (Helper Metodlar):**
```python
# Helper metodlar
def _initialize_search(self):
    self.pages_explored = 0
    self.max_queue_size = 0
    self.start_time = time.time()

def _print_header(self, algorithm, start, target):
    # Tek bir yerde print logic

def _get_page_links(self, page):
    # Sayfa çek + link al + metric update
    self.pages_explored += 1
    soup = self.scraper.get_page_html(page)
    return self.scraper.get_wiki_links(soup)

def _create_result(self, found, path, algorithm):
    # SearchResult dataclass oluştur
    return SearchResult(...)

# Ana metodlar
def bfs_search(...):
    self._initialize_search()  # ✅ Temiz!
    self._print_header("BFS", start, target)
    links = self._get_page_links(page)
    return self._create_result(True, path, "BFS")
```

**Kazanç:**
- Kod satırı: **~480 → ~395** (%18 azalma)
- Maintainability: Tek bir yerde değişiklik
- Readability: Daha anlaşılır

#### 3. SearchResult Dataclass (Type-Safe)

**Öncesi:**
```python
return {
    'found': True,
    'path': [...]
    'steps': 2,
    # Typo riski: 'stpes' yazarsan runtime error!
}
```

**Sonrası:**
```python
@dataclass
class SearchResult:
    found: bool
    path: list[str]
    steps: int
    pages_explored: int
    time_seconds: float
    max_queue_size: int
    algorithm: str

return SearchResult(
    found=True,
    path=[...],
    steps=2,
    # IDE autocomplete!
    # Compile-time type checking!
)
```

**Kazanç:**
- ✅ Type safety (IDE yardımı)
- ✅ Autocomplete
- ✅ Runtime error riski yok
- ✅ Daha temiz kod

#### 4. Gereksiz Kod Temizliği

**Silinen:**
- ❌ WikiNavigator class (kullanılmıyor)
- ❌ test_random_walk() (eski test)
- ❌ Gereksiz comment'ler
- ❌ Duplicate kod blokları

**Sonuç:**
- Daha clean codebase
- Daha az kafa karışıklığı
- Sadece gerekli kod

### Refactor Sonrası Proje Yapısı:

```
WikipediaML/
├── src/
│   ├── scraper.py           (Cache eklenmiş) ✅
│   └── pathfinder.py        (Helper metodlar + Dataclass) ✅
├── main.py                  (Temizlenmiş) ✅
├── PROJECT_CONTEXT.md       (Proje bağlamı)
├── ROADMAP.md               (5 fazlı plan)
├── BIDIRECTIONAL_BFS_EXPLAINED.md  (Detaylı açıklama)
├── REFACTOR_PLAN.md         (Refactor planı)
└── PROGRESS_LOG.md          (Bu dosya!)
```

### Beklenen Performance İyileştirmesi:

| Metrik | Öncesi | Sonrası (Beklenen) |
|--------|--------|-------------------|
| Cache Hit Rate | %0 | %30-50 |
| Network Calls | 100% | %50-70 |
| Execution Time | Baseline | %30-50 daha hızlı |
| Memory | Baseline | +10-20MB (cache) |
| Kod Satırı | 480 | 395 (%18 azalma) |

### Öğrenilenler:

- ✅ DRY principle önemli (Don't Repeat Yourself)
- ✅ Cache = Bedava performance
- ✅ Dataclass > Dictionary (type safety)
- ✅ Helper metodlar kod kalitesini artırır
- ✅ Gereksiz kod teknik borç oluşturur

---

## 📊 Genel Özet - Şu Ana Kadar

### Tamamlanan Adımlar:

1. ✅ **Proje Setup**: WikipediaScraper, temel yapı
2. ✅ **BFS Algoritması**: İlk pathfinding
3. ✅ **Bidirectional BFS**: %99 performance kazancı
4. ✅ **Code Refactoring**: Cache, DRY, type safety

### Sayısal Başarılar:

- **Bidirectional BFS kazancı**: %99.4 daha az sayfa tarama
- **Hızlanma**: 217s → 1.5s (144x daha hızlı!)
- **Kod kalitesi**: %18 daha az kod, daha temiz
- **Cache beklentisi**: %30-50 ek hızlanma

### Öğrenilenler:

- ✅ Graph search algoritmaları (BFS, Bidirectional)
- ✅ Wikipedia'nın small-world network yapısı
- ✅ Exponential growth'u optimize etme
- ✅ LRU cache implementasyonu
- ✅ Python dataclass ve type hints
- ✅ Clean code principles (DRY, helper metodlar)

---

## 🚀 Sırada Ne Var?

### Faz 2: Machine Learning - Semantic Search

**Hedef**: Linkleri "akıllıca" seçmek (random değil!)

**Plan:**
1. **Sentence Transformers**: Embedding model kurulumu
2. **Semantic Similarity**: Cosine similarity ile link skorlama
3. **Greedy Semantic Search**: En yakın link'i seç
4. **Beam Search**: Top-k linkleri paralel explore et

**Beklenen Kazanç:**
- Daha az sayfa tarama (semantically yakın path)
- Success rate artışı
- Gerçek "akıllı" navigasyon

**İlk Test:**
```python
# Embedding örnekleri
"Potato" → embedding_vector
"Vegetable" → embedding_vector
cosine_similarity(potato, vegetable) → 0.85 (çok yakın!)
cosine_similarity(potato, computer) → 0.12 (uzak)
```

---

## 📝 Notlar

### Test Etme Talimatları:

```bash
# Virtual environment aktif et
source venv/bin/activate

# Testleri çalıştır
python main.py

# Cache statistics'i görüntüle
# PathFinder sonunda otomatik gösterilecek
```

### Önemli Dosyalar:

- `PROJECT_CONTEXT.md`: Her session'da oku (bağlam)
- `ROADMAP.md`: Genel plan (5 faz)
- `BIDIRECTIONAL_BFS_EXPLAINED.md`: Bidirectional detaylar
- `PROGRESS_LOG.md`: Bu dosya (her adım)

### Değişiklik Takibi:

Her önemli değişiklikten sonra bu dosyayı güncelle:
- Yapılan iş
- Sonuçlar (sayısal)
- Öğrenilenler
- Kod örnekleri
