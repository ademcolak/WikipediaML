"""
link_filter.py
--------------
Link'leri hızlı heuristic'lerle filtrele (embedding'den önce).

Amaç: 500+ link → 50-100 link (embedding computation %80-90 azalma)

v3.3.0: Wikipedia Categories integration
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
    5. Category similarity (NEW!)
    """
    
    def __init__(self, verbose: bool = False, use_categories: bool = True):
        self.verbose = verbose
        self.use_categories = use_categories
        
        # Category analyzer (lazy loading)
        self._category_analyzer = None
    
    @property
    def category_analyzer(self):
        """Lazy load category analyzer."""
        if self._category_analyzer is None and self.use_categories:
            from src.category_analyzer import WikipediaCategoryAnalyzer
            self._category_analyzer = WikipediaCategoryAnalyzer(verbose=False)
        return self._category_analyzer
    
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
            
            # Category bonus (NEW!)
            if self.use_categories and self.category_analyzer:
                try:
                    category_sim = self.category_analyzer.category_similarity(link, target)
                    # Category bonus: 0.0-0.3 ek puan
                    base_score += category_sim * 0.3
                except:
                    pass  # Category fetch hatası, devam et
            
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


def test_link_filter():
    """Test fonksiyonu."""
    filter = LinkFilter(verbose=True)
    
    # Test 1: Basit kelime overlap
    links = [
        "United_States",
        "U.S._Route_111",
        "United_Kingdom",
        "Random_Page",
        "Another_Random",
        "U.S._History"
    ]
    target = "U.S._Route_111"
    
    print("\n" + "="*60)
    print("Test 1: Kelime Overlap")
    print("="*60)
    filtered = filter.quick_filter(links, target, max_links=3)
    print(f"Filtered: {filtered}")
    
    # Test 2: Çok fazla link
    links = [f"Page_{i}" for i in range(500)]
    links.extend(["United_States", "U.S._Route", "Route_111"])
    target = "U.S._Route_111"
    
    print("\n" + "="*60)
    print("Test 2: Çok Fazla Link")
    print("="*60)
    filtered = filter.quick_filter(links, target, max_links=10)
    print(f"Top 10: {filtered[:10]}")


if __name__ == "__main__":
    test_link_filter()