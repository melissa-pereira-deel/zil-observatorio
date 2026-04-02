"""Crawler do Senado Federal.

Ingere senadores, matérias (proposições) e votações da API de Dados Abertos
do Senado e classifica por pauta ZIL.
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import select

import sys
from pathlib import Path

# Ensure both repo root and apps/api are in sys.path (ADR-002)
_repo_root = str(Path(__file__).parent.parent.parent)
_api_dir = str(Path(__file__).parent.parent.parent / "apps" / "api")
for _p in (_repo_root, _api_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from packages.senado_client import SenadoClient
from apps.workers.classifiers import classificar_votacao, classificar_proposicao, relevancia_score

from models import (  # noqa: E402
    Parlamentar, Votacao, Voto, Proposicao, IngestionRun,
    FonteEnum, VotoEnum,
)

logger = logging.getLogger(__name__)

VOTO_MAP = {
    "Sim": VotoEnum.SIM,
    "S": VotoEnum.SIM,
    "Não": VotoEnum.NAO,
    "N": VotoEnum.NAO,
    "Abstenção": VotoEnum.ABSTENCAO,
    "A": VotoEnum.ABSTENCAO,
    "Obstrução": VotoEnum.OBSTRUCAO,
    "P-OD": VotoEnum.OBSTRUCAO,
    "Ausente": VotoEnum.AUSENTE,
    "AP": VotoEnum.AUSENTE,
}


def normalizar_voto(sigla: str) -> VotoEnum:
    return VOTO_MAP.get(sigla, VotoEnum.AUSENTE)


def sync_senadores(db: Session) -> int:
    """Sincroniza senadores em exercício. Retorna número de novos/atualizados."""
    client = SenadoClient()
    logger.info("Sincronizando senadores em exercício...")

    senadores = client.listar_senadores()
    logger.info(f"  API retornou {len(senadores)} senadores")

    count = 0
    for s in senadores:
        fonte_id = str(s.id)
        existing = db.execute(
            select(Parlamentar).where(
                Parlamentar.fonte_id == fonte_id,
                Parlamentar.fonte == FonteEnum.SENADO,
            )
        ).scalar_one_or_none()

        if existing:
            existing.nome = s.nome or existing.nome
            existing.partido = s.siglaPartido or existing.partido
            existing.uf = s.siglaUf or existing.uf
            existing.foto_url = s.urlFoto or existing.foto_url
            existing.email = s.email or existing.email
            existing.nome_civil = s.nomeCivil or existing.nome_civil
        else:
            parlamentar = Parlamentar(
                fonte_id=fonte_id,
                fonte=FonteEnum.SENADO,
                nome=s.nome,
                partido=s.siglaPartido,
                uf=s.siglaUf,
                foto_url=s.urlFoto,
                email=s.email,
                nome_civil=s.nomeCivil,
            )
            db.add(parlamentar)
            count += 1

    db.commit()
    logger.info(f"✅ {count} senadores novos criados, {len(senadores) - count} atualizados")
    return count


def sync_materias(db: Session, ano: int) -> int:
    """Sincroniza matérias (proposições) do Senado para um ano. Retorna contagem."""
    client = SenadoClient()
    logger.info(f"Sincronizando matérias Senado {ano}...")

    materias = client.listar_materias_ano(ano)
    logger.info(f"  API retornou {len(materias)} matérias")

    count = 0
    for m in materias:
        fonte_id = str(m.id)
        existing = db.execute(
            select(Proposicao).where(
                Proposicao.fonte_id == fonte_id,
                Proposicao.fonte == FonteEnum.SENADO,
            )
        ).scalar_one_or_none()

        ementa = m.ementa or ""
        categorias = classificar_proposicao(ementa=ementa)
        relevancia = relevancia_score(ementa) if ementa else 0.0

        if existing:
            existing.ementa = ementa or existing.ementa
            existing.situacao = m.situacao or existing.situacao
            existing.categorias_zil = categorias if categorias else existing.categorias_zil
            existing.relevancia_zil = relevancia if relevancia > 0 else existing.relevancia_zil
        else:
            proposicao = Proposicao(
                fonte_id=fonte_id,
                fonte=FonteEnum.SENADO,
                tipo=m.sigla,
                numero=m.numero,
                ano=m.ano,
                ementa=ementa,
                situacao=m.situacao,
                data_apresentacao=datetime.fromisoformat(m.data_apresentacao)
                if m.data_apresentacao
                else None,
                categorias_zil=categorias if categorias else None,
                relevancia_zil=relevancia if relevancia > 0 else None,
            )
            db.add(proposicao)
            count += 1

    db.commit()
    logger.info(f"✅ {count} novas matérias criadas")
    return count


def sync_votacoes_materia(db: Session, materia_id: int) -> int:
    """Sincroniza votações de uma matéria. Retorna contagem de votações novas."""
    client = SenadoClient()
    votacoes = client.listar_votacoes_materia(materia_id)
    count = 0

    # Find the proposicao in DB
    proposicao = db.execute(
        select(Proposicao).where(
            Proposicao.fonte_id == str(materia_id),
            Proposicao.fonte == FonteEnum.SENADO,
        )
    ).scalar_one_or_none()

    for v in votacoes:
        fonte_id = str(v.id)
        existing = db.execute(
            select(Votacao).where(
                Votacao.fonte_id == fonte_id,
                Votacao.fonte == FonteEnum.SENADO,
            )
        ).scalar_one_or_none()

        descricao = v.descricao or ""
        categorias = classificar_votacao(descricao=descricao)

        data_votacao = None
        if v.data:
            try:
                data_votacao = datetime.fromisoformat(v.data)
            except ValueError:
                pass

        if existing:
            existing.descricao = descricao or existing.descricao
            existing.resultado = v.resultado or existing.resultado
            existing.categorias_zil = categorias if categorias else existing.categorias_zil
            if proposicao and not existing.proposicao_id:
                existing.proposicao_id = proposicao.id
            db.flush()
            votacao_obj = existing
        else:
            votacao_obj = Votacao(
                fonte_id=fonte_id,
                fonte=FonteEnum.SENADO,
                proposicao_id=proposicao.id if proposicao else None,
                data=data_votacao,
                descricao=descricao,
                resultado=v.resultado,
                categorias_zil=categorias if categorias else None,
                peso=1.0,
            )
            db.add(votacao_obj)
            db.flush()
            count += 1

        # Sync individual votes
        try:
            votos = client.obter_votos_votacao(fonte_id)
            _sync_votos(db, votacao_obj, votos)
        except Exception as e:
            logger.warning(f"  Erro ao buscar votos da votação {fonte_id}: {e}")

    db.commit()
    return count


def _sync_votos(db: Session, votacao: Votacao, votos_api) -> None:
    """Upsert dos votos individuais de uma votação."""
    for v in votos_api:
        fonte_id = str(v.senador_id)
        parlamentar = db.execute(
            select(Parlamentar).where(
                Parlamentar.fonte_id == fonte_id,
                Parlamentar.fonte == FonteEnum.SENADO,
            )
        ).scalar_one_or_none()

        if not parlamentar:
            continue

        existing_voto = db.execute(
            select(Voto).where(
                Voto.votacao_id == votacao.id,
                Voto.parlamentar_id == parlamentar.id,
            )
        ).scalar_one_or_none()

        voto_enum = normalizar_voto(v.voto)

        if existing_voto:
            existing_voto.voto = voto_enum
        else:
            db.add(Voto(
                votacao_id=votacao.id,
                parlamentar_id=parlamentar.id,
                voto=voto_enum,
            ))


def run_full_sync(db: Session, anos: Optional[list[int]] = None) -> dict:
    """Executa sincronização completa: senadores + matérias + votações.

    Args:
        anos: Anos a sincronizar. Padrão: 2024 até o ano atual.

    Returns:
        Dict com contagens de senadores, matérias e votações.
    """
    if anos is None:
        current_year = datetime.now().year
        anos = list(range(2024, current_year + 1))

    logger.info("=" * 60)
    logger.info(f"ZIL Crawler — Senado Federal — anos: {anos}")
    logger.info("=" * 60)

    run = IngestionRun(
        tipo="full_sync_senado",
        status="running",
        iniciado_em=datetime.utcnow(),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    total_senadores = 0
    total_materias = 0
    total_votacoes = 0
    erros = []

    try:
        total_senadores = sync_senadores(db)
        run.registros_criados += total_senadores

        for ano in anos:
            try:
                n_materias = sync_materias(db, ano=ano)
                total_materias += n_materias
                run.registros_criados += n_materias
            except Exception as e:
                msg = f"Falha ao sincronizar matérias de {ano}: {e}"
                logger.error(msg)
                erros.append({"ano": ano, "mensagem": str(e)})
                run.erros_count += 1

        run.status = "success" if not erros else "partial"

    except Exception as e:
        logger.error(f"Falha fatal em run_full_sync_senado: {e}")
        run.status = "failed"
        run.erros_count += 1
        erros.append({"mensagem": str(e)})
        run.erro_detalhes = erros
        run.finalizado_em = datetime.utcnow()
        run.registros_processados = total_senadores + total_materias
        db.commit()
        raise

    run.finalizado_em = datetime.utcnow()
    run.registros_processados = total_senadores + total_materias + total_votacoes
    if erros:
        run.erro_detalhes = erros
    db.commit()

    logger.info("=" * 60)
    logger.info(
        f"Sync Senado completo! "
        f"Senadores: {total_senadores}, "
        f"Matérias: {total_materias}, "
        f"Votações: {total_votacoes}"
    )
    logger.info("=" * 60)

    return {
        "senadores": total_senadores,
        "materias": total_materias,
        "votacoes": total_votacoes,
        "erros": erros,
    }


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "api"))
    from core.config import SessionLocal

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    anos_arg = [int(a) for a in sys.argv[1:]] if len(sys.argv) > 1 else None

    with SessionLocal() as db:
        run_full_sync(db, anos=anos_arg)
