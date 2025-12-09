"""
scraper.py
----------
Bu dosya Wikipedia sayfalarından veri çekmek için kullanılır.
Caching ile performans optimizasyonu yapılmıştır.
"""

import requests
from bs4 import BeautifulSoup, Tag
from functools import lru_cache


class WikipediaScraper:
    """
    Wikipedia sayfalarını çeken ve işleyen sınıf.

    Features:
    - HTML fetching ve parsing
    - Link extraction
    - LRU Cache (sık kullanılan sayfaları tekrar çekmez)
    - Cache statistics
    """

    def __init__(self, cache_size: int = 128, timeout: int = 10):
        """
        WikipediaScraper'ı başlat.

        Parametreler:
            cache_size (int): Cache'lenecek maksimum sayfa sayısı
                             Default: 128 (LRU - en az kullanılan silinir)
            timeout (int): HTTP request timeout (saniye)
                          Default: 10
        """
        self.base_url = "https://en.wikipedia.org/wiki/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.timeout = timeout

        # Cache statistics
        self.cache_hits = 0
        self.cache_misses = 0

        # Cache için functools.lru_cache kullanmak yerine manual cache yapıyoruz
        # Çünkü class method'larında lru_cache kullanmak zor
        # Basit dict cache (LRU için collections.OrderedDict kullanabiliriz)
        from collections import OrderedDict
        self._cache = OrderedDict()
        self._cache_size = cache_size

    def get_page_html(self, page_title: str) -> BeautifulSoup | None:
        """
        Verilen Wikipedia sayfa başlığının HTML içeriğini çeker.
        Cache'de varsa direkt döndürür (network call yapmaz).

        Parametreler:
            page_title (str): Wikipedia sayfa başlığı, örn: "Potato"

        Dönüş:
            BeautifulSoup objesi (başarılı) veya None (başarısız)

        Cache Mantığı:
            1. Cache'de var mı kontrol et → Varsa döndür (CACHE HIT)
            2. Yoksa Wikipedia'dan çek → Cache'e ekle → Döndür (CACHE MISS)
            3. Cache doluysa → En eski entry'yi sil (LRU)
        """
        # Cache'de var mı kontrol et
        if page_title in self._cache:
            self.cache_hits += 1
            # Cache hit: Mevcut entry'yi en sona taşı (recently used)
            self._cache.move_to_end(page_title)
            return self._cache[page_title]

        # Cache miss: Wikipedia'dan çek
        self.cache_misses += 1
        soup = self._fetch_from_wikipedia(page_title)

        if soup:
            # Cache'e ekle
            self._add_to_cache(page_title, soup)

        return soup

    def _fetch_from_wikipedia(self, page_title: str) -> BeautifulSoup | None:
        """
        Wikipedia'dan sayfa HTML'ini çeker (network call).

        Bu metod sadece cache miss durumunda çağrılır.
        """
        url = self.base_url + page_title

        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup

        except requests.exceptions.RequestException as e:
            print(f"❌ Hata ({page_title}): {e}")
            return None

    def _add_to_cache(self, page_title: str, soup: BeautifulSoup):
        """
        Sayfayı cache'e ekler. Cache doluysa en eski entry'yi siler (LRU).
        """
        # Cache dolu mu kontrol et
        if len(self._cache) >= self._cache_size:
            # En eski entry'yi sil (FIFO - first in first out)
            self._cache.popitem(last=False)

        # Yeni entry'yi ekle (en sona)
        self._cache[page_title] = soup

    def clear_cache(self):
        """Cache'i temizle ve statistics'i sıfırla."""
        self._cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0

    def get_cache_stats(self) -> dict:
        """
        Cache istatistiklerini döndür.

        Returns:
            dict: {
                'size': Mevcut cache boyutu,
                'max_size': Maksimum cache boyutu,
                'hits': Cache hit sayısı,
                'misses': Cache miss sayısı,
                'hit_rate': Hit rate (%)
            }
        """
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0

        return {
            'size': len(self._cache),
            'max_size': self._cache_size,
            'hits': self.cache_hits,
            'misses': self.cache_misses,
            'hit_rate': hit_rate
        }

    def get_wiki_links(self, soup: BeautifulSoup) -> list[str]:
        """
        Bir Wikipedia sayfasındaki tüm makale linklerini bulur.

        Parametreler:
            soup (BeautifulSoup): HTML objesi

        Dönüş:
            list[str]: Wikipedia makale başlıkları
                      Örn: ["United_States", "Vegetable", ...]

        Filtreleme:
            - Sadece /wiki/ ile başlayan linkler
            - Özel sayfalar hariç (File:, Help:, Template: vs.)
            - Sayfa içi linkler hariç (#anchor)
            - Duplicate'ler hariç
        """
        wiki_links = []

        # Wikipedia'nın özel sayfaları (makale değil)
        excluded_prefixes = (
            "File:", "Help:", "Wikipedia:", "Template:",
            "Category:", "Special:", "Talk:", "Portal:",
            "User:", "Module:",
        )

        # Ana içerik alanını bul (menü/footer hariç)
        content_div = soup.find('div', id='mw-content-text')
        if not content_div or not isinstance(content_div, Tag):
            return []

        # Tüm linkleri bul ve filtrele
        for link in content_div.find_all('a', href=True):
            href = link['href']

            # Sadece Wikipedia makale linkleri
            if not href.startswith('/wiki/'):
                continue

            # "/wiki/" kısmını kaldır
            page_name = href[6:]

            # Filtreleme: anchor linkler, özel sayfalar, duplicate'ler
            if ('#' in page_name or
                page_name.startswith(excluded_prefixes) or
                page_name in wiki_links):
                continue

            wiki_links.append(page_name)

        return wiki_links