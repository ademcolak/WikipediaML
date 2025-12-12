# ☁️ Cloud Training Rehberi

Model eğitimi bilgisayarınızı çok yoruyor mu? Cloud'da eğitin!

---

## 🎯 Neden Cloud?

### Yerel Bilgisayar Sorunları
- ❌ Yüksek CPU/RAM kullanımı
- ❌ Uzun eğitim süreleri (saatler)
- ❌ Bilgisayarı başka işler için kullanamama
- ❌ Elektrik kesintisi riski
- ❌ Isınma ve fan gürültüsü

### Cloud Avantajları
- ✅ Güçlü GPU/CPU kaynakları
- ✅ Arka planda çalışma
- ✅ Otomatik checkpoint kaydetme
- ✅ Ölçeklenebilir kaynaklar
- ✅ Sadece kullandığın kadar öde
- ✅ 7/24 çalışabilme

---

## 💰 Maliyet Karşılaştırması

| Platform | Süre | Maliyet | Kredi Kartı | Önerilen |
|----------|------|---------|-------------|----------|
| **Google Colab** | 45-60 dk | **₺0** | ❌ Hayır | ⭐⭐⭐⭐⭐ |
| **GCP Preemptible** | 2-3 saat | **₺0** ($300 kredi) | ✅ Evet (ücret yok) | ⭐⭐⭐⭐⭐ |
| **AWS Spot** | 2-3 saat | ₺4.50 | ✅ Evet | ⭐⭐⭐⭐ |
| **Vast.ai** | 1-2 saat | ₺9 | ✅ Evet | ⭐⭐⭐ |
| **Yerel PC** | 3-5 saat | ₺0 (ama çok yorucu) | ❌ Hayır | ⭐⭐ |

---

## 🚀 Seçenek 1: Google Colab (ÖNERİLEN)

### Neden Colab?
- ✅ **Tamamen ücretsiz**
- ✅ Kredi kartı gerekmez
- ✅ GPU desteği
- ✅ 5 dakikada başla
- ✅ Jupyter notebook

### Adım Adım

#### 1. Notebook Hazırla

