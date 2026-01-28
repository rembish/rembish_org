.PHONY: help dev up down logs clean \
        backend-run backend-shell backend-lint backend-format backend-typecheck backend-test \
        frontend-dev frontend-build frontend-lint frontend-format frontend-typecheck \
        db-migrate db-revision db-shell \
        lint format typecheck test \
        version version-check version-sync tag \
        build-prod build-backend-prod build-frontend-prod \
        cv-pdf

.DEFAULT_GOAL := help

# Paths
BACKEND_DIR := app/backend
FRONTEND_DIR := app/frontend
COMPOSE_FILE := docker-compose.dev.yaml
VENV := .venv/bin

##@ General

help: ## Show this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} \
		/^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } \
		/^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' $(MAKEFILE_LIST)

venv: ## Create .venv and install backend dependencies
	python3 -m venv .venv
	$(VENV)/pip install -e "$(BACKEND_DIR)[dev]"

install: venv frontend-install ## Install all dependencies (backend + frontend)

setup: install ## Alias for install

##@ Development (Docker)

dev: up ## Start development environment (alias for 'up')

up: ## Start all services with docker-compose
	docker compose -f $(COMPOSE_FILE) up --build

up-detached: ## Start all services in background
	docker compose -f $(COMPOSE_FILE) up --build -d

down: ## Stop all services
	docker compose -f $(COMPOSE_FILE) down

logs: ## Tail logs from all services
	docker compose -f $(COMPOSE_FILE) logs -f

logs-backend: ## Tail logs from backend only
	docker compose -f $(COMPOSE_FILE) logs -f backend

logs-frontend: ## Tail logs from frontend only
	docker compose -f $(COMPOSE_FILE) logs -f frontend

clean: ## Stop services and remove volumes
	docker compose -f $(COMPOSE_FILE) down -v

##@ Backend

backend-run: ## Run backend locally (uses .venv)
	cd $(BACKEND_DIR) && ../../$(VENV)/uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

backend-shell: ## Open shell in running backend container
	docker compose -f $(COMPOSE_FILE) exec backend sh

backend-lint: ## Run ruff linter on backend
	$(VENV)/ruff check $(BACKEND_DIR)/src/

backend-lint-fix: ## Run ruff linter with auto-fix
	$(VENV)/ruff check $(BACKEND_DIR)/src/ --fix

backend-format: ## Format backend code with ruff
	$(VENV)/ruff format $(BACKEND_DIR)/src/

backend-format-check: ## Check backend formatting without changes
	$(VENV)/ruff format $(BACKEND_DIR)/src/ --check

backend-typecheck: ## Run mypy on backend
	cd $(BACKEND_DIR) && ../../$(VENV)/mypy src/

backend-test: ## Run backend tests
	cd $(BACKEND_DIR) && ../../$(VENV)/pytest

##@ Frontend

frontend-dev: ## Run frontend dev server locally
	cd $(FRONTEND_DIR) && npm run dev

frontend-build: ## Build frontend for production
	cd $(FRONTEND_DIR) && npm run build

frontend-lint: ## Run eslint on frontend
	cd $(FRONTEND_DIR) && npm run lint

frontend-lint-fix: ## Run eslint with auto-fix
	cd $(FRONTEND_DIR) && npm run lint -- --fix

frontend-format: ## Format frontend code with prettier
	cd $(FRONTEND_DIR) && npm run format

frontend-format-check: ## Check frontend formatting without changes
	cd $(FRONTEND_DIR) && npm run format:check

frontend-typecheck: ## Run TypeScript type checking
	cd $(FRONTEND_DIR) && npx tsc --noEmit

frontend-install: ## Install frontend dependencies
	cd $(FRONTEND_DIR) && npm install

##@ Database

db-migrate: ## Run database migrations
	docker compose -f $(COMPOSE_FILE) exec backend alembic upgrade head

db-revision: ## Create new migration (usage: make db-revision msg="description")
	docker compose -f $(COMPOSE_FILE) exec backend alembic revision --autogenerate -m "$(msg)"

db-history: ## Show migration history
	docker compose -f $(COMPOSE_FILE) exec backend alembic history

db-shell: ## Open MySQL shell
	docker compose -f $(COMPOSE_FILE) exec database mysql -u app -pdevpassword rembish_org

##@ Combined

lint: backend-lint frontend-lint ## Run all linters

format: backend-format frontend-format ## Format all code

typecheck: backend-typecheck frontend-typecheck ## Run all type checkers

test: backend-test ## Run all tests

check: backend-format-check frontend-format-check lint typecheck ## Run formatters, linters and type checkers

##@ Production Build

build-backend-prod: ## Build backend production Docker image
	docker build -f $(BACKEND_DIR)/Dockerfile.prod -t rembish-org-backend:test $(BACKEND_DIR)

build-frontend-prod: ## Build frontend production Docker image (uses repo root for CHANGELOG.md)
	docker build -f $(FRONTEND_DIR)/Dockerfile.prod -t rembish-org-frontend:test .

build-prod: build-backend-prod build-frontend-prod ## Build all production Docker images

##@ Version Management

# Version source of truth (in sibling ops repo)
VERSION_FILE := ../rembish_org_ops/VERSION

