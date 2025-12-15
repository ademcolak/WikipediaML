# 📖 WikipediaML - Kullanım Rehberi

## 🚀 Hızlı Başlangıç

### 1. Basit Arama

```bash
# Tek arama
python main.py Italy Rome --async

# Farklı örnekler
python main.py Potato Pizza --async
python main.py Albert_Einstein Physics --async
```

**Sonuç:**
- İlk arama: 1-2 saniye (semantic ile bulur)
- İkinci arama: 0.00 saniye (KG'den hatırlar!)

---

## 🤖 Otomatik KG Büyütme

### 2. Otomatik Eğitim

```bash
# 10 çift dene (hızlı test)
python auto_train.py --count 10

# 50 çift dene (önerilen)
python auto_train.py --count 50

# Tüm çiftleri dene (43 çift)
python auto_train.py --all

# Sonsuz döngü (Ctrl+C ile dur)
python auto_train.py --continuous
```

**Ne Yapar:**
- Hazır sayfa çiftlerini kullanır
- Her çifti dener
- Başarılı olanları KG'ye ekler
- İstatistikleri gösterir

**Örnek Çıktı:**
```
🤖 OTOMATİK KG BÜYÜTME SİSTEMİ
======================================================================
📦 İlk 50 çift kullanılacak (default)
   Kolay: 18 çift
   Orta: 15 çift
   Zor: 10 çift

[1/50] Italy → Rome
   ✅ Bulundu: 1 adım, 0.856s
   Path: Italy → Rome

[2/50] France → Paris
   ✅ Bulundu: 1 adım, 0.923s
   Path: France → Paris

...

📊 İSTATİSTİKLER
======================================================================
Toplam deneme: 50
Başarılı: 47 (94.0%)
Başarısız: 3 (6.0%)
Cache hit: 12 (24.0%)
Ortalama adım: 2.3
Ortalama süre: 1.12s

📈 KNOWLEDGE GRAPH
   Öğrenilen yol: 47
   Node sayısı: 156
   Edge sayısı: 203
   Dosya: cache/wiki_graph.pkl
```

---

## 📊 İstatistikleri Görüntüleme

### 3. KG İstatistikleri

```bash
# Temel istatistikler
python kg_stats.py

# Detaylı istatistikler
python kg_stats.py --detailed
```

**Örnek Çıktı:**
```
📊 KNOWLEDGE GRAPH İSTATİSTİKLERİ
======================================================================

📈 GENEL BİLGİLER
──────────────────────────────────────────────────────────────────────
Öğrenilen yol sayısı: 47
Tekrar kullanılan yol: 12
Node sayısı: 156
Edge sayısı: 203

💾 CACHE PERFORMANSI
──────────────────────────────────────────────────────────────────────
Toplam sorgu: 59
Cache hit: 12 (20.3%)
Cache miss: 47 (79.7%)

💾 DOSYA BİLGİLERİ
──────────────────────────────────────────────────────────────────────
Dosya: cache/wiki_graph.pkl
Boyut: 15.23 KB
Durum: ✅ Mevcut

💡 ÖNERİLER
──────────────────────────────────────────────────────────────────────
✅ Güzel ilerleme! (47 yol)

🚀 Daha da büyütmek için:
   python auto_train.py --count 100
```

---

## 🎯 Kullanım Senaryoları

### Senaryo 1: İlk Kurulum

```bash
# 1. Bağımlılıkları kur
pip install -r requirements.txt

# 2. İlk aramayı yap
python main.py Italy Rome --async

# 3. İstatistikleri kontrol et
python kg_stats.py
```

### Senaryo 2: KG Büyütme (Günlük Rutin)

```bash
# Her gün 50 çift dene
python auto_train.py --count 50

# İstatistikleri kontrol et
python kg_stats.py

# 1 hafta sonra: 350 yol öğrenilmiş!
```

### Senaryo 3: Sürekli Öğrenme

```bash
# Sonsuz döngü başlat (screen/tmux ile)
screen -S wiki-train
python auto_train.py --continuous

# Detach: Ctrl+A+D
# Reattach: screen -r wiki-train
```

---

## 📈 Beklenen Sonuçlar

### 1 Gün Sonra:
```
Öğrenilen yol: 50
Cache hit rate: %20
Ortalama süre: 1.2s
```

### 1 Hafta Sonra:
```
Öğrenilen yol: 350
Cache hit rate: %50
Ortalama süre: 0.8s
```

### 1 Ay Sonra:
```
Öğrenilen yol: 1500
Cache hit rate: %75
Ortalama süre: 0.4s
```

---

## 🔧 Sorun Giderme

### Problem: "ModuleNotFoundError"
```bash
# Çözüm: Bağımlılıkları kur
pip install -r requirements.txt
```

### Problem: "KG dosyası bulunamadı"
```bash
# Çözüm: İlk aramayı yap
python main.py Italy Rome --async
```

### Problem: "Çok yavaş çalışıyor"
```bash
# Çözüm: --async flag kullan
python main.py Potato Pizza --async
```

### Problem: "Path bulunamadı"
```bash
# Normal! Bazı yollar çok zor
# Farklı çiftler deneyin
python main.py Italy Rome --async  # Kolay
```

---

## 💡 İpuçları

### 1. Async Kullanın
```bash
# Yavaş (1-2s)
python main.py Italy Rome

# Hızlı (0.5-1s) ✅
python main.py Italy Rome --async
```

### 2. Kolay Çiftlerle Başlayın
```bash
# İlk 10 çift kolay
python auto_train.py --count 10
```

### 3. İstatistikleri Takip Edin
```bash
# Her 50 aramada bir kontrol et
python kg_stats.py
```

### 4. Cache Hit Rate'i İzleyin
```bash
# %50+ olmalı (1 hafta sonra)
# %75+ olmalı (1 ay sonra)
```

---

## 🎓 Sistem Nasıl Öğrenir?

### Adım 1: İlk Arama
```
Potato → Pizza
├─> KG'de yok
├─> Semantic ile bul
├─> 2 adımda bulundu: Potato → Tomato → Pizza
└─> Süre: 1.5s
```

### Adım 2: KG'ye Kaydet
```
Knowledge Graph'a ekle:
- Potato → Tomato (weight: 1)
- Tomato → Pizza (weight: 1)
```

### Adım 3: İkinci Arama
```
Potato → Pizza
├─> KG'de var! ✅
├─> Potato → Tomato → Pizza
└─> Süre: 0.00s (ANINDA!)
```

### Adım 4: Sürekli İyileşme
```
Her arama:
├─> Yeni yollar öğrenilir
├─> Cache hit rate artar
├─> Sistem hızlanır
└─> Daha akıllı olur!
```

---

## 📊 Performans Metrikleri

| Metrik | İlk Gün | 1 Hafta | 1 Ay |
|--------|---------|---------|------|
| Öğrenilen yol | 50 | 350 | 1500 |
| Cache hit rate | %20 | %50 | %75 |
| Ortalama süre | 1.2s | 0.8s | 0.4s |
| Node sayısı | 150 | 800 | 3000 |

---

## 🚀 Sonraki Adımlar

1. ✅ İlk aramayı yapın
2. ✅ Otomatik eğitimi başlatın
3. ✅ İstatistikleri takip edin
4. ✅ Günlük 50 çift deneyin
5. ✅ 1 ay sonra 1500+ yol!

**Sistem sürekli öğrenir ve iyileşir!** 🎉