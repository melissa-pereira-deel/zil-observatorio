"""Schema da Bússola ZIL — o que a API garante sobre um indicador.

Até aqui o endpoint devolvia o YAML cru, e a página calculava o progresso
como `valor / meta` travado em 100%: para um indicador em que menor é
melhor (dependência de fertilizantes, 87% com meta 60%) a barra aparecia
cheia. O progresso passa a ser calculado aqui, com a direção declarada no
dado, e o que o dado não sabe (origem da meta, link do dataset, validação)
vai explícito para a interface mostrar como está.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field, computed_field

Direcao = Literal["maior_melhor", "menor_melhor"]
Tendencia = Literal["avancando", "retrocedendo", "estavel"]
Validacao = Literal["nao-validado", "revisado"]
NaturezaFonte = Literal["estatal", "autarquia", "associacao_setorial", "academia", "imprensa"]


class MetaOrigem(BaseModel):
    nome: str
    url: Optional[str] = None


class Indicador(BaseModel):
    codigo: str = Field(pattern=r"^BUSSULA-[A-Z]{3}-\d{2}$")
    nome: str
    categoria: str = Field(pattern=r"^ZIL-[A-Z]{3}$")
    descricao: str = ""
    valor_atual: float
    unidade: str
    direcao: Direcao
    # Declarada pelo maintainer enquanto não há histórico para calcular.
    tendencia: Tendencia
    meta: Optional[float] = None
    prazo: Optional[int] = None
    meta_origem: Optional[MetaOrigem] = None
    fonte: str
    natureza_fonte: NaturezaFonte
    fonte_url: str
    fonte_dataset: Optional[str] = None
    ultima_atualizacao: str = Field(pattern=r"^\d{4}-\d{2}$")
    validacao: Validacao = "nao-validado"
    governo_referencia: Optional[str] = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def progresso_pct(self) -> Optional[int]:
        """Quanto do caminho até a meta já foi percorrido, de 0 a 100.

        Sem valor de base no dado, é uma aproximação: para "maior é melhor",
        valor/meta; para "menor é melhor", meta/valor. Ultrapassar a meta
        dá 100. Sem meta, não há progresso a mostrar.
        """
        if self.meta is None or self.meta <= 0 or self.valor_atual <= 0:
            return None
        if self.direcao == "maior_melhor":
            razao = self.valor_atual / self.meta
        else:
            razao = self.meta / self.valor_atual
        return max(0, min(100, round(razao * 100)))

    @computed_field  # type: ignore[prop-decorator]
    @property
    def meta_atingida(self) -> bool:
        if self.meta is None:
            return False
        return self.valor_atual >= self.meta if self.direcao == "maior_melhor" else self.valor_atual <= self.meta

    @computed_field  # type: ignore[prop-decorator]
    @property
    def meta_provisoria(self) -> bool:
        """Meta sem documento de origem: escolhida pelo projeto, não por plano oficial."""
        return self.meta is not None and self.meta_origem is None
