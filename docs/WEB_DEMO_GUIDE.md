# 🌐 Web Demo Kullanım Kılavuzu

## 🎯 Genel Bakış

WikipediaML artık **interaktif web arayüzü** ile geliyor! Terminal yerine tarayıcıda görsel olarak Wikipedia oyununu oynayabilir ve AI navigatorlarını test edebilirsiniz.

## 🚀 Hızlı Başlangıç

### 1. Bağımlılıkları Kur

```bash
# Flask ve gerekli paketleri kur
pip install -r requirements.txt
```

### 2. Web Demo'yu Başlat

```bash
# Demo'yu başlat
python web_demo.py

# Çıktı:
# 🚀 Initializing Wikipedia Game Demo...
# 📦 Loading navigators...
# ✅ Demo ready!
# 
# ============================================================
# 🎮 Wikipedia Game - Interactive Demo
# ============================================================
# 
# 📍 Open in browser: http://localhost:5000
```

### 3. Tarayıcıda Aç

```
http://localhost:5000
```

## 🎮 Özellikler

### 1. **Path Bulma**
- Başlangıç ve hedef makale gir
- Algoritma seç (Semantic veya Bidirectional)
- "Find Path" butonuna tıkla
- Path'i görsel olarak gör

### 2. **Algoritma Seçimi**
- **🚀 Semantic (Fast)**: Hızlı greedy search
- **🎯 Bidirectional (Optimal)**: Optimal path garantisi

### 3. **Adım Adım Navigasyon**
- "Next Step" butonu ile tek adım ilerle
- Her adımda en iyi link'i göster
- Semantic similarity skorlarını gör

### 4. **Rastgele Challenge**
- "Random Challenge" butonu
- Önceden hazırlanmış ilginç article çiftleri
- Hemen test etmeye başla

### 5. **Canlı Metrikler**
- Path uzunluğu (kaç makale)
- Tıklama sayısı
- Süre (saniye)
- KG istatistikleri
- Cache hit rate

## 📊 Arayüz Bileşenleri

### Ana Kart
```
┌─────────────────────────────────────┐
│  Start Article:  [Potato        ]  │
│  Target Article: [Pizza         ]  │
│                                     │
│  Algorithm: [Semantic] [Bidirect.] │
│                                     │
│  [🔍 Find Path] [🎲 Random] [👣 Step]│
└─────────────────────────────────────┘
```

### Path Görselleştirme
```
┌─────────────────────────────────────┐
│  📍 Path Found                      │
│                                     │
│  [Potato] → [Tomato] → [Pizza]     │
│                                     │
│  Click any article to open in       │
│  Wikipedia                          │
└─────────────────────────────────────┘
```

### Metrikler
```
┌──────────┬──────────┬──────────┬──────────┐
│    3     │    2     │  1.23s   │ Semantic │
│ Articles │  Clicks  │   Time   │Algorithm │
└──────────┴──────────┴──────────┴──────────┘
```

### Sistem İstatistikleri
```
┌──────────┬──────────┬──────────┐
│  8,234   │ 10,261   │  87.5%   │
│KG Nodes  │KG Edges  │Cache Hit │
└──────────┴──────────┴──────────┘
```

## 🎯 Kullanım Senaryoları

### Senaryo 1: Hızlı Test
```
1. Web demo'yu başlat
2. "Random Challenge" tıkla
3. "Find Path" tıkla
4. Sonucu gör
```

### Senaryo 2: Algoritma Karşılaştırması
```
1. Aynı start/end gir
2. Semantic ile test et → Sonucu kaydet
3. Bidirectional ile test et → Sonucu kaydet
4. Karşılaştır:
   - Hangi daha hızlı?
   - Hangi daha kısa path buldu?
```

### Senaryo 3: Adım Adım Öğrenme
```
1. Start ve target gir
2. "Next Step" tıkla
3. AI'ın seçtiği link'i gör
4. Reasoning'i oku (semantic similarity)
5. Start'ı güncelle (otomatik)
6. Tekrar "Next Step"
7. Hedefe ulaşana kadar devam et
```

### Senaryo 4: Manuel vs AI
```
1. Bir challenge seç
2. Önce kendin dene (Wikipedia'da)
3. Sonra AI'a yaptır (web demo)
4. Karşılaştır:
   - Sen kaç tıklama yaptın?
   - AI kaç tıklama yaptı?
   - Kim daha hızlıydı?
```

## 🔧 API Endpoints

Web demo aşağıdaki API endpoint'leri sunar:

### POST /api/navigate
Path bulma.

**Request:**
```json
{
  "start": "Potato",
  "end": "Pizza",
  "algorithm": "semantic"
}
```

**Response:**
```json
{
  "success": true,
  "path": ["Potato", "Tomato", "Pizza"],
  "length": 3,
  "time": 1.23,
  "algorithm": "semantic",
  "metrics": {
    "steps": 2,
    "time_per_step": 0.615,
    "kg_nodes": 8234,
    "kg_edges": 10261
  }
}
```

