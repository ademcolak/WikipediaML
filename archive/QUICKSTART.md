# 🚀 Wikipedia PathFinder - Hızlı Başlangıç

## Kurulum

```bash
# 1. Repo'yu klonla (veya indir)
cd WikipediaML

# 2. Virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Dependencies
pip install -r requirements.txt
```

**Not:** İlk çalıştırmada embedding model indirilecek (~80MB).

---

## Kullanım

### Temel Kullanım
```bash
python main.py <başlangıç> <hedef>
```

### Örnekler

**Basit:**
```bash
python main.py Potato Pizza
```
Çıktı: `Potato → Tomato → Pizza` (2 adım, 2-3 saniye)

**Bilim:**
```bash
python main.py Albert_Einstein Physics
```

**Teknoloji:**
```bash
python main.py Python_(programming_language) Machine_learning
```

---

## Ne Olur?

### İlk Çalıştırma
```
1. Semantic Search çalışır
2. Akıllı link seçimi (embeddings)
3. Path bulunur: A → B → C
4. Graph'a kaydedilir
⏱️  Süre: 2-3 saniye
```

### İkinci Çalıştırma (Aynı Path)
```
1. Graph'ta path var mı? → EVET!
2. Anında kullan
⏱️  Süre: 0.00 saniye (2000x+ hızlı!)
⚡ Öğrenme sistemi çalışıyor!
```

---

## Argüman Formatı

**Sayfa İsimleri:**
- Wikipedia URL'indeki `/wiki/` sonrası kısım
- Boşluklar → `_` kullan
- Parantez → Normal kullan: `Python_(programming_language)`

**Örnekler:**
```
https://en.wikipedia.org/wiki/Albert_Einstein
                                  ↓
                         Albert_Einstein


https://en.wikipedia.org/wiki/Python_(programming_language)
                                  ↓
                         Python_(programming_language)
```

---

## Sistem Özellikleri

🧠 **Semantic Embeddings**
- Model: all-MiniLM-L6-v2 (384 dim)
- Anlam bazlı link seçimi
- Top-5 candidate gösterme

🧬 **Knowledge Graph**
- Başarılı path'leri öğrenir
- NetworkX directed graph
- Persistent: wiki_graph.pkl

🔮 **Beam Search**
- Multi-path exploration
- Daha robust (greedy'den)

💾 **Triple Cache**
- Scraper cache (HTML)
- Embedder cache (vectors)
- Graph cache (paths)

---

## Örnek Çıktı

```bash
$ python main.py Potato Pizza

======================================================================
🌐 WIKIPEDIA PATHFINDER
======================================================================

📍 Başlangıç: Potato
🎯 Hedef: Pizza

...

✅ Path bulundu!

🛤️  Path:
   Potato → Tomato → Pizza

📏 Adım sayısı: 2
⏱️  Süre: 2.22s
🤖 Algoritma: Hybrid (Semantic)

Knowledge Graph:
  Paths learned: 1  ← Kaydedildi!
```

**İkinci çalıştırma:**
```bash
$ python main.py Potato Pizza

...

✅ Path bulundu!
⏱️  Süre: 0.00s  ← Anında!
🤖 Algoritma: Hybrid (Graph Reused)  ← Graph'tan geldi!

Knowledge Graph:
  Paths reused: 1  ← Kullanıldı!
```

---

## Sorun Giderme

**Model indirilemiyor:**
```bash
# Manuel indirme
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

**Sayfa bulunamadı:**
- Sayfa ismini kontrol et (Wikipedia'da var mı?)
- Boşluklar `_` ile değiştirilmiş mi?
- Büyük/küçük harf duyarlı

**Çok yavaş:**
- İlk çalıştırma yavaş olabilir (model yükleme)
- İkinci çalıştırmada graph kullanılacak (hızlı!)

---

## Gelişmiş Kullanım

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
```

### Graph'ı Temizle
```bash
rm wiki_graph.pkl
```

---

## Daha Fazla Bilgi

- **README.md** - Genel bilgi
- **ARCHITECTURE.md** - Teknik detaylar
- **docs/** - Detaylı dökümanlar

---

**Başarılar!** 🎉
