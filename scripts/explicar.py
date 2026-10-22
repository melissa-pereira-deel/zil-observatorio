"""Pipeline de explicação de proposições — linha de comando.

Este script é o que gasta tokens. A orquestração em `apps/workers/explicacao/`
é determinística e testada sem rede; aqui entra a chave.

Uso (da raiz do repositório):

    python scripts/explicar.py --testar-extracao --n 20
        Baixa o inteiro teor de N proposições recentes e reporta, por PDF,
        método de extração, chars/página e se achou JUSTIFICAÇÃO. É o
        experimento S5 da Fase 1 — não usa a API da Anthropic.

    python scripts/explicar.py --caso dissenso-plantado --dry-run
        Monta os prompts de um caso construído e imprime tamanhos. Sem rede.

    python scripts/explicar.py --proposicao 2558692 [--pipeline v1] [--gravar]
        Roda o pipeline de verdade sobre uma proposição da Câmara. Exige
        ANTHROPIC_API_KEY. Com --gravar, persiste na tabela `explicacoes`.
        O contexto econômico pré-registrado (apps/workers/fontes) é montado
        antes e entra idêntico em toda lente que o declara.

    python scripts/explicar.py --proposicao 2558692 --pipeline v2
        Igual, com verificação de alegações: extração cega, verificador com
        uma ferramenta fechada (séries do catálogo) e comparação pelo código.
        Contraditas e fontes divergentes vão para data/fontes/fila/, para
        decisão humana.

    python scripts/explicar.py --proposicao 2558692 --contexto
        Só monta e imprime o contexto que as lentes receberiam — ficha,
        temas, séries com proveniência. Rede pública, sem chave da Anthropic.

    python scripts/explicar.py --calibrar [--pipeline v1] [--out DIR]
        Roda os casos construídos com chamada real e imprime as métricas 1–9.
        Fase 2. Exige chave.
"""

import argparse
import json
import logging
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Optional

import yaml

