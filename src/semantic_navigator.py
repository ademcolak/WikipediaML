"""
semantic_navigator.py
---------------------
Semantic embeddings kullanarak akıllı Wikipedia navigasyonu.

Algorithms:
- Greedy Semantic Search: Her adımda en yüksek similarity'li link'i seç
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
from src.claude_reasoning import ClaudeReasoning
from src.link_filter import LinkFilter


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
        use_claude: bool = False,
        claude_api_key: Optional[str] = None,
        use_async: bool = False,
        use_ml: bool = False
    ):
        """
        SemanticNavigator'ı başlat.

        Parametreler:
            verbose (bool): Detaylı log çıktısı
            use_graph (bool): Knowledge Graph kullan (default: True)
            use_claude (bool): Claude reasoning kullan (default: False)
            claude_api_key (str): Anthropic API key (None ise env'den alınır)
            use_async (bool): Async scraper kullan (3-4x daha hızlı, default: False)
            use_ml (bool): ML-based link scoring kullan (Phase 2, default: False)
        """
        self.scraper = WikipediaScraper(cache_size=256)
        self.async_scraper = AsyncWikipediaScraper(cache_size=256) if use_async else None
        self.embedder = WikiEmbedder(cache_size=2048)  # Büyük cache (bazı sayfalarda 500+ link var)
        self.link_filter = LinkFilter(verbose=verbose, use_ml=use_ml)  # Pre-filtering + ML scoring
        self.knowledge_graph = WikiKnowledgeGraph() if use_graph else None
        self.claude_reasoning = ClaudeReasoning(api_key=claude_api_key) if use_claude else None
        self.verbose = verbose
        self.use_graph = use_graph
        self.use_claude = use_claude
        self.use_async = use_async
        self.use_ml = use_ml

        # Metrics
        self.pages_explored = 0
        self.start_time = 0

    def greedy_semantic_search(
        self,
        start: str,
        target: str,
        max_steps: int = 10
    ) -> SemanticSearchResult:
        """
        Greedy Semantic Search: Her adımda en yüksek similarity'li link'i seç.

        Algoritma:
        1. Target'ın embedding'ini hesapla (bir kere)
        2. Mevcut sayfanın linklerini al
        3. Her linkin target'a similarity'sini hesapla
        4. En yüksek similarity'ye sahip link'i seç
        5. O linke git ve tekrarla

        Avantajlar:
        - Çok hızlı (her adımda 1 sayfa)
        - Semantically mantıklı path'ler
        - Az memory kullanımı

        Dezavantajlar:
        - Greedy → local minima'ya takılabilir
        - Garanti optimal path değil
        - Hedefe direkt link yoksa takılabilir

        Parametreler:
            start (str): Başlangıç sayfası
            target (str): Hedef sayfa
            max_steps (int): Maksimum adım sayısı

        Dönüş:
            SemanticSearchResult
        """
        self._initialize_search()

        if self.verbose:
            print(f"\n{'='*60}")
            print(f"🤖 GREEDY SEMANTIC SEARCH")
            print(f"{'='*60}")
            print(f"📍 Başlangıç: {start}")
            print(f"🎯 Hedef: {target}")
            print(f"🚀 Semantic arama başlıyor...\n")

        # Edge case
        if start == target:
            return self._create_result(True, [start], [], "Greedy Semantic")

        # Target embedding'i hesapla (bir kere - tüm adımlarda kullanılacak)
        if self.verbose:
            print(f"🧮 Target embedding hesaplanıyor: {target}")

        target_emb = self.embedder.get_embedding(target)

        # Path tracking
        current_page = start
        path = [start]
        visited = {start}
        similarity_scores = []

        # Greedy search loop
        for step in range(max_steps):
            if self.verbose:
                print(f"\n{'─'*60}")
                print(f"📊 Adım {step + 1}")
                print(f"   Mevcut sayfa: {current_page}")

            # Mevcut sayfanın linklerini al
            soup = self.scraper.get_page_html(current_page)
            if not soup:
                if self.verbose:
                    print(f"   ❌ Sayfa çekilemedi!")
                break

            links = self.scraper.get_wiki_links(soup)
            self.pages_explored += 1

            if self.verbose:
                print(f"   📎 {len(links)} link bulundu")

            # Ziyaret edilmemiş linkleri filtrele
            unvisited_links = [link for link in links if link not in visited]

            if not unvisited_links:
                if self.verbose:
                    print(f"   ⚠️ Tüm linkler ziyaret edilmiş!")
                break

            if self.verbose:
                print(f"   🔍 {len(unvisited_links)} ziyaret edilmemiş link")

            # AKILLI SEÇİM: En yüksek similarity'ye sahip link'i bul
            best_link, best_score, top_candidates = self._select_best_link(
                unvisited_links,
                target_emb,
                show_top=5
            )

            # Verbose output: Top 5 candidate
            if self.verbose:
                print(f"\n   🎯 Top 5 Candidates:")
                for i, (candidate, score) in enumerate(top_candidates, 1):
                    marker = "👉" if candidate == best_link else "  "
                    print(f"   {marker} {i}. {candidate:<30} (similarity: {score:.3f})")

            # Seçilen linke git
            visited.add(best_link)
            path.append(best_link)
            similarity_scores.append(best_score)
            current_page = best_link

            if self.verbose:
                print(f"\n   ✅ Seçilen: {best_link} (similarity: {best_score:.3f})")

            # Hedefe ulaştık mı?
            if current_page == target:
                if self.verbose:
                    print(f"\n{'='*60}")
                    print(f"🎉 HEDEF BULUNDU!")
                    print(f"{'='*60}")

                result = self._create_result(True, path, similarity_scores, "Greedy Semantic")
                self._print_result(result)
                return result

            # Rate limiting
            time.sleep(0.3)

        # Max steps veya takıldı
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"⚠️ HEDEF BULUNAMADI")
            print(f"{'='*60}")
            print(f"   • {len(path)} adım atıldı")
            print(f"   • Max steps ulaşıldı veya takıldı")

        result = self._create_result(False, path, similarity_scores, "Greedy Semantic")
        self._print_result(result)
        return result

    def _select_best_link(
        self,
        links: list[str],
        target_emb,
        show_top: int = 5
    ) -> tuple[str, float, list[tuple[str, float]]]:
        """
        Linkler arasından en yüksek similarity'ye sahip olanı seç.

        Parametreler:
            links: Candidate linkler
            target_emb: Target embedding
            show_top: Kaç tane top candidate döndürülsün

        Dönüş:
            (best_link, best_score, top_candidates)
        """
        if self.verbose:
            print(f"   🧮 {len(links)} link için embedding hesaplanıyor...")

        # Batch olarak tüm linklerin embedding'lerini al (hızlı!)
        link_embeddings = self.embedder.get_embeddings_batch(links)

        # Her link için similarity hesapla
        similarities = []
        for i, link_emb in enumerate(link_embeddings):
            sim = self.embedder.cosine_similarity(target_emb, link_emb)
            similarities.append((links[i], sim))

        # Yüksekten düşüğe sırala
        similarities.sort(key=lambda x: x[1], reverse=True)

        # En iyi link
        best_link = similarities[0][0]
        best_score = similarities[0][1]

        # Top-k candidates
        top_candidates = similarities[:show_top]

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

                # ML-based filtering (Phase 2!)
                if self.use_ml:
                    # Hybrid filter: ML + heuristic
                    filtered_links = self.link_filter.hybrid_filter(
                        unvisited,
                        target,
                        current_page,
                        self.embedder,
                        self.link_filter.category_analyzer,
                        self.knowledge_graph,
                        max_links=beam_width * 10  # Get more candidates for beam
                    )
                else:
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

    def bidirectional_beam_search(
        self,
        start: str,
        target: str,
        beam_width: int = 3,
        max_depth: int = 6
    ) -> SemanticSearchResult:
        """
        Bidirectional Beam Search: Hem baştan hem sondan semantic search.

        Normal beam search'ten farkı:
        - Tek yönlü: start → target (k^d complexity)
        - İki yönlü: start → ← target (2×k^(d/2) complexity)
        - Exponential growth'u yarıya böler!

        Algoritma:
        1. İki beam: forward (start'tan) ve backward (target'tan)
        2. Her adımda her iki beam'i de genişlet
        3. Kesişme var mı kontrol et
        4. Kesişme bulunca path'leri birleştir

        Avantajlar:
        - Çok daha az sayfa tarama (%80-90 azalma)
        - Uzak path'lerde çok daha hızlı
        - Hub sayfalar (Italy, United_States) hemen kesişir

        Parametreler:
            start (str): Başlangıç sayfası
            target (str): Hedef sayfa
            beam_width (int): Her yönde kaç alternatif path (default: 3)
            max_depth (int): Her yön için maksimum derinlik (default: 6)

        Dönüş:
            SemanticSearchResult
        """
        self._initialize_search()

        if self.verbose:
            print(f"\n{'='*60}")
            print(f"🔄 BIDIRECTIONAL BEAM SEARCH (width={beam_width})")
            print(f"{'='*60}")
            print(f"📍 Başlangıç: {start}")
            print(f"🎯 Hedef: {target}")
            print(f"💡 İki yönlü arama: {beam_width}×2 alternatif path\n")

        # Edge case
        if start == target:
            return self._create_result(True, [start], [], "Bidirectional Beam Search")

        # Target ve start embeddings (bir kere hesapla)
        target_emb = self.embedder.get_embedding(target)
        start_emb = self.embedder.get_embedding(start)

        # Forward beam: start'tan target'a doğru
        # [(current_page, path, cumulative_score)]
        forward_beam = [(start, [start], 0.0)]
        forward_visited = {start: [start]}

        # Backward beam: target'tan start'a doğru
        backward_beam = [(target, [target], 0.0)]
        backward_visited = {target: [target]}

        # Main loop
        for depth in range(max_depth):
            if self.verbose:
                print(f"\n{'─'*60}")
                print(f"📊 Derinlik {depth + 1}")
                print(f"   Forward beam: {len(forward_beam)} paths")
                print(f"   Backward beam: {len(backward_beam)} paths")

            # FORWARD SEARCH (start → target)
            if forward_beam:
                forward_candidates = []

                for current_page, path, cum_score in forward_beam:
                    if self.verbose:
                        print(f"\n   🔍 Forward: {current_page}")

                    # Sayfayı çek
                    soup = self.scraper.get_page_html(current_page)
                    if not soup:
                        continue

                    links = self.scraper.get_wiki_links(soup)
                    self.pages_explored += 1

                    # Ziyaret edilmemiş linkler
                    unvisited = [l for l in links if l not in forward_visited]
                    if not unvisited:
                        continue

                    if self.verbose:
                        print(f"      {len(unvisited)} yeni link")

                    # Smart pre-filter (heuristic + hub detection)
                    if len(unvisited) > 100:
                        unvisited = self.link_filter.smart_filter(
                            unvisited,
                            target,
                            current_page,
                            max_links=100
                        )

                    # Similarity hesapla (target'a göre)
                    link_embs = self.embedder.get_embeddings_batch(unvisited)
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
                            # BULUNDU! Path'leri birleştir
                            forward_path = path + [link]
                            backward_path = backward_visited[link]
                            # Backward path'i ters çevir (target'tan link'e)
                            backward_path_reversed = list(reversed(backward_path))
                            # Birleştir (link ortakta, bir kere ekle)
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
                                f"Bidirectional Beam Search (width={beam_width})"
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

            # BACKWARD SEARCH (target → start)
            if backward_beam:
                backward_candidates = []

                for current_page, path, cum_score in backward_beam:
                    if self.verbose:
                        print(f"\n   🔍 Backward: {current_page}")

                    # Sayfayı çek
                    soup = self.scraper.get_page_html(current_page)
                    if not soup:
                        continue

                    links = self.scraper.get_wiki_links(soup)
                    self.pages_explored += 1

                    # Ziyaret edilmemiş linkler
                    unvisited = [l for l in links if l not in backward_visited]
                    if not unvisited:
                        continue

                    if self.verbose:
                        print(f"      {len(unvisited)} yeni link")

                    # Smart pre-filter (backward için start'a göre)
                    if len(unvisited) > 100:
                        unvisited = self.link_filter.smart_filter(
                            unvisited,
                            start,  # Backward search start'a doğru gidiyor
                            current_page,
                            max_links=100
                        )

                    # Similarity hesapla (start'a göre!)
                    link_embs = self.embedder.get_embeddings_batch(unvisited)
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
                            # BULUNDU! Path'leri birleştir
                            forward_path = forward_visited[link]
                            backward_path = path + [link]
                            # Backward path'i ters çevir
                            backward_path_reversed = list(reversed(backward_path))
                            # Birleştir
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
                                f"Bidirectional Beam Search (width={beam_width})"
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

            # Rate limiting
            time.sleep(0.3)

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
            f"Bidirectional Beam Search (width={beam_width})"
        )
        self._print_result(result)
        return result

    def claude_enhanced_search(
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
            top_candidates (int): Claude'a kaç candidate gösterilsin

        Dönüş:
            SemanticSearchResult
        """
        if not self.claude_reasoning:
            raise ValueError("Claude reasoning etkin değil! use_claude=True ile başlatın")

        self._initialize_search()

        if self.verbose:
            print(f"\n{'='*60}")
            print(f"🧠 CLAUDE-ENHANCED SEARCH")
            print(f"{'='*60}")
            print(f"📍 Başlangıç: {start}")
            print(f"🎯 Hedef: {target}")
            print(f"🤖 Claude reasoning aktif...\n")

        # Edge case
        if start == target:
            return self._create_result(True, [start], [], "Claude-Enhanced")

        # Target embedding
        target_emb = self.embedder.get_embedding(target)

        # Path tracking
        current_page = start
        path = [start]
        visited = {start}
        similarity_scores = []
        reasoning_log = []

        # Search loop
        for step in range(max_steps):
            if self.verbose:
                print(f"\n{'─'*60}")
                print(f"📊 Adım {step + 1}")
                print(f"   Mevcut sayfa: {current_page}")

            # Sayfayı çek
            soup = self.scraper.get_page_html(current_page)
            if not soup:
                if self.verbose:
                    print(f"   ❌ Sayfa çekilemedi!")
                break

            links = self.scraper.get_wiki_links(soup)
            self.pages_explored += 1

            # Ziyaret edilmemiş linkler
            unvisited_links = [link for link in links if link not in visited]

            if not unvisited_links:
                if self.verbose:
                    print(f"   ⚠️ Tüm linkler ziyaret edilmiş!")
                break

            if self.verbose:
                print(f"   📎 {len(links)} link, {len(unvisited_links)} ziyaret edilmemiş")

            # Top-N candidates bul (semantic)
            link_embs = self.embedder.get_embeddings_batch(unvisited_links)
            similarities = []
            for i, link_emb in enumerate(link_embs):
                sim = self.embedder.cosine_similarity(target_emb, link_emb)
                similarities.append((unvisited_links[i], sim))

            # Yüksekten düşüğe sırala
            similarities.sort(key=lambda x: x[1], reverse=True)
            candidates = similarities[:top_candidates]

            if self.verbose:
                print(f"\n   🎯 Top {len(candidates)} Candidates (Semantic):")
                for i, (candidate, score) in enumerate(candidates, 1):
                    print(f"      {i}. {candidate:<30} (similarity: {score:.3f})")

            # Claude'a sor
            if self.verbose:
                print(f"\n   🤖 Claude'a soruluyor...")

            choice = self.claude_reasoning.choose_best_link(
                current_page=current_page,
                target_page=target,
                candidates=candidates,
                path_so_far=path
            )

            if self.verbose:
                print(f"\n   ✅ Claude'un Seçimi: {choice.chosen_link}")
                print(f"   💭 Reasoning: {choice.reasoning}")
                print(f"   🎯 Confidence: {choice.confidence:.2f}")

            # Seçilen linke git
            visited.add(choice.chosen_link)
            path.append(choice.chosen_link)

            # Score olarak Claude confidence + semantic similarity ortalaması
            chosen_semantic = next((s for l, s in candidates if l == choice.chosen_link), 0.0)
            combined_score = (choice.confidence + chosen_semantic) / 2
            similarity_scores.append(combined_score)
            reasoning_log.append(choice.reasoning)

            current_page = choice.chosen_link

            # Hedefe ulaştık mı?
            if current_page == target:
                if self.verbose:
                    print(f"\n{'='*60}")
                    print(f"🎉 HEDEF BULUNDU!")
                    print(f"{'='*60}")

                result = self._create_result(True, path, similarity_scores, "Claude-Enhanced")
                self._print_result(result)

                # Reasoning log göster
                if self.verbose:
                    print(f"\n💭 Claude Reasoning Log:")
                    print(f"{'─'*60}")
                    for i, reason in enumerate(reasoning_log, 1):
                        print(f"   {i}. {reason}")

                return result

            # Rate limiting
            time.sleep(0.5)  # Claude API için biraz daha uzun bekleme

        # Max steps veya takıldı
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"⚠️ HEDEF BULUNAMADI")
            print(f"{'='*60}")

        result = self._create_result(False, path, similarity_scores, "Claude-Enhanced")
        self._print_result(result)
        return result

    def hybrid_search(
        self,
        start: str,
        target: str,
        max_steps: int = 10
    ) -> SemanticSearchResult:
        """
        Hybrid Search: Graph + Semantic/Claude Search kombinasyonu.

        1. Graph'ta path var mı bak
        2. Varsa kullan (hızlı!)
        3. Yoksa:
           - use_claude=True → Claude-Enhanced Search
           - use_claude=False → Beam Search
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
            mode = "Claude Reasoning" if self.use_claude else "Beam Search"
            print(f"\n{'='*60}")
            print(f"🧬 HYBRID SEARCH (Graph + {mode})")
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
                    if self.use_claude:
                        print(f"   Claude-Enhanced search kullanılacak...\n")
                    else:
                        print(f"   Beam search kullanılacak...\n")

        # 2. Claude, Bidirectional Beam, veya Beam Search
        if self.use_claude:
            # Claude-Enhanced Search (daha akıllı!)
            result = self.claude_enhanced_search(
                start=start,
                target=target,
                max_steps=max_steps,
                top_candidates=5
            )
            result.algorithm = "Hybrid (Claude-Enhanced)"
        else:
            # Bidirectional Beam Search (çok daha hızlı!)
            # Uzak path'ler için bidirectional kullan
            result = self.bidirectional_beam_search(
                start=start,
                target=target,
                beam_width=4,  # 4 alternatif yol (daha fazla exploration)
                max_depth=min(max_steps // 2 + 2, 10)  # Her yön için max depth (artırıldı)
            )
            result.algorithm = "Hybrid (Bidirectional Beam)"
            
            # Eğer bulunamadıysa ve çok uzak path ise, normal beam search dene
            if not result.found and max_steps > 15:
                if self.verbose:
                    print(f"\n{'='*60}")
                    print(f"⚠️ Bidirectional başarısız, normal beam search deneniyor...")
                    print(f"{'='*60}")
                
                # Normal beam search (tek yönlü ama daha derin)
                result = self.beam_search(
                    start=start,
                    target=target,
                    beam_width=5,  # Daha geniş beam
                    max_depth=max_steps
                )
                result.algorithm = "Hybrid (Beam Search Fallback)"

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

    def _save_to_graph(self, result: SemanticSearchResult):
        """Başarılı path'i graph'a kaydet."""
        if result.found and self.knowledge_graph:
            self.knowledge_graph.add_path(result.path, success=True)
            self.knowledge_graph.save()

    def get_stats(self) -> dict:
        """Tüm statistics'i döndür."""
        stats = {
            'scraper': self.scraper.get_cache_stats(),
            'embedder': self.embedder.get_cache_stats()
        }

        if self.knowledge_graph:
            stats['graph'] = self.knowledge_graph.get_stats()

        if self.claude_reasoning:
            stats['claude'] = self.claude_reasoning.get_stats()

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
