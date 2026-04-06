"""Endpoints for proposições and votações."""

import os
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query, HTTPException
from sqlalchemy import select, func, cast, Text
from sqlalchemy.orm import Session

from core.config import get_db, settings
from models import Proposicao, Votacao, Voto, Parlamentar, IngestionRun, ProposicaoAutor, ProposicaoRelacao
from schemas import (
    ProposicaoRead, VotacaoRead, VotoRead, ProposicaoContexto,
    LeiReferenciadaRead, ProposicaoSnippet, ParlamentarSnippet,
    CadeiaRead, AutorRead, TemaRead, RelacionadaRead,
)
from lib.situacao import get_situacao_grupo, get_cods_for_grupo, VALID_GRUPOS, SITUACAO_GRUPOS
from lib.urn import parse_urn_to_url

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
            resumo_simples=proposicao.resumo_simples,
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
        aprovacao=v.aprovacao,
        sigla_orgao=v.sigla_orgao,
        proposicao_objeto=v.proposicao_objeto,
    )


router = APIRouter(tags=["Proposições e Votações"])


def _parlamentar_snippet(parl: Optional[Parlamentar]) -> Optional[ParlamentarSnippet]:
    """Convert a Parlamentar model to a snippet for embedding."""
    if not parl:
        return None
    return ParlamentarSnippet(
        id=parl.id,
        nome=parl.nome,
        partido=parl.partido,
        uf=parl.uf,
        foto_url=parl.foto_url,
    )


def _proposicao_to_read(p: Proposicao, db: Session) -> ProposicaoRead:
    """Build enriched ProposicaoRead with computed fields."""
    # Computed fields
    situacao_grupo = get_situacao_grupo(p.cod_situacao) if p.cod_situacao else None
    url_lei = parse_urn_to_url(p.urn_final) if p.urn_final else None

    # Autor principal snippet
    autor_principal = None
    if p.autor_principal_id:
        parl = db.get(Parlamentar, p.autor_principal_id)
        autor_principal = _parlamentar_snippet(parl)

    # Relator snippet
    relator_snippet = None
    if p.relator_id:
        relator_parl = db.get(Parlamentar, p.relator_id)
        relator_snippet = _parlamentar_snippet(relator_parl)

    # Cadeia
    cadeia = None
    if p.prop_principal_id or p.prop_anterior_id or p.prop_posterior_id:
        cadeia = CadeiaRead(
            principal_fonte_id=p.prop_principal_id,
            anterior_fonte_id=p.prop_anterior_id,
            posterior_fonte_id=p.prop_posterior_id,
        )

    return ProposicaoRead(
        id=p.id,
        fonte_id=p.fonte_id,
        fonte=p.fonte.value,
        tipo=p.tipo,
        numero=p.numero,
        ano=p.ano,
        ementa=p.ementa,
        situacao=p.situacao,
        data_apresentacao=p.data_apresentacao,
        categorias_zil=p.categorias_zil,
        relevancia_zil=float(p.relevancia_zil) if p.relevancia_zil is not None else None,
        url_inteiro_teor=p.url_inteiro_teor,
        contexto_status=p.contexto_status,
        resumo_simples=p.resumo_simples,
        confianca=float(p.confianca) if p.confianca is not None else None,
        # Feature 012 fields
        cod_situacao=p.cod_situacao,
        regime=p.regime,
        apreciacao=p.apreciacao,
        keywords_camara=p.keywords_camara,
        urn_final=p.urn_final,
        url_lei=url_lei,
        situacao_grupo=situacao_grupo,
        temas_camara=p.temas_camara,
        autor_principal=autor_principal,
        orgao_situacao=p.orgao_situacao,
        relator=relator_snippet,
        cadeia=cadeia,
    )


# ── Proposições ──

