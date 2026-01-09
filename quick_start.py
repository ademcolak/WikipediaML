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
║         WikipediaML Quick Start                          ║
║                                                          ║
║  This will run the full training pipeline               ║
║  All scripts auto-skip if output already exists         ║
║  Estimated time: 30-50 hours (full Wikipedia)           ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # Activate venv
    venv_python = "source venv/bin/activate && python3"
    
    steps = [
        (
            f"{venv_python} scripts/download_wikipedia_dumps.py",
            "Step 1/5: Download Wikipedia dumps (auto-skips if exists)"
        ),
        (
            f"{venv_python} scripts/parse_wikipedia_dumps.py",
            "Step 2/5: Parse and clean Wikipedia data (auto-skips if exists)"
        ),
        (
            f"{venv_python} scripts/build_adjacency_map.py",
            "Step 3/5: Build graph adjacency matrix (auto-skips if exists)"
        ),
        (
            f"{venv_python} scripts/build_embedding_index.py",
            "Step 4/5: Generate embeddings and FAISS index (auto-skips if exists)"
        ),
        (
            f"{venv_python} scripts/generate_training_data.py",
            "Step 5/5: Generate training dataset (auto-skips if exists)"
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

Note: All scripts automatically skip if output already exists.
To start fresh, delete the output files or use clean_data.py
    """)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())