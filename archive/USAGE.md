# 🚀 WikipediaML - Kullanım Kılavuzu

## 📋 Hızlı Başlangıç

### Basit Kullanım (Sync Mode)
```bash
python main.py Potato Pizza
```

### Hızlı Kullanım (Async Mode - ÖNERİLİR!)
```bash
python main.py Potato Pizza --async
```

### Claude ile Akıllı Arama
```bash
python main.py Potato Pizza --async --claude
```

---

## 🎯 Kullanım Örnekleri

### 1. Basit Path'ler
```bash
# Sync mode
python main.py Albert_Einstein Physics

# Async mode (2-3x daha hızlı!)
python main.py Albert_Einstein Physics --async
```

**Sonuç:**
```
Path: Albert_Einstein → Physics
Süre: 0.74s (async) vs 0.84s (sync)
```

---

### 2. Orta Zorluk Path'ler
```bash
python main.py Python_(programming_language) Machine_learning --async
```

**Sonuç:**
```
Path: Python_(programming_language) → Machine_learning
Süre: 0.70s
Adım: 1
```

---

### 3. Kompleks Path'ler
```bash
python main.py Porsche Serik_Akhmetov_Government --async
```

**Sonuç:**
```
Path: Porsche → Germany → Kazakhstan → Serik_Akhmetov_Government
Süre: ~5-8s
Adım: 4
```

---

## 🚀 Mode Karşılaştırması

### Sync Mode (Default)
```bash
python main.py <start> <target>
```

**Özellikler:**
- ✅ Hybrid Search (Graph + Beam Search)
- ✅ Knowledge Graph cache
- ✅ Bidirectional beam search
- ⚠️  Sıralı sayfa çekme (daha yavaş)

**Ne Zaman Kullanılır:**
- Basit path'ler (1-2 adım)
- Graph cache hit (anında sonuç)
- Network bağlantısı yavaş

---

### Async Mode (ÖNERİLİR!)
```bash
python main.py <start> <target> --async
```

**Özellikler:**
- ✅ Paralel sayfa çekme (3x daha hızlı!)
- ✅ Async bidirectional beam search
- ✅ Aynı accuracy, daha hızlı
- ✅ Büyük beam width'te çok etkili

**Ne Zaman Kullanılır:**
- Orta/kompleks path'ler (3+ adım)
- İlk çalıştırma (graph cache yok)
- Hız önemli

**Performans:**
```
Sync:  1.53s (Potato → Pizza)
Async: 0.66s (Potato → Pizza)
Speedup: 2.32x (%56.9 daha hızlı)
```

---

### Claude Mode (Akıllı!)
```bash
python main.py <start> <target> --claude
# veya
python main.py <start> <target> --async --claude
```

**Özellikler:**
- ✅ Claude reasoning (en akıllı seçim)
- ✅ Açıklamalı kararlar
- ⚠️  API key gerekli
- ⚠️  Daha yavaş (API call)

**Setup:**
```bash
export ANTHROPIC_API_KEY='your-api-key'
```

**Ne Zaman Kullanılır:**
- Çok zor path'ler
- Reasoning görmek istiyorsanız
- Accuracy > Speed

---

## 📊 Performans Karşılaştırması

| Senaryo | Sync | Async | Speedup |
|---------|------|-------|---------|
| Basit (1 adım) | 0.80s | 0.70s | 1.13x |
| Orta (2-3 adım) | 1.53s | 0.66s | 2.32x |
| Kompleks (4+ adım) | 13.85s | 4-5s | 3x |
| Graph Cache Hit | 0.00s | 0.00s | - |

---

## 🎓 İpuçları

### 1. Sayfa İsimleri
Wikipedia URL'indeki `/wiki/` sonrası kısmı kullanın:
```
✅ Doğru: Python_(programming_language)
❌ Yanlış: Python (programming language)

✅ Doğru: United_States
❌ Yanlış: United States
```

### 2. İlk Çalıştırma
İlk çalıştırmada model indirilir (~80MB):
```bash
python main.py Potato Pizza --async
# Model indiriliyor... (bir kere)
```

### 3. Graph Cache
Aynı path'i tekrar çalıştırırsanız anında sonuç:
```bash
# İlk çalıştırma
python main.py Potato Pizza --async  # 0.66s

# İkinci çalıştırma
python main.py Potato Pizza          # 0.00s (graph cache!)
```

### 4. Async + Claude
En iyi sonuç için ikisini birlikte kullanın:
```bash
python main.py <start> <target> --async --claude
```

---

## 🔧 Troubleshooting

### "Module not found" Hatası
```bash
# Virtual environment aktif et
source venv/bin/activate

# Dependencies kur
pip install -r requirements.txt
```

### "ANTHROPIC_API_KEY not found" Hatası
```bash
# API key ekle
export ANTHROPIC_API_KEY='your-api-key'

# veya .env dosyası oluştur
echo "ANTHROPIC_API_KEY=your-api-key" > .env
```

### Yavaş Çalışıyor
```bash
# Async mode kullan
python main.py <start> <target> --async

# Graph cache'i kontrol et
ls wiki_graph.pkl  # Varsa cache aktif
```

---

## 📈 Gelecek Özellikler

- [ ] Wikipedia Categories integration
- [ ] Persistent embedding cache
- [ ] Hub page detection
- [ ] GPU acceleration
- [ ] Web UI (Dash)
- [ ] Multi-language support

---

## 🎯 Önerilen Kullanım

### Günlük Kullanım
```bash
python main.py <start> <target> --async
```

### Zor Path'ler
```bash
python main.py <start> <target> --async --claude
```

### Hızlı Test
```bash
python main.py <start> <target>  # Graph cache varsa anında
```

---

**Versiyon:** 3.2.0  
**Son Güncelleme:** 9 Aralık 2024  
**Async Support:** ✅ Aktif