# 🌐 Wikipedia PathFinder - Proje Bağlamı

## 🎯 Proje Amacı

Wikipedia oyununu otomatik oynayan bir AI sistemi geliştirmek. 

**Wikipedia Oyunu**: Bir başlangıç sayfasından sadece linklere tıklayarak hedef sayfaya en az adımda ulaşmaya çalışmak.

---

## 🏗️ Proje Mimarisi

### Katmanlar:

```
┌─────────────────────────────────────────┐
│         User Interface Layer            │
│  (main.py, future: Dash web app)        │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│      Navigation & Search Layer          │
│  • SemanticNavigator (beam search)      │
│  • PathFinder (BFS, bidirectional)      │
│  • ClaudeReasoning (AI reasoning)       │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│      Intelligence Layer                 │
│  • Embedder (semantic similarity)       │
│  • LinkFilter (pre-filtering)           │
│  • KnowledgeGraph (path storage)        │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         Data Layer                      │
│  • WikipediaScraper (HTML parsing)      │
│  • Cache (persistent storage)           │
└─────────────────────────────────────────┘
```

---

## 🎓 Öğrenme Yaklaşımı

- **Adım adım ilerleme**: Her fazı detaylıca anlayarak ilerlemek
- **Görselleştirme**: Tüm adımları, hangi sayfaya gidildiğini, neden gidildiğini görmek
- **Açıklayıcı**: Her değişiklik ve eklemenin nedenini anlamak
- **Performance tracking**: Kaç adımda buldu, kaç sayfa taradı, ne kadar sürdü

---

## 🗺️ Genel Yol Haritası

### ✅ Faz 1: Basic Pathfinding (Tamamlandı)
Basit graph search algoritmalarıyla (BFS, Bidirectional BFS) Wikipedia oyununu çözebilir hale getirmek.

**Sonuç**: %99.4 daha az sayfa tarama (Bidirectional BFS)

### ✅ Faz 2: Semantic Search (Tamamlandı)
Sentence transformers ile linkleri semantic similarity'e göre seçmek.

**Sonuç**: %90+ başarı oranı, 3-8s ortalama süre

### ✅ Faz 3: Claude API Entegrasyonu (Tamamlandı)
Claude API ile link seçimi ve reasoning yapabilmek.

**Sonuç**: Yüksek kaliteli reasoning, cost-effective

### ✅ Faz 4: Knowledge Graph (Tamamlandı)
Öğrenilen path'leri ve ilişkileri bir knowledge graph'ta saklamak.

**Sonuç**: %20-30 hızlanma (cached paths için)

### ✅ Faz 5: Performance Optimization (Tamamlandı)
Persistent cache, pre-filtering, hub detection.

**Sonuç**: %70-85 hızlanma, %94 daha az embedding

### 📋 Faz 6: 3D Visualization (Planlandı)
Plotly + Dash ile interaktif 3D görselleştirme.

**Hedef**: Real-time path exploration animation

---

## 🔧 Mevcut Durum

### Tamamlanan Özellikler:

- ✅ **WikipediaScraper**: HTML parsing, link extraction, LRU cache
- ✅ **PathFinder**: BFS, Bidirectional BFS
- ✅ **Embedder**: Sentence transformers, persistent cache
- ✅ **SemanticNavigator**: Beam search, bidirectional semantic search
- ✅ **LinkFilter**: Pre-filtering, hub detection
- ✅ **KnowledgeGraph**: NetworkX graph, path storage
- ✅ **ClaudeReasoning**: Claude API entegrasyonu

### Aktif Özellikler:

- 🔄 **Bidirectional Beam Search**: En iyi algoritma (%95+ başarı)
- 🔄 **Persistent Cache**: %50-70 cache hit rate
- 🔄 **Pre-filtering**: %94 daha az embedding
- 🔄 **Hub Detection**: Popüler sayfaları önceliklendirme

### Planlanan Özellikler:

- 📋 **3D Visualization**: Plotly + Dash web app
- 📋 **Advanced Analytics**: Detaylı metrics ve statistics
- 📋 **Fine-tuned Model**: Custom embedding model

---

## 📊 Performance Metrikleri

### Başarı Oranları:

| Algoritma | Başarı Oranı | Ortalama Adım | Ortalama Süre |
|-----------|--------------|---------------|---------------|
| BFS | %100 | 2-3 | 10-50s |
| Bidirectional BFS | %100 | 2-3 | 1-5s |
| Semantic Greedy | %70 | 3-4 | 2-5s |
| Beam Search | %90 | 2-3 | 3-8s |
| **Bidirectional Beam** | **%95+** | **2-3** | **2-5s** |

