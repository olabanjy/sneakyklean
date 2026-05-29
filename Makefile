.PHONY: help build up down restart logs shell migrate makemigrations createsuperuser populate test clean prune
.PHONY: prod-build prod-up prod-down prod-restart prod-logs prod-logs-web prod-logs-celery prod-status prod-ps prod-migrate prod-collectstatic prod-check prod-shell prod-bash prod-populate prod-superuser prod-setup prod-stop

PROD_COMPOSE := docker compose --env-file .env.production -f docker-compose.deploy.yml

# Help command
help:
	@echo "Sneaky Klean - Available Commands"
	@echo "=================================="
	@echo "make build          - Build Docker images"
	@echo "make up             - Start all services"
	@echo "make down           - Stop all services"
	@echo "make restart        - Restart all services"
	@echo "make logs           - View logs (all services)"
	@echo "make logs-web       - View Django logs"
	@echo "make logs-celery    - View Celery worker logs"
	@echo "make logs-redis     - View Redis logs"
	@echo "make shell          - Open Django shell"
	@echo "make bash           - Open bash in web container"
	@echo "make migrate        - Run database migrations"
	@echo "make makemigrations - Create new migrations"
	@echo "make createsuperuser- Create Django superuser"
	@echo "make populate       - Populate services in database"
	@echo "make test           - Run all tests"
	@echo "make coverage       - Run tests with coverage"
	@echo "make lint           - Run linting checks"
	@echo "make clean          - Remove Python cache files"
	@echo "make prune          - Remove all Docker containers and volumes"
	@echo "make rebuild        - Full rebuild (prune, build, migrate, populate)"
	@echo "make status         - Show service status"
	@echo "make ps             - Show running containers"
	@echo "make prod-build     - Build production images"
	@echo "make prod-up        - Start production stack"
	@echo "make prod-down      - Stop production stack"
	@echo "make prod-restart   - Restart production stack"
	@echo "make prod-logs      - Follow production logs"
	@echo "make prod-logs-web  - Follow production web logs"
	@echo "make prod-logs-celery - Follow production celery logs"
	@echo "make prod-status    - Show production service status"
	@echo "make prod-ps        - Show production containers"
	@echo "make prod-migrate   - Run production migrations"
	@echo "make prod-collectstatic - Collect production static files"
	@echo "make prod-populate  - Seed production services"
	@echo "make prod-superuser - Create a production superuser"
	@echo "make prod-check     - Run production Django checks"
	@echo "make prod-shell     - Open production Django shell"
	@echo "make prod-bash      - Open bash in production web container"
	@echo "make prod-stop      - Stop production services"
	@echo "make prod-setup     - Build, start, migrate, and collect static for prod"

# Build Docker images
build:
	docker compose build

# Start all services
up:
	docker compose up -d
	@echo "Services started! Visit http://localhost:8000"

# Start with logs visible
up-logs:
	docker compose up

# Stop all services
down:
	docker compose down

# Restart all services
restart:
	docker compose restart

# View all logs
logs:
	docker compose logs -f

# View specific service logs
logs-web:
	docker compose logs -f web

logs-celery:
	docker compose logs -f celery

logs-redis:
	docker compose logs -f redis

logs-db:
	docker compose logs -f db

# Django shell
shell:
	docker compose exec web python manage.py shell

# Bash shell in web container
bash:
	docker compose exec web bash

# Database migrations
migrate:
	docker compose exec web python manage.py migrate

makemigrations:
	docker compose exec web python manage.py makemigrations

# Create superuser
createsuperuser:
	docker compose exec web python manage.py createsuperuser

# Populate initial data
populate:
	docker compose exec web python manage.py populate_services

# Run tests
test:
	docker compose exec web python manage.py test

# Run tests with coverage
coverage:
	docker compose exec web coverage run --source='.' manage.py test
	docker compose exec web coverage report
	docker compose exec web coverage html

# Linting
lint:
	docker compose exec web flake8 . --exclude=migrations,venv,env
	docker compose exec web black . --check

# Format code
format:
	docker compose exec web black .

# Clean Python cache
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +

