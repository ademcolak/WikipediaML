"""
semantic_navigator.py
---------------------
Semantic embeddings kullanarak akıllı Wikipedia navigasyonu.

Algorithms:
- Greedy Semantic Search: Her adımda en yüksek similarity'li link'i seç
- Beam Search: Top-k linkleri paralel explore et (ileride)
"""

import time
from dataclasses import dataclass
from typing import Optional
from src.scraper import WikipediaScraper
from src.embedder import WikiEmbedder
from src.knowledge_graph import WikiKnowledgeGraph
from src.claude_reasoning import ClaudeReasoning


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
        claude_api_key: Optional[str] = None
    ):
        """
        SemanticNavigator'ı başlat.

        Parametreler:
            verbose (bool): Detaylı log çıktısı
            use_graph (bool): Knowledge Graph kullan (default: True)
            use_claude (bool): Claude reasoning kullan (default: False)
            claude_api_key (str): Anthropic API key (None ise env'den alınır)
        """
        self.scraper = WikipediaScraper(cache_size=256)
        self.embedder = WikiEmbedder(cache_size=2048)  # Büyük cache (bazı sayfalarda 500+ link var)
        self.knowledge_graph = WikiKnowledgeGraph() if use_graph else None
        self.claude_reasoning = ClaudeReasoning(api_key=claude_api_key) if use_claude else None
        self.verbose = verbose
        self.use_graph = use_graph
        self.use_claude = use_claude

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

                # Çok fazla link varsa pre-filter yap (performans)
                if len(unvisited) > 100:
                    unvisited = unvisited[:100]  # İlk 100 link yeterli

                # Link'lerin similarity'lerini hesapla
                link_embs = self.embedder.get_embeddings_batch(unvisited)
                similarities = []
                for i, link_emb in enumerate(link_embs):
                    sim = self.embedder.cosine_similarity(target_emb, link_emb)
                    similarities.append((unvisited[i], sim))

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

        # 1. Graph'ta path var mı?
        if self.knowledge_graph:
            if self.verbose:
                print(f"🔍 Knowledge Graph kontrol ediliyor...")

            graph_path = self.knowledge_graph.find_path(start, target)

            if graph_path:
                if self.verbose:
                    print(f"✅ Graph'ta path bulundu!")
                    print(f"   Path: {' → '.join(graph_path)}")
                    print(f"   🎯 Öğrenilmiş bilgi kullanılıyor!\n")

                result = self._create_result(
                    True,
                    graph_path,
                    [],  # Graph'tan geldi, similarity yok
                    "Hybrid (Graph Reused)"
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

        # 2. Claude veya Beam Search
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
            # Beam Search (greedy'den daha robust)
            result = self.beam_search(
                start=start,
                target=target,
                beam_width=2,  # 2 alternatif yol
                max_depth=min(max_steps, 15)  # Max 15 depth
            )
            result.algorithm = "Hybrid (Beam Search)"

        # 3. Başarılıysa graph'a kaydet
        if result.found and self.knowledge_graph:
            self.knowledge_graph.add_path(result.path, success=True)
            self.knowledge_graph.save()

            if self.verbose:
                print(f"\n💾 Path graph'a kaydedildi!")

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
