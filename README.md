# WikipediaML - AI-Powered Wikipedia Navigation

ML-based system for finding shortest paths between Wikipedia pages using neural heuristics and beam search.

## 🚀 Quick Start

### Option 1: Kaggle/Colab (Recommended)
1. Open `WikipediaML_Kaggle.ipynb` in Kaggle or Google Colab
2. Enable GPU (P100 or T4)
3. Run all cells
4. Download trained models

**Time**: ~1 hour for 1000 pages

### Option 2: Local Setup
```bash
# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Test system
python3 test_new_system.py

# Quick prototype (1000 pages)
python3 quick_start.py
```

### Option 3: AWS EC2 (Production - Full Wikipedia)
For training on full Wikipedia dataset (6M+ pages):

```bash
# See detailed guide in docs/aws/README.md
# Quick start:
1. Launch EC2 instance (m5.2xlarge recommended)
2. SSH to instance
3. Run: curl -O https://raw.githubusercontent.com/ademcolak/WikipediaML/main/aws/ec2_setup.sh
4. Run: chmod +x ec2_setup.sh && ./ec2_setup.sh
5. Run: cd ~/WikipediaML && nohup ./aws/run_training_pipeline.sh > logs/training.log 2>&1 &
```

**Time**: 30-50 hours | **Cost**: ~$7-8 (Spot) | **See**: [`docs/aws/README.md`](docs/aws/README.md)

## 📁 Project Structure

```
WikipediaML/
├── core/              # Core navigation modules
│   ├── beam_search.py           # Beam search navigator
│   ├── hybrid_scorer.py         # MLP + cosine + hub scoring
│   ├── fast_hybrid_scorer.py    # Two-stage filtering
│   ├── advanced_navigator.py    # Backtracking + tabu
│   └── wikipedia_fallback.py    # API fallback
├── models/            # Neural network models
│   └── mlp_scorer.py            # MLP distance predictor
├── scripts/           # Data processing & training
│   ├── download_wikipedia_dumps.py
│   ├── parse_wikipedia_dumps.py
│   ├── build_adjacency_map.py
│   ├── build_embedding_index.py
│   ├── generate_training_data.py
│   ├── train_mlp_scorer.py
│   ├── validate_mlp_scorer.py
│   └── benchmark_navigator.py
├── aws/               # AWS EC2 deployment scripts
│   ├── ec2_setup.sh             # Instance setup script
│   ├── run_training_pipeline.sh # Automated training
│   ├── sync_data.sh             # Data sync (EC2 ↔ Local)
│   └── config.example.sh        # Configuration template
├── docs/              # Documentation
│   ├── aws/                     # AWS deployment docs
│   │   ├── README.md            # Detailed AWS guide
│   │   ├── QUICKSTART.md        # Quick start guide
│   │   └── PROGRESS.md          # Progress report
│   └── todo.md                  # Project todo list
├── legacy/            # Old system (archived)
└── data/              # Generated data files
```

## 🎯 Features

- **Neural Heuristic**: MLP predicts distance to target
- **Hybrid Scoring**: Combines MLP, cosine similarity, hub scores
- **Beam Search**: Explores top-k paths simultaneously
- **Fast Filtering**: Two-stage scoring (80-90% speedup)
- **Backtracking**: Recovers from dead ends
- **API Fallback**: Live Wikipedia data when needed

## 📊 Performance

**Small Test (1000 pages)**:
- Training: 15-20 minutes (GPU)
- Inference: <100ms per path
- Success rate: ~85%

**Full Wikipedia (6M+ pages)**:
- Training: 20-30 hours (GPU)
- Inference: <200ms per path
- Success rate: ~95%

## 🛠️ Usage

### Training Pipeline
```bash
# 1. Download Wikipedia
python3 scripts/download_wikipedia_dumps.py --limit 1000

# 2. Parse and build graph
python3 scripts/parse_wikipedia_dumps.py
python3 scripts/build_adjacency_map.py

# 3. Generate embeddings
python3 scripts/build_embedding_index.py

# 4. Create training data
python3 scripts/generate_training_data.py

# 5. Train MLP (auto-resumes from checkpoint if exists)
python3 scripts/train_mlp_scorer.py --epochs 20

# 6. Validate
python3 scripts/validate_mlp_scorer.py

# 7. Benchmark
python3 scripts/benchmark_navigator.py
```

### Using Trained Model
```python
import numpy as np
import pickle
from scipy.sparse import load_npz
from core.hybrid_scorer import HybridScorer
from core.beam_search import BeamSearchNavigator

# Load data
adjacency = load_npz('data/adjacency_map.npz')
with open('data/page_mappings.pkl', 'rb') as f:
    mappings = pickle.load(f)
embeddings = np.load('data/embeddings.npy')

# Create navigator
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

# Find path
result = navigator.search("Python", "Computer", max_depth=6)
print(result['path'])  # ['Python', 'Programming', 'Computer']
```

## 📚 Documentation

- `docs/aws/README.md` - AWS EC2 deployment guide
- `docs/aws/QUICKSTART.md` - Quick start for AWS
- `docs/aws/RUNNING_ON_AWS.md` - **How to run training on AWS (where, how, background)**
- `docs/aws/PROGRESS.md` - AWS integration progress
- `docs/todo.md` - Project todo list
- `WikipediaML_Kaggle.ipynb` - Interactive tutorial

## 🧪 Testing

```bash
# System test
python3 test_new_system.py

# Unit tests (if available)
pytest tests/
```

## 📦 Requirements

- Python 3.8+
- PyTorch 2.0+
- sentence-transformers
- FAISS
- NetworkX
- scipy, numpy, pandas

See `requirements.txt` for full list.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Run tests
5. Submit pull request

## 📄 License

MIT License - see LICENSE file

## 🙏 Acknowledgments

- Wikipedia for data
- Sentence-Transformers for embeddings
- PyTorch for ML framework
- FAISS for vector search

## 📧 Contact

For questions or issues, please open a GitHub issue.
