# Quickstart: Ingestão da API da Câmara dos Deputados

**Feature**: `001-camara-api-ingestao`
**Date**: 2026-04-01

---

## Pré-requisitos

- Docker + Docker Compose instalados
- Python 3.12+ com `uv` ou `pip` (para rodar fora do Docker)
- `git clone` do repositório na branch `001-camara-api-ingestao`

---

## 1. Subir a infraestrutura

```bash
# Na raiz do repositório
docker compose up -d postgres redis

# Verificar que os serviços estão rodando
docker compose ps
```

Aguardar ~5s para o PostgreSQL aceitar conexões.

---

## 2. Criar o banco de dados

```bash
# Entrar no container do postgres e criar o banco
docker compose exec postgres psql -U postgres -c "CREATE DATABASE zil;"
docker compose exec postgres psql -U postgres -c "CREATE USER zil WITH PASSWORD 'zil';"
docker compose exec postgres psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE zil TO zil;"
```

O schema é criado automaticamente pelo lifespan da API (modo development).

---

## 3. Instalar dependências Python

```bash
cd apps/api
pip install -r requirements.txt

cd ../../apps/workers
pip install -r requirements.txt
```

---

## 4. Configurar variáveis de ambiente

```bash
# apps/api/.env (copiar de .env.example se existir)
DATABASE_URL=postgresql://zil:zil@localhost:5432/zil
REDIS_URL=redis://localhost:6379/0
ENV=development
```

---

## 5. Subir a API (cria o schema automaticamente)

```bash
cd apps/api
uvicorn main:app --reload --port 8000
```

Confirmar que o schema foi criado:
```bash
docker compose exec postgres psql -U zil -d zil -c "\dt"
# Deve listar: parlamentares, proposicoes, votacoes, votos, scores_votacao, ingestion_runs
```

---

## 6. Executar a ingestão manualmente

### Opção A — Script direto (sem Celery)

```bash
cd /  # raiz do repositório
python apps/workers/crawlers/camara.py 2024
# Argumento opcional: ano. Default: ano atual.
# Para ingestão multi-ano (conforme spec):
python apps/workers/crawlers/camara.py 2024
python apps/workers/crawlers/camara.py 2025
python apps/workers/crawlers/camara.py 2026
```

Saída esperada:
```
2024-03-15 14:00:00 INFO ============================================================
2024-03-15 14:00:00 INFO ZIL Crawler — Câmara dos Deputados — 2024
2024-03-15 14:00:00 INFO ============================================================
2024-03-15 14:00:01 INFO 🏛️  Sincronizando deputados da Câmara...
2024-03-15 14:00:10 INFO ✅ 513 novos deputados adicionados (total: 513)
2024-03-15 14:00:10 INFO 🗳️  Sincronizando votações da Câmara (2024)...
2024-03-15 14:01:30 INFO   Processadas 10 votações...
...
2024-03-15 14:30:00 INFO ✅ 847 novas votações processadas
```

### Opção B — Via Celery worker

```bash
# Terminal 1: worker
cd apps/workers
celery -A tasks worker --loglevel=info

# Terminal 2: disparar task manualmente
cd apps/workers
python -c "from tasks import sync_votacoes_task; sync_votacoes_task.delay(2024)"
```

---

## 7. Recalcular scores

```bash
python apps/workers/scoring/__init__.py
# Ou via Python:
python -c "
from apps.api.core.config import SessionLocal
from apps.workers.scoring import recalcular_todos_scores
with SessionLocal() as db:
    recalcular_todos_scores(db)
"
```

---

## 8. Verificar os dados via API

Com a API rodando em `localhost:8000`:

```bash
# Total de deputados indexados
curl -s localhost:8000/stats | python -m json.tool

# Ranking de deputados de SP
curl -s "localhost:8000/parlamentares?uf=SP&ordem=score_desc" | python -m json.tool

# Votos ZIL de um deputado específico (usar UUID do /parlamentares)
curl -s "localhost:8000/parlamentares/{id}/votos-zil" | python -m json.tool

# Proposições de minerais estratégicos
curl -s "localhost:8000/proposicoes?categoria=ZIL-MIN" | python -m json.tool
```

Swagger UI disponível em: `http://localhost:8000/docs`

---

## 9. Rodar os testes

```bash
# Da raiz do repositório
cd apps/api && python -m pytest ../../tests/ -v

# Apenas testes obrigatórios (CI gate)
python -m pytest tests/unit/test_scoring.py tests/integration/test_api_parlamentares.py -v

# Com mypy
mypy apps/api/ apps/workers/ --strict

# Com ruff
ruff check apps/api/ apps/workers/
```

---

## 10. Agendamento automático (Celery beat)

```bash
# Worker + beat juntos (desenvolvimento)
docker compose up worker beat

# Ou separado:
celery -A apps.workers.tasks beat --loglevel=info
celery -A apps.workers.tasks worker --loglevel=info
```

Schedule configurado:
- **Votações**: a cada 6 horas (0:00, 6:00, 12:00, 18:00)
- **Deputados**: toda segunda-feira às 03:00

---

## Tempo esperado de ingestão inicial

| Etapa | Tempo estimado |
|-------|---------------|
| Sync deputados (513) | ~2 min |
| Sync votações 2024 (~1.000 votações) | ~45 min |
| Sync votações 2025 (~1.000 votações) | ~45 min |
| Sync votações 2026 (parcial) | ~15 min |
| Recálculo de scores | ~2 min |
| **Total** | **~1h 45min** |

O tempo varia com a disponibilidade da API da Câmara. Em caso de erro, a ingestão
retenta automaticamente e retoma de onde parou na próxima execução (idempotência
via `fonte_id`).

---

## Troubleshooting

**API da Câmara retorna 503**: Normal — aguardar alguns minutos e tentar novamente.
O Celery task faz retry automático (30s → 2min → 10min).

**`ImportError: No module named 'apps'`**: Executar sempre da raiz do repositório ou
ajustar `PYTHONPATH=.`.

**Score ZIL nulo para todos os deputados**: Esperado na v0 — `direcao_esperada` nas
votações ainda não foi definido pelo comitê editorial. Scores serão calculados
conforme votações recebam `direcao_esperada` via YAML em `data/taxonomia/`.

**Banco não criado**: Verificar que a API subiu pelo menos uma vez (o lifespan
chama `create_all` em modo development).
