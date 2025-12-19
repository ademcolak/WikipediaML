"""
training_pipeline.py
--------------------
Standart eğitim pipeline'ı - Tüm eğitim işlemleri için merkezi sistem.

Mimari:
    TrainingPipeline (Abstract Base)
        ├── Başlat (setup)
        ├── Eğit (train)
        ├── Kaydet (save)
        ├── Backup (backup)
        ├── Temizle (cleanup)
        └── Sonuçlandır (finalize)

Kullanım:
    pipeline = TrainingPipeline(config)
    pipeline.run()
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Callable
import shutil

from src.semantic_navigator import SemanticNavigator
from src.knowledge_graph import WikiKnowledgeGraph


@dataclass
class TrainingConfig:
    """Eğitim konfigürasyonu."""
    # Worker ayarları
    worker_id: int = 1
    num_workers: int = 1
    
    # Eğitim ayarları
    num_iterations: int = 100
    batch_size: int = 10
    
    # Rate limiting
    rate_limit_delay: float = 1.0
    max_concurrent: int = 2
    
    # Dosya yolları
    cache_dir: Path = Path("cache")
    backup_dir: Path = Path("cache/backup")
    
    # Graph ayarları
    use_graph: bool = True
    use_async: bool = True
    
    # Hybrid Navigator (10K+ edge için)
    use_hybrid: bool = False
    use_llm: bool = False
    
    # Verbose
    verbose: bool = False
    
    def __post_init__(self):
        """Path'leri Path objesine çevir."""
        self.cache_dir = Path(self.cache_dir)
        self.backup_dir = Path(self.backup_dir)


@dataclass
class TrainingStats:
    """Eğitim istatistikleri."""
    total: int = 0
    success: int = 0
    failed: int = 0
    avg_steps: float = 0.0
    total_time: float = 0.0
    
    def update_success(self, steps: int, elapsed: float):
        """Başarılı deneme ekle."""
        self.success += 1
        self.total += 1
        self.total_time += elapsed
        self.avg_steps = (self.avg_steps * (self.success - 1) + steps) / self.success
    
    def update_failed(self, elapsed: float):
        """Başarısız deneme ekle."""
        self.failed += 1
        self.total += 1
        self.total_time += elapsed
    
    @property
    def success_rate(self) -> float:
        """Başarı oranı."""
        return (self.success / self.total * 100) if self.total > 0 else 0.0
    
    @property
    def avg_time(self) -> float:
        """Ortalama süre."""
        return self.total_time / self.total if self.total > 0 else 0.0


