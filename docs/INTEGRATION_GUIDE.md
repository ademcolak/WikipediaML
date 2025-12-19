# Integration Guide: External Wikipedia Speedrun Repositories

## Quick Start

### Step 1: Clone and Analyze
```bash
# Clone the repositories and generate analysis report
python analyze_external_repos.py --clone --output external_repos_report.txt

# Review the report
cat external_repos_report.txt
```

### Step 2: Explore Key Components
```bash
# Navigate to cloned repositories
cd external/WikiSpeedrun
ls -la

cd ../wikipedia-speedruns
ls -la
```

## Specific Integration Opportunities

### 1. Dataset Extraction for Benchmarking

**Goal**: Extract their challenge datasets to improve our benchmark

**Expected Files to Look For**:
- `challenges.json` or `puzzles.json`
- `leaderboard.json` or `games.json`
- Any CSV files with start/end article pairs
- Database dumps or seed data

**Integration Steps**:
```python
# Example: Convert their dataset to our format
import json

def convert_speedrun_dataset(external_file, output_file):
    """Convert external dataset to our benchmark format."""
    with open(external_file, 'r') as f:
        external_data = json.load(f)
    
    our_format = []
    for item in external_data:
        # Adapt based on their structure
        our_format.append({
            "start": item.get("start_article") or item.get("from"),
            "end": item.get("end_article") or item.get("to"),
            "difficulty": item.get("difficulty", "medium"),
            "optimal_path_length": item.get("best_path_length"),
            "source": "external_speedrun_repo"
        })
    
    with open(output_file, 'w') as f:
        json.dump(our_format, f, indent=2)

# Usage
convert_speedrun_dataset(
    'external/wikipedia-speedruns/data/challenges.json',
    'benchmark/speedrun_challenges.json'
)
```

### 2. Wikipedia API Optimization

**Goal**: Learn from their Wikipedia scraping patterns

**Files to Study**:
- Look for files with names like: `wikipedia.py`, `api.py`, `scraper.py`, `fetcher.py`
- Check their `package.json` or `requirements.txt` for Wikipedia libraries

**Key Patterns to Extract**:

```python
# Pattern 1: Efficient link extraction
def extract_article_links(html_content):
    """
    Extract only valid Wikipedia article links.
    Exclude: special pages, media, external links, etc.
    """
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all links in the main content area
    content = soup.find('div', {'id': 'mw-content-text'})
    if not content:
        return []
    
    links = []
    for link in content.find_all('a', href=True):
        href = link['href']
        
        # Filter valid article links
        if (href.startswith('/wiki/') and 
            ':' not in href and  # Exclude special pages
            '#' not in href and  # Exclude anchors
            not href.startswith('/wiki/File:') and
            not href.startswith('/wiki/Special:')):
            
            article = href.replace('/wiki/', '')
            links.append(article)
    
    return list(set(links))  # Remove duplicates

# Pattern 2: Caching strategy
import functools
from datetime import datetime, timedelta

def cache_with_expiry(expiry_hours=24):
    """Cache Wikipedia content with expiration."""
    cache = {}
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(article):
            now = datetime.now()
            
            if article in cache:
                content, timestamp = cache[article]
                if now - timestamp < timedelta(hours=expiry_hours):
                    return content
            
            content = func(article)
            cache[article] = (content, now)
            return content
        
        return wrapper
    return decorator

@cache_with_expiry(expiry_hours=24)
def fetch_wikipedia_article(article):
    """Fetch article with caching."""
    # Implementation here
    pass
```

### 3. Path Validation Logic

**Goal**: Ensure our navigators follow valid Wikipedia paths

**Integration**:

