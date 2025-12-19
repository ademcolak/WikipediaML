#!/usr/bin/env python3
"""
create_dataset.py
-----------------
Benchmark için test dataset oluştur.

Özellikler:
- Popüler Wikipedia sayfaları
- Random sayfalar
- Zorluk kategorileri (kolay, orta, zor)
- Test pair'leri oluştur

Kullanım:
    python benchmark/create_dataset.py --count 500
    python benchmark/create_dataset.py --count 100 --difficulty easy
"""

import argparse
import json
import random
import requests
from pathlib import Path
from typing import List, Tuple
import time


class DatasetCreator:
    """Benchmark dataset oluşturucu."""
    
    def __init__(self):
        self.base_url = "https://en.wikipedia.org/w/api.php"
        self.session = requests.Session()
        # User-Agent ekle (Wikipedia bunu gerektirir)
        self.session.headers.update({
            'User-Agent': 'WikipediaML-Benchmark/1.0 (Educational Project; Python/requests)'
        })
        
    def fetch_popular_pages(self, count: int = 100) -> List[str]:
        """
        Popüler Wikipedia sayfalarını getir.
        
        Wikipedia'nın "Most viewed pages" listesini kullanır.
        """
        print(f"\n📊 {count} popüler sayfa getiriliyor...")
        
        # Wikipedia'nın popüler kategorilerinden sayfalar al
        popular_categories = [
            "Science",
            "Technology",
            "History",
            "Geography",
            "Mathematics",
            "Physics",
            "Biology",
            "Chemistry",
            "Computer_science",
            "Philosophy",
            "Literature",
            "Art",
            "Music",
            "Sports",
            "Politics"
        ]
        
        pages = []
        pages_per_category = count // len(popular_categories) + 1
        
        for category in popular_categories:
            if len(pages) >= count:
                break
                
            try:
                # Kategoriden sayfalar al
                params = {
                    "action": "query",
                    "format": "json",
                    "list": "categorymembers",
                    "cmtitle": f"Category:{category}",
                    "cmlimit": pages_per_category,
                    "cmtype": "page"
                }
                
                response = self.session.get(self.base_url, params=params, timeout=10)
                response.raise_for_status()
                
                # Check if response has content
                if not response.text:
                    print(f"⚠️  {category}: Boş response")
                    continue
                
                data = response.json()
                
                if "query" in data and "categorymembers" in data["query"]:
                    for page in data["query"]["categorymembers"]:
                        title = page["title"]
                        # Meta sayfaları filtrele
                        if not any(prefix in title for prefix in ["Wikipedia:", "Category:", "Template:", "Help:", "File:"]):
                            pages.append(title)
                            if len(pages) >= count:
                                break
                
                time.sleep(0.5)  # Rate limiting (daha yavaş)
                
            except Exception as e:
                print(f"⚠️  {category} kategorisi alınamadı: {e}")
                continue
        
        print(f"✅ {len(pages)} popüler sayfa alındı")
        return pages[:count]
    
    def fetch_random_pages(self, count: int = 100) -> List[str]:
        """
        Random Wikipedia sayfalarını getir.
        
        Wikipedia'nın random page API'sini kullanır.
        """
        print(f"\n🎲 {count} random sayfa getiriliyor...")
        
        pages = []
        batch_size = 10  # Her seferde 10 sayfa al
        
        while len(pages) < count:
            try:
                params = {
                    "action": "query",
                    "format": "json",
                    "list": "random",
                    "rnnamespace": 0,  # Sadece article namespace
                    "rnlimit": min(batch_size, count - len(pages))
                }
                
                response = self.session.get(self.base_url, params=params, timeout=10)
                response.raise_for_status()
                
                # Check if response has content
                if not response.text:
                    print(f"⚠️  Boş response, tekrar deneniyor...")
                    time.sleep(1)
                    continue
                
                data = response.json()
                
                if "query" in data and "random" in data["query"]:
                    for page in data["query"]["random"]:
                        title = page["title"]
                        # Meta sayfaları filtrele
                        if not any(prefix in title for prefix in ["Wikipedia:", "Category:", "Template:", "Help:", "File:"]):
                            pages.append(title)
                
                time.sleep(0.5)  # Rate limiting (daha yavaş)
                
            except Exception as e:
                print(f"⚠️  Random sayfalar alınamadı: {e}")
                time.sleep(1)
                continue
        
        print(f"✅ {len(pages)} random sayfa alındı")
        return pages[:count]
    
    def create_test_pairs(
        self,
        popular_pages: List[str],
        random_pages: List[str],
        count: int = 500,
        difficulty: str = "mixed"
    ) -> List[Tuple[str, str, str]]:
        """
        Test pair'leri oluştur.
        
        Parametreler:
            popular_pages: Popüler sayfalar listesi
            random_pages: Random sayfalar listesi
            count: Oluşturulacak pair sayısı
            difficulty: "easy", "medium", "hard", "mixed"
        
        Dönüş:
            List of (start, target, difficulty)
        """
        print(f"\n🎯 {count} test pair oluşturuluyor (difficulty: {difficulty})...")
        
        pairs = []
        
        if difficulty == "mixed":
            # %40 easy, %40 medium, %20 hard
            easy_count = int(count * 0.4)
            medium_count = int(count * 0.4)
            hard_count = count - easy_count - medium_count
            
            pairs.extend(self._create_pairs_by_difficulty(popular_pages, random_pages, easy_count, "easy"))
            pairs.extend(self._create_pairs_by_difficulty(popular_pages, random_pages, medium_count, "medium"))
            pairs.extend(self._create_pairs_by_difficulty(popular_pages, random_pages, hard_count, "hard"))
        else:
            pairs = self._create_pairs_by_difficulty(popular_pages, random_pages, count, difficulty)
        
        # Shuffle
        random.shuffle(pairs)
        
        print(f"✅ {len(pairs)} test pair oluşturuldu")
        return pairs
    
    def _create_pairs_by_difficulty(
        self,
        popular_pages: List[str],
        random_pages: List[str],
        count: int,
        difficulty: str
    ) -> List[Tuple[str, str, str]]:
        """Belirli zorlukta pair'ler oluştur."""
        pairs = []
        
        for _ in range(count):
            if difficulty == "easy":
                # Popüler → Popüler (kolay, çünkü iyi bağlantılı)
                start = random.choice(popular_pages)
                target = random.choice(popular_pages)
            elif difficulty == "medium":
                # Popüler → Random veya Random → Popüler
                if random.random() < 0.5:
                    start = random.choice(popular_pages)
                    target = random.choice(random_pages)
                else:
                    start = random.choice(random_pages)
                    target = random.choice(popular_pages)
            else:  # hard
                # Random → Random (zor, az bağlantılı)
                start = random.choice(random_pages)
                target = random.choice(random_pages)
            
            # Aynı sayfa olmasın
            if start != target:
                pairs.append((start, target, difficulty))
        
        return pairs
    
    def save_dataset(self, pairs: List[Tuple[str, str, str]], output_file: str):
        """Dataset'i JSON olarak kaydet."""
        print(f"\n💾 Dataset kaydediliyor: {output_file}")
        
        # Format: list of dicts
        dataset = []
        for i, (start, target, difficulty) in enumerate(pairs):
            dataset.append({
                "id": i + 1,
                "start": start,
                "target": target,
                "difficulty": difficulty
            })
        
        # Kaydet
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Dataset kaydedildi: {len(dataset)} test pair")
        
        # İstatistikler
        easy_count = sum(1 for p in dataset if p["difficulty"] == "easy")
        medium_count = sum(1 for p in dataset if p["difficulty"] == "medium")
        hard_count = sum(1 for p in dataset if p["difficulty"] == "hard")
        
        print(f"\n📊 Dataset İstatistikleri:")
        print(f"   Kolay: {easy_count} (%{easy_count/len(dataset)*100:.1f})")
        print(f"   Orta: {medium_count} (%{medium_count/len(dataset)*100:.1f})")
        print(f"   Zor: {hard_count} (%{hard_count/len(dataset)*100:.1f})")


