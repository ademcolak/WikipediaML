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
from src.scraper import WikipediaScraper
from src.embedder import WikiEmbedder


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

    def __init__(self, verbose: bool = True):
        """
        SemanticNavigator'ı başlat.

        Parametreler:
            verbose (bool): Detaylı log çıktısı
        """
        self.scraper = WikipediaScraper(cache_size=256)
        self.embedder = WikiEmbedder(cache_size=2048)  # Büyük cache (bazı sayfalarda 500+ link var)
        self.verbose = verbose

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
                    score = result.similarity_scores[i-1]
                    print(f"  {i}. {page:<30} (sim: {score:.3f})")

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

    def get_stats(self) -> dict:
        """Tüm statistics'i döndür."""
        return {
            'scraper': self.scraper.get_cache_stats(),
            'embedder': self.embedder.get_cache_stats()
        }
