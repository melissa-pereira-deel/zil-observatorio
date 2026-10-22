"""Fontes externas curadas — inspeção pela linha de comando.

Nada aqui gasta tokens; só rede pública, só leitura. Serve para conferir o
catálogo, ver o que uma série devolve com proveniência, e montar o bloco de
contexto que as lentes receberiam — sem chamar a API da Anthropic.

Uso (da raiz do repositório):

    python scripts/fontes.py --catalogo
        Valida data/fontes/catalogo.yml e lista fontes, séries e hash.

    python scripts/fontes.py --serie bcb_sgs.selic_meta --de 2025-03-01 --ate 2025-03-31
        Consulta uma série no intervalo e imprime cada observação com URL e
        data da consulta. --sem-cache força a rede.

    python scripts/fontes.py --contexto --data 2025-03-10 --tema "Saúde" --categoria ZIL-MIN
        Monta o contexto pré-registrado para uma proposição apresentada
        naquela data, com esses temas, e imprime o bloco como vai ao prompt.

    python scripts/fontes.py --resolver "a Selic chegou a 25% e a população passou de 200 milhões"
        Mostra quais séries do catálogo casam com um texto — é o que o
        verificador (Fase B) vai usar para escolher o que conferir.
"""

import argparse
import sys
from datetime import date
from pathlib import Path

_repo_root = str(Path(__file__).parent.parent)
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from apps.workers.fontes import (  # noqa: E402
    carregar_catalogo,
    carregar_plano,
    consultar_serie,
    montar_contexto,
)


def mostrar_catalogo() -> int:
    c = carregar_catalogo()
    p = carregar_plano(catalogo=c)
    print(f"catálogo {c.origem} · hash {c.hash} · versão {c.versao}")
    print(f"plano {p.origem} · hash {p.hash} · sempre {list(p.sempre)} · {len(p.por_tema)} temas\n")
    print(f"hosts permitidos na rede: {sorted(c.hosts_permitidos)}\n")
    for f in c.fontes.values():
        estado = "habilitada" if f.habilitada else "NÃO habilitada"
        prim = "primária" if f.primaria else f"secundária ({f.uso})"
        chave = f" · chave: {f.chave}" if f.chave else ""
        print(f"{f.id:22} {f.natureza:20} {prim:34} {estado}{chave}")
        print(f"{'':22} {f.nome} · {f.host}")
        for s in f.series.values():
            dep = f" · primária de {s.primaria_de}" if s.primaria_de else ""
            rev = "revisável" if s.revisavel else "definitiva"
            print(f"{'':24} {s.ref:30} {s.frequencia:7} {s.unidade:10} {rev}{dep}")
            print(f"{'':24}   conceitos: {', '.join(s.conceitos)}")
    return 0


def mostrar_serie(ref: str, de: str, ate: str, sem_cache: bool) -> int:
    c = carregar_catalogo()
    extra = {"cache_dir": None} if sem_cache else {}
    res = consultar_serie(ref, date.fromisoformat(de), date.fromisoformat(ate), catalogo=c, **extra)
    s = c.serie(ref)
    print(f"{s.ref} — {s.descricao} ({s.unidade}, {s.frequencia}, {'revisável' if s.revisavel else 'definitiva'})")
    if not res.ok:
        print(f"✗ {res.erro}")
        return 1
    origem = "cache" if res.do_cache else "rede"
    print(f"url: {res.url}\nconsultado em: {res.data_consulta} ({origem}) · {len(res.observacoes)} observações")
    for o in res.observacoes:
        print(f"  {o.data}  {o.valor}")
    return 0


def mostrar_contexto(data: str, temas: list[str], categorias: list[str]) -> int:
    ctx = montar_contexto(ancora=data, temas_oficiais=temas, categorias_zil=categorias)
    print(f"plano: {ctx.motivo}\n")
    print(ctx.para_prompt())
    print(f"\nhash do contexto: {ctx.hash} · plano {ctx.plano_hash} · catálogo {ctx.catalogo_hash}")
    return 0 if not ctx.vazio else 1


def mostrar_resolucao(texto: str) -> int:
    c = carregar_catalogo()
    series = c.resolver(texto)
    if not series:
        print("nenhuma série do catálogo casa com esse texto — sem fonte curada")
        return 1
    for s in series:
        print(f"{s.ref:30} via conceitos {[k for k in s.conceitos if k.lower() in texto.lower()] or '(normalizado)'}")
    print(f"\norigens independentes: {sorted(c.independentes(series))}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--catalogo", action="store_true")
    ap.add_argument("--serie")
    ap.add_argument("--de")
    ap.add_argument("--ate")
    ap.add_argument("--sem-cache", action="store_true")
    ap.add_argument("--contexto", action="store_true")
    ap.add_argument("--data", help="data de apresentação (AAAA-MM-DD) — a âncora do contexto")
    ap.add_argument("--tema", action="append", default=[])
    ap.add_argument("--categoria", action="append", default=[])
    ap.add_argument("--resolver")
    a = ap.parse_args()

    if a.catalogo:
        return mostrar_catalogo()
    if a.serie:
        if not (a.de and a.ate):
            ap.error("--serie exige --de e --ate (AAAA-MM-DD) — consulta é sempre por intervalo explícito")
        return mostrar_serie(a.serie, a.de, a.ate, a.sem_cache)
    if a.contexto:
        if not a.data:
            ap.error("--contexto exige --data: o contexto é ancorado na data de apresentação")
        return mostrar_contexto(a.data, a.tema, a.categoria)
    if a.resolver:
        return mostrar_resolucao(a.resolver)
    ap.error("escolha --catalogo, --serie ..., --contexto ... ou --resolver ...")
    return 2


if __name__ == "__main__":
    sys.exit(main())
