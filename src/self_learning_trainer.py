"""
self_learning_trainer.py
------------------------
Self-supervised learning for Wikipedia PathFinder.

Bu modül:
- Random Wikipedia page'lerden otomatik training data üretir
- Başarılı path'leri toplar ve ML modelini train eder
- Sürekli öğrenen (continual learning) sistem
- Test verisi gerektirmez!

Yaklaşım:
1. Random Wikipedia page'ler seç (Special:Random)
2. Aralarında path bul (SemanticNavigator)
3. Başarılı path'leri kaydet
4. ML modelini train et
5. Tekrarla (sürekli öğrenme)

Phase 2: Self-Supervised Learning
"""

import requests
import random
import time
from typing import List, Tuple, Optional
from collections import defaultdict
import json
from pathlib import Path


class SelfLearningTrainer:
    """
    Self-supervised learning trainer.
    
    Random Wikipedia page'lerden otomatik training data üretir.
    Test verisi gerektirmez - kendi kendine öğrenir!
    
    Features:
    - Random page selection (Special:Random)
    - Automatic path finding
    - Success/failure tracking
    - ML model training
    - Continual learning
    - Training history
    
    Usage:
        trainer = SelfLearningTrainer(navigator, ml_scorer)
        
        # Generate training data
        trainer.generate_training_data(num_pairs=100)
        
        # Train ML model
        trainer.train_model()
        
        # Continuous learning
        trainer.continuous_learning(iterations=10)
    """
    
    def __init__(
        self,
        semantic_navigator,
        ml_scorer,
        history_file: str = 'cache/training_history.json',
        verbose: bool = True
    ):
        """
        Initialize Self-Learning Trainer.
        
        Args:
            semantic_navigator: SemanticNavigator instance
            ml_scorer: MLLinkScorer instance
            history_file: Path to save training history
            verbose: Print progress information
        """
        self.navigator = semantic_navigator
        self.ml_scorer = ml_scorer
        self.history_file = Path(history_file)
        self.verbose = verbose
        
        # Training data
        self.successful_paths = []
        self.failed_attempts = []
        
        # Statistics
        self.total_attempts = 0
        self.successful_attempts = 0
        self.total_training_time = 0.0
        
        # Load history
        self._load_history()
    
    def get_random_page(self) -> Optional[str]:
        """
        Get random Wikipedia page using Special:Random.
        
        Returns:
            Page title or None if failed
        """
        try:
            headers = {
                'User-Agent': 'WikipediaML/3.4.0 (Educational Project; Python/requests)'
            }
            
            response = requests.get(
                'https://en.wikipedia.org/wiki/Special:Random',
                headers=headers,
                allow_redirects=True,
                timeout=10
            )
            
            response.raise_for_status()
            
            # Extract page title from final URL
            final_url = response.url
            
            if '/wiki/' not in final_url:
                if self.verbose:
                    print(f"⚠️  Invalid URL: {final_url}")
                return None
            
            page_title = final_url.split('/wiki/')[-1]
            
            # Filter out special pages
            if ':' in page_title:
                if self.verbose:
                    print(f"⚠️  Special page filtered: {page_title}")
                return None
            
            if self.verbose:
                print(f"   ✅ Random page: {page_title}")
            
            return page_title
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Error getting random page: {e}")
                import traceback
                traceback.print_exc()
            return None
    
    def get_random_page_pair(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Get two random Wikipedia pages.
        
        Returns:
            (start_page, target_page) or (None, None) if failed
        """
        start = self.get_random_page()
        if not start:
            return None, None
        
        # Wait a bit to avoid rate limiting
        time.sleep(0.5)
        
        target = self.get_random_page()
        if not target:
            return None, None
        
        # Make sure they're different
        if start == target:
            return self.get_random_page_pair()
        
        return start, target
    
    def find_path_and_record(
        self,
        start: str,
        target: str,
        max_steps: int = 10
    ) -> bool:
        """
        Find path between two pages and record result.
        
        Args:
            start: Start page
            target: Target page
            max_steps: Maximum steps
            
        Returns:
            True if path found, False otherwise
        """
        if self.verbose:
            print(f"\n🔍 Searching: {start} → {target}")
        
        try:
            # Use greedy semantic search for training (much faster!)
            # hybrid_search is too slow with bidirectional beam search
            result = self.navigator.greedy_semantic_search(start, target, max_steps=max_steps)
            
            self.total_attempts += 1
            
            if result.found:
                # Success! Record path
                self.successful_paths.append(result.path)
                self.successful_attempts += 1
                
                if self.verbose:
                    print(f"✅ Path found: {len(result.path)} steps")
                    print(f"   Path: {' → '.join(result.path)}")
                
                return True
            else:
                # Failed
                self.failed_attempts.append((start, target))
                
                if self.verbose:
                    print(f"❌ Path not found")
                
                return False
                
        except Exception as e:
            if self.verbose:
                print(f"❌ Error during search: {e}")
            return False
    
    def generate_training_data(
        self,
        num_pairs: int = 100,
        max_steps: int = 10,
        save_interval: int = 10
    ):
        """
        Generate training data from random page pairs.
        
        Args:
            num_pairs: Number of random page pairs to try
            max_steps: Maximum steps per search
            save_interval: Save history every N attempts
        """
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"🤖 SELF-SUPERVISED LEARNING")
            print(f"{'='*60}")
            print(f"Generating training data from {num_pairs} random page pairs...")
            print(f"This will take approximately {num_pairs * 2} minutes.\n")
        
        start_time = time.time()
        
        for i in range(num_pairs):
            if self.verbose:
                print(f"\n{'─'*60}")
                print(f"Pair {i+1}/{num_pairs}")
            
            # Get random page pair
            start, target = self.get_random_page_pair()
            
            if not start or not target:
                if self.verbose:
                    print("⚠️  Failed to get random pages, skipping...")
                continue
            
            # Find path
            self.find_path_and_record(start, target, max_steps)
            
            # Save history periodically
            if (i + 1) % save_interval == 0:
                self._save_history()
                
                if self.verbose:
                    success_rate = (self.successful_attempts / self.total_attempts * 100) if self.total_attempts > 0 else 0
                    print(f"\n📊 Progress: {i+1}/{num_pairs}")
                    print(f"   Success rate: {success_rate:.1f}%")
                    print(f"   Successful paths: {len(self.successful_paths)}")
            
            # Rate limiting
            time.sleep(1.0)
        
        elapsed = time.time() - start_time
        self.total_training_time += elapsed
        
        # Final save
        self._save_history()
        
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"✅ Training data generation complete!")
            print(f"{'='*60}")
            print(f"Total attempts: {self.total_attempts}")
            print(f"Successful: {self.successful_attempts}")
            
            # Avoid division by zero
            if self.total_attempts > 0:
                success_rate = self.successful_attempts / self.total_attempts * 100
                print(f"Success rate: {success_rate:.1f}%")
            else:
                print(f"Success rate: N/A (no attempts made)")
            
            print(f"Time: {elapsed:.1f}s")
            
            # Debug info if no attempts
            if self.total_attempts == 0:
                print(f"\n⚠️  WARNING: No attempts were made!")
                print(f"   This usually means:")
                print(f"   1. Network connection issue")
                print(f"   2. Wikipedia API not responding")
                print(f"   3. Random page fetching failed")
                print(f"\n   Try checking your internet connection and try again.")
    
    def train_model(self):
        """
        Train ML model from collected paths.
        """
        if len(self.successful_paths) < 10:
            if self.verbose:
                print(f"⚠️  Not enough training data ({len(self.successful_paths)} paths)")
                print(f"   Need at least 10 successful paths to train.")
            return
        
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"🤖 Training ML Model")
            print(f"{'='*60}")
            print(f"Training from {len(self.successful_paths)} successful paths...")
        
        try:
            # Train model
            self.ml_scorer.train_from_paths(
                paths=self.successful_paths,
                embedder=self.navigator.embedder,
                category_analyzer=self.navigator.link_filter.category_analyzer,
                knowledge_graph=self.navigator.knowledge_graph
            )
            
            if self.verbose:
                print(f"✅ Model trained successfully!")
                
                # Show feature importance
                importance = self.ml_scorer.get_feature_importance()
                if importance:
                    print(f"\n📊 Feature Importance:")
                    sorted_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)
                    for feature, score in sorted_features[:5]:
                        print(f"   {feature}: {score:.3f}")
        
        except Exception as e:
            if self.verbose:
                print(f"❌ Training failed: {e}")
    
    def continuous_learning(
        self,
        iterations: int = 10,
        pairs_per_iteration: int = 10,
        train_interval: int = 2
    ):
        """
        Continuous learning loop.
        
        Args:
            iterations: Number of learning iterations
            pairs_per_iteration: Random pairs per iteration
            train_interval: Train model every N iterations
        """
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"🔄 CONTINUOUS LEARNING")
            print(f"{'='*60}")
            print(f"Iterations: {iterations}")
            print(f"Pairs per iteration: {pairs_per_iteration}")
            print(f"Train interval: {train_interval}\n")
        
        for i in range(iterations):
            if self.verbose:
                print(f"\n{'='*60}")
                print(f"Iteration {i+1}/{iterations}")
                print(f"{'='*60}")
            
            # Generate training data
            self.generate_training_data(
                num_pairs=pairs_per_iteration,
                save_interval=5
            )
            
            # Train model periodically
            if (i + 1) % train_interval == 0:
                self.train_model()
            
            # Show progress
            if self.verbose:
                print(f"\n📊 Overall Progress:")
                print(f"   Total attempts: {self.total_attempts}")
                print(f"   Successful paths: {len(self.successful_paths)}")
                print(f"   Success rate: {self.successful_attempts / self.total_attempts * 100:.1f}%")
                print(f"   Model updates: {self.ml_scorer.model_updates}")
    
    def _save_history(self):
        """Save training history to disk."""
        try:
            history = {
                'successful_paths': self.successful_paths,
                'failed_attempts': self.failed_attempts,
                'total_attempts': self.total_attempts,
                'successful_attempts': self.successful_attempts,
                'total_training_time': self.total_training_time
            }
            
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2)
            
            if self.verbose:
                print(f"💾 Training history saved to {self.history_file}")
        
        except Exception as e:
            if self.verbose:
                print(f"⚠️  Failed to save history: {e}")
    
    def _load_history(self):
        """Load training history from disk."""
        if not self.history_file.exists():
            return
        
        try:
            with open(self.history_file, 'r') as f:
                history = json.load(f)
            
            self.successful_paths = history.get('successful_paths', [])
            self.failed_attempts = history.get('failed_attempts', [])
            self.total_attempts = history.get('total_attempts', 0)
            self.successful_attempts = history.get('successful_attempts', 0)
            self.total_training_time = history.get('total_training_time', 0.0)
            
            if self.verbose:
                print(f"📦 Loaded training history from {self.history_file}")
                print(f"   Successful paths: {len(self.successful_paths)}")
                print(f"   Total attempts: {self.total_attempts}")
        
        except Exception as e:
            if self.verbose:
                print(f"⚠️  Failed to load history: {e}")
    
    def get_stats(self) -> dict:
        """Get training statistics."""
        success_rate = (self.successful_attempts / self.total_attempts * 100) if self.total_attempts > 0 else 0
        
        return {
            'total_attempts': self.total_attempts,
            'successful_attempts': self.successful_attempts,
            'failed_attempts': len(self.failed_attempts),
            'success_rate': success_rate,
            'successful_paths': len(self.successful_paths),
            'total_training_time': self.total_training_time,
            'ml_model_trained': self.ml_scorer.model is not None,
            'ml_training_samples': self.ml_scorer.training_samples
        }
    
    def clear_history(self):
        """Clear training history."""
        self.successful_paths = []
        self.failed_attempts = []
        self.total_attempts = 0
        self.successful_attempts = 0
        self.total_training_time = 0.0
        
        if self.history_file.exists():
            self.history_file.unlink()
        
        if self.verbose:
            print("🗑️  Training history cleared")