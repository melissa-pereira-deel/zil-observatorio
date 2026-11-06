"""Snapshots das tabelas de código da Câmara e do Senado, e o diff entre eles.

Sem rede e sem banco: `scripts/atualizar_referencias_tramitacao.py` baixa as respostas e grava o
que `planejar` decidiu. O plano é montado inteiro em memória porque uma atualização é tudo ou nada:
snapshot novo com YAML antigo faria a CI acusar uma divergência que ninguém pediu.

A chave é sempre o código. Há códigos diferentes com a mesma descrição (905 e 1382 na Câmara), e o
texto gravado fica como a fonte mandou (há espaço sobrando, ex.: 901); só a comparação usa `strip()`.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Iterator, Optional

import yaml

TABELAS: dict[str, tuple[str, str]] = {  # nome do arquivo → (url, campo do código)
    "camara-situacoes.json": ("https://dadosabertos.camara.leg.br/api/v2/referencias/proposicoes/codSituacao", "cod"),
    "camara-tipos-tramitacao.json": ("https://dadosabertos.camara.leg.br/api/v2/referencias/proposicoes/codTipoTramitacao", "cod"),
    "camara-tipos-orgao.json": ("https://dadosabertos.camara.leg.br/api/v2/referencias/orgaos/codTipoOrgao", "cod"),
    "senado-tipos-situacao.json": ("https://legis.senado.leg.br/dadosabertos/processo/tipos-situacao", "sigla"),
}

SUBDIRETORIO = "referencias"

FASES = "fases.yml"
MARCOS = "marcos.yml"
GLOSSARIO = "glossario.yml"
NAO_MAPEADOS = "nao_mapeados.yml"
YAMLS = (FASES, MARCOS, GLOSSARIO, NAO_MAPEADOS)

# Tipo de órgão não tem seção: o snapshot só serve para conferir os códigos da R7, e o esquema de
# `nao_mapeados.yml` recusa campo extra.
SECAO_NAO_MAPEADOS = {
    "camara-situacoes.json": "situacoes_camara",
    "camara-tipos-tramitacao.json": "tramitacao_camara",
    "senado-tipos-situacao.json": "situacoes_senado",
}
SECOES_DE_SITUACAO = {"situacoes_camara": "camara", "situacoes_senado": "senado"}
TIPOS_ORGAO = "camara-tipos-orgao.json"

CABECALHO_NAO_MAPEADOS = (
    "# data/tramitacao/nao_mapeados.yml — códigos sem tratamento (viram nao_sabemos ou \"não é marco\").\n"
    "# Reescrito por scripts/atualizar_referencias_tramitacao.py. Pode ser editado à mão para REMOVER\n"
    "# um código ao mapeá-lo em fases.yml ou marcos.yml.\n"
)


class ReferenciaInvalida(ValueError):
    """A fonte ou um arquivo local não tem o formato esperado; nada é gravado."""


class SubstituicaoInesperada(ValueError):
    """A troca textual de um renomeado não bateu com o que os YAMLs dizem; nada é gravado."""


@dataclass(frozen=True)
class Diferenca:
    novos: tuple[dict, ...]
    removidos: tuple[dict, ...]
    renomeados: tuple[tuple[str, str, str], ...]  # (cod, nome antigo, nome novo), comparados com strip()
    # Códigos com outro campo diferente (data_fim do Senado, espaço sobrando no nome). Não pedem
    # mapeamento, mas contam: sem isso, --verificar diria "em dia" sobre um snapshot que a gravação mudaria.
    alterados: tuple[str, ...] = ()

    @property
    def vazia(self) -> bool:
        return not (self.novos or self.removidos or self.renomeados or self.alterados)


@dataclass(frozen=True)
class ResultadoTabela:
    arquivo: str
    total: int
    linha_de_base: bool
    mudou: bool
    diferenca: Diferenca


@dataclass
class Plano:
    tabelas: list[ResultadoTabela] = field(default_factory=list)
    gravacoes: dict[str, str] = field(default_factory=dict)  # caminho relativo a --dir → conteúdo
    entradas_afetadas: list[str] = field(default_factory=list)  # "<arquivo>/<chave>"
    decisoes_humanas: list[str] = field(default_factory=list)
    problemas: list[str] = field(default_factory=list)  # com qualquer um, nada é gravado

    @property
    def mudou(self) -> bool:
        return any(t.mudou for t in self.tabelas)

    @property
    def fonte_vazia(self) -> bool:
        return any(t.total == 0 for t in self.tabelas)


def extrair_lista(arquivo: str, corpo: object) -> list[dict]:
    """Câmara embrulha em `{"dados": […]}`; o Senado devolve a lista direto."""
    lista = corpo.get("dados") if isinstance(corpo, dict) else corpo
    if not isinstance(lista, list):
        raise ReferenciaInvalida(f"{arquivo}: a fonte não devolveu uma lista")
    return lista


def normalizar_itens(arquivo: str, dados: list[dict]) -> list[dict]:
    """Câmara: cod, nome, sigla, descricao. Senado: cod (= sigla), id, nome (= descricao), data_inicio, data_fim."""
    do_senado = TABELAS[arquivo][1] == "sigla"
    try:
        if do_senado:
            itens = [
                {
                    "cod": d["sigla"],
                    "id": d["id"],
                    "nome": d["descricao"],
                    "data_inicio": d["dataInicio"],
                    "data_fim": d["dataFim"],
                }
                for d in dados
            ]
            itens.sort(key=lambda i: i["cod"])
        else:
            itens = [
                {"cod": str(d["cod"]), "nome": d["nome"], "sigla": d["sigla"], "descricao": d["descricao"]}
                for d in dados
            ]
            itens.sort(key=lambda i: int(i["cod"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise ReferenciaInvalida(f"{arquivo}: item fora do formato ({exc!r})") from exc

    codigos = [i["cod"] for i in itens]
    if any(not isinstance(c, str) or not c.strip() for c in codigos):
        raise ReferenciaInvalida(f"{arquivo}: item sem código na fonte")
    if len(codigos) != len(set(codigos)):
        raise ReferenciaInvalida(f"{arquivo}: código repetido na fonte")
    if any(not isinstance(i["nome"], str) or not i["nome"].strip() for i in itens):
        raise ReferenciaInvalida(f"{arquivo}: item sem nome na fonte")
    return itens


def carregar_snapshot(diretorio: Path, arquivo: str) -> dict:
    """`diretorio` é o de `--dir` (`data/tramitacao`), o pai de `referencias/`."""
    return json.loads((Path(diretorio) / SUBDIRETORIO / arquivo).read_text(encoding="utf-8"))


def montar_snapshot(arquivo: str, itens: list[dict], hoje: date) -> dict:
    url = TABELAS[arquivo][0]
    return {
        "tabela": f"{arquivo.split('-')[0]}.{url.rsplit('/', 1)[-1]}",
        "fonte": url,
        "obtido_em": hoje.isoformat(),
        "total": len(itens),
        "itens": itens,
    }


def serializar(snapshot: dict) -> str:
    return json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n"


def diferenca(antigo: list[dict], novo: list[dict]) -> Diferenca:
    por_cod_antigo = {i["cod"]: i for i in antigo}
    por_cod_novo = {i["cod"]: i for i in novo}
    renomeados: list[tuple[str, str, str]] = []
    alterados: list[str] = []
    for item in novo:
        anterior = por_cod_antigo.get(item["cod"])
        if anterior is None or anterior == item:
            continue
        if anterior["nome"].strip() != item["nome"].strip():
            renomeados.append((item["cod"], anterior["nome"], item["nome"]))
        else:
            alterados.append(item["cod"])
    return Diferenca(
        novos=tuple(i for i in novo if i["cod"] not in por_cod_antigo),
        removidos=tuple(i for i in antigo if i["cod"] not in por_cod_novo),
        renomeados=tuple(renomeados),
        alterados=tuple(alterados),
    )


def motivo_recusa(arquivo: str, anterior: Optional[int], novo: int, aceitar_remocoes: bool) -> Optional[str]:
    """Remoção em massa pode ser real e a flag a libera; tabela vazia nunca é, só falha da fonte."""
    if novo == 0:
        return f"{arquivo}: a fonte devolveu 0 itens; gravação recusada"
    if anterior is not None and (anterior - novo) * 10 > anterior and not aceitar_remocoes:
        return (
            f"{arquivo}: de {anterior} para {novo} itens, mais de 10% a menos; "
            "gravação recusada sem --aceitar-remocoes"
        )
    return None


def _escalar_yaml(valor: str) -> str:
    """Forma do texto no YAML; só vai sem aspas se também for seguro dentro de `{cod: …, …}`."""
    simples = valor[:1].isalpha() and not set(valor) & set(":#,[]{}\"'")
    if simples and yaml.safe_load(valor) == valor:  # "Sim" e "Null" viram bool e nulo sem aspas
        return valor
    return json.dumps(valor, ensure_ascii=False)


def substituir_descricao(texto: str, antigo: str, novo: str, esperado: int) -> str:
    """Troca `descricao_oficial: <antigo>` no texto, sem reescrever o YAML: os comentários ficam.

    Só o campo: `termo` e `texto` do glossário podem conter a mesma string e não são cópia do
    snapshot. A contagem é o que protege códigos diferentes com a mesma descrição: se a string
    aparece mais vezes do que as entradas do código renomeado, a troca levaria outro código junto.
    """
    antigo, novo = antigo.strip(), novo.strip()
    formas = (json.dumps(antigo, ensure_ascii=False), "'" + antigo.replace("'", "''") + "'", antigo)
    padrao = re.compile(
        r"(?<![\w-])(descricao_oficial:[ \t]*)(?:" + "|".join(re.escape(f) for f in formas) + r")"
        r"(?=[ \t]*(?:,|\}|\r?$)|[ \t]+#)",
        re.MULTILINE,
    )
    resultado, encontrados = padrao.subn(lambda m: m.group(1) + _escalar_yaml(novo), texto)
    if encontrados != esperado:
        raise SubstituicaoInesperada(
            f'"{antigo}" aparece {encontrados} vez(es) em descricao_oficial; esperado {esperado}'
        )
    return resultado


def _carregar_yaml(nome: str, texto: str) -> dict:
    try:
        dados = yaml.safe_load(texto)
    except yaml.YAMLError as exc:
        raise ReferenciaInvalida(f"{nome}: YAML inválido ({exc})") from exc
    if dados is None:
        return {}
    if not isinstance(dados, dict):
        raise ReferenciaInvalida(f"{nome}: o topo do arquivo não é um mapeamento")
    return dados


def _dicts(valor: object) -> list[dict]:
    return [v for v in valor if isinstance(v, dict)] if isinstance(valor, list) else []


def _do_codigo(entrada: dict, cod: str) -> bool:
    return str(entrada.get("cod")) == cod


def _entradas_do_codigo(nome: str, dados: dict, arquivo: str, cod: str) -> Iterator[tuple[str, dict]]:
    """Entradas de um YAML que tratam este código desta tabela, como (chave, entrada)."""
    if arquivo == TIPOS_ORGAO:
        # Tipo de órgão não tem entrada própria: quem o usa são os parâmetros da regra (R7).
        if nome == FASES:
            for regra in _dicts(dados.get("regras")):
                parametros = regra.get("parametros")
                usados = parametros.get("tipos_orgao_comissao") if isinstance(parametros, dict) else None
                if isinstance(usados, list) and cod in map(str, usados):
                    yield f"regra_{regra.get('id')}", regra
        return
    secao = SECAO_NAO_MAPEADOS[arquivo]
    if nome == NAO_MAPEADOS:
        for entrada in _dicts(dados.get(secao)):
            if _do_codigo(entrada, cod):
                yield f"{secao}/{cod}", entrada
    elif nome == MARCOS and secao == "tramitacao_camara":
        for entrada in _dicts(dados.get("marcos")):
            if _do_codigo(entrada, cod) and entrada.get("casa", "camara") == "camara":
                yield cod, entrada
        for entrada in _dicts(dados.get("ignorados")):
            if _do_codigo(entrada, cod) and entrada.get("casa", "camara") == "camara":
                yield f"ignorados/{cod}", entrada
    elif nome == FASES and secao in SECOES_DE_SITUACAO:
        for regra in _dicts(dados.get("regras")):
            for entrada in _dicts(regra.get(secao)):
                if _do_codigo(entrada, cod):
                    yield f"regra_{regra.get('id')}", entrada
    elif nome == GLOSSARIO and secao in SECOES_DE_SITUACAO:
        casa = SECOES_DE_SITUACAO[secao]
        for entrada in _dicts(dados.get("entradas")):
            if any(_do_codigo(c, cod) and c.get("casa") == casa for c in _dicts(entrada.get("codigos"))):
                yield str(entrada.get("chave")), entrada


def _codigos_que_ficam(entrada: dict, novo: str, renomeados: list[tuple[str, str, str, str]]) -> list[str]:
    """Códigos de uma entrada de glossário que não passam, nesta execução, ao texto `novo`."""
    grupo = {
        (SECOES_DE_SITUACAO[SECAO_NAO_MAPEADOS[arquivo]], cod)
        for arquivo, cod, _, texto_novo in renomeados
        if SECAO_NAO_MAPEADOS.get(arquivo) in SECOES_DE_SITUACAO and texto_novo.strip() == novo
    }
    return [
        str(c.get("cod"))
        for c in _dicts(entrada.get("codigos"))
        if (c.get("casa"), str(c.get("cod"))) not in grupo
    ]


def _renomear_no_yaml(
    nome: str, texto: str, dados: dict, renomeados: list[tuple[str, str, str, str]]
) -> str:
    """Aplica os renomeados `(arquivo, cod, antigo, novo)` a um YAML; `dados` sai atualizado."""
    # Agrupa pelo texto antigo: dois códigos iguais renomeados juntos são uma troca só, com a soma
    # das entradas como contagem esperada.
    trocas: dict[str, tuple[str, dict[int, dict]]] = {}
    for arquivo, cod, antigo, novo in renomeados:
        antigo, novo = antigo.strip(), novo.strip()
        for chave, entrada in _entradas_do_codigo(nome, dados, arquivo, cod):
            atual = entrada.get("descricao_oficial")
            if atual is None:
                continue
            atual = str(atual).strip()
            # Vem antes de "já ajustado": a entrada tem uma descrição só e não pode valer para os dois
            # textos, mesmo que alguém já a tenha trocado à mão. A saída é separar a entrada.
            ficam = _codigos_que_ficam(entrada, novo, renomeados) if nome == GLOSSARIO else []
            if ficam:
                raise SubstituicaoInesperada(
                    f'glossario/{chave} cobre também {", ".join(ficam)}, que não passa a "{novo}" '
                    f"como o código {cod}; separe a entrada, porque ela só tem uma descricao_oficial"
                )
            if atual == novo:  # já ajustado à mão, a saída de um aborto anterior
                continue
            if atual != antigo:
                raise SubstituicaoInesperada(
                    f'{chave} (código {cod}) diz "{atual}"; o snapshot anterior dizia "{antigo}"'
                )
            novo_do_grupo, entradas = trocas.setdefault(antigo, (novo, {}))
            if novo_do_grupo != novo:
                raise SubstituicaoInesperada(
                    f'"{antigo}" foi renomeado para textos diferentes ("{novo_do_grupo}" e "{novo}")'
                )
            entradas[id(entrada)] = entrada

    if not trocas:
        return texto
    for antigo, (novo, entradas) in trocas.items():
        texto = substituir_descricao(texto, antigo, novo, len(entradas))
        for entrada in entradas.values():
            entrada["descricao_oficial"] = novo
    try:
        confere = yaml.safe_load(texto) == dados
    except yaml.YAMLError:
        confere = False
    if not confere:
        raise SubstituicaoInesperada("a troca mudou mais do que as descrições esperadas")
    return texto


def _ordem_do_codigo(secao: str, cod: object) -> object:
    return str(cod) if secao == "situacoes_senado" else int(str(cod))


def acrescentar_nao_mapeados(dados: Optional[dict], novos: list[tuple[str, dict]], hoje: date) -> str:
    """Devolve o `nao_mapeados.yml` inteiro com `novos` = `(arquivo, item)`, cada seção em ordem de código.

    Reescrever perde comentários, por isso o cabeçalho é fixo e o arquivo é só mantido por script.
    """
    if dados is None:
        dados = {"versao_esquema": 1, "situacoes_camara": [], "situacoes_senado": [], "tramitacao_camara": []}
    for secao in SECAO_NAO_MAPEADOS.values():
        if not isinstance(dados.get(secao), list):
            raise ReferenciaInvalida(f"{NAO_MAPEADOS}: falta a lista {secao}")
    for arquivo, item in novos:
        dados[SECAO_NAO_MAPEADOS[arquivo]].append(
            {
                "cod": item["cod"],
                "descricao_oficial": item["nome"].strip(),
                "motivo": f"codigo_novo_{hoje.isoformat()}",
            }
        )
    try:
        for secao in SECAO_NAO_MAPEADOS.values():
            dados[secao].sort(key=lambda e, s=secao: _ordem_do_codigo(s, e.get("cod")))
    except (AttributeError, ValueError) as exc:
        raise ReferenciaInvalida(f"{NAO_MAPEADOS}: código fora do formato ({exc!r})") from exc
    # `width` grande: uma descrição dobrada em duas linhas a próxima substituição textual não acharia.
    corpo = yaml.safe_dump(dados, allow_unicode=True, sort_keys=False, default_flow_style=False, width=2**16)
    return CABECALHO_NAO_MAPEADOS + corpo


def _planejar_yamls(diretorio: Path, plano: Plano, hoje: date) -> None:
    com_diferenca = [
        t for t in plano.tabelas if t.diferenca.novos or t.diferenca.removidos or t.diferenca.renomeados
    ]
    if not com_diferenca:
        return

    textos: dict[str, str] = {}
    dados: dict[str, dict] = {}
    for nome in YAMLS:
        caminho = Path(diretorio) / nome
        if not caminho.exists():
            continue
        texto = caminho.read_bytes().decode("utf-8")
        try:
            dados[nome] = _carregar_yaml(nome, texto)
            textos[nome] = texto
        except ReferenciaInvalida as exc:
            plano.problemas.append(str(exc))

    def afetadas(arquivo: str, cod: str, nomes: tuple[str, ...] = YAMLS) -> list[str]:
        return [
            f"{Path(nome).stem}/{chave}"
            for nome in nomes
            if nome in dados
            for chave, _ in _entradas_do_codigo(nome, dados[nome], arquivo, cod)
        ]

    renomeados = [(t.arquivo, *r) for t in com_diferenca for r in t.diferenca.renomeados]
    for arquivo, cod, antigo, _ in renomeados:
        plano.entradas_afetadas.extend(afetadas(arquivo, cod))
        for _, entrada in _entradas_do_codigo(GLOSSARIO, dados.get(GLOSSARIO, {}), arquivo, cod):
            plano.decisoes_humanas.append(
                f"glossario/{entrada.get('chave')}: conferir `termo` e `codigos` à mão; "
                f'o código {cod} deixou de ser "{antigo.strip()}" e só descricao_oficial é trocada'
            )
    if renomeados:
        for nome in textos:
            try:
                novo_texto = _renomear_no_yaml(nome, textos[nome], dados[nome], renomeados)
            except SubstituicaoInesperada as exc:
                plano.problemas.append(f"{nome}: a troca de descrição não pode ser feita")
                plano.decisoes_humanas.append(f"{nome}: {exc}. Ajuste à mão e rode de novo")
                continue
            if novo_texto != textos[nome]:
                plano.gravacoes[nome] = novo_texto

    pendentes: list[tuple[str, dict]] = []
    for tabela in com_diferenca:
        arquivo = tabela.arquivo
        for item in tabela.diferenca.removidos:
            cod = item["cod"]
            entradas = afetadas(arquivo, cod)
            plano.entradas_afetadas.extend(entradas)
            plano.decisoes_humanas.append(
                f'{arquivo}: código {cod} ("{item["nome"].strip()}") saiu da fonte; '
                f"entradas: {', '.join(entradas) or 'nenhuma'}. O mapeamento não foi alterado"
            )
        for item in tabela.diferenca.novos:
            cod = item["cod"]
            if arquivo not in SECAO_NAO_MAPEADOS:
                plano.decisoes_humanas.append(
                    f'{arquivo}: código novo {cod} ("{item["nome"].strip()}"), '
                    f"sem seção em {NAO_MAPEADOS}; conferir se entra na R7"
                )
                continue
            donos = afetadas(arquivo, cod, (FASES, MARCOS, NAO_MAPEADOS))
            if donos:
                plano.entradas_afetadas.extend(donos)
                plano.decisoes_humanas.append(
                    f"{arquivo}: código {cod} voltou à fonte e já tem entrada ({', '.join(donos)}); conferir"
                )
                continue
            pendentes.append((arquivo, item))
            plano.entradas_afetadas.append(f"nao_mapeados/{SECAO_NAO_MAPEADOS[arquivo]}/{cod}")

    if pendentes:
        try:
            plano.gravacoes[NAO_MAPEADOS] = acrescentar_nao_mapeados(dados.get(NAO_MAPEADOS), pendentes, hoje)
        except ReferenciaInvalida as exc:
            plano.problemas.append(str(exc))


def planejar(diretorio: Path, corpos: dict[str, object], hoje: date, aceitar_remocoes: bool = False) -> Plano:
    """Decide o que gravar a partir das respostas da fonte, sem escrever nada.

    Tabela sem snapshot anterior é linha de base: não há com o que comparar, então nenhum código
    dela é "novo". Sem isso, a carga inicial poria as tabelas inteiras em `nao_mapeados.yml`.
    """
    plano = Plano()
    for arquivo in TABELAS:
        itens = normalizar_itens(arquivo, extrair_lista(arquivo, corpos[arquivo]))
        try:
            anteriores = carregar_snapshot(diretorio, arquivo)["itens"]
        except FileNotFoundError:
            anteriores = None
        except (KeyError, TypeError, ValueError) as exc:
            raise ReferenciaInvalida(f"{arquivo}: snapshot local ilegível ({exc!r})") from exc

        mudou = anteriores != itens
        plano.tabelas.append(
            ResultadoTabela(
                arquivo=arquivo,
                total=len(itens),
                linha_de_base=anteriores is None,
                mudou=mudou,
                diferenca=diferenca(anteriores if anteriores is not None else itens, itens),
            )
        )
        if mudou:
            recusa = motivo_recusa(arquivo, None if anteriores is None else len(anteriores), len(itens), aceitar_remocoes)
            if recusa:
                plano.problemas.append(recusa)
            plano.gravacoes[f"{SUBDIRETORIO}/{arquivo}"] = serializar(montar_snapshot(arquivo, itens, hoje))
    _planejar_yamls(diretorio, plano, hoje)
    return plano
