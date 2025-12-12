# ⚡ Cloud Training - Hızlı Başlangıç

Model eğitimi bilgisayarınızı çok yoruyor mu? İşte çözüm! 🚀

## 🎯 3 Kolay Seçenek

### 1️⃣ Google Colab (ÖNERİLEN - ÜCRETSIZ)

**Neden?**
- ✅ Tamamen ücretsiz
- ✅ Kredi kartı gerekmez
- ✅ GPU desteği
- ✅ 5 dakikada başla

**Nasıl?**
1. [WikipediaML_Training.ipynb](../WikipediaML_Training.ipynb) dosyasını aç
2. Google Colab'a yükle: https://colab.research.google.com/
3. Runtime → Change runtime type → GPU
4. Runtime → Run all
5. 45-60 dakika bekle
6. Model dosyalarını indir

**Maliyet:** ₺0 🎉

---

### 2️⃣ Google Cloud Platform ($300 Kredi)

**Neden?**
- ✅ $300 ücretsiz kredi (yeni kullanıcılar)
- ✅ Otomatik ücretlendirme YOK
- ✅ Güçlü kaynaklar
- ✅ 2,500+ eğitim yapabilirsiniz

**Nasıl?**
```bash
# 1. GCP hesabı aç ve $300 kredi al
# https://cloud.google.com/free

# 2. gcloud CLI kur
brew install google-cloud-sdk  # macOS
# veya https://cloud.google.com/sdk/docs/install

# 3. Giriş yap
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 4. VM oluştur (Preemptible - çok ucuz!)
gcloud compute instances create wikipediaml-trainer \
  --zone=us-central1-a \
  --machine-type=n1-standard-4 \
  --image-family=ubuntu-2004-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=50GB \
  --preemptible

# 5. SSH ile bağlan
gcloud compute ssh wikipediaml-trainer --zone=us-central1-a

# 6. Projeyi kur
git clone https://github.com/your-username/WikipediaML.git
cd WikipediaML
pip install -r requirements.txt

# 7. Eğitimi başlat
python train_cloud.py --upload-gcs --gcs-bucket YOUR_BUCKET

# 8. VM'i kapat (ÖNEMLİ!)
gcloud compute instances stop wikipediaml-trainer --zone=us-central1-a
```

**Maliyet:** $0.12 (₺3.60) - ama $300 kredi ile BEDAVA!

---

### 3️⃣ AWS Spot Instance (Deneyimliler İçin)

**Neden?**
- ✅ Çok ucuz (%70 indirim)
- ✅ Güvenilir
- ✅ Geniş hizmet yelpazesi

**Nasıl?**
```bash
# 1. AWS CLI kur
brew install awscli  # macOS
# veya pip install awscli

# 2. AWS hesabını yapılandır
aws configure

# 3. Spot instance başlat
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.xlarge \
  --key-name YOUR_KEY \
  --security-group-ids YOUR_SG \
  --instance-market-options '{"MarketType":"spot"}' \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":50}}]'

# 4. SSH ile bağlan
ssh -i your-key.pem ubuntu@YOUR_INSTANCE_IP

# 5. Projeyi kur
git clone https://github.com/your-username/WikipediaML.git
cd WikipediaML
pip install -r requirements.txt

# 6. Eğitimi başlat
python train_cloud.py --upload-s3 --s3-bucket YOUR_BUCKET

# 7. Instance'ı durdur (ÖNEMLİ!)
aws ec2 stop-instances --instance-ids YOUR_INSTANCE_ID
```

**Maliyet:** $0.15 (₺4.50)

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

## 🎯 Hangi Seçeneği Seçmeliyim?

### Hiç Para Harcamak İstemiyorum
→ **Google Colab** (ücretsiz, 45-60 dakika)

### Minimum Maliyet, Maksimum Esneklik
→ **GCP + $300 Kredi** (ilk 2,500 eğitim bedava!)

