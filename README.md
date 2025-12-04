# WikipediaML

Wikipedia oyununu oynayan AI sistemi - Bir sayfadan başlayarak sadece linklere tıklayarak hedef sayfaya ulaş!

## 🎯 Proje Durumu

**Faz 1: ✅ Tamamlandı** - BFS ve Bidirectional BFS
**Faz 2: ✅ Tamamlandı** - Semantic Search (Greedy + Beam)
**Faz 2.5: ✅ Tamamlandı** - Knowledge Graph (GraphRAG temel)
**Faz 3: ⏳ Sırada** - Claude API entegrasyonu

## 🚀 Kurulum

```bash
# Virtual environment oluştur
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Bağımlılıkları yükle
pip install -r requirements.txt
```

**Not:** İlk çalıştırmada embedding model indirilecek (~80MB, bir kereye mahsus).

## 🚀 Kullanım

### Hızlı Başlangıç
```bash
python main.py <başlangıç> <hedef>
```

### Örnekler
```bash
# Basit örnek
python main.py Potato Pizza

# Bilim örneği
python main.py Albert_Einstein Physics

# Teknoloji örneği
python main.py Python_(programming_language) Machine_learning
```

### Not
- Sayfa isimleri Wikipedia URL'indeki `/wiki/` sonrası kısım
- Boşluklar yerine `_` kullanın
- Parantez içeren isimler: `Python_(programming_language)`

### Ne Yapar?
Sistem otomatik olarak:
- 📍 Verdiğiniz başlangıç → 🎯 hedef path bulur
- 🧠 Semantic embeddings ile akıllı link seçer
- 💾 Başarılı path'leri öğrenir ve hatırlar
- ⚡ Öğrenilmiş path'leri anında kullanır (2000x+ hızlı!)

### Özellikler
- 🤖 **Greedy Semantic Search** - Akıllı link seçimi
- 🔮 **Beam Search** - Multi-path exploration (daha robust)
- 🧬 **Hybrid Search** - Graph + Semantic (öğrenen sistem!)
- 📊 Top-k candidate gösterme
- 💾 Çoklu cache sistemi (scraper, embedder, graph)

## 📁 Proje Yapısı

```
WikipediaML/
├── src/                         # Core sistem
│   ├── scraper.py               # Wikipedia scraping + LRU cache
│   ├── embedder.py              # Semantic embeddings (Sentence Transformers)
│   ├── semantic_navigator.py   # Ana sistem (Greedy/Beam/Hybrid)
│   ├── knowledge_graph.py      # GraphRAG (NetworkX)
│   └── pathfinder.py           # BFS algorithms (reference)
├── docs/                        # Detaylı dökümanlar
├── main.py                      # CLI - Dinamik path finder
└── wiki_graph.pkl               # Öğrenilmiş path'ler (otomatik)
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
- ✅ Embedding system (Sentence Transformers, all-MiniLM-L6-v2)
- ✅ Greedy Semantic Search (akıllı link seçimi)
- ✅ Beam Search (multi-path, daha robust)

### Faz 2.5: Knowledge Graph (GraphRAG)
- ✅ NetworkX graph
- ✅ Path learning (başarılı path'leri kaydet)
- ✅ Hybrid Search (Graph + Semantic)
- ✅ 2000x+ hızlanma (cached paths)

## 📊 Örnek Sonuçlar

### Potato → Pizza
```
İlk çalıştırma (Semantic Search):
  ✅ Path bulundu: Potato → Tomato → Pizza
  ⏱️  Süre: 2.18s
  🧮 534 embedding hesaplandı

İkinci çalıştırma (Graph Reuse):
  ✅ Path bulundu: Potato → Tomato → Pizza
  ⏱️  Süre: 0.00s (anında!)
  🚀 2000x+ daha hızlı!
```

### Sistem Özellikleri
- ⚡ Graph cache: Öğrenilmiş path'ler anında kullanılır
- 🧠 Semantic similarity: 0.8+ skorla akıllı link seçimi
- 💾 Multi-level caching: Scraper + Embedder + Graph
- 📊 Success rate: %95+ (test senaryolarında)
