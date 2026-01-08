#!/usr/bin/env python3
"""
Wikipedia Data Dumps Downloader
Downloads the necessary Wikipedia SQL dumps for building the knowledge graph.
"""

import os
import sys
import requests
from pathlib import Path
from tqdm import tqdm

# Wikipedia dump URLs
DUMP_BASE_URL = "https://dumps.wikimedia.org/enwiki/latest/"
REQUIRED_FILES = [
    "enwiki-latest-pagelinks.sql.gz",
    "enwiki-latest-page.sql.gz"
]

def download_file(url: str, destination: Path) -> bool:
    """
    Download a file with progress bar.
    
    Args:
        url: URL to download from
        destination: Local path to save the file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        print(f"\nDownloading: {url}")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(destination, 'wb') as f, tqdm(
            desc=destination.name,
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                size = f.write(chunk)
                pbar.update(size)
        
        print(f"✓ Successfully downloaded: {destination.name}")
        return True
        
    except Exception as e:
        print(f"✗ Error downloading {url}: {e}")
        return False

def main():
    """Main download function."""
    # Create data directory if it doesn't exist
    data_dir = Path("data/wikipedia_dumps")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 80)
    print("Wikipedia Data Dumps Downloader")
    print("=" * 80)
    print(f"\nDownload directory: {data_dir.absolute()}")
    print(f"Files to download: {len(REQUIRED_FILES)}")
    
    # Check existing files
    existing_files = []
    for filename in REQUIRED_FILES:
        filepath = data_dir / filename
        if filepath.exists():
            size_mb = filepath.stat().st_size / (1024 * 1024)
            existing_files.append(filename)
            print(f"\n⚠ File already exists: {filename} ({size_mb:.2f} MB)")
    
    if existing_files:
        response = input("\nSkip existing files? (y/n): ").lower()
        skip_existing = response == 'y'
    else:
        skip_existing = False
    
    # Download files
    success_count = 0
    for filename in REQUIRED_FILES:
        filepath = data_dir / filename
        
        if skip_existing and filepath.exists():
            print(f"\n⊘ Skipping: {filename}")
            success_count += 1
            continue
        
        url = DUMP_BASE_URL + filename
        if download_file(url, filepath):
            success_count += 1
    
    # Summary
    print("\n" + "=" * 80)
    print(f"Download Summary: {success_count}/{len(REQUIRED_FILES)} files successful")
    print("=" * 80)
    
    if success_count == len(REQUIRED_FILES):
        print("\n✓ All files downloaded successfully!")
        print(f"\nNext steps:")
        print("1. Extract and parse the SQL dumps")
        print("2. Clean and normalize the data")
        print("3. Build the binary adjacency map")
        return 0
    else:
        print("\n✗ Some downloads failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())