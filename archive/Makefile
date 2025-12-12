.PHONY: help install start stop restart logs clean test

# Default target
help:
	@echo "WikipediaML - Makefile Commands"
	@echo "================================"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install          - Install Python dependencies"
	@echo "  make setup            - Full setup (install + start services)"
	@echo ""
	@echo "Docker Services:"
	@echo "  make start            - Start Neo4j + Redis"
	@echo "  make stop             - Stop all services"
	@echo "  make restart          - Restart all services"
	@echo "  make logs             - Show service logs"
	@echo "  make status           - Check service status"
	@echo ""
	@echo "Database:"
	@echo "  make neo4j-shell      - Open Neo4j Cypher shell"
	@echo "  make redis-cli        - Open Redis CLI"
	@echo "  make neo4j-browser    - Open Neo4j Browser (http://localhost:7474)"
	@echo ""
	@echo "Training:"
	@echo "  make train            - Train ML model (50 pairs)"
	@echo "  make train-large      - Train ML model (500 pairs)"
	@echo "  make train-bg         - Train in background"
	@echo ""
	@echo "Testing:"
	@echo "  make test             - Run quick test"
	@echo "  make test-ml          - Test with ML mode"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            - Clean cache files"
	@echo "  make clean-all        - Clean everything (including Docker volumes)"
	@echo ""

# Installation
install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt
	@echo "✅ Dependencies installed!"

# Full setup
setup: install start
	@echo "⏳ Waiting for services to be ready..."
	@sleep 10
	@echo "✅ Setup complete!"
	@echo ""
	@echo "🌐 Neo4j Browser: http://localhost:7474"
	@echo "   Username: neo4j"
	@echo "   Password: wikipediaml123"
	@echo ""
	@echo "🚀 Ready to use!"

# Docker services
start:
	@echo "🚀 Starting Neo4j + Redis..."
	docker-compose up -d
	@echo "✅ Services started!"
	@echo ""
	@echo "🌐 Neo4j Browser: http://localhost:7474"
	@echo "📊 Neo4j Bolt: bolt://localhost:7687"
	@echo "🔴 Redis: localhost:6379"

stop:
	@echo "🛑 Stopping services..."
	docker-compose down
	@echo "✅ Services stopped!"

restart:
	@echo "🔄 Restarting services..."
	docker-compose restart
	@echo "✅ Services restarted!"

logs:
	docker-compose logs -f

status:
	@echo "📊 Service Status:"
	@docker-compose ps

# Database access
neo4j-shell:
	@echo "🔵 Opening Neo4j Cypher Shell..."
	@echo "Password: wikipediaml123"
	docker exec -it wikipediaml-neo4j cypher-shell -u neo4j -p wikipediaml123

redis-cli:
	@echo "🔴 Opening Redis CLI..."
	docker exec -it wikipediaml-redis redis-cli

neo4j-browser:
	@echo "🌐 Opening Neo4j Browser..."
	@echo "URL: http://localhost:7474"
	@echo "Username: neo4j"
	@echo "Password: wikipediaml123"
	@open http://localhost:7474 2>/dev/null || xdg-open http://localhost:7474 2>/dev/null || echo "Please open: http://localhost:7474"

# Training
train:
	@echo "🎓 Training ML model (50 pairs)..."
	python train_ml_model_curated.py --limit 50

train-large:
	@echo "🎓 Training ML model (500 pairs)..."
	python generate_large_dataset.py --count 500
	python train_ml_model_curated.py --dataset training_dataset_large.json

train-bg:
	@echo "🎓 Training ML model in background..."
	nohup python train_ml_model_curated.py > training.log 2>&1 &
	@echo "✅ Training started in background"
	@echo "📊 Monitor with: tail -f training.log"

# Testing
test:
	@echo "🧪 Running quick test..."
	python main.py "Albert_Einstein" "Physics" --async

test-ml:
	@echo "🧪 Testing with ML mode..."
	python main.py "Potato" "Pizza" --async --ml

# Cleanup
clean:
	@echo "🧹 Cleaning cache files..."
	rm -rf cache/*.pkl
	rm -f training.log
	@echo "✅ Cache cleaned!"

clean-all: stop
	@echo "🧹 Cleaning everything..."
	docker-compose down -v
	rm -rf cache/
	rm -f training.log
	@echo "✅ Everything cleaned!"

# Development
dev:
	@echo "🔧 Starting development environment..."
	@make start
	@echo "✅ Development environment ready!"