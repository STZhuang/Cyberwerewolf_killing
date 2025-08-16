# Cyber Werewolves Development Makefile

.PHONY: help setup dev build test clean logs shell db-reset

# Default target
help:
	@echo "Cyber Werewolves Development Commands:"
	@echo ""
	@echo "  setup     - Initial project setup"
	@echo "  dev       - Start development environment"
	@echo "  build     - Build all containers"
	@echo "  test      - Run tests"
	@echo "  clean     - Clean up containers and volumes"
	@echo "  logs      - Show service logs"
	@echo "  shell     - Open shell in specified service"
	@echo "  db-reset  - Reset database"
	@echo ""

# Initial setup
setup:
	@echo "Setting up Cyber Werewolves development environment..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env file from example"; fi
	@docker-compose pull
	@docker-compose build
	@echo "Setup complete! Run 'make dev' to start the development environment."

# Start development environment
dev:
	@echo "Starting development environment..."
	@docker-compose up -d postgres redis
	@echo "Waiting for database to be ready..."
	@sleep 10
	@docker-compose up api agents web

# Build all containers
build:
	@echo "Building all containers..."
	@docker-compose build

# Start production environment
prod:
	@echo "Starting production environment..."
	@docker-compose --profile production up -d

# Run tests
test:
	@echo "Running tests..."
	@docker-compose exec api python -m pytest
	@docker-compose exec web npm run test

# Clean up everything
clean:
	@echo "Cleaning up containers and volumes..."
	@docker-compose down -v
	@docker system prune -f
	@docker volume prune -f

# Show logs
logs:
	@docker-compose logs -f

# Show logs for specific service
logs-%:
	@docker-compose logs -f $*

# Open shell in specified service
shell-%:
	@docker-compose exec $* /bin/sh

# Reset database
db-reset:
	@echo "Resetting database..."
	@docker-compose stop postgres
	@docker-compose rm -f postgres
	@docker volume rm cyber_werewolves_postgres_data 2>/dev/null || true
	@docker-compose up -d postgres
	@echo "Database reset complete!"

# Database migration
db-migrate:
	@echo "Running database migrations..."
	@docker-compose exec api alembic upgrade head

# Create new migration
db-migration:
	@echo "Creating new migration..."
	@docker-compose exec api alembic revision --autogenerate -m "$(name)"

# Install dependencies
install:
	@echo "Installing dependencies..."
	@docker-compose exec api pip install -r requirements.txt
	@docker-compose exec agents pip install -r requirements.txt
	@docker-compose exec web npm install

# Format code
format:
	@echo "Formatting code..."
	@docker-compose exec api black app/
	@docker-compose exec api isort app/
	@docker-compose exec agents black .
	@docker-compose exec agents isort .
	@docker-compose exec web npm run format

# Lint code
lint:
	@echo "Linting code..."
	@docker-compose exec api flake8 app/
	@docker-compose exec agents flake8 .
	@docker-compose exec web npm run lint

# Generate API documentation
docs:
	@echo "Generating API documentation..."
	@echo "FastAPI docs available at: http://localhost:8000/docs"
	@echo "Agent API docs available at: http://localhost:8001/docs"

# Backup database
backup:
	@echo "Creating database backup..."
	@mkdir -p backups
	@docker-compose exec -T postgres pg_dump -U werewolves cyber_werewolves > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Backup created in backups/ directory"

# Restore database from backup
restore:
	@echo "Restoring database from backup..."
	@if [ -z "$(file)" ]; then echo "Usage: make restore file=backup_file.sql"; exit 1; fi
	@docker-compose exec -T postgres psql -U werewolves -d cyber_werewolves < $(file)
	@echo "Database restored from $(file)"

# Health check
health:
	@echo "Checking service health..."
	@curl -f http://localhost:8000/health && echo " - API: OK" || echo " - API: FAIL"
	@curl -f http://localhost:8001/ && echo " - Agents: OK" || echo " - Agents: FAIL"
	@curl -f http://localhost:3000/ && echo " - Web: OK" || echo " - Web: FAIL"

# Monitor resources
monitor:
	@echo "Monitoring container resources..."
	@docker stats