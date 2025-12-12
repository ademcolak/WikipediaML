# 🎓 ML Model Eğitim Rehberi

## 🎯 Hedef

Wikipedia oyununu oynayan ML modelini eğitmek ve sürekli iyileştirmek.

---

## 🚀 Hızlı Başlangıç

### 1. Hızlı Test (5-10 dakika)

```bash
# İlk 10 çift ile test et
python train_ml_model_curated.py --limit 10
```

**Beklenen Sonuç:**
- Süre: 5-10 dakika
- Başarı oranı: %60-70
- Training samples: ~50-100

### 2. Tam Eğitim (30-60 dakika)

```bash
# Tüm dataset ile eğit (50 çift)
python train_ml_model_curated.py
```

**Beklenen Sonuç:**
- Süre: 30-60 dakika
- Başarı oranı: %70-80
- Training samples: ~500-1000

### 3. Büyük Dataset (2-3 saat)

```bash
# Büyük dataset ile eğit (100+ çift)
python train_ml_model_curated.py --dataset training_dataset_large.json
```

**Beklenen Sonuç:**
- Süre: 2-3 saat
- Başarı oranı: %75-85
- Training samples: ~2000-5000

---

## 📊 Training Dataset

### Curated Dataset (Önerilen)

**Dosya:** `training_dataset.json`

```json
{
  "pairs": [
    {
      "start": "Potato",
      "target": "Pizza",
      "difficulty": "easy",
      "expected_steps": 2
    },
    {
      "start": "Albert_Einstein",
      "target": "Physics",
      "difficulty": "easy",
      "expected_steps": 1
    }
  ]
}
```

**Özellikler:**
- 50 özenle seçilmiş çift
- Kolay → Orta → Zor
- Yüksek başarı oranı
- Hızlı eğitim

### Large Dataset

**Dosya:** `training_dataset_large.json`

```json
{
  "pairs": [
    // 100+ random çift
  ]
}
```

**Özellikler:**
- 100+ random çift
- Daha çeşitli
- Daha uzun eğitim
- Daha robust model

---

## 🎮 Training Süreci

### Adım Adım

```
1. Dataset Yükle
   └─> training_dataset.json

2. Her Çift İçin:
   ├─> Path bul (semantic search)
   ├─> Başarılıysa:
   │   ├─> Path'i kaydet
   │   ├─> Features extract et
   │   └─> Training data'ya ekle
   └─> Başarısızsa:
       └─> Failed attempt kaydet

3. Her 10 Çiftte Bir:
   ├─> Training history kaydet
   └─> Progress göster

4. Eğitim Bitince:
   ├─> ML model eğit (XGBoost)
   ├─> Model kaydet (ml_model.pkl)
   ├─> Scaler kaydet (ml_scaler.pkl)
   └─> Statistics göster
```

### Training Output

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
Pair 1/10: Potato → Pizza
🔍 Searching path...
✅ Path found: Potato → Tomato → Pizza (2 steps)
⏱️  Time: 1.2s

📊 Progress: 1/10
   Success rate: 100.0%
   Successful paths: 1
   Failed attempts: 0

────────────────────────────────────────────────────────────
Pair 2/10: Albert_Einstein → Physics
🔍 Searching path...
✅ Path found: Albert_Einstein → Physics (1 step)
⏱️  Time: 0.8s

📊 Progress: 2/10
   Success rate: 100.0%
   Successful paths: 2
   Failed attempts: 0

...

============================================================
🎓 TRAINING ML MODEL
============================================================
✅ Sufficient training data: 8 successful paths
🔄 Training ML model...
✅ ML model trained successfully!

============================================================
📊 FINAL STATISTICS
============================================================
Total attempts: 10
Successful: 8
Failed: 2
Success rate: 80.0%
Training time: 245.3s
ML model trained: True
Training samples: 156

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

## 📁 Oluşturulan Dosyalar

### cache/ Klasörü

