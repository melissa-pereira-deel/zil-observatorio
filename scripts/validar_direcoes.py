"""Valida os arquivos de direções editoriais antes que um erro chegue ao score.

Hoje nada valida `data/direcoes/*.yml`. O `apply_direcoes.py` lê só quatro campos
e ignora o resto; `justificativa` e `validacao` não são lidos por código nenhum.
Um `direcao: Sim` com maiúscula, ou um `peso: 5`, passa em silêncio e distorce o
Score ZIL sem que ninguém perceba — num projeto cujo ativo é ser confiável sobre
fatos, isso é o pior tipo de falha.

Uso (da raiz do repositório):

    python scripts/validar_direcoes.py
    python scripts/validar_direcoes.py --dir data/direcoes

Sai com código 1 se encontrar qualquer problema, para poder rodar em CI.
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

import yaml

DIRECOES_VALIDAS = {"sim", "nao"}
PESOS_VALIDOS = {0.5, 1.0, 2.0, 3.0}
VALIDACOES_VALIDAS = {"nao-validado", "revisado"}
FONTES_VALIDAS = {"camara", "senado"}
OBRIGATORIOS = ("fonte_id", "fonte", "direcao")


def validar_arquivo(caminho: Path) -> list[str]:
    """Devolve a lista de problemas encontrados. Lista vazia = arquivo válido."""
    problemas: list[str] = []

    try:
        conteudo = yaml.safe_load(caminho.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        return [f"{caminho.name}: YAML inválido — {e}"]

    direcoes = conteudo.get("direcoes")
    if direcoes is None:
        return [f"{caminho.name}: falta a chave raiz `direcoes`"]
    if not isinstance(direcoes, list):
        return [f"{caminho.name}: `direcoes` deveria ser uma lista"]

    vistos: dict[str, int] = {}

    for i, d in enumerate(direcoes, start=1):
        onde = f"{caminho.name}[{i}]"

        if not isinstance(d, dict):
            problemas.append(f"{onde}: entrada não é um mapa")
            continue

        for campo in OBRIGATORIOS:
            if not d.get(campo):
                problemas.append(f"{onde}: campo obrigatório `{campo}` ausente ou vazio")

        fonte = d.get("fonte")
        if fonte and fonte not in FONTES_VALIDAS:
            problemas.append(
                f"{onde}: `fonte: {fonte}` — esperado um de {sorted(FONTES_VALIDAS)}"
            )

        direcao = d.get("direcao")
        if direcao and direcao not in DIRECOES_VALIDAS:
            problemas.append(
                f"{onde}: `direcao: {direcao}` — esperado `sim` ou `nao` "
                "(minúsculas, sem acento)"
            )

        if "peso" in d:
            try:
                peso = float(d["peso"])
                if peso not in PESOS_VALIDOS:
                    problemas.append(
                        f"{onde}: `peso: {d['peso']}` — esperado um de "
                        f"{sorted(PESOS_VALIDOS)} (ver PRD §10)"
                    )
            except (TypeError, ValueError):
                problemas.append(f"{onde}: `peso: {d['peso']}` não é numérico")

        validacao = d.get("validacao")
        if validacao and validacao not in VALIDACOES_VALIDAS:
            problemas.append(
                f"{onde}: `validacao: {validacao}` — esperado um de "
                f"{sorted(VALIDACOES_VALIDAS)}"
            )

        # A justificativa não é lida por código nenhum, mas é a única coisa que
        # torna a classificação auditável por um humano depois. Sem ela, a
        # entrada é um número sem procedência.
        justificativa = (d.get("justificativa") or "").strip()
        if not justificativa:
            problemas.append(f"{onde}: sem `justificativa` — obrigatória por governança")
        elif len(justificativa) < 40:
            problemas.append(
                f"{onde}: `justificativa` com {len(justificativa)} caracteres — "
                "curta demais para explicar uma decisão editorial"
            )

        chave = f"{d.get('fonte')}:{d.get('fonte_id')}"
        if d.get("fonte_id"):
            if chave in vistos:
                problemas.append(
                    f"{onde}: `{chave}` duplicado (já aparece na entrada {vistos[chave]})"
                )
            else:
                vistos[chave] = i

    return problemas


def resumir(diretorio: Path) -> dict:
    """Conta direções e validações — expõe o desequilíbrio do corpus."""
    contagem = Counter()
    validacoes = Counter()
    total = 0
    for arquivo in sorted(diretorio.glob("*.yml")):
        conteudo = yaml.safe_load(arquivo.read_text(encoding="utf-8")) or {}
        for d in conteudo.get("direcoes") or []:
            if isinstance(d, dict):
                total += 1
                contagem[d.get("direcao", "?")] += 1
                validacoes[d.get("validacao", "—")] += 1
    return {"total": total, "direcoes": dict(contagem), "validacoes": dict(validacoes)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--dir", type=Path, default=Path("data/direcoes"),
                        help="diretório dos YAMLs (padrão: data/direcoes)")
    args = parser.parse_args()

    if not args.dir.exists():
        print(f"✗ Diretório não encontrado: {args.dir}")
        sys.exit(1)

    arquivos = sorted(args.dir.glob("*.yml"))
    if not arquivos:
        print(f"✗ Nenhum .yml em {args.dir}")
        sys.exit(1)

    todos: list[str] = []
    for arquivo in arquivos:
        todos.extend(validar_arquivo(arquivo))

    resumo = resumir(args.dir)
    print(f"Validando {len(arquivos)} arquivo(s) — {resumo['total']} direções\n")

    if todos:
        print(f"✗ {len(todos)} problema(s):\n")
        for p in todos:
            print(f"  · {p}")
        print()
    else:
        print("✓ Nenhum problema de formato.\n")

    print(f"Direções: {resumo['direcoes']}")
    print(f"Validação: {resumo['validacoes']}")

    # Variância zero não é erro de formato, mas é um defeito real do corpus: com
    # todas as direções iguais, o score premia quem vota "sim" em tudo — ou seja,
    # mede presença e disciplina partidária, não alinhamento ZIL.
    if len(resumo["direcoes"]) == 1 and resumo["total"] > 1:
        unica = next(iter(resumo["direcoes"]))
        print(
            f"\n⚠ Todas as {resumo['total']} direções são `{unica}`. O Score ZIL "
            "não discrimina nesse corpus: quem vota sempre nessa direção tira nota "
            "máxima. Priorize votações em que a posição pró-soberania seja a oposta."
        )

    sys.exit(1 if todos else 0)


if __name__ == "__main__":
    main()
