#!/usr/bin/env python3
"""
train.py
--------
Yeni standart eğitim sistemi - Tüm eğitim türleri için tek entry point.

Kullanım:
    # Stratejik eğitim (popüler sayfalar)
    python train.py --strategy strategic --workers 3 --iterations 100
    
    # Rastgele eğitim (çeşitlilik)
    python train.py --strategy random --workers 3 --iterations 100
    
    # Hibrit eğitim (70% stratejik, 30% rastgele)
    python train.py --strategy hybrid --workers 3 --iterations 100
    
    # Özel eğitim (kendi listesi)
    python train.py --strategy custom --file my_pairs.txt --workers 1

Özellikler:
    - Standart pipeline (setup → train → save → backup → cleanup)
    - Otomatik merge
    - Rate limiting
    - Wikipedia 429 koruması
"""

import sys
import argparse
import asyncio
from pathlib import Path
from typing import List, Tuple

from src.training_pipeline import TrainingConfig
from src.training_strategies import (
    StrategicTraining,
    RandomTraining,
    CustomTraining,
    HybridTraining
)


def load_custom_pairs(file_path: str) -> List[Tuple[str, str]]:
    """
    Dosyadan özel çiftleri yükle.
    
    Format:
        Start_Page,Target_Page
        Italy,Rome
        Physics,Albert_Einstein
    
    Args:
        file_path: Dosya yolu
        
    Returns:
        (start, target) çiftleri listesi
    """
    pairs = []
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                parts = line.split(',')
                if len(parts) == 2:
                    pairs.append((parts[0].strip(), parts[1].strip()))
    return pairs


def run_training(args):
    """Eğitimi çalıştır."""
    # Konfigürasyon oluştur
    config = TrainingConfig(
        worker_id=args.worker_id,
        num_workers=args.workers,
        num_iterations=args.iterations,
        rate_limit_delay=args.rate_limit,
        max_concurrent=args.max_concurrent,
        use_graph=True,
        use_async=True,
        verbose=args.verbose
    )
    
    # Strateji seç
    if args.strategy == 'strategic':
        pipeline = StrategicTraining(config)
    elif args.strategy == 'random':
        pipeline = RandomTraining(config)
    elif args.strategy == 'hybrid':
        pipeline = HybridTraining(config, strategic_ratio=args.hybrid_ratio)
    elif args.strategy == 'custom':
        if not args.file:
            print("❌ Custom strategy için --file parametresi gerekli!")
            sys.exit(1)
        pairs = load_custom_pairs(args.file)
        pipeline = CustomTraining(config, pairs)
    else:
        print(f"❌ Bilinmeyen strateji: {args.strategy}")
        sys.exit(1)
    
    # Çalıştır
    pipeline.run()


def run_parallel_training(args):
    """Paralel eğitim - Birden fazla worker."""
    import subprocess
    import time
    
    print("\n" + "=" * 70)
    print(f"🚀 PARALEL EĞİTİM - {args.workers} WORKER")
    print("=" * 70)
    print(f"\nStrateji: {args.strategy}")
    print(f"Iterations: {args.iterations}")
    print(f"Rate limit: {args.rate_limit}s")
    print(f"Max concurrent: {args.max_concurrent}")
    print("=" * 70)
    
    # Her worker için process başlat
    processes = []
    for worker_id in range(1, args.workers + 1):
        cmd = [
            sys.executable,
            __file__,
            '--strategy', args.strategy,
            '--worker-id', str(worker_id),
            '--workers', str(args.workers),
            '--iterations', str(args.iterations),
            '--rate-limit', str(args.rate_limit),
            '--max-concurrent', str(args.max_concurrent),
            '--no-parallel'  # Recursive çağrıyı önle
        ]
        
        if args.verbose:
            cmd.append('--verbose')
        
        if args.strategy == 'hybrid':
            cmd.extend(['--hybrid-ratio', str(args.hybrid_ratio)])
        
        if args.strategy == 'custom' and args.file:
            cmd.extend(['--file', args.file])
        
        print(f"\n🔧 Worker {worker_id} başlatılıyor...")
        process = subprocess.Popen(cmd)
        processes.append(process)
        time.sleep(0.5)  # Stagger başlatma
    
    print(f"\n✅ {args.workers} worker başlatıldı!")
    print("⏳ Worker'ların bitmesi bekleniyor...")
    
    # Tüm worker'ların bitmesini bekle
    for process in processes:
        process.wait()
    
    print("\n✅ Tüm worker'lar tamamlandı!")
    
    # Merge
    if args.auto_merge:
        print("\n🔗 Graph'lar birleştiriliyor...")
        subprocess.run([sys.executable, 'merge_graphs.py', '--cleanup'])
        print("✅ Merge tamamlandı!")


def main():
    """Ana fonksiyon."""
    parser = argparse.ArgumentParser(
        description='Standart eğitim sistemi',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  # Stratejik eğitim (3 worker, 100 iteration)
  python train.py --strategy strategic --workers 3 --iterations 100
  
  # Rastgele eğitim (tek worker, 50 iteration)
  python train.py --strategy random --workers 1 --iterations 50
  
  # Hibrit eğitim (70% stratejik, 30% rastgele)
  python train.py --strategy hybrid --workers 3 --iterations 100 --hybrid-ratio 0.7
  
  # Özel eğitim (kendi listesi)
  python train.py --strategy custom --file pairs.txt --workers 1
        """
    )
    
    # Strateji
    parser.add_argument(
        '--strategy',
        type=str,
        choices=['strategic', 'random', 'hybrid', 'custom'],
        default='strategic',
        help='Eğitim stratejisi (default: strategic)'
    )
    
    # Worker ayarları
    parser.add_argument(
        '--workers',
        type=int,
        default=3,
        help='Worker sayısı (default: 3)'
    )
    
    parser.add_argument(
        '--worker-id',
        type=int,
        default=1,
        help='Worker ID (internal use)'
    )
    
    # Eğitim ayarları
    parser.add_argument(
        '--iterations',
        type=int,
        default=100,
        help='Iteration sayısı (default: 100)'
    )
    
    parser.add_argument(
        '--rate-limit',
        type=float,
        default=1.0,
        help='Rate limiting delay (saniye, default: 1.0)'
    )
    
    parser.add_argument(
        '--max-concurrent',
        type=int,
        default=2,
        help='Max concurrent requests (default: 2)'
    )
    
    # Hibrit strateji
    parser.add_argument(
        '--hybrid-ratio',
        type=float,
        default=0.7,
        help='Hibrit stratejide stratejik oran (default: 0.7)'
    )
    
    # Özel strateji
    parser.add_argument(
        '--file',
        type=str,
        help='Custom strategy için çift listesi dosyası'
    )
    
    # Diğer
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Detaylı log'
    )
    
    parser.add_argument(
        '--no-parallel',
        action='store_true',
        help='Paralel çalıştırmayı devre dışı bırak (internal)'
    )
    
    parser.add_argument(
        '--auto-merge',
        action='store_true',
        default=True,
        help='Otomatik merge (default: True)'
    )
    
    args = parser.parse_args()
    
    try:
        if args.workers > 1 and not args.no_parallel:
            # Paralel eğitim
            run_parallel_training(args)
        else:
            # Tek worker
            run_training(args)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  İşlem kullanıcı tarafından durduruldu.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Hata: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()