```
cache/
├── ml_model.pkl              # XGBoost model
├── ml_scaler.pkl             # StandardScaler
├── training_history.json     # Training log
├── embeddings_cache.pkl      # Embedding cache
└── wiki_graph.pkl            # Knowledge graph
```

### training_history.json

```json
{
  "total_attempts": 10,
  "successful_attempts": 8,
  "failed_attempts": 2,
  "success_rate": 80.0,
  "total_training_time": 245.3,
  "ml_model_trained": true,
  "ml_training_samples": 156,
  "paths": [
    {
      "start": "Potato",
      "target": "Pizza",
      "path": ["Potato", "Tomato", "Pizza"],
      "steps": 2,
      "time": 1.2,
      "success": true
    }
  ]
}
```

---

## 🎯 ML Model Detayları

### Features (10 adet)

```python
1. semantic_similarity      # Cosine similarity
2. embedding_distance       # Euclidean distance
3. text_overlap            # Jaccard similarity
4. char_overlap            # Character overlap
5. pagerank                # Graph centrality
6. degree                  # Node degree
7. betweenness             # Betweenness centrality
8. link_position           # Position in page
9. link_depth              # HTML depth
10. category_overlap       # Category similarity (optional)
```

### Model: XGBoost

```python
XGBClassifier(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    objective='binary:logistic'
)
```

**Neden XGBoost?**
- Hızlı training
- Yüksek accuracy
- Feature importance
- Robust

---

## 🔧 Training Parametreleri

### Komut Satırı Seçenekleri

```bash
# Dataset seçimi
--dataset FILE              # Dataset dosyası (default: training_dataset.json)

# Limit
--limit N                   # İlk N çift ile eğit (test için)

# Max steps
--max-steps N               # Maximum adım sayısı (default: 10)

# Verbose
--no-verbose                # Sessiz mod (daha hızlı)
```

### Örnekler

```bash
# Hızlı test
python train_ml_model_curated.py --limit 5 --max-steps 5

# Sessiz mod
python train_ml_model_curated.py --no-verbose

# Büyük dataset
python train_ml_model_curated.py --dataset training_dataset_large.json

# Custom parametreler
python train_ml_model_curated.py --limit 20 --max-steps 8
```

---

## ☁️ Cloud Training

### Google Colab (Önerilen - Ücretsiz!)

#### 1. Notebook Hazırla

`WikipediaML_Training.ipynb` dosyasını kullan.

#### 2. Colab'a Yükle

1. https://colab.research.google.com/ git
2. File → Upload notebook
3. `WikipediaML_Training.ipynb` seç

#### 3. GPU Aktif Et

1. Runtime → Change runtime type
2. Hardware accelerator → GPU
3. Save

#### 4. Çalıştır

1. Runtime → Run all
2. 45-60 dakika bekle
3. Model dosyalarını indir

#### 5. Model İndir

```python
from google.colab import files

# Model dosyalarını indir
files.download('cache/ml_model.pkl')
files.download('cache/ml_scaler.pkl')
files.download('cache/training_history.json')
```

### GCP (Güçlü Makine)

```bash
# 1. VM oluştur
gcloud compute instances create wikipediaml-trainer \
  --zone=us-central1-a \
  --machine-type=n1-standard-4 \
  --preemptible

# 2. SSH bağlan
gcloud compute ssh wikipediaml-trainer

# 3. Projeyi kur
git clone <repo-url>
cd WikipediaML
pip install -r requirements.txt

# 4. Eğitimi başlat
python train_ml_model_curated.py

# 5. Model indir
gcloud compute scp wikipediaml-trainer:~/WikipediaML/cache/*.pkl .
```

Detaylar için: [CLOUD_GUIDE.md](CLOUD_GUIDE.md)

---

## 📊 Model Performansı

### Başarı Oranları

```
Dataset Size → Success Rate
10 çift     → %60-70
50 çift     → %70-80
100 çift    → %75-85
500 çift    → %80-90
```

### Accuracy Metrikleri

