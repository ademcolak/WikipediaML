#!/usr/bin/env python3
"""
visualize_demo.py
-----------------
Demo script for 3D visualization of Wikipedia PathFinder.

Usage:
    python visualize_demo.py
    
Then open wiki_graph_3d.html in your browser!
"""

from src.semantic_navigator import SemanticNavigator
from src.visualizer import WikiVisualizer

def main():
    print("=" * 80)
    print("🎨 Wikipedia PathFinder - 3D Visualization Demo")
    print("=" * 80)
    
    # Initialize navigator
    print("\n📦 Initializing navigator...")
    navigator = SemanticNavigator(verbose=False, use_graph=True)
    
    # Test cases
    test_cases = [
        ("France", "Germany", "Kolay - Komşu ülkeler"),
        ("Computer", "Science", "Orta - İlgili konular"),
        ("Potato", "Pizza", "Orta - Yemek ilişkisi"),
    ]
    
    print("\n🔍 Finding paths...")
    results = []
    
    for start, target, description in test_cases:
        print(f"\n  • {start} → {target} ({description})")
        
        result = navigator.bidirectional_beam_search(
            start=start,
            target=target,
            beam_width=4,
            max_depth=10
        )
        
        if result.found:
            print(f"    ✅ Found in {result.steps} steps, {result.time_seconds:.2f}s")
            results.append((start, target, result))
        else:
            print(f"    ❌ Not found")
    
    # Create visualizer
    print("\n🎨 Creating 3D visualization...")
    visualizer = WikiVisualizer(
        knowledge_graph=navigator.knowledge_graph,
        embedder=navigator.embedder
    )
    
    # Visualize each result
    for i, (start, target, result) in enumerate(results):
        print(f"\n📊 Visualizing: {start} → {target}")
        
        # Create 3D plot
        fig = visualizer.visualize_graph(
            max_nodes=50,  # Limit for performance
            path=result.path,
            target=target
        )
        
        # Save to HTML
        filename = f"wiki_graph_3d_{i+1}_{start}_to_{target}.html"
        visualizer.save_html(fig, filename)
    
    # Create overall graph visualization
    print("\n📊 Creating overall graph visualization...")
    fig = visualizer.visualize_graph(max_nodes=100)
    visualizer.save_html(fig, "wiki_graph_3d_overall.html")
    
    print("\n" + "=" * 80)
    print("✅ Visualization complete!")
    print("=" * 80)
    print("\n📂 Generated files:")
    for i, (start, target, _) in enumerate(results):
        filename = f"wiki_graph_3d_{i+1}_{start}_to_{target}.html"
        print(f"   • {filename}")
    print(f"   • wiki_graph_3d_overall.html")
    
    print("\n🌐 Open these HTML files in your browser to see the 3D visualization!")
    print("   You can:")
    print("   • Rotate: Click and drag")
    print("   • Zoom: Scroll wheel")
    print("   • Pan: Right-click and drag")
    print("   • Hover: See node details")
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()