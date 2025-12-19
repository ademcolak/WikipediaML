# 🏗️ WikipediaML Mimari

## 📋 Genel Bakış

Proje **standart, tutarlı ve genişletilebilir** bir mimariye sahip. 10K+ edge milestone'u ile **Hybrid Navigator** sistemi devreye girdi.

## 🎯 Temel Prensipler

### 1. Tek Sorumluluk (Single Responsibility)
Her modül tek bir işten sorumlu:
- `TrainingPipeline`: Eğitim workflow'u
- `TrainingStrategies`: Farklı eğitim stratejileri
- `KnowledgeGraph`: Graph yönetimi
- `SemanticNavigator`: Path bulma

### 2. Standart Workflow
Tüm eğitim işlemleri aynı adımları takip eder:

```
1. Setup      → Navigator, graph hazırla
2. Train      → Eğitim döngüsü
3. Save       → Graph'ı kaydet
4. Backup     → Yedek al
5. Cleanup    → Geçici dosyaları temizle
6. Finalize   → İstatistikleri göster
```

### 3. Genişletilebilirlik
Yeni strateji eklemek çok kolay:

```python
class MyCustomStrategy(TrainingPipeline):
    def _get_next_pair(self, iteration: int) -> Tuple[str, str]:
        # Kendi mantığınız
        return ("Start", "Target")
```

## 📁 Yeni Dosya Yapısı

```
WikipediaML/
├── train.py                      # 🆕 TEK ENTRY POINT
│
├── src/
│   ├── training_pipeline.py     # 🆕 Abstract base class
│   ├── training_strategies.py   # 🆕 Farklı stratejiler
│   ├── knowledge_graph.py        # ✅ Mevcut (düzeltildi)
│   ├── semantic_navigator.py     # ✅ Mevcut
│   ├── embedder.py               # ✅ Mevcut
│   ├── scraper.py                # ✅ Mevcut
│   ├── async_scraper.py          # ✅ Mevcut
│   └── link_filter.py            # ✅ Mevcut
│
├── merge_graphs.py               # ✅ Mevcut (geliştirildi)
├── main.py                       # ✅ Mevcut (path bulma)
│
└── [ESKİ DOSYALAR]
    ├── auto_train.py             # ⚠️ Deprecated
    ├── auto_train_dynamic.py     # ⚠️ Deprecated
    ├── auto_train_parallel.py    # ⚠️ Deprecated
    ├── auto_train_strategic.py   # ⚠️ Deprecated
    └── start_parallel.sh         # ⚠️ Deprecated
```

## 🚀 Kullanım

### Basit Kullanım

```bash
# Stratejik eğitim (popüler sayfalar)
python train.py --strategy strategic --workers 3 --iterations 100

# Rastgele eğitim (çeşitlilik)
python train.py --strategy random --workers 3 --iterations 100

# Hibrit eğitim (70% stratejik, 30% rastgele)
python train.py --strategy hybrid --workers 3 --iterations 100
```

### Gelişmiş Kullanım

```bash
# Rate limiting ayarla (Wikipedia 429 önleme)
python train.py --strategy strategic --workers 2 --rate-limit 1.5 --max-concurrent 2

# Özel çift listesi
python train.py --strategy custom --file my_pairs.txt --workers 1

# Verbose mode
python train.py --strategy strategic --workers 3 --verbose
```

## 🏗️ Mimari Detayları

### TrainingPipeline (Abstract Base)

```python
class TrainingPipeline(ABC):
    def run(self):
        """Standart workflow"""
        self._setup()      # 1. Hazırlık
        self._train()      # 2. Eğitim
        self._save()       # 3. Kaydet
        self._backup()     # 4. Yedek
        self._cleanup()    # 5. Temizle
        self._finalize()   # 6. Sonuç
    
    @abstractmethod
    def _get_next_pair(self, iteration: int) -> Tuple[str, str]:
        """Alt sınıflar implement eder"""
        pass
```

### Stratejiler

#### 1. StrategicTraining
```python
# Popüler sayfalar arası (60 sayfa havuzu)
pipeline = StrategicTraining(config)
pipeline.run()

# Avantaj: Yüksek hit rate
# Dezavantaj: Sınırlı çeşitlilik
```

#### 2. RandomTraining
```python
# Wikipedia'dan tamamen rastgele
pipeline = RandomTraining(config)
pipeline.run()

# Avantaj: Çok fazla çeşitlilik
# Dezavantaj: Düşük hit rate
```

#### 3. HybridTraining
```python
# 70% stratejik, 30% rastgele
pipeline = HybridTraining(config, strategic_ratio=0.7)
pipeline.run()

# Avantaj: Denge (hit rate + çeşitlilik)
```

#### 4. CustomTraining
```python
# Kendi çift listeniz
pairs = [("Italy", "Rome"), ("Physics", "Einstein")]
pipeline = CustomTraining(config, pairs)
pipeline.run()
```

### Konfigürasyon

```python
config = TrainingConfig(
    worker_id=1,              # Worker ID
    num_workers=3,            # Toplam worker
    num_iterations=100,       # Kaç çift
    rate_limit_delay=1.0,     # Rate limiting (saniye)
    max_concurrent=2,         # Paralel istek sayısı
    use_graph=True,           # KG kullan
    use_async=True,           # Async scraper
    verbose=False             # Detaylı log
)
```

