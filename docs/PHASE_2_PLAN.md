# 🤖 FAZ 2: SEMANTIC SEARCH - Detaylı Plan

## 🎯 Amaç

**Şu anki durum (BFS):**
- Kör arama: Tüm linkleri eşit görüyor
- Hedefe yakın mı uzak mı bilmiyor
- "Italy" ile "Xyz_Random_Page" arasında fark yok

**Hedef (Semantic Search):**
- Akıllı seçim: Hedefe en yakın link'i seç
- Anlam bazlı karar: "Italy" ve "Pizza" semantically yakın!
- Daha az sayfa tara, daha hızlı bul

---

## 📚 Kullanılacak Teknoloji: Sentence Transformers

### Nedir?

Sentence Transformers, metinleri vector'lere (embedding) çeviren bir kütüphane.

**Basit Açıklama:**
```
"Pizza" → [0.2, 0.8, 0.1, 0.5, ...] (384 boyutlu vector)
"Italy" → [0.3, 0.7, 0.2, 0.4, ...] (384 boyutlu vector)
"Computer" → [0.9, 0.1, 0.8, 0.2, ...] (384 boyutlu vector)

Cosine similarity:
  "Pizza" ↔ "Italy" = 0.85 (çok yakın!)
  "Pizza" ↔ "Computer" = 0.12 (çok uzak)
```

**Neden önemli?**
- Kelimeler arasındaki anlamsal ilişkiyi sayısal olarak ölçebiliyoruz
- "Pizza" ve "Food" yakın, ama "Pizza" ve "Quantum Physics" uzak
- Bu bilgiyle akıllı kararlar verebiliriz

### Model Seçimi:

**`all-MiniLM-L6-v2`** (İlk adım için ideal)
- Boyut: 384 dimensions
- Hızlı: ~10ms per sentence
- Küçük: ~80MB
- Yeterince iyi accuracy

**Alternatifler (ileride):**
- `all-mpnet-base-v2`: Daha iyi ama daha yavaş
- `multi-qa-MiniLM-L6-cos-v1`: Q&A için optimize

---

## 🗺️ Adım Adım Plan

### Adım 2.1: Sentence Transformers Kurulumu (30 dk)

**Yapılacaklar:**

1. **Kütüphane kurulumu:**
```bash
pip install sentence-transformers
```

2. **Embedder sınıfı oluştur** (`src/embedder.py`):
```python
from sentence_transformers import SentenceTransformer
import numpy as np

class WikiEmbedder:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        print(f"🤖 Loading model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        print("✅ Model loaded!")

    def get_embedding(self, text: str) -> np.ndarray:
        """Tek bir text'in embedding'ini al."""
        return self.model.encode(text, convert_to_tensor=False)

    def get_embeddings_batch(self, texts: list[str]) -> np.ndarray:
        """Birden fazla text'in embedding'ini al (batch)."""
        return self.model.encode(texts, convert_to_tensor=False)

    def cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """İki embedding arasındaki cosine similarity."""
        return np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
```

3. **İlk test:**
```python
embedder = WikiEmbedder()

# Test embeddings
pizza_emb = embedder.get_embedding("Pizza")
italy_emb = embedder.get_embedding("Italy")
computer_emb = embedder.get_embedding("Computer")

# Similarities
print(f"Pizza ↔ Italy: {embedder.cosine_similarity(pizza_emb, italy_emb):.3f}")
# Beklenen: ~0.6-0.8

print(f"Pizza ↔ Computer: {embedder.cosine_similarity(pizza_emb, computer_emb):.3f}")
# Beklenen: ~0.1-0.3
```

**Öğrenilecekler:**
- Embedding nedir?
- Vector space'de semantic meaning
- Cosine similarity hesaplama

---

### Adım 2.2: Semantic Link Scoring (1 saat)

**Yapılacaklar:**

1. **SemanticNavigator sınıfı** (`src/semantic_navigator.py`):