```python
# Add to src/knowledge_graph.py or create src/path_validator.py

class PathValidator:
    """Validate Wikipedia navigation paths."""
    
    def __init__(self, knowledge_graph):
        self.kg = knowledge_graph
    
    def is_valid_path(self, path: list) -> tuple[bool, str]:
        """
        Check if a path is valid.
        Returns: (is_valid, error_message)
        """
        if len(path) < 2:
            return False, "Path must have at least 2 articles"
        
        # Check each step
        for i in range(len(path) - 1):
            current = path[i]
            next_article = path[i + 1]
            
            # Verify link exists in knowledge graph
            if not self.kg.has_edge(current, next_article):
                return False, f"No link from '{current}' to '{next_article}'"
        
        return True, "Valid path"
    
    def validate_against_wikipedia(self, path: list) -> tuple[bool, str]:
        """
        Validate path by checking actual Wikipedia links.
        More thorough but slower than graph-based validation.
        """
        from src.scraper import WikipediaScraper
        
        scraper = WikipediaScraper()
        
        for i in range(len(path) - 1):
            current = path[i]
            next_article = path[i + 1]
            
            # Fetch actual links from Wikipedia
            links = scraper.get_links(current)
            
            if next_article not in links:
                return False, f"'{next_article}' not linked from '{current}' on Wikipedia"
        
        return True, "Path validated against Wikipedia"
```

### 4. Scoring and Metrics

**Goal**: Standardize how we measure navigator performance

**Integration**:

```python
# Add to benchmark/run_benchmark.py

class SpeedrunMetrics:
    """Calculate metrics compatible with speedrun standards."""
    
    @staticmethod
    def calculate_score(path_length: int, time_seconds: float, 
                       optimal_length: int = None) -> dict:
        """
        Calculate comprehensive score metrics.
        
        Returns:
            - path_length: Number of clicks
            - time: Time taken in seconds
            - efficiency: How close to optimal path
            - score: Combined metric
        """
        metrics = {
            "path_length": path_length,
            "time_seconds": round(time_seconds, 2),
            "clicks_per_second": round(path_length / time_seconds, 2) if time_seconds > 0 else 0
        }
        
        if optimal_length:
            metrics["efficiency"] = round(optimal_length / path_length, 2)
            metrics["extra_clicks"] = path_length - optimal_length
        
        # Combined score (lower is better)
        # Penalize both extra clicks and time
        metrics["score"] = path_length * 10 + time_seconds
        
        return metrics
    
    @staticmethod
    def rank_results(results: list) -> list:
        """Rank results by score."""
        return sorted(results, key=lambda x: x.get("score", float('inf')))
```

### 5. Difficulty Classification

**Goal**: Categorize challenges by difficulty

**Integration**:

```python
# Add to benchmark/create_dataset.py

class DifficultyClassifier:
    """Classify Wikipedia challenges by difficulty."""
    
    @staticmethod
    def classify_by_distance(start: str, end: str, kg) -> str:
        """Classify based on graph distance."""
        try:
            import networkx as nx
            path_length = nx.shortest_path_length(kg.graph, start, end)
            
            if path_length <= 2:
                return "easy"
            elif path_length <= 4:
                return "medium"
            elif path_length <= 6:
                return "hard"
            else:
                return "expert"
        except:
            return "unknown"
    
    @staticmethod
    def classify_by_topic_similarity(start: str, end: str, embedder) -> str:
        """Classify based on semantic similarity."""
        similarity = embedder.get_similarity(start, end)
        
        if similarity > 0.7:
            return "easy"
        elif similarity > 0.4:
            return "medium"
        elif similarity > 0.2:
            return "hard"
        else:
            return "expert"
    
    @staticmethod
    def classify_combined(start: str, end: str, kg, embedder) -> dict:
        """Combined difficulty assessment."""
        return {
            "distance_difficulty": DifficultyClassifier.classify_by_distance(start, end, kg),
            "semantic_difficulty": DifficultyClassifier.classify_by_topic_similarity(start, end, embedder),
            "start": start,
            "end": end
        }
```

## Practical Usage Examples

### Example 1: Import Speedrun Challenges

```bash
# After cloning repos, find their challenge files
find external/ -name "*challenge*" -o -name "*puzzle*" -o -name "*game*"

# Convert to our format
python -c "
from analyze_external_repos import RepoAnalyzer
analyzer = RepoAnalyzer()
datasets = analyzer.find_datasets('wikipedia-speedruns')
print('Found datasets:', datasets)
"
```

