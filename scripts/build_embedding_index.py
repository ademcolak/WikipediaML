#!/usr/bin/env python3
"""
Embedding Index Builder
Generates embeddings for all Wikipedia pages using all-MiniLM-L6-v2
and builds a FAISS index for fast similarity search.
"""

import json
import pickle
import numpy as np
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from typing import Dict, List
import sys

class EmbeddingIndexBuilder:
    """Builds embedding index for Wikipedia pages."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the builder.
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        print(f"\n{'='*80}")
        print(f"Loading embedding model: {model_name}")
        print(f"{'='*80}")
        
        self.model = SentenceTransformer(model_name)
        embedding_dim = self.model.get_sentence_embedding_dimension()
        self.embedding_dim: int = embedding_dim if embedding_dim is not None else 384
        
        print(f"✓ Model loaded successfully")
        print(f"✓ Embedding dimension: {self.embedding_dim}")
        
        self.pages: Dict[int, str] = {}
        self.page_id_to_index: Dict[int, int] = {}
        self.index_to_page_id: Dict[int, int] = {}
        
    def load_pages(self, data_dir: Path) -> None:
        """
        Load page data.
        
        Args:
            data_dir: Directory containing cleaned data
        """
        print(f"\n{'='*80}")
        print("Loading page data...")
        print(f"{'='*80}")
        
        pages_file = data_dir / "pages.json"
        with open(pages_file, 'r', encoding='utf-8') as f:
            self.pages = {int(k): v for k, v in json.load(f).items()}
        
        print(f"✓ Loaded {len(self.pages):,} pages")
        
        # Create index mappings
        sorted_page_ids = sorted(self.pages.keys())
        self.page_id_to_index = {pid: idx for idx, pid in enumerate(sorted_page_ids)}
        self.index_to_page_id = {idx: pid for pid, idx in self.page_id_to_index.items()}
        
        print(f"✓ Created index mappings")
    
    def generate_embeddings(self, batch_size: int = 256) -> np.ndarray:
        """
        Generate embeddings for all pages.
        
        Args:
            batch_size: Batch size for encoding
            
        Returns:
            Array of embeddings with shape (n_pages, embedding_dim)
        """
        print(f"\n{'='*80}")
        print("Generating embeddings...")
        print(f"{'='*80}")
        
        n_pages = len(self.pages)
        embeddings = np.zeros((n_pages, self.embedding_dim), dtype=np.float32)  # type: ignore
        
        # Prepare titles in index order
        titles = [self.pages[self.index_to_page_id[i]] for i in range(n_pages)]
        
        # Generate embeddings in batches
        print(f"Processing {n_pages:,} pages in batches of {batch_size}...")
        
        for i in tqdm(range(0, n_pages, batch_size), desc="Encoding batches"):
            batch_titles = titles[i:i + batch_size]
            batch_embeddings = self.model.encode(
                batch_titles,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True  # L2 normalization for cosine similarity
            )
            embeddings[i:i + len(batch_embeddings)] = batch_embeddings
        
        print(f"✓ Generated embeddings for {n_pages:,} pages")
        print(f"✓ Embedding shape: {embeddings.shape}")
        print(f"✓ Memory usage: {embeddings.nbytes / (1024**2):.2f} MB")
        
        return embeddings
    
    def build_faiss_index(self, embeddings: np.ndarray, use_gpu: bool = False) -> faiss.Index:
        """
        Build FAISS index for fast similarity search.
        
        Args:
            embeddings: Array of embeddings
            use_gpu: Whether to use GPU acceleration (if available)
            
        Returns:
            FAISS index
        """
        print(f"\n{'='*80}")
        print("Building FAISS index...")
        print(f"{'='*80}")
        
        n_pages, dim = embeddings.shape
        
        # For large datasets, use IVF (Inverted File) index for faster search
        # For smaller datasets or exact search, use Flat index
        if n_pages > 1_000_000:
            # IVF index with 4096 clusters
            n_clusters = min(4096, n_pages // 39)
            quantizer = faiss.IndexFlatIP(dim)  # Inner Product for normalized vectors
            index = faiss.IndexIVFFlat(quantizer, dim, n_clusters, faiss.METRIC_INNER_PRODUCT)
            
            print(f"Using IVF index with {n_clusters} clusters")
            print("Training index...")
            index.train(embeddings)  # type: ignore
            print("✓ Training complete")
        else:
            # Flat index for exact search
            index = faiss.IndexFlatIP(dim)  # Inner Product = Cosine similarity for normalized vectors
            print("Using Flat index for exact search")
        
        # Add embeddings to index
        print("Adding embeddings to index...")
        index.add(embeddings)  # type: ignore
        
        print(f"✓ Index built successfully")
        print(f"✓ Total vectors in index: {index.ntotal:,}")
        
        # Move to GPU if requested and available
        if use_gpu and faiss.get_num_gpus() > 0:
            print("Moving index to GPU...")
            res = faiss.StandardGpuResources()  # type: ignore
            index = faiss.index_cpu_to_gpu(res, 0, index)  # type: ignore
            print("✓ Index moved to GPU")
        
        return index
    
    def test_index(self, index: faiss.Index, embeddings: np.ndarray, n_tests: int = 5) -> None:
        """
        Test the FAISS index with sample queries.
        
        Args:
            index: FAISS index
            embeddings: Array of embeddings
            n_tests: Number of test queries
        """
        print(f"\n{'='*80}")
        print("Testing FAISS index...")
        print(f"{'='*80}")
        
        # Select random pages for testing
        test_indices = np.random.choice(len(self.pages), n_tests, replace=False)
        
        for test_idx in test_indices:
            page_id = self.index_to_page_id[test_idx]
            title = self.pages[page_id]
            
            # Search for similar pages
            query_embedding = embeddings[test_idx:test_idx+1]
            distances, indices = index.search(query_embedding, k=6)  # type: ignore
            
            print(f"\nQuery: '{title}'")
            print("Top 5 similar pages:")
            for i, (dist, idx) in enumerate(zip(distances[0][1:], indices[0][1:]), 1):
                similar_page_id = self.index_to_page_id[idx]
                similar_title = self.pages[similar_page_id]
                print(f"  {i}. {similar_title} (similarity: {dist:.4f})")
    
    def save_index(self, index: faiss.Index, embeddings: np.ndarray, output_dir: Path) -> None:
        """
        Save FAISS index and embeddings.
        
        Args:
            index: FAISS index
            embeddings: Array of embeddings
            output_dir: Directory to save files
        """
        print(f"\n{'='*80}")
        print("Saving index and embeddings...")
        print(f"{'='*80}")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        index_file = output_dir / "faiss_index.bin"
        # Convert GPU index to CPU before saving
        if hasattr(index, 'index'):  # GPU index
            cpu_index = faiss.index_gpu_to_cpu(index)  # type: ignore
            faiss.write_index(cpu_index, str(index_file))
        else:
            faiss.write_index(index, str(index_file))
        print(f"✓ Saved FAISS index to {index_file}")
        
        # Save embeddings
        embeddings_file = output_dir / "embeddings.npy"
        np.save(embeddings_file, embeddings)
        print(f"✓ Saved embeddings to {embeddings_file}")
        
        # Save metadata
        metadata_file = output_dir / "embedding_metadata.pkl"
        metadata = {
            "model_name": self.model.get_sentence_embedding_dimension(),
            "embedding_dim": self.embedding_dim,
            "n_pages": len(self.pages),
            "page_id_to_index": self.page_id_to_index,
            "index_to_page_id": self.index_to_page_id
        }
        with open(metadata_file, 'wb') as f:
            pickle.dump(metadata, f)
        print(f"✓ Saved metadata to {metadata_file}")
        
        print(f"\n{'='*80}")
        print("Embedding Index Build Complete!")
        print(f"{'='*80}")

def main():
    """Main build function."""
    data_dir = Path("data/cleaned")
    output_dir = Path("data/embeddings")
    
    # Check if cleaned data exists
    if not data_dir.exists():
        print(f"✗ Error: {data_dir} not found!")
        print("Please run parse_wikipedia_dumps.py first.")
        return 1
    
    try:
        # Build index
        builder = EmbeddingIndexBuilder(model_name="all-MiniLM-L6-v2")
        builder.load_pages(data_dir)
        embeddings = builder.generate_embeddings(batch_size=256)
        index = builder.build_faiss_index(embeddings, use_gpu=False)
        builder.test_index(index, embeddings, n_tests=5)
        builder.save_index(index, embeddings, output_dir)
        
        print("\n✓ Embedding index built successfully!")
        print("\nPhase I Complete! Next steps:")
        print("1. Generate synthetic training dataset using BFS")
        print("2. Design and train MLP scorer model")
        print("3. Validate model on unseen page pairs")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Error during build: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())