#!/usr/bin/env python3
"""
generate_large_dataset.py
-------------------------
Generate large curated dataset for ML training.

Bu script:
- Wikipedia kategorilerinden otomatik dataset üretir
- 500+ page çifti oluşturur
- Kolay → orta → zor zorluk seviyeleri
- Kategori bazlı ilişkili page'ler seçer

Usage:
    # 500 çift üret
    python generate_large_dataset.py --count 500
    
    # 1000 çift üret
    python generate_large_dataset.py --count 1000
    
    # Mevcut dataset'e ekle
    python generate_large_dataset.py --count 500 --append
"""

import json
import argparse
from typing import List, Dict, Tuple
import random


# Wikipedia kategorileri ve popüler page'ler
CATEGORIES = {
    "science": {
        "hubs": ["Science", "Physics", "Chemistry", "Biology", "Mathematics"],
        "pages": [
            "Albert_Einstein", "Isaac_Newton", "Marie_Curie", "Charles_Darwin",
            "Galileo_Galilei", "Stephen_Hawking", "Richard_Feynman", "Niels_Bohr",
            "Quantum_mechanics", "Theory_of_relativity", "Evolution", "DNA",
            "Atom", "Molecule", "Cell_(biology)", "Photosynthesis", "Gravity",
            "Electromagnetism", "Thermodynamics", "Periodic_table", "Genetics",
            "Astronomy", "Cosmology", "Particle_physics", "Nuclear_physics"
        ]
    },
    "technology": {
        "hubs": ["Technology", "Computer", "Internet", "Software", "Programming"],
        "pages": [
            "Computer", "Internet", "Artificial_intelligence", "Machine_learning",
            "Python_(programming_language)", "Java_(programming_language)", "JavaScript",
            "Computer_science", "Algorithm", "Data_structure", "Database",
            "Operating_system", "Linux", "Microsoft_Windows", "MacOS",
            "Smartphone", "iPhone", "Android_(operating_system)", "Google",
            "Apple_Inc.", "Microsoft", "Facebook", "Amazon_(company)",
            "Cloud_computing", "Blockchain", "Cryptocurrency", "Bitcoin"
        ]
    },
    "geography": {
        "hubs": ["Geography", "Country", "City", "Continent", "Ocean"],
        "pages": [
            "Earth", "Europe", "Asia", "Africa", "North_America", "South_America",
            "United_States", "China", "India", "Russia", "Germany", "France",
            "United_Kingdom", "Italy", "Spain", "Japan", "Brazil", "Canada",
            "Australia", "New_York_City", "London", "Paris", "Tokyo", "Beijing",
            "Rome", "Berlin", "Madrid", "Moscow", "Sydney", "Los_Angeles"
        ]
    },
    "history": {
        "hubs": ["History", "War", "Empire", "Revolution", "Ancient_history"],
        "pages": [
            "World_War_II", "World_War_I", "Ancient_Rome", "Ancient_Greece",
            "Ancient_Egypt", "Roman_Empire", "Byzantine_Empire", "Ottoman_Empire",
            "French_Revolution", "American_Revolution", "Industrial_Revolution",
            "Renaissance", "Middle_Ages", "Cold_War", "Napoleon", "Julius_Caesar",
            "Alexander_the_Great", "Genghis_Khan", "Adolf_Hitler", "Winston_Churchill"
        ]
    },
    "culture": {
        "hubs": ["Culture", "Art", "Music", "Literature", "Film"],
        "pages": [
            "Art", "Music", "Literature", "Film", "Theatre", "Dance", "Painting",
            "Sculpture", "Architecture", "Leonardo_da_Vinci", "Michelangelo",
            "Pablo_Picasso", "Vincent_van_Gogh", "William_Shakespeare", "Mozart",
            "Beethoven", "Bach", "The_Beatles", "Elvis_Presley", "Michael_Jackson",
            "Cinema", "Hollywood", "Academy_Awards", "Nobel_Prize"
        ]
    },
    "sports": {
        "hubs": ["Sport", "Football", "Basketball", "Tennis", "Olympic_Games"],
        "pages": [
            "Football", "Basketball", "Tennis", "Cricket", "Baseball", "Golf",
            "Olympic_Games", "FIFA_World_Cup", "UEFA_Champions_League", "NBA",
            "NFL", "Premier_League", "La_Liga", "Serie_A", "Bundesliga",
            "Lionel_Messi", "Cristiano_Ronaldo", "Michael_Jordan", "Muhammad_Ali",
            "Usain_Bolt", "Roger_Federer", "Serena_Williams", "Tiger_Woods"
        ]
    },
    "food": {
        "hubs": ["Food", "Cuisine", "Cooking", "Restaurant", "Beverage"],
        "pages": [
            "Pizza", "Pasta", "Sushi", "Hamburger", "Bread", "Rice", "Cheese",
            "Italian_cuisine", "French_cuisine", "Chinese_cuisine", "Japanese_cuisine",
            "Indian_cuisine", "Mexican_cuisine", "Coffee", "Tea", "Wine", "Beer",
            "Chocolate", "Ice_cream", "Cake", "Restaurant", "Fast_food", "Vegetarianism"
        ]
    },
    "animals": {
        "hubs": ["Animal", "Mammal", "Bird", "Fish", "Reptile"],
        "pages": [
            "Dog", "Cat", "Lion", "Tiger", "Elephant", "Bear", "Wolf", "Fox",
            "Horse", "Cow", "Pig", "Sheep", "Chicken", "Eagle", "Owl", "Penguin",
            "Dolphin", "Whale", "Shark", "Snake", "Crocodile", "Turtle", "Frog"
        ]
    },
    "politics": {
        "hubs": ["Politics", "Government", "Democracy", "President", "Parliament"],
        "pages": [
            "Politics", "Democracy", "Republic", "Monarchy", "Communism", "Socialism",
            "Capitalism", "Government", "President", "Prime_minister", "Parliament",
            "United_Nations", "European_Union", "NATO", "Constitution", "Law",
            "Human_rights", "Election", "Political_party", "Diplomacy"
        ]
    },
    "nature": {
        "hubs": ["Nature", "Environment", "Climate", "Ecosystem", "Conservation"],
        "pages": [
            "Nature", "Environment", "Climate_change", "Global_warming", "Ecosystem",
            "Forest", "Ocean", "Mountain", "River", "Lake", "Desert", "Rainforest",
            "Biodiversity", "Conservation", "Endangered_species", "National_park",
            "Weather", "Season", "Rain", "Snow", "Wind", "Earthquake", "Volcano"
        ]
    }
}


