"""
semantic_navigator.py
---------------------
Semantic embeddings kullanarak akıllı Wikipedia navigasyonu.

Algorithms:
- Greedy Semantic Search: Her adımda en yüksek similarity'li link'i seç
- Parallel Evaluation: Linkleri paralel değerlendir (YENI!)
- Beam Search: Top-k linkleri paralel explore et (ileride)
"""

import time
import asyncio
from dataclasses import dataclass
from typing import Optional
from src.scraper import WikipediaScraper
from src.async_scraper import AsyncWikipediaScraper
from src.embedder import WikiEmbedder
from src.knowledge_graph import WikiKnowledgeGraph
from src.link_filter import LinkFilter
from src.hybrid_navigator import HybridNavigator
from src.embedding_navigator import EmbeddingNavigator
from src.llm_navigator import LLMNavigator
from src.parallel_evaluator import ParallelLinkEvaluator


@dataclass
class SemanticSearchResult:
    """Semantic search sonuçları."""
    found: bool
    path: list[str]
    steps: int
    pages_explored: int
    time_seconds: float
    similarity_scores: list[float]  # Her adımdaki seçilen link'in similarity'si
    algorithm: str


class SemanticNavigator:
    """
    Semantic embeddings ile Wikipedia navigasyonu.

    BFS kör arama yapar (tüm linkler eşit).
    Semantic search akıllı seçim yapar (hedefe en yakın link'i seç).

    Örnek:
        Potato sayfasında 500+ link var.
        BFS: Hepsini tara
        Semantic: Hedefe en yakın olanı seç (örn: "Food" → 0.85 similarity)
    """

    def __init__(
        self,
        verbose: bool = True,
        use_graph: bool = True,
        use_async: bool = False,
        use_hybrid: bool = False,
        use_llm: bool = False,
        use_parallel: bool = True,
        max_workers: int = 4
    ):
        """
        SemanticNavigator'ı başlat.

        Parametreler:
            verbose (bool): Detaylı log çıktısı
            use_graph (bool): Knowledge Graph kullan (default: True)
            use_async (bool): Async scraper kullan (3-4x daha hızlı, default: False)
            use_hybrid (bool): Hybrid Navigator kullan (Embedding + LLM, default: False)
            use_llm (bool): LLM Navigator kullan (Claude API, default: False)
            use_parallel (bool): Parallel link evaluation kullan (default: True)
            max_workers (int): Parallel evaluation için worker sayısı (default: 4)
        """
        self.scraper = WikipediaScraper(cache_size=256)
        # Async scraper için düşük max_concurrent (Wikipedia rate limiting)
        self.async_scraper = AsyncWikipediaScraper(
            cache_size=256,
            max_concurrent=3  # 10'dan 3'e düşür (rate limiting için)
        ) if use_async else None
        self.embedder = WikiEmbedder(cache_size=2048)  # Büyük cache (bazı sayfalarda 500+ link var)
        self.link_filter = LinkFilter(verbose=verbose)  # Pre-filtering
        self.knowledge_graph = WikiKnowledgeGraph() if use_graph else None
        self.verbose = verbose
        self.use_graph = use_graph
        self.use_async = use_async
        self.use_hybrid = use_hybrid
        self.use_llm = use_llm
        self.use_parallel = use_parallel

        # Parallel Evaluator (YENI!)
        self.parallel_evaluator = None
        if use_parallel:
            self.parallel_evaluator = ParallelLinkEvaluator(
                max_workers=max_workers,
                verbose=verbose
            )
            if verbose:
                print(f"✅ Parallel Evaluator initialized ({max_workers} workers)")

        # Hybrid Navigator (10K+ edge için)
        self.hybrid_navigator = None
        if use_hybrid and self.knowledge_graph:
            try:
                embedding_nav = EmbeddingNavigator() if use_hybrid else None
                llm_nav = LLMNavigator() if use_llm else None
                self.hybrid_navigator = HybridNavigator(
                    kg=self.knowledge_graph,
                    embedding_nav=embedding_nav,
                    llm_nav=llm_nav,
                    use_embedding=use_hybrid,
                    use_llm=use_llm
                )
                if verbose:
                    print("✅ Hybrid Navigator initialized")
                    if use_llm:
                        print("   • LLM mode: ACTIVE (Claude API)")
                    else:
                        print("   • LLM mode: DISABLED (Embedding only)")
            except Exception as e:
                if verbose:
                    print(f"⚠️ Hybrid Navigator initialization failed: {e}")
                    print("   Falling back to standard semantic search")
                self.hybrid_navigator = None

        # Metrics
        self.pages_explored = 0
        self.start_time = 0

    # Removed: greedy_semantic_search() - not used in v5.0.0

    def _select_best_link(
        self,
        links: list[str],
        target_emb,
        show_top: int = 5
    ) -> tuple[str, float, list[tuple[str, float]]]:
        """
        Linkler arasından en yüksek similarity'ye sahip olanı seç.
        
        UPDATED: Artık parallel evaluation kullanıyor (daha hızlı!)

        Parametreler:
            links: Candidate linkler
            target_emb: Target embedding
            show_top: Kaç tane top candidate döndürülsün

        Dönüş:
            (best_link, best_score, top_candidates)
        """
        if self.verbose:
            print(f"   🧮 {len(links)} link için embedding hesaplanıyor...")

        # Parallel evaluation kullan (varsa)
        if self.use_parallel and self.parallel_evaluator and len(links) > 10:
            # Parallel evaluation (daha hızlı!)
            top_candidates = self.parallel_evaluator.evaluate_links_parallel(
                links=links,
                target_embedding=target_emb,
                embedder=self.embedder,
                top_k=show_top
            )
        else:
            # Sequential evaluation (fallback)
            # Batch olarak tüm linklerin embedding'lerini al (hızlı!)
            link_embeddings = self.embedder.get_embeddings_batch(links)

            # Her link için similarity hesapla
            similarities = []
            for i, link_emb in enumerate(link_embeddings):
                sim = self.embedder.cosine_similarity(target_emb, link_emb)
                similarities.append((links[i], sim))

            # Yüksekten düşüğe sırala
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Top-k candidates
            top_candidates = similarities[:show_top]

        # En iyi link
        best_link = top_candidates[0][0]
        best_score = top_candidates[0][1]

        return best_link, best_score, top_candidates

    def _initialize_search(self):
        """Search metriklerini sıfırla."""
        self.pages_explored = 0
        self.start_time = time.time()

    def _create_result(
        self,
        found: bool,
        path: list[str],
        similarity_scores: list[float],
        algorithm: str
    ) -> SemanticSearchResult:
        """SemanticSearchResult objesi oluştur."""
        return SemanticSearchResult(
            found=found,
            path=path,
            steps=len(path) - 1,
            pages_explored=self.pages_explored,
            time_seconds=time.time() - self.start_time,
            similarity_scores=similarity_scores,
            algorithm=algorithm
        )

    def _print_result(self, result: SemanticSearchResult):
        """Search sonucunu yazdır."""
        if not self.verbose:
            return

        if result.found:
            print(f"\n🛤️ Bulunan Path:")
            print(f"{'─'*60}")
            for i, page in enumerate(result.path):
                if i == 0:
                    print(f"  🏁 {page}")
                elif i == len(result.path) - 1:
                    print(f"  🎯 {page}")
                else:
                    # Graph'tan geldi mi? (similarity yok)
                    if result.similarity_scores and i-1 < len(result.similarity_scores):
                        score = result.similarity_scores[i-1]
                        print(f"  {i}. {page:<30} (sim: {score:.3f})")
                    else:
                        print(f"  {i}. {page}")

        print(f"\n📊 İstatistikler:")
        print(f"  • Algoritma: {result.algorithm}")
        print(f"  • Adım sayısı: {result.steps}")
        print(f"  • Taranan sayfa: {result.pages_explored}")
        print(f"  • Toplam süre: {result.time_seconds:.2f}s")

        if result.similarity_scores:
            avg_sim = sum(result.similarity_scores) / len(result.similarity_scores)
            print(f"  • Ortalama similarity: {avg_sim:.3f}")

        # Cache statistics
        print(f"\n💾 Scraper Cache:")
        scraper_stats = self.scraper.get_cache_stats()
        print(f"  • Hit rate: {scraper_stats['hit_rate']:.1f}%")

        print(f"\n🧮 Embedder Cache:")
        embedder_stats = self.embedder.get_cache_stats()
        print(f"  • Hit rate: {embedder_stats['hit_rate']:.1f}%")
        print(f"  • Total embeddings: {embedder_stats['total_embeddings_computed']}")

    def beam_search(
        self,
        start: str,
        target: str,
        beam_width: int = 3,
        max_depth: int = 6
    ) -> SemanticSearchResult:
        """
        Beam Search: En iyi k path'i paralel explore et.

        Greedy'den farkı:
        - Greedy: Sadece 1 yol dener (takılabilir)
        - Beam: En iyi k yolu dener (daha robust)

        Parametreler:
            start (str): Başlangıç sayfası
            target (str): Hedef sayfa
            beam_width (int): Kaç alternatif path (default: 3)
            max_depth (int): Maksimum derinlik (default: 6)

        Dönüş:
            SemanticSearchResult
        """
        self._initialize_search()

        if self.verbose:
            print(f"\n{'='*60}")
            print(f"🔮 BEAM SEARCH (width={beam_width})")
            print(f"{'='*60}")
            print(f"📍 Başlangıç: {start}")
            print(f"🎯 Hedef: {target}")
            print(f"💡 {beam_width} alternatif path paralel deneniyor...\n")

        # Edge case
        if start == target:
            return self._create_result(True, [start], [], "Beam Search")

        # Target embedding (bir kere hesapla)
        target_emb = self.embedder.get_embedding(target)

        # Beam: [(current_page, path, cumulative_score)]
        beam = [(start, [start], 0.0)]
        visited = {start}

        # Main loop
        for depth in range(max_depth):
            if self.verbose:
                print(f"\n{'─'*60}")
                print(f"📊 Derinlik {depth + 1}")
                print(f"   Beam size: {len(beam)} path")

            candidates = []

            # Her beam element için expand et
            for current_page, path, cum_score in beam:
                if self.verbose:
                    print(f"\n   🔍 Exploring: {current_page}")

                # Sayfayı çek
                soup = self.scraper.get_page_html(current_page)
                if not soup:
                    continue

                links = self.scraper.get_wiki_links(soup)
                self.pages_explored += 1

                # Ziyaret edilmemiş linkleri filtrele
                unvisited = [l for l in links if l not in visited]

                if not unvisited:
                    continue

                if self.verbose:
                    print(f"      {len(unvisited)} yeni link bulundu")

                # Smart filter: heuristic only
                filtered_links = self.link_filter.smart_filter(
                    unvisited,
                    target,
                    current_page,
                    max_links=100
                )

                # Link'lerin similarity'lerini hesapla
                link_embs = self.embedder.get_embeddings_batch(filtered_links)
                similarities = []
                for i, link_emb in enumerate(link_embs):
                    sim = self.embedder.cosine_similarity(target_emb, link_emb)
                    similarities.append((filtered_links[i], sim))

                # En iyi top-k link'i al (her branch için)
                similarities.sort(key=lambda x: x[1], reverse=True)
                top_links = similarities[:beam_width]

                # Candidate'leri ekle
                for link, sim in top_links:
                    if link == target:
                        # HEDEF BULUNDU!
                        final_path = path + [link]
                        if self.verbose:
                            print(f"\n{'='*60}")
                            print(f"🎉 HEDEF BULUNDU!")
                            print(f"{'='*60}")

                        result = self._create_result(
                            True,
                            final_path,
                            [sim],  # Sadece son adımın similarity'si
                            f"Beam Search (width={beam_width})"
                        )
                        self._print_result(result)
                        return result

                    # Yeni path oluştur
                    new_path = path + [link]
                    # Score: Cumulative average
                    new_score = (cum_score * len(path) + sim) / len(new_path)

                    candidates.append((link, new_path, new_score))
                    visited.add(link)

            if not candidates:
                # Hiç candidate yok
                if self.verbose:
                    print(f"\n   ⚠️ Tüm yollar tükendi!")
                break

            # En iyi beam_width tanesini seç
            candidates.sort(key=lambda x: x[2], reverse=True)
            beam = candidates[:beam_width]

            if self.verbose:
                print(f"\n   🎯 Top {len(beam)} paths seçildi:")
                for i, (page, pth, score) in enumerate(beam, 1):
                    print(f"      {i}. {page} (avg sim: {score:.3f})")

            # Rate limiting
            time.sleep(0.3)

        # Max depth veya takıldı
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"⚠️ HEDEF BULUNAMADI")
            print(f"{'='*60}")

        # En iyi path'i döndür
        best_path = beam[0][1] if beam else [start]
        result = self._create_result(False, best_path, [], f"Beam Search (width={beam_width})")
        self._print_result(result)
        return result

    # Removed: bidirectional_beam_search() - async version is used instead (275 lines removed)
    # Removed: claude_enhanced_search() - not used in v5.0.0
    
    def _removed_claude_enhanced_search(
        self,
        start: str,
        target: str,
        max_steps: int = 10,
        top_candidates: int = 5
    ) -> SemanticSearchResult:
        """
        Claude-Enhanced Semantic Search: Claude reasoning ile akıllı link seçimi.

        Algoritma:
        1. Target embedding hesapla
        2. Mevcut sayfanın linklerini al
        3. Top-N candidate bul (semantic similarity)
        4. Claude'a sor: "Hangisi hedefe ulaşmak için en iyi?"
        5. Claude'un seçtiği link'i kullan

        Avantajlar:
        - Semantic + Reasoning kombinasyonu
        - Daha akıllı kararlar (alakasız döngülerden kaçınır)
        - Açıklamalı seçimler (neden bu link?)

        Dezavantajlar:
        - API calls → daha yavaş
        - API key gerekli
        - Maliyet (token kullanımı)

        Parametreler:
            start (str): Başlangıç sayfası
            target (str): Hedef sayfa
            max_steps (int): Maksimum adım sayısı
            top_candidates (int): Kaç candidate gösterilsin

        Dönüş:
            SemanticSearchResult
        
        Note: This method is deprecated and not used in v5.0.0
        """
        raise NotImplementedError("Claude-enhanced search removed in v5.0.0. Use beam search instead.")

    def hybrid_search(
        self,
        start: str,
        target: str,
        max_steps: int = 10
    ) -> SemanticSearchResult:
        """
        Hybrid Search: Graph + Semantic/Hybrid Navigator kombinasyonu.

        1. Graph'ta path var mı bak (A* search)
        2. Varsa kullan (hızlı!)
        3. Yoksa:
           - use_hybrid=True → HybridNavigator (KG + Embedding + LLM)
           - use_hybrid=False → Beam Search (sadece semantic)
        4. Başarılıysa graph'a kaydet

        Parametreler:
            start (str): Başlangıç sayfası
            target (str): Hedef sayfa
            max_steps (int): Maksimum adım sayısı

        Dönüş:
            SemanticSearchResult
        """
        self._initialize_search()

        if self.verbose:
            mode_name = "Hybrid Navigator (KG+Embedding+LLM)" if self.use_hybrid else "Beam Search"
            print(f"\n{'='*60}")
            print(f"🧬 HYBRID SEARCH (Graph + {mode_name})")
            print(f"{'='*60}")
            print(f"📍 Başlangıç: {start}")
            print(f"🎯 Hedef: {target}\n")

        # 1. Graph'ta path var mı? (A* search ile heuristic kullan)
        if self.knowledge_graph:
            if self.verbose:
                print(f"🔍 Knowledge Graph kontrol ediliyor...")

            # A* heuristic: Semantic similarity to target
            target_emb = self.embedder.get_embedding(target)
            
            def semantic_heuristic(node: str, target_node: str) -> float:
                """
                A* heuristic: Node'dan target'a semantic distance.
                Düşük değer = daha yakın (A* minimize eder)
                """
                try:
                    node_emb = self.embedder.get_embedding(node)
                    similarity = self.embedder.cosine_similarity(node_emb, target_emb)
                    # Similarity'yi distance'a çevir (1 - similarity)
                    # Yüksek similarity = düşük distance
                    return 1.0 - similarity
                except:
                    return 1.0  # Unknown node, max distance
            
            # A* search with semantic heuristic
            graph_path = self.knowledge_graph.find_path(
                start,
                target,
                heuristic=semantic_heuristic
            )

            if graph_path:
                if self.verbose:
                    print(f"✅ Graph'ta path bulundu! (A* search)")
                    print(f"   Path: {' → '.join(graph_path)}")
                    print(f"   🎯 Öğrenilmiş bilgi kullanılıyor!\n")

                result = self._create_result(
                    True,
                    graph_path,
                    [],  # Graph'tan geldi, similarity yok
                    "Hybrid (Graph A* Reused)"
                )
                self._print_result(result)
                return result
            else:
                if self.verbose:
                    print(f"❌ Graph'ta path yok")
                    if self.use_hybrid:
                        print(f"   Hybrid Navigator kullanılacak (KG + Embedding + LLM)...\n")
                    else:
                        print(f"   Beam search kullanılacak...\n")

        # 2. Hybrid Navigator veya Beam Search
        if self.use_hybrid and self.hybrid_navigator:
            # Yeni Hybrid Navigator ile path bul
            result = self._hybrid_navigator_search(start, target, max_steps)
        else:
            # Klasik Beam Search
            result = self.beam_search(
                start=start,
                target=target,
                beam_width=4,
                max_depth=max_steps
            )
            result.algorithm = "Hybrid (Beam Search)"

        # 3. Başarılıysa graph'a kaydet (path quality ile)
        if result.found and self.knowledge_graph:
            # Path quality: Kısa path = yüksek quality
            # 2 adım = 1.0, 3 adım = 0.8, 4 adım = 0.6, vs.
            path_length = len(result.path) - 1
            path_quality = max(0.2, 1.0 - (path_length - 2) * 0.2)
            
            self.knowledge_graph.add_path(
                result.path,
                success=True,
                path_quality=path_quality
            )
            self.knowledge_graph.save()

            if self.verbose:
                print(f"\n💾 Path graph'a kaydedildi! (quality: {path_quality:.2f})")
        
        # 4. Embedding cache'i kaydet (persistent)
        self.embedder.save_cache_to_disk()

        return result
    
    def _hybrid_navigator_search(
        self,
        start: str,
        target: str,
        max_steps: int = 10
    ) -> SemanticSearchResult:
        """
        HybridNavigator kullanarak path bul.
        
        3-tier system:
        1. KG lookup (fastest)
        2. Embedding filter (medium)
        3. LLM selection (smartest)
        """
        if self.verbose:
            print(f"🚀 Hybrid Navigator başlatılıyor...")
        
        path = [start]
        current = start
        similarity_scores = []
        
        for step in range(max_steps):
            if current == target:
                # Hedef bulundu!
                if self.verbose:
                    print(f"\n{'='*60}")
                    print(f"🎉 HEDEF BULUNDU!")
                    print(f"{'='*60}")
                
                return self._create_result(
                    True,
                    path,
                    similarity_scores,
                    "Hybrid Navigator (KG+Embedding+LLM)"
                )
            
            # Mevcut sayfanın linklerini al
            soup = self.scraper.get_page_html(current)
            links = self.scraper.get_wiki_links(soup) if soup else []
            
            self.pages_explored += 1
            
            if not links:
                if self.verbose:
                    print(f"   ❌ {current}: No links found")
                break
            
            if self.verbose:
                print(f"\n   🔍 Step {step + 1}: {current}")
                print(f"      Available links: {len(links)}")
            
            # Hybrid Navigator ile sonraki adımı seç
            try:
                if not self.hybrid_navigator:
                    raise ValueError("Hybrid Navigator not initialized")
                
                next_page = self.hybrid_navigator.find_next_step(
                    current_page=current,
                    target_page=target,
                    available_links=links,
                    embedding_k=5
                )
                
                if self.verbose:
                    print(f"      → Selected: {next_page}")
                
                path.append(next_page)
                current = next_page
                
                # Rate limiting
                time.sleep(0.3)
                
            except Exception as e:
                if self.verbose:
                    print(f"   ❌ Error: {e}")
                break
        
        # Max steps veya hata
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"⚠️ HEDEF BULUNAMADI (max steps: {max_steps})")
            print(f"{'='*60}")
        
        return self._create_result(
            False,
            path,
            similarity_scores,
            "Hybrid Navigator (KG+Embedding+LLM)"
        )

    # Removed: _save_to_graph() - not used, hybrid_search calls add_path directly

    def get_stats(self) -> dict:
        """Tüm statistics'i döndür."""
        stats = {
            'scraper': self.scraper.get_cache_stats(),
            'embedder': self.embedder.get_cache_stats()
        }

        if self.knowledge_graph:
            stats['graph'] = self.knowledge_graph.get_stats()

        return stats


    async def async_bidirectional_beam_search(
        self,
        start: str,
        target: str,
        beam_width: int = 3,
        max_depth: int = 6
    ) -> SemanticSearchResult:
        """
        ASYNC Bidirectional Beam Search: Paralel sayfa çekme ile 3-4x daha hızlı!
        
        Normal bidirectional beam search'ten farkı:
        - Sync: Her beam'deki sayfaları sırayla çeker (4 sayfa × 500ms = 2000ms)
        - Async: Tüm beam'i paralel çeker (4 sayfa paralel = 500ms) → 4x hızlı!
        
        Performance:
        - Beam width=4 için: 4x hızlanma
        - 13.85s → 3-4s (Minimax → U.S._Route_111)
        
        Parametreler:
            start (str): Başlangıç sayfası
            target (str): Hedef sayfa
            beam_width (int): Her yönde kaç alternatif path (default: 3)
            max_depth (int): Her yön için maksimum derinlik (default: 6)
            
        Dönüş:
            SemanticSearchResult
        """
        if not self.async_scraper:
            raise ValueError("Async scraper not initialized! Set use_async=True in constructor.")
        
        self._initialize_search()
        
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"⚡ ASYNC BIDIRECTIONAL BEAM SEARCH (width={beam_width})")
            print(f"{'='*60}")
            print(f"📍 Başlangıç: {start}")
            print(f"🎯 Hedef: {target}")
            print(f"💡 Paralel sayfa çekme aktif!\n")
        
        # Edge case
        if start == target:
            return self._create_result(True, [start], [], "Async Bidirectional Beam")
        
        # Target ve start embeddings
        target_emb = self.embedder.get_embedding(target)
        start_emb = self.embedder.get_embedding(start)
        
        # Forward beam
        forward_beam = [(start, [start], 0.0)]
        forward_visited = {start: [start]}
        
        # Backward beam
        backward_beam = [(target, [target], 0.0)]
        backward_visited = {target: [target]}
        
        # Main loop
        for depth in range(max_depth):
            if self.verbose:
                print(f"\n{'─'*60}")
                print(f"📊 Derinlik {depth + 1}")
                print(f"   Forward beam: {len(forward_beam)} paths")
                print(f"   Backward beam: {len(backward_beam)} paths")
            
            # PARALLEL FETCH: Tüm beam'deki sayfaları paralel çek!
            pages_to_fetch = []
            
            # Forward beam'deki sayfalar
            forward_pages = [page for page, _, _ in forward_beam]
            pages_to_fetch.extend(forward_pages)
            
            # Backward beam'deki sayfalar
            backward_pages = [page for page, _, _ in backward_beam]
            pages_to_fetch.extend(backward_pages)
            
            if self.verbose:
                print(f"\n   ⚡ Paralel çekiliyor: {len(pages_to_fetch)} sayfa...")
            
            # ASYNC MAGIC: Tüm sayfaları paralel çek!
            start_fetch = time.time()
            all_soups = await self.async_scraper.get_pages_batch(pages_to_fetch)
            fetch_time = time.time() - start_fetch
            
            if self.verbose:
                print(f"   ✅ Tamamlandı: {fetch_time:.2f}s ({len(pages_to_fetch)/fetch_time:.1f} pages/sec)")
            
            # FORWARD SEARCH
            forward_candidates = []
            
            for current_page, path, cum_score in forward_beam:
                soup = all_soups.get(current_page)
                if not soup:
                    continue
                
                links = self.async_scraper.get_wiki_links(soup)
                self.pages_explored += 1
                
                # Ziyaret edilmemiş linkler
                unvisited = [l for l in links if l not in forward_visited]
                if not unvisited:
                    continue
                
                if self.verbose:
                    print(f"\n   🔍 Forward: {current_page} ({len(unvisited)} yeni link)")
                
                # FAST pre-filter (quick_filter only, no categories!)
                if len(unvisited) > 30:
                    unvisited = self.link_filter.quick_filter(
                        unvisited,
                        target,
                        max_links=30  # Reduced to 30 for speed
                    )
                    if self.verbose:
                        print(f"   🔍 Pre-filter: {len(links)} → {len(unvisited)} links")
                
                if self.verbose:
                    print(f"      🧮 Computing embeddings for {len(unvisited)} links...")
                
                # Similarity hesapla (max 30 links now)
                emb_start = time.time()
                link_embs = self.embedder.get_embeddings_batch(unvisited, verbose=self.verbose)
                emb_time = time.time() - emb_start
                
                if self.verbose:
                    print(f"      ✅ Embeddings done in {emb_time:.2f}s")
                similarities = []
                for i, link_emb in enumerate(link_embs):
                    sim = self.embedder.cosine_similarity(target_emb, link_emb)
                    similarities.append((unvisited[i], sim))
                
                # Top-k link
                similarities.sort(key=lambda x: x[1], reverse=True)
                top_links = similarities[:beam_width]
                
                # Candidate'leri ekle
                for link, sim in top_links:
                    # KESİŞME KONTROLÜ!
                    if link in backward_visited:
                        # BULUNDU!
                        forward_path = path + [link]
                        backward_path = backward_visited[link]
                        backward_path_reversed = list(reversed(backward_path))
                        complete_path = forward_path + backward_path_reversed[1:]
                        
                        if self.verbose:
                            print(f"\n{'='*60}")
                            print(f"🎉 KESİŞME BULUNDU!")
                            print(f"{'='*60}")
                            print(f"🔗 Kesişme noktası: {link}")
                            print(f"   Forward: {' → '.join(forward_path)}")
                            print(f"   Backward: {' → '.join(backward_path)}")
                        
                        result = self._create_result(
                            True,
                            complete_path,
                            [sim],
                            f"Async Bidirectional Beam (width={beam_width})"
                        )
                        self._print_result(result)
                        return result
                    
                    # Yeni path
                    new_path = path + [link]
                    new_score = (cum_score * len(path) + sim) / len(new_path)
                    forward_candidates.append((link, new_path, new_score))
                    forward_visited[link] = new_path
            
            # En iyi beam_width tanesini seç
            if forward_candidates:
                forward_candidates.sort(key=lambda x: x[2], reverse=True)
                forward_beam = forward_candidates[:beam_width]
                
                if self.verbose:
                    print(f"\n   🎯 Forward top {len(forward_beam)}:")
                    for i, (page, _, score) in enumerate(forward_beam, 1):
                        print(f"      {i}. {page} (score: {score:.3f})")
            
            # BACKWARD SEARCH
            backward_candidates = []
            
            for current_page, path, cum_score in backward_beam:
                soup = all_soups.get(current_page)
                if not soup:
                    continue
                
                links = self.async_scraper.get_wiki_links(soup)
                self.pages_explored += 1
                
                # Ziyaret edilmemiş linkler
                unvisited = [l for l in links if l not in backward_visited]
                if not unvisited:
                    continue
                
                if self.verbose:
                    print(f"\n   🔍 Backward: {current_page} ({len(unvisited)} yeni link)")
                
                # FAST pre-filter (quick_filter only, no categories!)
                if len(unvisited) > 30:
                    unvisited = self.link_filter.quick_filter(
                        unvisited,
                        start,
                        max_links=30  # Reduced to 30 for speed
                    )
                    if self.verbose:
                        print(f"   🔍 Pre-filter: {len(links)} → {len(unvisited)} links")
                
                if self.verbose:
                    print(f"      🧮 Computing embeddings for {len(unvisited)} links...")
                
                # Similarity hesapla (start'a göre, max 30 links now)
                emb_start = time.time()
                link_embs = self.embedder.get_embeddings_batch(unvisited, verbose=self.verbose)
                emb_time = time.time() - emb_start
                
                if self.verbose:
                    print(f"      ✅ Embeddings done in {emb_time:.2f}s")
                similarities = []
                for i, link_emb in enumerate(link_embs):
                    sim = self.embedder.cosine_similarity(start_emb, link_emb)
                    similarities.append((unvisited[i], sim))
                
                # Top-k link
                similarities.sort(key=lambda x: x[1], reverse=True)
                top_links = similarities[:beam_width]
                
                # Candidate'leri ekle
                for link, sim in top_links:
                    # KESİŞME KONTROLÜ!
                    if link in forward_visited:
                        # BULUNDU!
                        forward_path = forward_visited[link]
                        backward_path = path + [link]
                        backward_path_reversed = list(reversed(backward_path))
                        complete_path = forward_path + backward_path_reversed[1:]
                        
                        if self.verbose:
                            print(f"\n{'='*60}")
                            print(f"🎉 KESİŞME BULUNDU!")
                            print(f"{'='*60}")
                            print(f"🔗 Kesişme noktası: {link}")
                            print(f"   Forward: {' → '.join(forward_path)}")
                            print(f"   Backward: {' → '.join(backward_path)}")
                        
                        result = self._create_result(
                            True,
                            complete_path,
                            [sim],
                            f"Async Bidirectional Beam (width={beam_width})"
                        )
                        self._print_result(result)
                        return result
                    
                    # Yeni path
                    new_path = path + [link]
                    new_score = (cum_score * len(path) + sim) / len(new_path)
                    backward_candidates.append((link, new_path, new_score))
                    backward_visited[link] = new_path
            
            # En iyi beam_width tanesini seç
            if backward_candidates:
                backward_candidates.sort(key=lambda x: x[2], reverse=True)
                backward_beam = backward_candidates[:beam_width]
                
                if self.verbose:
                    print(f"\n   🎯 Backward top {len(backward_beam)}:")
                    for i, (page, _, score) in enumerate(backward_beam, 1):
                        print(f"      {i}. {page} (score: {score:.3f})")
            
            # Her iki beam de boşsa dur
            if not forward_beam and not backward_beam:
                break
            
            # Rate limiting (async için daha kısa)
            await asyncio.sleep(0.2)
        
        # Max depth veya takıldı
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"⚠️ HEDEF BULUNAMADI")
            print(f"{'='*60}")
        
        # En iyi forward path'i döndür
        best_path = forward_beam[0][1] if forward_beam else [start]
        result = self._create_result(
            False,
            best_path,
            [],
            f"Async Bidirectional Beam (width={beam_width})"
        )
        self._print_result(result)
        return result
        return stats
