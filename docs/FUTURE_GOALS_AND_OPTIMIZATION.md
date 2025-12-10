# 🚀 WikipediaML: Gelecek Hedefler ve Optimizasyon Stratejileri

## 📋 İçindekiler
1. [Mevcut Durum](#mevcut-durum)
2. [Performans Optimizasyonları](#performans-optimizasyonları)
3. [Knowledge Graph İyileştirmeleri](#knowledge-graph-iyileştirmeleri)
4. [Machine Learning Geliştirmeleri](#machine-learning-geliştirmeleri)
5. [Ölçeklenebilirlik](#ölçeklenebilirlik)
6. [Yeni Özellikler](#yeni-özellikler)
7. [Uygulama Planı](#uygulama-planı)

---

## 🎯 Mevcut Durum

### Tamamlanan Optimizasyonlar (Phase 1 & 2)

**Phase 1: Core Optimizations** ✅
- ✅ Knowledge Graph Optimization (A* search, PageRank, pruning)
- ✅ Aggressive Batch Processing (adaptive sizing, connection pooling)
- ✅ Category Hierarchy Enhancement (multi-level analysis, depth scoring)
- **Beklenen İyileşme**: %170-270 performans artışı

**Phase 2: Machine Learning** ✅
- ✅ ML-based Link Scoring (10 features, XGBoost)
- ✅ Self-Supervised Learning (otomatik training data)
- ✅ Online Learning (incremental updates)
- **Beklenen İyileşme**: %30-50 accuracy artışı

### Mevcut Performans Metrikleri
```
Ortalama Arama Süresi: ~15-30 saniye
Başarı Oranı: %60-80
Ortalama Path Uzunluğu: 4-6 adım
Bellek Kullanımı: ~500MB-1GB
```

---

## ⚡ Performans Optimizasyonları

### 1. Caching Stratejileri

#### 1.1 Multi-Level Cache Sistemi
```python
# Öncelik sırası:
1. Memory Cache (LRU) - En sık kullanılan 10K sayfa
2. Redis Cache - Orta sıklıkta kullanılan 100K sayfa
3. Disk Cache - Nadir kullanılan sayfalar
4. Wikipedia API - Cache miss durumunda
```

**Beklenen İyileşme**: %40-60 hız artışı

**Uygulama**:
```python
class MultiLevelCache:
    def __init__(self):
        self.memory_cache = LRUCache(maxsize=10000)
        self.redis_client = redis.Redis()
        self.disk_cache = DiskCache('cache/')
    
    async def get(self, key):
        # 1. Memory cache
        if key in self.memory_cache:
            return self.memory_cache[key]
        
        # 2. Redis cache
        value = await self.redis_client.get(key)
        if value:
            self.memory_cache[key] = value
            return value
        
        # 3. Disk cache
        value = self.disk_cache.get(key)
        if value:
            await self.redis_client.set(key, value, ex=3600)
            self.memory_cache[key] = value
            return value
        
        return None
```

#### 1.2 Embedding Cache
- Sentence-BERT embeddings çok pahalı (her biri ~100ms)
- 1M sayfa için pre-computed embeddings: ~4GB
- Sık kullanılan 100K sayfa için cache

**Beklenen İyileşme**: %70-80 embedding hesaplama süresinde azalma

#### 1.3 Category Cache
- Category hierarchy çok stabil (günlük değişim %0.1)
- Tüm category tree'yi cache'le (günlük güncelleme)
- Parent-child ilişkilerini memory'de tut

**Beklenen İyileşme**: %90 category lookup süresinde azalma

### 2. Parallelization

#### 2.1 Multi-Process Search
```python
# Her process farklı search strategy kullanır:
Process 1: BFS (breadth-first)
Process 2: A* (heuristic-based)
Process 3: Bidirectional (two-way)
Process 4: ML-guided (machine learning)

# İlk bulan kazanır!
```

**Beklenen İyileşme**: %50-70 hız artışı

#### 2.2 GPU Acceleration
```python
# Batch embedding calculation on GPU
import torch

class GPUEmbedder:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.model = self.model.to('cuda')
    
    def batch_encode(self, texts, batch_size=256):
        # GPU'da batch processing
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            emb = self.model.encode(batch, convert_to_tensor=True)
            embeddings.append(emb.cpu().numpy())
        return np.vstack(embeddings)
```

**Beklenen İyileşme**: %80-90 embedding süresinde azalma

### 3. Algorithm Optimizations

#### 3.1 Beam Search
```python
# A* yerine Beam Search kullan
# Her adımda en iyi K candidate'i tut

class BeamSearch:
    def __init__(self, beam_width=5):
        self.beam_width = beam_width
    
    def search(self, start, target):
        beam = [(start, 0, [start])]  # (page, score, path)
        
        while beam:
            # En iyi K candidate'i genişlet
            next_beam = []
            for page, score, path in beam:
                links = self.get_links(page)
                for link in links:
                    new_score = self.score(link, target)
                    next_beam.append((link, new_score, path + [link]))
            
            # En iyi K'yi seç
            beam = sorted(next_beam, key=lambda x: x[1])[:self.beam_width]
```

**Beklenen İyileşme**: %30-40 daha iyi path quality

#### 3.2 Iterative Deepening
```python
# Önce shallow search, sonra deep search
# Hızlı sonuç + optimal path

for depth in [3, 5, 7, 10, 15]:
    result = search(start, target, max_depth=depth)
    if result.found:
        return result
```

**Beklenen İyileşme**: %40-50 ortalama hız artışı

---

## 🕸️ Knowledge Graph İyileştirmeleri

### 1. Graph Compression

#### 1.1 Hub-Based Compression
```python
# Hub page'leri özel işle
# Örnek: "United_States" → 500K+ link
# Sadece en önemli 1000 link'i sakla

class CompressedGraph:
    def __init__(self):
        self.hub_threshold = 10000  # 10K+ link = hub
        self.max_hub_links = 1000
    
    def add_page(self, page, links):
        if len(links) > self.hub_threshold:
            # Hub page - sadece en önemli link'leri sakla
            scored_links = self.score_links(page, links)
            links = scored_links[:self.max_hub_links]
        
        self.graph.add_node(page, links=links)
```

**Beklenen İyileşme**: %60-70 bellek kullanımında azalma

#### 1.2 Edge Pruning
```python
# Düşük skorlu edge'leri sil
# Örnek: semantic_similarity < 0.1

def prune_edges(self, threshold=0.1):
    edges_to_remove = []
    for u, v, data in self.G.edges(data=True):
        if data.get('weight', 0) < threshold:
            edges_to_remove.append((u, v))
    
    self.G.remove_edges_from(edges_to_remove)
```

**Beklenen İyileşme**: %40-50 graph size azalma

### 2. Graph Indexing

#### 2.1 Spatial Index (R-tree)
```python
# Embedding space'de spatial index
# Nearest neighbor search: O(log n)

from rtree import index

class SpatialGraphIndex:
    def __init__(self):
        self.idx = index.Index()
        self.embeddings = {}
    
    def add_page(self, page, embedding):
        # Embedding'i 2D'ye project et (PCA)
        coords = self.project_2d(embedding)
        self.idx.insert(id, coords)
        self.embeddings[page] = embedding
    
    def find_nearest(self, target_embedding, k=10):
        coords = self.project_2d(target_embedding)
        nearest_ids = list(self.idx.nearest(coords, k))
        return [self.id_to_page[id] for id in nearest_ids]
```

**Beklenen İyileşme**: %80-90 nearest neighbor search hızı

#### 2.2 Inverted Index
```python
# Kelime bazlı index
# "Machine Learning" → [AI, Computer_Science, ...]

class InvertedIndex:
    def __init__(self):
        self.index = defaultdict(set)
    
    def add_page(self, page):
        words = page.lower().replace('_', ' ').split()
        for word in words:
            self.index[word].add(page)
    
    def search(self, query):
        words = query.lower().split()
        candidates = set()
        for word in words:
            candidates.update(self.index[word])
        return candidates
```

**Beklenen İyileşme**: %70-80 text-based search hızı

### 3. Graph Precomputation

#### 3.1 Shortest Path Cache
```python
# Popüler page pair'ler için shortest path'i önceden hesapla
# Örnek: "United_States" ↔ "World_War_II"

class ShortestPathCache:
    def __init__(self):
        self.cache = {}
        self.popular_pages = self.get_popular_pages(top_k=1000)
    
    def precompute(self):
        # Top 1000 page arasındaki tüm path'leri hesapla
        # 1000 * 1000 = 1M path
        for start in self.popular_pages:
            for target in self.popular_pages:
                if start != target:
                    path = self.find_shortest_path(start, target)
                    self.cache[(start, target)] = path
```

**Beklenen İyileşme**: %95 popüler query'lerde instant sonuç

#### 3.2 Community Detection
```python
# Graph'ı community'lere böl
# Aynı community içinde search daha hızlı

import networkx as nx

def detect_communities(self):
    communities = nx.community.louvain_communities(self.G)
    
    # Her page'in community'sini sakla
    self.page_to_community = {}
    for i, community in enumerate(communities):
        for page in community:
            self.page_to_community[page] = i
    
    return communities
```

**Beklenen İyileşme**: %40-50 intra-community search hızı

---

## 🤖 Machine Learning Geliştirmeleri

### 1. Model Architecture

#### 1.1 Deep Learning Model
```python
# XGBoost → Neural Network
# Daha karmaşık pattern'leri öğren

import torch.nn as nn

class LinkScorerNN(nn.Module):
    def __init__(self, input_dim=10):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
    
    def forward(self, x):
        return self.network(x)
```

**Beklenen İyileşme**: %10-20 accuracy artışı

#### 1.2 Graph Neural Network (GNN)
```python
# Graph structure'ı direkt öğren
# Node embeddings + edge features

import torch_geometric.nn as gnn

class WikiGNN(nn.Module):
    def __init__(self, hidden_dim=128):
        super().__init__()
        self.conv1 = gnn.GCNConv(768, hidden_dim)  # 768 = BERT dim
        self.conv2 = gnn.GCNConv(hidden_dim, hidden_dim)
        self.conv3 = gnn.GCNConv(hidden_dim, 1)
    
    def forward(self, x, edge_index):
        x = F.relu(self.conv1(x, edge_index))
        x = F.relu(self.conv2(x, edge_index))
        x = self.conv3(x, edge_index)
        return x
```

**Beklenen İyileşme**: %20-30 accuracy artışı

### 2. Feature Engineering

#### 2.1 Advanced Features
```python
# Mevcut 10 feature → 25+ feature

new_features = [
    # Temporal features
    'page_age',  # Sayfa yaşı
    'edit_frequency',  # Düzenleme sıklığı
    'view_count',  # Görüntülenme sayısı
    
    # Graph features
    'betweenness_centrality',  # Köprü özelliği
    'closeness_centrality',  # Merkeze yakınlık
    'clustering_coefficient',  # Kümelenme
    'pagerank_score',  # PageRank
    
    # Semantic features
    'word2vec_similarity',  # Word2Vec benzerlik
    'bert_similarity',  # BERT benzerlik
    'topic_similarity',  # LDA topic benzerlik
    
    # Category features
    'category_overlap_ratio',  # Kategori örtüşme oranı
    'category_tree_distance',  # Kategori ağacında mesafe
    'subcategory_count',  # Alt kategori sayısı
    
    # Link features
    'inlink_count',  # Gelen link sayısı
    'outlink_count',  # Giden link sayısı
    'mutual_links',  # Karşılıklı link sayısı
]
```

**Beklenen İyileşme**: %15-25 accuracy artışı

#### 2.2 Feature Selection
```python
# Feature importance analysis
# En önemli 15 feature'ı seç

from sklearn.feature_selection import SelectKBest, f_classif

def select_best_features(X, y, k=15):
    selector = SelectKBest(f_classif, k=k)
    X_selected = selector.fit_transform(X, y)
    
    # Seçilen feature'ları göster
    selected_features = selector.get_support(indices=True)
    return X_selected, selected_features
```

**Beklenen İyileşme**: %10-15 training hızı, daha az overfitting

### 3. Training Strategy

#### 3.1 Active Learning
```python
# En belirsiz örnekleri seç ve label'la
# Daha az data ile daha iyi model

class ActiveLearner:
    def __init__(self, model):
        self.model = model
        self.uncertainty_threshold = 0.3
    
    def select_uncertain_samples(self, X, n=100):
        # Model'in en belirsiz olduğu örnekleri seç
        probs = self.model.predict_proba(X)
        uncertainty = 1 - np.abs(probs[:, 1] - 0.5) * 2
        
        # En belirsiz n örneği seç
        uncertain_indices = np.argsort(uncertainty)[-n:]
        return uncertain_indices
```

**Beklenen İyileşme**: %50-60 daha az training data gereksinimi

#### 3.2 Curriculum Learning
```python
# Kolay örneklerden başla, zor örneklere geç
# Daha stabil training

class CurriculumTrainer:
    def __init__(self):
        self.difficulty_levels = [
            'easy',    # Path length < 3
            'medium',  # Path length 3-5
            'hard',    # Path length 5-7
            'expert'   # Path length > 7
        ]
    
    def train(self, model, data):
        for level in self.difficulty_levels:
            level_data = self.filter_by_difficulty(data, level)
            model.fit(level_data)
```

**Beklenen İyileşme**: %20-30 daha hızlı convergence

#### 3.3 Transfer Learning
```python
# Wikipedia dışındaki knowledge graph'lerden öğren
# Örnek: Wikidata, DBpedia, YAGO

class TransferLearner:
    def __init__(self):
        self.source_models = {
            'wikidata': self.load_wikidata_model(),
            'dbpedia': self.load_dbpedia_model(),
        }
    
    def transfer(self, target_model):
        # Source model'lerin weight'lerini transfer et
        for name, source_model in self.source_models.items():
            target_model.load_partial_weights(source_model)
```

**Beklenen İyileşme**: %30-40 daha az Wikipedia-specific training

---

## 📈 Ölçeklenebilirlik

### 1. Distributed System

#### 1.1 Microservices Architecture
```
┌─────────────────────────────────────────┐
│           API Gateway (FastAPI)          │
└─────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
┌───────▼──────┐ ┌──▼──────┐ ┌─▼─────────┐
│   Scraper    │ │ Embedder│ │  Search   │
│   Service    │ │ Service │ │  Service  │
└──────────────┘ └─────────┘ └───────────┘
        │           │           │
        └───────────┼───────────┘
                    │
        ┌───────────▼───────────┐
        │   Message Queue       │
        │   (RabbitMQ/Kafka)    │
        └───────────────────────┘
                    │
        ┌───────────▼───────────┐
        │   Database Cluster    │
        │   (PostgreSQL/MongoDB)│
        └───────────────────────┘
```

**Beklenen İyileşme**: 10x-100x throughput artışı

#### 1.2 Load Balancing
```python
# Request'leri multiple worker'a dağıt

from fastapi import FastAPI
from celery import Celery

app = FastAPI()
celery_app = Celery('tasks', broker='redis://localhost:6379')

@celery_app.task
def search_task(start, target):
    # Async search task
    result = navigator.search(start, target)
    return result

@app.post("/search")
async def search(start: str, target: str):
    # Task'ı queue'ya ekle
    task = search_task.delay(start, target)
    return {"task_id": task.id}
```

**Beklenen İyileşme**: 5x-10x concurrent request handling

### 2. Database Optimization

#### 2.1 Sharding
```python
# Page'leri multiple database'e böl
# Örnek: A-M → DB1, N-Z → DB2

class ShardedDatabase:
    def __init__(self):
        self.shards = {
            'shard1': Database('db1'),  # A-M
            'shard2': Database('db2'),  # N-Z
        }
    
    def get_shard(self, page):
        first_letter = page[0].upper()
        if first_letter <= 'M':
            return self.shards['shard1']
        else:
            return self.shards['shard2']
    
    def get_page(self, page):
        shard = self.get_shard(page)
        return shard.get(page)
```

**Beklenen İyileşme**: 2x-3x database throughput

#### 2.2 Read Replicas
```python
# Write → Master DB
# Read → Replica DB (multiple)

class ReplicatedDatabase:
    def __init__(self):
        self.master = Database('master')
        self.replicas = [
            Database('replica1'),
            Database('replica2'),
            Database('replica3'),
        ]
        self.replica_index = 0
    
    def write(self, key, value):
        # Write to master
        self.master.set(key, value)
    
    def read(self, key):
        # Read from replica (round-robin)
        replica = self.replicas[self.replica_index]
        self.replica_index = (self.replica_index + 1) % len(self.replicas)
        return replica.get(key)
```

**Beklenen İyileşme**: 3x-5x read throughput

---

## 🎨 Yeni Özellikler

### 1. Advanced Visualization

#### 1.1 Interactive 3D Graph
```python
# Plotly/Three.js ile 3D interactive graph
# Zoom, rotate, filter

import plotly.graph_objects as go

def create_3d_graph(graph, path):
    # Node positions (3D layout)
    pos = nx.spring_layout(graph, dim=3)
    
    # Create 3D scatter plot
    fig = go.Figure(data=[
        go.Scatter3d(
            x=[pos[node][0] for node in graph.nodes()],
            y=[pos[node][1] for node in graph.nodes()],
            z=[pos[node][2] for node in graph.nodes()],
            mode='markers+text',
            marker=dict(size=5, color='blue'),
            text=list(graph.nodes())
        )
    ])
    
    return fig
```

#### 1.2 Real-time Search Animation
```python
# Search progress'i real-time göster
# WebSocket ile live updates

from fastapi import WebSocket

@app.websocket("/ws/search")
async def websocket_search(websocket: WebSocket):
    await websocket.accept()
    
    # Search callback
    def on_step(current_page, visited_count):
        websocket.send_json({
            'current': current_page,
            'visited': visited_count,
            'timestamp': time.time()
        })
    
    result = navigator.search(start, target, callback=on_step)
    await websocket.send_json({'result': result})
```

### 2. Multi-Language Support

#### 2.1 Cross-Language Search
```python
# İngilizce → Türkçe Wikipedia
# "Machine Learning" → "Makine Öğrenmesi"

class MultilingualNavigator:
    def __init__(self):
        self.languages = ['en', 'tr', 'de', 'fr', 'es']
        self.translators = {
            lang: WikiTranslator(lang) for lang in self.languages
        }
    
    def search(self, start, target, source_lang='en', target_lang='tr'):
        # Translate start page
        start_translated = self.translators[target_lang].translate(start)
        
        # Search in target language
        result = self.navigators[target_lang].search(
            start_translated, target
        )
        
        return result
```

### 3. API Enhancements

#### 3.1 RESTful API
```python
# Comprehensive REST API

@app.get("/api/v1/search")
async def search(
    start: str,
    target: str,
    max_steps: int = 10,
    strategy: str = 'hybrid'
):
    """Find path between two Wikipedia pages."""
    result = navigator.search(start, target, max_steps, strategy)
    return result

@app.get("/api/v1/page/{page_name}")
async def get_page_info(page_name: str):
    """Get page information."""
    info = {
        'title': page_name,
        'categories': get_categories(page_name),
        'links': get_links(page_name),
        'embedding': get_embedding(page_name)
    }
    return info

@app.get("/api/v1/stats")
async def get_stats():
    """Get system statistics."""
    return {
        'total_searches': stats.total_searches,
        'success_rate': stats.success_rate,
        'avg_path_length': stats.avg_path_length,
        'cache_hit_rate': stats.cache_hit_rate
    }
```

#### 3.2 GraphQL API
```python
# Flexible query language

import strawberry
from strawberry.fastapi import GraphQLRouter

@strawberry.type
class Page:
    title: str
    categories: List[str]
    links: List[str]

@strawberry.type
class SearchResult:
    found: bool
    path: List[str]
    steps: int
    time: float

@strawberry.type
class Query:
    @strawberry.field
    def search(self, start: str, target: str) -> SearchResult:
        result = navigator.search(start, target)
        return SearchResult(
            found=result.found,
            path=result.path,
            steps=len(result.path),
            time=result.time
        )
    
    @strawberry.field
    def page(self, title: str) -> Page:
        return Page(
            title=title,
            categories=get_categories(title),
            links=get_links(title)
        )

schema = strawberry.Schema(query=Query)
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")
```

---

## 📅 Uygulama Planı

### Phase 3: Performance Optimization (2-3 hafta)

**Week 1: Caching**
- [ ] Multi-level cache implementation
- [ ] Embedding cache
- [ ] Category cache
- [ ] Benchmark: %40-60 hız artışı

**Week 2: Parallelization**
- [ ] Multi-process search
- [ ] GPU acceleration
- [ ] Beam search implementation
- [ ] Benchmark: %50-70 hız artışı

**Week 3: Graph Optimization**
- [ ] Graph compression
- [ ] Spatial indexing
- [ ] Shortest path cache
- [ ] Benchmark: %60-80 bellek azalma

### Phase 4: ML Enhancement (2-3 hafta)

**Week 1: Model Architecture**
- [ ] Neural network implementation
- [ ] GNN implementation
- [ ] Model comparison
- [ ] Benchmark: %20-30 accuracy artışı

**Week 2: Feature Engineering**
- [ ] 25+ feature extraction
- [ ] Feature selection
- [ ] Feature importance analysis
- [ ] Benchmark: %15-25 accuracy artışı

**Week 3: Training Strategy**
- [ ] Active learning
- [ ] Curriculum learning
- [ ] Transfer learning
- [ ] Benchmark: %30-40 daha az training data

### Phase 5: Scalability (3-4 hafta)

**Week 1-2: Microservices**
- [ ] Service decomposition
- [ ] Message queue setup
- [ ] Load balancing
- [ ] Benchmark: 10x throughput

**Week 3-4: Database**
- [ ] Sharding implementation
- [ ] Read replicas
- [ ] Query optimization
- [ ] Benchmark: 3x-5x database performance

### Phase 6: New Features (2-3 hafta)

**Week 1: Visualization**
- [ ] 3D interactive graph
- [ ] Real-time animation
- [ ] Dashboard

**Week 2: Multi-language**
- [ ] Cross-language search
- [ ] Translation integration
- [ ] Language detection

**Week 3: API**
- [ ] REST API completion
- [ ] GraphQL API
- [ ] API documentation

---

## 🎯 Beklenen Toplam İyileşme

### Performans
```
Mevcut: 15-30 saniye
Phase 3: 5-10 saniye (%60-70 iyileşme)
Phase 4: 3-7 saniye (%80-85 iyileşme)
Phase 5: 1-3 saniye (%90-95 iyileşme)
```

### Accuracy
```
Mevcut: %60-80
Phase 4: %75-90 (%15-25 iyileşme)
Phase 6: %80-95 (%20-30 iyileşme)
```

### Scalability
```
Mevcut: 1-10 concurrent users
Phase 5: 100-1000 concurrent users (100x iyileşme)
```

### Bellek
```
Mevcut: 500MB-1GB
Phase 3: 200-400MB (%60-70 azalma)
```

---

## 🔧 Hızlı Başlangıç İçin Öncelikler

### Kısa Vadeli (1-2 hafta)
1. **Embedding Cache** - En kolay, en etkili
2. **Beam Search** - Algoritma iyileştirmesi
3. **Graph Compression** - Bellek optimizasyonu

### Orta Vadeli (1-2 ay)
1. **Neural Network Model** - Accuracy artışı
2. **Multi-process Search** - Hız artışı
3. **REST API** - Kullanılabilirlik

### Uzun Vadeli (3-6 ay)
1. **Microservices** - Ölçeklenebilirlik
2. **GNN Model** - State-of-the-art accuracy
3. **Multi-language** - Global kullanım

---

## 📊 Benchmark Metrikleri

### Ölçülecek Metrikler
```python
metrics = {
    # Performance
    'avg_search_time': float,
    'p50_search_time': float,
    'p95_search_time': float,
    'p99_search_time': float,
    
    # Accuracy
    'success_rate': float,
    'avg_path_length': float,
    'optimal_path_ratio': float,
    
    # Resource Usage
    'memory_usage': float,
    'cpu_usage': float,
    'cache_hit_rate': float,
    
    # Scalability
    'throughput': float,  # requests/second
    'concurrent_users': int,
    'queue_length': int,
}
```

### Benchmark Script
```python
# benchmark.py

import time
import psutil
from typing import List, Dict

class Benchmark:
    def __init__(self, navigator):
        self.navigator = navigator
        self.results = []
    
    def run_benchmark(self, test_cases: List[Tuple[str, str]], iterations=10):
        """Run benchmark on test cases."""
        for start, target in test_cases:
            times = []
            for _ in range(iterations):
                start_time = time.time()
                result = self.navigator.search(start, target)
                elapsed = time.time() - start_time
                
                times.append(elapsed)
                self.results.append({
                    'start': start,
                    'target': target,
                    'time': elapsed,
                    'found': result.found,
                    'path_length': len(result.path) if result.found else None
                })
            
            print(f"{start} → {target}")
            print(f"  Avg: {np.mean(times):.2f}s")
            print(f"  P50: {np.percentile(times, 50):.2f}s")
            print(f"  P95: {np.percentile(times, 95):.2f}s")
    
    def get_summary(self) -> Dict:
        """Get benchmark summary."""
        times = [r['time'] for r in self.results]
        found = [r['found'] for r in self.results]
        
        return {
            'total_searches': len(self.results),
            'success_rate': sum(found) / len(found),
            'avg_time': np.mean(times),
            'p50_time': np.percentile(times, 50),
            'p95_time': np.percentile(times, 95),
            'p99_time': np.percentile(times, 99),
        }
```

---

## 🎓 Öğrenme Kaynakları

### Graph Algorithms
- [NetworkX Documentation](https://networkx.org/)
- [Graph Neural Networks (Stanford CS224W)](http://web.stanford.edu/class/cs224w/)
- [A* Search Algorithm](https://en.wikipedia.org/wiki/A*_search_algorithm)

### Machine Learning
- [XGBoost Documentation](https://xgboost.readthedocs.io/)
- [PyTorch Geometric](https://pytorch-geometric.readthedocs.io/)
- [Active Learning Survey](https://arxiv.org/abs/2009.00236)

### Distributed Systems
- [Microservices Patterns](https://microservices.io/patterns/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Celery Documentation](https://docs.celeryproject.org/)

### Optimization
- [Python Performance Tips](https://wiki.python.org/moin/PythonSpeed/PerformanceTips)
- [Caching Strategies](https://aws.amazon.com/caching/)
- [Database Sharding](https://en.wikipedia.org/wiki/Shard_(database_architecture))

---

## 📝 Sonuç

Bu dokümanda WikipediaML projesinin gelecek hedeflerini ve optimizasyon stratejilerini detaylı olarak açıkladık. 

**Ana Hedefler**:
1. ⚡ **%90-95 hız artışı** (15-30s → 1-3s)
2. 🎯 **%20-30 accuracy artışı** (%60-80 → %80-95)
3. 📈 **100x ölçeklenebilirlik** (1-10 → 100-1000 concurrent users)
4. 💾 **%60-70 bellek azalma** (500MB-1GB → 200-400MB)

**Öncelikli Adımlar**:
1. Embedding cache (kolay + etkili)
2. Beam search (algoritma iyileştirmesi)
3. Neural network model (accuracy artışı)

**Tahmini Süre**: 3-6 ay (part-time)

Başarılar! 🚀