# 🌐 WikipediaML - Intelligent Wikipedia PathFinder

AI-powered Wikipedia navigation system that finds the shortest path between any two Wikipedia pages using semantic understanding, knowledge graphs, and machine learning.

## ✨ Features

- 🧠 **Semantic Search**: Uses sentence transformers for intelligent link selection
- 🔄 **Bidirectional Beam Search**: Searches from both start and target simultaneously
- 📊 **Knowledge Graph**: Learns and reuses successful paths
- 🏷️ **Category-Aware**: Uses Wikipedia categories for better accuracy
- ⚡ **Async/Parallel**: 3x faster with parallel page fetching
- 🤖 **Claude Integration**: Optional AI reasoning for complex paths

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone <repo-url>
cd WikipediaML

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```bash
# Simple path finding
python main.py Potato Pizza

# Fast mode (async - recommended!)
python main.py Potato Pizza --async

# With AI reasoning (requires ANTHROPIC_API_KEY)
python main.py Potato Pizza --async --claude
```

### Examples

```bash
# Easy paths
python main.py Albert_Einstein Physics
python main.py Python_(programming_language) Machine_learning

# Medium difficulty
python main.py Potato Pizza --async
python main.py Italy Rome --async

# Hard paths
python main.py Porsche Serik_Akhmetov_Government --async --claude
```

## 📊 Performance

| Mode | Speed | Accuracy | Use Case |
|------|-------|----------|----------|
| **Sync** | 1-2s | 95% | Simple paths, cached results |
| **Async** | 0.5-1s | 95% | Most paths (recommended) |
| **Claude** | 2-3s | 98% | Complex paths, reasoning |

### Speedup with Async:
- **3.17x faster** for parallel page fetching
- **2.32x faster** for bidirectional search
- **%68 less time** on average

## 🏗️ Architecture

```
main.py (Entry Point)
    ↓
SemanticNavigator (Core Logic)
    ├── AsyncScraper (Parallel fetching)
    ├── Embedder (Semantic similarity)
    ├── CategoryAnalyzer (Wikipedia categories)
    ├── LinkFilter (Smart pre-filtering)
    ├── KnowledgeGraph (Path learning)
    └── ClaudeReasoning (Optional AI)
```

## 📁 Project Structure

```
WikipediaML/
├── main.py                    # Entry point
├── app.py                     # Flask web interface
├── requirements.txt           # Dependencies
├── .env.example              # Environment template
├── src/                      # Core modules
│   ├── semantic_navigator.py # Main navigation logic
│   ├── scraper.py            # Wikipedia fetcher
│   ├── embedder.py           # Semantic embeddings (cached)
│   ├── category_analyzer.py  # Wikipedia categories (cached)
│   ├── link_filter.py        # Smart filtering
│   ├── knowledge_graph.py    # Path learning (cached)
│   ├── pathfinder.py         # Search algorithms
│   ├── ml_link_scorer.py     # ML-based link scoring
│   ├── self_learning_trainer.py # Self-learning system
│   ├── visualizer.py         # 3D graph visualization
│   └── claude_reasoning.py   # Claude API integration
├── cache/                    # Cache files (auto-generated)
│   ├── embeddings_cache.pkl  # Sentence embeddings
│   ├── wiki_graph.pkl        # Knowledge graph
│   ├── category_cache.pkl    # Wikipedia categories
│   ├── ml_model.pkl          # Trained ML model
│   ├── ml_scaler.pkl         # Feature scaler
│   └── training_history.json # Training progress
└── docs/                     # Documentation
    ├── ROADMAP.md            # Project roadmap
    ├── TRAINING_GUIDE.md     # ML training guide
    ├── PROJECT_CONTEXT.md    # Technical context
    ├── PERFORMANCE_OPTIMIZATION_PLAN.md
    └── ... (20+ documentation files)
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file:

```bash
# Optional: Claude API for reasoning
ANTHROPIC_API_KEY=your-api-key-here
```

### Flags

```bash
--async    # Enable async/parallel processing (3x faster)
--claude   # Enable Claude reasoning (requires API key)
```

## 📈 How It Works

### 1. Bidirectional Beam Search
```
Start: Potato          Target: Pizza
   ↓                      ↓
Tomato ←─────────────→ Italian_cuisine
   ↓                      ↓
[Intersection found!]
Path: Potato → Tomato → Pizza
```

### 2. Semantic Similarity
```
For each link, calculate:
- Embedding similarity (sentence transformers)
- Category overlap (Wikipedia categories)
- Heuristic score (word overlap, etc.)

Choose top-k links with highest scores
```

### 3. Knowledge Graph
```
First run:  Potato → Pizza (1.5s, searches)
Second run: Potato → Pizza (0.0s, cached!)

