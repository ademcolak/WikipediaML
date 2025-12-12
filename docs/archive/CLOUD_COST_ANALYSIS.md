# 💰 Cloud Training Maliyet Analizi

## 📊 Gerçekçi Maliyet Hesaplaması

### Projenizin Özellikleri
- **Dataset:** 50 Wikipedia sayfa çifti
- **Tahmini Süre:** 2-3 saat (CPU), 1-2 saat (GPU)
- **Gerekli Kaynaklar:** 4 CPU, 16GB RAM (minimum)

---

## 💵 Platform Karşılaştırması

### 1. Google Cloud Platform (GCP) - **ÖNERİLEN**

#### Neden GCP?
- ✅ **$300 ücretsiz kredi** (yeni kullanıcılar için)
- ✅ Kredi kartı gerekli ama **otomatik ücretlendirme YOK**
- ✅ Kredi bitince **otomatik durur**
- ✅ 90 gün geçerli
- ✅ Türkiye'den kullanılabilir

#### Maliyet (Preemptible VM)
```
Machine: n1-standard-4 (4 vCPU, 15GB RAM)
Preemptible: $0.04/saat
Süre: 3 saat
TOPLAM: $0.12 (₺3.60)
```

#### Maliyet (Normal VM)
```
Machine: n1-standard-4
Normal: $0.19/saat
Süre: 3 saat
TOPLAM: $0.57 (₺17.10)
```

**SONUÇ:** $300 kredi ile **2,500 eğitim** yapabilirsiniz! 🎉

---

### 2. AWS (Amazon Web Services)

#### Avantajlar
- ✅ Spot instances ile ucuz
- ✅ Geniş hizmet yelpazesi
- ✅ 12 ay ücretsiz tier (sınırlı)

#### Dezavantajlar
- ❌ Kredi kartı gerekli
- ❌ Otomatik ücretlendirme VAR
- ❌ Unutursanız para gider

#### Maliyet (Spot Instance)
```
Instance: t3.xlarge (4 vCPU, 16GB RAM)
Spot: $0.05/saat
Süre: 3 saat
TOPLAM: $0.15 (₺4.50)
```

#### Maliyet (Normal Instance)
```
Instance: t3.xlarge
Normal: $0.17/saat
Süre: 3 saat
TOPLAM: $0.51 (₺15.30)
```

**ÖNEMLİ:** Instance'ı kapatmayı unutursanız:
- 1 gün: $4.08 (₺122)
- 1 hafta: $28.56 (₺857)
- 1 ay: $122.40 (₺3,672)

---

### 3. Vast.ai - **EN UCUZ**

#### Avantajlar
- ✅ **En ucuz GPU** ($0.10-0.30/saat)
- ✅ Kredi kartı veya kripto
- ✅ Saatlik ödeme
- ✅ Otomatik kapatma

#### Dezavantajlar
- ❌ Topluluk GPU'ları (güvenilirlik?)
- ❌ Bazen yavaş olabilir
- ❌ Kurulum biraz karmaşık

#### Maliyet
```
GPU: RTX 3060 (örnek)
Fiyat: $0.15/saat
Süre: 2 saat (GPU ile daha hızlı)
TOPLAM: $0.30 (₺9.00)
```

---

### 4. Ücretsiz Alternatifler

#### Google Colab (Ücretsiz)
- ✅ **Tamamen ücretsiz**
- ✅ GPU desteği
- ✅ Jupyter notebook
- ❌ 12 saat limit
- ❌ Bazen yavaş
- ❌ Dosya yükleme gerekli

#### Kaggle Notebooks (Ücretsiz)
- ✅ **Tamamen ücretsiz**
- ✅ GPU desteği (30 saat/hafta)
- ✅ Dataset desteği
- ❌ Internet erişimi sınırlı

---

## 🎯 Önerilerim

### Senaryo 1: Hiç Para Harcamak İstemiyorum
**Çözüm:** Google Colab veya Kaggle

**Adımlar:**
1. Colab'a git: https://colab.research.google.com/
2. Yeni notebook oluştur
3. GPU'yu aktif et (Runtime → Change runtime type → GPU)
4. Kodları yükle ve çalıştır

**Artılar:**
- ✅ Tamamen ücretsiz
- ✅ Hemen başla
- ✅ Kredi kartı gerekmez

**Eksiler:**
- ❌ 12 saat limit
- ❌ Dosya yükleme gerekli
- ❌ Bazen yavaş

---

### Senaryo 2: Minimum Maliyet (₺3-10)
**Çözüm:** GCP Preemptible VM

**Neden?**
- $300 ücretsiz kredi
- Otomatik ücretlendirme YOK
- Kredi bitince durur
- Türkiye'den kullanılabilir

**Maliyet:** $0.12 (₺3.60) - ama $300 kredi ile BEDAVA!

**Adımlar:**
1. GCP hesabı aç (kredi kartı gerekli ama ücret YOK)
2. $300 kredi al
3. VM oluştur (Preemptible)
4. Eğitimi çalıştır
5. VM'i kapat

---

### Senaryo 3: Hızlı ve Güvenilir (₺15-50)
**Çözüm:** AWS Spot Instance + Otomatik Kapatma

