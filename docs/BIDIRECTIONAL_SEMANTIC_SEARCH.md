# 🔄 Bidirectional Semantic Search - Detaylı Açıklama

## 🎯 Amaç

Normal beam search tek yönlü çalışır (start → target). Bu exponential growth'a neden olur:
- Seviye 1: k sayfa
- Seviye 2: k² sayfa
- Seviye d: k^d sayfa

**Bidirectional search** hem baştan hem sondan arar ve kesişme noktasını bulur:
- Forward d/2 seviye: k^(d/2) sayfa
- Backward d/2 seviye: k^(d/2) sayfa
- **Toplam: 2×k^(d/2) sayfa** (çok daha az!)

## 📊 Matematiksel Analiz

### Örnek: k=500 link/sayfa, d=4 adım

**Normal Beam Search:**
```
500^4 = 62,500,000,000 sayfa (teorik)
```

**Bidirectional Beam Search:**
```
2 × 500^2 = 500,000 sayfa
```

**Kazanç: 125,000x daha az!**

## 🔧 Algoritma

### 1. İki Beam Başlat

```python
# Forward: start → target
forward_beam = [(start, [start], 0.0)]
forward_visited = {start: [start]}

# Backward: target → start
backward_beam = [(target, [target], 0.0)]
backward_visited = {target: [target]}
```

### 2. Her Adımda İki Yönü Genişlet

```python
for depth in range(max_depth):
    # FORWARD: start'tan ilerle
    for current_page, path, score in forward_beam:
        links = get_page_links(current_page)
        
        # Semantic similarity hesapla (target'a göre)
        for link in links:
            similarity = cosine_similarity(link_emb, target_emb)
            
            # KESİŞME KONTROLÜ!
            if link in backward_visited:
                # BULUNDU! Path'leri birleştir
                return merge_paths(forward, backward)
    
    # BACKWARD: target'tan ilerle
    for current_page, path, score in backward_beam:
        links = get_page_links(current_page)
        
        # Semantic similarity hesapla (start'a göre!)
        for link in links:
            similarity = cosine_similarity(link_emb, start_emb)
            
            # KESİŞME KONTROLÜ!
            if link in forward_visited:
                # BULUNDU! Path'leri birleştir
                return merge_paths(forward, backward)
```

### 3. Path Birleştirme

```python
def merge_paths(forward_path, backward_path, intersection):
    # Forward: start → intersection
    # Backward: target → intersection (ters çevir!)
    
    complete_path = forward_path + reversed(backward_path)[1:]
    return complete_path
```

## 🧪 Gerçek Örnek: Porsche → Serik_Akhmetov

### Forward Search (Porsche'den):
```
Derinlik 1: Porsche
  → Ferdinand_Alexander_Porsche (0.213)
  → Tiger_II (0.206)
  → Porsche_Macan (0.203)

Derinlik 2: Tiger_II
  → Maybach_HL230 (0.312)
  → Indonesian_language (0.289)
  → Jagdpanzer (0.281)

Derinlik 3: Jagdpanzer
  → Jagdpanzer_IV (0.366)
  → Grey_iron (0.340)
  → Jagdpanther (0.338)

Derinlik 4: Jagdpanzer_IV
  → ... (devam ediyor)
```

### Backward Search (Serik_Akhmetov'dan):
```
Derinlik 1: Serik_Akhmetov
  → Russia (0.222)
  → Nur-Sultan (0.202)
  → Soviet_Union (0.186)

Derinlik 2: Nur-Sultan
  → Factory (0.310)
  → Russians (0.277)
  → Russian_SFSR (0.268)

Derinlik 3: Factory
  → Automobile (0.399) ← HUB SAYFA!
  → Volkswagen (0.390)
  → Slovakia (0.329)

Derinlik 4: Automobile
  → Porsche ← KESİŞME! ✅
```

### Kesişme Bulundu!
```
Forward: Porsche
Backward: Serik_Akhmetov → Nur-Sultan → Factory → Automobile → Porsche

Birleştirilmiş Path:
Porsche → Automobile → Factory → Nur-Sultan → Serik_Akhmetov
```

## 📊 Performance Karşılaştırması

### Test Sonuçları

| Test Case | Adım | Taranan Sayfa | Süre | Algoritma |
|-----------|------|---------------|------|-----------|
| Potato → Pizza | 2 | 3 | 2.47s | Bidirectional |
| Albert_Einstein → Physics | 1 | 1 | 0.91s | Bidirectional |
| Python → Machine_learning | 4 | 15 | 9.72s | Bidirectional |
| Porsche → Serik_Akhmetov | 4 | 18 | 11.67s | Bidirectional |

### Kazançlar

**Taranan Sayfa:**
- Normal beam search: ~100-200 sayfa (tahmin)
- Bidirectional: 3-18 sayfa
- **Kazanç: %80-90 azalma**

**Execution Time:**
- Normal beam search: ~30-60 saniye (tahmin)
- Bidirectional: 0.91-11.67 saniye
- **Kazanç: %70-80 hızlanma**

## 🔑 Anahtar Noktalar

### 1. Hub Sayfalar
Wikipedia'da bazı sayfalar çok bağlantılı (hub):
- United_States
- Italy
- Automobile
- Russia
- Computer

Bu sayfalar genellikle erken kesişme yaratır!

### 2. Semantic Similarity Yönü
- **Forward**: Target'a göre similarity (hedefe yaklaş)
- **Backward**: Start'a göre similarity (başlangıca yaklaş)
- İki yön birbirini tamamlar!

### 3. Beam Width
- Daha büyük beam = daha fazla alternatif = daha yüksek başarı
- Ama daha fazla sayfa tarama
- **Optimal: 3** (her yönde)

### 4. Max Depth
- Her yön için ayrı depth
- Total depth = forward_depth + backward_depth
- **Optimal: 6-8** (her yön için)

## 💡 Ne Zaman Kullanılmalı?

### Bidirectional İyi:
- ✅ Uzak path'ler (4+ adım)
- ✅ Bilinmeyen path'ler
- ✅ Hub sayfalar varsa
- ✅ Başarı oranı önemli

### Normal Beam İyi:
- ✅ Yakın path'ler (1-2 adım)
- ✅ Direkt link varsa
- ✅ Hız kritik (çok basit path)

## 🚀 Gelecek İyileştirmeler

### 1. Adaptive Beam Width
```python
# Kesişme yakınsa beam'i daralt
if intersection_likely:
    beam_width = 2
else:
    beam_width = 5
```

### 2. Hub Detection
```python
# Hub sayfaları önceliklendir
if page in known_hubs:
    similarity_score *= 1.5
```

### 3. Category-Based Search
```python
# Wikipedia kategorilerini kullan
if same_category(forward_page, backward_page):
    # Kesişme yakın!
```

## 📚 Referanslar

- [Bidirectional BFS Explained](BIDIRECTIONAL_BFS_EXPLAINED.md)
- [ROADMAP.md](ROADMAP.md) - Faz 1.2
- [Wikipedia: Bidirectional Search](https://en.wikipedia.org/wiki/Bidirectional_search)

---

**Versiyon:** 3.1.0
**Tarih:** 9 Aralık 2025
**Yazar:** WikipediaML Team