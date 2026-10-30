"""Endpoints for proposições and votações."""

import secrets
from typing import Literal, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Header, Query, HTTPException
from sqlalchemy import case, select, func, cast, Text
from sqlalchemy.orm import Session

from core.config import get_db, settings
from models import Proposicao, Votacao, Voto, Parlamentar, IngestionRun
from schemas import ProposicaoRead, VotacaoRead, VotoRead, ProposicaoContexto, LeiReferenciadaRead, ProposicaoSnippet

import re

_PLACAR_RE = re.compile(
    r"[.,]?\s*sim\s*:\s*\d+\s*;.*$",
    re.IGNORECASE,
)

def _strip_placar(descricao: Optional[str]) -> Optional[str]:
    """Remove inline vote tally from Câmara session description.

    E.g. 'Aprovada a subemenda. Sim: 429; não: 19; abstenção: 3; total: 451.'
    becomes 'Aprovada a subemenda.'
    """
    if not descricao:
        return descricao
    return _PLACAR_RE.sub("", descricao).strip().rstrip(".")


def _votacao_to_read(v: Votacao, proposicao: Optional[Proposicao] = None) -> VotacaoRead:
    snippet = None
    if proposicao:
        snippet = ProposicaoSnippet(
            id=proposicao.id,
            tipo=proposicao.tipo,
            numero=proposicao.numero,
            ano=proposicao.ano,
            ementa=proposicao.ementa,
            resumo_simples=proposicao.resumo_publicavel,
        )
    return VotacaoRead(
        id=v.id,
        fonte_id=v.fonte_id,
        fonte=v.fonte.value,
        data=v.data,
        descricao=_strip_placar(v.descricao),
        resultado=v.resultado,
        votos_sim=v.votos_sim,
        votos_nao=v.votos_nao,
        categorias_zil=v.categorias_zil,
        direcao_esperada=v.direcao_esperada,
        peso=v.peso,
        proposicao=snippet,
    )


router = APIRouter(tags=["Proposições e Votações"])


# ── Proposições ──

