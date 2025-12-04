# 🏗️ WikipediaML - Sistem Mimarisi

## 📋 Genel Bakış

WikipediaML, Wikipedia sayfaları arasında akıllı path bulma sistemidir. Üç ana teknoloji kullanır:

1. **Semantic Embeddings** - Anlam bazlı link seçimi
2. **Knowledge Graph** - Öğrenme ve hatırlama (GraphRAG)
3. **Beam Search** - Multi-path exploration

---

## 🧩 Sistem Bileşenleri

### 1. Core Modüller (`src/`)

#### `scraper.py` - Wikipedia Scraping
```python
WikipediaScraper
├── get_page_html()      # HTML çekme + LRU cache
├── get_wiki_links()     # Link extraction
└── get_cache_stats()    # Cache istatistikleri
```

**Özellikler:**
- LRU cache (128 sayfa default)
- Rate limiting desteği
- BeautifulSoup HTML parsing
- Link filtreleme (Special:, File:, etc. hariç)

---

#### `embedder.py` - Semantic Embeddings
```python
WikiEmbedder
├── get_embedding()              # Tek text → vector
├── get_embeddings_batch()       # Çoklu text → vectors (hızlı)
├── cosine_similarity()          # İki vector arası benzerlik
└── get_most_similar()           # En benzer text'leri bul
```

**Model:**
- Sentence Transformers: `all-MiniLM-L6-v2`
- Dimension: 384
- Size: ~80MB
- Speed: ~10ms per sentence

**Cache:**
- LRU cache (512 embedding default)
- Batch processing optimize
- Hit rate tracking

---

#### `knowledge_graph.py` - GraphRAG
```python
WikiKnowledgeGraph
├── add_path()           # Başarılı path'leri kaydet
├── find_path()          # Graph'ta path ara
├── get_next_nodes()     # Bir node'dan nereye gidilir?
├── save()               # Pickle'a kaydet
└── get_stats()          # Graph istatistikleri
```

**Teknoloji:**
- NetworkX (directed graph)
- Edge weights (kaç kez kullanıldı)
- Persistence: `wiki_graph.pkl`

**Öğrenme:**
```
1. Path bulundu: A → B → C
2. Graph'a ekle: A→B (weight=1), B→C (weight=1)
3. Sonraki aramada: A → C isteniyor?
4. Graph'ta path var! A→B→C kullan (anında!)
```

---

#### `semantic_navigator.py` - Ana Sistem
```python
SemanticNavigator
├── greedy_semantic_search()     # En iyi linki seç (hızlı)
├── beam_search()                # Top-k linkleri paralel dene
└── hybrid_search()              # Graph + Semantic (ÖNERİLEN!)
```

**Hybrid Search Akışı:**
```
1. Graph'ta path var mı?
   ├── Evet → Kullan (0.00s, anında!)
   └── Hayır → Semantic search kullan
2. Semantic search yap
3. Başarılıysa graph'a kaydet
4. Sonraki aramada graph'tan kullan
```

**Greedy vs Beam:**
- **Greedy**: Sadece en iyi link (hızlı, basit)
- **Beam (width=3)**: Top-3 link'i paralel dene (robust, biraz yavaş)

---

#### `pathfinder.py` - BFS Algorithms (Reference)
```python
PathFinder
├── bfs_search()                 # Klasik BFS
└── bidirectional_bfs_search()   # İki yönlü BFS (%99 hızlı)
```

**Not:** Artık aktif kullanılmıyor, referans ve benchmark için tutuluyor.

---

## 🔄 Veri Akışı

### Örnek: "Potato → Pizza"

```
1. USER INPUT
   └─> start="Potato", target="Pizza"

2. HYBRID SEARCH
   ├─> Graph kontrol et
   │   └─> Path yok
   │
   └─> Greedy Semantic Search
       │
       ├─> Step 1: Potato sayfası
       │   ├─> 534 link bulundu
       │   ├─> Embeddings hesapla (batch)
       │   ├─> Similarity: Tomato (0.589) EN YÜKSEK
       │   └─> Tomato'ya git
       │
       └─> Step 2: Tomato sayfası
           ├─> 446 link bulundu
           ├─> Embeddings hesapla
           ├─> Similarity: Pizza (1.000) HEDEF!
           └─> BULUNDU!

3. GRAPH'A KAYDET
   └─> Potato → Tomato → Pizza (weight=1)

4. SONRAKI ARAMA (aynı path)
   └─> Graph'tan al: 0.00s (2000x+ hızlı!)
```

