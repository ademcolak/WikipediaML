# 🎨 Knowledge Graph Görselleştirme Rehberi

## 📊 Genel Bakış

10,000+ node içeren büyük Knowledge Graph'ları görselleştirmek performans sorunlarına yol açabilir. Bu rehber, optimize edilmiş görselleştirme stratejilerini açıklar.

## 🚀 Hızlı Başlangıç

### Temel Kullanım

```bash
# Otomatik (300 node - önerilen)
python visualize_kg_3d.py

# Hızlı görünüm (100 node)
python visualize_kg_3d.py --preset small

# Detaylı görünüm (500 node)
python visualize_kg_3d.py --preset large
```

## 🎯 Preset'ler

### Small (100 node)
- **Kullanım:** Hızlı genel bakış
- **Hız:** ⚡⚡⚡ Çok hızlı
- **Kalite:** Temel yapı görünür
- **Önerilen:** İlk bakış, hızlı kontrol

```bash
python visualize_kg_3d.py --preset small
```

### Medium (300 node) - VARSAYILAN
- **Kullanım:** Dengeli görünüm
- **Hız:** ⚡⚡ Hızlı
- **Kalite:** İyi detay seviyesi
- **Önerilen:** Genel kullanım

```bash
python visualize_kg_3d.py
# veya
python visualize_kg_3d.py --preset medium
```

### Large (500 node)
- **Kullanım:** Detaylı analiz
- **Hız:** ⚡ Orta
- **Kalite:** Yüksek detay
- **Önerilen:** Detaylı inceleme

```bash
python visualize_kg_3d.py --preset large
```

### Full (Tüm Graph)
- **Kullanım:** Tam görünüm
- **Hız:** 🐌 Yavaş
- **Kalite:** Maksimum detay
- **Önerilen:** ❌ 10K+ node için önerilmez!

```bash
python visualize_kg_3d.py --preset full
```

## ⚙️ Gelişmiş Seçenekler

### Özel Node Sayısı

```bash
# Tam olarak 150 node göster
python visualize_kg_3d.py --max-nodes 150

# 250 node göster
python visualize_kg_3d.py --max-nodes 250
```

### Weight Filtresi

```bash
# Sadece weight >= 2.0 olan edge'leri göster
python visualize_kg_3d.py --min-weight 2.0

# Sadece çok kullanılan yolları göster
python visualize_kg_3d.py --min-weight 3.0
```

### Hızlı Mod

```bash
# Düşük kalite layout (daha hızlı)
python visualize_kg_3d.py --preset small --fast

# Orta boyut + hızlı mod
python visualize_kg_3d.py --preset medium --fast
```

### Kombinasyonlar

```bash
# 200 node + minimum weight 2.0
python visualize_kg_3d.py --max-nodes 200 --min-weight 2.0

# Large preset + hızlı mod
python visualize_kg_3d.py --preset large --fast

# Özel ayarlar
python visualize_kg_3d.py --max-nodes 300 --min-weight 1.5 --fast
```

## 📈 Performans Optimizasyonları

### Otomatik Optimizasyonlar

1. **Node Seçimi:** En yüksek degree'li (en çok bağlantılı) node'lar otomatik seçilir
2. **Layout Iterasyonları:** Node sayısına göre otomatik ayarlanır
   - 300+ node: 20 iterasyon (hızlı)
   - 150-300 node: 30 iterasyon (orta)
   - <150 node: 50 iterasyon (yüksek kalite)
3. **Text Rendering:** 200+ node'da otomatik kapatılır (performans için)
4. **Edge Rendering:** Şeffaflık ile optimize edilmiş

### Manuel Optimizasyonlar

```bash
# En hızlı görselleştirme
python visualize_kg_3d.py --preset small --fast --min-weight 2.0

# Dengeli performans
python visualize_kg_3d.py --preset medium

# Maksimum detay (yavaş)
python visualize_kg_3d.py --preset large
```

## 🎨 Görselleştirme Özellikleri

### İnteraktif Özellikler

- **Döndürme:** Fare ile sürükle
- **Zoom:** Mouse scroll
- **Hover:** Node detayları
- **Renk:** Bağlantı sayısına göre (Viridis colormap)
- **Boyut:** Node degree'ye göre

### Node Bilgileri