**Neden?**
- Hızlı ve güvenilir
- Spot ile ucuz
- Otomatik kapatma ile güvenli

**Maliyet:** $0.15-0.50 (₺4.50-15)

**Adımlar:**
1. AWS hesabı aç
2. Spot instance başlat
3. Otomatik kapatma ayarla (2-3 saat)
4. Eğitimi çalıştır
5. Model indir

---

## 🛡️ Güvenlik Önlemleri

### 1. Otomatik Kapatma Ayarla
```bash
# AWS - 3 saat sonra otomatik kapat
aws ec2 stop-instances --instance-ids i-xxx

# Cron job ile
echo "0 */3 * * * aws ec2 stop-instances --instance-ids i-xxx" | crontab -
```

### 2. Billing Alarms Kur
```bash
# AWS - $5 üstü uyarı
aws cloudwatch put-metric-alarm \
  --alarm-name billing-alarm \
  --alarm-description "Alert when charges exceed $5" \
  --metric-name EstimatedCharges \
  --threshold 5
```

### 3. Budget Limiti Koy
- AWS: Budgets → Create budget → $10 limit
- GCP: Billing → Budgets → $10 limit

### 4. Her Gün Kontrol Et
- AWS Console → Billing Dashboard
- GCP Console → Billing
- Email uyarılarını aç

---

## 📋 Adım Adım Plan

### Aşama 1: Ücretsiz Test (0 TL)
1. **Google Colab** kullan
2. 10 çift ile test et
3. Başarılı olursa devam et

**Süre:** 30 dakika
**Maliyet:** ₺0

---

### Aşama 2: GCP ile Tam Eğitim ($300 kredi)
1. GCP hesabı aç
2. $300 kredi al
3. Preemptible VM oluştur
4. 50 çift ile eğit
5. Model indir
6. VM'i kapat

**Süre:** 2-3 saat
**Maliyet:** $0.12 (₺3.60) - ama kredi ile BEDAVA!

---

### Aşama 3: Düzenli Eğitim (İhtiyaç Halinde)
1. GCP kredisi bittiyse Vast.ai kullan
2. Veya AWS Spot instance
3. Her zaman otomatik kapatma ayarla

**Maliyet:** $0.10-0.50 per eğitim

---

## 🎓 Colab ile Hızlı Başlangıç

### 1. Colab Notebook Oluştur
```python
# 1. GitHub'dan klonla
!git clone https://github.com/your-username/WikipediaML.git
%cd WikipediaML

# 2. Bağımlılıkları kur
!pip install -r requirements.txt

# 3. Eğitimi başlat
!python train_ml_model_curated.py --limit 10

# 4. Modeli indir
from google.colab import files
files.download('cache/ml_model.pkl')
```

### 2. GPU Aktif Et
- Runtime → Change runtime type → GPU → Save

### 3. Çalıştır
- Runtime → Run all

**SONUÇ:** 30 dakikada ücretsiz eğitim! 🎉

---

## 💡 Sık Sorulan Sorular

### S: Kredi kartım olmadan yapabilir miyim?
**C:** Evet! Google Colab veya Kaggle tamamen ücretsiz ve kredi kartı gerektirmez.

### S: GCP $300 kredi gerçekten ücretsiz mi?
**C:** Evet! Kredi kartı gerekli ama otomatik ücretlendirme YOK. Kredi bitince durur.

### S: AWS'de unutup kapatmazsam ne olur?
**C:** Para gider! Mutlaka otomatik kapatma ayarlayın veya billing alarm kurun.

### S: En ucuz seçenek hangisi?
**C:** 
1. Colab/Kaggle (ücretsiz)
2. GCP Preemptible ($0.12 - ama $300 kredi ile bedava)
3. Vast.ai ($0.30)

### S: En güvenilir seçenek hangisi?
**C:** GCP veya AWS. Vast.ai topluluk GPU'ları bazen sorunlu olabilir.

### S: Kaç kere eğitim yapabilirim?
**C:** GCP $300 kredi ile ~2,500 eğitim yapabilirsiniz!

---

## 🎯 Sonuç ve Öneri

### Sizin İçin En İyi Seçenek: **Google Colab + GCP**

#### Neden?
1. **Colab ile test** (ücretsiz, 30 dakika)
2. **GCP ile tam eğitim** ($300 kredi, bedava)
3. **Güvenli** (otomatik ücretlendirme yok)
4. **Kolay** (dokümantasyon mevcut)

#### Tahmini Maliyet
- İlk eğitim: **₺0** (Colab)
- Sonraki eğitimler: **₺0** ($300 kredi ile)
- Kredi bittikten sonra: **₺3-10** per eğitim

#### Toplam Maliyet (1 yıl)
- 10 eğitim: **₺0** (kredi ile)
- 100 eğitim: **₺0** (kredi ile)
- 1000 eğitim: **₺0** (kredi ile)
- 3000 eğitim: **₺150** (kredi bittikten sonra)

---

## 📞 Sonraki Adım

Hangi yolu seçmek istersiniz?

1. **Colab ile hemen başla** (ücretsiz, 30 dakika)
2. **GCP hesabı aç** ($300 kredi al, sonra eğit)
3. **Daha fazla bilgi** (başka sorular)

Kararınızı verin, size adım adım yardımcı olayım! 🚀