# AWS EC2 Deployment Guide for WikipediaML

Bu rehber, WikipediaML projesini AWS EC2 üzerinde çalıştırmak için adım adım talimatlar içerir.

## 📋 İçindekiler

1. [Gereksinimler](#gereksinimler)
2. [EC2 Instance Oluşturma](#ec2-instance-oluşturma)
3. [Kurulum](#kurulum)
4. [Training Pipeline Çalıştırma](#training-pipeline-çalıştırma)
5. [Veri Senkronizasyonu](#veri-senkronizasyonu)
6. [Monitoring ve Troubleshooting](#monitoring-ve-troubleshooting)
7. [Maliyet Optimizasyonu](#maliyet-optimizasyonu)

## 🎯 Gereksinimler

### AWS Tarafı
- AWS hesabı
- EC2 erişim izinleri
- SSH key pair

### Yerel Makine
- SSH client
- rsync (veri senkronizasyonu için)
- AWS CLI (opsiyonel)

## 🚀 EC2 Instance Oluşturma

### Adım 1: AWS Console'a Giriş
1. [AWS Console](https://console.aws.amazon.com/) açın
2. EC2 Dashboard'a gidin
3. "Launch Instance" butonuna tıklayın

### Adım 2: Instance Konfigürasyonu

#### AMI Seçimi
- **Amazon Linux 2023** (önerilen) veya
- **Ubuntu 22.04 LTS**

#### Instance Type
Test için:
- **t3.xlarge** (4 vCPU, 16 GB RAM) - ~$0.17/saat

Tam Wikipedia için:
- **m5.2xlarge** (8 vCPU, 32 GB RAM) - ~$0.38/saat (önerilen)
- **c5.4xlarge** (16 vCPU, 32 GB RAM) - ~$0.68/saat (hızlı training)

#### Storage
- **200 GB** EBS volume (gp3)
- IOPS: 3000 (default)
- Throughput: 125 MB/s (default)

#### Security Group
Aşağıdaki portları açın:
- **SSH (22)**: Your IP (güvenlik için sadece kendi IP'niz)
- **Jupyter (8888)**: Your IP (opsiyonel, notebook kullanacaksanız)

#### Key Pair
- Yeni bir key pair oluşturun veya mevcut birini seçin
- `.pem` dosyasını güvenli bir yere kaydedin

### Adım 3: Instance'ı Başlatın
1. "Launch Instance" butonuna tıklayın
2. Instance'ın "running" durumuna geçmesini bekleyin
3. Public IP adresini not edin

## 🔧 Kurulum

### Adım 1: SSH Bağlantısı

```bash
# Key dosyasına doğru izinleri verin
chmod 400 ~/.ssh/your-key.pem

# EC2'ye bağlanın
ssh -i ~/.ssh/your-key.pem ec2-user@your-instance-ip
```

### Adım 2: Setup Script'ini Çalıştırın

EC2 instance'ına bağlandıktan sonra:

```bash
# Setup script'ini indirin
curl -O https://raw.githubusercontent.com/ademcolak/WikipediaML/main/aws/ec2_setup.sh

# Çalıştırılabilir yapın
chmod +x ec2_setup.sh

# Çalıştırın
./ec2_setup.sh
```

Bu script:
- ✅ Sistem paketlerini günceller
- ✅ Python 3 ve gerekli araçları yükler
- ✅ Projeyi klonlar
- ✅ Virtual environment oluşturur
- ✅ Bağımlılıkları yükler
- ✅ Gerekli dizinleri oluşturur
- ✅ Otomatik backup cron job'u kurar

## 🎓 Training Pipeline Çalıştırma

### Arka Planda Çalıştırma (Önerilen)

```bash
cd ~/WikipediaML
source venv/bin/activate

# Arka planda çalıştır
nohup ./aws/run_training_pipeline.sh > logs/training.log 2>&1 &

# Process ID'yi kaydet
echo $! > training.pid
```

### İlerlemeyi Takip Etme

```bash
# Log dosyasını canlı takip et
tail -f ~/WikipediaML/logs/training.log

# Son 50 satırı göster
tail -50 ~/WikipediaML/logs/training.log

# Training process'i kontrol et
ps aux | grep run_training_pipeline
```

### SSH Bağlantısı Koptuğunda

Training arka planda çalışmaya devam eder. Tekrar bağlandığınızda:

```bash
# Log'u kontrol edin
tail -f ~/WikipediaML/logs/training.log

# Process'in çalışıp çalışmadığını kontrol edin
cat ~/WikipediaML/training.pid | xargs ps -p
```

## 📦 Veri Senkronizasyonu

### Yerel Makine Konfigürasyonu

```bash
# Config dosyasını oluşturun
cd ~/WikipediaML/aws
cp config.example.sh config.sh

# Değerleri güncelleyin
nano config.sh
```

`config.sh` içeriği:
```bash
export EC2_HOST="ec2-user@your-instance-ip"
export EC2_KEY="~/.ssh/your-key.pem"
export EC2_PROJECT_DIR="~/WikipediaML"
```

### Veri İndirme (EC2 → Yerel)

```bash
# Config'i yükle
source aws/config.sh

# Tüm verileri indir
./aws/sync_data.sh download
```

Bu komut indirir:
- ✅ Eğitilmiş modeller (`models/`)
- ✅ İşlenmiş veriler (`data/*.pkl`, `data/*.npz`)
- ✅ Embeddings (`data/embeddings.npy`)
- ✅ En son checkpoint

### Veri Yükleme (Yerel → EC2)

```bash
# Yerel verileri EC2'ye yükle
./aws/sync_data.sh upload
```

### Training Durumunu Kontrol Etme

```bash
# EC2'deki training durumunu kontrol et
./aws/sync_data.sh status
```

## 📊 Monitoring ve Troubleshooting

### Disk Kullanımını Kontrol Etme

```bash
# EC2'de
df -h ~/WikipediaML
du -sh ~/WikipediaML/data/*
```

### Memory Kullanımını Kontrol Etme

```bash
# EC2'de
free -h
top
```

### Training'i Durdurma

```bash
# Process ID'yi bul
cat ~/WikipediaML/training.pid

# Process'i durdur
kill $(cat ~/WikipediaML/training.pid)

# Veya tüm training process'lerini durdur
pkill -f run_training_pipeline
```

### Training'i Yeniden Başlatma

Training pipeline otomatik olarak kaldığı yerden devam eder:

```bash
cd ~/WikipediaML
source venv/bin/activate
nohup ./aws/run_training_pipeline.sh > logs/training.log 2>&1 &
echo $! > training.pid
```

### Checkpoint'lerden Geri Yükleme

```bash
# Mevcut checkpoint'leri listele
ls -lh ~/WikipediaML/data/checkpoints/

# Bir checkpoint'i geri yükle
cd ~/WikipediaML
tar -xzf data/checkpoints/checkpoint_name.tar.gz
```

## 💰 Maliyet Optimizasyonu

### 1. Spot Instances Kullanın
- %70'e kadar daha ucuz
- Training kesintiye uğrayabilir ama checkpoint'ler sayesinde devam eder

### 2. Instance'ı Durdurun (Stop)
Training tamamlandığında:
```bash
# Yerel makineden
aws ec2 stop-instances --instance-ids i-1234567890abcdef0
```
- Sadece EBS storage için ödeme yaparsınız (~$20/ay)
- Tekrar başlatabilirsiniz

### 3. EBS Snapshot Alın
```bash
# AWS Console'dan veya CLI ile
aws ec2 create-snapshot --volume-id vol-1234567890abcdef0 \
    --description "WikipediaML trained model"
```
- Snapshot'lar EBS'den daha ucuz
- İstediğiniz zaman yeni bir volume oluşturabilirsiniz

### 4. Training Tamamlandıktan Sonra
1. Verileri yerel makineye indirin
2. Instance'ı terminate edin
3. Sadece snapshot'ı saklayın

## 📈 Training Süresi ve Maliyet Tahminleri

### Test (1000 sayfa)
- **Süre**: 30-60 dakika
- **Instance**: t3.xlarge
- **Maliyet**: ~$0.20

### Orta Ölçek (100K sayfa)
- **Süre**: 4-6 saat
- **Instance**: m5.xlarge
- **Maliyet**: ~$1.50

### Tam Wikipedia (6M+ sayfa)
- **Süre**: 30-50 saat (GPU ile) veya 60-100 saat (CPU)
- **Instance**: m5.2xlarge
- **Maliyet**: ~$20-40

## 🔐 Güvenlik En İyi Uygulamaları

1. **SSH Key'i Güvende Tutun**
   ```bash
   chmod 400 ~/.ssh/your-key.pem
   ```

2. **Security Group'u Kısıtlayın**
   - Sadece kendi IP'nizden SSH erişimi
   - Gereksiz portları kapatın

3. **IAM Roles Kullanın**
   - S3'e erişim için IAM role atayın
   - Access key'leri instance'a koymayın

4. **Düzenli Backup**
   - Otomatik checkpoint'ler aktif
   - Önemli verileri S3'e yedekleyin

## 🆘 Sık Karşılaşılan Sorunlar

### Problem: SSH bağlantısı kurulamıyor
**Çözüm**:
- Security group'ta SSH (22) portunu kontrol edin
- Key dosyası izinlerini kontrol edin: `chmod 400 key.pem`
- Instance'ın "running" durumda olduğunu kontrol edin

### Problem: Disk doldu
**Çözüm**:
```bash
# Eski checkpoint'leri temizle
cd ~/WikipediaML/data/checkpoints
ls -t *.tar.gz | tail -n +3 | xargs rm -f

# Wikipedia dump'larını sil (parse sonrası)
rm -f ~/WikipediaML/data/wikipedia_dumps/*.sql.gz
```

### Problem: Memory yetersiz
**Çözüm**:
- Daha büyük instance type'a geçin (m5.2xlarge veya daha büyük)
- Swap space ekleyin (geçici çözüm)

### Problem: Training çok yavaş
**Çözüm**:
- GPU instance kullanın (p3.2xlarge)
- Daha fazla CPU'lu instance seçin (c5.4xlarge)
- Batch size'ı azaltın

## 📚 Ek Kaynaklar

- [AWS EC2 Pricing](https://aws.amazon.com/ec2/pricing/)
- [AWS EC2 Instance Types](https://aws.amazon.com/ec2/instance-types/)
- [WikipediaML GitHub](https://github.com/ademcolak/WikipediaML)

## 🤝 Destek

Sorun yaşarsanız:
1. GitHub Issues'da sorun açın
2. Training log'larını paylaşın
3. Instance type ve konfigürasyonu belirtin