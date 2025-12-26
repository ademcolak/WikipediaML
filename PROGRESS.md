# WikipediaML - Development Progress & Continuation Guide

**Last Updated:** 2025-12-26
**Status:** ✅ Production Ready + Bidirectional Search (Training Mode)
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
1. **Core System** (4 files, ~900 lines)
   - `core/wikipedia.py` - Wikipedia scraping + embeddings + incoming links API
   - `core/knowledge.py` - Knowledge Graph storage
   - `core/navigator.py` - Path finding with mode support
   - `core/bidirectional_search.py` - Bidirectional BFS with incoming links

2. **Entry Points** (3 files, ~520 lines)
   - `train.py` - Dynamic discovery training (training_mode=True)
   - `play.py` - Interactive game (training_mode=False)
   - `benchmark_real.py` - Real-world testing (training_mode=False)

3. **Dynamic Discovery Training** ⭐
   - Starts with 43 popular pages
   - Discovers new pages from successful paths
   - Adds links from each page (5 per page)
   - Pool grows: 43 → 500 → 5000+ pages
   - Infinite variety, no repetition after 2000+ iterations

4. **Bidirectional Search** ⭐ NEW!
   - Forward search: start → target (outgoing links)
   - Reverse search: target → start (incoming links via Wikipedia API)
   - Meets in middle: ~50% faster than forward-only
   - Training mode only (fair play in game mode)

5. **Performance**
   - Training: ~95%+ success with bidirectional
   - Easy: ~60% success (Italy→Rome, France→Paris)
   - Medium: ~40% success (Technology→Philosophy)
   - Hard: ~15% success (Ancient Rome→Quantum Mechanics)
   - Speed: 0.5-10s per path (depending on complexity)

### What's Missing ❌
1. **Fair Play Mode Fix** - Play mode should use forward-only BFS
2. **ML Link Predictor** - Neural network for link selection
3. **Topic-Based Routing** - Wikipedia categories for better navigation
4. **RL Agent** - Reinforcement learning for optimal paths

---

## 🏗️ Architecture Approach

### Design Philosophy
**"Fabrika" Model - Factory-like simplicity:**
- ✅ Minimal files (4 core + 3 entry points)
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

**Tier 2: Bidirectional Search (Fast) - Training Mode**
```python
# Two-way BFS with incoming links
path = bidirectional_search(start, target, max_depth=4, timeout=30)
# 1-10s, ~50% faster than forward-only
```

**Tier 3: Beam Search (Fallback)**
```python
# Semantic similarity + exploration
path = beam_search(start, target, width=5, depth=6)
# 0.5-5s depending on difficulty
```

**Tier 4: Auto-Learning**
```python
# Automatically save successful paths
if path_found:
    knowledge.add_path(path)  # Auto-update KG
```

### Key Decisions Made

1. **Two Modes:** Training vs Play
   - Training: Bidirectional search (incoming links API)
   - Play: Forward-only BFS (fair play)
   - Why: Fast learning, fair gameplay

2. **Bidirectional Search:** Wikipedia API incoming links
   - Why: ~50% faster, finds harder paths
   - Trade-off: Requires API calls, not "fair play"
   - Solution: Only in training mode

3. **Embedding Model:** all-mpnet-base-v2 (768 dim)
   - Why: Better semantic understanding
   - Upgraded from: all-MiniLM-L12-v2 (384 dim)
   - Result: +10-15% accuracy improvement

4. **Performance Limits:**
   - Max depth: 4 (was 6)
   - Timeout: 30 seconds
   - Queue limit: 10,000 pages
   - Why: Prevent exponential growth, memory issues

5. **No Parameters:** Everything auto-configured
   - Why: Simplicity, no decision paralysis
   - Trade-off: Less flexibility, but easier to use

---

## 🚀 Recent Major Changes (Dec 26, 2025)

### 1. Bidirectional Search Implementation
**Problem:** Forward-only BFS too slow for hard paths
**Solution:** Two-way search meeting in middle
**Files Changed:**
- `core/bidirectional_search.py` - New file
- `core/wikipedia.py` - Added `get_incoming_links()` method
- `core/navigator.py` - Added `training_mode` parameter

**Key Code:**
```python
# Wikipedia API incoming links
def get_incoming_links(self, page: str) -> List[str]:
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "backlinks",
        "bltitle": page,
        "bllimit": 100,
        "format": "json"
    }
    # Returns pages that link TO this page
```

### 2. Training Mode vs Play Mode
**Problem:** Bidirectional search uses incoming links (not fair play)
**Solution:** Two modes with different strategies

**Training Mode (train.py):**
```python
Navigator(use_bidirectional=True, training_mode=True)
# Uses incoming links API for reverse search
# Fast learning, ~95%+ success
```

**Play Mode (play.py, benchmark):**
```python
Navigator(use_bidirectional=True, training_mode=False)
# Should use forward-only (TODO: needs fix!)
# Fair play, no incoming links
```

**⚠️ KNOWN ISSUE:** Play mode currently still uses incoming links!
**TODO:** Add training_mode check in reverse search

