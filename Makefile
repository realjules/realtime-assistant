.PHONY: help build dev prod stop logs shell clean

# Default target
help:
	@echo "Sasabot Docker Commands:"
	@echo "  build    - Build the Docker image"
	@echo "  dev      - Start development environment"
	@echo "  prod     - Start production environment"
	@echo "  stop     - Stop all containers"
	@echo "  logs     - View container logs"
	@echo "  shell    - Access container shell"
	@echo "  clean    - Clean up Docker resources"
	@echo ""
	@echo "First time setup:"
	@echo "  1. Copy .env.example to .env"
	@echo "  2. Add your OPENAI_API_KEY to .env"
	@echo "  3. Run 'make dev'"

# Build the Docker image
build:
	docker-compose build

# Start development environment
dev:
	@echo "Starting Sasabot development environment..."
	docker-compose up -d
	@echo "Sasabot is running at http://localhost:8000"
	docker-compose logs -f

# Start production environment
prod:
	@echo "Starting Sasabot production environment..."
	docker-compose -f docker-compose.prod.yml up -d
	@echo "Sasabot is running at http://localhost:8000"

# Stop all containers
stop:
	docker-compose down
	docker-compose -f docker-compose.prod.yml down

# View logs
logs:
	docker-compose logs -f

# Access container shell
shell:
	docker-compose exec sasabot bash

# Clean up Docker resources
clean:
	docker-compose down -v
	docker system prune -f

# Rebuild everything from scratch
rebuild:
	docker-compose down -v
	docker-compose build --no-cache
	docker-compose up -d