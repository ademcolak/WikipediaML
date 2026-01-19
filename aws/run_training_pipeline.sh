#!/bin/bash
################################################################################
# AWS EC2 Training Pipeline for WikipediaML
# This script runs the complete training pipeline on EC2
# Includes automatic checkpointing and resume capability
################################################################################

# Don't exit on error - we handle errors manually
set +e

# Configuration
PROJECT_DIR="$HOME/WikipediaML"
LOG_DIR="$PROJECT_DIR/logs"
DATA_DIR="$PROJECT_DIR/data"
CHECKPOINT_DIR="$DATA_DIR/checkpoints"

# Create log directory
mkdir -p "$LOG_DIR"
mkdir -p "$CHECKPOINT_DIR"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_DIR/training.log"
}

# Error handler
error_handler() {
    log "❌ ERROR: Pipeline failed at step: $1"
    log "Creating emergency checkpoint..."
    cd "$PROJECT_DIR"
    tar -czf "$CHECKPOINT_DIR/emergency_backup_$(date +%Y%m%d_%H%M%S).tar.gz" data/*.pkl models/*.pt 2>/dev/null || true
    exit 1
}

# Activate virtual environment
cd "$PROJECT_DIR"
source venv/bin/activate

log "=================================="
log "WikipediaML Training Pipeline"
log "=================================="
log "Instance: $(hostname)"
log "Start time: $(date)"
log "=================================="

# Step 1: Download Wikipedia dumps
log "📥 Step 1/7: Downloading Wikipedia dumps..."
if [ ! -f "$DATA_DIR/wikipedia_dumps/enwiki-latest-page.sql.gz" ] || \
   [ ! -f "$DATA_DIR/wikipedia_dumps/enwiki-latest-pagelinks.sql.gz" ]; then
    python3 scripts/download_wikipedia_dumps.py || error_handler "Download"
    log "✅ Wikipedia dumps downloaded"
else
    log "⊘ Wikipedia dumps already exist, skipping download"
fi

# Step 2: Parse Wikipedia dumps
log "🔍 Step 2/7: Parsing Wikipedia dumps..."
if [ ! -f "$DATA_DIR/cleaned/pages.json" ] || [ ! -f "$DATA_DIR/cleaned/links.json" ]; then
    python3 scripts/parse_wikipedia_dumps.py || error_handler "Parse"
    
    # Validate parse results
    if [ ! -f "$DATA_DIR/cleaned/pages.json" ] || [ ! -f "$DATA_DIR/cleaned/links.json" ]; then
        log "❌ ERROR: Parse completed but output files missing!"
        error_handler "Parse"
    fi
    
    # Check links.json is not empty
    if [ ! -s "$DATA_DIR/cleaned/links.json" ]; then
        log "❌ ERROR: links.json is empty! Parse failed."
        error_handler "Parse"
    fi
    
    # Check statistics
    if [ -f "$DATA_DIR/cleaned/statistics.json" ]; then
        TOTAL_LINKS=$(python3 -c "import json; print(json.load(open('$DATA_DIR/cleaned/statistics.json'))['total_links'])" 2>/dev/null || echo "0")
        if [ "$TOTAL_LINKS" -lt 1000 ]; then
            log "❌ ERROR: Too few links parsed ($TOTAL_LINKS). Parse likely failed!"
            error_handler "Parse"
        fi
        log "✓ Verified: $TOTAL_LINKS links parsed"
    fi
    
    log "✅ Wikipedia dumps parsed and validated"
    # Create checkpoint
    tar -czf "$CHECKPOINT_DIR/checkpoint_parse_$(date +%Y%m%d_%H%M%S).tar.gz" \
        "$DATA_DIR/cleaned/pages.json" "$DATA_DIR/cleaned/links.json" "$DATA_DIR/cleaned/statistics.json"
else
    log "⊘ Parsed data already exists, skipping parse"
fi

# Step 3: Build adjacency map
log "🗺️  Step 3/7: Building adjacency map (Knowledge Graph)..."
if [ ! -f "$DATA_DIR/graph/adjacency_matrix.npz" ]; then
    python3 scripts/build_adjacency_map.py || error_handler "Adjacency Map"
    
    # Validate adjacency matrix
    if [ ! -f "$DATA_DIR/graph/adjacency_matrix.npz" ]; then
        log "❌ ERROR: Adjacency matrix file not created!"
        error_handler "Adjacency Map"
    fi
    
    # Check matrix has edges using Python
    EDGE_COUNT=$(python3 -c "
from scipy.sparse import load_npz
import sys
try:
    matrix = load_npz('$DATA_DIR/graph/adjacency_matrix.npz')
    print(matrix.nnz)
except Exception as e:
    print('0', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null || echo "0")
    
    if [ "$EDGE_COUNT" -eq 0 ]; then
        log "❌ ERROR: Adjacency matrix has 0 edges! Build failed."
        error_handler "Adjacency Map"
    fi
    
    if [ "$EDGE_COUNT" -lt 1000 ]; then
        log "⚠️  WARNING: Very few edges in graph ($EDGE_COUNT). This is unusual."
    else
        log "✓ Verified: $EDGE_COUNT edges in graph"
    fi
    
    log "✅ Adjacency map built and validated"
    # Create checkpoint
    tar -czf "$CHECKPOINT_DIR/checkpoint_adjacency_$(date +%Y%m%d_%H%M%S).tar.gz" \
        "$DATA_DIR/graph/adjacency_matrix.npz" "$DATA_DIR/graph/page_mappings.pkl"
else
    log "⊘ Adjacency map already exists, skipping build"
    
    # Still validate existing matrix
    EDGE_COUNT=$(python3 -c "
from scipy.sparse import load_npz
try:
    matrix = load_npz('$DATA_DIR/graph/adjacency_matrix.npz')
    print(matrix.nnz)
except:
    print('0')
" 2>/dev/null || echo "0")
    
    if [ "$EDGE_COUNT" -eq 0 ]; then
        log "⚠️  WARNING: Existing adjacency matrix has 0 edges! Rebuilding..."
        rm -f "$DATA_DIR/graph/adjacency_matrix.npz"
        python3 scripts/build_adjacency_map.py || error_handler "Adjacency Map"
    fi
fi

# Step 4: Build embedding index
log "🧠 Step 4/7: Generating embeddings and FAISS index..."
if [ ! -f "$DATA_DIR/embeddings/embeddings.npy" ] || [ ! -f "$DATA_DIR/embeddings/faiss_index.bin" ]; then
    python3 scripts/build_embedding_index.py || error_handler "Embeddings"
    
    # Validate embeddings
    if [ ! -f "$DATA_DIR/embeddings/embeddings.npy" ] || [ ! -f "$DATA_DIR/embeddings/faiss_index.bin" ]; then
        log "❌ ERROR: Embedding files not created!"
        error_handler "Embeddings"
    fi
    
    # Check embeddings file size (should be > 100MB for full Wikipedia)
    EMBEDDING_SIZE=$(stat -f%z "$DATA_DIR/embeddings/embeddings.npy" 2>/dev/null || stat -c%s "$DATA_DIR/embeddings/embeddings.npy" 2>/dev/null || echo "0")
    if [ "$EMBEDDING_SIZE" -lt 1000000 ]; then
        log "⚠️  WARNING: Embeddings file is suspiciously small ($EMBEDDING_SIZE bytes)"
    else
        EMBEDDING_SIZE_MB=$((EMBEDDING_SIZE / 1024 / 1024))
        log "✓ Verified: Embeddings file size: ${EMBEDDING_SIZE_MB} MB"
    fi
    
    log "✅ Embeddings generated and validated"
    # Create checkpoint
    tar -czf "$CHECKPOINT_DIR/checkpoint_embeddings_$(date +%Y%m%d_%H%M%S).tar.gz" \
        "$DATA_DIR/embeddings/embeddings.npy" "$DATA_DIR/embeddings/faiss_index.bin"
else
    log "⊘ Embeddings already exist, skipping generation"
fi

# Step 5: Generate training data
log "📊 Step 5/7: Generating training data..."
TRAINING_SAMPLES_FILE="$DATA_DIR/training/training_samples.json"
if [ ! -f "$TRAINING_SAMPLES_FILE" ] || [ ! -s "$TRAINING_SAMPLES_FILE" ]; then
    # Remove empty/corrupted file if exists
    [ -f "$TRAINING_SAMPLES_FILE" ] && rm -f "$TRAINING_SAMPLES_FILE"
    
    # Generate training data (script uses hardcoded 100K samples)
    log "Starting training data generation (this may take a while)..."
    python3 scripts/generate_training_data.py 2>&1 | tee -a "$LOG_DIR/training.log" || error_handler "Training Data"
    
    # Verify training data was actually generated
    if [ ! -f "$TRAINING_SAMPLES_FILE" ] || [ ! -s "$TRAINING_SAMPLES_FILE" ]; then
        log "❌ ERROR: Training data file is empty or missing!"
        error_handler "Training Data"
    fi
    
    log "✅ Training data generated"
    # Create checkpoint
    tar -czf "$CHECKPOINT_DIR/checkpoint_training_data_$(date +%Y%m%d_%H%M%S).tar.gz" \
        "$TRAINING_SAMPLES_FILE" "$DATA_DIR/training/dataset_statistics.json"
else
    log "⊘ Training data already exists, skipping generation"
fi

# Step 6: Train MLP scorer
log "🎓 Step 6/7: Training MLP scorer model..."
if [ ! -f "models/checkpoints/mlp_scorer_best.pt" ]; then
    # Train for 50 epochs with checkpointing (default checkpoint interval is 5)
    python3 scripts/train_mlp_scorer.py --epochs 50 --checkpoint-interval 5 || error_handler "MLP Training"
    log "✅ MLP model trained"
    # Create checkpoint
    tar -czf "$CHECKPOINT_DIR/checkpoint_mlp_$(date +%Y%m%d_%H%M%S).tar.gz" \
        models/checkpoints/mlp_scorer_*.pt "$DATA_DIR/training/training_state.pkl" 2>/dev/null || true
else
    log "⊘ MLP model already exists, skipping training"
fi

# Step 7: Validate model
log "✅ Step 7/7: Validating trained model..."
python3 scripts/validate_mlp_scorer.py || error_handler "Validation"
log "✅ Model validation complete"

# Final checkpoint
log "💾 Creating final checkpoint..."
tar -czf "$CHECKPOINT_DIR/final_checkpoint_$(date +%Y%m%d_%H%M%S).tar.gz" \
    data/*.pkl data/*.npz data/*.npy data/*.bin models/*.pt

# Cleanup old checkpoints (keep last 5)
log "🧹 Cleaning up old checkpoints..."
cd "$CHECKPOINT_DIR"
ls -t checkpoint_*.tar.gz 2>/dev/null | tail -n +6 | xargs rm -f 2>/dev/null || true

log "=================================="
log "✅ Training Pipeline Complete!"
log "End time: $(date)"
log "=================================="
log ""
log "📦 Final checkpoint saved to:"
log "   $CHECKPOINT_DIR/final_checkpoint_$(date +%Y%m%d_%H%M%S).tar.gz"
log ""
log "📥 To download to local machine:"
log "   scp -i your-key.pem ec2-user@your-instance:$CHECKPOINT_DIR/final_checkpoint_*.tar.gz ."
log ""
log "🎮 To test the model:"
log "   python3 scripts/benchmark_navigator.py"
log ""