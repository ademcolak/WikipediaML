"""
scraper.py
----------
Bu dosya Wikipedia sayfalarından veri çekmek için kullanılır.
İlk adım: Bir sayfanın HTML içeriğini almak.
"""

import requests  # HTTP istekleri yapmak için (GET, POST vs.)
from bs4 import BeautifulSoup  # HTML'i parse etmek (okumak/anlamak) için


class WikipediaScraper:
    """
    Wikipedia sayfalarını çeken ve işleyen sınıf.

    Neden class kullanıyoruz?
    - İleride birçok fonksiyon ekleyeceğiz (link çekme, filtreleme vs.)
    - Hepsini bir arada tutmak kodu organize eder
    - Base URL gibi ortak değişkenleri bir kere tanımlarız
    """

    def __init__(self):
        """
        Constructor - class'tan obje oluşturulduğunda çalışır.
        Temel ayarları burada yapıyoruz.
        """
        # Wikipedia'nın base URL'i - tüm sayfa linkleri bununla başlar
        self.base_url = "https://en.wikipedia.org/wiki/"

        # HTTP isteklerinde kendimizi tanıtıyoruz (bazı siteler bot'ları engeller)
        # User-Agent ile normal bir tarayıcı gibi görünüyoruz
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def get_page_html(self, page_title: str) -> BeautifulSoup | None:
        """
        Verilen Wikipedia sayfa başlığının HTML içeriğini çeker.

        Parametreler:
            page_title (str): Wikipedia sayfa başlığı, örn: "Potato" veya "Barack_Obama"
                              Boşluklar yerine _ kullanılır

        Dönüş:
            BeautifulSoup objesi (başarılı) veya None (başarısız)

        Örnek kullanım:
            scraper = WikipediaScraper()
            soup = scraper.get_page_html("Potato")
        """
        # Tam URL'i oluştur: https://en.wikipedia.org/wiki/Potato
        url = self.base_url + page_title

        try:
            # GET isteği gönder - sayfanın içeriğini iste
            # headers ile tarayıcı gibi görünüyoruz
            # timeout=10 ile 10 saniyede cevap gelmezse vazgeç
            response = requests.get(url, headers=self.headers, timeout=10)

            # HTTP durum kodunu kontrol et
            # 200 = Başarılı, 404 = Sayfa bulunamadı, 500 = Sunucu hatası vs.
            # raise_for_status() 200 dışında hata fırlatır
            response.raise_for_status()

            # HTML içeriğini BeautifulSoup ile parse et
            # 'html.parser' Python'un dahili HTML parser'ı
            soup = BeautifulSoup(response.text, 'html.parser')

            return soup

        except requests.exceptions.RequestException as e:
            # Herhangi bir hata olursa (bağlantı, timeout, 404 vs.)
            print(f"Hata oluştu: {e}")
            return None

    def get_wiki_links(self, soup: BeautifulSoup) -> list[str]:
        """
        Bir Wikipedia sayfasındaki tüm Wikipedia makale linklerini bulur.

        Parametreler:
            soup (BeautifulSoup): Daha önce çektiğimiz HTML objesi

        Dönüş:
            list[str]: Wikipedia makale başlıklarının listesi
                       Örn: ["United_States", "Vegetable", "Starch", ...]

        Nasıl çalışır:
            1. Sayfadaki tüm <a> (anchor/link) etiketlerini bul
            2. href="/wiki/..." olanları filtrele
            3. Özel sayfaları (File:, Help:, Wikipedia: vs.) çıkar
            4. Sadece makale isimlerini döndür
        """
        # Sonuçları tutacak liste
        wiki_links = []

        # Filtrelemek istediğimiz özel sayfalar
        # Bunlar Wikipedia'nın iç sayfaları, makale değiller
        excluded_prefixes = (
            "File:",  # Dosyalar (resimler vs.)
            "Help:",  # Yardım sayfaları
            "Wikipedia:",  # Wikipedia hakkında sayfalar
            "Template:",  # Şablon sayfaları
            "Category:",  # Kategori sayfaları
            "Special:",  # Özel sayfalar (arama vs.)
            "Talk:",  # Tartışma sayfaları
            "Portal:",  # Portal sayfaları
            "User:",  # Kullanıcı sayfaları
            "Module:",  # Modül sayfaları
        )

        # Sadece ana içerik alanındaki linkleri al
        # Wikipedia'da ana içerik "mw-content-text" id'li div içinde
        # Bu sayede menü, footer vs. linkleri almıyoruz
        content_div = soup.find('div', id='mw-content-text')

        if not content_div:
            print("İçerik alanı bulunamadı!")
            return []

        # Tüm <a> etiketlerini bul
        # <a href="/wiki/United_States">United States</a> gibi
        all_links = content_div.find_all('a', href=True)

        for link in all_links:
            href = link['href']  # href özelliğini al

            # Sadece /wiki/ ile başlayanları al
            # Dış linkler https:// ile başlar, bunları istemiyoruz
            if not href.startswith('/wiki/'):
                continue

            # /wiki/ kısmını kaldır, sadece makale adını al
            # "/wiki/United_States" -> "United_States"
            page_name = href[6:]  # İlk 6 karakter "/wiki/"

            # # işareti varsa atla (sayfa içi link, örn: "Potato#History")
            if '#' in page_name:
                continue

            # Özel sayfaları atla
            if page_name.startswith(excluded_prefixes):
                continue

            # Aynı linki tekrar ekleme (duplicate kontrolü)
            if page_name not in wiki_links:
                wiki_links.append(page_name)

        return wiki_links