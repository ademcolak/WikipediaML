# AWS EC2 Hızlı Başlangıç Rehberi

WikipediaML'i AWS EC2'de 10 dakikada çalıştırın! 🚀

## 📋 Ön Gereksinimler

- ✅ AWS hesabı
- ✅ SSH key pair (.pem dosyası)
- ✅ Yerel makinede SSH client

## 🚀 3 Adımda Başlangıç

### 1️⃣ EC2 Instance Oluştur

**AWS Console'da:**
1. EC2 Dashboard → "Launch Instance"
2. **AMI**: Amazon Linux 2023 veya Ubuntu 22.04
3. **Instance Type**: `m5.2xlarge` (8 vCPU, 32 GB RAM)
4. **Storage**: 200 GB gp3
5. **Security Group**: SSH (22) portunu açın
6. **Key Pair**: Yeni oluştur veya mevcut birini seç
7. "Launch Instance" tıkla

**Tahmini Maliyet**: ~$0.38/saat (~$20-40 tam eğitim için)

### 2️⃣ Kurulum Yap

```bash
# EC2'ye bağlan
ssh -i ~/.ssh/your-key.pem ec2-user@your-instance-ip

# Setup script'ini çalıştır
curl -O https://raw.githubusercontent.com/ademcolak/WikipediaML/main/aws/ec2_setup.sh
chmod +x ec2_setup.sh
./ec2_setup.sh
```

⏱️ **Süre**: ~5 dakika

### 3️⃣ Training'i Başlat

**Önemli:** Training EC2'de çalışır, yerel makineni kapatabilirsin!

```bash
cd ~/WikipediaML
source venv/bin/activate

# Yöntem 1: nohup (basit)
nohup ./aws/run_training_pipeline.sh > logs/training.log 2>&1 &
echo $! > training.pid

# Yöntem 2: screen (önerilen - daha iyi kontrol)
screen -S training
./aws/run_training_pipeline.sh
# Ctrl+A, sonra D ile çık (training devam eder)

# Log'u takip et
tail -f logs/training.log
```

**Detaylı rehber:** [`docs/aws/RUNNING_ON_AWS.md`](../aws/RUNNING_ON_AWS.md)

⏱️ **Training Süresi**: 30-50 saat (tam Wikipedia için)

## 📊 İlerlemeyi Takip Et

### Yerel Makineden

```bash
# Config dosyasını oluştur
cd ~/WikipediaML/aws
cp config.example.sh config.sh

# Değerleri güncelle
nano config.sh
# EC2_HOST="ec2-user@your-instance-ip"
# EC2_KEY="~/.ssh/your-key.pem"

# Durumu kontrol et
./sync_data.sh status
```

### Veya Quick Deploy Script Kullan

```bash
# İnteraktif menü
./aws/quick_deploy.sh

# Seçenekler:
# 1) Setup EC2 instance
# 2) Start training
# 3) Check status
# 4) Download models
# 5) Stop training
# 6) View logs
```

## 📥 Eğitilmiş Modeli İndir

Training tamamlandığında:

```bash
# Yerel makineden
cd ~/WikipediaML
source aws/config.sh
./aws/sync_data.sh download
```

İndirilen dosyalar:
- ✅ `models/mlp_scorer_best.pt` - Eğitilmiş model
- ✅ `data/adjacency_map.npz` - Bilgi grafiği
- ✅ `data/embeddings.npy` - Sayfa embeddings
- ✅ `data/page_mappings.pkl` - Sayfa eşlemeleri

## 🎮 Modeli Test Et

```bash
# Yerel makinede
cd ~/WikipediaML
source venv/bin/activate

# Benchmark testi
python3 scripts/benchmark_navigator.py

# Veya interaktif test
python3 -c "
from core.beam_search import BeamSearchNavigator
nav = BeamSearchNavigator()
result = nav.search('Python', 'Computer', max_depth=6)
print(result['path'])
"
```

## 💰 Maliyeti Düşür

### Training Tamamlandıktan Sonra

```bash
# 1. Verileri indir
./aws/sync_data.sh download

# 2. Instance'ı durdur (terminate değil!)
# AWS Console'dan veya:
aws ec2 stop-instances --instance-ids i-xxxxx

# 3. Sadece storage için ödeme yaparsınız (~$20/ay)
```

### Spot Instance Kullan

%70'e kadar daha ucuz! Training kesintiye uğrayabilir ama checkpoint'ler sayesinde devam eder.

**AWS Console'da:**
- Instance Type seçerken "Spot" seçeneğini işaretle
- Maximum price: On-Demand fiyatının %100'ü

## 🔧 Sorun Giderme

### SSH bağlanamıyorum
```bash
# Key izinlerini kontrol et
chmod 400 ~/.ssh/your-key.pem

# Security group'u kontrol et (AWS Console)
# SSH (22) portunu kendi IP'nize açın
```

### Disk doldu
```bash
# EC2'de
cd ~/WikipediaML

# Eski checkpoint'leri temizle
rm -f data/checkpoints/checkpoint_*.tar.gz

# Wikipedia dump'larını sil (parse sonrası)
rm -f data/wikipedia_dumps/*.sql.gz
```

### Training çok yavaş
```bash
# Daha güçlü instance'a geç:
# - c5.4xlarge (16 vCPU) - CPU yoğun işler için
# - p3.2xlarge (GPU) - Embedding ve MLP training için
```

### Memory yetersiz
```bash
# Daha fazla RAM'li instance seç:
# - m5.4xlarge (64 GB RAM)
# - r5.2xlarge (64 GB RAM, memory optimized)
```

## 📚 Detaylı Dokümantasyon

- 📖 [Tam AWS Rehberi](../aws/README.md) - Detaylı açıklamalar
- 🔧 [Troubleshooting](../aws/README.md#monitoring-ve-troubleshooting)
- 💰 [Maliyet Optimizasyonu](../aws/README.md#maliyet-optimizasyonu)

## 🆘 Yardım

Sorun mu yaşıyorsunuz?

1. **Log'ları kontrol edin**: `tail -f ~/WikipediaML/logs/training.log`
2. **GitHub Issues**: [Sorun bildirin](https://github.com/ademcolak/WikipediaML/issues)
3. **Dokümantasyon**: [docs/aws/README.md](README.md)

## ✅ Checklist

Training başlamadan önce:

- [ ] EC2 instance oluşturuldu (m5.2xlarge veya daha büyük)
- [ ] 200 GB storage eklendi
- [ ] SSH (22) portu açık
- [ ] Setup script çalıştırıldı
- [ ] Training başlatıldı (nohup ile)
- [ ] Log takibi yapılıyor

Training tamamlandıktan sonra:

- [ ] Veriler yerel makineye indirildi
- [ ] Model test edildi
- [ ] Instance durduruldu (maliyet için)
- [ ] Checkpoint'ler yedeklendi

## 🎉 Başarılı!

Artık tam Wikipedia bilgi grafiğine sahip bir ML modeliniz var! 

**Sonraki adımlar:**
- Modeli kendi projelerinizde kullanın
- Farklı navigasyon stratejileri deneyin
- Kaggle yarışmalarında test edin

İyi eğlenceler! 🚀