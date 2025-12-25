#!/usr/bin/env python3
"""
WikipediaML Training - Sürekli Öğrenme
======================================

Otomatik training - gece çalışır, sürekli öğrenir.
Parametre yok, sadece çalıştır.

Kullanım:
    python train.py

Özellikler:
- Random challenge'lar oluşturur
- Path bulur ve KG'ye kaydeder
- Her 100 path'te bir otomatik save
- Ctrl+C ile güvenli çıkış
"""

import sys
import time
import random
import signal
from pathlib import Path

# Add core to path
sys.path.insert(0, str(Path(__file__).parent))

from core import Navigator


class Trainer:
    """Training orchestrator."""
    
    def __init__(self):
        """Initialize trainer."""
        self.navigator = Navigator()
        self.running = True
        self.iterations = 0
        self.successful = 0
        self.failed = 0
        
        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully."""
        print("\n\n⚠️  Stopping training...")
        self.running = False
    
    def generate_challenge(self) -> tuple[str, str]:
        """
        Generate random challenge.
        
        Strategy: Use popular pages for better connectivity.
        """
        # Popular pages (high connectivity)
        popular_pages = [
            'United_States', 'United_Kingdom', 'France', 'Germany', 'Italy',
            'China', 'Japan', 'India', 'Russia', 'Brazil',
            'Europe', 'Asia', 'Africa', 'North_America', 'South_America',
            'World_War_II', 'World_War_I', 'Cold_War',
            'Science', 'Technology', 'Mathematics', 'Physics', 'Chemistry',
            'Biology', 'Computer_science', 'Engineering',
            'History', 'Geography', 'Philosophy', 'Religion',
            'Art', 'Music', 'Literature', 'Film',
            'Sports', 'Football', 'Basketball', 'Tennis',
            'New_York_City', 'London', 'Paris', 'Tokyo', 'Rome'
        ]
        
        # Select two different pages
        start = random.choice(popular_pages)
        target = random.choice([p for p in popular_pages if p != start])
        
        return start, target
    
    def train_iteration(self):
        """Run one training iteration."""
        self.iterations += 1
        
        # Generate challenge
        start, target = self.generate_challenge()
        
        print(f"\n{'='*60}")
        print(f"Iteration {self.iterations}")
        print(f"Challenge: {start} → {target}")
        print(f"{'='*60}")
        
        # Find path
        result = self.navigator.find_path(start, target, verbose=True)
        
        # Update stats
        if result.found:
            self.successful += 1
        else:
            self.failed += 1
        
        # Auto-save every 100 iterations
        if self.iterations % 100 == 0:
            self.navigator.save()
            self._print_stats()
    
    def _print_stats(self):
        """Print training statistics."""
        print(f"\n{'='*60}")
        print("📊 TRAINING STATISTICS")
        print(f"{'='*60}")
        print(f"Iterations: {self.iterations}")
        print(f"Successful: {self.successful} ({self.successful/self.iterations*100:.1f}%)")
        print(f"Failed: {self.failed} ({self.failed/self.iterations*100:.1f}%)")
        
        stats = self.navigator.get_stats()
        print(f"\nKnowledge Graph:")
        print(f"  Nodes: {stats['knowledge']['nodes']}")
        print(f"  Edges: {stats['knowledge']['edges']}")
        print(f"  Paths learned: {stats['knowledge']['paths_learned']}")
        print(f"  Cache hit rate: {stats['kg_hit_rate']:.1f}%")
        print(f"{'='*60}")
    
    def run(self):
        """Run training loop."""
        print("\n" + "="*60)
        print("🏭 WIKIPEDIAML TRAINING")
        print("="*60)
        print("\nTraining will run continuously.")
        print("Press Ctrl+C to stop and save.\n")
        print("="*60)
        
        try:
            while self.running:
                self.train_iteration()
                
                # Rate limiting (be nice to Wikipedia)
                time.sleep(2)
        
        except KeyboardInterrupt:
            pass
        
        finally:
            # Final save
            print("\n\n💾 Saving final state...")
            self.navigator.save()
            self._print_stats()
            print("\n✅ Training complete!")


def main():
    """Main entry point."""
    trainer = Trainer()
    trainer.run()


if __name__ == '__main__':
    main()