"""Variante de pipeline e roteamento de lentes — tudo em YAML, nada em código.

`data/explicacao/pipelines/<nome>.yml` diz quais lentes rodam sempre, quais
são condicionais e que tema oficial da Câmara (ou categoria ZIL) liga cada
uma. Mudar o roteamento é PR com diff, pelo mesmo motivo que as instruções dos
agentes: quem controla o roteamento controla quais perspectivas o público vê.

`pipeline_versao` é o hash do arquivo. Duas execuções com o mesmo hash são
comparáveis; com hashes diferentes, são abordagens diferentes — e a tabela
`explicacao` guarda as duas lado a lado.
"""

import hashlib
from dataclasses import dataclass
from pathlib import Path

import yaml

PIPELINES_DIR = Path(__file__).parent.parent.parent.parent / "data" / "explicacao" / "pipelines"


@dataclass(frozen=True)
class Pipeline:
    nome: str
    versao: str
    lentes_fixas: tuple[str, ...]
    lentes_condicionais: tuple[str, ...]
    # tema oficial ou categoria ZIL → lente
    roteamento: dict[str, str]
    contraditor: str
    sintetizador: str
    max_reformulacoes: int = 2
    modelo_padrao: str = ""
    origem: str = ""
    # Verificação de alegações (apps/workers/explicacao/verificacao.py).
    # Vazios = a variante não verifica (v1). Os dois andam juntos.
    extrator: str = ""
    verificador: str = ""
    max_alegacoes: int = 12

    @property
    def verifica(self) -> bool:
        return bool(self.verificador)

    @property
    def todas_as_lentes(self) -> tuple[str, ...]:
        return self.lentes_fixas + self.lentes_condicionais


def carregar_pipeline(caminho: Path) -> Pipeline:
    bruto_txt = caminho.read_text(encoding="utf-8")
    bruto = yaml.safe_load(bruto_txt)
    if not isinstance(bruto, dict):
        raise ValueError(f"{caminho.name}: YAML não é um mapeamento")

    for campo in ("nome", "lentes_fixas", "lentes_condicionais", "roteamento", "contraditor", "sintetizador"):
        if campo not in bruto:
            raise ValueError(f"{caminho.name}: campo obrigatório ausente: {campo}")

    condicionais = tuple(bruto["lentes_condicionais"])
    fora = sorted(set(bruto["roteamento"].values()) - set(condicionais))
    if fora:
        raise ValueError(
            f"{caminho.name}: roteamento aponta para lentes que não são condicionais: {fora}"
        )

    if bool(bruto.get("extrator")) != bool(bruto.get("verificador")):
        raise ValueError(f"{caminho.name}: 'extrator' e 'verificador' andam juntos — declare os dois ou nenhum")

    return Pipeline(
        nome=bruto["nome"],
        versao=hashlib.sha256(bruto_txt.encode("utf-8")).hexdigest()[:16],
        lentes_fixas=tuple(bruto["lentes_fixas"]),
        lentes_condicionais=condicionais,
        roteamento=dict(bruto["roteamento"]),
        contraditor=bruto["contraditor"],
        sintetizador=bruto["sintetizador"],
        max_reformulacoes=int(bruto.get("max_reformulacoes", 2)),
        modelo_padrao=bruto.get("modelo_padrao", ""),
        origem=caminho.name,
        extrator=bruto.get("extrator") or "",
        verificador=bruto.get("verificador") or "",
        max_alegacoes=int(bruto.get("max_alegacoes", 12)),
    )


def carregar_pipeline_por_nome(nome: str = "v1", diretorio: Path = PIPELINES_DIR) -> Pipeline:
    return carregar_pipeline(diretorio / f"{nome}.yml")


def rotear(
    temas_oficiais: list[str],
    categorias_zil: list[str],
    pipeline: Pipeline,
) -> tuple[list[str], str]:
    """Decide quais lentes rodam. Devolve (lentes, motivo).

    Sem nenhum tema nem categoria — o caso da PNMCE, que não tinha tema oficial
    — rodam todas: ausência de roteamento não pode virar ausência de análise.
    """
    chaves = list(temas_oficiais) + list(categorias_zil)
    if not chaves:
        return list(pipeline.todas_as_lentes), "sem tema oficial nem categoria ZIL → todas as lentes"

    ligadas: list[str] = []
    for chave in chaves:
        lente = pipeline.roteamento.get(chave)
        if lente and lente not in ligadas:
            ligadas.append(lente)

    lentes = list(pipeline.lentes_fixas) + [c for c in pipeline.lentes_condicionais if c in ligadas]
    motivo = (
        f"fixas {list(pipeline.lentes_fixas)} + condicionais {ligadas} por {chaves}"
        if ligadas
        else f"fixas {list(pipeline.lentes_fixas)}; nenhuma condicional ligada por {chaves}"
    )
    return lentes, motivo
