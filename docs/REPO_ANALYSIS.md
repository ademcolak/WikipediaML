# Wikipedia Speedrun Repos Analysis

## Analyzed Repositories

1. **WikiSpeedrun** (B0und/WikiSpeedrun)
   - Frontend-focused React application
   - Live at: wikispeedrun.org
   - Focus: User experience, timer accuracy, multi-language

2. **Wikipedia Speedruns** (wikispeedruns/wikipedia-speedruns)
   - Full-stack Flask + React application
   - Live at: wikispeedruns.com
   - Focus: Competitive speedrunning, leaderboards, path finding

## Key Findings

### 1. Bidirectional BFS (CRITICAL) ⭐⭐⭐

**What they do:**
```python
def bidirectionalSearcher(start: int, end:int) -> List[List[int]]:
    forwardVisited = {start : (None, 0)}
    reverseVisited = {end : (None, 0)}
    
    forwardQueue = [start]
    reverseQueue = [end]
    
    while True:
        # Forward search
        a = forwardBFS(start, end, forwardVisited, reverseVisited, forwardQueue)
        
        # Reverse search
        if a != end:
            b = reverseBFS(start, end, forwardVisited, reverseVisited, reverseQueue)
        
        # Check intersection
        if a or b:
            return traceBidirectionalPath(intersection, start, end, 
                                         forwardVisited, reverseVisited)
```

**Benefits:**
- Searches from both start and end simultaneously
- Meets in the middle → ~50% faster than single-direction
- Batch processing: 200 pages at once
- Early termination when paths intersect

**Our Implementation Priority:** HIGH
- Would solve our Ancient_Egypt → Cryptocurrency timeout
- Expected 2-3x speedup on hard tests
- Complements our existing beam search

### 2. Database-Backed Graph

**What they do:**
- MySQL database with full Wikipedia graph
- Tables: `articleid`, `edgeidarticleid`
- Batch SQL queries for link retrieval

```python
def getLinks(pages: List[int], forward: bool = True) -> Dict[int, List[int]]:
    tuple_template = ','.join(['%s'] * len(pages))
    
    if forward:
        query = f"SELECT src AS cur, dest AS next FROM {EDGE_TABLE} 
                 WHERE src IN ({tuple_template})"
    else:
        query = f"SELECT dest AS cur, src AS next FROM {EDGE_TABLE} 
                 WHERE dest IN ({tuple_template})"
```

**Our Status:**
- ✅ We have NetworkX graph (in-memory)
- ✅ We have pickle serialization
- ❌ No database backend (not needed for our scale)
- ✅ Our approach is simpler and sufficient

### 3. Smart Article Filtering

**What they do:**
```python
def checkEnd(end: int, thresholdEnd: int) -> bool:
    title = convertToArticleName(end)
    
    # Filter "List of" articles
    if title[0:7] == "List of":
        return False
    
    # Word count filtering (logarithmic polynomial)
    x = countWords(title)
    if randomFilter(True, 0.0047*x*x*x - 0.0777*x*x + 0.2244*x + 1.226):
        return False
    
    # Sports filtering (5% acceptance)
    if randomFilter(checkSports(title), 0.05):
        return False
    
    # Minimum link threshold
    if numLinksOnArticle(end) < thresholdEnd:
        return False
```

**Our Implementation Priority:** MEDIUM
- Could improve training quality
- Filter out low-quality pages
- Reduce noise in knowledge graph

### 4. Async Task Queue (Celery + Redis)

**What they do:**
```python
@celery.task(time_limit=SCRAPER_TIMEOUT)
def shortest_path(start: str, end: str):
    start_id = convertToID(start)
    end_id = convertToID(end)
    return findPaths(start_id, end_id)
```

**Our Status:**
- ❌ Not needed for our use case
- We're building an AI, not a web service
- Our parallel beam search handles concurrency

### 5. Batch Processing

**What they do:**
- Process 200 pages simultaneously
- Single SQL query for multiple pages
- Depth-based batching (same depth together)

**Our Implementation Priority:** HIGH
- We already started with ThreadPoolExecutor
- Can batch our Wikipedia API calls
- Reduce network overhead

## Recommendations for Our Project

### Immediate Actions (High Priority)

1. **Implement Bidirectional Search** ⭐⭐⭐
   - Expected 2-3x speedup
   - Solves timeout issues
   - Complements existing beam search
   
2. **Add Article Quality Filtering**
   - Filter "List of" pages
   - Minimum link threshold
   - Improve training data quality

3. **Optimize Batch Processing**
   - Batch Wikipedia API calls
   - Process multiple pages per request
   - Reduce network latency

### Medium Priority

4. **Smart Page Selection**
   - Word count filtering
   - Sports page filtering
   - Category-based filtering

5. **Progress Tracking**
   - Real-time progress indicator
   - Estimated time remaining
   - Current depth/breadth stats

### Low Priority (Nice to Have)

6. **Multi-language Support**
   - Currently English only
   - Could expand to other languages
   - Requires separate training

7. **Alternative Paths**
   - Find multiple shortest paths
   - Show different strategies
   - Educational value

## Performance Comparison

### Their Approach (wikispeedruns.com)
- Bidirectional BFS
- Database-backed (MySQL)
- Batch processing (200 pages)
- 20 second timeout
- Pre-computed graph

### Our Approach (WikipediaML)
- Beam search (width=5, depth=6)
- In-memory graph (NetworkX)
- Parallel processing (ThreadPoolExecutor)
- 30 second timeout
- Dynamic discovery training

### Hybrid Approach (Recommended)
- **Bidirectional Beam Search** (best of both)
- In-memory graph (sufficient for our scale)
- Batch API calls (reduce network overhead)
- Smart filtering (improve quality)
- Keep our ML-based semantic similarity

## Implementation Plan

### Phase 1: Bidirectional Search (Week 1)
- [ ] Implement forward BFS
- [ ] Implement reverse BFS
- [ ] Implement intersection detection
- [ ] Implement path tracing
- [ ] Test on benchmark dataset

### Phase 2: Quality Improvements (Week 2)
- [ ] Add article filtering
- [ ] Implement batch API calls
- [ ] Add progress indicator
- [ ] Optimize memory usage

### Phase 3: Advanced Features (Week 3)
- [ ] Alternative paths
- [ ] Topic-aware routing
- [ ] Adaptive depth
- [ ] Performance profiling

## Conclusion

The most valuable insight from these repos is **bidirectional search**. This is a proven technique that would significantly improve our performance on hard tests. Combined with our existing semantic similarity and knowledge graph, we could achieve:

- **Speed:** 2-3x faster (5-27s → 2-10s)
- **Accuracy:** 96.7% → 100% (solve Ancient_Egypt → Cryptocurrency)
- **Reliability:** No more timeouts
- **Scalability:** Handle harder challenges

Our current approach is solid, but adding bidirectional search would make it production-ready for competitive speedrunning.