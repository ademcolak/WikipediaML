# 🎓 ML Model Training Rehberi

## ⚠️ Önemli: Training Süreci Hakkında

### "Derinlik 1'de Kaldı" - Normal mi?

**EVET, NORMAL!** 🎯

### Özel Durum: "🔍 Backward: Raven_Crown" Satırında Durdu

**Bu da NORMAL!** Şu anda:
1. ✅ 25 forward link buldu
2. ✅ 156 backward link buldu
3. 🔄 **Şimdi embedding'leri hesaplıyor** (156 link × 100ms = 15-30 saniye)
4. ⏳ Hiç output vermiyor - ama çalışıyor!

**Ne Oluyor:**
```
🔍 Backward: Raven_Crown
   156 yeni link
   
   [BURASI SESSIZ - AMA ÇALIŞIYOR!]
   ↓
   Embedding hesaplama: 15-30 saniye
   ↓
   Sonraki derinliğe geçecek
```

**Nasıl Anlarım Çalıştığını:**
- CPU kullanımı %50-100 (Activity Monitor / Task Manager)
- Python process aktif
- Bellek kullanımı artıyor
- 15-30 saniye sonra yeni output gelecek

Training script şu adımları yapıyor:
```
1. Random Wikipedia page çek (0.5-1s)
2. İkinci random page çek (0.5-1s)
3. Path ara (5-15s) ← BURASI UZUN SÜRÜYOR!
4. Sonucu kaydet
5. Tekrarla...
```

### Ne Görüyorsun:
```bash
$ python train_ml_model.py --quick

🤖 SELF-SUPERVISED ML TRAINING
Mode: Single
Random pairs: 10
Max steps: 10

📦 Initializing components...
✅ SemanticNavigator initialized
✅ MLLinkScorer initialized
✅ SelfLearningTrainer initialized

🤖 SELF-SUPERVISED LEARNING
Generating training data from 10 random page pairs...

────────────────────────────────────────────────────────────
Pair 1/10
   ✅ Random page: Some_Page
   ✅ Random page: Another_Page

🔍 Searching: Some_Page → Another_Page
   [BURASI UZUN SÜRER - 5-15 SANİYE!]
```

### Dondu mu, Çalışıyor mu?

**Çalışıyor!** Arka planda şunlar oluyor:
1. Wikipedia'dan link'leri çekiyor
2. Semantic similarity hesaplıyor
3. Path arıyor
4. Her adımda 50-100 link işliyor

**Beklenen Süreler:**
- **Quick mode (10 pair)**: 5-10 dakika
- **Normal (50 pair)**: 30-60 dakika
- **Continuous (100+ pair)**: 2-3 saat

---

## 🚀 Hızlandırma İpuçları

### 1. Daha Az Pair Kullan
```bash
# Çok hızlı test (5 pair, ~2-3 dakika)
python train_ml_model.py --pairs 5

# Hızlı test (10 pair, ~5-10 dakika)
python train_ml_model.py --quick
```

### 2. Max Steps Azalt
```bash
# Daha az adım = daha hızlı (ama daha az başarı)
python train_ml_model.py --quick --max-steps 5
```

### 3. Verbose Kapat (Daha Hızlı Görünür)
```bash
# Daha az output = daha hızlı görünür
python train_ml_model.py --quick --no-verbose
```

---

## 📊 İlerleme Takibi

### Normal Output (Verbose Açık)
```bash
Pair 1/10
   ✅ Random page: Potato
   ✅ Random page: Pizza

🔍 Searching: Potato → Pizza
   Step 1: Potato
   Step 2: Tomato
   Step 3: Pizza
✅ Path found: 3 steps

📊 Progress: 1/10
   Success rate: 100.0%
   Successful paths: 1

────────────────────────────────────────────────────────────
Pair 2/10
   ...
```

### Sessiz Output (Verbose Kapalı)
```bash
Pair 1/10 ✅
Pair 2/10 ✅
Pair 3/10 ❌
Pair 4/10 ✅
...
```

---

## 🐛 Sorun Giderme

### Problem 1: Çok Yavaş
**Çözüm:**
```bash
# Daha az pair kullan
python train_ml_model.py --pairs 5

# Max steps azalt
python train_ml_model.py --quick --max-steps 5
```

