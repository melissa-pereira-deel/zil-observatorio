#!/usr/bin/env python3
"""Mede o efeito de vocabulário novo na REDE de descoberta do ZIL Observatório.

POR QUE ESTE SCRIPT EXISTE

`scripts/candidatas.py:303-305` faz `if not evidencia: continue`: votação que não
casa keyword ZIL nunca entra na lista de candidatas. Logo a taxonomia não é só
rótulo — é a rede. Para o RFC do destino das categorias, a pergunta empírica é:
vocabulário novo pesca matéria real que a rede de hoje não vê, e a que custo em
falso positivo?

COMO ELE NÃO MENTE

1. **Coleta separada da classificação.** `--coletar` chama a API uma vez por ano
   e grava o corpus cru em JSONL. Toda medição depois roda offline sobre o MESMO
   corpus — então a diferença entre duas taxonomias é só a taxonomia.
2. **Linha de base conferida antes de qualquer medição.** `--baseline` classifica
   o corpus com a taxonomia do repositório, inalterada, e tem de reproduzir as
   varreduras já guardadas em `candidatas/{ano}.txt`. Se não reproduzir, o
   harness está errado e todo número que ele produzir depois também está.
3. **Reusa o motor de verdade.** O escore, as flags e a regra de casamento fraco
   vêm de `scripts/candidatas.py` e de `apps/workers/classifiers` por import. O
   script não reimplementa nenhuma delas.

NADA é escrito em `data/` nem em `apps/`. A taxonomia aumentada é um arquivo
temporário no scratchpad.
"""

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Optional

import yaml

# Este arquivo mora em docs/decisions/005-rfc-destino-das-categorias/, logo a
# raiz do repositório são três níveis acima. Derivado de __file__ de propósito:
# a primeira versão trazia um caminho absoluto do container onde a medição foi
# feita, e não rodava em nenhuma outra máquina.
REPO = Path(__file__).resolve().parents[3]
AQUI = Path(__file__).parent
CORPUS = AQUI / "corpus"