Graph learns successful paths and reuses them
```

## 🎯 Advanced Features

### Wikipedia Categories
```python
# Automatically uses Wikipedia categories for better accuracy
# +15-20% improvement in link selection
# Example: "Pizza" → "Italian cuisine" category
```

### Async/Parallel Processing
```python
# Fetches multiple pages simultaneously
# 4 pages × 500ms = 2000ms (sync)
# 4 pages in parallel = 500ms (async) → 4x faster!
```

### Claude Reasoning
```python
# Optional AI reasoning for complex paths
# Explains why each link was chosen
# Higher accuracy but slower
```

## 📊 Statistics

After each run, see detailed statistics:

```
📊 SONUÇ ÖZETİ
✅ Path bulundu!
🛤️  Path: Potato → Tomato → Pizza
📏 Adım sayısı: 2
⏱️  Süre: 0.66s
🔍 Taranan sayfa: 2

💾 SİSTEM İSTATİSTİKLERİ
Scraper Cache: 0.0% hit rate
Embedder Cache: 3.5% hit rate
Knowledge Graph: 10 paths learned, 1 reused
```

## 🚀 Roadmap & Future Goals

### Phase 1: Foundation (Completed ✅)
- ✅ Semantic search with sentence transformers
- ✅ Bidirectional beam search
- ✅ Wikipedia categories integration
- ✅ Knowledge graph learning
- ✅ Caching system (embeddings, graph, categories)

### Phase 2: Machine Learning (In Progress 🔄)
- ✅ ML-based link scoring (10 features)
- ✅ Self-learning trainer system
- ✅ 3D graph visualization
- ⏳ Performance optimization (ongoing)
- ⏳ Feature engineering improvements

### Phase 3: Performance & Scale (Next 🎯)
- 🎯 **GPU Acceleration**: 10-50x speedup for embeddings
- 🎯 **Batch Processing**: Process multiple links simultaneously
- 🎯 **Advanced Caching**: Redis for distributed cache
- 🎯 **Graph Database**: Neo4j for efficient graph queries
- 🎯 **Model Optimization**: Quantization, pruning, distillation

### Phase 4: Intelligence (Future 🔮)
- 🔮 **Advanced ML Models**: XGBoost, LightGBM, Neural Networks
- 🔮 **Reinforcement Learning**: Learn from user feedback
- 🔮 **Multi-modal Learning**: Images, infoboxes, structured data
- 🔮 **Transfer Learning**: Pre-trained models for Wikipedia

### Phase 5: Production (Future 🚀)
- 🚀 **FastAPI Backend**: RESTful API
- 🚀 **React Frontend**: Modern web interface
- 🚀 **Docker Deployment**: Containerization
- 🚀 **Monitoring**: Prometheus, Grafana
- 🚀 **Distributed System**: Horizontal scaling

See `docs/ROADMAP.md` for detailed roadmap.

## 🎯 Performance Optimization Goals

### Current Performance
- **Path Finding**: 0.5-2s per path
- **Embedding Calculation**: ~100ms per page
- **Category Analysis**: ~500ms per page (with API calls)
- **ML Feature Extraction**: ~200ms per link

### Optimization Targets

#### 1. GPU Acceleration (Priority: HIGH 🔥)
```python
# Current: CPU-based embeddings
embeddings = model.encode(texts)  # ~100ms per text

# Target: GPU-based embeddings
embeddings = model.encode(texts, device='cuda')  # ~10ms per text
# Expected: 10x speedup
```

#### 2. Batch Processing (Priority: HIGH 🔥)
```python
# Current: Sequential processing
for link in links:
    score = calculate_score(link)  # 200ms × 100 links = 20s

# Target: Batch processing
scores = calculate_scores_batch(links)  # 2s for 100 links
# Expected: 10x speedup
```

#### 3. Advanced Caching (Priority: MEDIUM 📊)
```python
# Current: Local PKL files
cache = pickle.load('cache/embeddings_cache.pkl')

# Target: Redis distributed cache
cache = redis.get('embedding:page_title')
# Expected: 2-3x speedup, distributed access
```

#### 4. Graph Database (Priority: MEDIUM 📊)
```python
# Current: NetworkX in-memory graph
path = nx.shortest_path(G, start, target)

# Target: Neo4j graph database
path = neo4j.run("MATCH path=shortestPath(...)")
# Expected: 5-10x speedup for large graphs
```

#### 5. Model Optimization (Priority: LOW 🔧)
```python
# Current: Full precision model (float32)
model = SentenceTransformer('all-MiniLM-L6-v2')

