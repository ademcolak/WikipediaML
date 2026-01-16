#!/usr/bin/env python3
"""
Wikipedia SQL Dump Parser and Cleaner
Parses Wikipedia SQL dumps and extracts clean page and link data.
Filters out non-article pages (Talk, Category, etc.) and redlinks.
"""

import gzip
import re
import json
from pathlib import Path
from typing import Dict, Set, Tuple
from tqdm import tqdm
import sys

# Wikipedia namespace IDs
# 0 = Main/Article namespace (what we want)
# Other namespaces: 1=Talk, 2=User, 3=User talk, 4=Wikipedia, etc.
MAIN_NAMESPACE = 0

class WikipediaParser:
    """Parser for Wikipedia SQL dumps."""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.pages: Dict[int, str] = {}  # page_id -> title
        self.valid_page_ids: Set[int] = set()
        self.links: Dict[int, Set[int]] = {}  # from_id -> set of to_ids
        
    def parse_page_dump(self, filepath: Path) -> None:
        """
        Parse the page SQL dump to extract valid article pages.
        
        Args:
            filepath: Path to enwiki-latest-page.sql.gz
        """
        print(f"\n{'='*80}")
        print("Parsing page dump...")
        print(f"{'='*80}")
        
        # Pattern to match INSERT statements
        insert_pattern = re.compile(r"INSERT INTO `page` VALUES \((.*?)\);", re.DOTALL)
        # Pattern to match individual rows
        row_pattern = re.compile(r"\((\d+),(\d+),'([^']*)'")
        
        total_pages = 0
        valid_pages = 0
        
        with gzip.open(filepath, 'rt', encoding='utf-8', errors='ignore') as f:
            buffer = ""
            
            for line in tqdm(f, desc="Reading page dump", unit=" lines"):
                buffer += line
                
                # Process complete INSERT statements
                if buffer.count('INSERT INTO') > 1 or line.strip().endswith(';'):
                    for match in insert_pattern.finditer(buffer):
                        values = match.group(1)
                        
                        # Parse each row in the INSERT statement
                        for row_match in row_pattern.finditer(values):
                            page_id = int(row_match.group(1))
                            namespace = int(row_match.group(2))
                            title = row_match.group(3)
                            
                            total_pages += 1
                            
                            # Only keep main namespace (articles)
                            if namespace == MAIN_NAMESPACE:
                                # Decode title (replace underscores with spaces)
                                clean_title = title.replace('_', ' ')
                                self.pages[page_id] = clean_title
                                self.valid_page_ids.add(page_id)
                                valid_pages += 1
                    
                    buffer = ""
        
        print(f"\n✓ Parsed {total_pages:,} total pages")
        print(f"✓ Kept {valid_pages:,} article pages (namespace 0)")
        print(f"✗ Filtered {total_pages - valid_pages:,} non-article pages")
    
    def parse_pagelinks_dump(self, filepath: Path) -> None:
        """
        Parse the pagelinks SQL dump to extract valid links.
        
        Args:
            filepath: Path to enwiki-latest-pagelinks.sql.gz
        """
        print(f"\n{'='*80}")
        print("Parsing pagelinks dump...")
        print(f"{'='*80}")
        
        # Try multiple patterns (Wikipedia dump format may vary)
        patterns_to_try = [
            (re.compile(r"INSERT INTO `pagelinks` VALUES \((.*?)\);", re.DOTALL), "pagelinks"),
            (re.compile(r"INSERT INTO `pagelinks`\s+VALUES\s+\((.*?)\);", re.DOTALL), "pagelinks with spaces"),
            (re.compile(r"INSERT INTO pagelinks VALUES \((.*?)\);", re.DOTALL), "pagelinks no backticks"),
        ]
        
        # Pattern to match individual rows: (from_id, namespace, title)
        # Try multiple row patterns
        row_patterns = [
            re.compile(r"\((\d+),(\d+),'([^']*)'"),  # Standard: (id, ns, 'title')
            re.compile(r"\((\d+),(\d+),\"([^\"]*)\""),  # Double quotes: (id, ns, "title")
            re.compile(r"\((\d+),(\d+),([^,)]+)\)"),  # No quotes: (id, ns, title)
        ]
        
        total_links = 0
        valid_links = 0
        redlinks = 0
        insert_statements_found = 0
        rows_parsed = 0
        
        # Build reverse lookup: title -> page_id
        title_to_id = {title: pid for pid, title in self.pages.items()}
        print(f"✓ Built title lookup for {len(title_to_id):,} pages")
        
        # First, try to detect the correct pattern
        print("\nDetecting SQL dump format...")
        detected_insert_pattern = None
        detected_row_pattern = None
        
        with gzip.open(filepath, 'rt', encoding='utf-8', errors='ignore') as f:
            sample_buffer = ""
            for i, line in enumerate(f):
                sample_buffer += line
                if i >= 1000:  # Check first 1000 lines
                    break
            
            # Try insert patterns
            for insert_pattern, pattern_name in patterns_to_try:
                matches = list(insert_pattern.finditer(sample_buffer))
                if matches:
                    detected_insert_pattern = insert_pattern
                    print(f"✓ Detected INSERT pattern: {pattern_name}")
                    break
            
            if detected_insert_pattern:
                # Try row patterns on first match
                first_match = list(detected_insert_pattern.finditer(sample_buffer))[0]
                values = first_match.group(1)
                
                for row_pattern in row_patterns:
                    matches = list(row_pattern.finditer(values))
                    if matches and len(matches) > 0:
                        detected_row_pattern = row_pattern
                        print(f"✓ Detected row pattern: {len(matches)} rows found in sample")
                        break
        
        if not detected_insert_pattern or not detected_row_pattern:
            print("\n⚠️  WARNING: Could not detect SQL format automatically!")
            print("Trying default patterns...")
            detected_insert_pattern = patterns_to_try[0][0]
            detected_row_pattern = row_patterns[0]
        
        # Now parse the full file
        print(f"\nParsing full dump file...")
        with gzip.open(filepath, 'rt', encoding='utf-8', errors='ignore') as f:
            buffer = ""
            
            for line in tqdm(f, desc="Reading pagelinks dump", unit=" lines"):
                buffer += line
                
                # Process complete INSERT statements
                if buffer.count('INSERT INTO') > 1 or line.strip().endswith(';'):
                    for match in detected_insert_pattern.finditer(buffer):
                        insert_statements_found += 1
                        values = match.group(1)
                        
                        # Parse each row in the INSERT statement
                        for row_match in detected_row_pattern.finditer(values):
                            try:
                                from_id = int(row_match.group(1))
                                to_namespace = int(row_match.group(2))
                                to_title = row_match.group(3).strip().strip("'\"")
                                
                                # Clean title
                                to_title = to_title.replace('_', ' ')
                                
                                rows_parsed += 1
                                total_links += 1
                                
                                # Only process if source page is valid
                                if from_id not in self.valid_page_ids:
                                    continue
                                
                                # Only keep links to main namespace
                                if to_namespace != MAIN_NAMESPACE:
                                    continue
                                
                                # Check if target page exists
                                to_id = title_to_id.get(to_title)
                                if to_id is None:
                                    redlinks += 1
                                    continue
                                
                                # Add valid link
                                if from_id not in self.links:
                                    self.links[from_id] = set()
                                self.links[from_id].add(to_id)
                                valid_links += 1
                            except (ValueError, IndexError) as e:
                                # Skip malformed rows
                                continue
                    
                    buffer = ""
        
        print(f"\n✓ Found {insert_statements_found:,} INSERT statements")
        print(f"✓ Parsed {rows_parsed:,} total rows")
        print(f"✓ Kept {valid_links:,} valid article-to-article links")
        print(f"✗ Filtered {redlinks:,} redlinks (non-existent pages)")
        print(f"✗ Filtered {total_links - valid_links - redlinks:,} non-article/invalid links")
        
        # Validation
        if valid_links == 0:
            print("\n⚠️  CRITICAL WARNING: No valid links parsed!")
            print("Possible issues:")
            print("  1. SQL dump format is different than expected")
            print("  2. All links are being filtered out")
            print("  3. Page IDs don't match between page and pagelinks dumps")
            print("\nPlease check:")
            print("  - Run debug_parse.py to inspect dump format")
            print("  - Verify pages.json and links.json are from same dump")
            raise ValueError("No valid links parsed from dump file!")
        
        if valid_links < 1000:
            print(f"\n⚠️  WARNING: Very few links parsed ({valid_links:,})")
            print("This is unusually low for Wikipedia. Please verify dump files.")
    
    def save_cleaned_data(self, output_dir: Path) -> None:
        """
        Save cleaned data to JSON files.
        
        Args:
            output_dir: Directory to save cleaned data
        """
        print(f"\n{'='*80}")
        print("Saving cleaned data...")
        print(f"{'='*80}")
        
        # Validation before saving
        if len(self.pages) == 0:
            raise ValueError("No pages to save! Parse may have failed.")
        
        if len(self.links) == 0:
            raise ValueError("No links to save! This will cause graph build to fail.")
        
        total_links = sum(len(to_ids) for to_ids in self.links.values())
        if total_links == 0:
            raise ValueError("Total links count is 0! Parse may have failed.")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save pages
        pages_file = output_dir / "pages.json"
        with open(pages_file, 'w', encoding='utf-8') as f:
            json.dump(self.pages, f, ensure_ascii=False, indent=2)
        print(f"✓ Saved {len(self.pages):,} pages to {pages_file}")
        
        # Verify file was written
        if not pages_file.exists() or pages_file.stat().st_size == 0:
            raise IOError(f"Failed to write {pages_file}")
        
        # Save links (convert sets to lists for JSON)
        links_file = output_dir / "links.json"
        links_serializable = {
            str(from_id): list(to_ids) 
            for from_id, to_ids in self.links.items()
        }
        with open(links_file, 'w', encoding='utf-8') as f:
            json.dump(links_serializable, f, indent=2)
        print(f"✓ Saved {len(self.links):,} link entries to {links_file}")
        
        # Verify file was written and has content
        if not links_file.exists():
            raise IOError(f"Failed to write {links_file}")
        
        file_size = links_file.stat().st_size
        if file_size < 1000:  # Less than 1KB is suspicious
            print(f"⚠️  WARNING: links.json is very small ({file_size} bytes)")
            print("This may indicate parsing issues.")
        else:
            print(f"✓ Links file size: {file_size / (1024*1024):.2f} MB")
        
        # Save statistics
        stats_file = output_dir / "statistics.json"
        avg_links = total_links / len(self.links) if self.links else 0
        
        stats = {
            "total_pages": len(self.pages),
            "total_link_entries": len(self.links),
            "total_links": total_links,
            "average_links_per_page": round(avg_links, 2),
            "links_file_size_bytes": file_size
        }
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
        print(f"✓ Saved statistics to {stats_file}")
        
        print(f"\n{'='*80}")
        print("Data Cleaning Summary:")
        print(f"{'='*80}")
        print(f"Total articles: {stats['total_pages']:,}")
        print(f"Total links: {stats['total_links']:,}")
        print(f"Average links per page: {stats['average_links_per_page']:.2f}")
        
        # Final validation
        if stats['total_links'] < 1000:
            raise ValueError(f"Too few links parsed ({stats['total_links']:,}). Parse likely failed!")