`WikipediaML_Training.ipynb` dosyasını kullan (proje root'unda).

#### 2. Colab'a Yükle

1. https://colab.research.google.com/ git
2. File → Upload notebook
3. `WikipediaML_Training.ipynb` seç

#### 3. GPU Aktif Et

1. Runtime → Change runtime type
2. Hardware accelerator → **GPU**
3. GPU type → **T4** (ücretsiz)
4. Save

#### 4. Çalıştır

1. Runtime → Run all
2. 45-60 dakika bekle
3. İlerlemeyi izle

#### 5. Model İndir

Notebook sonunda otomatik indirilir:
- `ml_model.pkl`
- `ml_scaler.pkl`
- `training_history.json`
- `embeddings_cache.pkl`
- `wiki_graph.pkl`

### Colab Limitleri

- **Süre:** 12 saat (yeterli!)
- **GPU:** Haftada ~30 saat
- **RAM:** 12GB
- **Disk:** 100GB

### Colab Pro (Opsiyonel)

**$9.99/ay:**
- Daha uzun süre (24 saat)
- Daha iyi GPU (V100, A100)
- Daha fazla RAM (32GB)
- Öncelikli erişim

**Gerekli mi?** Hayır, ücretsiz yeterli!

---

## 🔵 Seçenek 2: Google Cloud Platform (GCP)

### Neden GCP?
- ✅ **$300 ücretsiz kredi** (yeni kullanıcılar)
- ✅ Otomatik ücretlendirme YOK
- ✅ Kredi bitince durur
- ✅ Güçlü kaynaklar
- ✅ 2,500+ eğitim yapabilirsiniz

### Adım Adım

#### 1. GCP Hesabı Aç

1. https://cloud.google.com/free git
2. "Get started for free" tıkla
3. Google hesabı ile giriş yap
4. Kredi kartı bilgisi gir (ücret YOK, sadece doğrulama)
5. **$300 kredi al!**

#### 2. gcloud CLI Kur

```bash
# macOS
brew install google-cloud-sdk

# Linux
curl https://sdk.cloud.google.com | bash

# Windows
# https://cloud.google.com/sdk/docs/install adresinden indir
```

#### 3. Giriş Yap

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

#### 4. VM Oluştur (Preemptible - Çok Ucuz!)

```bash
gcloud compute instances create wikipediaml-trainer \
  --zone=us-central1-a \
  --machine-type=n1-standard-4 \
  --image-family=ubuntu-2004-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=50GB \
  --preemptible
```

**Maliyet:** $0.04/saat (₺1.20/saat)
**Toplam:** ~$0.12 (₺3.60) - ama $300 kredi ile BEDAVA!

#### 5. SSH Bağlan

```bash
gcloud compute ssh wikipediaml-trainer --zone=us-central1-a
```

#### 6. Projeyi Kur

```bash
# Git kur
sudo apt update
sudo apt install -y git python3-pip

# Projeyi klonla
git clone <repo-url>
cd WikipediaML

# Bağımlılıkları kur
pip3 install -r requirements.txt
```

#### 7. Eğitimi Başlat

```bash
# Screen ile arka planda çalıştır
screen -S training

# Eğitimi başlat
python3 train_ml_model_curated.py

# Detach: Ctrl+A, D
# Reattach: screen -r training
```

#### 8. Model İndir

```bash
# Yerel bilgisayardan çalıştır
gcloud compute scp wikipediaml-trainer:~/WikipediaML/cache/*.pkl ./cache/ --zone=us-central1-a
```

#### 9. VM'i Durdur (ÖNEMLİ!)

```bash
# Durdur (ücret durur)
gcloud compute instances stop wikipediaml-trainer --zone=us-central1-a

# Tamamen sil (ücret tamamen biter)
gcloud compute instances delete wikipediaml-trainer --zone=us-central1-a
```

### GCP Maliyet Detayları

```
Preemptible VM (n1-standard-4):
- Saat başı: $0.04 (₺1.20)
- 3 saat eğitim: $0.12 (₺3.60)
- $300 kredi ile: 7,500 saat = 2,500 eğitim!

Normal VM (n1-standard-4):
- Saat başı: $0.19 (₺5.70)
- 3 saat eğitim: $0.57 (₺17.10)
- $300 kredi ile: 1,578 saat = 526 eğitim
```

**Öneri:** Preemptible kullan (5x daha ucuz!)

---

## 🟠 Seçenek 3: AWS EC2

### Neden AWS?
- ✅ Spot instances ile ucuz
- ✅ Güvenilir
- ✅ Geniş hizmet yelpazesi

### Adım Adım

#### 1. AWS CLI Kur

```bash
# macOS
brew install awscli

# Linux/Windows
pip install awscli

# Yapılandır
aws configure
```

#### 2. Spot Instance Başlat

```bash
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.xlarge \
  --key-name YOUR_KEY \
  --security-group-ids YOUR_SG \
  --instance-market-options '{"MarketType":"spot"}' \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":50}}]'
```

#### 3. SSH Bağlan

```bash
ssh -i your-key.pem ubuntu@YOUR_INSTANCE_IP
```

#### 4. Projeyi Kur ve Çalıştır

```bash
git clone <repo-url>
cd WikipediaML
pip install -r requirements.txt
python train_ml_model_curated.py
```

#### 5. Model İndir

```bash
scp -i your-key.pem ubuntu@YOUR_INSTANCE_IP:~/WikipediaML/cache/*.pkl ./cache/
```

#### 6. Instance Durdur

```bash
aws ec2 stop-instances --instance-ids YOUR_INSTANCE_ID
```

### AWS Maliyet

```
Spot Instance (t3.xlarge):
- Saat başı: $0.05 (₺1.50)
- 3 saat: $0.15 (₺4.50)

Normal Instance:
- Saat başı: $0.17 (₺5.10)
- 3 saat: $0.51 (₺15.30)
```

---

## 🟣 Seçenek 4: Vast.ai (En Ucuz GPU)

### Neden Vast.ai?
- ✅ **En ucuz GPU** ($0.10-0.30/saat)
- ✅ Topluluk GPU'ları
- ✅ Saatlik ödeme

### Adım Adım

1. https://vast.ai/ git
2. Hesap oluştur
3. "Search" sekmesinden GPU seç
4. "PyTorch" template seç
5. Instance başlat
6. SSH ile bağlan
7. Projeyi kur ve çalıştır

### Maliyet

```
RTX 3060:
- Saat başı: $0.15 (₺4.50)
- 2 saat: $0.30 (₺9.00)
```

---

## 🛡️ Güvenlik ve Maliyet Kontrolü

### 1. Otomatik Kapatma Ayarla

```bash
# AWS - 3 saat sonra otomatik kapat
aws ec2 stop-instances --instance-ids i-xxx

# GCP - 3 saat sonra otomatik kapat
gcloud compute instances stop wikipediaml-trainer --zone=us-central1-a
```

### 2. Billing Alarm Kur

**AWS:**
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name billing-alarm \
  --alarm-description "Alert when charges exceed $5" \
  --metric-name EstimatedCharges \
  --threshold 5
```

**GCP:**
1. Billing → Budgets & alerts
2. Create budget
3. Set limit: $10
4. Email alert

### 3. Her Gün Kontrol Et

- AWS Console → Billing Dashboard
- GCP Console → Billing
- Email uyarılarını aç

### 4. Instance'ları Unutma!

**Unutursanız:**
- 1 gün: $4-8 (₺120-240)
- 1 hafta: $28-56 (₺840-1,680)
- 1 ay: $120-240 (₺3,600-7,200)

**Çözüm:** Otomatik kapatma!

---

## 📊 Platform Karşılaştırması

### Hız

| Platform | CPU | GPU | Süre |
|----------|-----|-----|------|
| Colab | ⭐⭐⭐ | ⭐⭐⭐⭐ | 45-60 dk |
| GCP | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 30-45 dk |
| AWS | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 30-45 dk |
| Vast.ai | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 20-30 dk |

### Maliyet

| Platform | İlk Eğitim | 10 Eğitim | 100 Eğitim |
|----------|-----------|-----------|------------|
| Colab | ₺0 | ₺0 | ₺0 |
| GCP | ₺0 ($300 kredi) | ₺0 | ₺0 |
| AWS Spot | ₺4.50 | ₺45 | ₺450 |
| Vast.ai | ₺9 | ₺90 | ₺900 |

### Kolaylık

| Platform | Kurulum | Kullanım | Önerilen |
|----------|---------|----------|----------|
| Colab | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Yeni başlayanlar |
| GCP | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Herkes |
| AWS | ⭐⭐⭐ | ⭐⭐⭐ | Deneyimliler |
| Vast.ai | ⭐⭐⭐ | ⭐⭐⭐ | GPU gerekenlere |

---

## 🎯 Hangi Platform?

### Hiç Para Harcamak İstemiyorum
→ **Google Colab** (ücretsiz, 45-60 dakika)

### Minimum Maliyet, Maksimum Esneklik
→ **GCP + $300 Kredi** (ilk 2,500 eğitim bedava!)

### Hızlı ve Güvenilir
→ **AWS Spot Instance** (₺4.50, 30-45 dakika)

### En Ucuz GPU
→ **Vast.ai** (₺9, 20-30 dakika, GPU)

---

## 🚀 Hızlı Başlangıç

### 5 Dakikada Başla (Colab)

```
1. WikipediaML_Training.ipynb aç
2. Colab'a yükle
3. GPU aktif et
4. Run all
5. Bekle (45-60 dk)
6. İndir
```

### 10 Dakikada Başla (GCP)

```bash
# 1. GCP hesabı aç ($300 kredi)
# 2. gcloud CLI kur
brew install google-cloud-sdk

# 3. VM oluştur
gcloud compute instances create wikipediaml-trainer \
  --zone=us-central1-a \
  --machine-type=n1-standard-4 \
  --preemptible

# 4. SSH bağlan
gcloud compute ssh wikipediaml-trainer

# 5. Projeyi kur
git clone <repo-url>
cd WikipediaML
pip3 install -r requirements.txt

# 6. Eğitimi başlat
python3 train_ml_model_curated.py
```

---

## 🐛 Sorun Giderme

### Problem: Colab GPU bulunamıyor

**Çözüm:**
1. Runtime → Change runtime type
2. Hardware accelerator → GPU
3. Save
4. Runtime → Restart runtime

### Problem: GCP kredi kartı istemiyor

**Sebep:** Zaten kredi kartı eklenmiş

**Kontrol:**
1. Billing → Payment methods
2. Kredi kartı var mı?

### Problem: SSH bağlantısı kurulamıyor

**Çözüm:**
```bash
# Firewall kurallarını kontrol et
gcloud compute firewall-rules list

# SSH port açık mı?
gcloud compute firewall-rules create allow-ssh \
  --allow tcp:22
```

### Problem: Out of memory

**Çözüm:**
- Daha büyük instance kullan
- Batch size küçült
- Limit ile test et

---

## 📚 Ek Kaynaklar

### Colab
- [Colab Docs](https://colab.research.google.com/)
- [Colab Pro](https://colab.research.google.com/signup)

### GCP
- [GCP Free Tier](https://cloud.google.com/free)
- [Compute Engine Pricing](https://cloud.google.com/compute/pricing)
- [Preemptible VMs](https://cloud.google.com/compute/docs/instances/preemptible)

### AWS
- [EC2 Pricing](https://aws.amazon.com/ec2/pricing/)
- [Spot Instances](https://aws.amazon.com/ec2/spot/)

### Vast.ai
- [Vast.ai](https://vast.ai/)
- [Pricing](https://vast.ai/pricing)

---

## 🎉 Özet

### En İyi Seçenek: Colab → GCP

1. **İlk test:** Colab (ücretsiz, 5 dakika)
2. **Tam eğitim:** GCP ($300 kredi, bedava)
3. **Sürekli kullanım:** GCP Preemptible (₺3.60/eğitim)

### Tahmini Maliyet

```
İlk eğitim: ₺0 (Colab)
10 eğitim: ₺0 (GCP kredi)
100 eğitim: ₺0 (GCP kredi)
1000 eğitim: ₺0 (GCP kredi)
2500 eğitim: ₺0 (GCP kredi biter)
Sonrası: ₺3.60/eğitim
```

### Başlangıç Komutu

```bash
# Colab
# WikipediaML_Training.ipynb → Colab'a yükle → Run all

# GCP
gcloud compute instances create wikipediaml-trainer --preemptible
gcloud compute ssh wikipediaml-trainer
git clone <repo-url> && cd WikipediaML
pip3 install -r requirements.txt
python3 train_ml_model_curated.py
```

---

**Versiyon:** 5.0.0  
**Son Güncelleme:** 12 Aralık 2024  
**Durum:** Aktif Geliştirme

**Hadi başlayalım!** 🚀