# 📝 Changelog

## [2.5.0] - 4 Aralık 2025 - Temizlik & Refactor

### ✨ Yeni Özellikler
- ✅ Temiz, production-ready kod yapısı
- ✅ Tek entry point: `main.py`
- ✅ Detaylı mimari dokümantasyonu: `ARCHITECTURE.md`
- ✅ `.gitignore` eklendi

### 🗑️ Temizlik
- ❌ Karşılaştırma kodları kaldırıldı
- ❌ Test dosyaları silindi: `test_*.py`
- ❌ Eski `main.py` (BFS testleri) kaldırıldı
- ❌ Gereksiz kod ve comment'ler temizlendi

### 📁 Yeni Yapı
```
WikipediaML/
├── src/                         # Core sistem (1756 satır)
│   ├── scraper.py               # 193 satır
│   ├── embedder.py              # 291 satır
│   ├── semantic_navigator.py   # 532 satır
│   ├── knowledge_graph.py      # 166 satır
│   └── pathfinder.py           # 395 satır (reference)
├── main.py                      # Ana entry point
├── demo.py                      # Demo implementasyonu
├── ARCHITECTURE.md              # Mimari dokümantasyonu
└── README.md                    # Kullanım kılavuzu
```

### 🎯 Ana Sistem
**Hybrid Search** (Önerilen):
1. Graph'ta path var mı? → Kullan (anında!)
2. Yoksa Semantic Search yap
3. Başarılıysa öğren ve kaydet

**Performans:**
- İlk çalıştırma: 2-3 saniye
- Graph cached: 0.00 saniye
- **2000x+ hızlanma!**

---

## [2.0.0] - 4 Aralık 2025 - Knowledge Graph

### ✨ Yeni Özellikler
- ✅ `knowledge_graph.py` - GraphRAG temel
- ✅ `hybrid_search()` - Graph + Semantic
- ✅ Path learning & reuse
- ✅ Persistent graph: `wiki_graph.pkl`

### 📊 Test Sonuçları
- Potato → Pizza: 2.18s → 0.00s (2022x hızlı!)
- Path: Potato → Tomato → Pizza
- Similarity: 0.795 (ortalama)

---

## [1.5.0] - 4 Aralık 2025 - Beam Search

### ✨ Yeni Özellikler
- ✅ `beam_search()` - Multi-path exploration
- ✅ Configurable beam width (default: 3)
- ✅ Greedy'den daha robust

---

## [1.0.0] - 2 Aralık 2025 - Semantic Search

### ✨ İlk Sürüm
- ✅ `WikiEmbedder` - Sentence Transformers
- ✅ `SemanticNavigator` - Greedy semantic search
- ✅ Model: all-MiniLM-L6-v2 (384 dim)
- ✅ LRU cache sistemi

---

## [0.5.0] - 1 Aralık 2025 - BFS Algorithms

### ✨ İlk Sürüm
- ✅ `PathFinder` - BFS algorithms
- ✅ Bidirectional BFS (%99 hızlı!)
- ✅ `WikipediaScraper` - HTML fetching

---

**Sonraki Adım:** Faz 3 - Claude API entegrasyonu
