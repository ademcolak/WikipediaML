#!/usr/bin/env python3
"""
train_ml_model.py
-----------------
Self-supervised ML model training script.

Bu script:
- Random Wikipedia page'lerden training data üretir
- ML modelini train eder
- Sürekli öğrenme (continuous learning) yapar
- Test verisi gerektirmez!

Usage:
    # Quick training (10 random pairs)
    python train_ml_model.py --quick
    
    # Normal training (100 random pairs)
    python train_ml_model.py
    
    # Continuous learning (10 iterations × 10 pairs)
    python train_ml_model.py --continuous
    
    # Custom
    python train_ml_model.py --pairs 50 --iterations 5
"""

import argparse
import sys
from src.semantic_navigator import SemanticNavigator
from src.ml_link_scorer import MLLinkScorer
from src.self_learning_trainer import SelfLearningTrainer


def main():
    parser = argparse.ArgumentParser(description='Train ML model with self-supervised learning')
    parser.add_argument('--quick', action='store_true', help='Quick training (10 pairs)')
    parser.add_argument('--continuous', action='store_true', help='Continuous learning mode')
    parser.add_argument('--pairs', type=int, default=100, help='Number of random page pairs')
    parser.add_argument('--iterations', type=int, default=10, help='Continuous learning iterations')
    parser.add_argument('--max-steps', type=int, default=10, help='Maximum steps per search')
    parser.add_argument('--no-verbose', action='store_true', help='Disable verbose output')
    
    args = parser.parse_args()
    
    verbose = not args.no_verbose
    
    # Quick mode
    if args.quick:
        args.pairs = 10
        args.continuous = False
    
    print("="*60)
    print("🤖 SELF-SUPERVISED ML TRAINING")
    print("="*60)
    print(f"Mode: {'Continuous' if args.continuous else 'Single'}")
    print(f"Random pairs: {args.pairs}")
    if args.continuous:
        print(f"Iterations: {args.iterations}")
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
    
    # Training
    try:
        if args.continuous:
            # Continuous learning
            trainer.continuous_learning(
                iterations=args.iterations,
                pairs_per_iteration=args.pairs // args.iterations,
                train_interval=2
            )
        else:
            # Single training session
            trainer.generate_training_data(
                num_pairs=args.pairs,
                max_steps=args.max_steps
            )
            
            # Train model
            trainer.train_model()
        
        # Show final stats
        print("\n" + "="*60)
        print("📊 FINAL STATISTICS")
        print("="*60)
        
        stats = trainer.get_stats()
        print(f"Total attempts: {stats['total_attempts']}")
        print(f"Successful: {stats['successful_attempts']}")
        print(f"Success rate: {stats['success_rate']:.1f}%")
        print(f"Training time: {stats['total_training_time']:.1f}s")
        print(f"ML model trained: {stats['ml_model_trained']}")
        print(f"Training samples: {stats['ml_training_samples']}")
        
        if stats['ml_model_trained']:
            print("\n✅ ML model is ready to use!")
            print("   Run: python main.py --ml <start> <target>")
        else:
            print("\n⚠️  ML model not trained (not enough data)")
            print("   Try running with more pairs: --pairs 100")
        
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