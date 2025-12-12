#!/usr/bin/env python3
"""
train_ml_model_curated.py
--------------------------
ML model training with curated dataset.

Bu script:
- Curated (önceden hazırlanmış) dataset kullanır
- Kolay Wikipedia page çiftleri ile eğitir
- Random page'lerden daha yüksek başarı oranı
- Daha hızlı ve güvenilir training

Usage:
    # Tüm dataset ile eğit (50 çift)
    python train_ml_model_curated.py
    
    # İlk 10 çift ile test
    python train_ml_model_curated.py --limit 10
    
    # Sessiz mod
    python train_ml_model_curated.py --no-verbose
"""

import argparse
import sys
import json
from pathlib import Path
from src.semantic_navigator import SemanticNavigator
from src.ml_link_scorer import MLLinkScorer
from src.self_learning_trainer import SelfLearningTrainer


def load_curated_dataset(dataset_file: str = 'data/training_dataset.json', limit: int | None = None):
    """
    Load curated dataset from JSON file.
    
    Args:
        dataset_file: Path to dataset JSON file
        limit: Maximum number of pairs to load (None = all)
        
    Returns:
        List of (start, target) tuples
    """
    try:
        with open(dataset_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        pairs = [(pair['start'], pair['target']) for pair in data['pairs']]
        
        if limit:
            pairs = pairs[:limit]
        
        return pairs
    
    except FileNotFoundError:
        print(f"❌ Dataset file not found: {dataset_file}")
        print("\nPlease make sure 'training_dataset.json' exists in the project root.")
        sys.exit(1)
    
    except Exception as e:
        print(f"❌ Error loading dataset: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Train ML model with curated dataset')
    parser.add_argument('--dataset', type=str, default='data/training_dataset.json',
                       help='Path to curated dataset JSON file')
    parser.add_argument('--limit', type=int, default=None, 
                       help='Limit number of pairs (for testing)')
    parser.add_argument('--max-steps', type=int, default=10, 
                       help='Maximum steps per search')
    parser.add_argument('--no-verbose', action='store_true', 
                       help='Disable verbose output')
    
    args = parser.parse_args()
    
    verbose = not args.no_verbose
    
    # Load curated dataset
    print("="*60)
    print("🤖 ML TRAINING WITH CURATED DATASET")
    print("="*60)
    print(f"📁 Loading dataset: {args.dataset}")
    
    pairs = load_curated_dataset(args.dataset, args.limit)
    
    print(f"✅ Loaded {len(pairs)} page pairs")
    print(f"Max steps: {args.max_steps}")
    print("="*60)
    
    # Initialize components
    print("\n📦 Initializing components...")
    
    try:
        navigator = SemanticNavigator(
            verbose=verbose,
            use_graph=True,
            use_claude=False
        )
        print("✅ SemanticNavigator initialized")
        
        ml_scorer = MLLinkScorer(verbose=verbose)
        print("✅ MLLinkScorer initialized")
        
        trainer = SelfLearningTrainer(
            semantic_navigator=navigator,
            ml_scorer=ml_scorer,
            verbose=verbose
        )
        print("✅ SelfLearningTrainer initialized")
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        print("\nMake sure you have installed dependencies:")
        print("  pip install xgboost scikit-learn")
        sys.exit(1)
    
    # Training with curated pairs
    print(f"\n{'='*60}")
    print(f"🎓 TRAINING WITH CURATED DATASET")
    print(f"{'='*60}")
    print(f"Processing {len(pairs)} page pairs...")
    print(f"Estimated time: {len(pairs) * 1.5:.0f}-{len(pairs) * 3:.0f} minutes\n")
    
    successful = 0
    failed = 0
    
    try:
        for i, (start, target) in enumerate(pairs, 1):
            if verbose:
                print(f"\n{'─'*60}")
                print(f"Pair {i}/{len(pairs)}: {start} → {target}")
            
            # Find path and record
            success = trainer.find_path_and_record(start, target, max_steps=args.max_steps)
            
            if success:
                successful += 1
            else:
                failed += 1
            
            # Show progress
            if verbose:
                success_rate = (successful / i) * 100
                print(f"\n📊 Progress: {i}/{len(pairs)}")
                print(f"   Success rate: {success_rate:.1f}%")
                print(f"   Successful paths: {successful}")
                print(f"   Failed attempts: {failed}")
            
            # Save progress periodically
            if i % 10 == 0:
                trainer._save_history()
                if verbose:
                    print(f"💾 Progress saved")
        
        # Final save
        trainer._save_history()
        
        # Train model if we have enough data
        print(f"\n{'='*60}")
        print(f"🎓 TRAINING ML MODEL")
        print(f"{'='*60}")
        
        if successful >= 10:
            print(f"✅ Sufficient training data: {successful} successful paths")
            print(f"🔄 Training ML model...")
            
            trainer.train_model()
            
            print(f"✅ ML model trained successfully!")
        else:
            print(f"⚠️  Insufficient training data: {successful} successful paths")
            print(f"   Need at least 10 successful paths")
            print(f"   Try running with more pairs or easier targets")
        
        # Show final stats
        print(f"\n{'='*60}")
        print(f"📊 FINAL STATISTICS")
        print(f"{'='*60}")
        
        stats = trainer.get_stats()
        print(f"Total attempts: {stats['total_attempts']}")
        print(f"Successful: {stats['successful_attempts']}")
        print(f"Failed: {failed}")
        print(f"Success rate: {stats['success_rate']:.1f}%")
        print(f"Training time: {stats['total_training_time']:.1f}s")
        print(f"ML model trained: {stats['ml_model_trained']}")
        print(f"Training samples: {stats['ml_training_samples']}")
        
        if stats['ml_model_trained']:
            print("\n✅ ML model is ready to use!")
            print("   Run: python main.py --ml <start> <target>")
        else:
            print("\n⚠️  ML model not trained (not enough data)")
            print("   Try running with full dataset (no --limit)")
        
        print(f"\n{'='*60}")
        print(f"💾 CACHE FILES GENERATED")
        print(f"{'='*60}")
        print(f"cache/ml_model.pkl          - Trained XGBoost model")
        print(f"cache/ml_scaler.pkl         - Feature scaler")
        print(f"cache/training_history.json - Training history")
        print(f"cache/embeddings_cache.pkl  - Semantic embeddings")
        print(f"cache/wiki_graph.pkl        - Knowledge graph")
        print(f"{'='*60}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Training interrupted by user")
        print("Saving progress...")
        trainer._save_history()
        sys.exit(0)
    
    except Exception as e:
        print(f"\n❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()