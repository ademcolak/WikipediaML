# 🎮 WikipediaML - Wikipedia Oyunu Çözücü

Wikipedia'da X sayfasından Y sayfasına sadece linklere tıklayarak ulaşma oyununu oynayan akıllı sistem.

## 🎯 Hedef

**Wikipedia oyununu mükemmel oynayan, öğrene öğrene gelişen bir AI sistemi.**

## ✨ Nasıl Çalışır?

### 3 Katmanlı Akıllı Sistem (10K+ Edge için)

```
1. KNOWLEDGE GRAPH (Hafıza)
   ├─> Daha önce bu yolu gördüm mü?
   ├─> Evet → Anında kullan! (0.00s, %100 doğru)
   └─> Hayır → Katman 2'ye git

2. EMBEDDING FILTER (Akıllı Filtreleme)
   ├─> Semantic similarity ile top-5 link seç
   ├─> 1-2 saniye
   ├─> %60-70 doğruluk
   └─> LLM'e gönder

3. LLM SELECTION (En Akıllı Seçim)
   ├─> Claude API ile en iyi link'i seç
   ├─> 3-5 saniye
   ├─> %70-80+ doğruluk
   └─> ~$0.02 per query

Sonuç: Her başarılı yol → KG'ye eklenir
       Sistem sürekli öğrenir ve iyileşir!
```

### Klasik Sistem (<10K Edge)

```
1. KNOWLEDGE GRAPH (Hafıza)
   └─> Öğrenilmiş yollar (anında!)

2. SEMANTIC SIMILARITY (Akıllı Arama)
   ├─> Cosine similarity ile link seçimi
   ├─> Her zaman çalışır
   └─> %95+ başarı oranı
```

## 🚀 Hızlı Başlangıç

### Kurulum

```bash
# Projeyi klonla
git clone <repo-url>
cd WikipediaML

# Virtual environment oluştur
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Bağımlılıkları kur
pip install -r requirements.txt
```

### Kullanım

```bash
# Basit kullanım
python main.py Potato Pizza

# Async mode (3x daha hızlı)
python main.py Potato Pizza --async

# Hybrid Navigator (10K+ edge için)
python main.py Italy Rome --hybrid

# Hybrid + LLM (en yüksek doğruluk)
python main.py Italy Rome --hybrid --llm
```

### Örnekler

```bash
# Kolay yollar
python main.py Albert_Einstein Physics --async
python main.py Python_(programming_language) Machine_learning --async

# Orta zorluk
python main.py Potato Pizza --async
python main.py Italy Rome --hybrid

# Zor yollar (Hybrid + LLM önerilir)
python main.py Porsche Serik_Akhmetov_Government --hybrid --llm
```

## 📊 Performans

| Mod | Hız | Doğruluk | Maliyet | Kullanım |
|-----|-----|----------|---------|----------|
| **Sync** | 1-2s | 95% | Ücretsiz | Basit yollar |
| **Async** | 0.5-1s | 95% | Ücretsiz | Çoğu yol |
| **Hybrid** | 2-3s | 70-80% | Ücretsiz | 10K+ edge |
| **Hybrid+LLM** | 4-5s | 75-85% | ~$0.02/query | Zor yollar |
| **KG Cache** | 0.00s | 100% | Ücretsiz | Öğrenilmiş yollar |