_repo_root = str(Path(__file__).parent.parent)
_api_dir = str(Path(__file__).parent.parent / "apps" / "api")
for _p in (_repo_root, _api_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from apps.workers.explicacao import Insumos, explicar  # noqa: E402
from apps.workers.explicacao.agentes import carregar_agentes  # noqa: E402
from apps.workers.explicacao.coleta import coletar_ficha  # noqa: E402
from apps.workers.explicacao.extracao import baixar_e_extrair  # noqa: E402
from apps.workers.explicacao.pipeline import (  # noqa: E402
    consultar_agente,
    montar_prompt_lente,
    montar_prompt_sintese,
)
from apps.workers.explicacao.roteamento import carregar_pipeline_por_nome, rotear  # noqa: E402
from apps.workers.fontes import montar_contexto  # noqa: E402
from apps.workers.explicacao.verificacao import fila_humana  # noqa: E402
from packages.camara_client import CamaraClient  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

CASOS = Path(_repo_root) / "data" / "explicacao" / "casos" / "construidos.yml"
FILA = Path(_repo_root) / "data" / "fontes" / "fila"


def _exigir_chave() -> None:
    from core.config import settings

    if not settings.ANTHROPIC_API_KEY:
        raise SystemExit("✗ ANTHROPIC_API_KEY não configurada — este modo gasta tokens e exige a chave no .env")


def testar_extracao(n: int, ano: int) -> int:
    """Experimento S5: o inteiro teor é texto nativo? Traz a justificação?"""
    with CamaraClient() as c:
        props = c.listar_proposicoes(ano, tipo="PL")[:n]
        print(f"{'proposição':16} {'método':13} {'págs':>4} {'c/pág':>6} {'justificação':>12}  {'origem':10}")
        total = texto = just = 0
        for p in props:
            d = c.obter_proposicao(p.id)
            rotulo = f"{d.get('siglaTipo', '?')} {d.get('numero', '?')}/{d.get('ano', '?')}"
            t = baixar_e_extrair(d.get("urlInteiroTeor") or "")
            total += 1
            if t.utilizavel:
                texto += 1
            if t.justificacao:
                just += 1
            origem = "senado" if t.origem_senado else "câmara"
            print(f"{rotulo:16} {t.metodo:13} {t.paginas:4} {t.chars_por_pagina:6.0f} {'sim' if t.justificacao else '—':>12}  {origem:10}")
    print(f"\n{total} PDFs: {texto} com texto nativo, {just} com seção de justificação")
    print("Sem justificação não é falha: autógrafo do Senado e texto final emendado não a trazem (S5).")
    return 0


def _caso(caso_id: str) -> dict:
    casos = yaml.safe_load(CASOS.read_text(encoding="utf-8"))["casos"]
    for c in casos:
        if c["id"] == caso_id:
            return c
    raise SystemExit(f"✗ caso não encontrado: {caso_id} — disponíveis: {[c['id'] for c in casos]}")


def dry_run_caso(caso_id: str, pipeline_nome: str) -> int:
    from tests.unit.test_explicacao_harness import _insumos  # mesma montagem dos testes

    caso = _caso(caso_id)
    pipe = carregar_pipeline_por_nome(pipeline_nome)
    ag = carregar_agentes()
    ins = _insumos(caso)
    lentes, motivo = rotear(ins.ficha.temas_oficiais, ins.categorias_zil, pipe)
    print(f"caso {caso_id} · pipeline {pipe.nome}@{pipe.versao}")
    print(f"roteamento: {motivo}")
    chars = 0
    for nome in lentes:
        p = montar_prompt_lente(ag[nome], ins)
        chars += len(p)
        print(f"  {nome:16} prompt {len(p):6} chars")
    p = montar_prompt_sintese(ag[pipe.sintetizador], ins, [])
    chars += len(p)
    print(f"  {pipe.sintetizador:16} prompt {len(p):6} chars")
    chamadas = f"{len(lentes) + 2}"
    if pipe.verifica:
        # A extração é uma chamada; o verificador, uma conversa por alegação
        # verificável, até `max_alegacoes`, cada uma com até 6 rodadas.
        chamadas += f" + 1 de extração + até {pipe.max_alegacoes} verificações (até 6 rodadas cada)"
    print(f"\nchamadas: {chamadas} · caracteres de prompt: {chars:,}\nNada foi chamado — --dry-run não usa a API.")
    return 0


def _contexto_da_ficha(ficha):
    """Uma chamada por execução — é o que torna a informação simétrica entre
    as lentes. Sem data de apresentação não há âncora, e o contexto fica vazio
    declarado, não inventado."""
    if not ficha.data_apresentacao:
        logger.warning("proposição sem data de apresentação — contexto econômico não montado")
        return None
    ctx = montar_contexto(ancora=ficha.data_apresentacao, temas_oficiais=ficha.temas_oficiais)
    logger.info("contexto: %d série(s), %d lacuna(s) · hash %s", len(ctx.linhas), len(ctx.lacunas), ctx.hash)
    return ctx


def mostrar_contexto(proposicao_id: int) -> int:
    with CamaraClient() as c:
        ficha = coletar_ficha(c, proposicao_id)
    print(f"{ficha.rotulo} · apresentada em {ficha.data_apresentacao or '(não informada)'} · temas: {ficha.temas_oficiais or 'nenhum'}\n")
    ctx = _contexto_da_ficha(ficha)
    if ctx is None:
        return 1
    print(f"plano: {ctx.motivo}\n\n{ctx.para_prompt()}\n\nhash do contexto: {ctx.hash}")
    return 0 if not ctx.vazio else 1


def rodar_proposicao(proposicao_id: int, pipeline_nome: str, gravar_no_banco: bool, out: Optional[Path]) -> int:
    _exigir_chave()
    pipe = carregar_pipeline_por_nome(pipeline_nome)
    ag = carregar_agentes()
    with CamaraClient() as c:
        ficha = coletar_ficha(c, proposicao_id)
    texto = baixar_e_extrair(ficha.url_inteiro_teor)
    logger.info("ficha: %s · texto: %s (%d págs, %.0f c/pág) · justificação: %s",
                ficha.rotulo, texto.metodo, texto.paginas, texto.chars_por_pagina, "sim" if texto.justificacao else "não")
    ctx = _contexto_da_ficha(ficha)
    ins = Insumos(
        ficha=ficha, texto=texto,
        contexto_economico=ctx.para_prompt() if ctx else "",
        contexto_hash=ctx.hash if ctx else "",
        contexto_evidencias=ctx.evidencias() if ctx else None,
    )
    res = explicar(ins, pipe, ag, consultar_agente)

    print(f"\n{'═' * 70}\n{ficha.rotulo} · status: {res.status} · {res.metricas.get('roteamento')}")
    if res.resumo_didatico:
        print(f"\n[RESUMO DIDÁTICO · {len(res.resumo_didatico.texto)} chars]\n{res.resumo_didatico.texto}")
    if res.resumo_detalhado:
        print(f"\n[RESUMO DETALHADO · {len(res.resumo_detalhado.texto)} chars]\n{res.resumo_detalhado.texto}")
    if res.analise:
        print("\n[ANÁLISE SISTÊMICA]")
        print(json.dumps({k: v for k, v in asdict(res.analise).items() if k != "lentes"}, ensure_ascii=False, indent=2))
    if res.problemas:
        print("\n[PROBLEMAS]")
        for prob in res.problemas:
            print(f"  · {prob}")
    if res.verificacoes:
        print("\n[VERIFICAÇÕES]")
        for v in res.verificacoes:
            a = v.alegacao
            achado = f" · {v.ref} = {v.valor_encontrado} em {v.data_referencia}" if v.valor_encontrado is not None else ""
            print(f"  {a.id} {v.veredito:24} ({a.origem}) {a.texto[:90]}{achado}")
            if v.recusas:
                print(f"      recusas da ferramenta: {v.recusas}")
        fila = fila_humana(ficha.fonte, ficha.fonte_id, res.verificacoes)
        if fila:
            FILA.mkdir(parents=True, exist_ok=True)
            destino = FILA / f"{ficha.fonte}-{ficha.fonte_id}.yml"
            destino.write_text(
                "# Fila humana — alegações contraditas ou com fontes divergentes.\n"
                "# Preencha `decisao`. O modelo não decide o destino de uma contradição.\n"
                + yaml.safe_dump(fila, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            print(f"\n{len(fila)} item(ns) para decisão humana em {destino}")
    print(f"\n[MÉTRICAS] {json.dumps(res.metricas, ensure_ascii=False)}")
    if res.meta.erros:
        print("[ERROS]")
        for err in res.meta.erros:
            print(f"  · {err}")

    if out:
        out.mkdir(parents=True, exist_ok=True)
        (out / f"{ficha.fonte}-{ficha.fonte_id}.json").write_text(
            json.dumps(asdict(res), ensure_ascii=False, indent=2, default=str), encoding="utf-8"
        )
    if gravar_no_banco:
        from uuid import UUID

        from sqlalchemy import select

        from apps.workers.explicacao.persistencia import gravar, hash_texto
        from core.config import SessionLocal
        from models import FonteEnum, Proposicao

        with SessionLocal() as db:
            prop = db.execute(select(Proposicao).where(Proposicao.fonte_id == str(proposicao_id), Proposicao.fonte == FonteEnum.CAMARA)).scalar_one_or_none()
            if not prop:
                raise SystemExit("✗ proposição não está no banco — rode o discover/sync antes de gravar")
            linha = gravar(db, UUID(str(prop.id)), res, hash_texto(texto.texto))
            db.commit()
            print(f"\ngravado: explicacoes.id={linha.id}")
    return 0 if res.status == "pronto" else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--testar-extracao", action="store_true")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--ano", type=int, default=2025)
    ap.add_argument("--caso")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--proposicao", type=int)
    ap.add_argument("--contexto", action="store_true", help="só o contexto pré-registrado; sem chave")
    ap.add_argument("--pipeline", default="v1")
    ap.add_argument("--gravar", action="store_true")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--calibrar", action="store_true")
    a = ap.parse_args()

    if a.testar_extracao:
        return testar_extracao(a.n, a.ano)
    if a.caso:
        if not a.dry_run:
            raise SystemExit("✗ --caso só roda com --dry-run na Fase 1; chamada real sobre casos é --calibrar (Fase 2)")
        return dry_run_caso(a.caso, a.pipeline)
    if a.proposicao and a.contexto:
        return mostrar_contexto(a.proposicao)
    if a.proposicao:
        return rodar_proposicao(a.proposicao, a.pipeline, a.gravar, a.out)
    if a.calibrar:
        raise SystemExit("✗ --calibrar é Fase 2: exige os casos com chamada real e o registro das métricas em docs/decisions/007")
    ap.error("escolha --testar-extracao, --caso ... --dry-run, --proposicao ou --calibrar")
    return 2


if __name__ == "__main__":
    sys.exit(main())
