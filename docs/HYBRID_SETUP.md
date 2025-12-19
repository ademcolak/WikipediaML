# Hybrid Navigation Setup Guide

## 10K Edge Milestone Reached! 🎉

Artık LLM + Embedding entegrasyonu ile %70-80 doğruluk hedefine ulaşabiliriz.

---

## Kurulum

### 1. Venv'i Aktif Et
```bash
cd /Users/ademcolak/dev/arge/WikipediaML
source venv/bin/activate  # Mac/Linux
# VEYA
venv\Scripts\activate  # Windows
```

### 2. Yeni Paketleri Yükle
```bash
pip install -r requirements.txt
```

**Yüklenecek yeni paketler:**
- `anthropic` - Claude API
- `sentence-transformers` - Embedding modeli
- `numpy` - Matematiksel işlemler

---

## API Key Setup

### Anthropic API Key Al

1. https://console.anthropic.com/ 'a git
2. Giriş yap
3. "API Keys" → "Create Key"
4. Key'i kopyala

### .env Dosyası Oluştur
```bash
# Proje kök dizininde
echo "ANTHROPIC_API_KEY=your_api_key_here" > .env
```

**VEYA** manuel olarak `.env` dosyası oluştur:
```
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxx
```

---

## Sistem Mimarisi

### Üç Katmanlı Sistem

```
┌─────────────────────────────────────────┐
│  1. KG Lookup (En Hızlı, Ücretsiz)     │
│     - 0.1 saniye                        │
│     - %30-40 hit rate (10K edge'de)    │
└─────────────────────────────────────────┘
              ↓ (KG'de yoksa)
┌─────────────────────────────────────────┐
│  2. Embedding Filter (Orta Hızlı)      │
│     - 1-2 saniye                        │
│     - Top 5 link seçer                  │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  3. LLM Selection (En Doğru)           │
│     - 3-5 saniye                        │
│     - ~$0.02 per query                  │
│     - %80+ doğruluk                     │
└─────────────────────────────────────────┘
```

---

## Kullanım

### Basit Test
```python
from src.knowledge_graph import WikiKnowledgeGraph
from src.hybrid_navigator import HybridNavigator

# KG'yi yükle
kg = WikiKnowledgeGraph()

# Hybrid navigator oluştur
navigator = HybridNavigator(
    kg=kg,
    use_embedding=True,
    use_llm=True
)

# Test et
available_links = ["Rome", "Milan", "Venice", "Italian_cuisine"]
next_step = navigator.find_next_step(
    current_page="Italy",
    target_page="Pizza",
    available_links=available_links
)

print(f"Next step: {next_step}")

# İstatistikleri gör
stats = navigator.get_stats()
print(stats)
```

### Main.py ile Kullanım
```bash
# Hybrid mode ile çalıştır
python main.py Italy Pizza --hybrid

# Sadece embedding (LLM yok)
python main.py Italy Pizza --embedding

# Sadece KG (eski sistem)
python main.py Italy Pizza
```

---

## Performans Beklentileri

### 10K Edge'de (Şu An)
- **KG hit rate:** %30-40
- **Ortalama süre:** ~3-4 saniye
- **Doğruluk:** %70-80
- **Maliyet:** ~$1.50 per 100 query

### 25K Edge'de (1 Ay Sonra)
- **KG hit rate:** %60-70
- **Ortalama süre:** ~2-3 saniye
- **Doğruluk:** %75-85
- **Maliyet:** ~$0.70 per 100 query

### 50K Edge'de (2-3 Ay Sonra)
- **KG hit rate:** %80-90
- **Ortalama süre:** ~1-2 saniye
- **Doğruluk:** %85-90
- **Maliyet:** ~$0.30 per 100 query

---

## Maliyet Kontrolü

### LLM Kullanımını Azaltma

#### 1. Sadece Zor Case'lerde LLM Kullan
```python
# Embedding confidence threshold
navigator = HybridNavigator(
    kg=kg,
    use_embedding=True,
    use_llm=True,
    llm_threshold=0.8  # Sadece similarity < 0.8 ise LLM kullan
)
```

#### 2. LLM'i Kapat (Sadece Embedding)
```python
navigator = HybridNavigator(
    kg=kg,
    use_embedding=True,
    use_llm=False  # LLM kapalı
)
```

#### 3. Her İkisini Kapat (Sadece KG)
```python
navigator = HybridNavigator(
    kg=kg,
    use_embedding=False,
    use_llm=False
)
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'anthropic'"
```bash
source venv/bin/activate
pip install anthropic
```

### "ANTHROPIC_API_KEY not found"
```bash
# .env dosyası oluştur
echo "ANTHROPIC_API_KEY=your_key" > .env
```

### "sentence-transformers model download failed"
```bash
# İlk çalıştırmada model indirilir (~90MB)
# İnternet bağlantısı gerekli
# Sonraki kullanımlarda cache'den yüklenir
```

### LLM Çok Pahalı
```bash
# LLM'i kapat, sadece embedding kullan
python main.py Italy Pizza --embedding
```

---

## Sonraki Adımlar

### 1. Test Et
```bash
# Basit test
python main.py Italy Rome --hybrid

# Zor test
python main.py Philosophy Mathematics --hybrid
```

### 2. İstatistikleri İzle
```python
stats = navigator.get_stats()
print(f"KG hit rate: {stats['kg_hit_rate']:.1f}%")
print(f"LLM cost: ${stats['llm_stats']['total_cost']:.2f}")
```

### 3. KG'yi Büyütmeye Devam Et
```bash
# 25K edge hedefi
python train.py --strategy hybrid --workers 2 --iterations 1000
```

---

## Özet

**Yeni Özellikler:**
- ✅ LLM Navigator (Claude Haiku)
- ✅ Embedding Navigator (Sentence-BERT)
- ✅ Hybrid Navigator (3-tier system)
- ✅ Maliyet kontrolü
- ✅ İstatistik takibi

**Beklenen Sonuç:**
- 🎯 %70-80 doğruluk
- ⚡ 3-4 saniye ortalama
- 💰 ~$1.50 per 100 query

**Kurulum:**
```bash
source venv/bin/activate
pip install -r requirements.txt
echo "ANTHROPIC_API_KEY=your_key" > .env
python main.py Italy Pizza --hybrid
```

**Başarılar!** 🚀