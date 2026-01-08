#!/usr/bin/env python3
"""
Quick Start Script - Test new system with minimal Wikipedia data
Creates a small prototype to validate the architecture
"""

import sys
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Run a command and show progress"""
    print(f"\n{'='*60}")
    print(f"📌 {description}")
    print(f"{'='*60}")
    print(f"$ {cmd}\n")
    
    result = subprocess.run(cmd, shell=True, cwd=Path.cwd())
    
    if result.returncode != 0:
        print(f"\n❌ Failed: {description}")
        return False
    
    print(f"\n✅ Completed: {description}")
    return True

def main():
    """Run quick start pipeline"""
    print("""
╔══════════════════════════════════════════════════════════╗
║         WikipediaML Quick Start (Prototype Mode)         ║
║                                                          ║
║  This will create a small prototype with ~1000 pages    ║
║  Estimated time: 30-60 minutes                          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # Activate venv
    venv_python = "source venv/bin/activate && python3"
    
    steps = [
        (
            f"{venv_python} scripts/download_wikipedia_dumps.py --limit 1000",
            "Step 1/5: Download Wikipedia sample (1000 pages)"
        ),
        (
            f"{venv_python} scripts/parse_wikipedia_dumps.py",
            "Step 2/5: Parse and clean Wikipedia data"
        ),
        (
            f"{venv_python} scripts/build_adjacency_map.py",
            "Step 3/5: Build graph adjacency matrix"
        ),
        (
            f"{venv_python} scripts/build_embedding_index.py",
            "Step 4/5: Generate embeddings and FAISS index"
        ),
        (
            f"{venv_python} scripts/generate_training_data.py --num_samples 5000",
            "Step 5/5: Generate training dataset"
        ),
    ]
    
    # Run pipeline
    for cmd, desc in steps:
        if not run_command(cmd, desc):
            print("\n❌ Pipeline failed. Please check errors above.")
            return 1
    
    print("""
╔══════════════════════════════════════════════════════════╗
║                  ✅ Setup Complete!                      ║
╚══════════════════════════════════════════════════════════╝

Next steps:

1. Train the MLP model:
   source venv/bin/activate
   python3 scripts/train_mlp_scorer.py --epochs 20

2. Run benchmark tests:
   python3 scripts/benchmark_navigator.py

3. Test navigation:
   python3 -c "from core.beam_search import BeamSearchNavigator; nav = BeamSearchNavigator(); print(nav.find_path('Python', 'Computer'))"

For full Wikipedia training (2-3 days):
   python3 scripts/download_wikipedia_dumps.py  # No --limit flag
   # Then repeat steps 2-5 above
    """)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())