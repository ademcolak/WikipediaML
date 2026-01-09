# AWS EC2'de Training Çalıştırma Rehberi

## 🎯 Önemli: Nerede Çalışır?

**AWS EC2'de çalışır, yerel makinede değil!**

- ✅ Training **AWS EC2 instance'ında** çalışır
- ✅ Yerel makineni **kapatabilirsin** - EC2 bağımsız çalışır
- ✅ SSH bağlantısı kopsa bile training devam eder (arka planda)
- ✅ AWS Console'dan instance durumunu kontrol edebilirsin

## 🚀 3 Yöntem: Arka Planda Çalıştırma

### Yöntem 1: nohup (En Basit) ✅ Önerilen

```bash
# EC2'ye bağlan
ssh -i ~/.ssh/your-key.pem ec2-user@your-instance-ip

# Training'i başlat (arka planda)
cd ~/WikipediaML
source venv/bin/activate
nohup ./aws/run_training_pipeline.sh > logs/training.log 2>&1 &
echo $! > training.pid

# Bağlantıyı kapatabilirsin - training devam eder
exit
```

**Avantajlar:**
- ✅ Basit ve hızlı
- ✅ SSH kapansa bile çalışır
- ✅ Log dosyasına yazıyor

**Kontrol:**
```bash
# Tekrar bağlan
ssh -i ~/.ssh/your-key.pem ec2-user@your-instance-ip

# Log'u izle
tail -f ~/WikipediaML/logs/training.log

# Process'i kontrol et
ps aux | grep run_training_pipeline
```

---

### Yöntem 2: screen (Daha İyi Kontrol) ⭐ En İyi

```bash
# EC2'ye bağlan
ssh -i ~/.ssh/your-key.pem ec2-user@your-instance-ip

# Screen session başlat
screen -S training

# Training'i başlat
cd ~/WikipediaML
source venv/bin/activate
./aws/run_training_pipeline.sh

# Screen'den çık (Ctrl+A, sonra D)
# Training arka planda devam eder
```

**Avantajlar:**
- ✅ Geri dönüp canlı output görebilirsin
- ✅ SSH kapansa bile çalışır
- ✅ Birden fazla session yönetebilirsin

**Kontrol:**
```bash
# Tekrar bağlan
ssh -i ~/.ssh/your-key.pem ec2-user@your-instance-ip

# Screen session'ları listele
screen -ls

# Session'a geri dön
screen -r training

# Session'tan çıkmak: Ctrl+A, sonra D
# Session'u kapatmak: exit yaz
```

---

### Yöntem 3: tmux (Profesyonel) 🚀

```bash
# EC2'ye bağlan
ssh -i ~/.ssh/your-key.pem ec2-user@your-instance-ip

# Tmux session başlat
tmux new -s training

# Training'i başlat
cd ~/WikipediaML
source venv/bin/activate
./aws/run_training_pipeline.sh

# Tmux'tan çık (Ctrl+B, sonra D)
# Training arka planda devam eder
```

**Avantajlar:**
- ✅ En güçlü terminal multiplexer
- ✅ Pencere bölme, tab'lar
- ✅ SSH kapansa bile çalışır

**Kontrol:**
```bash
# Tekrar bağlan
ssh -i ~/.ssh/your-key.pem ec2-user@your-instance-ip

# Tmux session'ları listele
tmux ls

# Session'a geri dön
tmux attach -t training

# Session'tan çıkmak: Ctrl+B, sonra D
# Session'u kapatmak: exit yaz
```

---

## 📊 İlerlemeyi Takip Etme

### 1. Log Dosyasını İzle

```bash
# EC2'ye bağlan
ssh -i ~/.ssh/your-key.pem ec2-user@your-instance-ip

# Log'u canlı izle
tail -f ~/WikipediaML/logs/training.log

# Son 100 satırı göster
tail -n 100 ~/WikipediaML/logs/training.log

# Hata satırlarını filtrele
grep -i error ~/WikipediaML/logs/training.log
```

### 2. Process Durumunu Kontrol Et

```bash
# Training process'ini bul
ps aux | grep run_training_pipeline

# CPU ve RAM kullanımını göster
top -p $(pgrep -f run_training_pipeline)

# Disk kullanımını kontrol et
df -h
du -sh ~/WikipediaML/data/*
```

### 3. Checkpoint Dosyalarını Kontrol Et

```bash
# Checkpoint'leri listele
ls -lh ~/WikipediaML/data/checkpoints/

# Son checkpoint'i göster
ls -t ~/WikipediaML/data/checkpoints/*.tar.gz | head -1
```

### 4. AWS Console'dan Kontrol

1. AWS Console → EC2 Dashboard
2. Instances → Instance'ını seç
3. **Status Checks**: 2/2 checks passed ✅
4. **Monitoring**: CPU, Network, Disk kullanımı
5. **Instance State**: running ✅

---

