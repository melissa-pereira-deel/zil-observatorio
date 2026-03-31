"""Endpoints for proposições and votações."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from core.config import get_db
from models import Proposicao, Votacao, Voto, Parlamentar
from schemas import ProposicaoRead, VotacaoRead, VotoRead

router = APIRouter(tags=["Proposições e Votações"])


# ── Proposições ──

@router.get("/proposicoes", response_model=list[ProposicaoRead])
def listar_proposicoes(
    categoria: Optional[str] = Query(None, description="Categoria ZIL (ex: ZIL-FER)"),
    tipo: Optional[str] = Query(None, description="Tipo (PL, PEC, PLP...)"),
    ano: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Lista proposições classificadas por pauta ZIL."""
    query = select(Proposicao).where(Proposicao.categorias_zil.isnot(None))

    if categoria:
        query = query.where(Proposicao.categorias_zil.any(categoria))
    if tipo:
        query = query.where(Proposicao.tipo == tipo.upper())
    if ano:
        query = query.where(Proposicao.ano == ano)

    query = query.order_by(Proposicao.data_apresentacao.desc().nulls_last())
    query = query.offset((page - 1) * per_page).limit(per_page)

    return db.execute(query).scalars().all()


@router.get("/proposicoes/{proposicao_id}", response_model=ProposicaoRead)
def obter_proposicao(proposicao_id: UUID, db: Session = Depends(get_db)):
    p = db.get(Proposicao, proposicao_id)
    if not p:
        raise HTTPException(status_code=404, detail="Proposição não encontrada")
    return p


# ── Votações ──

@router.get("/votacoes", response_model=list[VotacaoRead])
def listar_votacoes(
    categoria: Optional[str] = Query(None),
    ano: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Lista votações classificadas por pauta ZIL."""
    query = select(Votacao).where(Votacao.categorias_zil.isnot(None))

    if categoria:
        query = query.where(Votacao.categorias_zil.any(categoria))
    if ano:
        query = query.where(func.extract("year", Votacao.data) == ano)

    query = query.order_by(Votacao.data.desc().nulls_last())
    query = query.offset((page - 1) * per_page).limit(per_page)

    return db.execute(query).scalars().all()


@router.get("/votacoes/{votacao_id}/votos", response_model=list[VotoRead])
def votos_da_votacao(votacao_id: UUID, db: Session = Depends(get_db)):
    """Lista todos os votos individuais de uma votação."""
    v = db.get(Votacao, votacao_id)
    if not v:
        raise HTTPException(status_code=404, detail="Votação não encontrada")

    query = (
        select(Voto, Parlamentar)
        .join(Parlamentar, Voto.parlamentar_id == Parlamentar.id)
        .where(Voto.votacao_id == votacao_id)
        .order_by(Parlamentar.nome)
    )

    rows = db.execute(query).all()
    return [
        VotoRead(
            parlamentar_id=voto.parlamentar_id,
            parlamentar_nome=parl.nome,
            parlamentar_partido=parl.partido,
            parlamentar_uf=parl.uf,
            voto=voto.voto.value,
            orientacao_partido=voto.orientacao_partido,
        )
        for voto, parl in rows
    ]


# ── Stats ──

@router.get("/stats")
def estatisticas(db: Session = Depends(get_db)):
    """Estatísticas gerais da plataforma."""
    total_parl = db.execute(select(func.count(Parlamentar.id))).scalar() or 0
    total_dep = db.execute(
        select(func.count(Parlamentar.id)).where(Parlamentar.fonte == "camara")
    ).scalar() or 0
    total_sen = db.execute(
        select(func.count(Parlamentar.id)).where(Parlamentar.fonte == "senado")
    ).scalar() or 0
    total_prop = db.execute(
        select(func.count(Proposicao.id)).where(Proposicao.categorias_zil.isnot(None))
    ).scalar() or 0
    total_vot = db.execute(
        select(func.count(Votacao.id)).where(Votacao.categorias_zil.isnot(None))
    ).scalar() or 0
    score_medio = db.execute(
        select(func.avg(Parlamentar.score_zil)).where(Parlamentar.score_zil.isnot(None))
    ).scalar()

    return {
        "total_parlamentares": total_parl,
        "total_deputados": total_dep,
        "total_senadores": total_sen,
        "total_proposicoes_zil": total_prop,
        "total_votacoes_zil": total_vot,
        "score_medio": round(float(score_medio), 2) if score_medio else None,
    }
