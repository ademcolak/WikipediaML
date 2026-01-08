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
        
        # Pattern to match INSERT statements
        insert_pattern = re.compile(r"INSERT INTO `pagelinks` VALUES \((.*?)\);", re.DOTALL)
        # Pattern to match individual rows: (from_id, namespace, title)
        row_pattern = re.compile(r"\((\d+),(\d+),'([^']*)'")
        
        total_links = 0
        valid_links = 0
        redlinks = 0
        
        # Build reverse lookup: title -> page_id
        title_to_id = {title: pid for pid, title in self.pages.items()}
        
        with gzip.open(filepath, 'rt', encoding='utf-8', errors='ignore') as f:
            buffer = ""
            
            for line in tqdm(f, desc="Reading pagelinks dump", unit=" lines"):
                buffer += line
                
                # Process complete INSERT statements
                if buffer.count('INSERT INTO') > 1 or line.strip().endswith(';'):
                    for match in insert_pattern.finditer(buffer):
                        values = match.group(1)
                        
                        # Parse each row in the INSERT statement
                        for row_match in row_pattern.finditer(values):
                            from_id = int(row_match.group(1))
                            to_namespace = int(row_match.group(2))
                            to_title = row_match.group(3).replace('_', ' ')
                            
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
                    
                    buffer = ""
        
        print(f"\n✓ Parsed {total_links:,} total links")
        print(f"✓ Kept {valid_links:,} valid article-to-article links")
        print(f"✗ Filtered {redlinks:,} redlinks (non-existent pages)")
        print(f"✗ Filtered {total_links - valid_links - redlinks:,} non-article links")
    
    def save_cleaned_data(self, output_dir: Path) -> None:
        """
        Save cleaned data to JSON files.
        
        Args:
            output_dir: Directory to save cleaned data
        """
        print(f"\n{'='*80}")
        print("Saving cleaned data...")
        print(f"{'='*80}")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save pages
        pages_file = output_dir / "pages.json"
        with open(pages_file, 'w', encoding='utf-8') as f:
            json.dump(self.pages, f, ensure_ascii=False, indent=2)
        print(f"✓ Saved {len(self.pages):,} pages to {pages_file}")
        
        # Save links (convert sets to lists for JSON)
        links_file = output_dir / "links.json"
        links_serializable = {
            str(from_id): list(to_ids) 
            for from_id, to_ids in self.links.items()
        }
        with open(links_file, 'w', encoding='utf-8') as f:
            json.dump(links_serializable, f, indent=2)
        print(f"✓ Saved {len(self.links):,} link entries to {links_file}")
        
        # Save statistics
        stats_file = output_dir / "statistics.json"
        total_links = sum(len(to_ids) for to_ids in self.links.values())
        avg_links = total_links / len(self.links) if self.links else 0
        
        stats = {
            "total_pages": len(self.pages),
            "total_link_entries": len(self.links),
            "total_links": total_links,
            "average_links_per_page": round(avg_links, 2)
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

def main():
    """Main parsing function."""
    data_dir = Path("data/wikipedia_dumps")
    output_dir = Path("data/cleaned")
    
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