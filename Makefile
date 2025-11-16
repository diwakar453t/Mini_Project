.PHONY: dev init-db seed test build clean dev-reset dev-logs logs-backend logs-frontend

# detect docker compose command (docker compose or docker-compose)
DC := $(shell command -v docker-compose >/dev/null 2>&1 && echo docker-compose || echo docker compose)

# Development commands
dev:
	docker-compose up -d
	@echo "🚀 Development environment started!"
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:5173"
	@echo "Docs: http://localhost:8000/docs"

dev-logs:
	docker-compose logs -f

# Database commands
init-db:
	docker-compose exec backend alembic upgrade head
	@echo "✅ Database initialized with latest migrations"

seed:
	docker-compose exec backend python scripts/seed_data.py
	@echo "✅ Sample data seeded successfully"

reset-db:
	docker-compose exec backend alembic downgrade base
	docker-compose exec backend alembic upgrade head
	docker-compose exec backend python scripts/seed_data.py
	@echo "✅ Database reset and reseeded"

# Testing commands
test:
	@echo "Running backend tests..."
	docker-compose exec backend pytest -v
	@echo "Running frontend tests..."
	cd frontend && npm test
	@echo "✅ All tests completed"

test-backend:
	docker-compose exec backend pytest -v

test-frontend:
	cd frontend && npm test

test-e2e:
	cd frontend && npm run test:e2e

# Build commands
build:
	docker-compose -f docker-compose.prod.yml build
	@echo "✅ Production images built"

# Setup commands
install:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "✅ Dependencies installed"

# Cleanup commands
clean:
	docker-compose down -v
	docker system prune -f
	@echo "✅ Cleaned up containers and volumes"

# Development utilities
shell-backend:
	docker-compose exec backend bash

shell-db:
	docker-compose exec db psql -U chargemitra -d chargemitra

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

# Deployment commands
deploy-staging:
	./scripts/deploy_staging.sh

dev-reset:
	@echo "Bringing stack down and pruning volumes..."
	$(DC) down -v || true
	@echo "Building images (no cache)..."
	$(DC) build --no-cache
	@echo "Starting services..."
	$(DC) up -d
	@echo "Waiting for DB to become healthy..."
	@attempts=0; \
	until [ $$attempts -ge 20 ] || $(DC) ps | grep db | grep -q "(healthy)"; do \
	  attempts=$$((attempts+1)); \
	  echo "  ⏳ waiting for db health (attempt $$attempts/20)"; \
	  sleep 3; \
	done; \
	if ! $(DC) ps | grep db | grep -q "(healthy)"; then \
	  echo "❌ DB not healthy after waiting"; exit 1; \
	fi
	@echo "Running migrations..."
	$(DC) exec backend alembic upgrade head
	@echo "Seeding data..."
	$(DC) exec backend python scripts/seed_data.py
	@echo "✅ Dev stack is ready: Frontend http://localhost:5173 — Backend http://localhost:8000/docs"

deploy-production:
	./scripts/deploy_production.sh

# Code quality
lint:
	cd backend && flake8 app/ tests/
	cd backend && black app/ tests/ --check
	cd frontend && npm run lint

format:
	cd backend && black app/ tests/
	cd frontend && npm run format

# Utilities
backup-db:
	docker-compose exec db pg_dump -U chargemitra chargemitra > backup_$(shell date +%Y%m%d_%H%M%S).sql

restore-db:
	@read -p "Enter backup file path: " file; \
	docker-compose exec -T db psql -U chargemitra -d chargemitra < $$file