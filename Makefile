.PHONY: setup up down restart status logs test lint migrate migrate-stamp seed clean help

# ── Variáveis ──
DC = docker compose
# Usa o .venv local se existir; senão, o python3 do sistema.
# Sobrescrevível: make test-api PYTHON=/caminho/para/python
PYTHON ?= $(shell [ -x .venv/bin/python ] && echo .venv/bin/python || echo python3)

# ── Setup ──
# As migrations rodam ANTES da API subir: em desenvolvimento o lifespan do
# main.py chama Base.metadata.create_all, e se as tabelas já existirem sem o
# carimbo do Alembic o `upgrade head` falha. Migrando primeiro, o create_all
# vira no-op e o Alembic segue como fonte da verdade do schema.
setup: ## Setup completo do ambiente de desenvolvimento
	$(DC) build
	$(DC) up -d db redis
	@echo "⏳ Aguardando o banco..."
	@until $(DC) exec -T db pg_isready -U $${POSTGRES_USER:-zil} >/dev/null 2>&1; do sleep 1; done
	$(MAKE) migrate
	$(DC) up -d
	$(MAKE) seed
	@echo ""
	@echo "✅ ZIL Observatório rodando!"
	@echo "   Frontend:  http://localhost:3000"
	@echo "   API docs:  http://localhost:8000/docs"
	@echo "   DB:        localhost:$${POSTGRES_PORT:-5432} (zil/zil)"
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
migrate: ## Rodar migrations (Alembic)
	$(DC) run --rm api alembic upgrade head

migrate-new: ## Criar nova migration (uso: make migrate-new MSG="descrição")
	$(DC) run --rm api alembic revision --autogenerate -m "$(MSG)"

migrate-stamp: ## Marcar banco existente como já migrado (criado por create_all, sem carimbo)
	$(DC) run --rm api alembic stamp head

# O seed roda no HOST, como os testes: os scripts assumem a raiz do repositório
# no sys.path (`apps.workers.*`, `packages.*`), e o container achata apps/api em
# /app. Requer que DATABASE_URL no .env aponte para a porta publicada do db.
seed: ## Popular banco com as votações já curadas em data/direcoes/
	$(PYTHON) scripts/seed.py

db-shell: ## Acessar shell do PostgreSQL
	$(DC) exec db psql -U zil -d zil

# ── Testes ──
# Os testes do backend rodam no HOST, não no container: eles importam tanto
# `models`/`main` (imports curtos de apps/api) quanto `apps.*`, `packages.*` e
# `scripts.*` (da raiz do repo). O container da API monta só apps/api em /app —
# montar o repo inteiro quebraria o contrato de WORKDIR que faz os imports
# curtos funcionarem (ADR-002). É também como a CI roda.
# Use PYTHON=.venv/bin/python se suas dependências estiverem num virtualenv.
test: ## Rodar todas as verificações (backend: testes; frontend: lint + tipos)
	$(MAKE) test-api
	$(MAKE) test-web

test-api: ## Testes do backend (rodam no host — ver nota no Makefile)
	$(PYTHON) -m pytest tests/ -v

test-web: ## Frontend: lint + type check (apps/web não tem suíte de testes)
	$(DC) exec web npm run lint
	$(DC) exec web npx tsc --noEmit

test-cov: ## Testes do backend com cobertura (requer pytest-cov)
	$(PYTHON) -m pytest tests/ --cov=apps --cov=packages --cov-report=html -v

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
