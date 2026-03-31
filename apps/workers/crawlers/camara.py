"""Crawler da Câmara dos Deputados.

Ingere deputados, votações e votos individuais da API de Dados Abertos
da Câmara e classifica por pauta ZIL.
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import select

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent.parent))

from packages.camara_client import CamaraClient
from apps.workers.classifiers import classificar_votacao, classificar_proposicao, relevancia_score

# Models importados relativamente ao contexto de execução
from apps.api.models import (
    Parlamentar, Votacao, Voto, Proposicao,
    FonteEnum, VotoEnum,
)

logger = logging.getLogger(__name__)

VOTO_MAP = {
    "Sim": VotoEnum.SIM,
    "Não": VotoEnum.NAO,
    "Abstenção": VotoEnum.ABSTENCAO,
    "Obstrução": VotoEnum.OBSTRUCAO,
    "Art. 17": VotoEnum.ARTIGO_17,
}


def normalizar_voto(tipo_voto: str) -> VotoEnum:
    """Converte string de voto da API para enum interno."""
    return VOTO_MAP.get(tipo_voto, VotoEnum.AUSENTE)


def sync_deputados(db: Session, legislatura: Optional[int] = None) -> int:
    """Sincroniza todos os deputados da legislatura atual.

    Returns:
        Número de deputados criados ou atualizados.
    """
    logger.info("🏛️  Sincronizando deputados da Câmara...")

    with CamaraClient() as client:
        deputados = client.listar_deputados(legislatura=legislatura)

    count = 0
    for dep in deputados:
        existing = db.execute(
            select(Parlamentar).where(
                Parlamentar.fonte_id == str(dep.id),
                Parlamentar.fonte == FonteEnum.CAMARA,
            )
        ).scalar_one_or_none()

        if existing:
            existing.nome = dep.nome
            existing.partido = dep.siglaPartido
            existing.uf = dep.siglaUf
            existing.foto_url = dep.urlFoto
            existing.email = dep.email
            existing.updated_at = datetime.utcnow()
        else:
            parlamentar = Parlamentar(
                fonte_id=str(dep.id),
                fonte=FonteEnum.CAMARA,
                nome=dep.nome,
                partido=dep.siglaPartido,
                uf=dep.siglaUf,
                foto_url=dep.urlFoto,
                email=dep.email,
            )
            db.add(parlamentar)
            count += 1

    db.commit()
    logger.info(f"✅ {count} novos deputados adicionados (total: {len(deputados)})")
    return count


def sync_votacoes(db: Session, ano: int) -> int:
    """Sincroniza votações de um ano e classifica por pauta ZIL.

    Returns:
        Número de votações novas processadas.
    """
    logger.info(f"🗳️  Sincronizando votações da Câmara ({ano})...")

    with CamaraClient() as client:
        votacoes_api = client.listar_votacoes(ano=ano)

    count = 0
    for vot in votacoes_api:
        # Pular se já existe
        existing = db.execute(
            select(Votacao).where(
                Votacao.fonte_id == str(vot.id),
                Votacao.fonte == FonteEnum.CAMARA,
            )
        ).scalar_one_or_none()

        if existing:
            continue

        # Classificar
        categorias = classificar_votacao(vot.descricao)

        # Criar votação
        votacao = Votacao(
            fonte_id=str(vot.id),
            fonte=FonteEnum.CAMARA,
            data=datetime.fromisoformat(vot.data) if vot.data else None,
            descricao=vot.descricao,
            resultado="aprovado" if vot.aprovacao else "rejeitado" if vot.aprovacao is False else None,
            categorias_zil=categorias if categorias else None,
        )
        db.add(votacao)
        db.flush()  # get ID

        # Buscar votos individuais
        with CamaraClient() as client:
            votos_api = client.obter_votos(vot.id)

        sim_count = 0
        nao_count = 0

        for v in votos_api:
            # Resolver parlamentar
            parlamentar = db.execute(
                select(Parlamentar).where(
                    Parlamentar.fonte_id == str(v.deputado_id),
                    Parlamentar.fonte == FonteEnum.CAMARA,
                )
            ).scalar_one_or_none()

            if not parlamentar:
                # Deputado não cadastrado (pode ser suplente) — criar stub
                parlamentar = Parlamentar(
                    fonte_id=str(v.deputado_id),
                    fonte=FonteEnum.CAMARA,
                    nome=v.deputado_nome,
                    partido=v.deputado_partido,
                    uf=v.deputado_uf,
                )
                db.add(parlamentar)
                db.flush()

            voto_enum = normalizar_voto(v.voto)
            if voto_enum == VotoEnum.SIM:
                sim_count += 1
            elif voto_enum == VotoEnum.NAO:
                nao_count += 1

            voto = Voto(
                votacao_id=votacao.id,
                parlamentar_id=parlamentar.id,
                voto=voto_enum,
            )
            db.add(voto)

        votacao.votos_sim = sim_count
        votacao.votos_nao = nao_count

        count += 1
        if count % 10 == 0:
            db.commit()
            logger.info(f"  Processadas {count} votações...")

    db.commit()
    logger.info(f"✅ {count} novas votações processadas")
    return count


def run_full_sync(db: Session, ano: Optional[int] = None):
    """Executa sincronização completa: deputados + votações do ano."""
    ano = ano or datetime.now().year

    logger.info("=" * 60)
    logger.info(f"ZIL Crawler — Câmara dos Deputados — {ano}")
    logger.info("=" * 60)

    sync_deputados(db)
    sync_votacoes(db, ano=ano)

    logger.info("=" * 60)
    logger.info("Sync completo!")
    logger.info("=" * 60)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent.parent / "apps" / "api"))
    from core.config import SessionLocal

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    with SessionLocal() as db:
        run_full_sync(db, ano=int(sys.argv[1]) if len(sys.argv) > 1 else None)
