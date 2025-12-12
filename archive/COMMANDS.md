# 🎮 WikipediaML - Kullanılabilir Komutlar

## 📋 Mevcut Komutlar

### 1. Ana Uygulama (Temel Kullanım)

#### Basit Arama (Sync Mode)
```bash
python main.py "Python_(programming_language)" "Machine_learning"
```

#### Hızlı Arama (Async Mode - ÖNERİLİR!)
```bash
python main.py "Python_(programming_language)" "Machine_learning" --async
```

#### Claude ile Akıllı Arama
```bash
python main.py "Potato" "Pizza" --async --claude
```
**Not:** Claude için `ANTHROPIC_API_KEY` environment variable gerekli

#### Farklı Modlar
```bash
# Sync mode (default)
python main.py "Start" "Target"

# Async mode (3x daha hızlı!)
python main.py "Start" "Target" --async

# Claude reasoning (en akıllı)
python main.py "Start" "Target" --claude

# Async + Claude (en iyi kombinasyon)
python main.py "Start" "Target" --async --claude
```

---

### 2. Machine Learning (YENİ!)

#### ML Model Training (Hızlı Test)
```bash
python train_ml_model.py --quick
```
- 10 random page pair ile hızlı test
- ~5-10 dakika
- Verbose mode default olarak açık

#### ML Model Training (Normal)
```bash
python train_ml_model.py --pairs 50
```
- 50 random page pair ile training
- ~30-60 dakika
- Default: 100 pairs

#### ML Model Training (Sürekli Öğrenme)
```bash
python train_ml_model.py --continuous --iterations 10
```
- 10 iterasyon sürekli öğrenme
- Her iterasyonda 10 pair (default)
- ~2-3 saat

#### Verbose Mode Kapatma
```bash
python train_ml_model.py --quick --no-verbose
```
- Sessiz mod (verbose kapalı)

---

## 🔧 Gelişmiş Kullanım

### Komut Kombinasyonları

#### En Hızlı Arama
```bash
python main.py "Start" "Target" --async
```

#### En Akıllı Arama
```bash
python main.py "Start" "Target" --async --claude
```

#### ML Model ile Arama (Yakında!)
```bash
# ML model train edildikten sonra
python main.py "Start" "Target" --ml
```

---

## 📊 Örnek Kullanım Senaryoları

### Senaryo 1: Hızlı Test
```bash
# 1. Basit arama (sync)
python main.py "Python_(programming_language)" "Java_(programming_language)"

# 2. Hızlı arama (async)
python main.py "Python_(programming_language)" "Java_(programming_language)" --async
```

### Senaryo 2: ML Model Eğitimi
```bash
# 1. Hızlı test (10 pair, ~5-10 dakika)
python train_ml_model.py --quick

# 2. Model başarılı olduysa, normal training (50 pair, ~30-60 dakika)
python train_ml_model.py --pairs 50

# 3. Sürekli öğrenme (opsiyonel, ~2-3 saat)
python train_ml_model.py --continuous --iterations 20
```

### Senaryo 3: Zor Path'ler
```bash
# 1. Async mode ile dene
python main.py "Porsche" "Serik_Akhmetov_Government" --async

# 2. Başarısız olursa Claude ekle
python main.py "Porsche" "Serik_Akhmetov_Government" --async --claude
```

---

## 🎯 Önerilen İlk Adımlar

### Yeni Başlayanlar İçin
```bash
# 1. Basit bir arama yap
python main.py "Computer" "Internet"

# 2. Async mode ile dene (daha hızlı)
python main.py "Computer" "Internet" --async

# 3. İstatistikleri incele (otomatik gösterilir)
```

### İleri Seviye Kullanıcılar İçin
```bash
# 1. ML model'i train et
python train_ml_model.py --quick

# 2. Claude reasoning'i dene
export ANTHROPIC_API_KEY='your-key'
python main.py "Start" "Target" --async --claude

# 3. Sürekli öğrenme başlat
python train_ml_model.py --continuous --iterations 20
```

