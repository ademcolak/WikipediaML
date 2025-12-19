# 📊 Benchmark Sistemi Rehberi

## 🎯 Genel Bakış

Benchmark sistemi, WikipediaML'in performansını otomatik olarak test etmek ve ölçmek için geliştirilmiş kapsamlı bir araçtır.

## 🚀 Hızlı Başlangıç

### 3 Adımda Benchmark

```bash
# 1. Dataset oluştur (500 test)
python benchmark/create_dataset.py --count 500

# 2. Benchmark çalıştır
python benchmark/run_benchmark.py

# 3. Sonuçları görselleştir
python benchmark/visualize_results.py benchmark/results_*.json
```

## 📋 Detaylı Kullanım

### 1. Dataset Oluşturma

#### Temel Kullanım
```bash
# 500 mixed difficulty test
python benchmark/create_dataset.py --count 500
```

#### Zorluk Seviyeleri
```bash
# Sadece kolay test'ler
python benchmark/create_dataset.py --count 100 --difficulty easy

# Sadece orta zorluk
python benchmark/create_dataset.py --count 200 --difficulty medium

# Sadece zor test'ler
python benchmark/create_dataset.py --count 100 --difficulty hard

# Karışık (varsayılan: %40 easy, %40 medium, %20 hard)
python benchmark/create_dataset.py --count 500 --difficulty mixed
```

#### Özel Sayılar
```bash
# Popüler ve random sayfa sayılarını ayarla
python benchmark/create_dataset.py \
  --count 300 \
  --popular-count 150 \
  --random-count 150
```

#### Çıktı
- **Dosya:** `benchmark/test_dataset.json`
- **Format:** JSON array of test pairs
- **İçerik:** start, target, difficulty, id

### 2. Benchmark Çalıştırma

#### Greedy Algorithm (Varsayılan)
```bash
# Tüm test'leri çalıştır
python benchmark/run_benchmark.py

# İlk 50 test (hızlı test)
python benchmark/run_benchmark.py --max-tests 50

# Sync mode (daha yavaş)
python benchmark/run_benchmark.py --no-async
```

#### Beam Search
```bash
# Beam width = 3 (varsayılan)
python benchmark/run_benchmark.py --algorithm beam

# Farklı beam width'ler
python benchmark/run_benchmark.py --algorithm beam --beam-width 2
python benchmark/run_benchmark.py --algorithm beam --beam-width 5
python benchmark/run_benchmark.py --algorithm beam --beam-width 10
```

#### A* Search
```bash
# A* algorithm
python benchmark/run_benchmark.py --algorithm astar

# İlk 50 test
python benchmark/run_benchmark.py --algorithm astar --max-tests 50
```

#### Özel Dataset
```bash
# Farklı dataset kullan
python benchmark/run_benchmark.py --dataset benchmark/custom_dataset.json
```

#### Çıktı
- **Dosya:** `benchmark/results_<algorithm>_<timestamp>.json`
- **İçerik:** Metadata, analysis, detailed results

### 3. Sonuçları Görselleştirme

#### Tek Sonuç
```bash
# En son sonucu görselleştir
python benchmark/visualize_results.py benchmark/results_greedy_*.json

# Belirli bir sonuç
python benchmark/visualize_results.py benchmark/results_greedy_20250119_123456.json
```

#### Karşılaştırma
```bash
# Tüm sonuçları karşılaştır
python benchmark/visualize_results.py benchmark/results_*.json --compare

# Sadece beam search sonuçlarını karşılaştır
python benchmark/visualize_results.py benchmark/results_beam_*.json --compare

# Özel çıktı dosyası
python benchmark/visualize_results.py benchmark/results_*.json \
  --compare \
  --output benchmark/my_comparison.html
```

#### Çıktı
- **Dosya:** `benchmark/dashboard.html` veya `benchmark/dashboard_comparison.html`
- **Format:** İnteraktif HTML dashboard (Plotly)