### Optimization Kazançları:

- **Bidirectional BFS**: %99.4 daha az sayfa tarama
- **Persistent Cache**: %50-70 cache hit rate
- **Pre-filtering**: %94 daha az embedding
- **Toplam Hızlanma**: %70-85 daha hızlı

---

## 🛠️ Teknoloji Stack

### Core:
- **Python 3.11+**
- **BeautifulSoup4**: HTML parsing
- **Requests**: HTTP client

### Machine Learning:
- **Sentence Transformers**: all-MiniLM-L6-v2 (384-dim embeddings)
- **scikit-learn**: Cosine similarity
- **NumPy**: Numerical operations

### Graph & Storage:
- **NetworkX**: Knowledge graph
- **Pickle**: Cache serialization

### AI:
- **Claude API**: Reasoning (optional)

### Future:
- **Plotly + Dash**: 3D visualization
- **TensorBoard**: Embedding visualization

---

## 📋 İlkeler

- ✅ Her adımda çalışır durumda bir kod olmalı
- ✅ Test edilebilir olmalı
- ✅ Verbose output (hangi kararlar alındığını görmeli)
- ✅ Performance tracking (metrics)
- ✅ Clean code (DRY, type hints, docstrings)
- ✅ Persistent storage (cache, graph)

---

## 🎯 Kullanım

### Basit Kullanım:

```python
from src.semantic_navigator import SemanticNavigator

# Navigator oluştur
navigator = SemanticNavigator(verbose=True, use_graph=True)

# Path bul
result = navigator.bidirectional_beam_search(
    start="Potato",
    target="Pizza",
    beam_width=4,
    max_depth=10
)

# Sonuç
if result.found:
    print(f"Path: {' → '.join(result.path)}")
    print(f"Steps: {result.steps}")
    print(f"Time: {result.time_seconds:.2f}s")
```

### Test:

```bash
# Virtual environment
source venv/bin/activate

# Ana test
python main.py

# Performance test
python test_performance.py
```

---

## 📚 Önemli Dosyalar

### Kod:
- `src/scraper.py`: Wikipedia scraping
- `src/embedder.py`: Semantic embeddings
- `src/link_filter.py`: Pre-filtering
- `src/semantic_navigator.py`: Ana navigation logic
- `src/knowledge_graph.py`: Graph storage
- `src/pathfinder.py`: BFS algorithms
- `src/claude_reasoning.py`: Claude API

### Dokümantasyon:
- `README.md`: Proje overview
- `QUICKSTART.md`: Hızlı başlangıç
- `ARCHITECTURE.md`: Mimari detayları
- `docs/ROADMAP.md`: Detaylı roadmap
- `docs/PROGRESS_LOG.md`: İlerleme kaydı
- `docs/PERFORMANCE_OPTIMIZATION_PLAN.md`: Optimization planı
- `docs/3D_VISUALIZATION_PLAN.md`: Visualization planı
- `docs/PROJECT_CONTEXT.md`: Bu dosya

---

## 🔍 Öğrenilenler

### Algoritmalar:
- ✅ BFS garantili en kısa path'i bulur
- ✅ Bidirectional BFS exponential growth'u yarıya böler
- ✅ Semantic similarity hedefe yakınlığı ölçer
- ✅ Beam search greedy'den daha robust
- ✅ Pre-filtering büyük performance kazancı sağlar

### Wikipedia:
- ✅ Small-world network (6 derece of separation)
- ✅ Hub sayfalar var (United_States, Italy, Europe)
- ✅ Ortalama 500 link per page
- ✅ Popüler sayfalar hızlı kesişme yaratır

### Performance:
- ✅ Cache = bedava performance
- ✅ Pre-filtering > post-filtering
- ✅ Heuristics çok etkili (kelime overlap)
- ✅ Persistent storage önemli

---

## 🚀 Gelecek Planları

### Kısa Vadeli (1-2 hafta):
1. 📋 3D Visualization (Plotly + Dash)
2. 📋 Web dashboard
3. 📋 Advanced metrics

### Orta Vadeli (1-2 ay):
1. 📋 Fine-tuned embedding model
2. 📋 Multi-language support
3. 📋 API endpoint

### Uzun Vadeli (3+ ay):
1. 📋 Reinforcement learning
2. 📋 Mobile app
3. 📋 Competitive leaderboard

---

**Son Güncelleme**: 9 Aralık 2024
**Versiyon**: 3.1.0
**Durum**: Production-ready, optimization tamamlandı