### POST /api/step
Tek adım ilerle.

**Request:**
```json
{
  "current": "Potato",
  "target": "Pizza"
}
```

**Response:**
```json
{
  "success": true,
  "next": "Tomato",
  "links": [
    {"name": "Tomato", "score": 0.85},
    {"name": "Vegetable", "score": 0.72},
    ...
  ],
  "all_links_count": 247,
  "reasoning": "Semantic similarity to target: 0.850"
}
```

### GET /api/stats
Sistem istatistikleri.

**Response:**
```json
{
  "kg": {
    "nodes": 8234,
    "edges": 10261,
    "paths_learned": 10261,
    "paths_reused": 1523
  },
  "scraper": {
    "size": 256,
    "max_size": 256,
    "hits": 1234,
    "misses": 567,
    "hit_rate": 68.5
  },
  "embedder": {
    "model": "paraphrase-MiniLM-L6-v2",
    "dimension": 384
  },
  "navigators": ["semantic", "bidirectional"]
}
```

### GET /api/random
Rastgele article çifti.

**Response:**
```json
{
  "start": "Albert_Einstein",
  "end": "Physics"
}
```

## 🎨 Özelleştirme

### Port Değiştirme
```python
# web_demo.py son satır
app.run(debug=True, host='0.0.0.0', port=5000)  # 5000 yerine istediğiniz port
```

### Yeni Algoritma Ekleme
```python
# web_demo.py içinde navigators dict'ine ekle
navigators = {
    'semantic': {...},
    'bidirectional': {...},
    'your_algorithm': {  # YENI!
        'name': 'Your Algorithm',
        'description': 'Description here',
        'navigator': your_navigator_instance
    }
}
```

### UI Renkleri
```css
/* templates/index.html içinde style tag'inde */
.btn-primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    /* İstediğiniz renkleri kullanın */
}
```

## 🐛 Troubleshooting

### Problem: Port zaten kullanımda
```bash
# Çözüm 1: Farklı port kullan
# web_demo.py'de port'u değiştir

# Çözüm 2: Mevcut process'i kapat
lsof -ti:5000 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :5000   # Windows
```

### Problem: Flask bulunamadı
```bash
# Çözüm: Flask'ı kur
pip install flask flask-cors
```

### Problem: Navigator hatası
```bash
# Çözüm: Tüm bağımlılıkları kur
pip install -r requirements.txt
```

### Problem: Yavaş çalışıyor
```bash
# Çözüm 1: Cache'i temizle
rm -rf cache/wiki_graph.pkl

# Çözüm 2: Daha küçük beam width kullan
# (Eğer beam search kullanıyorsanız)

# Çözüm 3: Debug mode'u kapat
# web_demo.py'de debug=False yap
```

## 📈 Performans İpuçları

### 1. Cache Optimizasyonu
```python
# web_demo.py'de cache size'ları artır
scraper = WikipediaScraper(cache_size=512)  # 256'dan 512'ye
embedder = WikiEmbedder(cache_size=4096)    # 2048'den 4096'ya
```

### 2. Parallel Workers
```python
# Semantic navigator için worker sayısını artır
semantic_nav = SemanticNavigator(
    verbose=False,
    use_graph=True,
    use_async=False,
    max_workers=8  # 4'ten 8'e
)
```

### 3. Production Deployment
```python
# Production için Gunicorn kullan
pip install gunicorn

# Çalıştır
gunicorn -w 4 -b 0.0.0.0:5000 web_demo:app
```

## 🌟 Gelecek Özellikler

- [ ] Multiplayer mode (aynı anda birden fazla kullanıcı)
- [ ] Leaderboard (en hızlı path'ler)
- [ ] Path replay (animasyonlu gösterim)
- [ ] Custom challenges (kullanıcı tanımlı)
- [ ] Statistics dashboard (detaylı grafikler)
- [ ] Mobile responsive design
- [ ] Dark mode
- [ ] Export results (JSON/CSV)

## 🤝 Katkıda Bulunma

Web demo'ya katkıda bulunmak için:

1. UI iyileştirmeleri (`templates/index.html`)
2. Yeni API endpoint'leri (`web_demo.py`)
3. Yeni özellikler (yukarıdaki listeden)
4. Bug fix'ler
5. Dokümantasyon güncellemeleri

## 📚 İlgili Dokümantasyon

- [`README.md`](../README.md) - Ana dokümantasyon
- [`docs/USAGE.md`](./USAGE.md) - Terminal kullanımı
- [`docs/ARCHITECTURE.md`](./ARCHITECTURE.md) - Sistem mimarisi
- [`docs/BENCHMARK_GUIDE.md`](./BENCHMARK_GUIDE.md) - Benchmark sistemi

---

**Hazırlayan:** WikipediaML Team
**Tarih:** 19 Aralık 2024
**Versiyon:** 1.0
**Durum:** ✅ Aktif