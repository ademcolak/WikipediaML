# WikipediaML

ML-based system for finding short paths between Wikipedia pages using a neural heuristic and beam search.

---

## Turkce

### Amac
Wikipedia sayfalari arasinda kisa bir yol bulmak icin MLP tabanli heuristik + beam search kullanir.

### Kurulum (Lokal)
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Temel Pipeline (Lokal)
```bash
# 1) Dump indir
python3 scripts/download_wikipedia_dumps.py --limit 1000

# 2) Parse ve graph
python3 scripts/parse_wikipedia_dumps.py
python3 scripts/build_adjacency_map.py

# 3) Embeddings
python3 scripts/build_embedding_index.py

# 4) Training data
python3 scripts/generate_training_data.py

# 5) MLP train
python3 scripts/train_mlp_scorer.py --epochs 20

# 6) Validate + benchmark
python3 scripts/validate_mlp_scorer.py
python3 scripts/benchmark_navigator.py
```

### AWS (Tek Script, Sirali Calisir)
```bash
curl -O https://raw.githubusercontent.com/ademcolak/WikipediaML/main/aws/ec2_setup.sh
chmod +x ec2_setup.sh && ./ec2_setup.sh

cd ~/WikipediaML
nohup ./aws/run_training_pipeline.sh > logs/training.log 2>&1 &
```

Gerekirse pipeline parametreleri (ENV):
```bash
TRAINING_NUM_SAMPLES=100000 \
TRAINING_CANDIDATES=10 \
MLP_EPOCHS=30 \
nohup ./aws/run_training_pipeline.sh > logs/training.log 2>&1 &
```

### Tani / Diagnostik
```bash
python3 scripts/validate_artifacts.py --check-paths
python3 scripts/check_graph_connectivity.py
```

### Benchmark
```bash
python3 scripts/benchmark_navigator.py --n-pairs 50 --beam-width 50 --max-depth 10
```

### Proje Yapisi (Sade)
```
core/    models/    scripts/    aws/    data/    README.md
```

Not: `data/` buyuk dosyalari icerir ve git ile takip edilmez.

---

## English

### Goal
Find short paths between Wikipedia pages using an MLP-based heuristic and beam search.

### Local Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Local Pipeline
```bash
python3 scripts/download_wikipedia_dumps.py --limit 1000
python3 scripts/parse_wikipedia_dumps.py
python3 scripts/build_adjacency_map.py
python3 scripts/build_embedding_index.py
python3 scripts/generate_training_data.py
python3 scripts/train_mlp_scorer.py --epochs 20
python3 scripts/validate_mlp_scorer.py
python3 scripts/benchmark_navigator.py
```

### AWS (Single Script, Sequential)
```bash
curl -O https://raw.githubusercontent.com/ademcolak/WikipediaML/main/aws/ec2_setup.sh
chmod +x ec2_setup.sh && ./ec2_setup.sh

cd ~/WikipediaML
nohup ./aws/run_training_pipeline.sh > logs/training.log 2>&1 &
```

Optional ENV overrides:
```bash
TRAINING_NUM_SAMPLES=100000 \
TRAINING_CANDIDATES=10 \
MLP_EPOCHS=30 \
nohup ./aws/run_training_pipeline.sh > logs/training.log 2>&1 &
```

### Diagnostics
```bash
python3 scripts/validate_artifacts.py --check-paths
python3 scripts/check_graph_connectivity.py
```

### Benchmark
```bash
python3 scripts/benchmark_navigator.py --n-pairs 50 --beam-width 50 --max-depth 10
```

### Project Structure (Minimal)
```
core/    models/    scripts/    aws/    data/    README.md
```

Note: `data/` contains large artifacts and is not tracked in git.
