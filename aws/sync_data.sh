#!/bin/bash
################################################################################
# Data Sync Script for WikipediaML
# Syncs trained models and data between EC2 and local machine
################################################################################

# Configuration - UPDATE THESE VALUES
EC2_HOST="${EC2_HOST:-ec2-user@your-instance-ip}"
EC2_KEY="${EC2_KEY:-~/.ssh/your-key.pem}"
EC2_PROJECT_DIR="${EC2_PROJECT_DIR:-~/WikipediaML}"
LOCAL_PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print usage
usage() {
    echo "Usage: $0 [download|upload|status]"
    echo ""
    echo "Commands:"
    echo "  download  - Download trained models and data from EC2 to local"
    echo "  upload    - Upload local data to EC2"
    echo "  status    - Check EC2 training status"
    echo ""
    echo "Environment variables:"
    echo "  EC2_HOST          - EC2 instance address (default: ec2-user@your-instance-ip)"
    echo "  EC2_KEY           - Path to SSH key (default: ~/.ssh/your-key.pem)"
    echo "  EC2_PROJECT_DIR   - Project directory on EC2 (default: ~/WikipediaML)"
    echo ""
    echo "Example:"
    echo "  EC2_HOST=ec2-user@1.2.3.4 EC2_KEY=~/.ssh/mykey.pem $0 download"
    exit 1
}

# Check if EC2 is reachable
check_connection() {
    echo -e "${YELLOW}🔍 Checking EC2 connection...${NC}"
    if ssh -i "$EC2_KEY" -o ConnectTimeout=5 "$EC2_HOST" "echo 'Connected'" &>/dev/null; then
        echo -e "${GREEN}✅ EC2 connection successful${NC}"
        return 0
    else
        echo -e "${RED}❌ Cannot connect to EC2${NC}"
        echo "Please check:"
        echo "  - EC2_HOST is correct"
        echo "  - EC2_KEY path is correct"
        echo "  - EC2 instance is running"
        echo "  - Security group allows SSH (port 22)"
        return 1
    fi
}

# Download data from EC2
download_data() {
    echo -e "${GREEN}📥 Downloading data from EC2...${NC}"
    
    # Create local data directory
    mkdir -p "$LOCAL_PROJECT_DIR/data"
    mkdir -p "$LOCAL_PROJECT_DIR/models"
    
    # Download trained models
    echo "Downloading models..."
    rsync -avz --progress -e "ssh -i $EC2_KEY" \
        "$EC2_HOST:$EC2_PROJECT_DIR/models/" \
        "$LOCAL_PROJECT_DIR/models/" || true
    
    # Download data files (excluding large dumps)
    echo "Downloading data files..."
    rsync -avz --progress -e "ssh -i $EC2_KEY" \
        --exclude='wikipedia_dumps/' \
        --exclude='*.sql.gz' \
        "$EC2_HOST:$EC2_PROJECT_DIR/data/" \
        "$LOCAL_PROJECT_DIR/data/" || true
    
    # Download latest checkpoint
    echo "Downloading latest checkpoint..."
    LATEST_CHECKPOINT=$(ssh -i "$EC2_KEY" "$EC2_HOST" \
        "ls -t $EC2_PROJECT_DIR/data/checkpoints/final_checkpoint_*.tar.gz 2>/dev/null | head -1" || echo "")
    
    if [ -n "$LATEST_CHECKPOINT" ]; then
        mkdir -p "$LOCAL_PROJECT_DIR/data/checkpoints"
        scp -i "$EC2_KEY" "$EC2_HOST:$LATEST_CHECKPOINT" \
            "$LOCAL_PROJECT_DIR/data/checkpoints/" || true
        echo -e "${GREEN}✅ Latest checkpoint downloaded${NC}"
    else
        echo -e "${YELLOW}⚠️  No checkpoint found${NC}"
    fi
    
    echo -e "${GREEN}✅ Download complete!${NC}"
    echo ""
    echo "Downloaded files are in:"
    echo "  Models: $LOCAL_PROJECT_DIR/models/"
    echo "  Data:   $LOCAL_PROJECT_DIR/data/"
}

# Upload data to EC2
upload_data() {
    echo -e "${GREEN}📤 Uploading data to EC2...${NC}"
    
    # Upload models
    if [ -d "$LOCAL_PROJECT_DIR/models" ]; then
        echo "Uploading models..."
        rsync -avz --progress -e "ssh -i $EC2_KEY" \
            "$LOCAL_PROJECT_DIR/models/" \
            "$EC2_HOST:$EC2_PROJECT_DIR/models/" || true
    fi
    
    # Upload data files (excluding large dumps)
    if [ -d "$LOCAL_PROJECT_DIR/data" ]; then
        echo "Uploading data files..."
        rsync -avz --progress -e "ssh -i $EC2_KEY" \
            --exclude='wikipedia_dumps/' \
            --exclude='*.sql.gz' \
            "$LOCAL_PROJECT_DIR/data/" \
            "$EC2_HOST:$EC2_PROJECT_DIR/data/" || true
    fi
    
    echo -e "${GREEN}✅ Upload complete!${NC}"
}

# Check training status on EC2
check_status() {
    echo -e "${YELLOW}📊 Checking EC2 training status...${NC}"
    echo ""
    
    # Check if training is running
    TRAINING_PID=$(ssh -i "$EC2_KEY" "$EC2_HOST" \
        "pgrep -f 'run_training_pipeline.sh' || echo ''" 2>/dev/null)
    
    if [ -n "$TRAINING_PID" ]; then
        echo -e "${GREEN}✅ Training is running (PID: $TRAINING_PID)${NC}"
    else
        echo -e "${YELLOW}⚠️  Training is not running${NC}"
    fi
    
    # Show last 20 lines of training log
    echo ""
    echo "Recent training log:"
    echo "-------------------"
    ssh -i "$EC2_KEY" "$EC2_HOST" \
        "tail -20 $EC2_PROJECT_DIR/logs/training.log 2>/dev/null || echo 'No log file found'" || true
    
    # Show disk usage
    echo ""
    echo "Disk usage:"
    echo "-----------"
    ssh -i "$EC2_KEY" "$EC2_HOST" \
        "df -h $EC2_PROJECT_DIR | tail -1" || true
    
    # List checkpoints
    echo ""
    echo "Available checkpoints:"
    echo "---------------------"
    ssh -i "$EC2_KEY" "$EC2_HOST" \
        "ls -lh $EC2_PROJECT_DIR/data/checkpoints/*.tar.gz 2>/dev/null || echo 'No checkpoints found'" || true
}

# Main script
main() {
    if [ $# -eq 0 ]; then
        usage
    fi
    
    # Check connection first
    if ! check_connection; then
        exit 1
    fi
    
    case "$1" in
        download)
            download_data
            ;;
        upload)
            upload_data
            ;;
        status)
            check_status
            ;;
        *)
            usage
            ;;
    esac
}

main "$@"