def main():
    """Ana fonksiyon."""
    parser = argparse.ArgumentParser(description='Benchmark Dataset Oluştur')
    parser.add_argument('--count', type=int, default=500, help='Test pair sayısı (default: 500)')
    parser.add_argument('--difficulty', type=str, default='mixed',
                       choices=['easy', 'medium', 'hard', 'mixed'],
                       help='Zorluk seviyesi (default: mixed)')
    parser.add_argument('--output', type=str, default='benchmark/test_dataset.json',
                       help='Çıktı dosyası (default: benchmark/test_dataset.json)')
    parser.add_argument('--popular-count', type=int, default=200,
                       help='Popüler sayfa sayısı (default: 200)')
    parser.add_argument('--random-count', type=int, default=300,
                       help='Random sayfa sayısı (default: 300)')
    
    args = parser.parse_args()
    
    print("="*70)
    print("🎯 BENCHMARK DATASET OLUŞTURUCU")
    print("="*70)
    
    # Creator oluştur
    creator = DatasetCreator()
    
    # Sayfaları getir
    popular_pages = creator.fetch_popular_pages(args.popular_count)
    random_pages = creator.fetch_random_pages(args.random_count)
    
    # Test pair'leri oluştur
    pairs = creator.create_test_pairs(
        popular_pages,
        random_pages,
        args.count,
        args.difficulty
    )
    
    # Kaydet
    creator.save_dataset(pairs, args.output)
    
    print("\n" + "="*70)
    print("✅ DATASET OLUŞTURMA TAMAMLANDI")
    print("="*70)
    print(f"\n💡 Kullanım:")
    print(f"   python benchmark/run_benchmark.py --dataset {args.output}")


if __name__ == "__main__":
    main()