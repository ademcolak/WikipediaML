# ☁️ Cloud Training Guide

Bu rehber, WikipediaML model eğitimini bulut ortamında çalıştırmak için gereken tüm adımları içerir.

## 📋 İçindekiler

1. [Neden Cloud Training?](#neden-cloud-training)
2. [Platform Seçenekleri](#platform-seçenekleri)
3. [AWS ile Eğitim](#aws-ile-eğitim)
4. [Google Cloud ile Eğitim](#google-cloud-ile-eğitim)
5. [Azure ile Eğitim](#azure-ile-eğitim)
6. [Docker ile Eğitim](#docker-ile-eğitim)
7. [Maliyet Optimizasyonu](#maliyet-optimizasyonu)
8. [Sorun Giderme](#sorun-giderme)

---

## 🤔 Neden Cloud Training?

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

## 🌐 Platform Seçenekleri

### 1. AWS (Amazon Web Services)
**En İyi Seçenek:** Genel amaçlı, geniş hizmet yelpazesi

**Avantajlar:**
- Çok sayıda instance tipi
- Spot instances ile %70 maliyet tasarrufu
- S3 ile kolay model saklama
- Geniş dokümantasyon

**Tahmini Maliyet:**
- CPU (t3.xlarge): ~$0.17/saat
- GPU (g4dn.xlarge): ~$0.53/saat
- Spot instance: %50-70 indirim

### 2. Google Cloud Platform (GCP)
**En İyi Seçenek:** ML/AI odaklı projeler

**Avantajlar:**
- Vertex AI entegrasyonu
- Preemptible VMs ile düşük maliyet
- Kolay ML pipeline kurulumu
- Ücretsiz $300 kredi (yeni kullanıcılar)

**Tahmini Maliyet:**
- CPU (n1-standard-4): ~$0.19/saat
- GPU (n1-standard-4 + T4): ~$0.35/saat
- Preemptible: %60-80 indirim

### 3. Azure
**En İyi Seçenek:** Microsoft ekosistemi kullanıcıları

**Avantajlar:**
- Azure ML Studio entegrasyonu
- Spot VMs ile düşük maliyet
- Visual Studio entegrasyonu

**Tahmini Maliyet:**
- CPU (Standard_D4s_v3): ~$0.19/saat
- GPU (NC6): ~$0.90/saat

### 4. Alternatif Platformlar

#### Vast.ai (En Ucuz GPU)
- GPU: $0.10-0.30/saat
- Topluluk GPU'ları
- Spot market benzeri

#### Lambda Labs
- GPU: $0.50-1.10/saat
- ML'e özel
- Kolay kurulum

#### Paperspace Gradient
- GPU: $0.51/saat
- Jupyter notebook desteği
- Ücretsiz tier

---

## 🚀 AWS ile Eğitim

### Adım 1: AWS Hesabı Oluştur
```bash
# AWS CLI kur
brew install awscli  # macOS
# veya
pip install awscli

# AWS hesabını yapılandır
aws configure
```

### Adım 2: EC2 Instance Başlat

#### Seçenek A: AWS Console (Kolay)
1. AWS Console → EC2 → Launch Instance
2. **AMI Seç:** Deep Learning AMI (Ubuntu 20.04)
3. **Instance Type:**
   - Başlangıç: `t3.xlarge` (4 vCPU, 16GB RAM)
   - GPU: `g4dn.xlarge` (4 vCPU, 16GB RAM, T4 GPU)
4. **Storage:** 50GB EBS
5. **Security Group:** SSH (22) portunu aç
6. **Key Pair:** Oluştur ve indir

#### Seçenek B: AWS CLI (Hızlı)
```bash
# Spot instance başlat (70% daha ucuz!)
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.xlarge \
  --key-name your-key-name \
  --security-group-ids sg-xxxxxxxx \
  --instance-market-options '{"MarketType":"spot"}' \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":50}}]'
```

### Adım 3: Instance'a Bağlan
```bash
# SSH ile bağlan
ssh -i your-key.pem ubuntu@ec2-xx-xx-xx-xx.compute.amazonaws.com

# Veya AWS Systems Manager Session Manager kullan (key gerekmez)
aws ssm start-session --target i-xxxxxxxxx
```

### Adım 4: Projeyi Kur
```bash
# Git kur (genelde yüklü)
sudo apt update
sudo apt install -y git

# Projeyi klonla
git clone https://github.com/your-username/WikipediaML.git
cd WikipediaML

# Python ve pip kur
sudo apt install -y python3.11 python3-pip

# Bağımlılıkları kur
pip install -r requirements.txt
```

### Adım 5: Eğitimi Başlat
```bash
# Basit eğitim
python train_cloud.py

# S3'e otomatik yükleme ile
python train_cloud.py --upload-s3 --s3-bucket my-ml-models

# Büyük dataset ile
python train_cloud.py --dataset training_dataset_large.json

# Screen ile arka planda çalıştır
screen -S training
python train_cloud.py
# Ctrl+A, D ile detach
# screen -r training ile geri dön
```

### Adım 6: Model İndir
```bash
# SCP ile
scp -i your-key.pem ubuntu@ec2-xx-xx-xx-xx.compute.amazonaws.com:~/WikipediaML/cache/ml_model.pkl .

# S3'ten
aws s3 cp s3://my-ml-models/wikipediaml/cache/ml_model.pkl .
```

### Adım 7: Instance'ı Durdur
```bash
# AWS Console'dan Stop
# veya CLI ile
aws ec2 stop-instances --instance-ids i-xxxxxxxxx

# Tamamen sil (dikkat!)
aws ec2 terminate-instances --instance-ids i-xxxxxxxxx
```

---

## 🔵 Google Cloud ile Eğitim

### Adım 1: GCP Hesabı Oluştur
```bash
# gcloud CLI kur
brew install google-cloud-sdk  # macOS

# Giriş yap
gcloud auth login
gcloud config set project your-project-id
```

### Adım 2: VM Instance Oluştur
```bash
# CPU instance
gcloud compute instances create wikipediaml-trainer \
  --zone=us-central1-a \
  --machine-type=n1-standard-4 \
  --image-family=ubuntu-2004-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=50GB \
  --preemptible  # 80% daha ucuz!

# GPU instance
gcloud compute instances create wikipediaml-trainer-gpu \
  --zone=us-central1-a \
  --machine-type=n1-standard-4 \
  --accelerator=type=nvidia-tesla-t4,count=1 \
  --image-family=pytorch-latest-gpu \
  --image-project=deeplearning-platform-release \
  --boot-disk-size=50GB \
  --preemptible
```

### Adım 3: SSH Bağlantısı
```bash
# Tarayıcı üzerinden SSH
gcloud compute ssh wikipediaml-trainer --zone=us-central1-a

# Veya yerel terminal
gcloud compute ssh wikipediaml-trainer --zone=us-central1-a
```

### Adım 4: Projeyi Kur ve Çalıştır
```bash
# Projeyi klonla
git clone https://github.com/your-username/WikipediaML.git
cd WikipediaML

# Bağımlılıkları kur
pip install -r requirements.txt

# GCS ile eğitim
python train_cloud.py --upload-gcs --gcs-bucket my-ml-models
```

### Adım 5: Model İndir
```bash
# GCS'ten indir
gsutil cp gs://my-ml-models/wikipediaml/cache/ml_model.pkl .
```

---

## 🐳 Docker ile Eğitim

### Yerel Docker Test
```bash
# Image oluştur
docker build -t wikipediaml-trainer .

# CPU ile çalıştır
docker run -v $(pwd)/cache:/app/cache wikipediaml-trainer

# GPU ile çalıştır
docker build -f Dockerfile.gpu -t wikipediaml-trainer-gpu .
docker run --gpus all -v $(pwd)/cache:/app/cache wikipediaml-trainer-gpu
```

### AWS ECS ile Docker
```bash
# ECR'a push
aws ecr create-repository --repository-name wikipediaml-trainer
docker tag wikipediaml-trainer:latest xxxx.dkr.ecr.us-east-1.amazonaws.com/wikipediaml-trainer:latest
docker push xxxx.dkr.ecr.us-east-1.amazonaws.com/wikipediaml-trainer:latest

# ECS task tanımla ve çalıştır
aws ecs create-cluster --cluster-name ml-training
aws ecs run-task --cluster ml-training --task-definition wikipediaml-trainer
```

### Google Cloud Run ile Docker
```bash
# Container Registry'e push
docker tag wikipediaml-trainer gcr.io/your-project/wikipediaml-trainer
docker push gcr.io/your-project/wikipediaml-trainer

# Cloud Run job oluştur
gcloud run jobs create wikipediaml-trainer \
  --image gcr.io/your-project/wikipediaml-trainer \
  --region us-central1 \
  --memory 8Gi \
  --cpu 4
```

---

## 💰 Maliyet Optimizasyonu

### 1. Spot/Preemptible Instances Kullan
**Tasarruf: %50-80**

```bash
# AWS Spot
aws ec2 run-instances --instance-market-options '{"MarketType":"spot"}'

# GCP Preemptible
gcloud compute instances create --preemptible

# Azure Spot
az vm create --priority Spot
```

### 2. Otomatik Kapatma Ayarla
```bash
# AWS - 2 saat sonra otomatik kapat
aws ec2 stop-instances --instance-ids i-xxx --dry-run

# Cron job ile
echo "0 */2 * * * aws ec2 stop-instances --instance-ids i-xxx" | crontab -
```

### 3. Küçük Dataset ile Test
```bash
# İlk 10 çift ile test et
python train_cloud.py --limit 10

# Başarılı olursa tam dataset
python train_cloud.py
```

### 4. Checkpoint Kullan
```bash
# Her 5 dakikada checkpoint kaydet
python train_cloud.py --checkpoint-interval 300
```

### 5. Bölge Seçimi
- **En Ucuz AWS Bölgeleri:** us-east-1, us-west-2
- **En Ucuz GCP Bölgeleri:** us-central1, us-west1
- **Avrupa:** eu-west-1 (AWS), europe-west1 (GCP)

### Tahmini Maliyetler (50 çift eğitim)

| Platform | Instance Type | Süre | Maliyet |
|----------|--------------|------|---------|
| AWS t3.xlarge | CPU | 2-3 saat | $0.34-0.51 |
| AWS g4dn.xlarge | GPU | 1-2 saat | $0.53-1.06 |
| AWS Spot | CPU | 2-3 saat | $0.10-0.15 |
| GCP n1-standard-4 | CPU | 2-3 saat | $0.38-0.57 |
| GCP Preemptible | CPU | 2-3 saat | $0.08-0.12 |
| Vast.ai | GPU | 1-2 saat | $0.10-0.30 |

**Sonuç:** Spot/Preemptible kullanarak **$0.10-0.15** ile eğitim yapabilirsiniz!

---

## 🎯 Hızlı Başlangıç Önerileri

### Yeni Başlayanlar İçin
1. **GCP Free Tier** kullan ($300 kredi)
2. **Preemptible VM** ile başla
3. **10 çift** ile test et
4. Başarılı olursa tam dataset

### Deneyimliler İçin
1. **AWS Spot Instance** kullan
2. **Docker** ile çalıştır
3. **S3/GCS** otomatik yükleme
4. **CloudWatch/Stackdriver** ile monitoring

### Minimum Maliyet İçin
1. **Vast.ai** kullan ($0.10/saat)
2. **Spot instances** tercih et
3. **Checkpoint** ile güvenli eğitim
4. **Otomatik kapatma** ayarla

---

## 🔧 Sorun Giderme

### Problem: SSH bağlantısı kurulamıyor
```bash
# Security group kontrol et
aws ec2 describe-security-groups --group-ids sg-xxx

# Port 22 açık mı?
# Firewall kurallarını kontrol et
```

### Problem: Out of memory
```bash
# Daha büyük instance kullan
# veya batch size küçült
# veya limit ile test et
python train_cloud.py --limit 10
```

### Problem: Training çok yavaş
```bash
# GPU instance kullan
# veya verbose mode kapat
python train_cloud.py --no-verbose
```

### Problem: Instance beklenmedik kapandı
```bash
# Checkpoint'ten devam et
# cache/checkpoint.json dosyasını kontrol et
# Son kaydedilen yerden devam edebilirsin
```

---

## 📚 Ek Kaynaklar

### AWS
- [EC2 Pricing](https://aws.amazon.com/ec2/pricing/)
- [Spot Instances](https://aws.amazon.com/ec2/spot/)
- [Deep Learning AMI](https://aws.amazon.com/machine-learning/amis/)

### GCP
- [Compute Engine Pricing](https://cloud.google.com/compute/pricing)
- [Preemptible VMs](https://cloud.google.com/compute/docs/instances/preemptible)
- [AI Platform](https://cloud.google.com/ai-platform)

### Azure
- [Virtual Machines Pricing](https://azure.microsoft.com/pricing/details/virtual-machines/)
- [Spot VMs](https://azure.microsoft.com/services/virtual-machines/spot/)

### Alternatifler
- [Vast.ai](https://vast.ai/)
- [Lambda Labs](https://lambdalabs.com/)
- [Paperspace](https://www.paperspace.com/)

---

## 🎉 Özet

1. **Platform Seç:** GCP (yeni başlayanlar), AWS (genel), Vast.ai (ucuz)
2. **Instance Oluştur:** Spot/Preemptible kullan
3. **Projeyi Kur:** Git clone + pip install
4. **Eğitimi Başlat:** `python train_cloud.py`
5. **Model İndir:** S3/GCS veya SCP
6. **Instance Kapat:** Maliyetten kaçın!

**Tahmini Maliyet:** $0.10-0.50 (tek eğitim)
**Tahmini Süre:** 1-3 saat

Sorularınız için: GitHub Issues veya Discord