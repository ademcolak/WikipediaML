# WikipediaML

Wikipedia oyununu oynayan AI sistemi - Bir sayfadan başlayarak sadece linklere tıklayarak hedef sayfaya ulaş!

## 🎯 Proje Durumu

**Faz 1: ✅ Tamamlandı** - BFS ve Bidirectional BFS
**Faz 2: 🔄 Devam Ediyor** - Semantic Search (Embedding-based)

## 🚀 Kurulum

```bash
# Virtual environment oluştur
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Bağımlılıkları yükle
pip install -r requirements.txt
```

**Not:** İlk çalıştırmada embedding model indirilecek (~80MB, bir kereye mahsus).

## 🧪 Testler

### Faz 1: BFS Testleri
```bash
python main.py
```

### Faz 2: Embedding Testleri
```bash
python test_embeddings.py
```

Bu test:
- ✅ Embedding sisteminin çalıştığını doğrular
- ✅ Semantic similarity'i test eder
- ✅ Gerçek Wikipedia path senaryosu simüle eder
- ✅ Cache performance'ı ölçer

### Faz 2.2: Semantic Search (GERÇEK Wikipedia!) 🎯
```bash
# Tüm test senaryoları
python test_semantic_search.py

# Tek senaryo (detaylı)
python test_semantic_search.py single
```

Bu test:
- 🤖 Greedy Semantic Search (akıllı link seçimi)
- 📊 Top 5 candidate'leri gösterir
- 🎯 Gerçek Wikipedia'da path bulur
- 💾 Cache statistics

## 📁 Proje Yapısı

```
WikipediaML/
├── src/
│   ├── scraper.py      # Wikipedia HTML fetching + caching
│   ├── pathfinder.py   # BFS algorithms
│   └── embedder.py     # Semantic embeddings (NEW!)
├── docs/               # Tüm dökümanlar
├── main.py            # BFS testleri
└── test_embeddings.py # Embedding testleri (NEW!)
```

## 📚 Dökümanlar

Tüm detaylı dökümanlar `docs/` klasöründe:
- **PROGRESS_LOG.md** - Her adımın detaylı kaydı
- **PHASE_2_PLAN.md** - Faz 2 detaylı planı
- **ROADMAP.md** - 5 fazlı genel yol haritası
- **BIDIRECTIONAL_BFS_EXPLAINED.md** - Bidirectional BFS açıklaması

## 🎯 Algoritmalar

### Faz 1: Graph Search
- ✅ BFS (Breadth-First Search)
- ✅ Bidirectional BFS (%99 daha hızlı!)

### Faz 2: Semantic Search
- ✅ Embedding system (Sentence Transformers)
- ✅ Greedy Semantic Search (TAMAMLANDI!)
- 🔄 Beam Search (sırada)

## 📊 Sonuçlar (Faz 1)

Einstein → Pizza testi:
- **BFS**: 356 sayfa, 217 saniye
- **Bidirectional BFS**: 2 sayfa, 1.5 saniye ⚡
- **Kazanç**: %99.4 daha az sayfa tarama!
