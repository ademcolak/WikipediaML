# 🚨 Acil Durdurma Rehberi

## ⚠️ Problem: Ctrl+C Çalışmıyor!

### Neden Olur?
- Embedding hesaplama sırasında thread takılır
- Sentence-BERT model GPU/CPU'da kilitleniyor
- KeyboardInterrupt yakalanmıyor

---

## 🛑 Acil Durdurma Yöntemleri

### Yöntem 1: Zorla Durdur (Önerilen)
```bash
# Mac/Linux:
Ctrl+Z  # Process'i durdur
kill %1  # Process'i öldür

# Veya:
ps aux | grep python  # Process ID'yi bul
kill -9 <PID>  # Zorla öldür
```

### Yöntem 2: Terminal'i Kapat
```bash
# Terminal penceresini kapat
# Yeni terminal aç
# Process otomatik ölecek
```

### Yöntem 3: Activity Monitor / Task Manager
```
1. Activity Monitor (Mac) / Task Manager (Windows) aç
2. "Python" process'ini bul
3. "Force Quit" / "End Task" tıkla
```

---

## 🔧 Kalıcı Çözüm

### Problem: Embedding Hesaplama Çok Yavaş

**Sebep:**
- 156 link × 100ms = 15+ saniye
- Bu süre boyunca KeyboardInterrupt yakalanmıyor
- Sentence-BERT model thread-safe değil

**Çözüm 1: Daha Az Link İşle**
```bash
# Max steps azalt (daha az link bulur)
python train_ml_model.py --pairs 3 --max-steps 3
```

**Çözüm 2: Timeout Ekle**
Script'e timeout mekanizması ekleyelim (geliştiriciler için)

---

## 🚀 Önerilen Kullanım

### Donma Riskini Azalt

#### 1. Çok Az Pair Kullan
```bash
# 3 pair, 3 adım - en güvenli
python train_ml_model.py --pairs 3 --max-steps 3
```

#### 2. Verbose Kapat (Daha Hızlı)
```bash
python train_ml_model.py --pairs 3 --max-steps 3 --no-verbose
```

#### 3. Arka Planda Çalıştır
```bash
# Terminal'i kapatsan bile çalışır
nohup python train_ml_model.py --pairs 3 --max-steps 3 > training.log 2>&1 &

# Process ID'yi kaydet
echo $! > training.pid

# Durdurmak için:
kill $(cat training.pid)
```

---

## 🐛 Debug: Neden Takılıyor?

### Olası Sebepler

1. **Embedding Hesaplama**
   - Sentence-BERT çok yavaş
   - 156 link için 15-30 saniye
   - Bu süre boyunca KeyboardInterrupt yakalanmıyor

2. **Thread Kilidi**
   - PyTorch thread'leri kilitlenebilir
   - GPU kullanımı varsa daha da yavaş

3. **Memory Leak**
   - Çok fazla embedding cache'leniyor
   - Bellek dolunca yavaşlıyor

---

## 💡 Hızlı Çözümler

### Şu An Ne Yapmalı?

#### Durum 1: Hala Çalışıyor
```bash
# 1. Zorla durdur
Ctrl+Z
kill %1

# 2. Veya terminal'i kapat
```

#### Durum 2: Durdu Ama Process Hala Aktif
```bash
# Process'i bul ve öldür
ps aux | grep python
kill -9 <PID>
```

#### Durum 3: Her Şey Durdu
```bash
# Yeni terminal aç
# Daha güvenli parametrelerle başlat
python train_ml_model.py --pairs 3 --max-steps 3
```

---

## 🎯 Güvenli Kullanım Parametreleri

### Donma Riski: Düşük ✅
```bash
# 3 pair, 3 adım, ~1 dakika
python train_ml_model.py --pairs 3 --max-steps 3
```

### Donma Riski: Orta ⚠️
```bash
# 5 pair, 5 adım, ~2-3 dakika
python train_ml_model.py --pairs 5 --max-steps 5
```

### Donma Riski: Yüksek ❌
```bash
# 10 pair, 10 adım, ~10-15 dakika
python train_ml_model.py --quick
```

---

## 🔍 Process Yönetimi

### Process'i Bul
```bash
# Mac/Linux:
ps aux | grep "train_ml_model"

# Çıktı:
# user  12345  50.0  2.0  ... python train_ml_model.py --quick
#       ^^^^^ 
#       PID
```

### Process'i Durdur
```bash
# Nazikçe durdur (önce bunu dene)
kill 12345

# Zorla durdur (çalışmazsa)
kill -9 12345

# Tüm Python process'lerini durdur (DİKKAT!)
killall python
```

### Process'i İzle
```bash
# CPU/Memory kullanımını izle
top -p 12345

# Veya:
htop  # Daha güzel görünüm
```

---

## 📝 Gelecek İçin Notlar

### Script İyileştirmeleri (Geliştiriciler İçin)

1. **Timeout Ekle**
   ```python
   import signal
   
   def timeout_handler(signum, frame):
       raise TimeoutError("Embedding timeout!")
   
   signal.signal(signal.SIGALRM, timeout_handler)
   signal.alarm(30)  # 30 saniye timeout
   ```

2. **Progress Bar Ekle**
   ```python
   from tqdm import tqdm
   
   for link in tqdm(links, desc="Computing embeddings"):
       embedding = embedder.get_embedding(link)
   ```

3. **Batch Embedding**
   ```python
   # Tek tek yerine batch olarak
   embeddings = embedder.batch_encode(links)
   ```

4. **KeyboardInterrupt Handler**
   ```python
   try:
       # Training code
   except KeyboardInterrupt:
       print("\n⚠️  Interrupted! Saving progress...")
       save_progress()
       sys.exit(0)
   ```

---

## 🎓 Özet

**Problem:** Ctrl+C çalışmıyor  
**Sebep:** Embedding hesaplama sırasında thread takılıyor  
**Çözüm:** Zorla durdur (kill -9) veya terminal'i kapat

**Acil Durdurma:**
```bash
# Mac/Linux:
Ctrl+Z
kill %1

# Veya:
ps aux | grep python
kill -9 <PID>
```

**Güvenli Kullanım:**
```bash
# En güvenli (1 dakika)
python train_ml_model.py --pairs 3 --max-steps 3

# Orta risk (2-3 dakika)
python train_ml_model.py --pairs 5 --max-steps 5
```

**Önerim:** 
1. Şimdi zorla durdur (kill -9)
2. `--pairs 3 --max-steps 3` ile tekrar başlat
3. 1 dakika içinde bitecek!

---

**Versiyon:** 3.4.0  
**Son Güncelleme:** 10 Aralık 2024