# Contexto de build: a RAIZ do repositório, não apps/api.
#
# A API e os workers carregam dados editoriais (data/taxonomia, data/bussula)
# resolvendo o caminho relativo ao próprio arquivo, o que dentro do container
# aponta para /data. Em desenvolvimento isso vem de um bind mount; em produção
# não há mount, então os arquivos precisam estar NA IMAGEM — e para isso o
# contexto precisa enxergar a raiz.
#
# Build: docker build -f apps/api/Dockerfile .
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY apps/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# /app é apps/api — mantém os imports curtos do projeto (ADR-002)
COPY apps/api/ /app/

# Workers e clients em /app/workers e /app/packages, onde o WORKDIR os alcança
COPY apps/workers/ /app/workers/
COPY packages/ /app/packages/

# Dados editoriais em /data — exatamente onde os loaders procuram
COPY data/ /data/

EXPOSE 8000

# Migra o schema antes de servir. $PORT vem da plataforma; 8000 é o default local.
CMD ["./entrypoint.sh"]