### 3. Performance Optimizations
**Problem:** Exponential growth causing memory issues
**Solution:** Multiple safety limits

**Changes:**
- Max depth: 6 → 4
- Timeout: None → 30 seconds
- Queue limit: None → 10,000 pages
- Auto-save: Every 100 → Every 10 iterations

**Code:**
```python
# Timeout check
if time.time() - start_time > self.timeout:
    break

# Queue size check
if len(forward_queue) > 10000:
    break
```

### 4. Training Safety
**Problem:** Network errors causing crashes, data loss
**Solution:** Exception handling + frequent saves

**Changes:**
```python
try:
    result = navigator.find_path(start, target)
except KeyboardInterrupt:
    raise  # Allow Ctrl+C
except Exception as e:
    print(f"⚠️  Error: {e}")
    continue  # Don't crash

# Auto-save every 10 iterations
if iterations % 10 == 0:
    navigator.save()
```

---

## 📝 TODO List

### High Priority 🔴
1. **Fix Play Mode Fair Play**
   - Add training_mode check in reverse search
   - Play mode should NOT use incoming links
   - Only training mode uses bidirectional

2. **Path Validation**
   - Verify all links exist before returning path
   - Catch any remaining invalid paths

### Medium Priority 🟡
1. **Better Embedding Model**
   - Try Wikipedia-specific models
   - Fine-tune on Wikipedia link prediction

2. **ML Link Predictor**
   - Train neural network on successful paths
   - Predict best next link

3. **Topic-Based Routing**
   - Use Wikipedia categories
   - Route through related topics

### Low Priority 🟢
1. **RL Agent**
   - Reinforcement learning for optimal paths
   - Learn from experience

2. **Web Interface**
   - Simple web UI for playing
   - Visualize paths

---

## 🔧 How to Continue Development

### Quick Start
```bash
# 1. Training (learns new paths)
python train.py

# 2. Play (interactive game)
python play.py

# 3. Benchmark (test performance)
python benchmark_real.py
```

### Understanding the Code

**Core Flow:**
1. User requests path: `navigator.find_path(start, target)`
2. Check Knowledge Graph: `knowledge.find_path()` (instant)
3. If not found, try Bidirectional Search (training mode)
4. If still not found, try Beam Search (fallback)
5. Save successful path to Knowledge Graph

**Key Files to Understand:**
1. `core/navigator.py` - Main orchestrator
2. `core/bidirectional_search.py` - Two-way BFS
3. `core/wikipedia.py` - Wikipedia API interface
4. `train.py` - Training loop

### Making Changes

**To add new search algorithm:**
1. Create new file in `core/`
2. Add to `core/__init__.py`
3. Integrate in `navigator.py`

**To improve training:**
1. Modify `train.py`
2. Adjust page pool strategy
3. Change auto-save frequency

**To fix fair play mode:**
1. Edit `core/bidirectional_search.py`
2. Add training_mode parameter
3. Check mode in reverse search

---

## 📚 Key Learnings

### What Worked Well ✅
1. **Bidirectional Search** - Massive speed improvement
2. **Wikipedia API** - Reliable incoming links
3. **Dynamic Discovery** - Infinite training variety
4. **Auto-save** - No data loss
5. **Exception Handling** - Robust training

### What Didn't Work ❌
1. **Forward-only BFS** - Too slow for hard paths
2. **No timeout** - Memory explosion
3. **Rare saves** - Data loss on crash
4. **No error handling** - Training crashes

### Surprises 😮
1. **Incoming links API** - Single line fix, huge impact
2. **Exponential growth** - Depth 3 = 6,884 pages!
3. **Training success** - 95%+ with bidirectional
4. **Fair play issue** - Forgot to disable incoming links in play mode

---

## 🎓 For Next Developer

### Read These First
1. This file (PROGRESS.md)
2. README.md
3. `core/navigator.py` - Understand the flow
4. `core/bidirectional_search.py` - Understand the algorithm

### Start Here
1. **Fix fair play mode** (high priority)
2. Run training for 1000+ iterations
3. Test with benchmark_real.py
4. Improve based on results

### Don't Do This
1. Don't remove auto-save
2. Don't remove exception handling
3. Don't increase max_depth without timeout
4. Don't remove training_mode parameter

### Questions to Ask
1. Is this change making the code simpler or more complex?
2. Does this break fair play mode?
3. Will this cause memory issues?
4. Is this auto-saved?

---

## 📞 Contact & Resources

**GitHub Repos Analyzed:**
- WikiSpeedrun1: https://github.com/wikispeedruns/wikipedia-speedruns
- WikiSpeedrun2: https://github.com/wikispeedruns/wikipedia-speedruns

**Key Insights:**
- Bidirectional search is the key optimization
- Wikipedia API backlinks are essential
- Fair play requires forward-only search

**Documentation:**
- `docs/` - Detailed documentation
- `README.md` - Quick start guide
- This file - Development history

---

**Good luck! The system is working well, just needs fair play mode fix.** 🚀