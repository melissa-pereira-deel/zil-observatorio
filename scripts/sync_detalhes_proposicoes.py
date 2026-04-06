#!/usr/bin/env python3
"""
Backfill: Feature 012 — Sync detail fields for proposicoes.

Step 1.5 in the pipeline. For each proposicao without detalhes_sincronizados_em,
fetches detail data from the Camara API and updates the database.

Usage:
    python3 scripts/sync_detalhes_proposicoes.py [--dry-run] [--fase 1|2|3]
"""

import argparse
import logging
import re
import sys
import time
from datetime import datetime
from pathlib import Path

# ADR-002: add paths
_repo_root = str(Path(__file__).parent.parent)
_api_dir = str(Path(__file__).parent.parent / "apps" / "api")
for _p in (_repo_root, _api_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from core.config import settings
from models import Proposicao, Votacao, Parlamentar, ProposicaoAutor
from packages.camara_client import CamaraClient
from apps.api.lib.relacoes import classificar_tipo_relacao

logger = logging.getLogger(__name__)


def _extract_id_from_uri(uri: str) -> str | None:
    """Extract numeric ID from API URI, e.g. '/api/v2/deputados/204554' → '204554'."""
    if not uri:
        return None
    match = re.search(r"/(\d+)$", uri)
    return match.group(1) if match else None


def sync_fase1(db: Session, client: CamaraClient, dry_run: bool = False) -> dict:
    """Phase 1: Fetch detail fields from existing proposicao endpoint."""
    props = db.execute(
        select(Proposicao).where(Proposicao.detalhes_sincronizados_em.is_(None))
    ).scalars().all()

    total = len(props)
    updated = 0
    errors = 0

    print(f"Phase 1: {total} proposicoes to process")

    for i, prop in enumerate(props):
        try:
            detail = client.obter_proposicao(int(prop.fonte_id))
            if not detail:
                logger.warning(f"[{i+1}/{total}] No detail for {prop.fonte_id}")
                errors += 1
                continue

            status = detail.get("statusProposicao") or {}

            if not dry_run:
                prop.cod_situacao = status.get("codSituacao")
                prop.regime = status.get("regime")
                prop.apreciacao = status.get("apreciacao")
                prop.keywords_camara = detail.get("keywords")
                prop.urn_final = status.get("urnFinal") or None
                prop.orgao_situacao = status.get("siglaOrgao")

                # Cadeia links
                for attr, uri_key in [
                    ("prop_principal_id", "uriPropPrincipal"),
                    ("prop_anterior_id", "uriPropAnterior"),
                    ("prop_posterior_id", "uriPropPosterior"),
                ]:
                    uri = detail.get(uri_key) or ""
                    setattr(prop, attr, _extract_id_from_uri(uri))

                prop.detalhes_sincronizados_em = datetime.utcnow()
                db.commit()

            label = f"{prop.tipo} {prop.numero}/{prop.ano}" if prop.tipo else prop.fonte_id
            cod = status.get("codSituacao", "?")
            regime = status.get("regime", "?")
            kw_count = len((detail.get("keywords") or "").split(",")) if detail.get("keywords") else 0
            print(f"  [{i+1}/{total}] {label}: cod_situacao={cod} regime={regime} keywords={kw_count}")
            updated += 1

        except Exception as e:
            logger.warning(f"  [{i+1}/{total}] Error on {prop.fonte_id}: {e}")
            errors += 1

    # Also update linked votacoes
    votacao_updated = 0
    if not dry_run:
        votacoes = db.execute(
            select(Votacao).where(Votacao.aprovacao.is_(None))
        ).scalars().all()
        print(f"\nPhase 1 votacoes: {len(votacoes)} to process")
        for v in votacoes:
            try:
                vdetail = client.obter_votacao_detalhes(v.fonte_id)
                if vdetail:
                    v.aprovacao = 1 if vdetail.get("aprovacao") == 1 or vdetail.get("aprovacao") is True else (0 if vdetail.get("aprovacao") == 0 or vdetail.get("aprovacao") is False else None)
                    v.sigla_orgao = vdetail.get("siglaOrgao")
                    v.proposicao_objeto = vdetail.get("proposicaoObjeto")
                    votacao_updated += 1
            except Exception as e:
                logger.warning(f"  Votacao {v.fonte_id} error: {e}")
        db.commit()

    return {"total": total, "updated": updated, "errors": errors, "votacoes_updated": votacao_updated}


def sync_fase2(db: Session, client: CamaraClient, dry_run: bool = False) -> dict:
    """Phase 2: Fetch autores and temas for each proposicao."""
    props = db.execute(select(Proposicao)).scalars().all()

    total = len(props)
    autores_created = 0
    temas_updated = 0
    errors = 0

    # Build parlamentar lookup by fonte_id
    parlamentares = db.execute(select(Parlamentar)).scalars().all()
    parl_map = {p.fonte_id: p for p in parlamentares}

    print(f"Phase 2: {total} proposicoes to process ({len(parl_map)} parlamentares in DB)")

    for i, prop in enumerate(props):
        try:
            # Autores
            autores_data = client.listar_autores_proposicao(int(prop.fonte_id))
            for idx, autor in enumerate(autores_data):
                if dry_run:
                    continue
                # Check if already exists
                existing = db.execute(
                    select(ProposicaoAutor).where(
                        ProposicaoAutor.proposicao_id == prop.id,
                        ProposicaoAutor.ordem == idx + 1,
                    )
                ).scalar_one_or_none()
                if existing:
                    continue

                # Match parlamentar
                uri = autor.get("uri", "")
                dep_id = _extract_id_from_uri(uri)
                parlamentar = parl_map.get(dep_id) if dep_id else None

                pa = ProposicaoAutor(
                    proposicao_id=prop.id,
                    parlamentar_id=parlamentar.id if parlamentar else None,
                    nome=autor.get("nome", "Desconhecido"),
                    tipo=autor.get("tipo", "Outro") or "Outro",
                    ordem=idx + 1,
                    proponente=bool(autor.get("proponente", True)),
                    uri_autor=uri or None,
                )
                db.add(pa)
                autores_created += 1

                # Set autor_principal_id for first author
                if idx == 0 and parlamentar and not prop.autor_principal_id:
                    prop.autor_principal_id = parlamentar.id

            # Temas
            temas_data = client.listar_temas_proposicao(int(prop.fonte_id))
            if temas_data and not dry_run:
                prop.temas_camara = [
                    {"cod": t.get("codTema", 0), "tema": t.get("tema", "")}
                    for t in temas_data
                ]
                temas_updated += 1

            if not dry_run:
                db.commit()

            label = f"{prop.tipo} {prop.numero}/{prop.ano}" if prop.tipo else prop.fonte_id
            n_autores = len(autores_data)
            n_temas = len(temas_data) if temas_data else 0
            print(f"  [{i+1}/{total}] {label}: autores={n_autores} temas={n_temas}")

        except Exception as e:
            logger.warning(f"  [{i+1}/{total}] Error on {prop.fonte_id}: {e}")
            errors += 1
            db.rollback()

    return {"total": total, "autores_created": autores_created, "temas_updated": temas_updated, "errors": errors}


def sync_fase3(db: Session, client: CamaraClient, dry_run: bool = False) -> dict:
    """Phase 3: Fetch relacionadas for each proposicao."""
    from models import ProposicaoRelacao

    props = db.execute(select(Proposicao)).scalars().all()
    prop_map = {p.fonte_id: p for p in props}  # for matching relacionada_id

    total = len(props)
    relacoes_created = 0
    errors = 0

    print(f"Phase 3: {total} proposicoes to process")

    for i, prop in enumerate(props):
        try:
            rel_data = client.listar_relacionadas_proposicao(int(prop.fonte_id))
            for rel in rel_data:
                if dry_run:
                    continue

                rel_id_str = str(rel.get("id", ""))
                if not rel_id_str:
                    continue

                # Check if already exists
                existing = db.execute(
                    select(ProposicaoRelacao).where(
                        ProposicaoRelacao.proposicao_id == prop.id,
                        ProposicaoRelacao.relacionada_fonte_id == rel_id_str,
                    )
                ).scalar_one_or_none()
                if existing:
                    continue

                sigla = rel.get("siglaTipo", "")
                tipo_rel = classificar_tipo_relacao(sigla)
                relacionada = prop_map.get(rel_id_str)

                pr = ProposicaoRelacao(
                    proposicao_id=prop.id,
                    relacionada_id=relacionada.id if relacionada else None,
                    relacionada_fonte_id=rel_id_str,
                    tipo_relacao=tipo_rel,
                    sigla_tipo=sigla or None,
                    numero=rel.get("numero"),
                    ano=rel.get("ano"),
                    ementa=rel.get("ementa"),
                )
                db.add(pr)
                relacoes_created += 1

            if not dry_run:
                db.commit()

            label = f"{prop.tipo} {prop.numero}/{prop.ano}" if prop.tipo else prop.fonte_id
            print(f"  [{i+1}/{total}] {label}: relacionadas={len(rel_data)}")

        except Exception as e:
            logger.warning(f"  [{i+1}/{total}] Error on {prop.fonte_id}: {e}")
            errors += 1
            db.rollback()

    return {"total": total, "relacoes_created": relacoes_created, "errors": errors}


def run(fase: int = 0, dry_run: bool = False) -> dict:
    """Run sync for specified phase(s)."""
    engine = create_engine(settings.DATABASE_URL)
    results = {}

    with Session(engine) as db, CamaraClient() as client:
        if fase == 0 or fase == 1:
            results["fase1"] = sync_fase1(db, client, dry_run)
        if fase == 0 or fase == 2:
            results["fase2"] = sync_fase2(db, client, dry_run)
        if fase == 0 or fase == 3:
            results["fase3"] = sync_fase3(db, client, dry_run)

    if dry_run:
        print("\n[DRY RUN — no changes applied]")
    else:
        print(f"\nSync complete: {results}")

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    parser = argparse.ArgumentParser(description="Feature 012 detail sync")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--fase", type=int, default=0, choices=[0, 1, 2, 3])
    args = parser.parse_args()
    run(fase=args.fase, dry_run=args.dry_run)