---

## 💾 Cache Sistemi

### 3 Katmanlı Cache

1. **Scraper Cache**
   - LRU (128 sayfa)
   - Network call azaltır
   - Hit rate: %30-50

2. **Embedder Cache**
   - LRU (512 embedding)
   - Model inference azaltır
   - Hit rate: %60-80

3. **Graph Cache**
   - Persistent (wiki_graph.pkl)
   - Tüm search'ü skip eder
   - Anında sonuç: 0.00s

**Toplam Kazanç:**
- İlk çalıştırma: 2-3 saniye
- Graph cached: 0.00 saniye
- **2000x+ hızlanma!**

---

## 📊 Performance Metrikleri

| Metrik | İlk Çalıştırma | Graph Cached |
|--------|---------------|--------------|
| Süre | 2.18s | 0.00s |
| Network calls | 2 | 0 |
| Embeddings | 534 | 0 |
| Taranan sayfa | 2 | 0 |

---

## 🚀 Kullanım

### CLI Kullanımı (Önerilen)
```bash
# Temel kullanım
python main.py <başlangıç> <hedef>

# Örnekler
python main.py Potato Pizza
python main.py Albert_Einstein Physics
python main.py Python_(programming_language) Machine_learning
```

### Python API
```python
from src.semantic_navigator import SemanticNavigator

nav = SemanticNavigator(verbose=True, use_graph=True)

result = nav.hybrid_search(
    start="Potato",
    target="Pizza",
    max_steps=10
)

print(f"Path: {' → '.join(result.path)}")
print(f"Süre: {result.time_seconds:.2f}s")
print(f"Algoritma: {result.algorithm}")
```

---

## 🔮 Sonraki Adımlar (Faz 3)

### Claude API Entegrasyonu
```
Hybrid Search + Claude Reasoning:

1. Semantic → Top-5 link bul
2. Graph → Bu linkler hakkında ne biliyoruz?
3. Claude → "Hangisi en iyi? Neden?"
   └─> Context: Graph bilgisi + Semantic scores
4. Daha akıllı kararlar!
```

**Örnek Claude Prompt:**
```
Potato sayfasından Pizza'ya gitmek istiyoruz.

Top 5 link:
1. Tomato (similarity: 0.589) - Graph'ta 3 kez başarılı
2. Fat (similarity: 0.468) - Graph'ta yok
3. Staple_food (similarity: 0.446) - 1 kez başarısız

Hangisini seçmeliyiz ve neden?
```

---

## 📚 Teknik Detaylar

### Dependency'ler
```
requests          # HTTP requests
beautifulsoup4    # HTML parsing
sentence-transformers  # Embeddings
torch             # ML backend
numpy             # Vector operations
networkx          # Graph operations
```

### Python Version
- Minimum: Python 3.10+
- Test edildi: Python 3.14

### Dosya Yapısı
```
WikipediaML/
├── src/                 # Core modules (5 dosya, 1756 satır)
├── docs/                # Documentation (6 dosya)
├── main.py              # CLI - Dinamik path finder
├── wiki_graph.pkl       # Learned paths (auto-generated)
└── requirements.txt     # Dependencies
```

---

## 🎯 Tasarım Prensipleri

1. **Modülerlik**: Her component bağımsız
2. **Cache-First**: Maximum performance
3. **Progressive Enhancement**: BFS → Semantic → Graph
4. **Learning**: Her arama sistemin bilgisini artırır
5. **Production-Ready**: Clean code, no test/comparison code

---

**Son Güncelleme:** 4 Aralık 2025
**Versiyon:** 2.5 (GraphRAG)
