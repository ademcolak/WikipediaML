# 🎮 WikipediaML - Wikipedia Oyunu Çözücü

Wikipedia'da X sayfasından Y sayfasına sadece linklere tıklayarak ulaşma oyununu oynayan akıllı sistem.

## 🎯 Hedef

**Wikipedia oyununu mükemmel oynayan, öğrene öğrene gelişen bir AI sistemi.**

## ✨ Nasıl Çalışır?

### 2 Katmanlı Akıllı Sistem

```
1. KNOWLEDGE GRAPH (Hafıza)
   ├─> Daha önce bu yolu gördüm mü?
   ├─> Evet → Anında kullan! (0.00s, %100 doğru)
   └─> Hayır → Katman 2'ye git

2. SEMANTIC SIMILARITY (Akıllı Arama)
   ├─> Cosine similarity ile link seçimi
   ├─> Her zaman çalışır
   ├─> %95+ başarı oranı
   └─> Baseline performance

Sonuç: Her başarılı yol → KG'ye eklenir
       Sistem sürekli öğrenir ve iyileşir!
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

# Async mode (3x daha hızlı - ÖNERİLİR!)
python main.py Potato Pizza --async
```

### Örnekler

```bash
# Kolay yollar
python main.py Albert_Einstein Physics --async
python main.py Python_(programming_language) Machine_learning --async

# Orta zorluk
python main.py Potato Pizza --async
python main.py Italy Rome --async

# Zor yollar
python main.py Porsche Serik_Akhmetov_Government --async
```

## 📊 Performans

| Mod | Hız | Doğruluk | Kullanım |
|-----|-----|----------|----------|
| **Sync** | 1-2s | 95% | Basit yollar |
| **Async** | 0.5-1s | 95% | Çoğu yol (önerilen) |
| **KG Cache** | 0.00s | 100% | Öğrenilmiş yollar |

### Speedup
- **Async:** 3x daha hızlı
- **KG Cache:** 2000x+ daha hızlı (anında!)

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
└── data/                            # Veri dosyaları
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
- ✅ Async Processing (3x hızlı)
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

```bash
# Basit arama
python main.py Potato Pizza --async

# Farklı örnekler
python main.py Albert_Einstein Physics --async
python main.py Italy Rome --async
python main.py Computer Science --async
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

**Versiyon:** 5.0.0 (Clean)  
**Durum:** Aktif Geliştirme  
**Son Güncelleme:** 15 Aralık 2024

**Hedef:** Wikipedia oyununu mükemmel oynayan, sürekli öğrenen AI sistemi 🎮🧠