### Speedup & Accuracy
- **Async:** 3x daha hızlı
- **KG Cache:** 2000x+ daha hızlı (anında!)
- **Hybrid Navigator:** %70-80 doğruluk (10K+ edge'de)
- **Hybrid + LLM:** %75-85 doğruluk (en yüksek)

## 🧠 Sistem Mimarisi

```
main.py
    ↓
SemanticNavigator (Orchestrator)
    ├── KnowledgeGraph (Hafıza)
    │   └── Öğrenilmiş yollar (anında sonuç)
    │
    ├── Embedder (Semantic)
    │   ├── Sentence transformers
    │   └── Cosine similarity
    │
    ├── AsyncScraper (Hız)
    │   └── Parallel page fetching
    │
    └── LinkFilter (Optimizasyon)
        └── Smart pre-filtering
```

## 📁 Proje Yapısı

```
WikipediaML/
├── main.py                          # Ana uygulama
├── requirements.txt                 # Bağımlılıklar
├── .env.example                     # Environment template
│
├── src/                             # Core modüller
│   ├── semantic_navigator.py        # Ana orchestrator
│   ├── knowledge_graph.py           # Hafıza sistemi
│   ├── embedder.py                  # Semantic similarity
│   ├── scraper.py                   # Wikipedia fetcher
│   ├── async_scraper.py             # Async fetcher
│   └── link_filter.py               # Link filtering
│
├── cache/                           # KG ve cache dosyaları
├── data/                            # Veri dosyaları
│
├── auto_train_parallel.py           # Paralel eğitim sistemi
├── merge_graphs.py                  # Graph birleştirme
├── start_parallel.sh                # Otomatik paralel başlatma
└── PARALLEL_TRAINING.md             # Paralel eğitim rehberi
```

## 📈 Sistem Nasıl Öğrenir?

### 1. İlk Çalıştırma
```
Potato → Pizza
├─> Semantic similarity kullan
├─> 2 adımda bul: Potato → Tomato → Pizza
└─> Süre: 1.5s
```

### 2. Yolu Öğren
```
Knowledge Graph'a ekle:
- Potato → Tomato (weight: 1)
- Tomato → Pizza (weight: 1)
```

### 3. İkinci Çalıştırma
```
Potato → Pizza
├─> KG'de var mı? EVET!
├─> Potato → Tomato → Pizza
└─> Süre: 0.00s (ANINDA!)
```

## 🎯 Özellikler

### ✅ Mevcut Özellikler:
- ✅ Knowledge Graph (öğrenme ve hafıza)
- ✅ Semantic Similarity (akıllı link seçimi)
- ✅ **Hybrid Navigator (KG + Embedding + LLM)** 🆕
- ✅ Async Processing (3x hızlı)
- ✅ Paralel Eğitim (4-5x hızlı öğrenme)
- ✅ Cache System (performans)
- ✅ Bidirectional Search (daha hızlı)
- ✅ Beam Search (multi-path)

### 🎓 Teknolojiler:
- **Python 3.11+**
- **Sentence Transformers** - Semantic embeddings
- **NetworkX** - Knowledge graph
- **aiohttp** - Async HTTP
- **BeautifulSoup** - HTML parsing

## 📊 İstatistikler

- **Core Modüller:** 6 dosya
- **Toplam Kod:** ~3,700 satır
- **Cache Layers:** 3 katman
- **Öğrenme:** Sürekli

## 🚀 Hızlı Komutlar

### Temel Kullanım
```bash
# Basit arama
python main.py Potato Pizza --async

# Farklı örnekler
python main.py Albert_Einstein Physics --async
python main.py Italy Rome --async
python main.py Computer Science --async
```

### Paralel Eğitim (Yeni!) 🆕
```bash
# Otomatik başlatma (5 worker)
./start_parallel.sh

# Manuel başlatma (5 farklı terminal)
python auto_train_parallel.py --worker-id 1 --count 100
python auto_train_parallel.py --worker-id 2 --count 100
python auto_train_parallel.py --worker-id 3 --count 100
python auto_train_parallel.py --worker-id 4 --count 100
python auto_train_parallel.py --worker-id 5 --count 100

# Birleştirme
python merge_graphs.py

# Detaylı rehber
cat PARALLEL_TRAINING.md
```

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing`)
3. Commit yapın (`git commit -m 'Add amazing feature'`)
4. Push yapın (`git push origin feature/amazing`)
5. Pull Request açın

## 📄 Lisans

MIT License

## 🎓 Öğrenme Kaynakları

Bu proje şunları gösterir:
- Semantic search (sentence transformers)
- Knowledge graphs (NetworkX)
- Async programming (asyncio)
- Self-supervised learning
- Production systems

---

**Versiyon:** 5.2.0 (Hybrid Navigator)
**Durum:** Aktif Geliştirme
**Son Güncelleme:** 18 Aralık 2024

**Hedef:** Wikipedia oyununu mükemmel oynayan, sürekli öğrenen AI sistemi 🎮🧠

---

## 🆕 Yenilikler (v5.2.0)

### Hybrid Navigator Sistemi (10K+ Edge için)
- ✅ 3 katmanlı navigasyon (KG → Embedding → LLM)
- ✅ %70-80 doğruluk hedefi
- ✅ Claude API entegrasyonu (opsiyonel)
- ✅ Maliyet kontrolü
- ✅ Detaylı dokümantasyon ([`HYBRID_SETUP.md`](HYBRID_SETUP.md))

**Hızlı Başlangıç:**
```bash
# Hybrid mode (Embedding only)
python main.py Italy Rome --hybrid

# Hybrid + LLM (en yüksek doğruluk)
python main.py Italy Rome --hybrid --llm

# Eğitim (Hybrid Navigator ile)
python train.py --strategy strategic --workers 2 --iterations 100 --use-hybrid --use-llm
```

### Önceki Özellikler (v5.1.0)
- ✅ Paralel Eğitim Sistemi
- ✅ 4-5x daha hızlı öğrenme
- ✅ Process-safe graph yönetimi