@router.get("/proposicoes", response_model=list[ProposicaoRead])
def listar_proposicoes(
    categoria: Optional[str] = Query(None, description="Categoria ZIL (ex: ZIL-FER)"),
    tipo: Optional[str] = Query(None, description="Tipo (PL, PEC, PLP...)"),
    ano: Optional[int] = Query(None),
    regime: Optional[str] = Query(None, description="Regime legislativo (URGENCIA, ESPECIAL, ORDINARIO)"),
    situacao_grupo: Optional[str] = Query(None, description="Grupo de situacao (tramitando, aprovada, arquivada, outras)"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Lista proposições classificadas por pauta ZIL."""
    query = select(Proposicao).where(Proposicao.categorias_zil.isnot(None))

    if categoria:
        query = query.where(cast(Proposicao.categorias_zil, Text).like(f'%"{categoria}"%'))
    if tipo:
        query = query.where(Proposicao.tipo == tipo.upper())
    if ano:
        query = query.where(Proposicao.ano == ano)
    if regime:
        query = query.where(Proposicao.regime == regime.upper())
    if situacao_grupo:
        if situacao_grupo not in VALID_GRUPOS:
            raise HTTPException(
                status_code=422,
                detail=f"situacao_grupo invalido: '{situacao_grupo}'. Use: {', '.join(sorted(VALID_GRUPOS))}",
            )
        if situacao_grupo == "outras":
            # NOT IN all known codes
            all_known = set()
            for cods in SITUACAO_GRUPOS.values():
                all_known |= cods
            if all_known:
                query = query.where(
                    Proposicao.cod_situacao.notin_(all_known) | Proposicao.cod_situacao.is_(None)
                )
        else:
            cods = get_cods_for_grupo(situacao_grupo)
            if cods:
                query = query.where(Proposicao.cod_situacao.in_(cods))

    query = query.order_by(Proposicao.data_apresentacao.desc().nulls_last())
    query = query.offset((page - 1) * per_page).limit(per_page)

    props = db.execute(query).scalars().all()
    return [_proposicao_to_read(p, db) for p in props]


@router.get("/proposicoes/{proposicao_id}", response_model=ProposicaoRead)
def obter_proposicao(proposicao_id: UUID, db: Session = Depends(get_db)):
    p = db.get(Proposicao, proposicao_id)
    if not p:
        raise HTTPException(status_code=404, detail="Proposição não encontrada")
    return _proposicao_to_read(p, db)


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

    return ProposicaoContexto(
        proposicao_id=p.id,
        ementa_original=p.ementa,
        contexto_status=p.contexto_status,
        resumo_simples=p.resumo_simples,
        glossario=p.glossario,
        impacto_zil=p.impacto_zil,
        leis_referenciadas=leis_ref,
        confianca=float(p.confianca) if p.confianca is not None else None,
        enriquecido_em=p.enriquecido_em,
        versao_pipeline="1.0",
        modelo_llm=settings.ENRICHMENT_MODEL,
        fontes=fontes,
    )


@router.post("/proposicoes/{proposicao_id}/enriquecer")
def forcar_enriquecimento(
    proposicao_id: UUID,
    background_tasks: BackgroundTasks,
    admin_token: str = Query(..., description="Token de administração"),
    db: Session = Depends(get_db),
):
    """Força re-enriquecimento de uma proposição (admin only, Feature 002)."""
    expected = settings.ADMIN_TOKEN
    if not expected or admin_token != expected:
        raise HTTPException(status_code=403, detail="Token inválido")

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


# ── Proposição sub-resources (Feature 012) ──

@router.get("/proposicoes/{proposicao_id}/autores", response_model=list[AutorRead])
def autores_da_proposicao(proposicao_id: UUID, db: Session = Depends(get_db)):
    """Lista autores de uma proposição com vinculação a parlamentar."""
    p = db.get(Proposicao, proposicao_id)
    if not p:
        raise HTTPException(status_code=404, detail="Proposição não encontrada")

    autores = db.execute(
        select(ProposicaoAutor)
        .where(ProposicaoAutor.proposicao_id == proposicao_id)
        .order_by(ProposicaoAutor.ordem)
    ).scalars().all()

    result = []
    for a in autores:
        parl_snippet = None
        if a.parlamentar_id:
            parl = db.get(Parlamentar, a.parlamentar_id)
            parl_snippet = _parlamentar_snippet(parl)
        result.append(AutorRead(
            id=a.id,
            nome=a.nome,
            tipo=a.tipo,
            ordem=a.ordem,
            proponente=a.proponente,
            parlamentar=parl_snippet,
        ))
    return result


@router.get("/proposicoes/{proposicao_id}/temas", response_model=list[TemaRead])
def temas_da_proposicao(proposicao_id: UUID, db: Session = Depends(get_db)):
    """Lista temas oficiais da Câmara para uma proposição."""
    p = db.get(Proposicao, proposicao_id)
    if not p:
        raise HTTPException(status_code=404, detail="Proposição não encontrada")

    if not p.temas_camara:
        return []
    return [TemaRead(cod=t.get("cod", 0), tema=t.get("tema", "")) for t in p.temas_camara]


@router.get("/proposicoes/{proposicao_id}/relacionadas", response_model=list[RelacionadaRead])
def relacionadas_da_proposicao(
    proposicao_id: UUID,
    tipo_relacao: Optional[str] = Query(None, description="Filtrar por tipo de relação"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Lista proposições relacionadas (emendas, pareceres, substitutivos, etc.)."""
    p = db.get(Proposicao, proposicao_id)
    if not p:
        raise HTTPException(status_code=404, detail="Proposição não encontrada")

    query = select(ProposicaoRelacao).where(ProposicaoRelacao.proposicao_id == proposicao_id)

    if tipo_relacao:
        from lib.relacoes import VALID_TIPOS_RELACAO
        if tipo_relacao not in VALID_TIPOS_RELACAO:
            raise HTTPException(
                status_code=422,
                detail=f"tipo_relacao invalido: '{tipo_relacao}'. Use: {', '.join(sorted(VALID_TIPOS_RELACAO))}",
            )
        query = query.where(ProposicaoRelacao.tipo_relacao == tipo_relacao)

    query = query.order_by(ProposicaoRelacao.tipo_relacao, ProposicaoRelacao.ano.desc().nulls_last())
    query = query.offset((page - 1) * per_page).limit(per_page)

    rels = db.execute(query).scalars().all()
    return [
        RelacionadaRead(
            id=r.id,
            tipo_relacao=r.tipo_relacao,
            sigla_tipo=r.sigla_tipo,
            numero=r.numero,
            ano=r.ano,
            ementa=r.ementa,
            relacionada_fonte_id=r.relacionada_fonte_id,
            proposicao_id_zil=r.relacionada_id,
        )
        for r in rels
    ]


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
