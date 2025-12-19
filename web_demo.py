#!/usr/bin/env python3
"""
Wikipedia Game - Interactive Web Demo
--------------------------------------
Flask-based web interface for testing Wikipedia navigators in real-time.

Features:
- Live path visualization
- Multiple algorithm selection
- Step-by-step navigation
- Performance metrics
- Interactive UI
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import time
import secrets

# Import core components
from src.knowledge_graph import WikiKnowledgeGraph
from src.scraper import WikipediaScraper
from src.embedder import WikiEmbedder
from src.semantic_navigator import SemanticNavigator
from src.bidirectional_navigator import BidirectionalNavigator

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
CORS(app)

# Initialize components
print("🚀 Initializing Wikipedia Game Demo...")
print("⚡ Production mode: Optimized for performance")
kg = WikiKnowledgeGraph()
scraper = WikipediaScraper(cache_size=512)  # Increased cache
embedder = WikiEmbedder(cache_size=4096)  # Increased cache

# Initialize navigators
print("📦 Loading navigators...")
semantic_nav = SemanticNavigator(
    verbose=False,
    use_graph=True,
    use_async=False,
    use_parallel=True,  # Enable parallel evaluation
    max_workers=4  # 4 parallel workers
)
bidirectional_nav = BidirectionalNavigator(kg, scraper)

navigators = {
    'semantic': {
        'name': 'Semantic (Greedy)',
        'description': 'Fast greedy search using semantic similarity',
        'navigator': semantic_nav
    },
    'bidirectional': {
        'name': 'Bidirectional BFS',
        'description': 'Optimal path using two-way search',
        'navigator': bidirectional_nav
    }
}

print("✅ Demo ready!")


@app.route('/')
def index():
    """Main page."""
    return render_template('index.html', algorithms=navigators)


@app.route('/api/navigate', methods=['POST'])
def navigate():
    """
    Navigate from start to end using selected algorithm.
    
    Request JSON:
    {
        "start": "Potato",
        "end": "Pizza",
        "algorithm": "semantic"
    }
    
    Response JSON:
    {
        "success": true,
        "path": ["Potato", "Tomato", "Pizza"],
        "length": 3,
        "time": 1.23,
        "algorithm": "semantic",
        "metrics": {...}
    }
    """
    try:
        data = request.json
        start = data.get('start', '').strip().replace(' ', '_')
        end = data.get('end', '').strip().replace(' ', '_')
        algorithm = data.get('algorithm', 'semantic')
        
        if not start or not end:
            return jsonify({
                'success': False,
                'error': 'Start and end articles are required'
            }), 400
        
        if algorithm not in navigators:
            return jsonify({
                'success': False,
                'error': f'Unknown algorithm: {algorithm}'
            }), 400
        
        # Navigate
        nav_info = navigators[algorithm]
        navigator = nav_info['navigator']
        start_time = time.time()
        
        if algorithm == 'semantic':
            result = navigator.search(start, end)
            path = result.path if result and result.found else []
        elif algorithm == 'bidirectional':
            path, _ = navigator.find_path(start, end)
        else:
            path = []
        
        time_taken = time.time() - start_time
        
        # Prepare response
        response = {
            'success': len(path) > 0,
            'path': path,
            'length': len(path),
            'time': round(time_taken, 3),
            'algorithm': algorithm,
            'algorithm_name': nav_info['name'],
            'metrics': {
                'steps': len(path) - 1 if len(path) > 0 else 0,
                'time_per_step': round(time_taken / max(len(path) - 1, 1), 3),
                'kg_nodes': kg.graph.number_of_nodes(),
                'kg_edges': kg.graph.number_of_edges()
            }
        }
        
        if not path:
            response['error'] = 'No path found'
        
        return jsonify(response)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/step', methods=['POST'])
def step():
    """
    Get next step from current article.
    
    Request JSON:
    {
        "current": "Potato",
        "target": "Pizza"
    }
    
    Response JSON:
    {
        "success": true,
        "next": "Tomato",
        "links": ["Tomato", "Vegetable", "Food", ...],
        "reasoning": "Semantic similarity: 0.85"
    }
    """
    try:
        data = request.json
        current = data.get('current', '').strip().replace(' ', '_')
        target = data.get('target', '').strip().replace(' ', '_')
        
        if not current or not target:
            return jsonify({
                'success': False,
                'error': 'Current and target articles are required'
            }), 400
        
        # Get links from current page
        soup = scraper.get_page_html(current)
        if not soup:
            return jsonify({
                'success': False,
                'error': f'Could not fetch page: {current}'
            }), 404
        
        links = scraper.get_wiki_links(soup)
        
        if not links:
            return jsonify({
                'success': False,
                'error': f'No links found on page: {current}'
            }), 404
        
        # Use embedder to find best link
        target_emb = embedder.get_embedding(target)
        link_scores = []
        
        for link in links[:50]:  # Limit to first 50 for performance
            link_emb = embedder.get_embedding(link)
            similarity = embedder.cosine_similarity(link_emb, target_emb)
            link_scores.append((link, similarity))
        
        link_scores.sort(key=lambda x: x[1], reverse=True)
        best_link = link_scores[0][0]
        best_score = link_scores[0][1]
        
        reasoning = f"Semantic similarity to target: {best_score:.3f}"
        top_links = [{'name': link, 'score': float(score)} for link, score in link_scores[:10]]
        
        return jsonify({
            'success': True,
            'next': best_link,
            'links': top_links,
            'all_links_count': len(links),
            'reasoning': reasoning
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stats', methods=['GET'])
def stats():
    """Get system statistics."""
    return jsonify({
        'kg': {
            'nodes': kg.graph.number_of_nodes(),
            'edges': kg.graph.number_of_edges(),
            'paths_learned': kg.paths_learned,
            'paths_reused': kg.paths_reused
        },
        'scraper': scraper.get_cache_stats(),
        'embedder': {
            'model': 'paraphrase-MiniLM-L6-v2',
            'dimension': 384
        },
        'navigators': list(navigators.keys())
    })


@app.route('/api/random', methods=['GET'])
def random_articles():
    """Get random article suggestions from benchmark dataset."""
    import random
    import json
    from pathlib import Path
    
    try:
        # Load benchmark dataset
        dataset_path = Path('benchmark/test_dataset.json')
        if dataset_path.exists():
            with open(dataset_path, 'r') as f:
                dataset = json.load(f)
            
            if dataset:
                # Randomly select a challenge
                challenge = random.choice(dataset)
                return jsonify({
                    'start': challenge['start'],
                    'end': challenge['target'],
                    'difficulty': challenge.get('difficulty', 'medium'),
                    'source': 'benchmark'
                })
    except Exception as e:
        print(f"Error loading benchmark dataset: {e}")
    
    # Fallback to curated pairs if benchmark not available
    curated_pairs = [
        ("United_States", "Washington,_D.C.", "easy"),
        ("France", "Paris", "easy"),
        ("Italy", "Rome", "easy"),
        ("Potato", "Pizza", "medium"),
        ("Computer", "Science", "easy"),
        ("Albert_Einstein", "Physics", "easy"),
        ("Mathematics", "Calculus", "medium"),
        ("Biology", "DNA", "medium"),
        ("Quantum_mechanics", "Schrödinger's_cat", "hard"),
        ("Artificial_intelligence", "Turing_test", "hard"),
    ]
    
    pair = random.choice(curated_pairs)
    return jsonify({
        'start': pair[0],
        'end': pair[1],
        'difficulty': pair[2],
        'source': 'curated'
    })


@app.route('/api/algorithms', methods=['GET'])
def get_algorithms():
    """Get available algorithms."""
    return jsonify({
        algo_id: {
            'name': info['name'],
            'description': info['description']
        }
        for algo_id, info in navigators.items()
    })


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎮 Wikipedia Game - Interactive Demo")
    print("="*60)
    print("\n📍 Open in browser: http://localhost:5001")
    print("\n🎯 Features:")
    print("  - Live path visualization")
    print("  - Multiple algorithms")
    print("  - Step-by-step navigation")
    print("  - Performance metrics")
    print("\n🔧 Available Algorithms:")
    for algo_id, info in navigators.items():
        print(f"  - {info['name']}: {info['description']}")
    print("\n⌨️  Press Ctrl+C to stop\n")
    
    # Production mode: disable debug, enable threading
    app.run(debug=False, host='0.0.0.0', port=5001, threaded=True)