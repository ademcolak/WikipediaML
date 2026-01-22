#!/bin/bash
################################################################################
# Quick Deploy Script for WikipediaML on AWS EC2
# This script helps you quickly deploy to a new EC2 instance
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
cat << "EOF"
╔══════════════════════════════════════════════════════════╗
║         WikipediaML AWS EC2 Quick Deploy                ║
║                                                          ║
║  This script will help you deploy WikipediaML to EC2    ║
╚══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Check if config exists
if [ ! -f "aws/config.sh" ]; then
    echo -e "${YELLOW}⚠️  Config file not found. Creating from template...${NC}"
    cp aws/config.example.sh aws/config.sh
    echo -e "${GREEN}✅ Created aws/config.sh${NC}"
    echo ""
    echo -e "${YELLOW}Please edit aws/config.sh with your EC2 details:${NC}"
    echo "  - EC2_HOST: Your EC2 instance IP or DNS"
    echo "  - EC2_KEY: Path to your SSH key (.pem file)"
    echo ""
    echo "Then run this script again."
    exit 0
fi

# Load config
source aws/config.sh

echo -e "${BLUE}Configuration:${NC}"
echo "  EC2 Host: $EC2_HOST"
echo "  SSH Key:  $EC2_KEY"
echo ""

# Test connection
echo -e "${YELLOW}🔍 Testing EC2 connection...${NC}"
if ssh -i "$EC2_KEY" -o ConnectTimeout=5 "$EC2_HOST" "echo 'Connected'" &>/dev/null; then
    echo -e "${GREEN}✅ Connection successful${NC}"
else
    echo -e "${RED}❌ Cannot connect to EC2${NC}"
    echo "Please check:"
    echo "  1. EC2 instance is running"
    echo "  2. EC2_HOST is correct in aws/config.sh"
    echo "  3. EC2_KEY path is correct"
    echo "  4. Security group allows SSH from your IP"
    exit 1
fi

# Menu
echo ""
echo -e "${BLUE}What would you like to do?${NC}"
echo "  1) Setup EC2 instance (first time)"
echo "  2) Start training pipeline (run_training_pipeline.sh)"
echo "  3) Check training status"
echo "  4) Download trained models"
echo "  5) Stop training"
echo "  6) View logs"
echo "  0) Exit"
echo ""
read -p "Enter choice [0-6]: " choice

case $choice in
    1)
        echo -e "${GREEN}📦 Setting up EC2 instance...${NC}"
        
        # Upload setup script
        scp -i "$EC2_KEY" aws/ec2_setup.sh "$EC2_HOST:~/"
        
        # Run setup
        ssh -i "$EC2_KEY" "$EC2_HOST" "chmod +x ~/ec2_setup.sh && ~/ec2_setup.sh"
        
        echo -e "${GREEN}✅ Setup complete!${NC}"
        ;;
        
    2)
        echo -e "${GREEN}🚀 Starting training pipeline...${NC}"
        
        # Upload training script
        scp -i "$EC2_KEY" aws/run_training_pipeline.sh "$EC2_HOST:~/WikipediaML/aws/"
        
        # Start training in background
        ssh -i "$EC2_KEY" "$EC2_HOST" << 'ENDSSH'
cd ~/WikipediaML
source venv/bin/activate
chmod +x aws/run_training_pipeline.sh
nohup ./aws/run_training_pipeline.sh > logs/training.log 2>&1 &
echo $! > training.pid
echo "Training started with PID: $(cat training.pid)"
ENDSSH
        
        echo -e "${GREEN}✅ Training started!${NC}"
        echo "Monitor with: $0 (choose option 3)"
        ;;
        
    3)
        echo -e "${YELLOW}📊 Checking training status...${NC}"
        ./aws/sync_data.sh status
        ;;
        
    4)
        echo -e "${GREEN}📥 Downloading trained models...${NC}"
        ./aws/sync_data.sh download
        echo -e "${GREEN}✅ Download complete!${NC}"
        ;;
        
    5)
        echo -e "${YELLOW}🛑 Stopping training...${NC}"
        ssh -i "$EC2_KEY" "$EC2_HOST" << 'ENDSSH'
if [ -f ~/WikipediaML/training.pid ]; then
    PID=$(cat ~/WikipediaML/training.pid)
    kill $PID 2>/dev/null || true
    echo "Training stopped (PID: $PID)"
else
    pkill -f run_training_pipeline || true
    echo "Training processes stopped"
fi
ENDSSH
        echo -e "${GREEN}✅ Training stopped${NC}"
        ;;
        
    6)
        echo -e "${YELLOW}📋 Viewing logs (Ctrl+C to exit)...${NC}"
        ssh -i "$EC2_KEY" "$EC2_HOST" "tail -f ~/WikipediaML/logs/training.log"
        ;;
        
    0)
        echo "Goodbye!"
        exit 0
        ;;
        
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac