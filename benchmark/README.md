# 📊 Benchmark Sistemi

Otomatik test ve performans ölçüm sistemi.

## 🎯 Özellikler

- **Dataset Oluşturma:** Popüler ve random Wikipedia sayfalarından test pair'leri
- **Otomatik Test:** Farklı algoritmalarla benchmark çalıştırma
- **Görselleştirme:** İnteraktif dashboard'lar
- **Karşılaştırma:** Algoritmaları karşılaştırma

## 🚀 Hızlı Başlangıç

### 1. Dataset Oluştur

```bash
# 500 test pair (mixed difficulty)
python benchmark/create_dataset.py --count 500

# Sadece kolay test'ler
python benchmark/create_dataset.py --count 100 --difficulty easy

# Özel sayılar
python benchmark/create_dataset.py --count 200 --popular-count 100 --random-count 100
```

### 2. Benchmark Çalıştır

```bash
# Greedy algorithm
python benchmark/run_benchmark.py

# Beam search
python benchmark/run_benchmark.py --algorithm beam --beam-width 3

# A* search
python benchmark/run_benchmark.py --algorithm astar

# İlk 50 test
python benchmark/run_benchmark.py --max-tests 50
```

### 3. Sonuçları Görselleştir

```bash
# Tek sonuç
python benchmark/visualize_results.py benchmark/results_greedy_*.json

# Karşılaştırma
python benchmark/visualize_results.py benchmark/results_*.json --compare
```

## 📁 Dosya Yapısı

```
benchmark/
├── README.md                    # Bu dosya
├── create_dataset.py            # Dataset oluşturucu
├── run_benchmark.py             # Benchmark runner
├── visualize_results.py         # Görselleştirme
├── test_dataset.json            # Test dataset
└── results_*.json               # Benchmark sonuçları
```

## 📊 Metrikler

### Toplanan Metrikler

- **Başarı Oranı:** Başarılı test / Toplam test
- **Ortalama Süre:** Başarılı test'lerin ortalama süresi
- **Ortalama Tıklama:** Başarılı test'lerin ortalama tıklama sayısı
- **KG Hit Rate:** Knowledge Graph'tan direkt bulunan yollar
- **Zorluk Bazlı:** Easy, Medium, Hard kategorilerinde ayrı metrikler

### Görselleştirmeler

1. **Süre Dağılımı:** Histogram
2. **Tıklama Dağılımı:** Histogram
3. **Zorluk Bazlı Başarı:** Bar chart
4. **Süre vs Tıklama:** Scatter plot
5. **Algoritma Karşılaştırması:** Multi-bar charts

## 🎯 Kullanım Senaryoları

### Senaryo 1: Hızlı Test (50 test)

```bash
# Dataset oluştur
python benchmark/create_dataset.py --count 50 --difficulty easy

# Test et
python benchmark/run_benchmark.py --max-tests 50

# Görselleştir
python benchmark/visualize_results.py benchmark/results_*.json
```

### Senaryo 2: Tam Benchmark (500 test)

```bash
# Dataset oluştur
python benchmark/create_dataset.py --count 500

# Greedy test
python benchmark/run_benchmark.py --algorithm greedy

# Beam search test
python benchmark/run_benchmark.py --algorithm beam --beam-width 3

# A* search test
python benchmark/run_benchmark.py --algorithm astar

# Karşılaştır
python benchmark/visualize_results.py benchmark/results_*.json --compare
```

### Senaryo 3: Algoritma Tuning

```bash
# Farklı beam width'ler dene
python benchmark/run_benchmark.py --algorithm beam --beam-width 2
python benchmark/run_benchmark.py --algorithm beam --beam-width 3
python benchmark/run_benchmark.py --algorithm beam --beam-width 5

# Karşılaştır
python benchmark/visualize_results.py benchmark/results_beam_*.json --compare
```

## 📈 Örnek Sonuçlar

### Greedy Algorithm
```
✅ Başarılı: 475/500 (%95.0)
⏱️  Ortalama Süre: 1.85s
🎯 Ortalama Tıklama: 3.2
💾 KG Hit Rate: %45.2
```

### Beam Search (width=3)
```
✅ Başarılı: 480/500 (%96.0)
⏱️  Ortalama Süre: 2.15s
🎯 Ortalama Tıklama: 2.8
💾 KG Hit Rate: %42.1
```

### A* Search
```
✅ Başarılı: 485/500 (%97.0)
⏱️  Ortalama Süre: 2.45s
🎯 Ortalama Tıklama: 2.6
💾 KG Hit Rate: %40.5
```

## 🔧 Gelişmiş Kullanım

### Özel Dataset

```python
# create_custom_dataset.py
from benchmark.create_dataset import DatasetCreator

creator = DatasetCreator()

# Özel sayfalar
custom_pages = ["Python", "Java", "JavaScript", "C++", "Ruby"]

# Test pair'leri oluştur
pairs = []
for start in custom_pages:
    for target in custom_pages:
        if start != target:
            pairs.append((start, target, "custom"))

# Kaydet
creator.save_dataset(pairs, "benchmark/custom_dataset.json")
```

### Özel Metrikler

```python
# analyze_custom.py
import json

with open("benchmark/results_greedy_*.json") as f:
    data = json.load(f)

# Özel analiz
for result in data['results']:
    if result['success']:
        efficiency = result['clicks'] / result['time']
        print(f"{result['start']} → {result['target']}: {efficiency:.2f} clicks/s")
```

## 💡 İpuçları

1. **Küçük Başla:** İlk test'lerde `--max-tests 50` kullan
2. **Zorluk Seç:** Kolay test'lerle başla (`--difficulty easy`)
3. **Karşılaştır:** Farklı algoritmaları karşılaştır
4. **Iterasyon:** Sonuçlara göre parametreleri ayarla
5. **Dokümante Et:** Sonuçları kaydet ve analiz et

## 🐛 Sorun Giderme

### Problem: Dataset oluşturulamıyor

**Çözüm:** İnternet bağlantısını kontrol edin, Wikipedia API'sine erişim gerekli.

### Problem: Benchmark çok yavaş

**Çözüm:** `--max-tests` ile test sayısını azaltın veya `--no-async` kullanmayın.

### Problem: Görselleştirme açılmıyor

**Çözüm:** Plotly kurulu olduğundan emin olun: `pip install plotly`

## 📚 Daha Fazla Bilgi

- [Ana README](../README.md)
- [ROADMAP](../docs/ROADMAP.md)
- [ARCHITECTURE](../docs/ARCHITECTURE.md)