## 🔧 Wikipedia Rate Limiting Çözümü

### Sorun
- Çok fazla paralel istek → 429 hatası
- 110. adımda Wikipedia engelliyor

### Çözüm
```python
# Önceki: 3 worker × 3 concurrent = 9 paralel istek ❌
# Yeni:    2 worker × 2 concurrent = 4 paralel istek ✅

python train.py --workers 2 --max-concurrent 2 --rate-limit 1.0
```

### Optimal Ayarlar

| Worker | Concurrent | Rate Limit | Sonuç |
|--------|------------|------------|-------|
| 2 | 2 | 1.0s | ✅ Güvenli |
| 3 | 2 | 1.0s | ✅ Güvenli |
| 3 | 3 | 1.5s | ⚠️ Dikkatli |
| 5 | 3 | 0.8s | ❌ 429 hatası |

## 📊 Doğruluk Beklentileri

### Gerçekçi Hedefler

| Edge Sayısı | Sistem | Doğruluk | Süre |
|-------------|--------|----------|------|
| 1,000 | Semantic | %20-30 | 1 gün |
| 5,000 | Semantic | %40-50 | 1 hafta |
| 10,000 | **Hybrid (Embedding)** | **%70-80** | 2 hafta |
| 25,000 | **Hybrid (Embedding)** | **%75-85** | 1 ay |
| 50,000 | **Hybrid + LLM** | **%85-90** | 2-3 ay |

### 10K+ Edge Milestone 🎉

- **Hybrid Navigator** devreye girer
- 3 katmanlı sistem: KG → Embedding → LLM
- %70-80 doğruluk hedefi
- Maliyet kontrolü ile LLM kullanımı

### Neden %100 İmkansız?

- Wikipedia: ~6 milyon sayfa
- Olası path: Milyarlarca
- 50,000 edge = %0.0008 coverage
- **%85-90 mükemmel bir sonuç!**

## 🎯 Önerilen Strateji

### Kısa Vade (1 Hafta)

```bash
# Gün 1-3: Stratejik (temel oluştur)
python train.py --strategy strategic --workers 2 --iterations 200

# Gün 4-7: Rastgele (çeşitlilik ekle)
python train.py --strategy random --workers 2 --iterations 200
```

**Hedef:** 5,000 edge → %40-50 doğruluk

### Uzun Vade (1 Ay)

```bash
# Her gün hibrit eğitim
python train.py --strategy hybrid --workers 2 --iterations 300
```

**Hedef:** 20,000 edge → %65-70 doğruluk

## 🔄 Migration (Eski → Yeni)

### Eski Sistem
```bash
# Karmaşık, tutarsız
./start_parallel.sh
python auto_train_strategic.py --worker-id 1 --count 100 &
python merge_graphs.py --cleanup
```

### Yeni Sistem
```bash
# Basit, standart
python train.py --strategy strategic --workers 3 --iterations 100
```

**Avantajlar:**
- ✅ Tek komut
- ✅ Otomatik merge
- ✅ Standart workflow
- ✅ Rate limiting koruması
- ✅ Tutarlı backup

## 🧪 Test

```bash
# Küçük test (10 iteration)
python train.py --strategy strategic --workers 1 --iterations 10

# Orta test (50 iteration)
python train.py --strategy hybrid --workers 2 --iterations 50

# Tam eğitim (100+ iteration)
python train.py --strategy strategic --workers 2 --iterations 100
```

## 📝 Notlar

1. **Eski scriptler hala çalışır** ama deprecated
2. **Yeni sistem kullanın**: `train.py`
3. **Rate limiting önemli**: 429 hatası önlenir
4. **Doğruluk beklentisi**: %70-80 maksimum (gerçekçi)
5. **Sürekli eğitim**: Günde 1-2 saat yeterli

## 🎉 Sonuç

Artık **profesyonel, ölçeklenebilir ve sürdürülebilir** bir sistem var!

- ✅ Standart mimari
- ✅ Tek entry point
- ✅ Genişletilebilir
- ✅ **Hybrid Navigator (10K+ edge için)** 🆕
- ✅ Rate limiting korumalı
- ✅ Otomatik backup/merge
- ✅ Tutarlı workflow

## 🆕 Hybrid Navigator (v5.2.0)

### Mimari

```
SemanticNavigator
    ├── HybridNavigator (10K+ edge için)
    │   ├── KnowledgeGraph (Tier 1: Fastest)
    │   ├── EmbeddingNavigator (Tier 2: Smart Filter)
    │   └── LLMNavigator (Tier 3: Best Selection)
    │
    ├── KnowledgeGraph (Klasik sistem)
    ├── Embedder (Semantic similarity)
    └── AsyncScraper (Hız)
```

### Kullanım

```bash
# Hybrid mode (Embedding only)
python main.py Italy Rome --hybrid

# Hybrid + LLM (en yüksek doğruluk)
python main.py Italy Rome --hybrid --llm

# Eğitim
python train_with_hybrid_nav.py --iterations 100 --use-llm
```

### Performans

- **10K edge:** %70-80 doğruluk, ~$1.50/100 query
- **25K edge:** %75-85 doğruluk, ~$0.70/100 query
- **50K edge:** %85-90 doğruluk, ~$0.30/100 query