```python
class SemanticNavigator:
    def __init__(self, verbose=True):
        self.scraper = WikipediaScraper(cache_size=256)
        self.embedder = WikiEmbedder()
        self.verbose = verbose

    def greedy_semantic_search(
        self,
        start: str,
        target: str,
        max_steps: int = 10
    ) -> SearchResult:
        """
        Greedy Semantic Search:
        Her adımda en yüksek semantic similarity'ye sahip link'i seç.
        """
        current_page = start
        path = [start]
        visited = {start}

        # Target embedding'i önceden hesapla (bir kere)
        target_emb = self.embedder.get_embedding(target)

        for step in range(max_steps):
            # Mevcut sayfanın linklerini al
            soup = self.scraper.get_page_html(current_page)
            links = self.scraper.get_wiki_links(soup)

            # Ziyaret edilmemiş linkleri filtrele
            unvisited_links = [link for link in links if link not in visited]

            if not unvisited_links:
                break

            # AKILLI SEÇİM: En yüksek similarity'ye sahip link
            best_link = self._select_best_link(unvisited_links, target_emb)

            # Seçilen linke git
            visited.add(best_link)
            path.append(best_link)
            current_page = best_link

            if self.verbose:
                print(f"Adım {step+1}: {current_page}")

            # Hedefe ulaştık mı?
            if current_page == target:
                return SearchResult(found=True, path=path, ...)

        return SearchResult(found=False, path=path, ...)

    def _select_best_link(
        self,
        links: list[str],
        target_emb: np.ndarray
    ) -> str:
        """
        Linkler arasından en yüksek similarity'ye sahip olanı seç.
        """
        # Tüm linklerin embedding'lerini al (batch olarak hızlı)
        link_embeddings = self.embedder.get_embeddings_batch(links)

        # Her link için similarity hesapla
        similarities = []
        for link_emb in link_embeddings:
            sim = self.embedder.cosine_similarity(link_emb, target_emb)
            similarities.append(sim)

        # En yüksek similarity'ye sahip link'i seç
        best_idx = np.argmax(similarities)
        best_link = links[best_idx]
        best_score = similarities[best_idx]

        if self.verbose:
            print(f"  → {best_link} (similarity: {best_score:.3f})")

        return best_link
```

2. **Test senaryosu:**
```python
# Test: Potato → Pizza
navigator = SemanticNavigator(verbose=True)
result = navigator.greedy_semantic_search(
    start="Potato",
    target="Pizza",
    max_steps=10
)

# Beklenen path (tahmin):
# Potato → Food → Italian_cuisine → Pizza
# (Semantic olarak mantıklı bir path!)
```

**Beklenen Davranış:**
- Her adımda en "anlamlı" link seçilecek
- Random yerine semantically yakın sayfalar
- Daha direkt path bulabilir

**Potansiyel Sorunlar:**
- Greedy her zaman optimal değil (local minima)
- Bazı durumlarda döngüye girebilir
- Hedefe yakın ama direkt link yok ise takılabilir

**Öğrenilecekler:**
- Greedy search algoritması
- Batch embedding (performance için önemli)
- Semantic similarity scoring

---

### Adım 2.3: Beam Search - Çoklu Path Exploration (1.5 saat)

**Sorun:**
Greedy search sadece 1 yol deniyor. Ya o yol막막 막히면?

**Çözüm:**
Beam search - En iyi **k** link'i paralel explore et!

**Nasıl çalışır:**

```
Başlangıç: Potato

Seviye 1: En iyi 3 link seç (beam_width=3)
  - Food (0.85 similarity)
  - Vegetable (0.82 similarity)
  - Plant (0.65 similarity)

Seviye 2: Her birinden en iyi 3 link seç
  Food →
    - Italian_cuisine (0.90)
    - Recipe (0.75)
    - Nutrition (0.68)

  Vegetable →
    - Tomato (0.82)
    - Salad (0.78)
    - Cooking (0.72)

  Plant →
    - Agriculture (0.60)
    - Crop (0.55)
    - ...

  → Toplam 9 path var ama sadece en iyi 3'ünü tut
    1. Food → Italian_cuisine (total score: 0.875)
    2. Vegetable → Tomato (total score: 0.820)
    3. Food → Recipe (total score: 0.800)

Seviye 3: Devam et...
```

**Kod:**
```python
class SemanticNavigator:
    def beam_search(
        self,
        start: str,
        target: str,
        beam_width: int = 3,
        max_depth: int = 6
    ) -> SearchResult:
        """
        Beam Search: En iyi k path'i paralel explore et.
        """
        target_emb = self.embedder.get_embedding(target)

        # Beam: [(current_page, path, cumulative_score), ...]
        beam = [(start, [start], 0.0)]
        visited = {start}

        for depth in range(max_depth):
            candidates = []

            # Her beam element için linkler expand et
            for current_page, path, score in beam:
                soup = self.scraper.get_page_html(current_page)
                links = self.scraper.get_wiki_links(soup)

                # Unvisited links
                unvisited = [l for l in links if l not in visited]

                # Link scores hesapla
                link_scores = self._score_links(unvisited, target_emb)

                for link, link_score in link_scores:
                    if link == target:
                        # BULUNDU!
                        return SearchResult(
                            found=True,
                            path=path + [link],
                            ...
                        )

                    # Candidate ekle
                    new_path = path + [link]
                    new_score = (score * depth + link_score) / (depth + 1)  # Avg
                    candidates.append((link, new_path, new_score))
                    visited.add(link)

            # En iyi beam_width tanesini seç
            candidates.sort(key=lambda x: x[2], reverse=True)
            beam = candidates[:beam_width]

            if not beam:
                break

        # Bulunamadı
        return SearchResult(found=False, path=[], ...)
```

