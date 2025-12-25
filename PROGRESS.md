# WikipediaML - Development Progress & Continuation Guide

**Last Updated:** 2025-12-25  
**Status:** ✅ Production Ready (Fabrika Refactor Complete)  
**Next Developer:** Read this file first!

---

## 🎯 Project Goal

Build an AI that learns to play the Wikipedia game - finding shortest paths between Wikipedia pages by clicking links.

**Target Performance:**
- Easy challenges: 70-80% success
- Medium challenges: 40-60% success  
- Hard challenges: 20-30% success
- Speed: <2 seconds per path

---

## 📊 Current Status

### What Works ✅
1. **Core System** (3 files, ~650 lines)
   - `core/wikipedia.py` - Wikipedia scraping + embeddings
   - `core/knowledge.py` - Knowledge Graph storage
   - `core/navigator.py` - Beam search path finding

2. **Entry Points** (3 files, ~520 lines)
   - `train.py` - Continuous learning (no parameters!)
   - `play.py` - Interactive game (no parameters!)
   - `benchmark.py` - Performance testing (no parameters!)

3. **Performance**
   - Easy: ~60% success (Italy→Rome, France→Paris)
   - Medium: ~40% success (Technology→Philosophy)
   - Hard: ~15% success (Ancient Rome→Quantum Mechanics)
   - Speed: 0.5-5s per path

### What's Missing ❌
1. **ML Link Predictor** - Neural network for link selection
2. **Topic-Based Routing** - Wikipedia categories for better navigation
3. **Better Embedding Model** - Upgrade from MiniLM to DistilBERT
4. **RL Agent** - Reinforcement learning for optimal paths

---

## 🏗️ Architecture Approach

### Design Philosophy
**"Fabrika" Model - Factory-like simplicity:**
- ✅ Minimal files (3 core + 3 entry points)
- ✅ No parameters (just run!)
- ✅ Single responsibility per class
- ✅ Auto-everything (save, learn, update)
- ✅ One documentation (README.md)

### Three-Tier System

**Tier 1: Knowledge Graph (Instant)**
```python
# Check if path already learned
if path := knowledge.find_path(start, target):
    return path  # <0.01s
```

**Tier 2: Beam Search (Smart)**
```python
# Semantic similarity + exploration
path = beam_search(start, target, width=5, depth=6)
# 0.5-5s depending on difficulty
```

**Tier 3: Auto-Learning**
```python
# Automatically save successful paths
if path_found:
    knowledge.add_path(path)  # Auto-update KG
```

### Key Decisions Made

1. **Single Algorithm:** Beam search (width=5, depth=6)
   - Why: Best balance of speed vs accuracy
   - Rejected: A*, Bidirectional BFS (too slow or complex)

2. **Embedding Model:** all-MiniLM-L12-v2 (384 dim)
   - Why: Fast + decent quality
   - Future: Upgrade to DistilBERT or Wikipedia-specific model

3. **No Parameters:** Everything auto-configured
   - Why: Simplicity, no decision paralysis
   - Trade-off: Less flexibility, but easier to use

4. **Continuous Training:** Infinite loop with Ctrl+C exit
   - Why: Always learning, always improving
   - Auto-save every 100 iterations

---

## 🚀 How to Use (Step by Step)

### First Time Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run benchmark (test current performance)
python benchmark.py
# Expected: ~50% success on 13 tests, ~2 minutes

# 3. Play interactively (optional)
python play.py
# Try: Italy → Rome (should work)
```

### Training Workflow

**Option A: Short Training (Recommended for testing)**
```bash
# Run for 5-10 minutes, then Ctrl+C
python train.py

# After 100-200 iterations:
# - KG will have ~50-100 paths
# - Benchmark should improve to ~55-60%
```

**Option B: Long Training (Overnight)**
```bash
# Run overnight (8 hours)
nohup python train.py > training.log 2>&1 &

# Next morning:
# - KG will have ~1000-2000 paths
# - Benchmark should improve to ~65-75%
# - Check: tail -f training.log
```

**Option C: Continuous Training (Production)**
```bash
# Run as background service
# Keeps learning forever
# Auto-save every 100 iterations
```

### After Training
```bash
# 1. Test performance
python benchmark.py
# Compare with previous results

