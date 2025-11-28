"""
navigator.py
------------
Wikipedia sayfaları arasında gezinmeyi sağlar.
Scraper'ı kullanarak sayfa sayfa ilerler.
"""

import random  # Rastgele seçim için
import time  # Bekleme süresi için (Wikipedia'yı spam'lememek için)

from src.scraper import WikipediaScraper


class WikiNavigator:
    """
    Wikipedia sayfaları arasında gezinen sınıf.

    Bu sınıf:
    - Bir başlangıç sayfasından başlar
    - Hedefe ulaşana kadar linkler arasında gezinir
    - Gezdiği yolu (path) kaydeder
    """

    def __init__(self):
        """
        Navigator'ı başlat.
        Scraper'ı burada oluşturuyoruz çünkü her gezinti için kullanacağız.
        """
        self.scraper = WikipediaScraper()

        # Gezdiğimiz sayfaları tutacak liste
        # Örn: ["Potato", "Vegetable", "Food", "Human"]
        self.path = []

        # Daha önce ziyaret ettiğimiz sayfalar (döngüye girmemek için)
        # Set kullanıyoruz çünkü arama O(1) - çok hızlı
        self.visited = set()

    def reset(self):
        """
        Yeni bir gezinti başlatmadan önce eski verileri temizle.
        """
        self.path = []
        self.visited = set()

    def random_walk(self, start: str, max_steps: int = 10) -> list[str]:
        """
        Rastgele linkler seçerek gezin.

        Bu fonksiyon henüz hedefe gitmiyor, sadece rastgele dolaşıyor.
        Amacı: Sistemin çalıştığını test etmek.

        Parametreler:
            start (str): Başlangıç sayfası, örn: "Potato"
            max_steps (int): Maksimum adım sayısı

        Dönüş:
            list[str]: Gezilen sayfaların listesi
        """
        # Önceki gezintiyi temizle
        self.reset()

        # Mevcut sayfa
        current_page = start

        print(f"🚀 Başlangıç: {current_page}")
        print("=" * 50)

        for step in range(max_steps):
            # Bu sayfayı ziyaret ettik olarak işaretle
            self.visited.add(current_page)
            self.path.append(current_page)

            # Sayfanın HTML'ini çek
            soup = self.scraper.get_page_html(current_page)

            if not soup:
                print(f"❌ Sayfa çekilemedi: {current_page}")
                break

            # Sayfadaki linkleri al
            links = self.scraper.get_wiki_links(soup)

            if not links:
                print(f"❌ Link bulunamadı: {current_page}")
                break

            # Daha önce ziyaret etmediğimiz linkleri filtrele
            # Böylece aynı sayfalarda dönmeyiz
            unvisited_links = [link for link in links if link not in self.visited]

            if not unvisited_links:
                print(f"⚠️ Tüm linkler zaten ziyaret edilmiş!")
                break

            # Rastgele bir link seç
            next_page = random.choice(unvisited_links)

            print(f"  Adım {step + 1}: {current_page} → {next_page}")

            # Bir sonraki sayfaya geç
            current_page = next_page

            # Wikipedia'yı spam'lememek için kısa bir bekleme
            # Bu önemli - çok hızlı istek atarsan IP'ni engelleyebilirler
            time.sleep(0.5)

        # Son sayfayı da ekle
        if current_page not in self.path:
            self.path.append(current_page)

        print("=" * 50)
        print(f"✅ Toplam {len(self.path)} sayfa gezildi")

        return self.path