**Avantajlar:**
- Greedy'den daha robust
- Local minima'ya takılmaz (alternatif pathler)
- Success rate daha yüksek

**Dezavantajlar:**
- Daha fazla sayfa tara (beam_width × adım)
- Daha yavaş (ama yine de BFS'den hızlı olabilir)

**Öğrenilecekler:**
- Beam search algoritması
- Trade-off: exploration vs exploitation
- Score aggregation (ortalama vs toplam)

---

### Adım 2.4: Performance Karşılaştırması (30 dk)

**Test Senaryoları:**

```python
tests = [
    ("Potato", "Pizza"),
    ("Albert_Einstein", "Quantum_mechanics"),
    ("Python_(programming_language)", "Machine_learning"),
    ("Basketball", "Michael_Jordan"),
]

algorithms = [
    ("Random Walk", random_walk),
    ("BFS", bfs_search),
    ("Bidirectional BFS", bidirectional_bfs),
    ("Greedy Semantic", greedy_semantic_search),
    ("Beam Search (k=3)", beam_search),
]
```

**Karşılaştırma Metrikleri:**

| Algoritma | Adım | Sayfa Tarandı | Süre | Success Rate |
|-----------|------|---------------|------|--------------|
| Random Walk | ? | ? | ? | %? |
| BFS | 2 | 21 | 9.5s | %100 |
| Bidirectional | 2 | 2 | 1.5s | %100 |
| Greedy Semantic | ? | ? | ? | %? |
| Beam Search | ? | ? | ? | %? |

**Beklenen Sonuçlar:**

**Greedy Semantic:**
- Adım sayısı: BFS ile aynı veya daha az
- Sayfa tarandı: Çok daha az (her adımda 1 sayfa)
- Süre: Embedding overhead var ama az sayfa = hızlı
- Success rate: %80-90 (greedy takılabilir)

**Beam Search:**
- Adım sayısı: BFS ile aynı
- Sayfa tarandı: Greedy'den fazla ama BFS'den az
- Süre: Orta (embedding + biraz fazla sayfa)
- Success rate: %95-100 (robust)

**Öğrenilecekler:**
- Hangi algoritma ne zaman iyi?
- Speed vs Accuracy trade-off
- Embedding overhead vs network overhead

---

## 🧪 Gerçek Hayat Örneği: Potato → Pizza

### Şu Anki BFS:
```
Potato → [534 link'e bak]
  → United_States bulundu
    → United_States → [1000+ link'e bak]
      → Pizza bulunamadı
  → Food bulundu
    → Food → [500+ link'e bak]
      → Italian_cuisine bulundu
        → Italian_cuisine → [300+ link'e bak]
          → Pizza bulundu! ✅

Toplam: ~50+ sayfa tarandı
```

### Semantic Search (Greedy):
```
Potato → [534 link'in embedding'ini hesapla]
  Semantic scores:
    - Food: 0.85 ← EN YÜKSEK! Bunu seç
    - United_States: 0.45
    - History: 0.30
    - ...

Food → [500 link'in embedding'ini hesapla]
  Semantic scores:
    - Italian_cuisine: 0.90 ← EN YÜKSEK! Bunu seç
    - Recipe: 0.75
    - Nutrition: 0.68

Italian_cuisine → [300 link'in embedding'ini hesapla]
  Semantic scores:
    - Pizza: 0.95 ← HEDEF! Bulundu! ✅

Toplam: 3 sayfa tarandı
Path: Potato → Food → Italian_cuisine → Pizza
```

**Kazanç:**
- 50 sayfa → 3 sayfa (%94 azalma!)
- Semantically mantıklı path
- Daha tahmin edilebilir

---

## 💾 Cache'in Önemi (Faz 2'de)

### Embedding Cache:

```python
class WikiEmbedder:
    def __init__(self):
        self.model = SentenceTransformer(...)
        self.embedding_cache = {}  # {text: embedding}

    def get_embedding(self, text: str):
        # Cache hit?
        if text in self.embedding_cache:
            return self.embedding_cache[text]

        # Cache miss: Hesapla ve cache'le
        embedding = self.model.encode(text)
        self.embedding_cache[text] = embedding
        return embedding
```

**Neden önemli?**
- Embedding hesaplama: ~10ms
- Beam search'te aynı linkler tekrar görülebilir
- Cache ile %50-70 hızlanma

---

## 📊 Faz 2 Sonunda Beklentiler

### Başarı Metrikleri:

**Greedy Semantic:**
- ✅ Success rate: %80-90
- ✅ Adım sayısı: BFS ile aynı veya daha iyi
- ✅ Taranan sayfa: %90+ azalma
- ✅ Semantically meaningful paths

**Beam Search:**
- ✅ Success rate: %95-100
- ✅ Robust (greedy'nin sorunlarını çözer)
- ✅ Taranan sayfa: %80+ azalma
- ✅ Configurable (beam_width trade-off)

### Öğrenilecek Konular:

1. **Machine Learning Basics:**
   - Embeddings (vector representations)
   - Cosine similarity
   - Vector space models

2. **Algoritma:**
   - Greedy search
   - Beam search
   - Heuristic functions

3. **Performance Optimization:**
   - Batch processing
   - Embedding cache
   - Trade-off analysis

4. **Python:**
   - NumPy operations
   - Sentence Transformers kütüphanesi
   - Efficient data structures

---

## 🚧 Potansiyel Zorluklar

### 1. Embedding Quality
**Sorun:** "Pizza" ve "Italy" arasında semantic link olmayabilir.
**Çözüm:** Link text + sayfa context kullan (sadece sayfa ismi değil).

### 2. Greedy Takılması
**Sorun:** Her zaman en iyi path'i bulamayabilir.
**Çözüm:** Beam search veya epsilon-greedy (bazen random seç).

### 3. Performance
**Sorun:** 534 link için 534 embedding hesapla = yavaş.
**Çözüm:** Batch processing + cache + GPU (ileride).

### 4. Model Boyutu
**Sorun:** 80MB model memory'de.
**Çözüm:** Model bir kere yüklenir, problem değil.

---

## 📝 Faz 2 Checklist

### Adım 2.1: Setup (✅ Hazır başlayacağız)
- [ ] sentence-transformers kurulumu
- [ ] WikiEmbedder class
- [ ] İlk embedding testleri
- [ ] Cosine similarity testleri

### Adım 2.2: Greedy Search
- [ ] SemanticNavigator class
- [ ] greedy_semantic_search metodu
- [ ] Link scoring implementasyonu
- [ ] Test senaryoları

### Adım 2.3: Beam Search
- [ ] beam_search metodu
- [ ] Multiple path tracking
- [ ] Score aggregation
- [ ] Test senaryoları

### Adım 2.4: Evaluation
- [ ] Karşılaştırma test suite
- [ ] Performance metrics
- [ ] Success rate analizi
- [ ] PROGRESS_LOG.md güncelleme

---

## 🎯 İlk Kodlama Sessiyonunda Yapılacaklar

1. **Kurulum (5 dk):**
   ```bash
   pip install sentence-transformers
   ```

2. **WikiEmbedder oluştur (15 dk):**
   - Model loading
   - get_embedding metodu
   - cosine_similarity metodu

3. **İlk test (10 dk):**
   ```python
   # Gerçek örnek
   embedder = WikiEmbedder()
   pizza_emb = embedder.get_embedding("Pizza")
   italy_emb = embedder.get_embedding("Italy")
   print(f"Similarity: {embedder.cosine_similarity(pizza_emb, italy_emb)}")
   # Sonuç ne çıkacak? Görelim! 🎯
   ```

**Toplam süre:** ~30 dakika
**Çıktı:** Embedding sistemi çalışır halde!

---

## 💡 Önemli Notlar

1. **İlerleme sırası önemli:** Önce greedy, sonra beam search
2. **Her adımı test et:** Çalışmayan kodu bir sonraki adıma taşıma
3. **PROGRESS_LOG.md'yi güncelle:** Her adım sonrası sonuçları kaydet
4. **Embedding'leri anla:** İlk adım en önemli (temeli oluşturur)

---

## 🚀 Faz 2 Sonrası: Faz 3 Preview

**Faz 3: Claude API Integration**
- Claude'a linkleri göster
- "Hangisi Pizza'ya götürür?" diye sor
- Reasoning + Semantic birlikte!

**Beklenen sonuç:**
- %100 success rate
- Optimal paths
- Açıklama: "Italy'yi seçtim çünkü Pizza İtalyan yemeği"

Ama önce Faz 2! 🎯
