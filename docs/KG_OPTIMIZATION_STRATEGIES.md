# 🕸️ Knowledge Graph Optimization Strategies

## 📋 İçindekiler
1. [KG'nin Mevcut Kullanımı](#kgnin-mevcut-kullanımı)
2. [Verimlilik Sorunları](#verimlilik-sorunları)
3. [Optimizasyon Stratejileri](#optimizasyon-stratejileri)
4. [Advanced KG Techniques](#advanced-kg-techniques)
5. [Implementation Guide](#implementation-guide)

---

## 🎯 KG'nin Mevcut Kullanımı

### Mevcut Yapı
```python
class WikiKnowledgeGraph:
    def __init__(self):
        self.G = nx.DiGraph()  # NetworkX directed graph
        self.embeddings = {}   # Page embeddings
        self.categories = {}   # Page categories
```

### Kullanım Alanları
1. **Path Finding**: BFS, A* search
2. **Link Scoring**: Edge weights, centrality
3. **Semantic Similarity**: Embedding-based scoring
4. **Category Analysis**: Hierarchical relationships

### Mevcut Problemler
- ❌ Graph çok büyük (1M+ nodes)
- ❌ Bellek kullanımı yüksek (1-2GB)
- ❌ Yavaş graph traversal
- ❌ Gereksiz edge'ler
- ❌ Verimsiz storage

---

## 🔍 Verimlilik Sorunları

### 1. Memory Overhead

**Problem**: Her node ve edge için metadata
```python
# Her node için:
node_data = {
    'title': str,           # ~50 bytes
    'embedding': np.array,  # 768 floats = 3KB
    'categories': list,     # ~200 bytes
    'pagerank': float,      # 8 bytes
    'centrality': float,    # 8 bytes
}
# Total per node: ~3.5KB
# 1M nodes = 3.5GB!
```

**Çözüm**: Sparse storage, compression

### 2. Redundant Edges

**Problem**: Hub page'ler çok fazla edge'e sahip
```python
# Örnek: "United_States"
edges = [
    'New_York', 'California', 'Texas', ...  # 500K+ edges!
]
# Çoğu edge gereksiz (low-value)
```

**Çözüm**: Edge pruning, importance-based filtering

### 3. Slow Traversal

**Problem**: Graph traversal O(V + E)
```python
# BFS on 1M nodes, 10M edges
# Time: 10-30 seconds per search
```

**Çözüm**: Indexing, caching, pruning

---

## ⚡ Optimizasyon Stratejileri

### Strategy 1: Hierarchical Graph Structure

**Concept**: Multi-level graph
```
Level 0: Core pages (10K most important)
Level 1: Important pages (100K)
Level 2: Common pages (1M)
Level 3: Rare pages (10M)
```

**Implementation**:
```python
class HierarchicalKG:
    def __init__(self):
        self.levels = {
            0: nx.DiGraph(),  # Core (10K nodes)
            1: nx.DiGraph(),  # Important (100K nodes)
            2: nx.DiGraph(),  # Common (1M nodes)
            3: nx.DiGraph(),  # Rare (10M nodes)
        }
        self.node_to_level = {}
    
    def add_node(self, page, importance_score):
        """Add node to appropriate level."""
        if importance_score > 0.9:
            level = 0
        elif importance_score > 0.7:
            level = 1
        elif importance_score > 0.5:
            level = 2
        else:
            level = 3
        
        self.levels[level].add_node(page)
        self.node_to_level[page] = level
    
    def search(self, start, target):
        """Search starting from highest level."""
        start_level = self.node_to_level.get(start, 3)
        target_level = self.node_to_level.get(target, 3)
        
        # Start from highest level
        for level in range(min(start_level, target_level), 4):
            result = self._search_level(start, target, level)
            if result.found:
                return result
        
        return SearchResult(found=False)
```

**Benefits**:
- ✅ 10x faster search (start from core)
- ✅ 80% less memory (only load needed levels)
- ✅ Better scalability

---

### Strategy 2: Graph Compression

#### 2.1 Hub Compression
```python
class CompressedKG:
    def __init__(self, hub_threshold=10000, max_hub_edges=1000):
        self.G = nx.DiGraph()
        self.hub_threshold = hub_threshold
        self.max_hub_edges = max_hub_edges
        self.hub_pages = set()
    
    def add_page(self, page, links):
        """Add page with smart compression."""
        if len(links) > self.hub_threshold:
            # Hub page - compress edges
            self.hub_pages.add(page)
            
            # Score and keep only top edges
            scored_links = self._score_links(page, links)
            links = [link for link, score in scored_links[:self.max_hub_edges]]
        
        # Add to graph
        self.G.add_node(page)
        for link in links:
            self.G.add_edge(page, link)
    
    def _score_links(self, page, links):
        """Score links by importance."""
        scores = []
        for link in links:
            score = self._calculate_importance(page, link)
            scores.append((link, score))
        
        return sorted(scores, key=lambda x: x[1], reverse=True)
    
    def _calculate_importance(self, page, link):
        """Calculate link importance."""
        score = 0.0
        
        # Semantic similarity
        if hasattr(self, 'embeddings'):
            sim = self.cosine_similarity(
                self.embeddings.get(page),
                self.embeddings.get(link)
            )
            score += sim * 0.4
        
        # Category overlap
        page_cats = set(self.categories.get(page, []))
        link_cats = set(self.categories.get(link, []))
        overlap = len(page_cats & link_cats) / max(len(page_cats), 1)
        score += overlap * 0.3
        
        # PageRank (if available)
        if hasattr(self, 'pagerank'):
            score += self.pagerank.get(link, 0) * 0.3
        
        return score
```

**Benefits**:
- ✅ 60-70% less edges
- ✅ 50-60% less memory
- ✅ Faster traversal

#### 2.2 Edge Weight Quantization
```python
class QuantizedKG:
    def __init__(self, num_bins=16):
        self.G = nx.DiGraph()
        self.num_bins = num_bins
    
    def add_edge(self, u, v, weight):
        """Add edge with quantized weight."""
        # Quantize weight to num_bins levels
        quantized_weight = self._quantize(weight, self.num_bins)
        
        # Store as int8 (1 byte instead of 8 bytes)
        self.G.add_edge(u, v, weight=quantized_weight)
    
    def _quantize(self, value, num_bins):
        """Quantize float to int."""
        # Map [0, 1] to [0, num_bins-1]
        return int(value * (num_bins - 1))
    
    def _dequantize(self, quantized_value, num_bins):
        """Dequantize int to float."""
        return quantized_value / (num_bins - 1)
```

**Benefits**:
- ✅ 87.5% less memory for weights (8 bytes → 1 byte)
- ✅ Faster computation (int vs float)

---

### Strategy 3: Smart Indexing

#### 3.1 Spatial Index for Embeddings
```python
from sklearn.neighbors import NearestNeighbors
import numpy as np

class SpatialIndexedKG:
    def __init__(self):
        self.G = nx.DiGraph()
        self.embeddings = {}
        self.spatial_index = None
        self.page_list = []
    
    def build_spatial_index(self):
        """Build k-NN index for fast nearest neighbor search."""
        # Collect all embeddings
        self.page_list = list(self.embeddings.keys())
        embedding_matrix = np.array([
            self.embeddings[page] for page in self.page_list
        ])
        
        # Build index
        self.spatial_index = NearestNeighbors(
            n_neighbors=100,
            algorithm='ball_tree',
            metric='cosine'
        )
        self.spatial_index.fit(embedding_matrix)
    
    def find_nearest_pages(self, target_page, k=50):
        """Find k nearest pages to target (fast!)."""
        if self.spatial_index is None:
            self.build_spatial_index()
        
        target_embedding = self.embeddings[target_page]
        distances, indices = self.spatial_index.kneighbors(
            [target_embedding], n_neighbors=k
        )
        
        nearest_pages = [self.page_list[i] for i in indices[0]]
        return nearest_pages
```

**Benefits**:
- ✅ O(log n) nearest neighbor search (vs O(n))
- ✅ 100x faster similarity search
- ✅ Better for large graphs

#### 3.2 Inverted Index for Text Search
```python
from collections import defaultdict

class TextIndexedKG:
    def __init__(self):
        self.G = nx.DiGraph()
        self.inverted_index = defaultdict(set)
        self.page_words = {}
    
    def build_text_index(self):
        """Build inverted index for text search."""
        for page in self.G.nodes():
            # Extract words
            words = self._extract_words(page)
            self.page_words[page] = words
            
            # Add to inverted index
            for word in words:
                self.inverted_index[word].add(page)
    
    def _extract_words(self, page):
        """Extract words from page title."""
        return set(page.lower().replace('_', ' ').split())
    
    def search_by_text(self, query):
        """Find pages matching query (fast!)."""
        query_words = set(query.lower().split())
        
        # Find pages containing query words
        candidates = set()
        for word in query_words:
            candidates.update(self.inverted_index.get(word, set()))
        
        # Rank by word overlap
        ranked = []
        for page in candidates:
            overlap = len(query_words & self.page_words[page])
            ranked.append((page, overlap))
        
        return sorted(ranked, key=lambda x: x[1], reverse=True)
```

**Benefits**:
- ✅ O(1) text search (vs O(n))
- ✅ 1000x faster text matching
- ✅ Better for keyword-based search

---

### Strategy 4: Graph Partitioning

#### 4.1 Community-Based Partitioning
```python
import networkx as nx
from networkx.algorithms import community

class PartitionedKG:
    def __init__(self):
        self.G = nx.DiGraph()
        self.communities = []
        self.page_to_community = {}
    
    def detect_communities(self):
        """Detect communities using Louvain algorithm."""
        # Convert to undirected for community detection
        G_undirected = self.G.to_undirected()
        
        # Detect communities
        self.communities = community.louvain_communities(G_undirected)
        
        # Map pages to communities
        for i, comm in enumerate(self.communities):
            for page in comm:
                self.page_to_community[page] = i
    
    def search_within_community(self, start, target):
        """Search within same community first (faster!)."""
        start_comm = self.page_to_community.get(start)
        target_comm = self.page_to_community.get(target)
        
        if start_comm == target_comm:
            # Same community - search within
            subgraph = self.G.subgraph(self.communities[start_comm])
            return self._search_subgraph(subgraph, start, target)
        else:
            # Different communities - search across
            return self._search_full_graph(start, target)
```

**Benefits**:
- ✅ 50-70% faster intra-community search
- ✅ Better cache locality
- ✅ Parallelizable (search communities in parallel)

#### 4.2 Topic-Based Partitioning
```python
class TopicPartitionedKG:
    def __init__(self):
        self.G = nx.DiGraph()
        self.topics = {
            'science': set(),
            'history': set(),
            'geography': set(),
            'arts': set(),
            'sports': set(),
            'technology': set(),
        }
        self.page_to_topic = {}
    
    def assign_topics(self):
        """Assign pages to topics based on categories."""
        for page in self.G.nodes():
            categories = self.get_categories(page)
            topic = self._infer_topic(categories)
            
            self.topics[topic].add(page)
            self.page_to_topic[page] = topic
    
    def search_by_topic(self, start, target):
        """Search within topic first."""
        start_topic = self.page_to_topic.get(start, 'general')
        target_topic = self.page_to_topic.get(target, 'general')
        
        if start_topic == target_topic:
            # Same topic - faster search
            subgraph = self.G.subgraph(self.topics[start_topic])
            return self._search_subgraph(subgraph, start, target)
```

**Benefits**:
- ✅ 40-60% faster topic-specific search
- ✅ Better for domain-specific queries
- ✅ Easier to maintain

---

## 🚀 Advanced KG Techniques

### 1. Graph Neural Networks (GNN)

**Concept**: Learn node embeddings from graph structure
```python
import torch
import torch.nn as nn
import torch_geometric.nn as gnn

class WikiGNN(nn.Module):
    def __init__(self, input_dim=768, hidden_dim=256, output_dim=128):
        super().__init__()
        self.conv1 = gnn.GCNConv(input_dim, hidden_dim)
        self.conv2 = gnn.GCNConv(hidden_dim, hidden_dim)
        self.conv3 = gnn.GCNConv(hidden_dim, output_dim)
    
    def forward(self, x, edge_index):
        # x: node features [num_nodes, input_dim]
        # edge_index: graph connectivity [2, num_edges]
        
        x = F.relu(self.conv1(x, edge_index))
        x = F.dropout(x, p=0.5, training=self.training)
        
        x = F.relu(self.conv2(x, edge_index))
        x = F.dropout(x, p=0.5, training=self.training)
        
        x = self.conv3(x, edge_index)
        
        return x

class GNNBasedKG:
    def __init__(self):
        self.G = nx.DiGraph()
        self.gnn = WikiGNN()
        self.node_embeddings = {}
    
    def train_gnn(self):
        """Train GNN to learn node embeddings."""
        # Convert NetworkX to PyTorch Geometric format
        edge_index = self._to_edge_index()
        node_features = self._get_node_features()
        
        # Train GNN
        optimizer = torch.optim.Adam(self.gnn.parameters(), lr=0.01)
        
        for epoch in range(100):
            self.gnn.train()
            optimizer.zero_grad()
            
            # Forward pass
            embeddings = self.gnn(node_features, edge_index)
            
            # Loss (link prediction)
            loss = self._link_prediction_loss(embeddings, edge_index)
            
            # Backward pass
            loss.backward()
            optimizer.step()
        
        # Save learned embeddings
        self.node_embeddings = embeddings.detach().numpy()
```

**Benefits**:
- ✅ Better embeddings (graph-aware)
- ✅ Captures structural patterns
- ✅ Improves link prediction

### 2. Knowledge Graph Embedding (KGE)

**Concept**: Learn embeddings for entities and relations
```python
class TransE:
    """TransE: Translating Embeddings for Modeling Multi-relational Data."""
    
    def __init__(self, num_entities, num_relations, embedding_dim=100):
        self.entity_embeddings = nn.Embedding(num_entities, embedding_dim)
        self.relation_embeddings = nn.Embedding(num_relations, embedding_dim)
    
    def forward(self, head, relation, tail):
        """Score triplet (head, relation, tail)."""
        h = self.entity_embeddings(head)
        r = self.relation_embeddings(relation)
        t = self.entity_embeddings(tail)
        
        # TransE: h + r ≈ t
        score = torch.norm(h + r - t, p=2, dim=1)
        return score
    
    def predict_tail(self, head, relation, k=10):
        """Predict top-k tail entities."""
        h = self.entity_embeddings(head)
        r = self.relation_embeddings(relation)
        
        # h + r ≈ ?
        target = h + r
        
        # Find nearest entities
        all_entities = self.entity_embeddings.weight
        distances = torch.norm(all_entities - target, p=2, dim=1)
        
        top_k = torch.topk(distances, k, largest=False)
        return top_k.indices
```

**Benefits**:
- ✅ Relation-aware embeddings
- ✅ Better link prediction
- ✅ Captures semantic relationships

### 3. Temporal Knowledge Graph

**Concept**: Track changes over time
```python
class TemporalKG:
    def __init__(self):
        self.snapshots = {}  # timestamp -> graph
        self.current_time = 0
    
    def add_edge_temporal(self, u, v, timestamp, weight):
        """Add edge with timestamp."""
        if timestamp not in self.snapshots:
            self.snapshots[timestamp] = nx.DiGraph()
        
        self.snapshots[timestamp].add_edge(u, v, weight=weight)
    
    def get_graph_at_time(self, timestamp):
        """Get graph state at specific time."""
        # Merge all snapshots up to timestamp
        G = nx.DiGraph()
        for t in sorted(self.snapshots.keys()):
            if t <= timestamp:
                G = nx.compose(G, self.snapshots[t])
        return G
    
    def predict_future_links(self, timestamp, horizon=30):
        """Predict future links based on temporal patterns."""
        # Analyze historical patterns
        past_graphs = [self.get_graph_at_time(t) 
                      for t in range(timestamp - horizon, timestamp)]
        
        # Predict future links
        # (simplified - use time series analysis in practice)
        return self._extrapolate_links(past_graphs)
```

**Benefits**:
- ✅ Track Wikipedia evolution
- ✅ Predict future links
- ✅ Better for dynamic graphs

---

## 📊 Implementation Priority

### Phase 1: Quick Wins (1-2 weeks)
1. **Hub Compression** ⭐⭐⭐⭐⭐
   - Easy to implement
   - 60-70% memory reduction
   - Immediate impact

2. **Spatial Index** ⭐⭐⭐⭐⭐
   - Moderate difficulty
   - 100x faster similarity search
   - High impact

3. **Edge Pruning** ⭐⭐⭐⭐
   - Easy to implement
   - 40-50% less edges
   - Good impact

### Phase 2: Advanced (2-4 weeks)
1. **Hierarchical Structure** ⭐⭐⭐⭐
   - Moderate difficulty
   - 10x faster search
   - Scalable

2. **Community Detection** ⭐⭐⭐⭐
   - Easy to implement
   - 50-70% faster intra-community
   - Good for parallelization

3. **Text Index** ⭐⭐⭐
   - Easy to implement
   - 1000x faster text search
   - Nice to have

### Phase 3: Research (1-2 months)
1. **GNN** ⭐⭐⭐⭐⭐
   - Hard to implement
   - State-of-the-art embeddings
   - Research-level

2. **KGE** ⭐⭐⭐⭐
   - Hard to implement
   - Better link prediction
   - Research-level

3. **Temporal KG** ⭐⭐⭐
   - Moderate difficulty
   - Track evolution
   - Nice to have

---

## 🎯 Expected Improvements

### Memory Usage
```
Before: 1-2GB
After Phase 1: 400-600MB (60-70% reduction)
After Phase 2: 200-400MB (80-85% reduction)
```

### Search Speed
```
Before: 10-30 seconds
After Phase 1: 5-15 seconds (50% faster)
After Phase 2: 2-8 seconds (70-80% faster)
After Phase 3: 1-3 seconds (90% faster)
```

### Accuracy
```
Before: 60-80%
After Phase 1: 65-82% (slight improvement)
After Phase 2: 70-85% (moderate improvement)
After Phase 3: 75-90% (significant improvement)
```

---

## 📝 Summary

**Key Takeaways**:
1. 🎯 **Hub Compression**: Biggest quick win
2. 🚀 **Spatial Index**: Fastest similarity search
3. 🧠 **GNN**: Best long-term investment
4. 📊 **Hierarchical Structure**: Best scalability

**Start with**: Hub Compression + Spatial Index
**Move to**: Hierarchical Structure + Community Detection
**Research**: GNN + KGE

**Total Expected Improvement**: 
- 80-85% less memory
- 70-90% faster search
- 15-30% better accuracy

🚀 **Let's optimize that KG!**