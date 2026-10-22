"""Gravação de uma execução na tabela `explicacoes`.

Idempotente na chave `(proposicao_id, pipeline_versao, texto_hash)`: rodar o
mesmo pipeline sobre o mesmo texto não gera linha nova. Mudou o YAML do
pipeline ou o inteiro teor, é outra execução, e as duas ficam — comparar é
o ponto.
"""

import hashlib
from dataclasses import asdict
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from .schema import Explicacao as ExplicacaoResultado


def hash_texto(texto: str) -> str:
    return hashlib.sha256((texto or "").encode("utf-8")).hexdigest()


def _evidencias(res: ExplicacaoResultado) -> dict:
    return {
        "pareceres": [asdict(p) for p in res.pareceres],
        "dissensos": [asdict(d) for d in (res.analise.dissensos if res.analise else [])],
        "lentes": list(res.analise.lentes) if res.analise else [],
    }


def gravar(
    db: Session,
    proposicao_id: UUID,
    resultado: ExplicacaoResultado,
    texto_hash: str,
    custo_estimado: Optional[float] = None,
    force: bool = False,
):
    """Devolve a linha gravada, ou a já existente para a mesma chave.

    Com `force=True`, a linha existente é substituída — serve para reprocessar
    depois de corrigir um bug de parse sem precisar mudar o pipeline.
    """
    from models import Explicacao  # import curto (ADR-002)

    existente = db.execute(
        select(Explicacao).where(
            Explicacao.proposicao_id == proposicao_id,
            Explicacao.pipeline_versao == resultado.pipeline_versao,
            Explicacao.texto_hash == texto_hash,
        )
    ).scalar_one_or_none()

    if existente is not None and not force:
        return existente
    if existente is not None:
        db.delete(existente)
        db.flush()

    linha = Explicacao(
        proposicao_id=proposicao_id,
        pipeline_versao=resultado.pipeline_versao,
        texto_hash=texto_hash,
        resumo_didatico=resultado.resumo_didatico.texto if resultado.resumo_didatico else None,
        resumo_detalhado=resultado.resumo_detalhado.texto if resultado.resumo_detalhado else None,
        analise_sistemica=(
            {
                "causas_raizes": resultado.analise.causas_raizes,
                "dependencias": resultado.analise.dependencias,
                "fatores_limitantes": resultado.analise.fatores_limitantes,
                "dimensoes": resultado.analise.dimensoes,
            }
            if resultado.analise
            else None
        ),
        evidencias=_evidencias(resultado),
        meta=asdict(resultado.meta),
        metricas=resultado.metricas or None,
        problemas=resultado.problemas or None,
        status=resultado.status,
        custo_estimado=custo_estimado,
    )
    db.add(linha)
    db.flush()
    return linha
