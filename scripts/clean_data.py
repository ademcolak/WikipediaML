#!/usr/bin/env python3
"""
Data Cleanup Script
Removes processed data files to start fresh training pipeline.
"""

import sys
from pathlib import Path
from typing import List

def get_data_directories() -> List[Path]:
    """Get list of data directories to clean."""
    base_dir = Path("data")
    
    directories = [
        base_dir / "cleaned",      # Parsed Wikipedia data
        base_dir / "graph",         # Adjacency maps
        base_dir / "embeddings",    # Embeddings and FAISS index
        base_dir / "training",      # Training datasets
    ]
    
    return directories

def get_model_files() -> List[Path]:
    """Get list of model files to clean."""
    model_dir = Path("models/checkpoints")
    
    files = [
        model_dir / "last_checkpoint.pt",
        model_dir / "mlp_scorer_best.pt",
        model_dir / "mlp_scorer_final.pt",
        model_dir / "training_history.json",
    ]
    
    return files

def clean_directories(directories: List[Path], keep_dumps: bool = True) -> int:
    """
    Clean data directories.
    
    Args:
        directories: List of directories to clean
        keep_dumps: Whether to keep Wikipedia dump files
        
    Returns:
        Number of files/directories removed
    """
    removed_count = 0
    
    for directory in directories:
        if not directory.exists():
            continue
        
        # Count files before removal
        files_before = sum(1 for _ in directory.rglob("*") if _.is_file())
        
        # Remove directory contents
        for item in directory.iterdir():
            if item.is_file():
                item.unlink()
                removed_count += 1
            elif item.is_dir():
                import shutil
                shutil.rmtree(item)
                removed_count += 1
        
        # Remove empty directory
        try:
            directory.rmdir()
        except OSError:
            pass
    
    return removed_count

def clean_model_files(files: List[Path]) -> int:
    """
    Clean model checkpoint files.
    
    Args:
        files: List of files to remove
        
    Returns:
        Number of files removed
    """
    removed_count = 0
    
    for file_path in files:
        if file_path.exists():
            file_path.unlink()
            removed_count += 1
    
    return removed_count

def main():
    """Main cleanup function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Clean processed data files to start fresh',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Clean all processed data (keep Wikipedia dumps)
  python3 scripts/clean_data.py
  
  # Clean everything including Wikipedia dumps
  python3 scripts/clean_data.py --include-dumps
  
  # Clean only training data
  python3 scripts/clean_data.py --only-training
        """
    )
    parser.add_argument('--include-dumps', action='store_true',
                       help='Also remove Wikipedia dump files')
    parser.add_argument('--only-training', action='store_true',
                       help='Only clean training data and models')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be removed without actually removing')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("WikipediaML Data Cleanup")
    print("=" * 80)
    
    if args.dry_run:
        print("\n⚠️  DRY RUN MODE - No files will be deleted")
    
    # Get items to clean
    if args.only_training:
        directories = [Path("data/training")]
        model_files = get_model_files()
    else:
        directories = get_data_directories()
        model_files = get_model_files()
    
    # Show what will be removed
    print("\n📋 Items to be removed:")
    print("\nDirectories:")
    for directory in directories:
        if directory.exists():
            file_count = sum(1 for _ in directory.rglob("*") if _.is_file())
            print(f"  - {directory}/ ({file_count} files)")
        else:
            print(f"  - {directory}/ (does not exist)")
    
    print("\nModel files:")
    for file_path in model_files:
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"  - {file_path} ({size_mb:.2f} MB)")
        else:
            print(f"  - {file_path} (does not exist)")
    
    if args.include_dumps:
        dump_dir = Path("data/wikipedia_dumps")
        if dump_dir.exists():
            dump_files = list(dump_dir.glob("*.sql.gz"))
            print(f"\nWikipedia dumps ({len(dump_files)} files):")
            for dump_file in dump_files:
                size_mb = dump_file.stat().st_size / (1024 * 1024)
                print(f"  - {dump_file.name} ({size_mb:.2f} MB)")
    
    # Confirm
    if not args.dry_run:
        print("\n" + "=" * 80)
        response = input("⚠️  Are you sure you want to delete these files? (yes/no): ").lower()
        if response != 'yes':
            print("❌ Cleanup cancelled.")
            return 0
    
    # Clean
    print("\n🧹 Cleaning...")
    
    removed_dirs = clean_directories(directories, keep_dumps=not args.include_dumps)
    removed_models = clean_model_files(model_files)
    
    if args.include_dumps:
        dump_dir = Path("data/wikipedia_dumps")
        if dump_dir.exists():
            import shutil
            for dump_file in dump_dir.glob("*.sql.gz"):
                dump_file.unlink()
                removed_dirs += 1
    
    total_removed = removed_dirs + removed_models
    
    print(f"\n✅ Cleanup complete!")
    print(f"   Removed: {total_removed} files/directories")
    
    if args.dry_run:
        print("\n⚠️  This was a dry run. No files were actually deleted.")
    else:
        print("\n📝 Next steps:")
        print("   1. python3 scripts/download_wikipedia_dumps.py")
        print("   2. python3 scripts/parse_wikipedia_dumps.py")
        print("   3. python3 scripts/build_adjacency_map.py")
        print("   4. python3 scripts/build_embedding_index.py")
        print("   5. python3 scripts/generate_training_data.py")
        print("   6. python3 scripts/train_mlp_scorer.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
