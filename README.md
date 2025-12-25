# WikipediaML - Wikipedia Path Finder 🎮

AI that learns to play the Wikipedia game using semantic search and knowledge graphs.

## 🎯 What It Does

Finds the shortest path between two Wikipedia pages by clicking links, just like the Wikipedia game!

**Example:**
```
Italy → Rome (2 steps)
Italy → Europe → Rome

Physics → Albert Einstein (2 steps)  
Physics → Scientist → Albert Einstein
```

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/WikipediaML.git
cd WikipediaML

# Install dependencies
pip install -r requirements.txt
```

### Usage

**1. Play the Game (Interactive)**
```bash
python play.py
```
Interactive mode - enter start and target pages, get instant results!

**2. Train the System (Background)**
```bash
python train.py
```
Runs continuously, learns from random challenges, builds knowledge graph.
Press Ctrl+C to stop and save.

**3. Run Benchmark (Test Performance)**
```bash
python benchmark.py
```
Tests performance on standard dataset, shows detailed metrics.

## 📊 How It Works

### Three-Tier System

**Tier 1: Knowledge Graph (Instant)**
- Stores successful paths
- Instant lookup if path exists
- Grows with training

**Tier 2: Beam Search (Smart)**
- Semantic similarity (sentence transformers)
- Explores top 5 paths simultaneously
- Max depth: 6 steps

**Tier 3: Auto-Learning**
- Saves successful paths automatically
- Improves over time
- No manual intervention needed

### Architecture

```
WikipediaML/
├── train.py          # Training script (continuous learning)
├── play.py           # Interactive game
├── benchmark.py      # Performance testing
│
├── core/            # Core system (3 files)
│   ├── wikipedia.py    # Wikipedia interface (scraping + embeddings)
│   ├── knowledge.py    # Knowledge graph + ML
│   └── navigator.py    # Path finding (beam search)
│
├── data/            # Data storage
│   ├── knowledge_graph.pkl      # Learned paths
│   ├── benchmark_dataset.json   # Test dataset
│   └── benchmark_results_*.json # Test results
│
└── archive/         # Old code (reference only)
```

## 📈 Performance

### Current Results
- **Easy challenges:** ~70% success (e.g., Italy → Rome)
- **Medium challenges:** ~40% success (e.g., Technology → Philosophy)
- **Hard challenges:** ~20% success (e.g., Ancient Rome → Quantum Mechanics)
- **Average time:** <2 seconds per path

### Knowledge Graph Stats
- **Nodes:** Grows with training
- **Edges:** Weighted by usage
- **Cache hit rate:** Improves over time

## 🛠️ Technical Details

### Core Technologies
- **Sentence Transformers:** `all-MiniLM-L12-v2` (384 dim)
- **Graph Library:** NetworkX (directed, weighted)
- **Web Scraping:** BeautifulSoup + Requests
- **Search Algorithm:** Beam search (width=5, depth=6)

### Key Features
- **LRU Caching:** Fast repeated lookups
- **Semantic Similarity:** Cosine similarity on embeddings
- **Weighted Edges:** Usage-based path quality
- **Auto-Save:** Every 100 iterations
- **Graceful Shutdown:** Ctrl+C saves state

## 📝 Examples

### Training
```bash
$ python train.py

🏭 WIKIPEDIAML TRAINING
======================================
Training will run continuously.
Press Ctrl+C to stop and save.
======================================

Iteration 1
Challenge: United_States → New_York_City
✅ Path found! 2 steps, 1.23s

Iteration 2
Challenge: Physics → Albert_Einstein
✅ Path found! 2 steps, 0.87s

...
```

### Playing
```bash
$ python play.py

🎮 WIKIPEDIAML - WIKIPEDIA GAME
======================================

Start page: Italy
Target page: Rome

✅ PATH FOUND!
======================================

🛤️  Path (1 steps):
  🏁 Italy
  🎯 Rome

📊 Stats:
  Steps: 1
  Time: 0.45s
  Source: knowledge_graph
  ⚡ Instant (from Knowledge Graph!)
```

### Benchmark
```bash
$ python benchmark.py

🎯 WIKIPEDIAML BENCHMARK
======================================

Test #1: Italy → Rome (easy)
✅ Success! 1 steps, 0.45s

Test #2: Technology → Philosophy (medium)
✅ Success! 3 steps, 2.13s

...

📊 BENCHMARK RESULTS
======================================
✅ Successful: 8/13 (61.5%)
❌ Failed: 5/13
⏱️  Total Time: 24.56s

📈 Performance Metrics:
   Avg Time: 1.87s (±0.92s)
   Avg Steps: 2.3
```

## 🔮 Future Plans

### Short Term
- Topic-based routing (Wikipedia categories)
- Better embedding model (DistilBERT)
- Hybrid similarity (semantic + structural)

### Medium Term
- ML link predictor (neural network)
- Pattern recognition
- Hub detection

### Long Term
- Reinforcement learning agent
- Multi-modal embeddings
- Distributed training

## 🤝 Contributing

This is an educational project. Feel free to:
- Report issues
- Suggest improvements
- Fork and experiment

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Wikipedia for the amazing knowledge base
- Sentence Transformers for semantic embeddings
- NetworkX for graph algorithms

## 📧 Contact

Questions? Open an issue or reach out!

---

**Made with ❤️ for learning and fun!**