version: ## Show current version from all sources
	@echo "VERSION file (ops):     $$(cat $(VERSION_FILE) 2>/dev/null || echo 'NOT FOUND')"
	@echo "package.json:           $$(grep -o '"version": "[^"]*"' $(FRONTEND_DIR)/package.json | cut -d'"' -f4)"
	@echo "pyproject.toml:         $$(grep '^version = ' $(BACKEND_DIR)/pyproject.toml | cut -d'"' -f2)"
	@echo "main.py (FastAPI):      $$(grep -o 'version="[^"]*"' $(BACKEND_DIR)/src/main.py | head -1 | cut -d'"' -f2)"
	@echo "main.py (info API):     $$(grep -o '"version": "[^"]*"' $(BACKEND_DIR)/src/main.py | cut -d'"' -f4)"

version-check: ## Verify all version files match VERSION
	@if [ ! -f "$(VERSION_FILE)" ]; then \
		echo "ERROR: VERSION file not found at $(VERSION_FILE)"; \
		echo "The ops repo VERSION file is the source of truth."; \
		exit 1; \
	fi; \
	VERSION=$$(cat $(VERSION_FILE) | tr -d '[:space:]'); \
	if [ -z "$$VERSION" ]; then \
		echo "ERROR: VERSION file is empty"; \
		exit 1; \
	fi; \
	if ! echo "$$VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$$'; then \
		echo "ERROR: Invalid version format '$$VERSION' (expected X.Y.Z)"; \
		exit 1; \
	fi; \
	ERRORS=0; \
	echo "Expected version: $$VERSION"; \
	echo "---"; \
	PKG=$$(grep -o '"version": "[^"]*"' $(FRONTEND_DIR)/package.json | cut -d'"' -f4); \
	if [ "$$PKG" != "$$VERSION" ]; then echo "MISMATCH package.json: $$PKG"; ERRORS=1; else echo "OK package.json"; fi; \
	PYPROJ=$$(grep '^version = ' $(BACKEND_DIR)/pyproject.toml | cut -d'"' -f2); \
	if [ "$$PYPROJ" != "$$VERSION" ]; then echo "MISMATCH pyproject.toml: $$PYPROJ"; ERRORS=1; else echo "OK pyproject.toml"; fi; \
	FASTAPI=$$(grep -o 'version="[^"]*"' $(BACKEND_DIR)/src/main.py | head -1 | cut -d'"' -f2); \
	if [ "$$FASTAPI" != "$$VERSION" ]; then echo "MISMATCH main.py (FastAPI): $$FASTAPI"; ERRORS=1; else echo "OK main.py (FastAPI)"; fi; \
	INFO=$$(grep -o '"version": "[^"]*"' $(BACKEND_DIR)/src/main.py | cut -d'"' -f4); \
	if [ "$$INFO" != "$$VERSION" ]; then echo "MISMATCH main.py (info): $$INFO"; ERRORS=1; else echo "OK main.py (info)"; fi; \
	if [ $$ERRORS -ne 0 ]; then exit 1; fi; \
	echo "---"; \
	echo "All versions match!"

version-sync: ## Update all version files from VERSION (run after editing VERSION)
	@if [ ! -f "$(VERSION_FILE)" ]; then \
		echo "ERROR: VERSION file not found at $(VERSION_FILE)"; \
		echo "The ops repo VERSION file is the source of truth."; \
		exit 1; \
	fi; \
	VERSION=$$(cat $(VERSION_FILE) | tr -d '[:space:]'); \
	if [ -z "$$VERSION" ]; then \
		echo "ERROR: VERSION file is empty"; \
		exit 1; \
	fi; \
	if ! echo "$$VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$$'; then \
		echo "ERROR: Invalid version format '$$VERSION' (expected X.Y.Z)"; \
		exit 1; \
	fi; \
	echo "Syncing version $$VERSION to all files..."; \
	sed -i 's/"version": "[^"]*"/"version": "'$$VERSION'"/' $(FRONTEND_DIR)/package.json; \
	sed -i 's/^version = "[^"]*"/version = "'$$VERSION'"/' $(BACKEND_DIR)/pyproject.toml; \
	sed -i 's/version="[^"]*"/version="'$$VERSION'"/' $(BACKEND_DIR)/src/main.py; \
	sed -i 's/"version": "[^"]*"/"version": "'$$VERSION'"/' $(BACKEND_DIR)/src/main.py; \
	cp CHANGELOG.md $(FRONTEND_DIR)/public/; \
	echo "Done. Run 'make version' to verify."

tag: ## Create git tag with current version (v0.X.Y)
	@VERSION=$$(cat $(VERSION_FILE) 2>/dev/null); \
	if [ -z "$$VERSION" ]; then \
		echo "ERROR: VERSION file not found at $(VERSION_FILE)"; \
		exit 1; \
	fi; \
	git tag -a "v$$VERSION" -m "Release v$$VERSION"; \
	echo "Created tag v$$VERSION"; \
	echo "Run 'git push --tags' to push to remote."

##@ CV Management

cv-pdf: ## Export CV page to PDF (requires dev server running)
	@if ! curl -s http://localhost:5173 > /dev/null 2>&1; then \
		echo "Error: Dev server not running. Start with 'make up' or 'npm run dev'"; \
		exit 1; \
	fi
	cd $(FRONTEND_DIR) && node scripts/export_cv_pdf.mjs