for _p in (str(REPO), str(REPO / "apps" / "api")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import apps.workers.classifiers as C  # noqa: E402

sys.path.insert(0, str(REPO / "scripts"))
import candidatas as K  # noqa: E402

from packages.camara_client import CamaraClient  # noqa: E402

# ─────────────────────────────────────────────────────────────────────────────
# Vocabulários candidatos
#
# `keywords_fracas` aqui segue o mesmo princípio do repositório: termo que, só,
# não sustenta a categoria. Declarar isso de saída é parte da hipótese — um
# vocabulário que só funciona sem freio de polissemia não é um vocabulário bom.
# ─────────────────────────────────────────────────────────────────────────────

VOCABULARIOS = {
    "saude": {
        "codigo": "ZIL-SAU",
        "nome": "Complexo Industrial da Saúde",
        "keywords": [
            "insumo farmacêutico", "insumos farmacêuticos", "IFA",
            "farmoquímico", "farmoquímica", "vacina", "vacinas",
            "medicamento", "medicamentos", "complexo industrial da saúde",
            "equipamento médico-hospitalar", "material médico-hospitalar",
            "Farmanguinhos", "Butantan", "Fiocruz", "Hemobrás",
            "produção nacional de medicamentos", "genérico",
        ],
        # `medicamento` e `genérico` são os suspeitos: aparecem em matéria de
        # preço, de SUS e de registro sanitário, que não são política industrial.
        "keywords_fracas": ["medicamento", "medicamentos", "genérico", "vacina", "vacinas"],
    },
    "instrumentos": {
        "codigo": "ZIL-INS",
        "nome": "Instrumentos de Política Industrial",
        "keywords": [
            "depreciação acelerada", "crédito à exportação", "BNDES", "FINEP",
            "compras públicas", "margem de preferência", "desoneração",
            "poder de compra do Estado", "política industrial",
            "conteúdo local", "encomenda tecnológica", "fundo garantidor",
        ],
        # Vocabulário de instrumento é genérico por natureza: `desoneração` e
        # `compras públicas` aparecem em qualquer matéria fiscal ou de licitação.
        "keywords_fracas": ["desoneração", "compras públicas", "BNDES", "fundo garantidor"],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Coleta
# ─────────────────────────────────────────────────────────────────────────────

def coletar(ano: int) -> Path:
    """Varre o ano na API e grava o corpus cru. Uma chamada por votação nominal."""
    CORPUS.mkdir(parents=True, exist_ok=True)
    saida = CORPUS / f"{ano}.jsonl"

    with CamaraClient() as client:
        try:
            votacoes = client.listar_votacoes(ano)
        except Exception as e:  # noqa: BLE001
            raise SystemExit(
                f"✗ A API da Câmara falhou ao listar {ano}: {type(e).__name__}. "
                "São ~100 páginas; tente de novo em alguns minutos."
            ) from e
        print(f"  {ano}: {len(votacoes)} votações no ano", flush=True)

        nominais = []
        for v in votacoes:
            fonte_id = str(getattr(v, "fonte_id", "") or getattr(v, "id", ""))
            descricao = getattr(v, "descricao", "") or ""
            if not fonte_id:
                continue
            sim, nao = K.extrair_placar(descricao)
            if sim is None:
                continue
            nominais.append((fonte_id, descricao, str(getattr(v, "data", "") or ""), sim, nao))

        print(f"  {ano}: {len(nominais)} com voto nominal — buscando ementas", flush=True)

        registros = []
        for i, (fonte_id, descricao, data, sim, nao) in enumerate(nominais, start=1):
            if i % 25 == 0:
                print(f"    {i}/{len(nominais)}...", flush=True)
            try:
                detalhes = client.obter_votacao_detalhes(fonte_id)
            except Exception:  # noqa: BLE001 — uma falha não derruba a varredura
                continue
            if not isinstance(detalhes, dict):
                continue
            prop = detalhes.get("proposicaoPrincipal")
            if not prop:
                afetadas = detalhes.get("proposicoesAfetadas") or []
                prop = afetadas[0] if afetadas else None
            registros.append({
                "fonte_id": fonte_id,
                "descricao_votacao": descricao,
                "data": data,
                "sim": sim,
                "nao": nao,
                "ementa": (prop or {}).get("ementa") or (prop or {}).get("titulo") or "",
                "proposicao": (
                    f"{(prop or {}).get('siglaTipo', '')} "
                    f"{(prop or {}).get('numero', '')}/{(prop or {}).get('ano', '')}"
                ).strip(),
            })

    saida.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in registros) + "\n",
        encoding="utf-8",
    )
    print(f"  {ano}: {len(registros)} registros → {saida}", flush=True)
    return saida


def carregar(ano: int) -> list[dict]:
    arq = CORPUS / f"{ano}.jsonl"
    if not arq.exists():
        raise SystemExit(
            f"✗ Corpus de {ano} não coletado. Rode primeiro:\n"
            f"    python3 {Path(__file__).name} --coletar --ano {ano}"
        )
    return [
        json.loads(linha)
        for linha in arq.read_text(encoding="utf-8").splitlines()
        if linha.strip()
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Troca de taxonomia em memória
# ─────────────────────────────────────────────────────────────────────────────

def aplicar_taxonomia(categorias: list[dict]) -> None:
    """Reconstrói os patterns do classificador como `__init__.py:66-92` faz.

    O módulo monta `_patterns_com_keyword`, `_patterns` e `KEYWORDS_FRACAS` em
    código de topo, não numa função — então não há builder para chamar. Isto
    replica esse bloco; se ele mudar no repositório, a validação de linha de base
    (`--baseline`) é o que acusa a divergência.
    """
    C._taxonomia = categorias
    C._patterns_com_keyword = {
        cat["codigo"]: [
            (kw, re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE))
            for kw in cat.get("keywords", [])
        ]
        for cat in categorias
    }
    C._patterns = {
        codigo: [p for _kw, p in pares]
        for codigo, pares in C._patterns_com_keyword.items()
    }
    fracas = {
        cat["codigo"]: frozenset(k.lower() for k in (cat.get("keywords_fracas") or []))
        for cat in categorias
    }
    C.KEYWORDS_FRACAS = fracas
    # `candidatas.py` importou KEYWORDS_FRACAS por valor e tem o seu próprio
    # `_e_fraca` — sem esta linha, o filtro de casamento fraco usaria a
    # taxonomia antiga e o resultado seria silenciosamente errado.
    K.KEYWORDS_FRACAS = fracas


def taxonomia_do_repo() -> list[dict]:
    dados = yaml.safe_load((REPO / "data" / "taxonomia" / "categorias.yml").read_text(encoding="utf-8"))
    return dados["categorias"]


def taxonomia_aumentada(vocab: str) -> list[dict]:
    base = taxonomia_do_repo()
    nova = VOCABULARIOS[vocab]
    return base + [{
        "codigo": nova["codigo"],
        "nome": nova["nome"],
        "keywords": nova["keywords"],
        "keywords_fracas": nova["keywords_fracas"],
    }]


# ─────────────────────────────────────────────────────────────────────────────
# Classificação do corpus — reusa Candidata e escore de candidatas.py
# ─────────────────────────────────────────────────────────────────────────────

def classificar(registros: list[dict], excluir: set[str]) -> list[K.Candidata]:
    out: list[K.Candidata] = []
    for r in registros:
        if r["fonte_id"] in excluir:
            continue
        texto = f"{r['ementa']} {r['descricao_votacao']}"
        evidencia = C.classificar_texto_com_evidencia(texto)
        if not evidencia:
            continue
        substantivas = {
            kw
            for kws in C.classificar_texto_com_evidencia(
                C.sem_citacoes_de_lei(texto)
            ).values()
            for kw in kws
        }
        out.append(K.Candidata(
            fonte_id=r["fonte_id"],
            descricao=(r["ementa"] or r["descricao_votacao"]),
            data=r["data"],
            categorias=list(evidencia),
            votos_sim=r["sim"],
            votos_nao=r["nao"],
            descricao_votacao=r["descricao_votacao"],
            keywords=evidencia,
            keywords_substantivas=substantivas,
        ))
    return sorted(out, key=lambda c: c.escore, reverse=True)


# ─────────────────────────────────────────────────────────────────────────────
# Regressão: as afirmações de "isto NÃO classifica" que a suíte guarda
#
# `tests/unit/test_classifier.py` codifica, em asserts `== []`, cada falso
# positivo que o projeto já pagou para descobrir — "pesquisa clínica com seres
# humanos", "Tarifa Social de Água e Esgoto", atletas do Mercosul, a LGPD citada
# dentro de um projeto de homicídio qualificado. Vocabulário novo que reacenda
# qualquer um deles está reintroduzindo um bug conhecido.
#
# Os textos são extraídos do arquivo de teste por AST, não copiados à mão: assim
# não há como a checagem sair de sincronia com a suíte.
# ─────────────────────────────────────────────────────────────────────────────

_CLASSIFICADORES = {"classificar_texto", "classificar_votacao", "classificar_proposicao"}


def _texto_do_call(no: ast.Call) -> Optional[str]:
    for arg in list(no.args) + [k.value for k in no.keywords]:
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            return arg.value
    return None


def expectativas_de_vazio() -> list[tuple[int, str, str]]:
    """Devolve (linha, função, texto) de cada assert `classificar_*(...) == []`.

    A **função** importa: `classificar_texto` aplica a regra de keyword forte e
    devolve `[]` para casamento só-fraco, enquanto
    `classificar_texto_com_evidencia` devolve o casamento cru. Checar com a
    função errada acusa regressão onde não há — foi o que a primeira versão
    desta checagem fez, e o que a validação de linha de base pegou.
    """
    arq = REPO / "tests" / "unit" / "test_classifier.py"
    arvore = ast.parse(arq.read_text(encoding="utf-8"))
    out: list[tuple[int, str, str]] = []

    for fn in ast.walk(arvore):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        # `result = classificar_votacao(...)` seguido de `assert result == []`
        atribuicoes: dict[str, ast.Call] = {}
        for no in ast.walk(fn):
            if isinstance(no, ast.Assign) and isinstance(no.value, ast.Call):
                f = no.value.func
                nome = getattr(f, "id", None) or getattr(f, "attr", None)
                if nome in _CLASSIFICADORES:
                    for alvo in no.targets:
                        if isinstance(alvo, ast.Name):
                            atribuicoes[alvo.id] = no.value

        for no in ast.walk(fn):
            if not (isinstance(no, ast.Compare) and len(no.ops) == 1
                    and isinstance(no.ops[0], ast.Eq)):
                continue
            direita = no.comparators[0]
            if not (isinstance(direita, ast.List) and not direita.elts):
                continue
            esquerda = no.left
            chamada: Optional[ast.Call] = None
            if isinstance(esquerda, ast.Call):
                f = esquerda.func
                nome = getattr(f, "id", None) or getattr(f, "attr", None)
                if nome in _CLASSIFICADORES:
                    chamada = esquerda
            elif isinstance(esquerda, ast.Name):
                chamada = atribuicoes.get(esquerda.id)
            if chamada is None:
                continue
            texto = _texto_do_call(chamada)
            f = chamada.func
            nome = getattr(f, "id", None) or getattr(f, "attr", None)
            if texto:  # `classificar_votacao(None)` não tem texto a checar
                out.append((no.lineno, nome, texto))

    return out


def _chamar(funcao: str, texto: str) -> list[str]:
    """Chama exatamente a função que o assert chama."""
    if funcao == "classificar_proposicao":
        return C.classificar_proposicao(ementa=texto)
    if funcao == "classificar_votacao":
        return C.classificar_votacao(texto)
    return C.classificar_texto(texto)


def modo_regressao(rotulo: str) -> int:
    casos = expectativas_de_vazio()
    print(f"\n--- regressão: {len(casos)} afirmações de \"não classifica\" na suíte "
          f"({rotulo}) ---")
    quebrados = 0
    for linha, funcao, texto in casos:
        cats = _chamar(funcao, texto)
        if cats:
            quebrados += 1
            print(f"  ✗ test_classifier.py:{linha} volta a classificar → {cats}")
            print(f"      {funcao}(\"{texto[:90]}\")")
    if not quebrados:
        print(f"  ✓ nenhuma reacendeu ({len(casos)}/{len(casos)} seguem vazias)")
    return quebrados


def flags(c: K.Candidata) -> str:
    m = []
    if c.rejeitada:
        m.append("REJEITADA")
    if not c.classificavel:
        m.append("indecidível")
    if c.so_casamento_fraco:
        m.append("só casou dentro do nome de uma lei citada"
                 if c.keywords_citadas else "só casou por palavra comum")
    return " · ".join(m) or "—"


# ─────────────────────────────────────────────────────────────────────────────
# Modos
# ─────────────────────────────────────────────────────────────────────────────

def modo_baseline(anos: list[int], excluir: set[str]) -> None:
    aplicar_taxonomia(taxonomia_do_repo())
    print("\n=== LINHA DE BASE — taxonomia do repositório, inalterada ===")
    print("Compare com scratchpad/candidatas/<ano>.txt. Divergência aqui\n"
          "invalida qualquer medição posterior.\n")
    for ano in anos:
        cands = classificar(carregar(ano), excluir)
        print(f"{ano}: {len(cands)} candidata(s)")
        for c in cands:
            print(f"  {c.fonte_id:>14}  escore {c.escore:5.1f}  "
                  f"{c.votos_sim}×{c.votos_nao}  {','.join(c.categorias)}  [{flags(c)}]")
        print()
    modo_regressao("taxonomia do repositório")


def modo_vocab(vocab: str, anos: list[int], excluir: set[str]) -> None:
    nova = VOCABULARIOS[vocab]
    codigo = nova["codigo"]

    aplicar_taxonomia(taxonomia_do_repo())
    antes = {ano: {c.fonte_id for c in classificar(carregar(ano), excluir)} for ano in anos}

    aplicar_taxonomia(taxonomia_aumentada(vocab))
    depois = {ano: classificar(carregar(ano), excluir) for ano in anos}

    print(f"\n=== VOCABULÁRIO `{vocab}` → {codigo} ({nova['nome']}) ===")
    print(f"keywords: {', '.join(nova['keywords'])}")
    print(f"fracas:   {', '.join(nova['keywords_fracas'])}\n")

    tot_novas = tot_fortes = 0
    for ano in anos:
        novas = [c for c in depois[ano] if c.fonte_id not in antes[ano]]
        fortes = [c for c in novas if not c.so_casamento_fraco]
        tot_novas += len(novas)
        tot_fortes += len(fortes)
        print(f"{ano}: {len(antes[ano])} → {len(depois[ano])} candidatas "
              f"({len(novas)} novas, {len(fortes)} por keyword forte)")
        for c in novas:
            marca = "✓" if not c.so_casamento_fraco else "⚠"
            print(f"  {marca} {c.fonte_id:>14} escore {c.escore:5.1f} "
                  f"{c.votos_sim}×{c.votos_nao}  [{flags(c)}]")
            print(f"      casou por: {', '.join(c.keywords_casadas)}")
            print(f"      {c.descricao[:150]}")
        print()

    print(f"TOTAL: {tot_novas} candidatas novas, das quais {tot_fortes} por keyword forte.")
    print("Cada uma precisa de leitura humana: casar keyword forte não prova\n"
          "que a matéria é de soberania industrial — prova que entrou na rede.")

    quebrados = modo_regressao(f"taxonomia + {codigo}")
    if quebrados:
        print(f"\n⚠ {quebrados} falso(s) positivo(s) conhecido(s) reacendido(s) por este\n"
              "  vocabulário. Cada um é um bug que o projeto já pagou para descobrir.")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--coletar", action="store_true", help="varre a API e grava o corpus")
    p.add_argument("--baseline", action="store_true", help="valida o harness contra as varreduras guardadas")
    p.add_argument("--vocab", choices=sorted(VOCABULARIOS), help="mede um vocabulário candidato")
    p.add_argument("--ano", type=int, nargs="+", required=True)
    args = p.parse_args()

    if not (args.coletar or args.baseline or args.vocab):
        raise SystemExit("Escolha --coletar, --baseline ou --vocab.")

    if args.coletar:
        for ano in args.ano:
            coletar(ano)
        return

    # Mesmo filtro do candidatas.py: as já curadas não são candidatas.
    excluir = K.ja_curadas(REPO / "data" / "direcoes")

    if args.baseline:
        modo_baseline(args.ano, excluir)
    if args.vocab:
        modo_vocab(args.vocab, args.ano, excluir)


if __name__ == "__main__":
    main()
