"""Endpoints for parlamentares (deputados + senadores)."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core.config import get_db
from models import Parlamentar, Voto, Votacao, Proposicao, ProposicaoAutor, FonteEnum
from schemas import ParlamentarRead, ParlamentarRanking, VotoHistorico, ProposicaoRead

router = APIRouter(prefix="/parlamentares", tags=["Parlamentares"])


@router.get("", response_model=list[ParlamentarRanking])
def listar_parlamentares(
    fonte: Optional[str] = Query(None, description="camara ou senado"),
    partido: Optional[str] = Query(None),
    uf: Optional[str] = Query(None),
    ordem: str = Query("score_desc", regex="^(score_desc|score_asc|nome)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=600),
    db: Session = Depends(get_db),
):
    """Lista parlamentares com score ZIL, com filtros e paginação."""
    query = select(Parlamentar)

    if fonte:
        query = query.where(Parlamentar.fonte == FonteEnum(fonte))
    if partido:
        query = query.where(Parlamentar.partido == partido.upper())
    if uf:
        query = query.where(Parlamentar.uf == uf.upper())

    if ordem == "score_desc":
        query = query.order_by(Parlamentar.score_zil.desc().nulls_last())
    elif ordem == "score_asc":
        query = query.order_by(Parlamentar.score_zil.asc().nulls_last())
    else:
        query = query.order_by(Parlamentar.nome)

    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    parlamentares = db.execute(query).scalars().all()

    results = []
    for p in parlamentares:
        total_votos = db.execute(
            select(func.count(Voto.id))
            .join(Votacao, Voto.votacao_id == Votacao.id)
            .where(Voto.parlamentar_id == p.id)
            .where(Votacao.categorias_zil.isnot(None))
        ).scalar() or 0

        results.append(ParlamentarRanking(
            id=p.id,
            nome=p.nome,
            partido=p.partido,
            uf=p.uf,
            foto_url=p.foto_url,
            fonte=p.fonte.value,
            score_zil=float(p.score_zil) if p.score_zil else None,
            total_votos_zil=total_votos,
        ))

    return results


@router.get("/{parlamentar_id}", response_model=ParlamentarRead)
def obter_parlamentar(
    parlamentar_id: UUID,
    db: Session = Depends(get_db),
):
    """Perfil completo de um parlamentar."""
    p = db.get(Parlamentar, parlamentar_id)
    if not p:
        raise HTTPException(status_code=404, detail="Parlamentar não encontrado")
    return p


@router.get("/{parlamentar_id}/votos-zil", response_model=list[VotoHistorico])
def votos_zil_parlamentar(
    parlamentar_id: UUID,
    categoria: Optional[str] = Query(None, description="Categoria ZIL (ex: ZIL-FER)"),
    db: Session = Depends(get_db),
):
    """Histórico de votos do parlamentar em pautas ZIL."""
    p = db.get(Parlamentar, parlamentar_id)
    if not p:
        raise HTTPException(status_code=404, detail="Parlamentar não encontrado")

    query = (
        select(Voto, Votacao, Proposicao)
        .join(Votacao, Voto.votacao_id == Votacao.id)
        .outerjoin(Proposicao, Votacao.proposicao_id == Proposicao.id)
        .where(Voto.parlamentar_id == parlamentar_id)
        .where(Votacao.categorias_zil.isnot(None))
        .order_by(Votacao.data.desc())
    )

    rows = db.execute(query).all()

    results = []
    for voto, votacao, proposicao in rows:
        if categoria and (not votacao.categorias_zil or categoria not in votacao.categorias_zil):
            continue

        alinhado = None
        if votacao.direcao_esperada:
            alinhado = voto.voto.value == votacao.direcao_esperada

        prop_label = None
        if proposicao and proposicao.tipo and proposicao.numero and proposicao.ano:
            prop_label = f"{proposicao.tipo} {proposicao.numero}/{proposicao.ano}"

        results.append(VotoHistorico(
            votacao_id=votacao.id,
            data=votacao.data,
            descricao=votacao.descricao,
            categorias_zil=votacao.categorias_zil,
            voto=voto.voto.value,
            direcao_esperada=votacao.direcao_esperada,
            alinhado=alinhado,
            proposicao_label=prop_label,
            proposicao_id=proposicao.id if proposicao else None,
        ))

    return results


@router.get("/{parlamentar_id}/proposicoes", response_model=list[ProposicaoRead])
def proposicoes_de_autoria(
    parlamentar_id: UUID,
    tipo: Optional[str] = Query(None, description="Tipo (PL, PEC, PLP...)"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Lista proposições de autoria de um parlamentar."""
    p = db.get(Parlamentar, parlamentar_id)
    if not p:
        raise HTTPException(status_code=404, detail="Parlamentar não encontrado")

    query = (
        select(Proposicao)
        .join(ProposicaoAutor, ProposicaoAutor.proposicao_id == Proposicao.id)
        .where(ProposicaoAutor.parlamentar_id == parlamentar_id)
    )

    if tipo:
        query = query.where(Proposicao.tipo == tipo.upper())

    query = query.order_by(Proposicao.data_apresentacao.desc().nulls_last())
    query = query.offset((page - 1) * per_page).limit(per_page)

    props = db.execute(query).scalars().all()

    # Build enriched response using the legislativo helper
    from routers.legislativo import _proposicao_to_read
    return [_proposicao_to_read(prop, db) for prop in props]


@router.get("/partidos/ranking")
def ranking_partidos(
    fonte: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Score médio por partido."""
    query = (
        select(
            Parlamentar.partido,
            func.avg(Parlamentar.score_zil).label("score_medio"),
            func.count(Parlamentar.id).label("membros"),
        )
        .where(Parlamentar.score_zil.isnot(None))
        .group_by(Parlamentar.partido)
        .order_by(func.avg(Parlamentar.score_zil).desc())
    )

    if fonte:
        query = query.where(Parlamentar.fonte == FonteEnum(fonte))

    rows = db.execute(query).all()
    return [
        {"partido": r.partido, "score_medio": round(float(r.score_medio), 2), "membros": r.membros}
        for r in rows
    ]