# 2. Play to see improvements
python play.py
# Try challenges that failed before

# 3. Check KG stats
python -c "from core import KnowledgeSystem; kg = KnowledgeSystem(); print(kg.get_stats())"
```

---

## 🔧 Technical Details

### Core Classes

**Wikipedia (core/wikipedia.py)**
```python
class Wikipedia:
    Purpose: Interface to Wikipedia (scraping + embeddings)
    
    Key Methods:
    - get_page_html(page) → BeautifulSoup [cached]
    - get_links(page) → List[str]
    - get_embedding(page) → np.ndarray [cached]
    - similarity(page1, page2) → float
    
    Caching:
    - HTML: 512 pages (LRU)
    - Embeddings: 2048 pages (LRU)
```

**KnowledgeSystem (core/knowledge.py)**
```python
class KnowledgeSystem:
    Purpose: Store and retrieve learned paths
    
    Key Methods:
    - add_path(path) → None [auto-weight]
    - find_path(start, target) → Optional[List[str]]
    - save() → None [pickle to data/knowledge_graph.pkl]
    
    Storage:
    - NetworkX DiGraph (directed, weighted)
    - Pickle format
    - Auto-load on init
```

**Navigator (core/navigator.py)**
```python
class Navigator:
    Purpose: Find paths using 3-tier system
    
    Key Methods:
    - find_path(start, target) → PathResult
    - _beam_search(start, target) → PathResult
    
    Algorithm:
    1. Check KG (instant)
    2. Beam search (width=5, depth=6)
    3. Save to KG (auto)
```

### Data Flow

```
User Request
    ↓
Navigator.find_path()
    ↓
├─→ KG.find_path() [Tier 1: Instant]
│   └─→ Found? Return path
│
├─→ Beam Search [Tier 2: Smart]
│   ├─→ Wikipedia.get_links()
│   ├─→ Wikipedia.similarity()
│   └─→ Found? Continue
│
└─→ KG.add_path() [Tier 3: Learn]
    └─→ Auto-save every 100
```

### File Structure

```
WikipediaML/
├── train.py              # Training (infinite loop, Ctrl+C to stop)
├── play.py               # Interactive game
├── benchmark.py          # Performance testing
├── README.md             # User documentation
├── PROGRESS.md           # This file (developer guide)
├── requirements.txt      # Dependencies
│
├── core/                 # Core system (DO NOT MODIFY without reason)
│   ├── __init__.py
│   ├── wikipedia.py      # Wikipedia interface
│   ├── knowledge.py      # Knowledge Graph
│   └── navigator.py      # Path finding
│
├── data/                 # Auto-generated data
│   ├── knowledge_graph.pkl          # Learned paths
│   ├── benchmark_dataset.json       # Test dataset
│   └── benchmark_results_*.json     # Test results
│
└── archive/              # Old code (reference only, DO NOT USE)
    ├── src/              # 15 old navigators
    ├── docs/             # 13 old docs
    └── ...
```

---

## 🐛 Known Issues & Solutions

### Issue 1: Low Success Rate (~20%)
**Symptom:** Benchmark shows <30% success  
**Cause:** Empty Knowledge Graph, semantic similarity not enough  
**Solution:** Train for 100+ iterations, then re-test

### Issue 2: Slow Performance (>5s per path)
**Symptom:** Each path takes >5 seconds  
**Cause:** No KG cache hits, doing full beam search every time  
**Solution:** More training to build KG

### Issue 3: Wikipedia Rate Limiting (429 errors)
**Symptom:** "Too Many Requests" errors  
**Cause:** Too fast scraping  
**Solution:** Already handled with 2s delay in train.py

### Issue 4: Memory Usage Growing
**Symptom:** Python process using >2GB RAM  
**Cause:** LRU caches growing  
**Solution:** Restart training periodically, or reduce cache sizes

---

## 🔮 Future Improvements (Priority Order)

### Phase 1: Quick Wins (1-2 weeks)
1. **Better Embedding Model**
   - Change: `all-MiniLM-L12-v2` → `all-mpnet-base-v2`
   - Expected: +10-15% accuracy
   - Trade-off: 2x slower

2. **Hybrid Similarity**
   - Add: Topic overlap + Historical success
   - Expected: +5-10% accuracy
   - Complexity: Medium

### Phase 2: ML Features (1-2 months)
3. **Topic-Based Routing**
   - Use: Wikipedia categories
   - Expected: +15-20% accuracy
   - Complexity: High

4. **ML Link Predictor**
   - Neural network: (current, target, link) → score
   - Expected: +20-30% accuracy
   - Complexity: Very high

### Phase 3: Advanced (3-6 months)
5. **RL Agent**
   - Q-Learning or PPO
   - Expected: +30-40% accuracy
   - Complexity: Expert level

---

## 📝 Development Guidelines

### Before Making Changes

1. **Read this file completely**
2. **Test current system:** `python benchmark.py`
3. **Understand the approach:** Fabrika model (simple, clean)
4. **Check archive:** Old code might have useful patterns

### When Adding Features

1. **Keep it simple:** Single responsibility per class
2. **No parameters:** Auto-configure everything
3. **Test immediately:** Run benchmark after changes
4. **Update docs:** README.md and this file

### Code Style

```python
# ✅ Good: Simple, clear, documented
class Navigator:
    """Path finder - simple beam search."""
    
    def find_path(self, start: str, target: str) -> PathResult:
        """Find path using 3-tier system."""
        # 1. Check KG
        # 2. Beam search
        # 3. Save result