def generate_pairs_from_category(category: str, data: Dict, count: int) -> List[Dict]:
    """Generate page pairs from a category."""
    pairs = []
    hubs = data["hubs"]
    pages = data["pages"]
    
    # Type 1: Page → Hub (easy)
    for _ in range(count // 3):
        page = random.choice(pages)
        hub = random.choice(hubs)
        pairs.append({
            "start": page,
            "target": hub,
            "difficulty": "easy",
            "category": category
        })
    
    # Type 2: Page → Page (same category, medium)
    for _ in range(count // 3):
        page1, page2 = random.sample(pages, 2)
        pairs.append({
            "start": page1,
            "target": page2,
            "difficulty": "medium",
            "category": category
        })
    
    # Type 3: Hub → Hub (easy)
    for _ in range(count // 3):
        hub1, hub2 = random.sample(hubs, 2)
        pairs.append({
            "start": hub1,
            "target": hub2,
            "difficulty": "easy",
            "category": category
        })
    
    return pairs


def generate_cross_category_pairs(count: int) -> List[Dict]:
    """Generate pairs across different categories (harder)."""
    pairs = []
    categories = list(CATEGORIES.keys())
    
    for _ in range(count):
        cat1, cat2 = random.sample(categories, 2)
        page1 = random.choice(CATEGORIES[cat1]["pages"])
        page2 = random.choice(CATEGORIES[cat2]["pages"])
        
        pairs.append({
            "start": page1,
            "target": page2,
            "difficulty": "hard",
            "category": f"{cat1}-{cat2}"
        })
    
    return pairs


def generate_dataset(total_count: int = 500) -> Dict:
    """Generate complete dataset."""
    all_pairs = []
    
    # Calculate pairs per category
    num_categories = len(CATEGORIES)
    pairs_per_category = (total_count * 2 // 3) // num_categories  # 2/3 for same category
    cross_category_pairs = total_count // 3  # 1/3 for cross category
    
    print(f"Generating {total_count} page pairs...")
    print(f"  - {pairs_per_category} pairs per category ({num_categories} categories)")
    print(f"  - {cross_category_pairs} cross-category pairs")
    
    # Generate pairs for each category
    for category, data in CATEGORIES.items():
        print(f"  Generating {category} pairs...")
        pairs = generate_pairs_from_category(category, data, pairs_per_category)
        all_pairs.extend(pairs)
    
    # Generate cross-category pairs
    print(f"  Generating cross-category pairs...")
    cross_pairs = generate_cross_category_pairs(cross_category_pairs)
    all_pairs.extend(cross_pairs)
    
    # Shuffle
    random.shuffle(all_pairs)
    
    # Trim to exact count
    all_pairs = all_pairs[:total_count]
    
    dataset = {
        "description": f"Large curated Wikipedia dataset - {total_count} page pairs",
        "total_pairs": len(all_pairs),
        "categories": list(CATEGORIES.keys()),
        "difficulty_distribution": {
            "easy": sum(1 for p in all_pairs if p["difficulty"] == "easy"),
            "medium": sum(1 for p in all_pairs if p["difficulty"] == "medium"),
            "hard": sum(1 for p in all_pairs if p["difficulty"] == "hard")
        },
        "pairs": all_pairs
    }
    
    return dataset


def main():
    parser = argparse.ArgumentParser(description='Generate large curated dataset')
    parser.add_argument('--count', type=int, default=500, 
                       help='Number of page pairs to generate')
    parser.add_argument('--output', type=str, default='training_dataset_large.json',
                       help='Output file name')
    parser.add_argument('--append', action='store_true',
                       help='Append to existing training_dataset.json')
    
    args = parser.parse_args()
    
    print("="*60)
    print("📊 LARGE DATASET GENERATOR")
    print("="*60)
    
    # Generate dataset
    dataset = generate_dataset(args.count)
    
    # Append to existing if requested
    if args.append:
        try:
            with open('training_dataset.json', 'r', encoding='utf-8') as f:
                existing = json.load(f)
            
            print(f"\n📁 Appending to existing dataset...")
            print(f"   Existing pairs: {len(existing['pairs'])}")
            print(f"   New pairs: {len(dataset['pairs'])}")
            
            existing['pairs'].extend(dataset['pairs'])
            dataset = existing
            dataset['total_pairs'] = len(dataset['pairs'])
            args.output = 'training_dataset.json'
            
            print(f"   Total pairs: {len(dataset['pairs'])}")
        except FileNotFoundError:
            print(f"\n⚠️  training_dataset.json not found, creating new file")
    
    # Save
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Dataset saved to: {args.output}")
    print(f"\n📊 STATISTICS")
    print(f"   Total pairs: {dataset['total_pairs']}")
    print(f"   Easy: {dataset['difficulty_distribution']['easy']}")
    print(f"   Medium: {dataset['difficulty_distribution']['medium']}")
    print(f"   Hard: {dataset['difficulty_distribution']['hard']}")
    print(f"   Categories: {len(dataset['categories'])}")
    
    print(f"\n🚀 NEXT STEPS")
    print(f"   Train with: python train_ml_model_curated.py --dataset {args.output}")
    print(f"   Or test first: python train_ml_model_curated.py --dataset {args.output} --limit 50")
    print("="*60)


if __name__ == '__main__':
    main()