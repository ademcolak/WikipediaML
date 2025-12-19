#!/usr/bin/env python3
"""
Analyze external Wikipedia speedrun repositories and extract useful components.

This script helps identify useful patterns, datasets, and code from:
- WikiSpeedrun by B0und
- Wikipedia Speedruns (official)
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any


class RepoAnalyzer:
    """Analyze external repositories for useful components."""
    
    def __init__(self, external_dir: str = "external"):
        self.external_dir = Path(external_dir)
        self.external_dir.mkdir(exist_ok=True)
        
        self.repos = {
            "wikispeedrun": {
                "url": "https://github.com/B0und/WikiSpeedrun.git",
                "path": self.external_dir / "WikiSpeedrun",
                "description": "WikiSpeedrun game implementation"
            },
            "wikipedia-speedruns": {
                "url": "https://github.com/wikispeedruns/wikipedia-speedruns.git",
                "path": self.external_dir / "wikipedia-speedruns",
                "description": "Official Wikipedia speedruns platform"
            }
        }
    
    def clone_repos(self):
        """Clone the repositories if not already present."""
        print("=" * 60)
        print("CLONING REPOSITORIES")
        print("=" * 60)
        
        for name, info in self.repos.items():
            if info["path"].exists():
                print(f"\n✓ {name} already cloned at {info['path']}")
            else:
                print(f"\n→ Cloning {name}...")
                try:
                    subprocess.run(
                        ["git", "clone", info["url"], str(info["path"])],
                        check=True,
                        capture_output=True
                    )
                    print(f"✓ Successfully cloned {name}")
                except subprocess.CalledProcessError as e:
                    print(f"✗ Failed to clone {name}: {e}")
    
    def analyze_structure(self, repo_name: str) -> Dict[str, Any]:
        """Analyze the structure of a repository."""
        repo_path = self.repos[repo_name]["path"]
        
        if not repo_path.exists():
            return {"error": "Repository not found"}
        
        analysis = {
            "name": repo_name,
            "path": str(repo_path),
            "files": [],
            "directories": [],
            "languages": {},
            "key_files": []
        }
        
        # Walk through the repository
        for root, dirs, files in os.walk(repo_path):
            # Skip .git directory
            if ".git" in root:
                continue
            
            rel_root = Path(root).relative_to(repo_path)
            
            for file in files:
                file_path = Path(root) / file
                rel_path = file_path.relative_to(repo_path)
                
                # Track file extensions
                ext = file_path.suffix
                if ext:
                    analysis["languages"][ext] = analysis["languages"].get(ext, 0) + 1
                
                analysis["files"].append(str(rel_path))
                
                # Identify key files
                if file.lower() in ["readme.md", "package.json", "requirements.txt", 
                                   "setup.py", "config.json", "docker-compose.yml"]:
                    analysis["key_files"].append(str(rel_path))
        
        return analysis
    
    def find_datasets(self, repo_name: str) -> List[str]:
        """Find potential dataset files in the repository."""
        repo_path = self.repos[repo_name]["path"]
        datasets = []
        
        if not repo_path.exists():
            return datasets
        
        # Look for common dataset file patterns
        patterns = ["*.json", "*.csv", "*.txt", "*dataset*", "*challenges*", "*puzzles*"]
        
        for pattern in patterns:
            for file_path in repo_path.rglob(pattern):
                if ".git" not in str(file_path):
                    rel_path = file_path.relative_to(repo_path)
                    datasets.append(str(rel_path))
        
        return datasets
    
    def find_api_code(self, repo_name: str) -> List[str]:
        """Find files that likely contain Wikipedia API usage."""
        repo_path = self.repos[repo_name]["path"]
        api_files = []
        
        if not repo_path.exists():
            return api_files
        
        # Search for files containing Wikipedia API patterns
        search_terms = ["wikipedia", "api", "fetch", "scrape", "request"]
        
        for file_path in repo_path.rglob("*.py"):
            if ".git" in str(file_path):
                continue
            
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                if any(term in content.lower() for term in search_terms):
                    rel_path = file_path.relative_to(repo_path)
                    api_files.append(str(rel_path))
            except Exception:
                pass
        
        # Also check JavaScript/TypeScript files
        for ext in ["*.js", "*.ts", "*.jsx", "*.tsx"]:
            for file_path in repo_path.rglob(ext):
                if ".git" in str(file_path):
                    continue
                
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    if any(term in content.lower() for term in search_terms):
                        rel_path = file_path.relative_to(repo_path)
                        api_files.append(str(rel_path))
                except Exception:
                    pass
        
        return api_files
    
    def generate_report(self) -> str:
        """Generate a comprehensive analysis report."""
        report = []
        report.append("=" * 80)
        report.append("EXTERNAL REPOSITORY ANALYSIS REPORT")
        report.append("=" * 80)
        report.append("")
        
        for repo_name in self.repos.keys():
            report.append(f"\n{'=' * 80}")
            report.append(f"Repository: {repo_name}")
            report.append(f"Description: {self.repos[repo_name]['description']}")
            report.append(f"{'=' * 80}\n")
            
            # Structure analysis
            structure = self.analyze_structure(repo_name)
            
            if "error" in structure:
                report.append(f"⚠️  {structure['error']}")
                report.append("   Run with --clone flag to clone repositories first.\n")
                continue
            
            report.append(f"📁 Total Files: {len(structure['files'])}")
            report.append(f"📂 Path: {structure['path']}\n")
            
            # Languages
            report.append("🔤 Languages/File Types:")
            for ext, count in sorted(structure["languages"].items(), 
                                    key=lambda x: x[1], reverse=True)[:10]:
                report.append(f"   {ext}: {count} files")
            report.append("")
            
            # Key files
            if structure["key_files"]:
                report.append("🔑 Key Configuration Files:")
                for file in structure["key_files"]:
                    report.append(f"   - {file}")
                report.append("")
            
            # Datasets
            datasets = self.find_datasets(repo_name)
            if datasets:
                report.append("📊 Potential Dataset Files:")
                for dataset in datasets[:20]:  # Limit to first 20
                    report.append(f"   - {dataset}")
                if len(datasets) > 20:
                    report.append(f"   ... and {len(datasets) - 20} more")
                report.append("")
            
            # API code
            api_files = self.find_api_code(repo_name)
            if api_files:
                report.append("🌐 Files with Wikipedia API Usage:")
                for file in api_files[:15]:  # Limit to first 15
                    report.append(f"   - {file}")
                if len(api_files) > 15:
                    report.append(f"   ... and {len(api_files) - 15} more")
                report.append("")
        
        report.append("\n" + "=" * 80)
        report.append("RECOMMENDATIONS")
        report.append("=" * 80)
        report.append("")
        report.append("1. Review dataset files for potential benchmark challenges")
        report.append("2. Study API usage patterns in identified files")
        report.append("3. Check README files for architecture documentation")
        report.append("4. Look for validation logic in game/path verification code")
        report.append("5. Extract any difficulty classification systems")
        report.append("6. Review caching and optimization strategies")
        report.append("")
        
        return "\n".join(report)
    
    def save_report(self, filename: str = "external_repos_report.txt"):
        """Save the analysis report to a file."""
        report = self.generate_report()
        
        output_path = Path(filename)
        output_path.write_text(report, encoding="utf-8")
        
        print(f"\n✓ Report saved to: {output_path.absolute()}")
        return output_path


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Analyze external Wikipedia speedrun repositories"
    )
    parser.add_argument(
        "--clone",
        action="store_true",
        help="Clone repositories before analysis"
    )
    parser.add_argument(
        "--output",
        default="external_repos_report.txt",
        help="Output file for the report"
    )
    
    args = parser.parse_args()
    
    analyzer = RepoAnalyzer()
    
    if args.clone:
        analyzer.clone_repos()
        print()
    
    print("\n" + "=" * 60)
    print("ANALYZING REPOSITORIES")
    print("=" * 60)
    
    report = analyzer.generate_report()
    print(report)
    
    analyzer.save_report(args.output)
    
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("\n1. Review the generated report")
    print("2. Explore identified dataset files")
    print("3. Study API usage patterns")
    print("4. Extract useful validation logic")
    print("5. Consider integration opportunities")
    print("\nFor detailed integration guide, see: docs/EXTERNAL_REPOS_ANALYSIS.md")


if __name__ == "__main__":
    main()