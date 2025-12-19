"""
embedder.py
-----------
Wikipedia sayfaları için semantic embedding'ler.

Sentence Transformers kullanarak:
- Text → Vector (embedding) dönüşümü
- Semantic similarity hesaplama
- Embedding cache (performance)
"""

import numpy as np
from typing import Union
from sentence_transformers import SentenceTransformer


class WikiEmbedder:
    """
    Wikipedia sayfaları için semantic embedding sınıfı.

    Features:
    - Text to vector conversion (embedding)
    - Cosine similarity hesaplama
    - Embedding cache (aynı text'i tekrar hesaplama)
    - Batch processing (çok text'i birden)

    Model: paraphrase-MiniLM-L6-v2 (UPDATED from benchmark results)
    - Boyut: 384 dimensions
    - Hız: ~0.6ms per text (5.9x faster than all-MiniLM-L6-v2)
    - Throughput: 1669 texts/sec
    - Size: ~80MB
    - Best balance: speed + semantic quality
    """

    def __init__(self, model_name: str = 'paraphrase-MiniLM-L6-v2', cache_size: int = 10000, cache_file: str = 'cache/embeddings_cache.pkl'):
        """
        WikiEmbedder'ı başlat ve model yükle.

        Parametreler:
            model_name (str): Sentence transformer model ismi
                             Default: 'paraphrase-MiniLM-L6-v2' (UPDATED: 5.9x faster)
            cache_size (int): Cache'lenecek maksimum embedding sayısı
                             Default: 10000 (UPDATED: 5x increase for better hit rate)
            cache_file (str): Persistent cache dosyası
                             Default: 'cache/embeddings_cache.pkl'
        """
        print(f"🤖 Loading embedding model: {model_name}...")
        print(f"   (İlk seferinde ~80MB indirilecek, sonra cache'den yüklenir)")

        # Model yükle
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name

        print(f"✅ Model loaded! Embedding dimension: {self.model.get_sentence_embedding_dimension()}")

        # Embedding cache (LRU)
        from collections import OrderedDict
        self._cache_size = cache_size
        self._cache_file = cache_file

        # Statistics
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_embeddings_computed = 0
        
        # Load persistent cache from disk
        self._load_cache_from_disk()

    def get_embedding(self, text: str) -> np.ndarray:
        """
        Tek bir text'in embedding'ini al.

        Parametreler:
            text (str): Embedding'e çevrilecek text (örn: "Pizza", "Italy")

        Dönüş:
            np.ndarray: Embedding vector (384 boyutlu)

        Örnek:
            >>> embedder = WikiEmbedder()
            >>> pizza_emb = embedder.get_embedding("Pizza")
            >>> pizza_emb.shape
            (384,)
        """
        # Cache'de var mı?
        if text in self._embedding_cache:
            self.cache_hits += 1
            # Recently used yap
            self._embedding_cache.move_to_end(text)
            return self._embedding_cache[text]

        # Cache miss: Hesapla
        self.cache_misses += 1
        self.total_embeddings_computed += 1

        embedding = self.model.encode(
            text,
            convert_to_tensor=False,  # NumPy array döndür
            show_progress_bar=False    # Progress bar gösterme
        )

        # Ensure it's a numpy array (convert if needed)
        if not isinstance(embedding, np.ndarray):
            embedding = np.array(embedding)

        # Cache'e ekle
        self._add_to_cache(text, embedding)

        return embedding

    def get_embeddings_batch(self, texts: list[str], verbose: bool = False) -> np.ndarray:
        """
        Birden fazla text'in embedding'lerini al (batch - daha hızlı!).

        Parametreler:
            texts (list[str]): Embedding'e çevrilecek text'ler
            verbose (bool): Progress göster

        Dönüş:
            np.ndarray: Embeddings (n×384 matrix)

        Örnek:
            >>> texts = ["Pizza", "Italy", "Computer"]
            >>> embeddings = embedder.get_embeddings_batch(texts)
            >>> embeddings.shape
            (3, 384)

        Not:
            - Batch processing tek tek yapmaktan 2-3x daha hızlı
            - Cache'lenmiş olanları skip eder (mixed approach)
        """
        # Boş liste kontrolü
        if not texts:
            return np.array([])

        # Her text için embedding al (cache'den veya hesapla)
        embeddings = []
        uncached_texts = []
        uncached_indices = []

        # İlk geçiş: cache'de olanları topla, olmayanları not et
        for i, text in enumerate(texts):
            if text in self._embedding_cache:
                self.cache_hits += 1
                self._embedding_cache.move_to_end(text)  # Recently used
                embeddings.append(None)  # Placeholder
            else:
                self.cache_misses += 1
                uncached_texts.append(text)
                uncached_indices.append(i)
                embeddings.append(None)  # Placeholder

        # Uncached text'leri batch olarak hesapla
        if uncached_texts:
            if verbose:
                print(f"      🧮 Computing embeddings: {len(uncached_texts)} links (cached: {len(texts) - len(uncached_texts)})...")
            
            import time
            start_time = time.time()
            
            uncached_embeddings = self.model.encode(
                uncached_texts,
                convert_to_tensor=False,
                show_progress_bar=False,
                batch_size=32
            )
            
            elapsed = time.time() - start_time
            if verbose:
                print(f"      ✅ Embeddings computed in {elapsed:.2f}s ({len(uncached_texts)/elapsed:.1f} emb/sec)")

            # Ensure it's a numpy array (convert if needed)
            if not isinstance(uncached_embeddings, np.ndarray):
                uncached_embeddings = np.array(uncached_embeddings)

            # Cache'e ekle
            for text, emb in zip(uncached_texts, uncached_embeddings):
                self._add_to_cache(text, emb)
                self.total_embeddings_computed += 1

        # Embeddings'i doğru sırayla doldur
        for i, text in enumerate(texts):
            if self._cache_size > 0 and text in self._embedding_cache:
                embeddings[i] = self._embedding_cache[text]
            else:
                # Cache disabled veya text cache'de yok, tekrar hesapla
                embeddings[i] = self.model.encode(text, convert_to_tensor=False, show_progress_bar=False)

        return np.array(embeddings)

    def cosine_similarity(
        self,
        emb1: Union[np.ndarray, str],
        emb2: Union[np.ndarray, str]
    ) -> float:
        """
        İki embedding arasındaki cosine similarity hesapla.

        Parametreler:
            emb1: İlk embedding (vector veya text)
            emb2: İkinci embedding (vector veya text)

        Dönüş:
            float: Cosine similarity (-1 ile 1 arası, genelde 0-1)
                  1.0 = Aynı
                  0.0 = İlgisiz
                  -1.0 = Zıt (nadiren olur)

        Örnek:
            >>> sim = embedder.cosine_similarity("Pizza", "Italy")
            >>> print(f"Similarity: {sim:.3f}")
            Similarity: 0.672
        """
        # String ise embedding'e çevir
        if isinstance(emb1, str):
            emb1 = self.get_embedding(emb1)
        if isinstance(emb2, str):
            emb2 = self.get_embedding(emb2)

        # Cosine similarity: dot product / (norm1 * norm2)
        dot_product = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)

        # Sıfıra bölme kontrolü
        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)

        return float(similarity)

    def get_most_similar(
        self,
        query: str,
        candidates: list[str],
        top_k: int = 5
    ) -> list[tuple[str, float]]:
        """
        Query'ye en benzer candidate'leri bul.

        Parametreler:
            query (str): Aranacak text (örn: "Pizza")
            candidates (list[str]): Adaylar (örn: ["Italy", "Computer", "Food"])
            top_k (int): Kaç tane döndürülsün (default: 5)

        Dönüş:
            list[tuple[str, float]]: (candidate, similarity) çiftleri
                                     Yüksekten düşüğe sıralı

        Örnek:
            >>> results = embedder.get_most_similar(
            ...     "Pizza",
            ...     ["Italy", "Computer", "Food", "Chemistry"]
            ... )
            >>> for text, score in results:
            ...     print(f"{text}: {score:.3f}")
            Food: 0.824
            Italy: 0.672
            Computer: 0.123
        """
        # Query embedding
        query_emb = self.get_embedding(query)

        # Candidate embeddings (batch)
        candidate_embs = self.get_embeddings_batch(candidates)

        # Similarity'leri hesapla
        similarities = []
        for i, candidate_emb in enumerate(candidate_embs):
            sim = self.cosine_similarity(query_emb, candidate_emb)
            similarities.append((candidates[i], sim))

        # Yüksekten düşüğe sırala
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Top-k'yı döndür
        return similarities[:top_k]

    def _add_to_cache(self, text: str, embedding: np.ndarray):
        """Embedding'i cache'e ekle (LRU)."""
        # Cache dolu mu?
        if len(self._embedding_cache) >= self._cache_size and self._cache_size > 0:
            # En eski entry'yi sil
            if len(self._embedding_cache) > 0:
                self._embedding_cache.popitem(last=False)

        # Yeni entry ekle (cache_size > 0 ise)
        if self._cache_size > 0:
            self._embedding_cache[text] = embedding

    def clear_cache(self):
        """Cache'i temizle ve statistics'i sıfırla."""
        self._embedding_cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0

    def _load_cache_from_disk(self):
        """Persistent cache'i disk'ten yükle."""
        import os
        import pickle
        from collections import OrderedDict
        
        if os.path.exists(self._cache_file):
            try:
                print(f"📦 Loading embedding cache from {self._cache_file}...")
                with open(self._cache_file, 'rb') as f:
                    self._embedding_cache = pickle.load(f)
                
                # Cache size limit kontrolü
                if len(self._embedding_cache) > self._cache_size:
                    # En eski entry'leri sil
                    while len(self._embedding_cache) > self._cache_size:
                        self._embedding_cache.popitem(last=False)
                
                print(f"✅ Loaded {len(self._embedding_cache)} cached embeddings")
            except Exception as e:
                print(f"⚠️  Cache load failed: {e}")
                print(f"   Starting with empty cache...")
                self._embedding_cache = OrderedDict()
        else:
            print(f"📝 No cache file found, starting fresh...")
            self._embedding_cache = OrderedDict()

    def save_cache_to_disk(self):
        """Cache'i disk'e kaydet."""
        import pickle
        
        try:
            with open(self._cache_file, 'wb') as f:
                pickle.dump(self._embedding_cache, f)
            print(f"💾 Saved {len(self._embedding_cache)} embeddings to {self._cache_file}")
        except Exception as e:
            print(f"⚠️  Cache save failed: {e}")

    def get_cache_stats(self) -> dict:
        """
        Cache istatistiklerini döndür.

        Returns:
            dict: Statistics
        """
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0

        return {
            'cache_size': len(self._embedding_cache),
            'max_cache_size': self._cache_size,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate': hit_rate,
            'total_embeddings_computed': self.total_embeddings_computed
        }

    def __repr__(self):
        return (
            f"WikiEmbedder(model='{self.model_name}', "
            f"dim={self.model.get_sentence_embedding_dimension()}, "
            f"cache={len(self._embedding_cache)}/{self._cache_size})"
        )