## 📊 Metrikler

### Toplanan Metrikler

1. **Başarı Oranı**
   - Başarılı test / Toplam test
   - Zorluk bazlı (easy, medium, hard)

2. **Süre Metrikleri**
   - Ortalama süre
   - Medyan süre
   - Min/Max süre
   - Standart sapma

3. **Tıklama Metrikleri**
   - Ortalama tıklama
   - Medyan tıklama
   - Min/Max tıklama

4. **KG Cache Hit Rate**
   - Knowledge Graph'tan direkt bulunan yollar
   - Cache efficiency

### Görselleştirmeler

#### Tek Sonuç Dashboard
1. **Süre Dağılımı:** Histogram
2. **Tıklama Dağılımı:** Histogram
3. **Zorluk Bazlı Başarı:** Bar chart
4. **Süre vs Tıklama:** Scatter plot

#### Karşılaştırma Dashboard
1. **Ortalama Süre:** Bar chart
2. **Ortalama Tıklama:** Bar chart
3. **Başarı Oranı:** Bar chart
4. **Süre Dağılımı:** Box plot

## 🎯 Kullanım Senaryoları

### Senaryo 1: Hızlı Performans Kontrolü

**Amaç:** Sistemin genel performansını hızlıca kontrol et

```bash
# 50 kolay test
python benchmark/create_dataset.py --count 50 --difficulty easy
python benchmark/run_benchmark.py --max-tests 50
python benchmark/visualize_results.py benchmark/results_*.json
```

**Beklenen Süre:** ~2-3 dakika

### Senaryo 2: Algoritma Karşılaştırması

**Amaç:** Greedy, Beam, A* algoritmalarını karşılaştır

```bash
# Dataset oluştur (bir kere)
python benchmark/create_dataset.py --count 200

# Her algoritmayı test et
python benchmark/run_benchmark.py --algorithm greedy
python benchmark/run_benchmark.py --algorithm beam --beam-width 3
python benchmark/run_benchmark.py --algorithm astar

# Karşılaştır
python benchmark/visualize_results.py benchmark/results_*.json --compare
```

**Beklenen Süre:** ~15-20 dakika

### Senaryo 3: Beam Width Optimizasyonu

**Amaç:** En iyi beam width'i bul

```bash
# Dataset oluştur
python benchmark/create_dataset.py --count 100

# Farklı width'leri test et
python benchmark/run_benchmark.py --algorithm beam --beam-width 2
python benchmark/run_benchmark.py --algorithm beam --beam-width 3
python benchmark/run_benchmark.py --algorithm beam --beam-width 5
python benchmark/run_benchmark.py --algorithm beam --beam-width 10

# Karşılaştır
python benchmark/visualize_results.py benchmark/results_beam_*.json --compare
```

**Beklenen Süre:** ~10-15 dakika

### Senaryo 4: Tam Benchmark (Production)

**Amaç:** Kapsamlı performans testi

```bash
# Büyük dataset
python benchmark/create_dataset.py --count 500

# Tüm algoritmalar
python benchmark/run_benchmark.py --algorithm greedy
python benchmark/run_benchmark.py --algorithm beam --beam-width 3
python benchmark/run_benchmark.py --algorithm astar

# Karşılaştır
python benchmark/visualize_results.py benchmark/results_*.json --compare
```

**Beklenen Süre:** ~30-45 dakika

## 📈 Sonuç Analizi

### Başarı Kriterleri

#### Minimum (MVP)
- ✅ Başarı Oranı: >%90
- ✅ Ortalama Süre: <2s
- ✅ Ortalama Tıklama: <4

#### İdeal
- 🎯 Başarı Oranı: >%95
- 🎯 Ortalama Süre: <1.5s
- 🎯 Ortalama Tıklama: <3.5

#### Mükemmel
- 🌟 Başarı Oranı: >%97
- 🌟 Ortalama Süre: <1s
- 🌟 Ortalama Tıklama: <3

