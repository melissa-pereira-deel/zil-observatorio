#!/bin/sh
# Entrypoint de produção: migra o schema e só então sobe a API.
#
# As migrations rodam aqui, e não num pre-deploy hook, porque o plano free do
# Render não oferece esse hook. Com uma única instância isso é seguro; se um dia
# houver mais de uma, mover para um job de pre-deploy (duas instâncias subindo
# ao mesmo tempo tentariam migrar em paralelo).
set -e

echo "→ Aplicando migrations (alembic upgrade head)..."
alembic upgrade head

echo "→ Subindo a API na porta ${PORT:-8000}..."
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