def main():
    """Main parsing function."""
    data_dir = Path("data/wikipedia_dumps")
    output_dir = Path("data/cleaned")
    
    # Check if output already exists (auto-skip)
    pages_file = output_dir / "pages.json"
    links_file = output_dir / "links.json"
    if pages_file.exists() and links_file.exists():
        print(f"⊘ Parsed data already exists in {output_dir}")
        print("  Skipping parse step. Delete output files to re-run.")
        return 0
    
    # Check if dump files exist
    page_dump = data_dir / "enwiki-latest-page.sql.gz"
    links_dump = data_dir / "enwiki-latest-pagelinks.sql.gz"
    
    if not page_dump.exists():
        print(f"✗ Error: {page_dump} not found!")
        print("Please run download_wikipedia_dumps.py first.")
        return 1
    
    if not links_dump.exists():
        print(f"✗ Error: {links_dump} not found!")
        print("Please run download_wikipedia_dumps.py first.")
        return 1
    
    # Parse dumps
    parser = WikipediaParser(data_dir)
    
    try:
        parser.parse_page_dump(page_dump)
        parser.parse_pagelinks_dump(links_dump)
        parser.save_cleaned_data(output_dir)
        
        print("\n✓ Data cleaning completed successfully!")
        print("\nNext steps:")
        print("1. Build binary adjacency map (CSR format)")
        print("2. Generate embeddings for all pages")
        print("3. Create FAISS index")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Error during parsing: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())