### Hızlı ve Güvenilir
→ **AWS Spot Instance** (₺4.50, 2-3 saat)

### Deneyimliyim, En Ucuz GPU İstiyorum
→ **Vast.ai** (₺9, 1-2 saat, GPU)

---

## 🛡️ Güvenlik İpuçları

### 1. Otomatik Kapatma Ayarla
```bash
# AWS
aws ec2 stop-instances --instance-ids i-xxx

# GCP
gcloud compute instances stop wikipediaml-trainer
```

### 2. Billing Alarm Kur
- AWS: Budgets → $10 limit
- GCP: Billing → Budgets → $10 limit

### 3. Her Gün Kontrol Et
- AWS Console → Billing Dashboard
- GCP Console → Billing

### 4. Checkpoint Kullan
```bash
# Her 5 dakikada kaydet
python train_cloud.py --checkpoint-interval 300
```

---

## 📊 Beklenen Sonuçlar

### 10 Çift (Test)
- **Süre:** 15-30 dakika
- **Başarı Oranı:** ~60-70%
- **Maliyet:** ₺0 (Colab) veya ₺1-2

### 50 Çift (Tam)
- **Süre:** 45-90 dakika
- **Başarı Oranı:** ~70-80%
- **Maliyet:** ₺0 (Colab/GCP kredi) veya ₺3-10

### 100 Çift (Büyük)
- **Süre:** 2-3 saat
- **Başarı Oranı:** ~75-85%
- **Maliyet:** ₺0 (GCP kredi) veya ₺5-15

---

## 🚨 Sık Yapılan Hatalar

### ❌ Instance'ı kapatmayı unutmak
**Sonuç:** Gereksiz maliyet (günde ₺100+)
**Çözüm:** Otomatik kapatma ayarla

### ❌ GPU seçmeden Colab'da çalıştırmak
**Sonuç:** Çok yavaş (3-4 saat)
**Çözüm:** Runtime → Change runtime type → GPU

### ❌ Checkpoint kullanmamak
**Sonuç:** Kesinti olursa baştan başla
**Çözüm:** `--checkpoint-interval 300` kullan

### ❌ Billing alarm kurmamak
**Sonuç:** Beklenmedik faturalar
**Çözüm:** $10 limit koy

---

## 📚 Detaylı Dokümantasyon

- **Maliyet Analizi:** [CLOUD_COST_ANALYSIS.md](CLOUD_COST_ANALYSIS.md)
- **Tam Rehber:** [CLOUD_TRAINING_GUIDE.md](CLOUD_TRAINING_GUIDE.md)
- **Docker Kullanımı:** [../Dockerfile](../Dockerfile)

---

## 🎉 Hızlı Başlangıç (5 Dakika)

### Colab ile (En Kolay)
1. [WikipediaML_Training.ipynb](../WikipediaML_Training.ipynb) aç
2. Colab'a yükle
3. GPU aktif et
4. Run all
5. Bekle (45-60 dk)
6. İndir

### GCP ile (En Ekonomik)
```bash
# Tek komut ile başla!
./deploy_cloud.sh
# Seçenek 2'yi seç (GCP)
```

---

## 💡 Sonuç

**En İyi Seçenek:** Google Colab (ücretsiz) → GCP ($300 kredi)

**Tahmini Maliyet:** ₺0 (ilk 2,500 eğitim)

**Tahmini Süre:** 45-60 dakika

**Zorluk:** ⭐⭐ (Kolay)

---

## 🆘 Yardım

Sorun mu yaşıyorsunuz?

1. [CLOUD_TRAINING_GUIDE.md](CLOUD_TRAINING_GUIDE.md) - Detaylı rehber
2. [CLOUD_COST_ANALYSIS.md](CLOUD_COST_ANALYSIS.md) - Maliyet analizi
3. GitHub Issues - Soru sorun
4. Discord - Topluluk desteği

**Hadi başlayalım!** 🚀