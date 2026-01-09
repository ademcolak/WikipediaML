#!/bin/bash
################################################################################
# AWS Configuration Example for WikipediaML
# Copy this file to config.sh and update with your values
################################################################################

# EC2 Instance Configuration
export EC2_HOST="ec2-user@your-instance-ip-or-dns"
export EC2_KEY="~/.ssh/your-key.pem"
export EC2_PROJECT_DIR="~/WikipediaML"

# AWS Region
export AWS_REGION="us-east-1"

# Recommended EC2 Instance Types (On-Demand Prices)
# Budget Options:
# - t3.large:   2 vCPU, 8 GB RAM   (~$0.08/hour) - Test only (1K-10K pages)
# - t3.xlarge:  4 vCPU, 16 GB RAM  (~$0.17/hour) - Small datasets (100K pages)
# - m5.xlarge:  4 vCPU, 16 GB RAM  (~$0.19/hour) - Medium datasets
# - m5.2xlarge: 8 vCPU, 32 GB RAM  (~$0.38/hour) - Full Wikipedia (RECOMMENDED)
# - c5.2xlarge: 8 vCPU, 16 GB RAM  (~$0.34/hour) - CPU intensive

# 💰 SPOT INSTANCE (70% CHEAPER - HIGHLY RECOMMENDED!)
# Same instances but ~70% discount. Training auto-resumes from checkpoints if interrupted.
# - t3.xlarge Spot:  ~$0.05/hour (was $0.17) - Save $0.12/hour
# - m5.xlarge Spot:  ~$0.06/hour (was $0.19) - Save $0.13/hour
# - m5.2xlarge Spot: ~$0.11/hour (was $0.38) - Save $0.27/hour
# To use: Select "Spot" when launching instance, set max price to On-Demand price

# Storage Requirements
# - Minimum: 100 GB EBS volume (gp3)
# - Recommended: 200 GB EBS volume (for full Wikipedia + checkpoints)

# Training Time Estimates (full Wikipedia ~6M pages)
# m5.2xlarge (8 vCPU, 32 GB RAM):
# - Data download: 2-4 hours
# - Parsing: 4-8 hours
# - Graph building: 2-4 hours
# - Embeddings: 8-12 hours
# - Training data: 4-6 hours
# - MLP training: 6-12 hours
# Total: ~30-50 hours

# m5.xlarge (4 vCPU, 16 GB RAM) - Budget option:
# Total: ~60-80 hours (slower but cheaper)

# Cost Estimates (Full Wikipedia Training)
# Option 1: m5.2xlarge On-Demand (48 hours)
# - EC2: ~$18 | Storage: ~$3 | Total: ~$21

# Option 2: m5.2xlarge Spot (48 hours) - RECOMMENDED!
# - EC2: ~$5 | Storage: ~$3 | Total: ~$8 (62% savings!)

# Option 3: m5.xlarge Spot (70 hours) - Most Budget-Friendly
# - EC2: ~$4 | Storage: ~$3 | Total: ~$7 (67% savings!)

# 💡 TIP: Use Spot + Checkpoint system for maximum savings!
# Training auto-resumes if Spot instance is interrupted.