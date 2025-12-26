#!/usr/bin/env python3
"""
WikipediaML Play - Interaktif Oyun
===================================

Wikipedia oyunu oyna - hızlı, interaktif.
Parametre yok, sadece çalıştır.

Kullanım:
    python play.py

Özellikler:
- Interactive mode
- Knowledge Graph kullanır (hızlı)
- Beam search fallback
- Sonuçları gösterir
"""

import sys
from pathlib import Path

# Add core to path
sys.path.insert(0, str(Path(__file__).parent))

from core import Navigator


def print_banner():
    """Print welcome banner."""
    print("\n" + "="*60)
    print("🎮 WIKIPEDIAML - WIKIPEDIA GAME")
    print("="*60)
    print("\nFind the shortest path between two Wikipedia pages!")
    print("Type 'quit' or 'exit' to stop.\n")
    print("="*60)


def print_result(result):
    """Print path result."""
    print(f"\n{'='*60}")
    
    if result.found:
        print("✅ PATH FOUND!")
        print(f"{'='*60}")
        
        # Print path
        print(f"\n🛤️  Path ({result.steps} steps):")
        for i, page in enumerate(result.path):
            if i == 0:
                print(f"  🏁 {page}")
            elif i == len(result.path) - 1:
                print(f"  🎯 {page}")
            else:
                print(f"  {i}. {page}")
        
        # Print metadata
        print(f"\n📊 Stats:")
        print(f"  Steps: {result.steps}")
        print(f"  Time: {result.time_seconds:.2f}s")
        print(f"  Source: {result.source}")
        
        if result.source == 'knowledge_graph':
            print(f"  ⚡ Instant (from Knowledge Graph!)")
        else:
            print(f"  Pages explored: {result.pages_explored}")
    
    else:
        print("❌ PATH NOT FOUND")
        print(f"{'='*60}")
        print(f"\nCouldn't find a path within {result.time_seconds:.2f}s")
        print("Try different pages or wait for more training.")
    
    print(f"{'='*60}")


def get_input(prompt: str) -> str:
    """Get user input with validation."""
    while True:
        value = input(prompt).strip()
        
        if value.lower() in ['quit', 'exit', 'q']:
            return 'QUIT'
        
        if value:
            # Replace spaces with underscores
            return value.replace(' ', '_')
        
        print("⚠️  Please enter a valid page name.")


def main():
    """Main entry point."""
    print_banner()
    
    # Initialize navigator (fair play mode - no incoming links)
    print("🚀 Loading Navigator...")
    navigator = Navigator(use_bidirectional=True, training_mode=False)
    print()
    
    # Game loop
    while True:
        print("\n" + "-"*60)
        
        # Get start page
        start = get_input("Start page: ")
        if start == 'QUIT':
            break
        
        # Get target page
        target = get_input("Target page: ")
        if target == 'QUIT':
            break
        
        # Find path
        result = navigator.find_path(start, target, verbose=False)
        
        # Print result
        print_result(result)
        
        # Ask to continue
        print()
        continue_game = input("Play again? (y/n): ").strip().lower()
        if continue_game not in ['y', 'yes', '']:
            break
    
    # Save before exit
    print("\n💾 Saving Knowledge Graph...")
    navigator.save()
    
    # Print final stats
    stats = navigator.get_stats()
    print(f"\n📊 Session Stats:")
    print(f"  Searches: {stats['searches_performed']}")
    print(f"  KG hits: {stats['kg_hits']}")
    print(f"  KG hit rate: {stats['kg_hit_rate']:.1f}%")
    
    print("\n👋 Thanks for playing!\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!\n")