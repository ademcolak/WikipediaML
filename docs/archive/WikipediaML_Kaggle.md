# WikipediaML - ML-Powered Wikipedia Navigation

**Kaggle/Colab Setup Guide (Archived)**

Not: Bu içerik arşivlenmiştir. Dosya yolları ve komutlar güncel akışla
tam uyumlu olmayabilir.

Bu doküman, WikipediaML sistemini Kaggle veya Google Colab'da çalıştırmayı anlatır.

## Önerilen Ayarlar
- Kaggle: GPU P100 veya T4 (ücretsiz, haftada 30 saat)
- Google Colab: T4 GPU (ücretsiz)
- Süre: ~1-2 saat (1000 sayfa için)

## Adımlar

### 1) Setup ve Dependencies
```bash
pip install -q torch sentence-transformers faiss-cpu networkx scipy pandas tqdm python-igraph lxml beautifulsoup4
```

```python
import torch
print(f"Device: {'GPU' if torch.cuda.is_available() else 'CPU'}")
if torch.cuda.is_available():
    print(torch.cuda.get_device_name(0))
```

### 2) Repository'yi Klonla veya Dosyaları Yükle
```bash
git clone https://github.com/ademcolak/WikipediaML.git
cd WikipediaML
```

### 3) Wikipedia Verisi İndir (1000 sayfa - test için)
```bash
python3 scripts/download_wikipedia_dumps.py --limit 1000
```

### 4) Veriyi Parse Et ve Temizle
```bash
python3 scripts/parse_wikipedia_dumps.py
```

### 5) Graph Adjacency Matrix Oluştur
```bash
python3 scripts/build_adjacency_map.py
```

### 6) Embeddings ve FAISS Index Oluştur
```bash
python3 scripts/build_embedding_index.py
```

### 7) Training Data Üret
```bash
python3 scripts/generate_training_data.py --num_samples 5000
```

### 8) MLP Scorer Modelini Eğit
```bash
python3 scripts/train_mlp_scorer.py --epochs 20 --batch_size 512
```

### 9) Model Validasyonu
```bash
python3 scripts/validate_mlp_scorer.py
```

### 10) Benchmark Testleri
```bash
python3 scripts/benchmark_navigator.py
```

### 11) Manuel Test - Path Bulma
```python
import numpy as np
import pickle
from scipy.sparse import load_npz
from core.hybrid_scorer import HybridScorer
from core.beam_search import BeamSearchNavigator

print("Loading data...")
adjacency = load_npz('data/adjacency_map.npz')
with open('data/page_mappings.pkl', 'rb') as f:
    mappings = pickle.load(f)

embeddings = np.load('data/embeddings.npy')

scorer = HybridScorer(
    embeddings=embeddings,
    mlp_model_path='models/mlp_scorer_best.pt'
)

navigator = BeamSearchNavigator(
    adjacency_matrix=adjacency,
    page_mappings=mappings,
    hybrid_scorer=scorer,
    beam_width=10
)
```

### 12) Sonuçları İndir
```bash
zip -r wikipediaml_results.zip \
    data/adjacency_map.npz \
    data/embeddings.npy \
    data/faiss_index.bin \
    data/page_mappings.pkl \
    models/mlp_scorer_best.pt \
    models/training_history.json
```

## Tam Wikipedia Eğitimi İçin
```bash
python3 scripts/download_wikipedia_dumps.py
python3 scripts/train_mlp_scorer.py --epochs 50 --batch_size 1024
```