@router.get("/proposicoes", response_model=list[ProposicaoRead])
def listar_proposicoes(
    categoria: Optional[str] = Query(None, description="Categoria ZIL (ex: ZIL-FER)"),
    tipo: Optional[str] = Query(None, description="Tipo (PL, PEC, PLP...)"),
    ano: Optional[int] = Query(None),
    analise: Optional[Literal["analisada", "pendente"]] = Query(
        None, description="analisada = enriquecimento pronto; pendente = o resto"
    ),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Lista proposições classificadas por pauta ZIL, com as analisadas primeiro."""
    query = select(Proposicao).where(Proposicao.categorias_zil.isnot(None))

    if categoria:
        query = query.where(cast(Proposicao.categorias_zil, Text).like(f'%"{categoria}"%'))
    if tipo:
        query = query.where(Proposicao.tipo == tipo.upper())
    if ano:
        query = query.where(Proposicao.ano == ano)
    pronta = Proposicao.contexto_status == "pronto"
    if analise == "analisada":
        query = query.where(pronta)
    elif analise == "pendente":
        query = query.where((Proposicao.contexto_status.is_(None)) | (Proposicao.contexto_status != "pronto"))

    # Analisadas primeiro: a lista não abre com uma parede de "sem análise".
    query = query.order_by(case((pronta, 0), else_=1), Proposicao.data_apresentacao.desc().nulls_last())
    query = query.offset((page - 1) * per_page).limit(per_page)

    return db.execute(query).scalars().all()


@router.get("/proposicoes/{proposicao_id}", response_model=ProposicaoRead)
def obter_proposicao(proposicao_id: UUID, db: Session = Depends(get_db)):
    p = db.get(Proposicao, proposicao_id)
    if not p:
        raise HTTPException(status_code=404, detail="Proposição não encontrada")
    return p


@router.get("/proposicoes/{proposicao_id}/contexto", response_model=ProposicaoContexto)
def contexto_proposicao(proposicao_id: UUID, db: Session = Depends(get_db)):
    """Retorna o contexto enriquecido de uma proposição (Feature 002)."""
    p = db.get(Proposicao, proposicao_id)
    if not p:
        raise HTTPException(status_code=404, detail="Proposição não encontrada")

    leis_ref: Optional[list[LeiReferenciadaRead]] = None
    fontes: list[str] = []
    if p.leis_referenciadas:
        leis_ref = [LeiReferenciadaRead(**r) for r in p.leis_referenciadas]
        fontes = [r.get("url_planalto") for r in p.leis_referenciadas if r.get("url_planalto")]

    # Glossário e impacto de uma recusa também são recusa ("não é possível
    # avaliar o impacto…"): saem junto com o resumo.
    pronta = p.contexto_status == "pronto"
    return ProposicaoContexto(
        proposicao_id=p.id,
        ementa_original=p.ementa,
        contexto_status=p.contexto_status,
        resumo_simples=p.resumo_publicavel,
        glossario=p.glossario if pronta else None,
        impacto_zil=p.impacto_zil if pronta else None,
        leis_referenciadas=leis_ref,
        confianca=float(p.confianca) if p.confianca is not None else None,
        enriquecido_em=p.enriquecido_em,
        versao_pipeline="1.0",
        modelo_llm=settings.ENRICHMENT_MODEL,
        fontes=fontes,
    )


def _exigir_admin(authorization: Optional[str]) -> None:
    """Valida `Authorization: Bearer <ADMIN_TOKEN>` em tempo constante.

    compare_digest evita que o tempo de resposta revele quantos caracteres do
    token o atacante já acertou.
    """
    expected = settings.ADMIN_TOKEN
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="ADMIN_TOKEN não configurado no servidor",
        )

    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not secrets.compare_digest(token.strip(), expected):
        raise HTTPException(
            status_code=401,
            detail="Token de administração inválido ou ausente",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/proposicoes/{proposicao_id}/enriquecer")
def forcar_enriquecimento(
    proposicao_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None, description="Bearer <ADMIN_TOKEN>"),
):
    """Força re-enriquecimento de uma proposição (admin only, Feature 002).

    Autentica por header `Authorization: Bearer <token>`. Nunca por query
    string: URLs vazam em log de servidor, histórico de browser e header
    Referer, então um token ali é um token comprometido.
    """
    _exigir_admin(authorization)

    p = db.get(Proposicao, proposicao_id)
    if not p:
        raise HTTPException(status_code=404, detail="Proposição não encontrada")

    # Try Celery; fallback to FastAPI BackgroundTask with its own session
    try:
        from workers.tasks import task_enriquecer_proposicao as _task
        _task.delay(str(proposicao_id), force=True)
        return {"status": "enqueued", "proposicao_id": str(proposicao_id)}
    except Exception:
        def _run_inline(pid: str) -> None:
            from core.config import SessionLocal
            from workers.enrichment import enriquecer_proposicao
            _db = SessionLocal()
            try:
                enriquecer_proposicao(UUID(pid), _db, force=True)
            finally:
                _db.close()

        background_tasks.add_task(_run_inline, str(proposicao_id))
        return {"status": "processing", "proposicao_id": str(proposicao_id)}


@router.get("/proposicoes/{proposicao_id}/votacoes", response_model=list[VotacaoRead])
def votacoes_da_proposicao(proposicao_id: UUID, db: Session = Depends(get_db)):
    """Lista votações vinculadas a uma proposição."""
    p = db.get(Proposicao, proposicao_id)
    if not p:
        raise HTTPException(status_code=404, detail="Proposição não encontrada")
    query = (
        select(Votacao)
        .where(Votacao.proposicao_id == proposicao_id)
        .order_by(Votacao.data.desc().nulls_last())
    )
    votacoes = db.execute(query).scalars().all()
    return [_votacao_to_read(v, p) for v in votacoes]


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
    query = (
        select(Votacao, Proposicao)
        .outerjoin(Proposicao, Votacao.proposicao_id == Proposicao.id)
        .where(Votacao.categorias_zil.isnot(None))
    )

    if categoria:
        query = query.where(cast(Votacao.categorias_zil, Text).like(f'%"{categoria}"%'))
    if ano:
        query = query.where(func.extract("year", Votacao.data) == ano)

    query = query.order_by(Votacao.data.desc().nulls_last())
    query = query.offset((page - 1) * per_page).limit(per_page)

    rows = db.execute(query).all()
    return [_votacao_to_read(v, p) for v, p in rows]


@router.get("/votacoes/{votacao_id}", response_model=VotacaoRead)
def obter_votacao(votacao_id: UUID, db: Session = Depends(get_db)):
    row = db.execute(
        select(Votacao, Proposicao)
        .outerjoin(Proposicao, Votacao.proposicao_id == Proposicao.id)
        .where(Votacao.id == votacao_id)
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Votação não encontrada")
    v, p = row
    return _votacao_to_read(v, p)


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
    """Estatísticas gerais da plataforma (US-3 AC-1)."""
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

    # ultima_atualizacao: finalizado_em do IngestionRun mais recente com status success (FR-009)
    ultima_atualizacao = db.execute(
        select(func.max(IngestionRun.finalizado_em)).where(IngestionRun.status == "success")
    ).scalar()

    return {
        "total_parlamentares": total_parl,
        "total_deputados": total_dep,
        "total_senadores": total_sen,
        "total_proposicoes_zil": total_prop,
        "total_votacoes_zil": total_vot,
        "score_medio": round(float(score_medio), 2) if score_medio else None,
        "ultima_atualizacao": ultima_atualizacao,
    }