```
Baseline (Semantic only):  %95
ML Model (10 features):    %98
Improvement:               +%3
```

### Training Samples

```
Başarılı path başına:
- Ortalama 20-30 training sample
- Her link bir sample
- Positive + Negative samples

50 başarılı path:
- ~1000-1500 training sample
- Yeterli model eğitimi için
```

---

## 🐛 Sorun Giderme

### Problem: Training çok yavaş

**Çözüm 1:** Limit kullan
```bash
python train_ml_model_curated.py --limit 10
```

**Çözüm 2:** Max steps azalt
```bash
python train_ml_model_curated.py --max-steps 5
```

**Çözüm 3:** Verbose kapat
```bash
python train_ml_model_curated.py --no-verbose
```

### Problem: Başarı oranı düşük

**Çözüm 1:** Kolay dataset kullan
```bash
python train_ml_model_curated.py  # Curated dataset
```

**Çözüm 2:** Max steps artır
```bash
python train_ml_model_curated.py --max-steps 15
```

**Çözüm 3:** Daha fazla çift eğit
```bash
python train_ml_model_curated.py --dataset training_dataset_large.json
```

### Problem: Model eğitilmiyor

**Sebep:** Yetersiz training data (< 10 başarılı path)

**Çözüm:** Daha fazla çift eğit
```bash
python train_ml_model_curated.py --limit 20
```

### Problem: Out of memory

**Çözüm 1:** Batch size küçült (kod değişikliği gerekli)

**Çözüm 2:** Cloud'da eğit (daha fazla RAM)

**Çözüm 3:** Cache temizle
```bash
rm -rf cache/*.pkl
```

---

## 🎯 Best Practices

### 1. İlk Test

```bash
# Önce küçük test yap
python train_ml_model_curated.py --limit 5

# Çalışıyorsa tam eğitim
python train_ml_model_curated.py
```

### 2. Checkpoint Kullan

Training her 10 çiftte bir otomatik kayıt yapar:
- `cache/training_history.json`
- Kesintide kaldığı yerden devam edebilir

### 3. Cloud Kullan

Uzun eğitimler için:
- Google Colab (ücretsiz, GPU)
- GCP ($300 kredi)
- Yerel bilgisayarı yorma

### 4. Model Versioning

```bash
# Her eğitimde model'i yedekle
cp cache/ml_model.pkl cache/ml_model_v1.pkl
cp cache/ml_model.pkl cache/ml_model_v2.pkl
```

### 5. Performance Tracking

```bash
# Training history'yi sakla
cp cache/training_history.json logs/training_$(date +%Y%m%d).json
```

---

## 📈 Sürekli İyileştirme

### Strateji

```
1. İlk Eğitim (50 çift)
   └─> Baseline model

2. Model Kullan
   └─> Yeni path'ler bul

3. Yeni Path'leri Ekle
   └─> Training data büyür

4. Model Güncelle
   └─> Daha iyi model

5. Tekrarla
   └─> Sürekli iyileşme!
```

### Hedefler

```
1 hafta:  100 path öğren
1 ay:     1,000 path öğren
3 ay:     10,000 path öğren
1 yıl:    100,000+ path öğren
```

---

## 🎓 Özet

### Hızlı Başlangıç

```bash
# 1. Test et (5-10 dakika)
python train_ml_model_curated.py --limit 10

# 2. Tam eğitim (30-60 dakika)
python train_ml_model_curated.py

# 3. Model kullan
python main.py --ml Potato Pizza
```

### Başarı Kriterleri

- ✅ 10+ başarılı path
- ✅ Model eğitildi (ml_model.pkl)
- ✅ %70+ başarı oranı
- ✅ 500+ training sample

### Sonraki Adımlar

1. Model'i kullan (`--ml` flag)
2. Yeni path'ler öğren
3. Model'i güncelle
4. Performansı izle

---

**Versiyon:** 5.0.0  
**Son Güncelleme:** 12 Aralık 2024  
**Durum:** Aktif Geliştirme