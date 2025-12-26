#!/usr/bin/env python3
"""
WikipediaML Training - Dynamic Discovery Learning
==================================================

Otomatik training - gece çalışır, sürekli öğrenir.
Parametre yok, sadece çalıştır.

Kullanım:
    python train.py

Özellikler:
- Dynamic page discovery (başlangıç: 43 sayfa → sonsuz)
- Her başarılı path'ten yeni sayfalar keşfeder
- Sonsuz varyasyon, tekrar yok
- Her 100 path'te bir otomatik save
- Ctrl+C ile güvenli çıkış

Nasıl Çalışır:
1. 43 popüler sayfa ile başlar
2. Path bulunca, path'teki tüm sayfaları havuza ekler
3. Her sayfanın ilk 5 linkini de ekler
4. Havuz büyüdükçe challenge çeşitliliği artar
5. 1000. iterasyonda ~5000+ sayfa, 25M+ kombinasyon!
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
    """Training orchestrator with dynamic page discovery."""
    
    def __init__(self):
        """Initialize trainer."""
        self.navigator = Navigator(use_bidirectional=True, training_mode=True)
        self.running = True
        self.iterations = 0
        self.successful = 0
        self.failed = 0
        
        # Dynamic page pool - starts with popular pages, grows over time
        self.page_pool = set([
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
        ])
        
        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully."""
        print("\n\n⚠️  Stopping training...")
        self.running = False
    
    def add_discovered_pages(self, path: list[str]):
        """
        Add pages from successful path to the pool.
        Also adds some links from each page for exploration.
        
        Args:
            path: Successful path found
        """
        # Add all pages in the path
        initial_size = len(self.page_pool)
        self.page_pool.update(path)
        
        # Add some links from each page (for exploration)
        for page in path:
            try:
                links = self.navigator.wiki.get_links(page)
                if links:
                    # Add first 5 links from each page
                    self.page_pool.update(links[:5])
            except:
                pass  # Skip if page fetch fails
        
        new_pages = len(self.page_pool) - initial_size
        if new_pages > 0:
            print(f"   📚 Discovered {new_pages} new pages (pool: {len(self.page_pool)})")
    
    def generate_challenge(self) -> tuple[str, str]:
        """
        Generate random challenge from dynamic page pool.
        
        Strategy:
        - Start with popular pages
        - Grow pool by discovering new pages from successful paths
        - This creates infinite variety and prevents repetition
        """
        # Convert set to list for random selection
        pages = list(self.page_pool)
        
        # Select two different pages
        start = random.choice(pages)
        target = random.choice([p for p in pages if p != start])
        
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
        
        try:
            # Find path with timeout protection
            result = self.navigator.find_path(start, target, verbose=True)
            
            # Update stats
            if result.found:
                self.successful += 1
                # Add discovered pages to pool for future challenges
                self.add_discovered_pages(result.path)
            else:
                self.failed += 1
        
        except KeyboardInterrupt:
            # Re-raise to stop training
            raise
        
        except Exception as e:
            # Catch any other errors, log and continue
            print(f"\n⚠️  Error in iteration: {e}")
            self.failed += 1
        
        # Auto-save every 10 iterations (more frequent)
        if self.iterations % 10 == 0:
            self.navigator.save()
            print(f"\n💾 Auto-saved at iteration {self.iterations}")
        
        # Print stats every 100 iterations
        if self.iterations % 100 == 0:
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
        
        print(f"\nDynamic Discovery:")
        print(f"  Page pool size: {len(self.page_pool)}")
        print(f"  Unique challenges: {len(self.page_pool) * (len(self.page_pool) - 1):,}")
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