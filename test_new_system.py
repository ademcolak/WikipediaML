#!/usr/bin/env python3
"""
Test script for new ML-powered Wikipedia navigation system
"""

import sys
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        import torch
        import sentence_transformers
        import faiss
        import scipy
        import networkx
        print("✅ All core libraries imported successfully")
        print(f"   PyTorch: {torch.__version__}")
        print(f"   CUDA available: {torch.cuda.is_available()}")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_models():
    """Test if model classes can be instantiated"""
    print("\n🔍 Testing model classes...")
    
    try:
        from models.mlp_scorer import MLPScorer
        
        # Test basic MLP
        model = MLPScorer(embedding_dim=384, hidden_dims=(256, 128))
        print(f"✅ MLPScorer created: {sum(p.numel() for p in model.parameters()):,} parameters")
        
        return True
    except Exception as e:
        print(f"❌ Model test error: {e}")
        return False

def test_core_modules():
    """Test if core modules can be imported"""
    print("\n🔍 Testing core modules...")
    
    try:
        from core.hybrid_scorer import HybridScorer
        from core.fast_hybrid_scorer import FastHybridScorer
        from core.beam_search import BeamSearchNavigator
        from core.advanced_navigator import AdvancedNavigator
        from core.wikipedia_fallback import WikipediaAPIFallback
        
        print("✅ All core modules imported successfully")
        return True
    except Exception as e:
        print(f"❌ Core module test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_data_files():
    """Check what data files exist"""
    print("\n🔍 Checking data files...")
    
    data_dir = Path("data")
    if not data_dir.exists():
        print("❌ data/ directory not found")
        return False
    
    files = list(data_dir.glob("*"))
    print(f"📁 Found {len(files)} files in data/:")
    for f in files:
        size_mb = f.stat().st_size / (1024 * 1024)
        print(f"   - {f.name}: {size_mb:.2f} MB")
    
    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("WikipediaML New System Test")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Models", test_models()))
    results.append(("Core Modules", test_core_modules()))
    results.append(("Data Files", check_data_files()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        print("\n🎉 All tests passed! System is ready.")
        print("\nNext steps:")
        print("1. Download Wikipedia data: python3 scripts/download_wikipedia_dumps.py --limit 1000")
        print("2. Parse and build graph: python3 scripts/parse_wikipedia_dumps.py")
        print("3. Build embeddings: python3 scripts/build_embedding_index.py")
        print("4. Generate training data: python3 scripts/generate_training_data.py")
        print("5. Train MLP: python3 scripts/train_mlp_scorer.py")
        return 0
    else:
        print("\n❌ Some tests failed. Please fix errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())