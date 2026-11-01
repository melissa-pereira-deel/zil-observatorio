#!/usr/bin/env python3
"""
Re-marca como `llm_recusou` as proposições `pronto` cujo resumo é uma recusa
do modelo ("Não tenho informações suficientes…").

Até 2026-10-30 o pipeline de enriquecimento gravava essas recusas como
`pronto`, e elas apareciam como resumo em /proposicoes. Hoje o pipeline já
marca a recusa ao gravar (`apps.workers.enrichment.eh_recusa`); este script
corrige o que foi gravado antes, com o mesmo detector.

Só o status muda: o texto fica para auditoria, e a API deixa de publicá-lo.
Para desfazer, basta voltar o status a `pronto`.

Usage:
    python scripts/marcar_recusas.py --dry-run   # lista o que seria re-marcado
    python scripts/marcar_recusas.py             # re-marca
"""

import argparse
import sys
from pathlib import Path

# Add repo root + apps/api to sys.path (ADR-002)
_repo_root = str(Path(__file__).parent.parent)
_api_dir = str(Path(__file__).parent.parent / "apps" / "api")
for _p in (_repo_root, _api_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from core.config import settings


def marcar_recusas(db: Session, dry_run: bool = False) -> list:
    """Devolve as proposições re-marcadas (ou que seriam, com `dry_run`)."""
    from models import Proposicao
    from apps.workers.enrichment import eh_recusa

    prontas = db.execute(select(Proposicao).where(Proposicao.contexto_status == "pronto")).scalars().all()
    recusas = [p for p in prontas if eh_recusa(p.resumo_simples)]
    if not dry_run:
        for p in recusas:
            p.contexto_status = "llm_recusou"
        db.commit()
    return recusas


def main():
    parser = argparse.ArgumentParser(description="Re-marca recusas do modelo gravadas como resumo pronto")
    parser.add_argument("--dry-run", action="store_true", help="Só lista, sem gravar")
    args = parser.parse_args()

    engine = create_engine(settings.DATABASE_URL)
    with Session(engine) as db:
        recusas = marcar_recusas(db, dry_run=args.dry_run)
        for p in recusas:
            print(f"  {p.tipo} {p.numero}/{p.ano}: {(p.resumo_simples or '')[:90]}")
        verbo = "seriam re-marcadas" if args.dry_run else "re-marcadas"
        print(f"\n{len(recusas)} proposições {verbo} como llm_recusou")


if __name__ == "__main__":
    main()