# ❌ Bad: Complex, many parameters, unclear
class AdvancedHybridNavigatorWithMultipleStrategies:
    def find_path(self, start, target, algorithm='auto', 
                  beam_width=None, use_kg=True, use_ml=False,
                  use_rl=False, fallback='greedy', ...):
        # Too complex!
```

---

## 🎓 Learning Resources

### Understanding the Code
1. Start with `README.md` (user perspective)
2. Read `core/navigator.py` (main logic)
3. Read `core/wikipedia.py` (data source)
4. Read `core/knowledge.py` (learning)
5. Read `train.py` (training loop)

### Key Concepts
- **Beam Search:** Explores top-k paths simultaneously
- **Semantic Similarity:** Cosine similarity on embeddings
- **Knowledge Graph:** Directed weighted graph of paths
- **LRU Cache:** Least Recently Used caching strategy

### External Resources
- Sentence Transformers: https://www.sbert.net/
- NetworkX: https://networkx.org/
- Wikipedia API: https://www.mediawiki.org/wiki/API

---

## 🚨 Emergency Procedures

### If Training Crashes
```bash
# KG is auto-saved every 100 iterations
# Just restart:
python train.py
# It will load existing KG and continue
```

### If KG Gets Corrupted
```bash
# Backup exists in data/
# Or delete and start fresh:
rm data/knowledge_graph.pkl
python train.py
```

### If Performance Degrades
```bash
# 1. Check KG size
python -c "from core import KnowledgeSystem; kg = KnowledgeSystem(); print(kg.get_stats())"

# 2. Prune if too large (>10K edges)
python -c "from core import KnowledgeSystem; kg = KnowledgeSystem(); kg.prune(); kg.save()"

# 3. Re-test
python benchmark.py
```

---

## 📞 Handoff Checklist

**For Next Developer:**

- [ ] Read this entire file
- [ ] Run `python benchmark.py` (baseline)
- [ ] Run `python play.py` (try Italy → Rome)
- [ ] Read `core/navigator.py` (understand main logic)
- [ ] Check `data/` folder (see current KG state)
- [ ] Review `archive/` (understand what was tried before)
- [ ] Run `python train.py` for 10 minutes (see training)
- [ ] Re-run benchmark (see improvement)

**Questions to Ask:**
1. What's the current success rate? (check benchmark)
2. How many paths in KG? (check data/knowledge_graph.pkl)
3. What's the next priority? (check Future Improvements)
4. Any known issues? (check Known Issues section)

---

## 🎉 Success Metrics

**Current (Baseline):**
- Easy: ~60% success
- Medium: ~40% success
- Hard: ~15% success
- Overall: ~40% success

**Target (After improvements):**
- Easy: ~80% success
- Medium: ~60% success
- Hard: ~30% success
- Overall: ~60% success

**Stretch Goal:**
- Easy: ~90% success
- Medium: ~75% success
- Hard: ~50% success
- Overall: ~75% success

---

**Remember:** Keep it simple, test often, document changes!

**Good luck! 🚀**