# ADR-002: Importações por caminho curto para evitar duplo registro de tabelas

**Data:** 2026-04-01
**Status:** Aceito

## Contexto

O Python carrega módulos pelo caminho de importação como chave no `sys.modules`. Se o mesmo arquivo físico é importado por dois caminhos diferentes (`models` e `apps.api.models`), Python cria dois módulos distintos. Ambos tentam registrar as mesmas tabelas na mesma instância `Base.metadata`, resultando em `sqlalchemy.exc.InvalidRequestError: Table 'parlamentares' is already defined`.

Isso ocorreu quando `conftest.py` importava via caminho curto (`from models import`) enquanto `apps/workers/scoring/__init__.py` importava via caminho longo (`from apps.api.models import`).

## Decisão

**Padronizar todas as importações de `apps/api/` via caminho curto** (`from models import`, `from core.config import`, etc.), adicionando `apps/api` ao `sys.path` explicitamente antes da importação:

```python
import sys
from pathlib import Path

_api_dir = str(Path(__file__).parent.parent.parent / "apps" / "api")
if _api_dir not in sys.path:
    sys.path.insert(0, _api_dir)

from models import Parlamentar, Votacao  # sempre caminho curto
```

## Regra

**Nenhum arquivo fora de `apps/api/` deve importar com `from apps.api.models import`.**
Sempre adicionar `apps/api` ao sys.path e usar `from models import`.

## Consequências

- **Positivo:** Python nunca carrega o mesmo módulo duas vezes
- **Positivo:** imports consistentes em todos os workers, testes e scripts
- **Negativo:** sys.path manipulation explícita em cada worker (aceitável)
