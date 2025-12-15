"""
link_filter.py
--------------
Link'leri hızlı heuristic'lerle filtrele (embedding'den önce).

Amaç: 500+ link → 50-100 link (embedding computation %80-90 azalma)

v3.3.0: Wikipedia Categories integration
v3.3.1: Hierarchical category scoring (Phase 1)
"""

from typing import List, Tuple, Optional
import re


class LinkFilter:
    """
    Link'leri hızlı heuristic'lerle filtrele.
    
    Stratejiler:
    1. Kelime overlap (ortak kelimeler)
    2. Edit distance (benzer kelimeler)
    3. Length similarity (benzer uzunluk)
    4. Common prefixes/suffixes
    5. Category similarity
    6. ML-based scoring (NEW - Phase 2!)
    """
    
    def __init__(
        self,
        verbose: bool = False
    ):
        self.verbose = verbose
    
    def quick_filter(
        self,
        links: List[str],
        target: str,
        max_links: int = 100
    ) -> List[str]:
        """
        Link'leri hızlı heuristic'lerle filtrele.
        
        Parametreler:
            links: Tüm linkler (500+)
            target: Hedef sayfa
            max_links: Maksimum döndürülecek link sayısı
        
        Dönüş:
            Filtrelenmiş linkler (en iyi max_links tane)
        """
        if len(links) <= max_links:
            return links
        
        # Target'ı normalize et
        target_normalized = self._normalize(target)
        target_words = set(target_normalized.split('_'))
        
        # Her link için score hesapla
        scored_links = []
        for link in links:
            score = self._calculate_score(link, target, target_words)
            scored_links.append((link, score))
        
        # Score'a göre sırala (yüksekten düşüğe)
        scored_links.sort(key=lambda x: x[1], reverse=True)
        
        # En iyi max_links tanesini al
        filtered = [link for link, score in scored_links[:max_links]]
        
        if self.verbose:
            print(f"   🔍 Pre-filter: {len(links)} → {len(filtered)} links")
            if scored_links:
                print(f"      Top score: {scored_links[0][1]:.3f} ({scored_links[0][0]})")
        
        return filtered
    
    def _calculate_score(
        self,
        link: str,
        target: str,
        target_words: set
    ) -> float:
        """
        Link için heuristic score hesapla.
        
        Faktörler:
        1. Kelime overlap (0-1)
        2. Prefix/suffix match (0-0.5)
        3. Length similarity (0-0.3)
        4. Character overlap (0-0.2)
        """
        link_normalized = self._normalize(link)
        target_normalized = self._normalize(target)
        link_words = set(link_normalized.split('_'))
        
        # 1. Kelime overlap (en önemli!)
        word_overlap = len(target_words & link_words)
        word_overlap_score = min(word_overlap / max(len(target_words), 1), 1.0)
        
        # 2. Prefix/suffix match
        prefix_score = 0.0
        if link_normalized.startswith(target_normalized[:3]):
            prefix_score = 0.3
        if link_normalized.endswith(target_normalized[-3:]):
            prefix_score += 0.2
        
        # 3. Length similarity
        len_diff = abs(len(link_normalized) - len(target_normalized))
        length_score = max(0, 0.3 - (len_diff / 100))
        
        # 4. Character overlap (Jaccard similarity)
        link_chars = set(link_normalized)
        target_chars = set(target_normalized)
        char_overlap = len(link_chars & target_chars) / len(link_chars | target_chars)
        char_score = char_overlap * 0.2
        
        # Toplam score
        total_score = (
            word_overlap_score * 1.0 +  # En önemli
            prefix_score +
            length_score +
            char_score
        )
        
        return total_score
    
    def _normalize(self, text: str) -> str:
        """Text'i normalize et (lowercase, temizle)."""
        # Lowercase
        text = text.lower()
        
        # Parantez içini temizle
        text = re.sub(r'\([^)]*\)', '', text)
        
        # Özel karakterleri temizle
        text = re.sub(r'[^a-z0-9_]', '_', text)
        
        # Çoklu underscore'ları tek yap
        text = re.sub(r'_+', '_', text)
        
        # Baş/son underscore'ları temizle
        text = text.strip('_')
        
        return text
    
    def smart_filter(
        self,
        links: List[str],
        target: str,
        current_page: str,
        max_links: int = 100
    ) -> List[str]:
        """
        Daha akıllı filtreleme (context-aware + categories).
        
        Ek faktörler:
        - Current page ile target arasındaki ilişki
        - Hub sayfaları önceliklendir
        - Kategori sayfalarını filtrele
        - Category similarity (NEW!)
        """
        # Önce quick filter uygula
        filtered = self.quick_filter(links, target, max_links * 2)
        
        # Hub sayfaları (popüler sayfalar)
        hub_pages = {
            'United_States', 'United_Kingdom', 'Europe', 'Asia',
            'World_War_II', 'Computer', 'Science', 'History',
            'Geography', 'Mathematics', 'Physics', 'Chemistry',
            'Biology', 'Technology', 'Internet', 'Language'
        }
        
        # Score'ları yeniden hesapla (hub + category bonus ile)
        scored_links = []
        for link in filtered:
            base_score = self._calculate_score(link, target, set(self._normalize(target).split('_')))
            
            # Hub bonus
            if link in hub_pages:
                base_score *= 1.5
            
            # Category bonus removed in v5.0.0
            
            # Kategori/template sayfalarını cezalandır
            if link.startswith(('Category:', 'Template:', 'Wikipedia:', 'Help:')):
                base_score *= 0.1
            
            scored_links.append((link, base_score))
        
        # Yeniden sırala
        scored_links.sort(key=lambda x: x[1], reverse=True)
        
        # En iyi max_links tanesini al
        result = [link for link, score in scored_links[:max_links]]
        
        if self.verbose:
            print(f"   🧠 Smart filter: {len(filtered)} → {len(result)} links")
        
        return result
    
    def ml_filter(
        self,
        links: List[str],
        target: str,
        current_page: str,
        embedder,
        category_analyzer,
        knowledge_graph,
        max_links: int = 100
    ) -> List[str]:
        """
        ML-based filtering (Phase 2 - NEW!).
        
        Uses trained ML model to score and filter links.
        Falls back to smart_filter if ML not available.
        
        Args:
            links: All candidate links
            target: Target page
            current_page: Current page
            embedder: WikiEmbedder instance
            category_analyzer: WikipediaCategoryAnalyzer instance
            knowledge_graph: WikiKnowledgeGraph instance
            max_links: Maximum links to return
            
        Returns:
            Filtered links (best max_links)
        """
        # ML filter removed in v5.0.0 - use smart filter
        return self.smart_filter(links, target, current_page, max_links)
    
    def hybrid_filter(
        self,
        links: List[str],
        target: str,
        current_page: str,
        embedder=None,
        category_analyzer=None,
        knowledge_graph=None,
        max_links: int = 100,
        ml_weight: float = 0.7
    ) -> List[str]:
        """
        Hybrid filtering: Combine heuristic + ML scores.
        
        Best of both worlds:
        - Heuristic: Fast, always works
        - ML: Accurate, learns from data
        
        Args:
            links: All candidate links
            target: Target page
            current_page: Current page
            embedder: WikiEmbedder instance (optional for ML)
            category_analyzer: WikipediaCategoryAnalyzer instance (optional)
            knowledge_graph: WikiKnowledgeGraph instance (optional)
            max_links: Maximum links to return
            ml_weight: Weight for ML scores (0-1), heuristic gets (1-ml_weight)
            
        Returns:
            Filtered links (best max_links)
        """
        # Pre-filter with heuristics (limit to reasonable size)
        pre_filter_size = min(max_links * 2, 200)  # Max 200 links for ML
        pre_filtered = self.quick_filter(links, target, pre_filter_size)
        
        if self.verbose:
            print(f"   🔀 Hybrid filter: {len(links)} → {len(pre_filtered)} (pre-filter)")
        
        # Get heuristic scores
        target_words = set(self._normalize(target).split('_'))
        heuristic_scores = {}
        for link in pre_filtered:
            score = self._calculate_score(link, target, target_words)
            heuristic_scores[link] = score
        
        # ML scoring removed in v5.0.0
        ml_scores = {}
        ml_weight = 0.0
        
        # Combine scores
        combined_scores = []
        for link in pre_filtered:
            heur_score = heuristic_scores.get(link, 0.0)
            ml_score = ml_scores.get(link, 0.0)
            
            # Weighted combination
            if ml_weight > 0 and link in ml_scores:
                combined = ml_weight * ml_score + (1 - ml_weight) * heur_score
            else:
                combined = heur_score  # Heuristic only
            
            combined_scores.append((link, combined))
        
        # Sort by combined score
        combined_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Take top max_links
        result = [link for link, score in combined_scores[:max_links]]
        
        if self.verbose:
            print(f"   🔀 Hybrid filter: {len(pre_filtered)} → {len(result)} links")
            if combined_scores:
                print(f"      Top hybrid score: {combined_scores[0][1]:.3f} ({combined_scores[0][0]})")
        
        return result


# Removed: test_link_filter() - test function not needed in v5.0.0