### Zorluk Bazlı Beklentiler

#### Easy
- Başarı: >%98
- Süre: <1.5s
- Tıklama: <3

#### Medium
- Başarı: >%95
- Süre: <2s
- Tıklama: <3.5

#### Hard
- Başarı: >%85
- Süre: <3s
- Tıklama: <4.5

## 🔧 İleri Seviye

### Özel Dataset Oluşturma

```python
# custom_dataset.py
import json

# Özel test pair'leri
custom_pairs = [
    {"id": 1, "start": "Python", "target": "Java", "difficulty": "easy"},
    {"id": 2, "start": "Physics", "target": "Chemistry", "difficulty": "medium"},
    {"id": 3, "start": "Ancient_Rome", "target": "Modern_Japan", "difficulty": "hard"}
]

# Kaydet
with open("benchmark/custom_dataset.json", "w") as f:
    json.dump(custom_pairs, f, indent=2)

# Kullan
# python benchmark/run_benchmark.py --dataset benchmark/custom_dataset.json
```

### Sonuç Analizi

```python
# analyze_results.py
import json
import statistics

# Sonuçları yükle
with open("benchmark/results_greedy_*.json") as f:
    data = json.load(f)

# Özel analiz
successful = [r for r in data['results'] if r['success']]

# Efficiency (clicks per second)
for result in successful:
    efficiency = result['clicks'] / result['time']
    print(f"{result['start']} → {result['target']}: {efficiency:.2f} clicks/s")

# En hızlı/yavaş test'ler
fastest = min(successful, key=lambda x: x['time'])
slowest = max(successful, key=lambda x: x['time'])

print(f"\nEn hızlı: {fastest['start']} → {fastest['target']} ({fastest['time']:.2f}s)")
print(f"En yavaş: {slowest['start']} → {slowest['target']} ({slowest['time']:.2f}s)")
```

### CI/CD Integration

```yaml
# .github/workflows/benchmark.yml
name: Benchmark

on:
  push:
    branches: [ main ]
  schedule:
    - cron: '0 0 * * 0'  # Her Pazar

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run benchmark
        run: |
          python benchmark/create_dataset.py --count 100
          python benchmark/run_benchmark.py --max-tests 100
      
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: benchmark-results
          path: benchmark/results_*.json
```

## 💡 İpuçları

1. **Küçük Başla:** İlk test'lerde `--max-tests 50` kullan
2. **Zorluk Seç:** Kolay test'lerle başla
3. **Karşılaştır:** Farklı algoritmaları karşılaştır
4. **İterasyon:** Sonuçlara göre parametreleri ayarla
5. **Dokümante Et:** Sonuçları kaydet ve analiz et
6. **Otomatikleştir:** CI/CD ile düzenli benchmark

## 🐛 Sorun Giderme

### Problem: Dataset oluşturulamıyor

**Çözüm:**
- İnternet bağlantısını kontrol edin
- Wikipedia API'sine erişim gerekli
- Rate limiting nedeniyle yavaş olabilir

### Problem: Benchmark çok yavaş

**Çözüm:**
- `--max-tests` ile test sayısını azaltın
- `--no-async` kullanmayın (async daha hızlı)
- Daha az zorluk seviyesi seçin

### Problem: Görselleştirme açılmıyor

**Çözüm:**
- Plotly kurulu olduğundan emin olun: `pip install plotly`
- HTML dosyasını manuel olarak açın
- Tarayıcı uyumluluğunu kontrol edin

### Problem: Düşük başarı oranı

**Çözüm:**
- Knowledge Graph'ı büyütün (daha fazla eğitim)
- Farklı algoritma deneyin (Beam, A*)
- Test zorluk seviyesini kontrol edin

## 📚 İlgili Dokümantasyon

- [Benchmark README](../benchmark/README.md)
- [ROADMAP](ROADMAP.md)
- [ARCHITECTURE](ARCHITECTURE.md)
- [Ana README](../README.md)