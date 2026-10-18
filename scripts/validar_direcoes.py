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
from typing import Optional

import httpx
import yaml

DIRECOES_VALIDAS = {"sim", "nao"}
PESOS_VALIDOS = {0.5, 1.0, 2.0, 3.0}
VALIDACOES_VALIDAS = {"nao-validado", "revisado"}
FONTES_VALIDAS = {"camara", "senado"}
OBRIGATORIOS = ("fonte_id", "fonte", "direcao")

# Art. 185 do Regimento Interno da Câmara: o processo simbólico é a REGRA —
# os favoráveis permanecem como estão, os contrários se manifestam, e o
# Presidente proclama só o resultado. Ninguém registra quem votou o quê.
#
# Consequência para o Score ZIL: uma votação simbólica não produz voto
# individual, logo não contribui com nada, por mais bem curada que esteja.
# Três das sete entradas curadas eram simbólicas e ninguém percebeu — elas
# tinham peso 3.0, 3.0 e 2.0 e somavam zero. Nada no fluxo contava isso.
#
# A votação nominal (Art. 186) é a exceção: quórum qualificado, decisão do
# Presidente, deliberação do Plenário ou pedido de verificação. Só nela o
# painel eletrônico registra cada deputado.
#
# Medido na varredura de 2023–2026: 211 de 246 votações são simbólicas (86%).
PROCESSOS_VALIDOS = {"nominal", "simbolica"}


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

        processo = d.get("processo")
        if processo and processo not in PROCESSOS_VALIDOS:
            problemas.append(
                f"{onde}: `processo: {processo}` — esperado um de "
                f"{sorted(PROCESSOS_VALIDOS)}"
            )

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
    processos = Counter()
    total = 0
    for arquivo in sorted(diretorio.glob("*.yml")):
        conteudo = yaml.safe_load(arquivo.read_text(encoding="utf-8")) or {}
        for d in conteudo.get("direcoes") or []:
            if isinstance(d, dict):
                total += 1
                contagem[d.get("direcao", "?")] += 1
                validacoes[d.get("validacao", "—")] += 1
                processos[d.get("processo", "nao-verificado")] += 1
    return {
        "total": total,
        "direcoes": dict(contagem),
        "validacoes": dict(validacoes),
        "processos": dict(processos),
    }


def entradas(diretorio: Path) -> list[dict]:
    """Todas as entradas de todos os arquivos, na ordem."""
    saida: list[dict] = []
    for arquivo in sorted(diretorio.glob("*.yml")):
        conteudo = yaml.safe_load(arquivo.read_text(encoding="utf-8")) or {}
        for d in conteudo.get("direcoes") or []:
            if isinstance(d, dict):
                saida.append(d)
    return saida


def verificar_processo_na_api(entrada: dict) -> tuple[Optional[str], Optional[str]]:
    """Descobre na API da Câmara se a votação teve voto individual.

    Devolve `(processo_observado, problema)`. `processo_observado` é
    "nominal" ou "simbolica"; `problema` só vem preenchido quando o que está
    declarado no YAML contradiz o que a API mostra, ou quando não deu para
    verificar.

    Uma requisição por entrada. É por isso que fica atrás de uma flag: o
    validador roda offline em segundos, e essa é uma qualidade a preservar.
    """
    fonte_id = str(entrada.get("fonte_id") or "")
    declarado = entrada.get("processo")

    if entrada.get("fonte") != "camara":
        return None, None  # só a Câmara tem esse endpoint

    url = f"https://dadosabertos.camara.leg.br/api/v2/votacoes/{fonte_id}/votos"
    try:
        resp = httpx.get(url, timeout=30)
        resp.raise_for_status()
        votos = resp.json().get("dados") or []
    except Exception as e:  # noqa: BLE001 — rede fora não é erro de dado
        return None, f"{fonte_id}: não foi possível verificar na API — {type(e).__name__}"

    observado = "nominal" if votos else "simbolica"

    if declarado and declarado != observado:
        return observado, (
            f"{fonte_id}: declarado `processo: {declarado}`, mas a API mostra "
            f"{len(votos)} voto(s) individual(is) — é {observado}"
        )
    if not declarado and observado == "simbolica":
        return observado, (
            f"{fonte_id}: votação **simbólica** sem `processo` declarado. Ela não "
            "produz voto individual (RICD art. 185) e não contribui para o Score "
            "ZIL. Marque com `processo: simbolica` para deixar isso explícito."
        )
    return observado, None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--dir", type=Path, default=Path("data/direcoes"),
                        help="diretório dos YAMLs (padrão: data/direcoes)")
    parser.add_argument("--verificar-api", action="store_true",
                        help="consulta a API da Câmara para conferir se cada "
                             "votação teve voto individual (uma requisição por "
                             "entrada; sem isto o validador roda offline)")
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
    print(f"Processo: {resumo['processos']}")

    # O número que a documentação deveria citar. Uma votação simbólica não
    # produz voto individual (RICD art. 185), então não alimenta o Score ZIL
    # por mais bem curada que esteja.
    simbolicas = resumo["processos"].get("simbolica", 0)
    if simbolicas:
        alimentam = resumo["total"] - simbolicas
        print(
            f"\n⚠ {simbolicas} das {resumo['total']} votações curadas são "
            f"simbólicas e não produzem voto individual. O Score ZIL se apoia "
            f"em {alimentam}, não em {resumo['total']} — é esse o número a citar "
            "na documentação."
        )

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

    if args.verificar_api:
        print("\n── Conferindo na API da Câmara ──")
        observados = Counter()
        problemas_api: list[str] = []
        for entrada in entradas(args.dir):
            observado, problema = verificar_processo_na_api(entrada)
            if observado:
                observados[observado] += 1
            if problema:
                problemas_api.append(problema)
                print(f"  ✗ {problema}")
        todos.extend(problemas_api)
        print(f"  Observado na API: {dict(observados)}")
        if not problemas_api:
            print("  ✓ Todas as entradas batem com a API.")
        if observados.get("simbolica"):
            print(
                f"  → O Score ZIL se apoia em {observados.get('nominal', 0)} "
                f"votação(ões), não em {sum(observados.values())}."
            )

    sys.exit(1 if todos else 0)


if __name__ == "__main__":
    main()
