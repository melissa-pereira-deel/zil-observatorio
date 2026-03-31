.PHONY: setup up down restart status logs test lint migrate seed clean help

# ── Variáveis ──
DC = docker compose

# ── Setup ──
setup: ## Setup completo do ambiente de desenvolvimento
	$(DC) build
	$(DC) up -d
	@echo "⏳ Aguardando serviços..."
	@sleep 5
	$(MAKE) migrate
	$(MAKE) seed
	@echo ""
	@echo "✅ ZIL Observatório rodando!"
	@echo "   Frontend:  http://localhost:3000"
	@echo "   API docs:  http://localhost:8000/docs"
	@echo "   DB:        localhost:5432 (zil/zil)"
	@echo ""

# ── Docker ──
up: ## Subir todos os serviços
	$(DC) up -d

down: ## Parar todos os serviços
	$(DC) down

restart: ## Reiniciar todos os serviços
	$(DC) restart

status: ## Status dos serviços
	$(DC) ps

logs: ## Logs (todos os serviços)
	$(DC) logs -f

logs-api: ## Logs apenas da API
	$(DC) logs -f api

logs-worker: ## Logs apenas do worker
	$(DC) logs -f worker

logs-web: ## Logs apenas do frontend
	$(DC) logs -f web

# ── Banco de Dados ──
migrate: ## Rodar migrations
	$(DC) exec api alembic upgrade head

migrate-new: ## Criar nova migration (uso: make migrate-new MSG="descrição")
	$(DC) exec api alembic revision --autogenerate -m "$(MSG)"

seed: ## Popular banco com dados iniciais
	$(DC) exec api python -m scripts.seed

db-shell: ## Acessar shell do PostgreSQL
	$(DC) exec db psql -U zil -d zil

# ── Testes ──
test: ## Rodar todos os testes
	$(DC) exec api pytest -v
	$(DC) exec web npm test -- --watchAll=false

test-api: ## Testes do backend
	$(DC) exec api pytest -v

test-web: ## Testes do frontend
	$(DC) exec web npm test -- --watchAll=false

test-cov: ## Testes com cobertura
	$(DC) exec api pytest --cov=. --cov-report=html -v

# ── Qualidade ──
lint: ## Lint em todo o código
	$(DC) exec api ruff check .
	$(DC) exec api mypy . --strict
	$(DC) exec web npm run lint

format: ## Formatar código
	$(DC) exec api black .
	$(DC) exec api ruff check . --fix
	$(DC) exec web npm run format

# ── Crawlers ──
crawl-camara: ## Executar crawler da Câmara manualmente
	$(DC) exec worker python -m workers.crawlers.camara

crawl-senado: ## Executar crawler do Senado manualmente
	$(DC) exec worker python -m workers.crawlers.senado

recalc-scores: ## Recalcular todos os scores ZIL
	$(DC) exec worker python -m workers.scoring.recalculate

# ── Utilidades ──
shell-api: ## Shell Python no container da API
	$(DC) exec api python

shell-web: ## Shell no container do frontend
	$(DC) exec web sh

clean: ## Limpar tudo (volumes, containers, imagens)
	$(DC) down -v --remove-orphans
	docker system prune -f

# ── Help ──
help: ## Mostrar esta ajuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
