#!/usr/bin/env python3
"""
train_cloud.py
--------------
Cloud-optimized training script with remote model upload support.

Features:
- Automatic checkpoint saving
- Progress tracking
- Model artifact upload to cloud storage
- Resource monitoring
- Graceful shutdown handling

Usage:
    # Basic training
    python train_cloud.py
    
    # With custom dataset
    python train_cloud.py --dataset training_dataset_large.json
    
    # With S3 upload
    python train_cloud.py --upload-s3 --s3-bucket my-bucket
    
    # With GCS upload
    python train_cloud.py --upload-gcs --gcs-bucket my-bucket
"""

import argparse
import sys
import json
import os
import time
import signal
from pathlib import Path
from datetime import datetime
from src.semantic_navigator import SemanticNavigator
from src.ml_link_scorer import MLLinkScorer
from src.self_learning_trainer import SelfLearningTrainer


class CloudTrainer:
    """Cloud-optimized trainer with checkpoint and upload support."""
    
    def __init__(self, args):
        self.args = args
        self.start_time = time.time()
        self.checkpoint_interval = args.checkpoint_interval
        self.last_checkpoint = time.time()
        self.interrupted = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print("\n⚠️  Shutdown signal received. Saving progress...")
        self.interrupted = True
    
    def load_dataset(self):
        """Load training dataset."""
        try:
            with open(self.args.dataset, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            pairs = [(pair['start'], pair['target']) for pair in data['pairs']]
            
            if self.args.limit:
                pairs = pairs[:self.args.limit]
            
            return pairs
        
        except FileNotFoundError:
            print(f"❌ Dataset file not found: {self.args.dataset}")
            sys.exit(1)
        
        except Exception as e:
            print(f"❌ Error loading dataset: {e}")
            sys.exit(1)
    
    def initialize_components(self):
        """Initialize training components."""
        print("\n📦 Initializing components...")
        
        try:
            navigator = SemanticNavigator(
                verbose=self.args.verbose,
                use_graph=True,
                use_claude=False
            )
            print("✅ SemanticNavigator initialized")
            
            ml_scorer = MLLinkScorer(verbose=self.args.verbose)
            print("✅ MLLinkScorer initialized")
            
            trainer = SelfLearningTrainer(
                semantic_navigator=navigator,
                ml_scorer=ml_scorer,
                verbose=self.args.verbose
            )
            print("✅ SelfLearningTrainer initialized")
            
            return trainer
        
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            sys.exit(1)
    
    def save_checkpoint(self, trainer, current_pair, total_pairs):
        """Save training checkpoint."""
        checkpoint_data = {
            'timestamp': datetime.now().isoformat(),
            'current_pair': current_pair,
            'total_pairs': total_pairs,
            'elapsed_time': time.time() - self.start_time,
            'stats': trainer.get_stats()
        }
        
        checkpoint_file = Path('cache/checkpoint.json')
        checkpoint_file.parent.mkdir(exist_ok=True)
        
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
        
        print(f"💾 Checkpoint saved: {current_pair}/{total_pairs} pairs completed")
    
    def upload_to_s3(self):
        """Upload trained model to S3."""
        if not self.args.upload_s3:
            return
        
        try:
            import boto3  # type: ignore[import-untyped]
            
            print("\n📤 Uploading to S3...")
            s3 = boto3.client('s3')
            bucket = self.args.s3_bucket
            
            files_to_upload = [
                'cache/ml_model.pkl',
                'cache/ml_scaler.pkl',
                'cache/training_history.json',
                'cache/checkpoint.json'
            ]
            
            for file_path in files_to_upload:
                if Path(file_path).exists():
                    key = f"wikipediaml/{file_path}"
                    s3.upload_file(file_path, bucket, key)
                    print(f"✅ Uploaded: {file_path} → s3://{bucket}/{key}")
            
            print("✅ All files uploaded to S3")
        
        except ImportError:
            print("⚠️  boto3 not installed. Install with: pip install boto3")
        except Exception as e:
            print(f"❌ S3 upload failed: {e}")
    
    def upload_to_gcs(self):
        """Upload trained model to Google Cloud Storage."""
        if not self.args.upload_gcs:
            return
        
        try:
            from google.cloud import storage  # type: ignore[import-untyped]
            
            print("\n📤 Uploading to GCS...")
            client = storage.Client()
            bucket = client.bucket(self.args.gcs_bucket)
            
            files_to_upload = [
                'cache/ml_model.pkl',
                'cache/ml_scaler.pkl',
                'cache/training_history.json',
                'cache/checkpoint.json'
            ]
            
            for file_path in files_to_upload:
                if Path(file_path).exists():
                    blob = bucket.blob(f"wikipediaml/{file_path}")
                    blob.upload_from_filename(file_path)
                    print(f"✅ Uploaded: {file_path} → gs://{self.args.gcs_bucket}/wikipediaml/{file_path}")
            
            print("✅ All files uploaded to GCS")
        
        except ImportError:
            print("⚠️  google-cloud-storage not installed. Install with: pip install google-cloud-storage")
        except Exception as e:
            print(f"❌ GCS upload failed: {e}")
    
    def train(self):
        """Main training loop."""
        print("="*60)
        print("☁️  CLOUD ML TRAINING")
        print("="*60)
        print(f"📁 Dataset: {self.args.dataset}")
        print(f"💾 Checkpoint interval: {self.args.checkpoint_interval}s")
        print(f"📤 S3 upload: {self.args.upload_s3}")
        print(f"📤 GCS upload: {self.args.upload_gcs}")
        print("="*60)
        
        # Load dataset
        pairs = self.load_dataset()
        print(f"✅ Loaded {len(pairs)} page pairs")
        
        # Initialize components
        trainer = self.initialize_components()
        
        # Training loop
        print(f"\n{'='*60}")
        print(f"🎓 TRAINING IN PROGRESS")
        print(f"{'='*60}")
        
        successful = 0
        failed = 0
        i = 0
        
        try:
            for i, (start, target) in enumerate(pairs, 1):
                if self.interrupted:
                    print("\n⚠️  Training interrupted. Saving final checkpoint...")
                    break
                
                if self.args.verbose:
                    print(f"\n{'─'*60}")
                    print(f"Pair {i}/{len(pairs)}: {start} → {target}")
                
                # Train on this pair
                success = trainer.find_path_and_record(start, target, max_steps=self.args.max_steps)
                
                if success:
                    successful += 1
                else:
                    failed += 1
                
                # Show progress
                if self.args.verbose:
                    success_rate = (successful / i) * 100
                    elapsed = time.time() - self.start_time
                    print(f"\n📊 Progress: {i}/{len(pairs)} ({success_rate:.1f}% success)")
                    print(f"⏱️  Elapsed: {elapsed/60:.1f} minutes")
                
                # Periodic checkpoint
                if time.time() - self.last_checkpoint > self.checkpoint_interval:
                    trainer._save_history()
                    self.save_checkpoint(trainer, i, len(pairs))
                    self.last_checkpoint = time.time()
            
            # Final save
            trainer._save_history()
            self.save_checkpoint(trainer, len(pairs), len(pairs))
            
            # Train ML model
            if successful >= 10:
                print(f"\n{'='*60}")
                print(f"🎓 TRAINING ML MODEL")
                print(f"{'='*60}")
                print(f"✅ Training data: {successful} successful paths")
                
                trainer.train_model()
                print("✅ ML model trained successfully!")
            else:
                print(f"\n⚠️  Insufficient data: {successful} successful paths (need 10+)")
            
            # Upload to cloud storage
            self.upload_to_s3()
            self.upload_to_gcs()
            
            # Final statistics
            print(f"\n{'='*60}")
            print(f"📊 TRAINING COMPLETE")
            print(f"{'='*60}")
            
            stats = trainer.get_stats()
            total_time = time.time() - self.start_time
            
            print(f"Total pairs: {len(pairs)}")
            print(f"Successful: {successful}")
            print(f"Failed: {failed}")
            print(f"Success rate: {stats['success_rate']:.1f}%")
            print(f"Total time: {total_time/60:.1f} minutes")
            print(f"ML model trained: {stats['ml_model_trained']}")
            print(f"Training samples: {stats['ml_training_samples']}")
            print("="*60)
            
            return stats['ml_model_trained']
        
        except Exception as e:
            print(f"\n❌ Training failed: {e}")
            import traceback
            traceback.print_exc()
            
            # Save progress before exit
            trainer._save_history()
            self.save_checkpoint(trainer, i, len(pairs))
            
            return False


def main():
    parser = argparse.ArgumentParser(description='Cloud-optimized ML training')
    
    # Dataset options
    parser.add_argument('--dataset', type=str, default='data/training_dataset.json',
                       help='Path to training dataset')
    parser.add_argument('--limit', type=int, default=None,
                       help='Limit number of pairs (for testing)')
    
    # Training options
    parser.add_argument('--max-steps', type=int, default=10,
                       help='Maximum steps per search')
    parser.add_argument('--checkpoint-interval', type=int, default=300,
                       help='Checkpoint save interval in seconds (default: 300)')
    parser.add_argument('--verbose', action='store_true', default=True,
                       help='Enable verbose output')
    parser.add_argument('--no-verbose', dest='verbose', action='store_false',
                       help='Disable verbose output')
    
    # Cloud storage options
    parser.add_argument('--upload-s3', action='store_true',
                       help='Upload trained model to S3')
    parser.add_argument('--s3-bucket', type=str,
                       help='S3 bucket name')
    parser.add_argument('--upload-gcs', action='store_true',
                       help='Upload trained model to Google Cloud Storage')
    parser.add_argument('--gcs-bucket', type=str,
                       help='GCS bucket name')
    
    args = parser.parse_args()
    
    # Validate cloud storage options
    if args.upload_s3 and not args.s3_bucket:
        parser.error("--s3-bucket required when using --upload-s3")
    if args.upload_gcs and not args.gcs_bucket:
        parser.error("--gcs-bucket required when using --upload-gcs")
    
    # Run training
    cloud_trainer = CloudTrainer(args)
    success = cloud_trainer.train()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()