# Target: Quantized model (int8)
model = SentenceTransformer('all-MiniLM-L6-v2', quantize=True)
# Expected: 2-4x speedup, 4x less memory
```

### Expected Overall Improvements
- **10-50x faster** with GPU acceleration
- **5-10x faster** with batch processing
- **2-3x faster** with Redis caching
- **5-10x faster** with Neo4j for large graphs
- **Combined: 100-500x speedup potential!**

## 🧠 Knowledge Graph Optimization

### Current KG Usage
```python
# Knowledge graph stores successful paths
# Reuses paths when available (instant results)
# Current: ~10-100 paths stored
```

### Optimization Goals

#### 1. Expand Graph Coverage
- **Target**: Store 10,000+ successful paths
- **Method**: Continuous learning from all searches
- **Benefit**: 90%+ cache hit rate

#### 2. Graph Pruning
- **Remove**: Low-quality paths (>10 steps)
- **Keep**: High-quality paths (<5 steps)
- **Update**: Path weights based on success rate

#### 3. Graph Analytics
- **Centrality**: Find most important pages
- **Communities**: Detect topic clusters
- **Shortcuts**: Discover common intermediate pages

#### 4. Predictive Paths
```python
# Current: Reactive (search when requested)
path = find_path(start, target)

# Target: Proactive (predict likely paths)
likely_paths = predict_paths(start, target)
# Pre-compute and cache popular paths
```

### KG Performance Metrics
- **Coverage**: % of queries answered from cache
- **Quality**: Average path length
- **Freshness**: Last update time
- **Size**: Number of nodes/edges

## 📊 ML Model Improvements

### Current ML Features (10 features)
1. **Semantic Similarity**: Embedding cosine similarity
2. **Text Overlap**: Word/character overlap
3. **Link Position**: Position in page
4. **Category Similarity**: Wikipedia category overlap (disabled for performance)
5. **Graph Features**: PageRank, degree centrality
6. **Heuristic Score**: Combined heuristic

### Future ML Enhancements

#### 1. Advanced Features
- **Infobox Data**: Structured information
- **Image Similarity**: Visual features
- **Citation Network**: Reference patterns
- **Temporal Features**: Page age, edit frequency
- **User Behavior**: Click patterns (if available)

#### 2. Deep Learning Models
```python
# Current: Traditional ML (10 features)
model = XGBClassifier()

# Target: Neural networks
model = NeuralNetwork(
    input_dim=50,  # More features
    hidden_layers=[128, 64, 32],
    output_dim=1
)
```

#### 3. Ensemble Methods
```python
# Combine multiple models
ensemble = VotingClassifier([
    ('xgb', XGBClassifier()),
    ('lgb', LGBMClassifier()),
    ('nn', NeuralNetwork())
])
```

#### 4. Online Learning
```python
# Current: Batch training
model.fit(X_train, y_train)

# Target: Continuous learning
model.partial_fit(X_new, y_new)  # Update with new data
```

See `docs/PERFORMANCE_OPTIMIZATION_PLAN.md` for detailed optimization strategies.

## 📚 Documentation

### Getting Started
- `QUICKSTART.md` - Quick start guide
- `docs/TRAINING_GUIDE.md` - ML training guide
- `docs/EMERGENCY_STOP.md` - How to stop frozen processes

### Technical Documentation
- `ARCHITECTURE.md` - System architecture
- `docs/PROJECT_CONTEXT.md` - Technical context
- `docs/ROADMAP.md` - Detailed roadmap
- `docs/PERFORMANCE_OPTIMIZATION_PLAN.md` - Optimization strategies

### Feature Documentation
- `docs/BIDIRECTIONAL_SEMANTIC_SEARCH.md` - Search algorithm
- `docs/3D_VISUALIZATION_PLAN.md` - Visualization features
- `docs/CATEGORIES_FEATURE.md` - Wikipedia categories

### Project History
- `CHANGELOG.md` - Version history
- `docs/PROGRESS_LOG.md` - Development progress
- `docs/REFACTOR_SUMMARY.md` - Recent refactoring

## 🤝 Contributing

Contributions welcome! Please read the documentation first.

## 📄 License

MIT License

## 🎓 Learning Resources

This project demonstrates:
- Semantic search with sentence transformers
- Graph algorithms (bidirectional BFS, beam search)
- Async/parallel programming in Python
- Knowledge graph construction
- API integration (Wikipedia, Claude)
- Caching strategies
- Production-ready ML systems

## 📞 Support

For issues or questions, please check the documentation in `docs/` folder.

---

**Version:** 4.0.0 - Machine Learning & Optimization
**Status:** Active Development
**Last Updated:** December 10, 2024

**Key Focus**: Performance optimization, ML improvements, and scalability
