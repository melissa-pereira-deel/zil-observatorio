#!/usr/bin/env python3
"""Baixa as tabelas de código da Câmara e do Senado, compara com os snapshots e grava a diferença.

Roda por PR, não no cron: muda arquivos do repositório, não o banco.

    python scripts/atualizar_referencias_tramitacao.py [--verificar] [--aceitar-remocoes] [--dir data/tramitacao]

Saída: 0 em dia ou gravado; 1 erro (rede, fonte fora do formato ou vazia, --dir inexistente, gravação
recusada ou interrompida); 2 só com --verificar, há diferença. Só a gravação interrompida pode deixar
arquivo trocado: ver `gravar`.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import date, datetime
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

import httpx

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from packages.tramitacao.referencias import SUBDIRETORIO, TABELAS, Plano, planejar  # noqa: E402

DIRETORIO_PADRAO = _REPO_ROOT / "data" / "tramitacao"


def baixar(transport: Optional[httpx.BaseTransport], intervalo: float) -> dict[str, object]:
    corpos: dict[str, object] = {}
    with httpx.Client(timeout=30, transport=transport, headers={"Accept": "application/json"}) as cliente:
        for indice, (arquivo, (url, _)) in enumerate(TABELAS.items()):
            if indice:
                time.sleep(intervalo)
            resposta = cliente.get(url)
            resposta.raise_for_status()
            corpos[arquivo] = resposta.json()
    return corpos


def gravar(diretorio: Path, gravacoes: dict[str, str]) -> None:
    """Cada arquivo é trocado de forma atômica; o conjunto não é.

    Escrever tudo em temporários antes de trocar cobre a falha mais provável (disco cheio): nela, nada
    muda. Uma falha entre duas trocas deixa parte dos arquivos nova. Por isso os snapshots são os
    últimos: enquanto um deles não foi trocado, a diferença continua visível, e rodar de novo termina o
    trabalho, porque YAML já ajustado não é trocado outra vez. Na ordem inversa, a segunda execução não
    veria mais a diferença e os YAMLs ficariam para trás.
    """
    temporarios: list[tuple[Path, Path]] = []
    snapshots_por_ultimo = sorted(gravacoes, key=lambda relativo: relativo.startswith(f"{SUBDIRETORIO}/"))
    try:
        for relativo in snapshots_por_ultimo:
            conteudo = gravacoes[relativo]
            destino = diretorio / relativo
            destino.parent.mkdir(parents=True, exist_ok=True)
            temporario = destino.with_name(destino.name + ".tmp")
            temporarios.append((temporario, destino))
            temporario.write_bytes(conteudo.encode("utf-8"))
        for temporario, destino in temporarios:
            os.replace(temporario, destino)
    finally:
        for temporario, _ in temporarios:
            temporario.unlink(missing_ok=True)


def imprimir(plano: Plano) -> None:
    for tabela in plano.tabelas:
        if tabela.linha_de_base:
            print(f"{tabela.arquivo}: {tabela.total} itens, linha de base (sem snapshot anterior)")
            continue
        print(f"{tabela.arquivo}: {tabela.total} itens{'' if tabela.mudou else ', sem diferença'}")
        dif = tabela.diferenca
        for item in dif.novos:
            print(f'  novo      {item["cod"]}: "{item["nome"]}"')
        for item in dif.removidos:
            print(f'  removido  {item["cod"]}: "{item["nome"]}"')
        for cod, antigo, novo in dif.renomeados:
            print(f'  renomeado {cod}: "{antigo}" -> "{novo}"')
        for cod in dif.alterados:
            print(f"  alterado  {cod}: outro campo mudou; não pede mapeamento")

    if plano.entradas_afetadas:
        print("\nEntradas afetadas (para o lote de revisão):")
        for entrada in dict.fromkeys(plano.entradas_afetadas):
            print(f"  {entrada}")
    if plano.decisoes_humanas:
        print("\nPrecisa de decisão humana:")
        for decisao in dict.fromkeys(plano.decisoes_humanas):
            print(f"  {decisao}")
    if plano.problemas:
        print("\nA gravação não pode seguir:")
        for problema in plano.problemas:
            print(f"  {problema}")


def main(
    argv: Optional[list[str]] = None,
    transport: Optional[httpx.BaseTransport] = None,
    intervalo: float = 1.0,
    hoje: Optional[date] = None,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--verificar", action="store_true", help="só compara: sai 2 se houver diferença")
    parser.add_argument("--aceitar-remocoes", action="store_true", help="grava mesmo com mais de 10%% a menos de itens")
    parser.add_argument("--dir", type=Path, default=DIRETORIO_PADRAO, help="diretório de data/tramitacao")
    args = parser.parse_args(argv)
    hoje = hoje or datetime.now(ZoneInfo("America/Sao_Paulo")).date()

    # Sem isto, um --dir digitado errado viraria linha de base e criaria uma árvore nova com exit 0.
    if not args.dir.is_dir():
        print(f"Erro: o diretório {args.dir} não existe. Nada foi gravado.", file=sys.stderr)
        return 1

    try:
        plano = planejar(args.dir, baixar(transport, intervalo), hoje, args.aceitar_remocoes)
    except httpx.HTTPError as exc:
        print(f"Erro de rede: {exc}. Nada foi gravado.", file=sys.stderr)
        return 1
    except ValueError as exc:  # inclui JSON inválido e ReferenciaInvalida
        print(f"Erro: {exc}. Nada foi gravado.", file=sys.stderr)
        return 1

    imprimir(plano)

    # Tabela vazia é falha da fonte, não diferença: quem automatiza sobre o código de saída não pode
    # ler uma como a outra. As demais recusas dependem de decisão humana e seguem como diferença.
    if plano.fonte_vazia or (plano.problemas and not args.verificar):
        print("\nNada foi gravado.")
        return 1
    if args.verificar:
        return 2 if plano.mudou else 0
    if plano.gravacoes:
        try:
            gravar(args.dir, plano.gravacoes)
        except OSError as exc:
            print(f"Erro ao gravar: {exc}. Parte dos arquivos pode ter mudado; rode de novo.", file=sys.stderr)
            return 1
        print("\nGravados:")
        for relativo in plano.gravacoes:
            print(f"  {relativo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
