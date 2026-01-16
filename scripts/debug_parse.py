#!/usr/bin/env python3
"""
Debug script to check SQL dump format and parse issues
"""

import gzip
import re
from pathlib import Path
import sys

def check_dump_format(filepath: Path, n_lines: int = 50):
    """Check the actual format of SQL dump."""
    print("=" * 80)
    print(f"Checking dump format: {filepath.name}")
    print("=" * 80)
    
    if not filepath.exists():
        print(f"✗ File not found: {filepath}")
        return
    
    # Check file size
    file_size = filepath.stat().st_size / (1024**3)  # GB
    print(f"File size: {file_size:.2f} GB")
    
    print(f"\nFirst {n_lines} lines of dump:")
    print("-" * 80)
    
    with gzip.open(filepath, 'rt', encoding='utf-8', errors='ignore') as f:
        for i, line in enumerate(f):
            if i >= n_lines:
                break
            # Show first 200 chars, but highlight INSERT statements
            line_preview = line[:200].rstrip()
            if 'INSERT' in line.upper():
                print(f"{i+1:3d}: >>> {line_preview}")
            else:
                print(f"{i+1:3d}: {line_preview}")
    
    print("\n" + "=" * 80)
    print("Testing regex patterns...")
    print("=" * 80)
    
    # Test current patterns
    insert_pattern = re.compile(r"INSERT INTO `pagelinks` VALUES \((.*?)\);", re.DOTALL)
    row_pattern = re.compile(r"\((\d+),(\d+),'([^']*)'")
    
    matches_found = 0
    rows_found = 0
    
    with gzip.open(filepath, 'rt', encoding='utf-8', errors='ignore') as f:
        buffer = ""
        for i, line in enumerate(f):
            buffer += line
            
            if buffer.count('INSERT INTO') > 1 or line.strip().endswith(';'):
                for match in insert_pattern.finditer(buffer):
                    matches_found += 1
                    values = match.group(1)
                    
                    for row_match in row_pattern.finditer(values):
                        rows_found += 1
                        if rows_found <= 5:  # Show first 5 rows
                            from_id = row_match.group(1)
                            namespace = row_match.group(2)
                            title = row_match.group(3)
                            print(f"  Row {rows_found}: from_id={from_id}, ns={namespace}, title={title[:50]}")
                
                buffer = ""
            
            if i >= 10000:  # Check first 10k lines
                break
    
    print(f"\n✓ Found {matches_found} INSERT statements")
    print(f"✓ Found {rows_found} rows in first 10k lines")
    
    if matches_found == 0:
        print("\n❌ CRITICAL: No INSERT statements found!")
        print("\nPossible issues:")
        print("  1. Table name might be different (not 'pagelinks')")
        print("  2. SQL format might be different")
        print("  3. File might be corrupted")
        print("\nPlease check the first few lines above to see the actual format.")
        print("Look for lines starting with 'INSERT INTO' or similar.")
        return False
    
    if rows_found == 0 and matches_found > 0:
        print("\n❌ CRITICAL: INSERT statements found but no rows parsed!")
        print("Row pattern might be wrong.")
        print("\nPlease check the INSERT statement format above.")
        print("The row pattern expects: (from_id, namespace, 'title')")
        return False
    
    if rows_found > 0:
        print(f"\n✅ SUCCESS: Found {rows_found} rows in sample!")
        print("Parse patterns appear to be working correctly.")
        print("If parse still fails, check:")
        print("  1. Full dump file is not corrupted")
        print("  2. Page IDs match between page and pagelinks dumps")
        return True
    
    return False

def main():
    """Main debug function."""
    data_dir = Path("data/wikipedia_dumps")
    
    links_dump = data_dir / "enwiki-latest-pagelinks.sql.gz"
    
    if not links_dump.exists():
        print(f"✗ Error: {links_dump} not found!")
        print("Please run download_wikipedia_dumps.py first.")
        return 1
    
    check_dump_format(links_dump, n_lines=100)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
