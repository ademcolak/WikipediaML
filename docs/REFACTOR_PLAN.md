# 🔧 Refactor Planı

## 📋 Tespit Edilen Sorunlar

### 1. PathFinder - Kod Tekrarı (DRY İhlali)
**Sorun**: `bfs_search` ve `bidirectional_bfs_search` metodlarında çok fazla ortak kod var.

**Ortak kodlar**:
- Metrics initialization (pages_explored, total_time, max_queue_size)
- Edge case kontrolü (start == target)
- Verbose printing (başlık, sonuç)
- Path reconstruction ve printing
- Wikipedia rate limiting (time.sleep)
- Sayfa çekme ve link alma

**Çözüm**:
```python
# Helper metodlar oluştur:
- _initialize_metrics()
- _check_edge_case(start, target)
- _get_page_links(page) → soup çek + link al + metric update
- _reconstruct_path(forward_path, backward_path, intersection)
- _create_result_dict(found, path, ...)
```

### 2. WikiNavigator - Gereksiz Sınıf
**Sorun**:
- Sadece `random_walk` metodu var
- PathFinder daha gelişmiş ve kullanılıyor
- İki ayrı class kafa karıştırıcı

**Çözüm**:
- `random_walk` metodunu PathFinder'a taşı
- WikiNavigator'ı sil (veya deprecated işaretle)

### 3. WikipediaScraper - İyileştirmeler
**Sorun**:
- Her seferinde aynı sayfayı tekrar çekiyor (inefficient)
- Timeout sabit (10s)
- No caching

**Çözüm**:
```python
class WikipediaScraper:
    def __init__(self, cache_size=100, timeout=10):
        self._cache = {}  # LRU cache için dict
        self.timeout = timeout

    def get_page_html(self, page_title):
        # Cache'de var mı kontrol et
        if page_title in self._cache:
            return self._cache[page_title]

        # Yoksa çek ve cache'le
        soup = self._fetch_page(page_title)
        self._cache[page_title] = soup
        return soup
```

### 4. Type Hints Eksikliği
**Sorun**: Bazı yerlerde type hints yok

**Çözüm**: Tüm metodlara proper type hints ekle

### 5. Metrics - Dataclass Kullanımı
**Sorun**: Metrics dictionary olarak döndürülüyor, type-safe değil

**Çözüm**:
```python
from dataclasses import dataclass

@dataclass
class SearchMetrics:
    found: bool
    path: list[str]
    steps: int
    pages_explored: int
    time_seconds: float
    max_queue_size: int
```

---

## 🎯 Refactor Adımları

### Adım 1: WikipediaScraper'a Cache Ekle
- LRU cache implementasyonu
- Cache hit/miss statistics
- Clear cache metodu

### Adım 2: PathFinder Helper Metodları
- `_get_page_links()`: Sayfa çek + link al (tek metod)
- `_print_search_header()`: Başlık yazdır
- `_create_result()`: Result dict oluştur
- `_merge_paths()`: Forward + backward path birleştir

### Adım 3: Metrics Dataclass
- SearchMetrics class oluştur
- Tüm return type'ları güncelle

### Adım 4: WikiNavigator'ı Entegre Et
- `random_walk` metodunu PathFinder'a taşı
- WikiNavigator'ı deprecated işaretle

### Adım 5: Clean-up
- Gereksiz comment'leri kaldır
- Docstring'leri güncelle
- Type hints ekle

---

## 📊 Beklenen Kazançlar

✅ **Kod tekrarı**: ~40% azalma (200+ satır → 120 satır)
✅ **Performance**: Cache ile %30-50 hızlanma
✅ **Maintainability**: Helper metodlar ile daha kolay debug
✅ **Type Safety**: Dataclass ile compile-time error detection
✅ **Readability**: Daha temiz, daha anlaşılır kod

---

## 🚀 Öncelik Sırası

1. **Yüksek Öncelik**: WikipediaScraper cache (büyük performance kazancı)
2. **Orta Öncelik**: PathFinder helper metodları (kod kalitesi)
3. **Düşük Öncelik**: Dataclass ve type hints (nice-to-have)
