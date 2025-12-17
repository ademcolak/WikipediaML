"""
training_strategies.py
----------------------
Farklı eğitim stratejileri - TrainingPipeline'dan türetilmiş.

Stratejiler:
    - StrategicTraining: Popüler sayfalar arası
    - RandomTraining: Rastgele Wikipedia sayfaları
    - CustomTraining: Özel sayfa listesi
"""

import random
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple

from src.training_pipeline import TrainingPipeline, TrainingConfig


# Popüler Wikipedia sayfaları
POPULAR_PAGES = [
    # Ülkeler
    "United_States", "China", "India", "United_Kingdom", "Germany",
    "France", "Italy", "Spain", "Japan", "Russia",
    
    # Şehirler
    "New_York_City", "London", "Paris", "Tokyo", "Beijing",
    "Los_Angeles", "Chicago", "Berlin", "Rome", "Madrid",
    
    # Bilim
    "Physics", "Chemistry", "Biology", "Mathematics", "Computer_science",
    "Medicine", "Engineering", "Astronomy", "Psychology", "Economics",
    
    # Teknoloji
    "Computer", "Internet", "Artificial_intelligence", "Machine_learning",
    "Programming", "Software", "Hardware", "Database", "Algorithm",
    
    # Tarih
    "World_War_II", "Ancient_Rome", "Ancient_Greece", "Middle_Ages",
    "Renaissance", "Industrial_Revolution", "Cold_War",
    
    # Kültür
    "Music", "Art", "Literature", "Film", "Philosophy",
    "Religion", "Language", "Culture", "History", "Science"
]


class StrategicTraining(TrainingPipeline):
    """
    Stratejik eğitim - Popüler sayfalar arası path'leri öğrenir.
    
    Avantajlar:
        - Sık kullanılan path'leri öğrenir
        - Daha yüksek hit rate
        - Kullanıcılar genelde popüler sayfalar arar
    
    Kullanım:
        config = TrainingConfig(worker_id=1, num_iterations=100)
        pipeline = StrategicTraining(config)
        pipeline.run()
    """
    
    def _get_next_pair(self, iteration: int) -> Tuple[str, str]:
        """Popüler sayfalardan rastgele 2 sayfa seç."""
        pages = random.sample(POPULAR_PAGES, 2)
        return (pages[0], pages[1])


class RandomTraining(TrainingPipeline):
    """
    Rastgele eğitim - Wikipedia'dan tamamen rastgele sayfalar.
    
    Avantajlar:
        - Çok fazla çeşitlilik
        - Tüm Wikipedia'yı kapsar
        - Nadir path'leri de öğrenir
    
    Kullanım:
        config = TrainingConfig(worker_id=1, num_iterations=100)
        pipeline = RandomTraining(config)
        pipeline.run()
    """
    
    def __init__(self, config: TrainingConfig):
        super().__init__(config)
        self._page_cache: List[str] = []
    
    def _get_next_pair(self, iteration: int) -> Tuple[str, str]:
        """Wikipedia'dan rastgele 2 sayfa çek."""
        # Cache'de yeterli sayfa yoksa yeni çek
        if len(self._page_cache) < 2:
            self._page_cache = self._fetch_random_pages(count=10)
        
        # Cache'den 2 sayfa al
        if len(self._page_cache) >= 2:
            start = self._page_cache.pop(0)
            target = self._page_cache.pop(0)
            return start, target
        else:
            # Fallback: Popüler sayfalardan seç
            pages = random.sample(POPULAR_PAGES, 2)
            return (pages[0], pages[1])
    
    def _fetch_random_pages(self, count: int = 10, max_attempts: int = 50) -> List[str]:
        """
        Wikipedia'dan rastgele sayfalar çek.
        
        Args:
            count: Kaç sayfa çekilecek
            max_attempts: Maksimum deneme sayısı
            
        Returns:
            Sayfa listesi
        """
        pages = []
        
        def fetch_one():
            """Tek bir rastgele sayfa çek."""
            try:
                response = requests.get(
                    'https://en.wikipedia.org/wiki/Special:Random',
                    timeout=3,
                    allow_redirects=True,
                    headers={'User-Agent': 'WikipediaML/1.0'}
                )
                
                if response.status_code == 200:
                    page_title = response.url.split('/wiki/')[-1]
                    
                    # Özel sayfaları filtrele
                    if (not page_title.startswith(('Special:', 'Wikipedia:', 'Help:',
                                                   'Category:', 'Template:', 'File:',
                                                   'Talk:', 'User:', 'Portal:', 'Draft:'))
                        and len(page_title) > 2
                        and ':' not in page_title):
                        return page_title
            except:
                pass
            return None
        
        # Paralel olarak sayfaları çek
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(fetch_one) for _ in range(max_attempts)]
            
            for future in as_completed(futures):
                result = future.result()
                if result and result not in pages:
                    pages.append(result)
                    if len(pages) >= count:
                        break
        
        return pages


class CustomTraining(TrainingPipeline):
    """
    Özel eğitim - Kullanıcı tarafından belirlenen sayfa listesi.
    
    Kullanım:
        pairs = [
            ("Potato", "Pizza"),
            ("Italy", "Rome"),
            ("Physics", "Albert_Einstein")
        ]
        config = TrainingConfig(worker_id=1, num_iterations=len(pairs))
        pipeline = CustomTraining(config, pairs)
        pipeline.run()
    """
    
    def __init__(self, config: TrainingConfig, pairs: List[Tuple[str, str]]):
        """
        Özel eğitim pipeline'ı.
        
        Args:
            config: Eğitim konfigürasyonu
            pairs: (start, target) çiftleri listesi
        """
        super().__init__(config)
        self.pairs = pairs
        
        # Iteration sayısını pair sayısına eşitle
        self.config.num_iterations = len(pairs)
    
    def _get_next_pair(self, iteration: int) -> Tuple[str, str]:
        """Listeden sıradaki çifti döndür."""
        if iteration < len(self.pairs):
            return self.pairs[iteration]
        else:
            # Fallback: Popüler sayfalardan seç
            pages = random.sample(POPULAR_PAGES, 2)
            return (pages[0], pages[1])


class HybridTraining(TrainingPipeline):
    """
    Hibrit eğitim - Stratejik + Rastgele karışımı.
    
    %70 stratejik (popüler), %30 rastgele (çeşitlilik)
    
    Kullanım:
        config = TrainingConfig(worker_id=1, num_iterations=100)
        pipeline = HybridTraining(config, strategic_ratio=0.7)
        pipeline.run()
    """
    
    def __init__(self, config: TrainingConfig, strategic_ratio: float = 0.7):
        """
        Hibrit eğitim pipeline'ı.
        
        Args:
            config: Eğitim konfigürasyonu
            strategic_ratio: Stratejik eğitim oranı (0.0-1.0)
        """
        super().__init__(config)
        self.strategic_ratio = strategic_ratio
        self._random_trainer = RandomTraining(config)
    
    def _get_next_pair(self, iteration: int) -> Tuple[str, str]:
        """Stratejik veya rastgele seç (oran'a göre)."""
        if random.random() < self.strategic_ratio:
            # Stratejik: Popüler sayfalar
            pages = random.sample(POPULAR_PAGES, 2)
            return (pages[0], pages[1])
        else:
            # Rastgele: Wikipedia'dan çek
            return self._random_trainer._get_next_pair(iteration)