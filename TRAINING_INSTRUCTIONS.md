# 🎓 ML Model Eğitim Talimatları

## 📋 Hazırlık Tamamlandı! ✅

Senin için her şey hazır. Şimdi sadece aşağıdaki adımları takip et:

---

## 🚀 Adım Adım Eğitim

### 1️⃣ Cache Dosyaları Hakkında

**Soru:** "Cache'de sadece JSON var, diğer dosyalar ne zaman oluşuyor?"

**Cevap:** 
- `training_history.json` - Şu anda var (training geçmişi)
- `ml_model.pkl` - Training sonrası oluşacak ✨
- `ml_scaler.pkl` - Training sonrası oluşacak ✨
- `embeddings_cache.pkl` - İlk arama sonrası oluşacak ✨
- `wiki_graph.pkl` - İlk arama sonrası oluşacak ✨
- `category_cache.pkl` - Kategori kullanımı sonrası oluşacak ✨

**Yani:** Training script'i çalıştırdığında otomatik olarak oluşacaklar!

---

### 2️⃣ Hazırladığım Dosyalar

#### ✅ `training_dataset.json` (50 kolay page çifti)
```json
{
  "pairs": [
    {"start": "Albert_Einstein", "target": "Physics"},
    {"start": "Pizza", "target": "Italian_cuisine"},
    {"start": "Dog", "target": "Animal"},
    ... (50 çift toplam)
  ]
}
```

**Özellikler:**
- ✅ 50 kolay Wikipedia page çifti
- ✅ Kategorilere göre organize
- ✅ Kolay → orta zorluk
- ✅ %70-80 başarı oranı bekleniyor

#### ✅ `train_ml_model_curated.py` (Yeni training script)
Bu script:
- Curated dataset'i kullanır
- Random page yerine hazır çiftleri kullanır
- Daha hızlı ve güvenilir
- Otomatik cache dosyaları oluşturur

---

### 3️⃣ Eğitimi Başlat

#### Seçenek A: Hızlı Test (İlk 10 çift - 15-20 dakika)
```bash
python train_ml_model_curated.py --limit 10
```

**Ne olacak:**
- 10 page çifti denenecek
- ~7-8 başarılı path bulunacak
- Cache dosyaları oluşacak
- Model eğitilecek (yeterli data varsa)

#### Seçenek B: Tam Eğitim (50 çift - 60-90 dakika) ⭐ ÖNERİLEN
```bash
python train_ml_model_curated.py
```

**Ne olacak:**
- 50 page çifti denenecek
- ~35-40 başarılı path bulunacak
- Tüm cache dosyaları oluşacak
- Model tam eğitilecek

#### Seçenek C: Sessiz Mod (Output az)
```bash
python train_ml_model_curated.py --no-verbose
```

---

### 4️⃣ Eğitim Sırasında Ne Göreceksin

```bash
$ python train_ml_model_curated.py --limit 10

============================================================
🤖 ML TRAINING WITH CURATED DATASET
============================================================
📁 Loading dataset: training_dataset.json
✅ Loaded 10 page pairs
Max steps: 10
============================================================

📦 Initializing components...
✅ SemanticNavigator initialized
✅ MLLinkScorer initialized
✅ SelfLearningTrainer initialized

============================================================
🎓 TRAINING WITH CURATED DATASET
============================================================
Processing 10 page pairs...
Estimated time: 15-30 minutes

────────────────────────────────────────────────────────────
Pair 1/10: Albert_Einstein → Physics

🔍 Searching: Albert_Einstein → Physics
   [Arama yapılıyor... 5-15 saniye]
✅ Path found: 2 steps
   Path: Albert_Einstein → Theoretical_physics → Physics

📊 Progress: 1/10
   Success rate: 100.0%
   Successful paths: 1
   Failed attempts: 0

────────────────────────────────────────────────────────────
Pair 2/10: Pizza → Italian_cuisine
...
```

---

### 5️⃣ Eğitim Tamamlandığında

```bash
============================================================
📊 FINAL STATISTICS
============================================================
Total attempts: 10
Successful: 8
Failed: 2
Success rate: 80.0%
Training time: 245.3s
ML model trained: True
Training samples: 16

✅ ML model is ready to use!
   Run: python main.py --ml <start> <target>

============================================================
💾 CACHE FILES GENERATED
============================================================
cache/ml_model.pkl          - Trained XGBoost model
cache/ml_scaler.pkl         - Feature scaler
cache/training_history.json - Training history
cache/embeddings_cache.pkl  - Semantic embeddings
cache/wiki_graph.pkl        - Knowledge graph
============================================================
```

---

### 6️⃣ Model'i Test Et

Eğitim tamamlandıktan sonra:

```bash
# ML mode ile arama yap
python main.py "Potato" "Pizza" --ml

# Async + ML (en hızlı)
python main.py "Potato" "Pizza" --async --ml
```

---

## 📊 Beklenen Sonuçlar

### İlk 10 Çift (Test)
- ⏱️ Süre: 15-20 dakika
- ✅ Başarı: 7-8 path
- 📈 Success rate: %70-80
- 🎯 Training samples: 14-16

### Tam 50 Çift (Önerilen)
- ⏱️ Süre: 60-90 dakika
- ✅ Başarı: 35-40 path
- 📈 Success rate: %70-80
- 🎯 Training samples: 70-80

---

## 🐛 Sorun Giderme

### Problem: "Dataset file not found"
**Çözüm:** `training_dataset.json` dosyasının proje root'unda olduğundan emin ol

### Problem: Çok yavaş
**Çözüm:** `--limit 10` ile test et, sonra tam eğitim yap

### Problem: Dondu gibi
**Çözüm:** Normal! Her pair 1-3 dakika sürüyor. CPU kullanımını kontrol et.

### Problem: Başarı oranı düşük
**Çözüm:** Normal, bazı page'ler zor olabilir. %60+ yeterli.

---

## ✅ Özet - Ne Yapmalısın?

### Hızlı Başlangıç (15-20 dakika):
```bash
python train_ml_model_curated.py --limit 10
```

### Tam Eğitim (60-90 dakika) - ÖNERİLEN:
```bash
python train_ml_model_curated.py
```

### Test:
```bash
python main.py "Potato" "Pizza" --ml
```

---

## 🎯 Sonuç

1. ✅ Dataset hazır (`training_dataset.json`)
2. ✅ Training script hazır (`train_ml_model_curated.py`)
3. ✅ Sadece komutu çalıştır
4. ✅ Cache dosyaları otomatik oluşacak
5. ✅ Model eğitilecek
6. ✅ Test edebilirsin

**Şimdi yapman gereken tek şey:**
```bash
python train_ml_model_curated.py
```

Komutu çalıştır ve bekle! ☕

---

**Not:** İlk kez çalıştırıyorsan `--limit 10` ile test et, sonra tam eğitim yap.

**Tahmini Süre:** 
- Test (10 çift): 15-20 dakika
- Tam (50 çift): 60-90 dakika

**Başarı Garantisi:** %70-80 başarı oranı bekleniyor! 🎉