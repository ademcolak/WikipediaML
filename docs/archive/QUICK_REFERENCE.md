# ⚡ WikipediaML - Hızlı Referans Kılavuzu

## 🚀 En Çok Kullanılan Komutlar

### Temel Arama
```bash
# Hızlı arama (ÖNERİLİR!)
python main.py "Potato" "Pizza" --async

# Basit arama
python main.py "Potato" "Pizza"

# Akıllı arama (Claude)
python main.py "Potato" "Pizza" --async --claude
```

### ML Training
```bash
# Hızlı test (10 pair, ~5-10 dakika)
python train_ml_model.py --quick

# Normal (50 pair, ~30-60 dakika)
python train_ml_model.py --pairs 50

# Sürekli öğrenme
python train_ml_model.py --continuous --iterations 20
```

---

## 📝 Argüman Referansı

### main.py
```bash
python main.py <start> <target> [--async] [--claude]

Pozisyonel:
  start_page          Başlangıç Wikipedia sayfası
  target_page         Hedef Wikipedia sayfası

Opsiyonel:
  --async             Async/parallel processing (3x daha hızlı)
  --claude            Claude reasoning (ANTHROPIC_API_KEY gerekli)
```

### train_ml_model.py
```bash
python train_ml_model.py [--quick] [--continuous] [--pairs N] [--iterations N] [--no-verbose]

Opsiyonel:
  --quick             Hızlı training (10 pairs)
  --continuous        Sürekli öğrenme modu
  --pairs N           Random page pair sayısı (default: 100)
  --iterations N      Continuous mode iterasyon (default: 10)
  --max-steps N       Her arama için max adım (default: 10)
  --no-verbose        Verbose mode'u kapat (default: açık)
```

---

## 🎯 Kullanım Senaryoları

### Senaryo 1: İlk Kullanım
```bash
# 1. Basit bir arama yap
python main.py "Computer" "Internet"

# 2. Async mode ile dene (daha hızlı)
python main.py "Computer" "Internet" --async
```

### Senaryo 2: ML Model Eğitimi
```bash
# 1. Hızlı test
python train_ml_model.py --quick

# 2. Başarılıysa normal training
python train_ml_model.py --pairs 50

# 3. Sürekli öğrenme (opsiyonel)
python train_ml_model.py --continuous --iterations 20
```

### Senaryo 3: Zor Path'ler
```bash
# 1. Async ile dene
python main.py "Porsche" "Serik_Akhmetov_Government" --async

# 2. Başarısızsa Claude ekle
python main.py "Porsche" "Serik_Akhmetov_Government" --async --claude
```

---

## 🔧 Sayfa İsimleri

Wikipedia URL'indeki `/wiki/` sonrası kısmı kullan:

```
✅ Doğru:
  Python_(programming_language)
  United_States
  Albert_Einstein

❌ Yanlış:
  Python (programming language)
  United States
  Albert Einstein
```

---

## 📊 Performans Karşılaştırması

| Mode | Hız | Accuracy | Kullanım |
|------|-----|----------|----------|
| **Sync** | 1-2s | 95% | Basit path'ler |
| **Async** | 0.5-1s | 95% | Çoğu durum (ÖNERİLİR!) |
| **Claude** | 2-3s | 98% | Zor path'ler |

---

## 🐛 Hata Çözümleri

### "Module not found"
```bash
pip install -r requirements.txt
```

### "ANTHROPIC_API_KEY not found"
```bash
export ANTHROPIC_API_KEY='your-api-key'
```

### "unrecognized arguments"
```bash
# Yanlış:
python train_ml_model.py --mode quick --verbose

# Doğru:
python train_ml_model.py --quick
```

---

## 📚 Daha Fazla Bilgi

- **COMMANDS.md** - Tüm komutlar detaylı
- **PROJECT_STATUS.md** - Proje durumu
- **README.md** - Genel bilgi
- **QUICKSTART.md** - Hızlı başlangıç

---

## 💡 İpuçları

1. **İlk kullanım**: `--async` flag'i kullan
2. **ML training**: Önce `--quick` ile test et
3. **Zor path'ler**: `--claude` ekle
4. **Verbose kapatma**: `--no-verbose` kullan
5. **Graph cache**: Aynı path'i tekrar çalıştır (anında!)

---

**Versiyon:** 3.4.0  
**Son Güncelleme:** 10 Aralık 2024