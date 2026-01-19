#!/bin/bash
################################################################################
# WikipediaML Pipeline Management Script
# Use this script to check, start, stop, and monitor the training pipeline
################################################################################

PROJECT_DIR="$HOME/WikipediaML"
LOG_DIR="$PROJECT_DIR/logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if process is running
check_process() {
    local process_name=$1
    if pgrep -f "$process_name" > /dev/null; then
        return 0  # Running
    else
        return 1  # Not running
    fi
}

# Function to show running processes
show_processes() {
    echo -e "${GREEN}=== Running WikipediaML Processes ===${NC}"
    local processes=$(ps aux | grep -E "(generate_training_data|run_training_pipeline|train_mlp_scorer|build_embedding|parse_wikipedia)" | grep -v grep)
    
    if [ -z "$processes" ]; then
        echo -e "${YELLOW}No WikipediaML processes found running.${NC}"
        return 1
    else
        echo "$processes"
        return 0
    fi
}

# Function to stop all processes
stop_all() {
    echo -e "${YELLOW}Stopping all WikipediaML processes...${NC}"
    
    local pids=$(pgrep -f "run_training_pipeline|generate_training_data|train_mlp_scorer")
    
    if [ -z "$pids" ]; then
        echo -e "${GREEN}No processes to stop.${NC}"
        return 0
    fi
    
    echo "Found PIDs: $pids"
    
    # Try graceful shutdown first
    pkill -f run_training_pipeline
    pkill -f generate_training_data
    pkill -f train_mlp_scorer
    
    sleep 2
    
    # Check if still running, force kill if needed
    if pgrep -f "run_training_pipeline|generate_training_data" > /dev/null; then
        echo -e "${RED}Processes still running, forcing shutdown...${NC}"
        pkill -9 -f run_training_pipeline
        pkill -9 -f generate_training_data
        pkill -9 -f train_mlp_scorer
        sleep 1
    fi
    
    if ! pgrep -f "run_training_pipeline|generate_training_data" > /dev/null; then
        echo -e "${GREEN}All processes stopped successfully.${NC}"
        return 0
    else
        echo -e "${RED}Warning: Some processes may still be running.${NC}"
        return 1
    fi
}

# Function to show log tail
show_log() {
    local lines=${1:-50}
    if [ -f "$LOG_DIR/training.log" ]; then
        echo -e "${GREEN}=== Last $lines lines of training.log ===${NC}"
        tail -n "$lines" "$LOG_DIR/training.log"
    else
        echo -e "${RED}Log file not found: $LOG_DIR/training.log${NC}"
        return 1
    fi
}

# Function to follow log
follow_log() {
    if [ -f "$LOG_DIR/training.log" ]; then
        echo -e "${GREEN}Following log (Ctrl+C to exit)...${NC}"
        tail -f "$LOG_DIR/training.log"
    else
        echo -e "${RED}Log file not found: $LOG_DIR/training.log${NC}"
        return 1
    fi
}

# Function to check data progress
check_progress() {
    echo -e "${GREEN}=== Pipeline Progress ===${NC}"
    
    # Check training samples
    local samples_file="$PROJECT_DIR/data/training/training_samples.json"
    if [ -f "$samples_file" ]; then
        local sample_count=$(python3 -c "import json; f=open('$samples_file'); data=json.load(f); print(len(data))" 2>/dev/null || echo "0")
        local file_size=$(du -h "$samples_file" | cut -f1)
        echo -e "Training samples: ${GREEN}$sample_count${NC} samples ($file_size)"
    else
        echo -e "Training samples: ${YELLOW}Not started${NC}"
    fi
    
    # Check embeddings
    local embeddings_file="$PROJECT_DIR/data/embeddings/embeddings.npy"
    if [ -f "$embeddings_file" ]; then
        local emb_size=$(du -h "$embeddings_file" | cut -f1)
        echo -e "Embeddings: ${GREEN}Exists${NC} ($emb_size)"
    else
        echo -e "Embeddings: ${YELLOW}Not generated${NC}"
    fi
    
    # Check graph
    local graph_file="$PROJECT_DIR/data/graph/adjacency_matrix.npz"
    if [ -f "$graph_file" ]; then
        local graph_size=$(du -h "$graph_file" | cut -f1)
        echo -e "Graph: ${GREEN}Exists${NC} ($graph_size)"
    else
        echo -e "Graph: ${YELLOW}Not built${NC}"
    fi
}

# Function to start pipeline
start_pipeline() {
    if check_process "run_training_pipeline"; then
        echo -e "${YELLOW}Pipeline is already running!${NC}"
        show_processes
        return 1
    fi
    
    echo -e "${GREEN}Starting training pipeline...${NC}"
    cd "$PROJECT_DIR"
    source venv/bin/activate
    nohup ./aws/run_training_pipeline.sh > /dev/null 2>&1 &
    
    sleep 2
    
    if check_process "run_training_pipeline"; then
        echo -e "${GREEN}Pipeline started successfully!${NC}"
        echo "Use './aws/manage_pipeline.sh log' to follow progress"
        return 0
    else
        echo -e "${RED}Failed to start pipeline. Check logs.${NC}"
        return 1
    fi
}

# Main menu
case "${1:-status}" in
    status|check)
        echo -e "${GREEN}=== WikipediaML Pipeline Status ===${NC}"
        echo ""
        show_processes
        echo ""
        check_progress
        ;;
    stop|kill)
        stop_all
        ;;
    start)
        start_pipeline
        ;;
    log|logs)
        show_log "${2:-50}"
        ;;
    follow|tail)
        follow_log
        ;;
    progress)
        check_progress
        ;;
    *)
        echo "Usage: $0 {status|stop|start|log|follow|progress}"
        echo ""
        echo "Commands:"
        echo "  status   - Show running processes and progress (default)"
        echo "  stop     - Stop all running processes"
        echo "  start    - Start the training pipeline"
        echo "  log [N]  - Show last N lines of log (default: 50)"
        echo "  follow   - Follow log in real-time"
        echo "  progress - Show data generation progress"
        exit 1
        ;;
esac