Her node'un hover'ında:
- Node adı
- Bağlantı sayısı
- İlk 5 komşu (+ toplam sayı)

### Renk Skalası

- **Mavi:** Az bağlantılı node'lar
- **Yeşil:** Orta bağlantılı node'lar
- **Sarı:** Çok bağlantılı node'lar

## 📊 Çıktı Dosyası

### HTML Dosyası

```bash
# Varsayılan: kg_3d.html
python visualize_kg_3d.py

# Özel dosya adı
python visualize_kg_3d.py --output my_graph.html
```

### Dosya Boyutu

- **Small (100 node):** ~1-2 MB
- **Medium (300 node):** ~3-5 MB
- **Large (500 node):** ~6-10 MB
- **Full (10K+ node):** ~50-100+ MB ⚠️

## 🔧 Sorun Giderme

### Problem: Görselleştirme çok yavaş

**Çözüm:**
```bash
# Daha az node kullan
python visualize_kg_3d.py --preset small

# Hızlı mod aktif et
python visualize_kg_3d.py --preset medium --fast

# Weight filtresi ekle
python visualize_kg_3d.py --preset medium --min-weight 2.0
```

### Problem: HTML dosyası çok büyük

**Çözüm:**
```bash
# Node sayısını azalt
python visualize_kg_3d.py --max-nodes 200

# Sadece önemli edge'leri göster
python visualize_kg_3d.py --preset medium --min-weight 2.0
```

### Problem: Tarayıcı donuyor

**Çözüm:**
```bash
# Çok daha az node kullan
python visualize_kg_3d.py --preset small

# Veya istatistiklere bak
python kg_stats.py
```

### Problem: Layout kalitesi düşük

**Çözüm:**
```bash
# Daha fazla iterasyon (--fast kullanma)
python visualize_kg_3d.py --preset medium

# Daha az node ile daha iyi layout
python visualize_kg_3d.py --max-nodes 150
```

## 💡 En İyi Pratikler

### 10K+ Node için

1. **İlk bakış:** `--preset small` ile başla
2. **Detaylı inceleme:** `--preset medium` kullan
3. **Spesifik analiz:** `--min-weight` ile filtrele
4. **Full görünüm:** ❌ Kullanma (çok yavaş)

### Örnek İş Akışı

```bash
# 1. Hızlı genel bakış
python visualize_kg_3d.py --preset small

# 2. Orta detay inceleme
python visualize_kg_3d.py --preset medium

# 3. Önemli yolları analiz et
python visualize_kg_3d.py --preset medium --min-weight 2.0

# 4. Spesifik bölge
python visualize_kg_3d.py --max-nodes 200 --min-weight 1.5
```

## 📈 İstatistikler

### Görselleştirme Çıktısı

```
📊 GRAPH İSTATİSTİKLERİ
==================================================
📍 Node sayısı: 300
🔗 Edge sayısı: 1,245

📈 Bağlantı İstatistikleri:
   Ortalama: 8.30
   Maksimum: 45
   Minimum: 1

🌟 En Bağlantılı Sayfalar:
   1. United_States: 45 bağlantı
   2. Europe: 38 bağlantı
   3. World_War_II: 32 bağlantı
   4. France: 28 bağlantı
   5. Germany: 25 bağlantı

⚖️  Weight İstatistikleri:
   Ortalama: 1.85
   Maksimum: 5.00
   Minimum: 1.00
==================================================
```

## 🎓 İpuçları

1. **Başlangıç:** Her zaman `--preset medium` ile başla
2. **Performans:** Yavaşsa `--preset small` kullan
3. **Detay:** Daha fazla detay için `--preset large`
4. **Filtreleme:** `--min-weight` ile önemli yolları vurgula
5. **Hız:** `--fast` ile layout hızını artır
6. **Dosya Boyutu:** Küçük dosya için az node kullan

## 🔗 İlgili Komutlar

```bash
# KG istatistikleri
python kg_stats.py

# Graph birleştirme
python merge_graphs.py

# Eğitim
python train.py --strategy strategic --iterations 50
```

## 📚 Daha Fazla Bilgi

- [ARCHITECTURE.md](ARCHITECTURE.md) - Sistem mimarisi
- [USAGE.md](USAGE.md) - Kullanım kılavuzu
- [README.md](../README.md) - Ana dokümantasyon