## ⚠️ Önemli Notlar

### Yerel Makineyi Kapatabilirsin

✅ **Evet!** Yerel makineni kapatabilirsin. Training EC2'de çalışıyor, yerel makineye bağlı değil.

### SSH Bağlantısı Koparsa

✅ **Sorun değil!** nohup, screen veya tmux kullanıyorsan training devam eder.

### Instance'ı Durdurursan

❌ **Dikkat!** EC2 instance'ını durdurursan training durur. Ama:
- ✅ Checkpoint'ler kaydedildi
- ✅ Instance'ı tekrar başlatınca training resume edebilir

### Spot Instance Kesilirse

✅ **Sorun değil!** Checkpoint sistemi sayesinde:
- ✅ Training kaldığı yerden devam eder
- ✅ Spot instance tekrar başlatınca otomatik resume

---

## 🛑 Training'i Durdurma

### Güvenli Durdurma

```bash
# EC2'ye bağlan
ssh -i ~/.ssh/your-key.pem ec2-user@your-instance-ip

# Process ID'yi bul
cat ~/WikipediaML/training.pid

# Güvenli şekilde durdur (Ctrl+C gibi)
kill -SIGINT $(cat ~/WikipediaML/training.pid)

# Veya process'i bul ve durdur
pkill -f run_training_pipeline
```

**Not:** Checkpoint otomatik kaydedilir, kaldığı yerden devam edebilirsin.

### Acil Durdurma

```bash
# Zorla durdur (kullanma, checkpoint kaybolabilir)
pkill -9 -f run_training_pipeline
```

---

## 🔄 Training'i Devam Ettirme

Training durdurulduysa veya instance yeniden başlatıldıysa:

```bash
# EC2'ye bağlan
ssh -i ~/.ssh/your-key.pem ec2-user@your-instance-ip

# Virtual environment'ı aktive et
cd ~/WikipediaML
source venv/bin/activate

# Training'i tekrar başlat (otomatik resume)
nohup ./aws/run_training_pipeline.sh > logs/training.log 2>&1 &
```

**Not:** Script'ler otomatik olarak checkpoint'lerden devam eder.

---

## 📥 Sonuçları İndirme

Training tamamlandığında:

```bash
# Yerel makineden
cd ~/WikipediaML
source aws/config.sh  # EC2_HOST ve EC2_KEY ayarlı olmalı
./aws/sync_data.sh download
```

Veya manuel:

```bash
# Yerel makineden
scp -i ~/.ssh/your-key.pem \
    ec2-user@your-instance-ip:~/WikipediaML/models/checkpoints/*.pt \
    ./models/checkpoints/

scp -i ~/.ssh/your-key.pem \
    ec2-user@your-instance-ip:~/WikipediaML/data/checkpoints/*.tar.gz \
    ./data/checkpoints/
```

---

## 💡 Önerilen Workflow

1. **EC2 Instance Oluştur** (AWS Console)
2. **Setup Yap** (`./ec2_setup.sh`)
3. **Training Başlat** (screen ile):
   ```bash
   screen -S training
   cd ~/WikipediaML && source venv/bin/activate
   ./aws/run_training_pipeline.sh
   # Ctrl+A, D ile çık
   ```
4. **Yerel Makineyi Kapat** ✅
5. **Ara Sıra Kontrol Et**:
   ```bash
   ssh ... ec2-user@...
   screen -r training  # Durumu gör
   tail -f logs/training.log  # Log'u izle
   ```
6. **Training Tamamlanınca İndir**:
   ```bash
   ./aws/sync_data.sh download
   ```

---

## ❓ Sık Sorulan Sorular

**S: Yerel makineyi kapatabilir miyim?**
A: Evet! Training EC2'de çalışıyor, yerel makineye bağlı değil.

**S: SSH bağlantısı koparsa ne olur?**
A: nohup/screen/tmux kullanıyorsan training devam eder.

**S: Instance'ı durdurursam training durur mu?**
A: Evet, ama checkpoint'ler kaydedildi. Tekrar başlatınca resume eder.

**S: Hangi yöntemi kullanmalıyım?**
A: **screen** önerilir - basit ve güçlü.

**S: Training ne kadar sürer?**
A: Tam Wikipedia için 30-50 saat (m5.2xlarge).

**S: Maliyet ne kadar?**
A: Spot instance ile ~$7-8, On-Demand ile ~$18-21.

---

## 🎯 Özet

- ✅ Training **AWS EC2'de** çalışır
- ✅ Yerel makineni **kapatabilirsin**
- ✅ **screen** veya **nohup** kullan (arka planda)
- ✅ SSH kapansa bile **devam eder**
- ✅ Checkpoint'ler **otomatik kaydedilir**
- ✅ Instance durursa **resume edebilirsin**

**En İyi Pratik:** `screen -S training` ile başlat, yerel makineyi kapat, ara sıra kontrol et! 🚀
