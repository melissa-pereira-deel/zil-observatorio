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
from pathlib import Path

# Ensure both repo root and apps/api are in sys.path for consistent imports
_repo_root = str(Path(__file__).parent.parent.parent)
_api_dir = str(Path(__file__).parent.parent.parent / "apps" / "api")
for _p in (_repo_root, _api_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from packages.camara_client import CamaraClient
from apps.workers.classifiers import classificar_votacao, classificar_proposicao, relevancia_score

from models import (  # noqa: E402
    Parlamentar, Votacao, Voto, Proposicao, IngestionRun,
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


def _upsert_proposicao(db: Session, client: CamaraClient, prop_data: dict) -> Optional[Proposicao]:
    """Cria ou atualiza uma Proposicao a partir dos dados da API."""
    if not prop_data or not prop_data.get("id"):
        return None

    fonte_id = str(prop_data["id"])
    existing = db.execute(
        select(Proposicao).where(
            Proposicao.fonte_id == fonte_id,
            Proposicao.fonte == FonteEnum.CAMARA,
        )
    ).scalar_one_or_none()

    ementa = prop_data.get("ementa") or prop_data.get("titulo") or ""
    tipo = prop_data.get("siglaTipo") or prop_data.get("tipo")
    numero = prop_data.get("numero")
    ano = prop_data.get("ano")

    categorias = classificar_proposicao(ementa=ementa)
    relevancia = relevancia_score(ementa) if ementa else 0.0

    if existing:
        existing.ementa = ementa or existing.ementa
        existing.tipo = tipo or existing.tipo
        existing.categorias_zil = categorias if categorias else existing.categorias_zil
        existing.relevancia_zil = relevancia if relevancia > 0 else existing.relevancia_zil
        db.flush()
        return existing

    proposicao = Proposicao(
        fonte_id=fonte_id,
        fonte=FonteEnum.CAMARA,
        tipo=tipo,
        numero=numero,
        ano=ano,
        ementa=ementa,
        categorias_zil=categorias if categorias else None,
        relevancia_zil=relevancia if relevancia > 0 else None,
        classificacao_automatica=True,
    )
    db.add(proposicao)
    db.flush()
    return proposicao


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

        # Buscar detalhes da votação para obter proposição vinculada
        proposicao_id = None
        try:
            with CamaraClient() as client:
                detalhes = client.obter_votacao_detalhes(str(vot.id))
            prop_raw = detalhes.get("proposicaoPrincipal") if detalhes else None
            if prop_raw:
                proposicao = _upsert_proposicao(db, client, prop_raw)
                if proposicao:
                    proposicao_id = proposicao.id
        except Exception as e:
            logger.warning(f"Não foi possível obter proposição para votação {vot.id}: {e}")

        # Classificar: combinar descrição da votação + ementa da proposição
        texto_classificacao = vot.descricao or ""
        if proposicao_id:
            prop_obj = db.get(Proposicao, proposicao_id)
            if prop_obj and prop_obj.ementa:
                texto_classificacao = f"{texto_classificacao} {prop_obj.ementa}"

        categorias = classificar_votacao(texto_classificacao)

        # Criar votação
        votacao = Votacao(
            fonte_id=str(vot.id),
            fonte=FonteEnum.CAMARA,
            proposicao_id=proposicao_id,
            data=datetime.fromisoformat(vot.data) if vot.data else None,
            descricao=vot.descricao,
            resultado="aprovado" if vot.aprovacao else "rejeitado" if vot.aprovacao is False else None,
            categorias_zil=categorias if categorias else None,
        )
        db.add(votacao)
        db.flush()  # get ID

        # Buscar orientações dos partidos nesta votação
        partido_orientacao: dict[str, str] = {}
        try:
            with CamaraClient() as client:
                orientacoes = client.obter_votacao_orientacoes(str(vot.id))
            for ori in orientacoes:
                partido = ori.get("siglaPartido") or ori.get("partido") or ""
                orientacao = ori.get("orientacao") or ori.get("voto") or ""
                if partido and orientacao:
                    partido_orientacao[partido.upper()] = orientacao
        except Exception as e:
            logger.debug(f"Orientações não disponíveis para votação {vot.id}: {e}")

        # Buscar votos individuais
        with CamaraClient() as client:
            votos_api = client.obter_votos(str(vot.id))

        sim_count = 0
        nao_count = 0
        abstencao_count = 0

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
            elif voto_enum == VotoEnum.ABSTENCAO:
                abstencao_count += 1

            orientacao_partido = None
            if v.deputado_partido:
                orientacao_partido = partido_orientacao.get(v.deputado_partido.upper())

            voto = Voto(
                votacao_id=votacao.id,
                parlamentar_id=parlamentar.id,
                voto=voto_enum,
                orientacao_partido=orientacao_partido,
            )
            db.add(voto)

        votacao.votos_sim = sim_count
        votacao.votos_nao = nao_count
        votacao.abstencoes = abstencao_count

        count += 1
        if count % 10 == 0:
            db.commit()
            logger.info(f"  Processadas {count} votações...")

    db.commit()
    logger.info(f"✅ {count} novas votações processadas")
    return count


def run_full_sync(
    db: Session,
    anos: Optional[list[int]] = None,
) -> dict:
    """Executa sincronização completa: deputados + votações dos anos especificados.

    Args:
        anos: Lista de anos a sincronizar. Padrão: 2024 até o ano atual.

    Returns:
        Dict com contagens de deputados e votações por ano.
    """
    if anos is None:
        current_year = datetime.now().year
        anos = list(range(2024, current_year + 1))

    logger.info("=" * 60)
    logger.info(f"ZIL Crawler — Câmara dos Deputados — anos: {anos}")
    logger.info("=" * 60)

    # Abrir IngestionRun para full_sync
    run = IngestionRun(
        tipo="full_sync",
        status="running",
        iniciado_em=datetime.utcnow(),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    total_deputados = 0
    total_votacoes = 0
    erros = []

    try:
        total_deputados = sync_deputados(db)
        run.registros_criados += total_deputados

        for ano in anos:
            try:
                n = sync_votacoes(db, ano=ano)
                total_votacoes += n
                run.registros_criados += n
            except Exception as e:
                msg = f"Falha ao sincronizar votações de {ano}: {e}"
                logger.error(msg)
                erros.append({"ano": ano, "mensagem": str(e)})
                run.erros_count += 1

        run.status = "success" if not erros else "partial"

    except Exception as e:
        logger.error(f"Falha fatal em run_full_sync: {e}")
        run.status = "failed"
        run.erros_count += 1
        erros.append({"mensagem": str(e)})
        run.erro_detalhes = erros
        run.finalizado_em = datetime.utcnow()
        run.registros_processados = total_deputados + total_votacoes
        db.commit()
        raise

    run.finalizado_em = datetime.utcnow()
    run.registros_processados = total_deputados + total_votacoes
    if erros:
        run.erro_detalhes = erros
    db.commit()

    logger.info("=" * 60)
    logger.info(f"Sync completo! Deputados: {total_deputados}, Votações: {total_votacoes}")
    logger.info("=" * 60)

    return {"deputados": total_deputados, "votacoes": total_votacoes, "erros": erros}


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent.parent / "apps" / "api"))
    from core.config import SessionLocal

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    anos_arg = [int(a) for a in sys.argv[1:]] if len(sys.argv) > 1 else None

    with SessionLocal() as db:
        run_full_sync(db, anos=anos_arg)
