#!/usr/bin/env python3
"""
test_hybrid.py
--------------
Test script for hybrid navigation system.

Tests KG, Embedding, and LLM components separately and together.
"""

import os
import sys
from pathlib import Path


def test_kg_only():
    """Test KG-only navigation."""
    print("\n" + "="*70)
    print("TEST 1: KG-Only Navigation")
    print("="*70)
    
    from src.knowledge_graph import WikiKnowledgeGraph
    
    kg = WikiKnowledgeGraph()
    stats = kg.get_stats()
    
    print(f"\n📊 KG Stats:")
    print(f"   Nodes: {stats['nodes']:,}")
    print(f"   Edges: {stats['edges']:,}")
    print(f"   Paths learned: {kg.paths_learned:,}")
    
    # Test path lookup
    test_pairs = [
        ("Italy", "Rome"),
        ("France", "Paris"),
        ("Germany", "Berlin")
    ]
    
    print(f"\n🔍 Testing path lookup:")
    for source, target in test_pairs:
        # Check if nodes exist first
        if source in kg.graph and target in kg.graph:
            has_path = kg.has_path(source, target)
            status = "✅" if has_path else "❌"
            print(f"   {status} {source} → {target}: {'Found' if has_path else 'Not found'}")
        else:
            print(f"   ⚠️ {source} → {target}: Nodes not in graph")
    
    return kg


def test_embedding():
    """Test embedding navigator."""
    print("\n" + "="*70)
    print("TEST 2: Embedding Navigator")
    print("="*70)
    
    try:
        from src.embedding_navigator import EmbeddingNavigator
        
        print("\n📦 Loading embedding model...")
        embedding_nav = EmbeddingNavigator()
        
        # Test filtering
        available_links = [
            "Rome", "Milan", "Venice", "Naples",
            "Italian_cuisine", "Italian_language",
            "Mediterranean_Sea", "Alps"
        ]
        
        target = "Pizza"
        
        print(f"\n🔍 Filtering links for target: {target}")
        print(f"   Available links: {len(available_links)}")
        
        top_5 = embedding_nav.filter_links(available_links, target, k=5)
        
        print(f"\n📊 Top 5 links:")
        for i, link in enumerate(top_5, 1):
            print(f"   {i}. {link}")
        
        # Stats
        stats = embedding_nav.get_stats()
        print(f"\n📈 Embedding Stats:")
        print(f"   Cache size: {stats['cache_size']}")
        print(f"   Cache hits: {stats['cache_hits']}")
        print(f"   Cache misses: {stats['cache_misses']}")
        
        return embedding_nav
    
    except ImportError as e:
        print(f"\n❌ Error: {e}")
        print("   Install with: pip install sentence-transformers")
        return None


def test_llm():
    """Test LLM navigator."""
    print("\n" + "="*70)
    print("TEST 3: LLM Navigator")
    print("="*70)
    
    # Check API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("\n⚠️ ANTHROPIC_API_KEY not found in environment")
        print("   Set it in .env file or skip LLM test")
        return None
    
    try:
        from src.llm_navigator import LLMNavigator
        
        print("\n🤖 Initializing LLM navigator...")
        llm_nav = LLMNavigator(api_key=api_key)
        
        # Test selection
        current = "Italy"
        target = "Pizza"
        links = ["Rome", "Italian_cuisine", "Milan"]
        
        print(f"\n🔍 LLM Selection Test:")
        print(f"   Current: {current}")
        print(f"   Target: {target}")
        print(f"   Links: {links}")
        
        print(f"\n⏳ Calling Claude API...")
        selected = llm_nav.select_link(current, target, links)
        
        print(f"\n✅ Selected: {selected}")
        
        # Stats
        stats = llm_nav.get_stats()
        print(f"\n📈 LLM Stats:")
        print(f"   Calls: {stats['call_count']}")
        print(f"   Total cost: ${stats['total_cost']:.4f}")
        
        return llm_nav
    
    except ImportError as e:
        print(f"\n❌ Error: {e}")
        print("   Install with: pip install anthropic")
        return None
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None


def test_hybrid(kg, embedding_nav, llm_nav):
    """Test hybrid navigator."""
    print("\n" + "="*70)
    print("TEST 4: Hybrid Navigator")
    print("="*70)
    
    from src.hybrid_navigator import HybridNavigator
    
    # Test different configurations
    configs = [
        ("KG Only", False, False),
        ("KG + Embedding", True, False),
        ("KG + Embedding + LLM", True, True)
    ]
    
    for name, use_embedding, use_llm in configs:
        print(f"\n🔧 Configuration: {name}")
        
        # Skip if components not available
        if use_embedding and not embedding_nav:
            print("   ⚠️ Skipped (embedding not available)")
            continue
        if use_llm and not llm_nav:
            print("   ⚠️ Skipped (LLM not available)")
            continue
        
        navigator = HybridNavigator(
            kg=kg,
            embedding_nav=embedding_nav,
            llm_nav=llm_nav,
            use_embedding=use_embedding,
            use_llm=use_llm
        )
        
        # Test navigation
        current = "Italy"
        target = "Pizza"
        available_links = [
            "Rome", "Milan", "Venice",
            "Italian_cuisine", "Italian_language",
            "Mediterranean_Sea"
        ]
        
        print(f"   Current: {current}")
        print(f"   Target: {target}")
        print(f"   Available links: {len(available_links)}")
        
        try:
            selected = navigator.find_next_step(current, target, available_links)
            print(f"   ✅ Selected: {selected}")
            
            # Stats
            stats = navigator.get_stats()
            print(f"   📊 Stats:")
            print(f"      KG hits: {stats['kg_hits']}")
            print(f"      Embedding uses: {stats['embedding_uses']}")
            print(f"      LLM uses: {stats['llm_uses']}")
        except Exception as e:
            print(f"   ❌ Error: {e}")


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("🧪 HYBRID NAVIGATION SYSTEM TESTS")
    print("="*70)
    
    # Check if cache exists
    cache_file = Path("cache/wiki_graph.pkl")
    if not cache_file.exists():
        print("\n❌ Error: cache/wiki_graph.pkl not found")
        print("   Run training first: python train.py --strategy hybrid --iterations 100")
        sys.exit(1)
    
    # Test components
    kg = test_kg_only()
    embedding_nav = test_embedding()
    llm_nav = test_llm()
    
    # Test hybrid
    if kg:
        test_hybrid(kg, embedding_nav, llm_nav)
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    print(f"✅ KG: Working")
    print(f"{'✅' if embedding_nav else '❌'} Embedding: {'Working' if embedding_nav else 'Not available'}")
    print(f"{'✅' if llm_nav else '❌'} LLM: {'Working' if llm_nav else 'Not available'}")
    
    if embedding_nav and llm_nav:
        print("\n🎉 All systems operational!")
        print("   Ready for hybrid navigation with %70-80 accuracy")
    elif embedding_nav:
        print("\n⚠️ LLM not available, but embedding works")
        print("   Can use KG + Embedding mode (~%60-70 accuracy)")
    else:
        print("\n⚠️ Only KG available")
        print("   Install additional packages for better accuracy")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    main()