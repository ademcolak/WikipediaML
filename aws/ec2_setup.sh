#!/bin/bash
################################################################################
# AWS EC2 Instance Setup Script for WikipediaML
# This script prepares an EC2 instance for Wikipedia Knowledge Graph training
################################################################################

set -e  # Exit on error

echo "=================================="
echo "WikipediaML EC2 Setup"
echo "=================================="

# Update system packages
echo "📦 Updating system packages..."
sudo yum update -y || sudo apt-get update -y

# Install Python 3 and development tools
echo "🐍 Installing Python 3 and development tools..."
if command -v yum &> /dev/null; then
    # Amazon Linux / CentOS
    sudo yum install -y python3 python3-devel python3-pip git gcc gcc-c++ make
else
    # Ubuntu / Debian
    sudo apt-get install -y python3 python3-dev python3-pip git gcc g++ make
fi

# Install system dependencies for igraph
echo "📚 Installing igraph system dependencies..."
if command -v yum &> /dev/null; then
    sudo yum install -y libxml2-devel zlib-devel
else
    sudo apt-get install -y libxml2-dev zlib1g-dev
fi

# Upgrade pip
echo "⬆️  Upgrading pip..."
python3 -m pip install --upgrade pip

# Clone or update repository
REPO_URL="https://github.com/ademcolak/WikipediaML.git"
PROJECT_DIR="$HOME/WikipediaML"

if [ -d "$PROJECT_DIR" ]; then
    echo "📂 Project directory exists, pulling latest changes..."
    cd "$PROJECT_DIR"
    git pull
else
    echo "📥 Cloning repository..."
    git clone "$REPO_URL" "$PROJECT_DIR"
    cd "$PROJECT_DIR"
fi

# Create virtual environment
echo "🔧 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment and install dependencies
echo "📦 Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating data directories..."
mkdir -p data/wikipedia_dumps
mkdir -p data/checkpoints
mkdir -p models
mkdir -p logs

# Set up cron job for automatic checkpointing (optional)
echo "⏰ Setting up automatic backup cron job..."
CRON_JOB="0 */6 * * * cd $PROJECT_DIR && tar -czf data/checkpoints/backup_\$(date +\%Y\%m\%d_\%H\%M).tar.gz data/*.pkl models/*.pt"
(crontab -l 2>/dev/null | grep -v "WikipediaML backup"; echo "$CRON_JOB") | crontab -

echo ""
echo "=================================="
echo "✅ Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Activate virtual environment:"
echo "   cd $PROJECT_DIR"
echo "   source venv/bin/activate"
echo ""
echo "2. Start the training pipeline:"
echo "   ./aws/run_training_pipeline.sh"
echo ""
echo "3. Monitor progress:"
echo "   tail -f logs/training.log"
echo ""
echo "4. To run in background (recommended):"
echo "   nohup ./aws/run_training_pipeline.sh > logs/training.log 2>&1 &"
echo ""