### Example 2: Compare Our AI vs Speedrun Records

```python
# Create comparison script
import json

def compare_with_speedruns(our_results, speedrun_data):
    """Compare our AI performance with human speedruns."""
    
    comparisons = []
    
    for challenge in speedrun_data:
        start = challenge['start']
        end = challenge['end']
        human_best = challenge.get('best_time')
        human_clicks = challenge.get('best_clicks')
        
        # Find our result for same challenge
        our_result = next(
            (r for r in our_results if r['start'] == start and r['end'] == end),
            None
        )
        
        if our_result:
            comparison = {
                "challenge": f"{start} → {end}",
                "human_clicks": human_clicks,
                "ai_clicks": our_result['path_length'],
                "human_time": human_best,
                "ai_time": our_result['time'],
                "ai_advantage": human_clicks - our_result['path_length']
            }
            comparisons.append(comparison)
    
    return comparisons
```

### Example 3: Create Web Demo

```python
# Simple Flask app to demo our AI
from flask import Flask, render_template, request, jsonify
from src.hybrid_navigator import HybridNavigator

app = Flask(__name__)
navigator = HybridNavigator()

@app.route('/')
def index():
    return render_template('speedrun.html')

@app.route('/api/navigate', methods=['POST'])
def navigate():
    data = request.json
    start = data['start']
    end = data['end']
    
    path, time_taken = navigator.find_path(start, end)
    
    return jsonify({
        'path': path,
        'length': len(path),
        'time': time_taken,
        'success': len(path) > 0
    })

if __name__ == '__main__':
    app.run(debug=True)
```

## Integration Checklist

### Phase 1: Analysis (Week 1)
- [ ] Clone both repositories
- [ ] Run analysis script
- [ ] Review generated report
- [ ] Identify key files and patterns
- [ ] Document useful code snippets

### Phase 2: Dataset Integration (Week 2)
- [ ] Extract challenge datasets
- [ ] Convert to our format
- [ ] Add to benchmark suite
- [ ] Classify by difficulty
- [ ] Test with our navigators

### Phase 3: Code Integration (Week 3)
- [ ] Adopt link filtering logic
- [ ] Implement path validation
- [ ] Add caching strategies
- [ ] Optimize API usage
- [ ] Update scraper code

### Phase 4: Metrics & Comparison (Week 4)
- [ ] Implement speedrun metrics
- [ ] Compare AI vs human performance
- [ ] Generate comparison reports
- [ ] Identify improvement areas
- [ ] Document findings

### Phase 5: Community Engagement (Optional)
- [ ] Create web demo
- [ ] Share results with speedrun community
- [ ] Contribute datasets back
- [ ] Collaborate on improvements
- [ ] Publish research findings

## Expected Outcomes

1. **Better Benchmarks**: Real-world challenges from speedrun community
2. **Improved Performance**: Optimized scraping and caching
3. **Validation**: Robust path verification
4. **Standardization**: Compatible metrics and scoring
5. **Community**: Connection with Wikipedia speedrun enthusiasts

## Troubleshooting

### Issue: Repositories use different languages
**Solution**: Focus on extracting data and patterns, not direct code reuse

### Issue: Different data formats
**Solution**: Create adapter functions to convert between formats

### Issue: API rate limiting
**Solution**: Adopt their caching and throttling strategies

### Issue: Missing datasets
**Solution**: Use their game logs or leaderboard data as proxy

## Resources

- [WikiSpeedrun Repository](https://github.com/B0und/WikiSpeedrun)
- [Wikipedia Speedruns Official](https://github.com/wikispeedruns/wikipedia-speedruns)
- [Analysis Script](../analyze_external_repos.py)
- [External Repos Analysis](./EXTERNAL_REPOS_ANALYSIS.md)

---

**Next Steps**: Run `python analyze_external_repos.py --clone` to begin analysis