# Remove all Docker containers and volumes
prune:
	docker compose down -v
	docker system prune -f

# Full rebuild
rebuild: prune build up migrate populate
	@echo "Full rebuild complete!"

# Show service status
status:
	docker compose ps

# Show running containers
ps:
	docker compose ps

# Backup database
backup-db:
	docker compose exec db pg_dump -U ${DB_USER} ${DB_NAME} > backup_$(shell date +%Y%m%d_%H%M%S).sql

# Restore database
restore-db:
	@echo "Usage: make restore-db FILE=backup_file.sql"
	docker compose exec -T db psql -U ${DB_USER} ${DB_NAME} < $(FILE)

# Check Django configuration
check:
	docker compose exec web python manage.py check

# Collect static files
collectstatic:
	docker compose exec web python manage.py collectstatic --noinput

# View Celery tasks
celery-tasks:
	docker compose exec celery celery -A sneakyklean inspect active

# Purge Celery queue
celery-purge:
	docker compose exec celery celery -A sneakyklean purge -f

# Redis CLI
redis-cli:
	docker compose exec redis redis-cli

# Show environment variables
env:
	docker compose exec web printenv | sort

# Install new packages
install:
	docker compose build --no-cache web
	docker compose up -d

# Quick start (for first time setup)
quickstart: build up migrate populate createsuperuser
	@echo "Setup complete! Visit http://localhost:8000"
	@echo "Admin: http://localhost:8000/admin"

# Development mode (with live logs)
dev: up-logs

# Production build
prod-build:
	$(PROD_COMPOSE) build

prod-up:
	$(PROD_COMPOSE) up -d --build

prod-down:
	$(PROD_COMPOSE) down

prod-restart:
	$(PROD_COMPOSE) restart

prod-logs:
	$(PROD_COMPOSE) logs -f

prod-logs-web:
	$(PROD_COMPOSE) logs -f web

prod-logs-celery:
	$(PROD_COMPOSE) logs -f celery

prod-status:
	$(PROD_COMPOSE) ps

prod-ps:
	$(PROD_COMPOSE) ps

prod-shell:
	$(PROD_COMPOSE) exec web python manage.py shell

prod-bash:
	$(PROD_COMPOSE) exec web bash

prod-migrate:
	$(PROD_COMPOSE) exec web python manage.py migrate --noinput

prod-collectstatic:
	$(PROD_COMPOSE) exec web python manage.py collectstatic --noinput

prod-populate:
	$(PROD_COMPOSE) exec web python manage.py populate_services

prod-superuser:
	$(PROD_COMPOSE) exec web python manage.py createsuperuser

prod-check:
	$(PROD_COMPOSE) exec web python manage.py check

prod-stop:
	$(PROD_COMPOSE) stop

prod-setup: prod-build prod-up prod-migrate prod-collectstatic prod-populate
	@echo "Production stack started."
	@echo "If this is a fresh deployment, create a superuser with: $(PROD_COMPOSE) exec web python manage.py createsuperuser"

# Show all URLs
urls:
	docker compose exec web python manage.py show_urls

# Flush database (DANGER!)
flush:
	@echo "WARNING: This will delete all data!"
	@read -p "Are you sure? (yes/no): " confirm && [ "$$confirm" = "yes" ] || exit 1
	docker compose exec web python manage.py flush --noinput

# Create database backup directory
init-backup:
	mkdir -p backups

# Health check
health:
	@echo "Checking services health..."
	@curl -f http://localhost:8000/ > /dev/null 2>&1 && echo "✅ Web: OK" || echo "❌ Web: FAILED"
	@docker compose exec db pg_isready -U ${DB_USER} > /dev/null 2>&1 && echo "✅ Database: OK" || echo "❌ Database: FAILED"
	@docker compose exec redis redis-cli ping > /dev/null 2>&1 && echo "✅ Redis: OK" || echo "❌ Redis: FAILED"
	@docker compose exec celery celery -A sneakyklean inspect ping > /dev/null 2>&1 && echo "✅ Celery: OK" || echo "❌ Celery: FAILED"