class TrainingPipeline(ABC):
    """
    Standart eğitim pipeline'ı (Abstract Base Class).
    
    Tüm eğitim scriptleri bu sınıftan türetilir ve standart
    workflow'u takip eder:
    
    1. setup() - Navigator, graph, vb. hazırla
    2. train() - Eğitim döngüsü
    3. save() - Graph'ı kaydet
    4. backup() - Backup al
    5. cleanup() - Geçici dosyaları temizle
    6. finalize() - İstatistikleri göster
    """
    
    def __init__(self, config: TrainingConfig):
        """
        Pipeline'ı başlat.
        
        Args:
            config: Eğitim konfigürasyonu
        """
        self.config = config
        self.stats = TrainingStats()
        self.navigator: Optional[SemanticNavigator] = None
        self.start_time = 0.0
        
        # Worker-specific graph dosyası
        self.graph_file = self.config.cache_dir / f"wiki_graph_worker_{config.worker_id}.pkl"
    
    def run(self):
        """
        Pipeline'ı çalıştır (ana entry point).
        
        Workflow:
            1. Setup
            2. Train
            3. Save
            4. Backup
            5. Cleanup
            6. Finalize
        """
        try:
            self.start_time = time.time()
            
            # 1. Setup
            self._setup()
            
            # 2. Train
            if self.config.use_async:
                asyncio.run(self._train_async())
            else:
                self._train_sync()
            
            # 3. Save
            self._save()
            
            # 4. Backup (optional)
            if self.config.num_workers > 1:
                self._backup()
            
            # 5. Cleanup
            self._cleanup()
            
            # 6. Finalize
            self._finalize()
            
        except KeyboardInterrupt:
            print(f"\n\n⚠️  Worker {self.config.worker_id} kullanıcı tarafından durduruldu.")
            self._emergency_save()
        except Exception as e:
            print(f"\n\n❌ Hata: {e}")
            import traceback
            traceback.print_exc()
            self._emergency_save()
    
    def _setup(self):
        """1. Setup - Navigator ve graph hazırla."""
        print("\n" + "=" * 70)
        print(f"🤖 EĞİTİM PIPELINE - WORKER {self.config.worker_id}")
        print("=" * 70)
        print(f"\n📦 Konfigürasyon:")
        print(f"   • Iterations: {self.config.num_iterations}")
        print(f"   • Workers: {self.config.num_workers}")
        print(f"   • Rate limit: {self.config.rate_limit_delay}s")
        print(f"   • Max concurrent: {self.config.max_concurrent}")
        print(f"   • Hybrid mode: {self.config.use_hybrid}")
        print(f"   • LLM mode: {self.config.use_llm}")
        print(f"   • Graph file: {self.graph_file}")
        print("=" * 70)
        
        # Navigator oluştur
        print("\n🔧 Navigator başlatılıyor...")
        self.navigator = SemanticNavigator(
            verbose=self.config.verbose,
            use_graph=self.config.use_graph,
            use_async=self.config.use_async,
            use_hybrid=self.config.use_hybrid,
            use_llm=self.config.use_llm
        )
        
        # Worker-specific graph ayarla
        if self.navigator.knowledge_graph:
            self.navigator.knowledge_graph.cache_file = self.graph_file
            self.navigator.knowledge_graph._load_from_cache()
        
        # Async scraper rate limiting
        if self.navigator.async_scraper:
            self.navigator.async_scraper.max_concurrent = self.config.max_concurrent
            self.navigator.async_scraper._semaphore = asyncio.Semaphore(self.config.max_concurrent)
            print(f"   ⚙️ Async scraper max_concurrent: {self.config.max_concurrent}")
        
        print(f"✅ Worker {self.config.worker_id} hazır!")
    
    @abstractmethod
    def _get_next_pair(self, iteration: int) -> tuple[str, str]:
        """
        Bir sonraki (start, target) çiftini döndür.
        
        Bu metod alt sınıflar tarafından implement edilmeli:
        - StrategicPipeline: Popüler sayfalar
        - RandomPipeline: Rastgele sayfalar
        - CustomPipeline: Özel liste
        
        Args:
            iteration: Mevcut iterasyon numarası
            
        Returns:
            (start, target) tuple
        """
        pass
    
    async def _train_async(self):
        """2. Train - Async eğitim döngüsü."""
        print("\n🔄 Eğitim başlıyor (async)...")
        
        for i in range(self.config.num_iterations):
            # Sonraki çifti al
            start, target = self._get_next_pair(i)
            
            # Eğit
            await self._train_single_async(start, target, i + 1)
            
            # Rate limiting
            await asyncio.sleep(self.config.rate_limit_delay)
            
            # İlerleme raporu
            if (i + 1) % 10 == 0:
                self._print_progress()
        
        # Async scraper'ı kapat
        if self.navigator and self.navigator.async_scraper:
            await self.navigator.async_scraper.close()
    
    def _train_sync(self):
        """2. Train - Sync eğitim döngüsü."""
        print("\n🔄 Eğitim başlıyor (sync)...")
        
        for i in range(self.config.num_iterations):
            # Sonraki çifti al
            start, target = self._get_next_pair(i)
            
            # Eğit
            self._train_single_sync(start, target, i + 1)
            
            # Rate limiting
            time.sleep(self.config.rate_limit_delay)
            
            # İlerleme raporu
            if (i + 1) % 10 == 0:
                self._print_progress()
    
    async def _train_single_async(self, start: str, target: str, iteration: int):
        """Tek bir çifti eğit (async)."""
        if not self.navigator:
            raise RuntimeError("Navigator not initialized")
        
        print(f"\n[Worker {self.config.worker_id}] [{iteration}/{self.config.num_iterations}] {start} → {target}")
        
        iter_start = time.time()
        
        try:
            # Path bul
            result = await self.navigator.async_bidirectional_beam_search(
                start=start,
                target=target,
                beam_width=4,
                max_depth=6
            )
            
            elapsed = time.time() - iter_start
            
            if result.found:
                self.stats.update_success(result.steps, elapsed)
                
                # KG'ye kaydet
                if self.navigator.knowledge_graph and result.path:
                    path_length = len(result.path) - 1
                    path_quality = max(0.2, 1.0 - (path_length - 2) * 0.2)
                    
                    self.navigator.knowledge_graph.add_path(
                        result.path,
                        success=True,
                        path_quality=path_quality
                    )
                    # Her 10 path'te bir kaydet (performans)
                    if self.stats.success % 10 == 0:
                        self.navigator.knowledge_graph.save()
                
                print(f"   ✅ Bulundu: {result.steps} adım, {elapsed:.3f}s")
                print(f"   Path: {' → '.join(result.path[:5])}{'...' if len(result.path) > 5 else ''}")
            else:
                self.stats.update_failed(elapsed)
                print(f"   ❌ Bulunamadı: {elapsed:.3f}s")
        
        except Exception as e:
            elapsed = time.time() - iter_start
            self.stats.update_failed(elapsed)
            print(f"   ⚠️ Hata: {e}")
    
    def _train_single_sync(self, start: str, target: str, iteration: int):
        """Tek bir çifti eğit (sync)."""
        # Sync version - implement if needed
        raise NotImplementedError("Sync training not implemented yet")
    
    def _save(self):
        """3. Save - Graph'ı kaydet."""
        if self.navigator and self.navigator.knowledge_graph:
            print("\n💾 Graph kaydediliyor...")
            self.navigator.knowledge_graph.save()
            print(f"   ✅ Kaydedildi: {self.graph_file}")
    
    def _backup(self):
        """4. Backup - Worker graph'ını backup'la."""
        if not self.graph_file.exists():
            return
        
        print("\n📦 Backup alınıyor...")
        self.config.backup_dir.mkdir(parents=True, exist_ok=True)
        
        backup_file = self.config.backup_dir / self.graph_file.name
        shutil.copy2(self.graph_file, backup_file)
        print(f"   ✅ Backup: {backup_file}")
    
    def _cleanup(self):
        """5. Cleanup - Geçici dosyaları temizle."""
        # Alt sınıflar override edebilir
        pass
    
    def _finalize(self):
        """6. Finalize - İstatistikleri göster."""
        total_time = time.time() - self.start_time
        
        print("\n" + "=" * 70)
        print(f"📊 WORKER {self.config.worker_id} İSTATİSTİKLER")
        print("=" * 70)
        
        print(f"\nToplam deneme: {self.stats.total}")
        print(f"Başarılı: {self.stats.success} ({self.stats.success_rate:.1f}%)")
        print(f"Başarısız: {self.stats.failed}")
        
        if self.stats.success > 0:
            print(f"Ortalama adım: {self.stats.avg_steps:.1f}")
            print(f"Ortalama süre: {self.stats.avg_time:.2f}s")
        
        print(f"\nToplam süre: {total_time:.2f}s")
        
        # KG istatistikleri
        if self.navigator and self.navigator.knowledge_graph:
            kg = self.navigator.knowledge_graph
            print(f"\n📈 KNOWLEDGE GRAPH")
            print(f"   Öğrenilen yol: {kg.paths_learned}")
            print(f"   Node sayısı: {kg.graph.number_of_nodes()}")
            print(f"   Edge sayısı: {kg.graph.number_of_edges()}")
            print(f"   Dosya: {self.graph_file}")
        
        print("=" * 70)
    
    def _print_progress(self):
        """İlerleme raporu."""
        print("\n" + "─" * 70)
        print(f"📊 Worker {self.config.worker_id} İlerleme: {self.stats.total}/{self.config.num_iterations}")
        print(f"   Başarı: {self.stats.success}/{self.stats.total} ({self.stats.success_rate:.1f}%)")
        print("─" * 70)
    
    def _emergency_save(self):
        """Acil durum kaydı."""
        print("\n🚨 Acil durum kaydı yapılıyor...")
        self._save()
        print("✅ Kayıt tamamlandı.")