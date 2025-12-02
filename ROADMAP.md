# 🗺️ Wikipedia ML - Detaylı Yol Haritası

## 📍 FAZ 1: BASIC PATHFINDING (Model Kullanmadan)

### 1.1 BFS (Breadth-First Search) İmplementasyonu
**Amaç**: En kısa path'i garantili bir şekilde bulmak (adım sayısı açısından).

**Yapılacaklar**:
- [ ] `PathFinder` sınıfı oluştur (`src/pathfinder.py`)
- [ ] BFS algoritması implementasyonu
- [ ] Verbose mode: Her explore edilen sayfayı logla
- [ ] Path reconstruction: Hedefe nasıl ulaştığını göster
- [ ] Performance metrics:
  - Kaç sayfa tarandı
  - Kaç adımda buldu
  - Toplam süre
  - Memory kullanımı

**Öğrenilecekler**:
- Queue veri yapısı ve BFS mantığı
- Visited tracking (döngülerden kaçınma)
- Parent tracking (path'i geri oluşturma)

**Test Senaryosu**:
```
Başlangıç: "Potato" → Hedef: "Barack_Obama"
Beklenen: Çalışır bir path bulmalı ve adımları göstermeli
```

### 1.2 Bidirectional BFS (İki Yönlü Arama)
**Amaç**: Performance optimization - hem baştan hem sondan ara.

**Yapılacaklar**:
- [ ] Bidirectional BFS implementasyonu
- [ ] İki aramanın kesişme noktasını bulma
- [ ] Performance karşılaştırması (normal BFS vs bidirectional)

**Öğrenilecekler**:
- İki yönlü arama mantığı
- Intersection detection
- Time/space complexity analizi

### 1.3 Heuristic-Based Search (A*)
**Amaç**: Daha akıllı arama - hedefe daha yakın sayfaları önceliklendir.

**Yapılacaklar**:
- [ ] Basit heuristic'ler:
  - Link count similarity (kaç ortak link var)
  - Page title similarity (kelime benzerliği)
  - Category overlap (ortak kategoriler)
- [ ] A* algoritması implementasyonu
- [ ] Priority queue kullanımı
- [ ] Heuristic effectiveness analizi

**Öğrenilecekler**:
- A* ve informed search
- Heuristic tasarımı
- Priority queue veri yapısı

---

## 📍 FAZ 2: EMBEDDED MODEL İLE AKILLI SEÇİM

### 2.1 Sentence Transformers Kurulumu
**Amaç**: Sayfa ve link'lerin semantic meaning'ini anlamak.

**Yapılacaklar**:
- [ ] `sentence-transformers` kurulumu
- [ ] Model yükle (örn: `all-MiniLM-L6-v2` - hızlı ve küçük)
- [ ] Embedding generation fonksiyonları
- [ ] `src/embedder.py` oluştur

**Öğrenilecekler**:
- Sentence embeddings nedir
- Cosine similarity
- Vector space'de semantic search

**Test**:
```python
"Potato" ile "Vegetable" daha yakın mı, yoksa "Computer" mı?
```

### 2.2 Semantic Link Selection
**Amaç**: Hedef sayfaya semantically en yakın link'i seç.

**Yapılacaklar**:
- [ ] Hedef sayfa embedding'i
- [ ] Her link'in embedding'i (link text + kısa açıklama)
- [ ] Cosine similarity hesapla
- [ ] En yüksek similarity'ye sahip link'i seç
- [ ] `SemanticNavigator` sınıfı (`src/semantic_navigator.py`)

**Öğrenilecekler**:
- Greedy semantic search
- Embedding caching (performans)
- Batch processing

**Karşılaştırma**:
- Random walk vs Semantic selection
- Success rate, adım sayısı, süre

### 2.3 Beam Search ile Çoklu Path Exploration
**Amaç**: Sadece en iyi değil, top-k linkleri paralel explore et.

**Yapılacaklar**:
- [ ] Beam search implementasyonu
- [ ] Beam width parametresi (kaç alternatif path)
- [ ] Her path için score tracking
- [ ] Visualization (hangi path'ler explore edildi)

**Öğrenilecekler**:
- Beam search algoritması
- Trade-off: exploration vs exploitation
- Parallel thinking

---

## 📍 FAZ 3: REINFORCEMENT LEARNING YAKLAŞIMI (Opsiyonel ama öğretici)

### 3.1 Q-Learning Basics
**Amaç**: Agent'ın deneme-yanılma ile öğrenmesi.

**Yapılacaklar**:
- [ ] State representation (current page + target page)
- [ ] Action space (hangi linke tıkla)
- [ ] Reward function:
  - Hedefe ulaştı: +100
  - Hedefe yaklaştı: +10
  - Uzaklaştı: -5
  - Her adım: -1
- [ ] Q-table veya Q-network
- [ ] Training loop

**Öğrenilecekler**:
- RL basics: state, action, reward
- Exploration vs exploitation (epsilon-greedy)
- Q-learning update rule

### 3.2 Policy Gradient / Actor-Critic (İleri seviye)
**Amaç**: Daha sofistike RL yaklaşımı.

**Yapılacaklar**:
- [ ] Policy network (hangi linke tıklama olasılığı)
- [ ] Value network (bu state ne kadar iyi)
- [ ] Training loop
- [ ] Experience replay

---

## 📍 FAZ 4: CLAUDE API ENTEGRASYONU

### 4.1 Claude API Setup
**Amaç**: Claude'un reasoning yeteneğini kullanmak.

**Yapılacaklar**:
- [ ] `anthropic` library kurulumu
- [ ] API key yönetimi (.env)
- [ ] `src/claude_navigator.py` oluştur
- [ ] Rate limiting ve cost tracking

### 4.2 Prompt Engineering
**Amaç**: Claude'a görevi en iyi şekilde açıklamak.

**Yapılacaklar**:
- [ ] System prompt tasarla:
  ```
  Sen bir Wikipedia navigator'sın. Amacın [START] sayfasından
  [TARGET] sayfasına en az adımda ulaşmak. Mevcut sayfadaki
  linklerden en uygun olanını seç ve nedenini açıkla.
  ```
- [ ] Few-shot examples (örnek path'ler)
- [ ] Chain-of-thought reasoning
- [ ] Link'leri context ile ver (sadece başlık değil, açıklama da)

**Öğrenilecekler**:
- Prompt engineering best practices
- Chain-of-thought reasoning
- Few-shot learning

### 4.3 Hybrid Approach
**Amaç**: Embedded model + Claude'u birlikte kullan.

**Yapılacaklar**:
- [ ] Embedded model ile top-10 link bul
- [ ] Bu 10 link'i Claude'a ver (cost reduction)
- [ ] Claude en iyisini seçsin ve açıklasın

---

## 📍 FAZ 5: KNOWLEDGE GRAPH

### 5.1 Graph Construction
**Amaç**: Öğrenilen path'leri ve ilişkileri sakla.

**Yapılacaklar**:
- [ ] NetworkX ile basit graph
- [ ] Her başarılı path'i graph'a ekle
- [ ] Node properties: page title, categories, link count
- [ ] Edge properties: traversal count, success rate
- [ ] Graph serialization (pickle/JSON)

**Öğrenilecekler**:
- Graph veri yapısı
- NetworkX kullanımı
- Graph persistence

### 5.2 Graph-Based Pathfinding
**Amaç**: Daha önce öğrenilen path'leri kullan.

**Yapılacaklar**:
- [ ] Graph'ta path var mı kontrol et
- [ ] Partial match (A→B→? ve ?→C→D varsa, birleştir)
- [ ] Graph-based heuristics (bu node'dan genellikle nereye gidilir)
- [ ] Confidence scores

### 5.3 Neo4j Integration (Production-ready)
**Amaç**: Büyük graph'lar için production database.

**Yapılacaklar**:
- [ ] Neo4j kurulumu (Docker)
- [ ] Cypher query'leri
- [ ] Graph algorithms (shortest path, PageRank)
- [ ] Visualization (Neo4j Browser)

---

## 📍 BONUS: ADVANCED FEATURES

### B.1 Multi-Language Support
- [ ] Farklı dillerde Wikipedia (tr.wikipedia.org)
- [ ] Cross-language path finding

### B.2 Web Interface
- [ ] Flask/FastAPI backend
- [ ] React frontend
- [ ] Real-time visualization
- [ ] Interactive mode

### B.3 Competitive Mode
- [ ] Farklı algoritmalar yarışsın
- [ ] Leaderboard
- [ ] Different metrics (speed, accuracy, cost)

---

## 🎯 ŞU ANKİ DURUM

Şu anda: **Faz 1 öncesi** (random walk var ama path finding yok)

**İlk adım**: Faz 1.1 - BFS implementasyonu

## 📊 İLERLEME TAKİBİ

- [ ] Faz 1: Basic Pathfinding
  - [ ] 1.1 BFS
  - [ ] 1.2 Bidirectional BFS
  - [ ] 1.3 A* with Heuristics
- [ ] Faz 2: Embedded Model
  - [ ] 2.1 Setup
  - [ ] 2.2 Semantic Selection
  - [ ] 2.3 Beam Search
- [ ] Faz 3: RL (Opsiyonel)
- [ ] Faz 4: Claude API
  - [ ] 4.1 Setup
  - [ ] 4.2 Prompt Engineering
  - [ ] 4.3 Hybrid
- [ ] Faz 5: Knowledge Graph
  - [ ] 5.1 Construction
  - [ ] 5.2 Graph-based Search
  - [ ] 5.3 Neo4j