### Problem 2: Dondu Gibi Görünüyor
**Kontrol Et:**
1. Terminal'de output var mı? (verbose açıksa göreceksin)
2. CPU kullanımı var mı? (Activity Monitor / Task Manager)
3. Network trafiği var mı? (Wikipedia API çağrıları)

**Eğer bunlar varsa**: Çalışıyor, bekle! ⏳

### Problem 3: Gerçekten Dondu
**Çözüm:**
```bash
# Ctrl+C ile durdur
# Script progress'i kaydeder

# Tekrar başlat (daha az pair ile)
python train_ml_model.py --pairs 5
```

---

## ⏱️ Beklenen Süreler

### Quick Mode (10 pair)
```
Başlangıç: 0s
Pair 1: 10s
Pair 2: 20s
Pair 3: 30s
...
Pair 10: 100s (~1.5 dakika)
Training: 110s (~2 dakika)
Toplam: ~5-10 dakika
```

### Normal Mode (50 pair)
```
50 pair × 10s = 500s (~8 dakika)
Training: 30s
Toplam: ~30-60 dakika
```

### Continuous Mode (10 iterations × 10 pair)
```
100 pair × 10s = 1000s (~17 dakika)
Training: 10 × 30s = 300s (~5 dakika)
Toplam: ~2-3 saat
```

---

## 💡 Öneriler

### İlk Kez Kullanıyorsan
```bash
# 1. Çok hızlı test (5 pair, ~2-3 dakika)
python train_ml_model.py --pairs 5

# 2. Başarılıysa quick mode (10 pair, ~5-10 dakika)
python train_ml_model.py --quick

# 3. Başarılıysa normal mode (50 pair, ~30-60 dakika)
python train_ml_model.py --pairs 50
```

### Sabırsızsan
```bash
# En hızlı test (3 pair, ~1-2 dakika)
python train_ml_model.py --pairs 3 --max-steps 5 --no-verbose
```

### Zamanın Varsa
```bash
# Gece boyunca çalıştır (100 pair, ~2-3 saat)
python train_ml_model.py --pairs 100
```

---

## 🎯 Başarı Kriterleri

### Minimum Gereksinimler
```
Başarılı path'ler: En az 10
Success rate: En az %30
Training samples: En az 20
```

### İyi Sonuçlar
```
Başarılı path'ler: 30+
Success rate: %50+
Training samples: 60+
```

### Mükemmel Sonuçlar
```
Başarılı path'ler: 50+
Success rate: %70+
Training samples: 100+
```

---

## 📝 Training Sırasında Ne Yapmalı?

### Opsiyonlar:
1. **Bekle**: Terminal'i aç bırak, başka işlerle uğraş
2. **İzle**: Verbose açıksa progress'i izle
3. **Arka Planda Çalıştır**: 
   ```bash
   nohup python train_ml_model.py --quick > training.log 2>&1 &
   tail -f training.log  # Log'u izle
   ```

---

## 🔍 Debug Mode

### Detaylı Output İçin
```bash
# Verbose açık (default)
python train_ml_model.py --quick

# Her adımı görmek için
# (semantic_navigator.py'de verbose=True)
```

### Log Dosyasına Kaydet
```bash
python train_ml_model.py --quick > training.log 2>&1
tail -f training.log  # Başka terminal'de izle
```

---

## ✅ Training Tamamlandı - Ne Yapmalı?

### Sonuçları Kontrol Et
```bash
# Training history dosyasını kontrol et
cat training_history.json

# Model dosyasını kontrol et
ls -lh ml_model.pkl ml_scaler.pkl
```

### Model'i Test Et
```bash
# ML mode ile arama yap (yakında!)
python main.py "Start" "Target" --ml
```

---

## 🎓 Özet

**"Derinlik 1'de kaldı" = Normal!**

- ✅ Script çalışıyor
- ✅ Arka planda path arıyor
- ✅ Her pair 5-15 saniye sürüyor
- ✅ 10 pair için 5-10 dakika bekle
- ✅ Sabırlı ol! ⏳

**Hızlandırma:**
- Daha az pair: `--pairs 5`
- Daha az adım: `--max-steps 5`
- Sessiz mod: `--no-verbose`

**İpucu:** İlk kez kullanıyorsan `--pairs 5` ile başla!

---

**Versiyon:** 3.4.0  
**Son Güncelleme:** 10 Aralık 2024