# 🚀 Neo4j Setup Guide - WikipediaML

## 📋 Hazırlık Tamamlandı!

✅ **docker-compose.yml** - Neo4j + Redis servisleri
✅ **Makefile** - Kolay komutlar
✅ **.env.example** - Environment variables

---

## 🎯 Adım Adım Kurulum

### 1️⃣ Docker Kurulu mu Kontrol Et

```bash
docker --version
docker-compose --version
```

**Yoksa kur:**
- Mac: Docker Desktop (https://www.docker.com/products/docker-desktop)
- Linux: `sudo apt install docker.io docker-compose`

---

### 2️⃣ Servisleri Başlat

```bash
# Tek komut ile her şeyi başlat
make setup
```

**Veya manuel:**
```bash
# Dependencies kur
make install

# Servisleri başlat
make start

# 10 saniye bekle
sleep 10
```

---

### 3️⃣ Neo4j Browser'ı Aç

```bash
# Otomatik aç
make neo4j-browser

# Veya manuel: http://localhost:7474
```

**Login:**
- Username: `neo4j`
- Password: `wikipediaml123`

---

### 4️⃣ Test Et

```bash
# Neo4j çalışıyor mu?
make status

# Neo4j shell'e gir
make neo4j-shell

# Redis çalışıyor mu?
make redis-cli
```

---

## 🎯 Kullanım

### Servis Yönetimi

```bash
# Başlat
make start

# Durdur
make stop

# Yeniden başlat
make restart

# Log'ları izle
make logs

# Durum kontrol
make status
```

---

### Database Erişimi

```bash
# Neo4j Cypher Shell
make neo4j-shell

# Neo4j Browser
make neo4j-browser

# Redis CLI
make redis-cli
```

---

### Training

```bash
# Hızlı training (50 çift)
make train

# Büyük training (500 çift)
make train-large

# Arka planda training
make train-bg
```

---

### Test

```bash
# Basit test
make test

# ML ile test
make test-ml
```

---

## 📊 Servis Bilgileri

### Neo4j
- **Browser:** http://localhost:7474
- **Bolt:** bolt://localhost:7687
- **Username:** neo4j
- **Password:** wikipediaml123
- **Memory:** 2GB heap, 1GB pagecache

### Redis
- **Host:** localhost
- **Port:** 6379
- **Memory:** 2GB max
- **Policy:** allkeys-lru

---

## 🔧 Sorun Giderme

### Port zaten kullanımda
```bash
# Çalışan servisleri durdur
make stop

# Veya port'u değiştir (docker-compose.yml)
```

### Docker izni yok
```bash
# Linux'ta
sudo usermod -aG docker $USER
# Logout/login gerekli
```

### Servis başlamıyor
```bash
# Log'ları kontrol et
make logs

# Yeniden başlat
make restart
```

---

## 🎯 Sonraki Adımlar

### 1. Neo4j Driver Implementation
```bash
# src/neo4j_graph.py oluşturulacak
# Neo4j bağlantısı ve temel operasyonlar
```

### 2. Hybrid Knowledge Graph
```bash
# src/hybrid_knowledge_graph.py oluşturulacak
# NetworkX + Neo4j birlikte çalışacak
```

### 3. Migration Script
```bash
# scripts/migrate_to_neo4j.py oluşturulacak
# Mevcut graph'i Neo4j'ye taşıyacak
```

---

## ✅ Kurulum Tamamlandı mı?

**Kontrol listesi:**
- [ ] Docker kurulu
- [ ] `make start` çalıştı
- [ ] Neo4j Browser açıldı (http://localhost:7474)
- [ ] Login başarılı (neo4j/wikipediaml123)
- [ ] `make status` servisleri gösteriyor

**Hepsi ✅ ise:** Neo4j driver implementation'a geçebiliriz! 🚀

---

## 📝 Notlar

- İlk başlatma 30-60 saniye sürebilir
- Neo4j plugins (APOC, GDS) otomatik yüklenir
- Data Docker volume'lerde saklanır (kalıcı)
- `make clean-all` her şeyi siler (dikkat!)

---

**Hazır mısın?** Servisleri başlat ve bana söyle! 🎉