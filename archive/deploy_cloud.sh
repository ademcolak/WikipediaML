#!/bin/bash
# WikipediaML Cloud Deployment Script
# Hızlı cloud deployment için otomatik script

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Main menu
show_menu() {
    clear
    print_header "☁️  WikipediaML Cloud Deployment"
    echo ""
    echo "Hangi platformda eğitim yapmak istiyorsunuz?"
    echo ""
    echo "1) AWS EC2 (Genel amaçlı, güvenilir)"
    echo "2) Google Cloud (ML odaklı, $300 kredi)"
    echo "3) Azure (Microsoft ekosistemi)"
    echo "4) Vast.ai (En ucuz GPU)"
    echo "5) Docker (Yerel test)"
    echo "6) Çıkış"
    echo ""
    read -p "Seçiminiz (1-6): " choice
}

# AWS Deployment
deploy_aws() {
    print_header "AWS EC2 Deployment"
    
    # Check AWS CLI
    if ! command_exists aws; then
        print_error "AWS CLI bulunamadı!"
        print_info "Kurulum: brew install awscli (macOS) veya pip install awscli"
        return 1
    fi
    
    print_success "AWS CLI bulundu"
    
    # Get configuration
    read -p "Instance type (t3.xlarge/g4dn.xlarge) [t3.xlarge]: " instance_type
    instance_type=${instance_type:-t3.xlarge}
    
    read -p "Spot instance kullan? (70% daha ucuz) (y/n) [y]: " use_spot
    use_spot=${use_spot:-y}
    
    read -p "Key pair adı: " key_name
    
    read -p "Security group ID: " sg_id
    
    # Launch instance
    print_info "Instance başlatılıyor..."
    
    if [ "$use_spot" = "y" ]; then
        instance_id=$(aws ec2 run-instances \
            --image-id ami-0c55b159cbfafe1f0 \
            --instance-type "$instance_type" \
            --key-name "$key_name" \
            --security-group-ids "$sg_id" \
            --instance-market-options '{"MarketType":"spot"}' \
            --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":50}}]' \
            --query 'Instances[0].InstanceId' \
            --output text)
    else
        instance_id=$(aws ec2 run-instances \
            --image-id ami-0c55b159cbfafe1f0 \
            --instance-type "$instance_type" \
            --key-name "$key_name" \
            --security-group-ids "$sg_id" \
            --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":50}}]' \
            --query 'Instances[0].InstanceId' \
            --output text)
    fi
    
    print_success "Instance oluşturuldu: $instance_id"
    print_info "Instance başlatılıyor, lütfen bekleyin..."
    
    aws ec2 wait instance-running --instance-ids "$instance_id"
    
    # Get public IP
    public_ip=$(aws ec2 describe-instances \
        --instance-ids "$instance_id" \
        --query 'Reservations[0].Instances[0].PublicIpAddress' \
        --output text)
    
    print_success "Instance hazır: $public_ip"
    
    # Show connection command
    echo ""
    print_header "Bağlantı Bilgileri"
    echo "Instance ID: $instance_id"
    echo "Public IP: $public_ip"
    echo ""
    echo "SSH Bağlantısı:"
    echo "  ssh -i $key_name.pem ubuntu@$public_ip"
    echo ""
    echo "Kurulum Komutları:"
    echo "  git clone https://github.com/your-username/WikipediaML.git"
    echo "  cd WikipediaML"
    echo "  pip install -r requirements.txt"
    echo "  python train_cloud.py"
    echo ""
    
    read -p "Instance'ı şimdi durdurmak ister misiniz? (y/n): " stop_now
    if [ "$stop_now" = "y" ]; then
        aws ec2 stop-instances --instance-ids "$instance_id"
        print_success "Instance durduruldu"
    fi
}

# GCP Deployment
deploy_gcp() {
    print_header "Google Cloud Deployment"
    
    # Check gcloud CLI
    if ! command_exists gcloud; then
        print_error "gcloud CLI bulunamadı!"
        print_info "Kurulum: brew install google-cloud-sdk (macOS)"
        return 1
    fi
    
    print_success "gcloud CLI bulundu"
    
    # Get configuration
    read -p "Project ID: " project_id
    gcloud config set project "$project_id"
    
    read -p "Zone [us-central1-a]: " zone
    zone=${zone:-us-central1-a}
    
    read -p "Machine type (n1-standard-4/n1-standard-4+GPU) [n1-standard-4]: " machine_type
    machine_type=${machine_type:-n1-standard-4}
    
    read -p "Preemptible kullan? (80% daha ucuz) (y/n) [y]: " use_preemptible
    use_preemptible=${use_preemptible:-y}
    
    # Launch instance
    print_info "VM instance oluşturuluyor..."
    
    cmd="gcloud compute instances create wikipediaml-trainer \
        --zone=$zone \
        --machine-type=$machine_type \
        --image-family=ubuntu-2004-lts \
        --image-project=ubuntu-os-cloud \
        --boot-disk-size=50GB"
    
    if [ "$use_preemptible" = "y" ]; then
        cmd="$cmd --preemptible"
    fi
    
    eval "$cmd"
    
    print_success "VM instance oluşturuldu"
    
    # Show connection command
    echo ""
    print_header "Bağlantı Bilgileri"
    echo "SSH Bağlantısı:"
    echo "  gcloud compute ssh wikipediaml-trainer --zone=$zone"
    echo ""
    echo "Kurulum Komutları:"
    echo "  git clone https://github.com/your-username/WikipediaML.git"
    echo "  cd WikipediaML"
    echo "  pip install -r requirements.txt"
    echo "  python train_cloud.py --upload-gcs --gcs-bucket your-bucket"
    echo ""
}

# Docker Deployment
deploy_docker() {
    print_header "Docker Deployment"
    
    # Check Docker
    if ! command_exists docker; then
        print_error "Docker bulunamadı!"
        print_info "Kurulum: https://docs.docker.com/get-docker/"
        return 1
    fi
    
    print_success "Docker bulundu"
    
    # Build image
    print_info "Docker image oluşturuluyor..."
    docker build -t wikipediaml-trainer .
    
    print_success "Docker image oluşturuldu"
    
    # Run container
    read -p "Şimdi çalıştırmak ister misiniz? (y/n) [y]: " run_now
    run_now=${run_now:-y}
    
    if [ "$run_now" = "y" ]; then
        print_info "Container başlatılıyor..."
        docker run -v "$(pwd)/cache:/app/cache" wikipediaml-trainer
    else
        echo ""
        print_info "Manuel çalıştırma komutu:"
        echo "  docker run -v \$(pwd)/cache:/app/cache wikipediaml-trainer"
    fi
}

# Vast.ai Deployment
deploy_vastai() {
    print_header "Vast.ai Deployment"
    
    print_info "Vast.ai web arayüzünden instance oluşturun:"
    echo ""
    echo "1. https://vast.ai/ adresine gidin"
    echo "2. 'Search' sekmesinden GPU seçin"
    echo "3. 'PyTorch' template seçin"
    echo "4. Instance başlatın"
    echo "5. SSH ile bağlanın"
    echo ""
    echo "Kurulum Komutları:"
    echo "  git clone https://github.com/your-username/WikipediaML.git"
    echo "  cd WikipediaML"
    echo "  pip install -r requirements.txt"
    echo "  python train_cloud.py"
    echo ""
    
    read -p "Devam etmek için Enter'a basın..."
}

# Main script
main() {
    while true; do
        show_menu
        
        case $choice in
            1)
                deploy_aws
                ;;
            2)
                deploy_gcp
                ;;
            3)
                print_warning "Azure deployment yakında eklenecek!"
                print_info "Manuel kurulum için: docs/CLOUD_TRAINING_GUIDE.md"
                ;;
            4)
                deploy_vastai
                ;;
            5)
                deploy_docker
                ;;
            6)
                print_info "Çıkılıyor..."
                exit 0
                ;;
            *)
                print_error "Geçersiz seçim!"
                ;;
        esac
        
        echo ""
        read -p "Ana menüye dönmek için Enter'a basın..."
    done
}

# Run main
main