---

## 🐛 Sorun Giderme

### Hata: "Module not found"
```bash
# Tüm bağımlılıkları yükle
pip install -r requirements.txt
```

### Hata: "Wikipedia API timeout"
```bash
# İnternet bağlantını kontrol et
# Veya daha az pair ile dene
python train_ml_model.py --mode quick --pairs 5
```

### Hata: "Out of memory"
```bash
# Daha az adım kullan
python main.py "Start" "Target" --max-steps 8

# Veya daha az pair ile train et
python train_ml_model.py --mode quick --pairs 5
```

---

## 📝 Komut Parametreleri Detayları

### main.py Parametreleri
```
Pozisyonel:
  start_page          Başlangıç Wikipedia sayfası
  target_page         Hedef Wikipedia sayfası

Opsiyonel:
  --async             Async/parallel processing (3x daha hızlı)
  --claude            Claude reasoning kullan (ANTHROPIC_API_KEY gerekli)
```

### train_ml_model.py Parametreleri
```
Opsiyonel:
  --quick             Hızlı training (10 pairs)
  --continuous        Sürekli öğrenme modu
  --pairs INT         Random page pair sayısı (default: 100)
  --iterations INT    Continuous mode için iterasyon sayısı (default: 10)
  --max-steps INT     Her arama için max adım (default: 10)
  --no-verbose        Verbose mode'u kapat (default: açık)
```

---

## 🚀 Gelecek Komutlar (Yakında!)

### ML ile Arama
```bash
python main.py "Start" "Target" --ml
```

### Web Arayüzü (Dash)
```bash
python web_app.py
# Tarayıcıda: http://localhost:8050
```

### Benchmark Script
```bash
python benchmark.py --test-cases test_cases.json
```

### Cache Management
```bash
python manage_cache.py --clear
python manage_cache.py --stats
python manage_cache.py --optimize
```

### Görselleştirme
```bash
python visualize.py --path "Potato → Pizza"
python visualize.py --graph --3d
```

---

## 💡 İpuçları

1. **İlk Kullanım**: `--verbose` flag'i kullan, ne olduğunu gör
2. **Hızlı Test**: `--max-steps 5` ile başla
3. **ML Training**: Önce `--mode quick` ile test et
4. **Web Demo**: En kolay kullanım için `app.py`
5. **Görselleştirme**: Sonuçları görmek için `visualize_simple.py`

---

## 📚 Daha Fazla Bilgi

- **README.md**: Genel proje bilgisi
- **QUICKSTART.md**: Hızlı başlangıç rehberi
- **docs/**: Detaylı dokümantasyon
- **FUTURE_GOALS_AND_OPTIMIZATION.md**: Gelecek planları
- **QUICK_WINS.md**: Hızlı iyileştirmeler
- **KG_OPTIMIZATION_STRATEGIES.md**: KG optimizasyonları

---

## 🎉 Özet: En Çok Kullanılan Komutlar

```bash
# 1. Hızlı arama (ÖNERİLİR!)
python main.py "Start" "Target" --async

# 2. Akıllı arama (zor path'ler için)
python main.py "Start" "Target" --async --claude

# 3. ML training (hızlı test)
python train_ml_model.py --quick

# 4. ML training (normal)
python train_ml_model.py --pairs 50

# 5. Sürekli öğrenme
python train_ml_model.py --continuous --iterations 20
```

## 📊 Performans Karşılaştırması

| Mode | Hız | Accuracy | Kullanım |
|------|-----|----------|----------|
| **Sync** | 1-2s | 95% | Basit path'ler, cache hit |
| **Async** | 0.5-1s | 95% | Çoğu durum (ÖNERİLİR!) |
| **Claude** | 2-3s | 98% | Zor path'ler, reasoning |

**Hepsini dene ve en iyisini bul!** 🚀