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


class Base(BaseModel):
    """Ponto de partida do caminho até a meta: o valor e o ano em que foi medido."""

    valor: float
    ano: int


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
    # Sem base não há caminho percorrido a mostrar, só a distância até a meta.
    base: Optional[Base] = None
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
        """Quanto do caminho da base até a meta já foi percorrido, de 0 a 100.

        Só existe com base declarada: `(atual − base) / (meta − base)`, que
        vale nos dois sentidos porque o sinal cancela. Sem base, nenhuma
        razão é honesta — `valor/meta` trata zero como ponto de partida, e
        para fertilizantes (87% com meta 60%) a primeira versão mostrava a
        barra cheia; `meta/valor` dava 69% e ainda sugeria avanço. Nesse caso
        devolve None e a interface mostra só a distância. Retrocesso abaixo
        da base dá 0; ultrapassar a meta dá 100.
        """
        if self.meta is None or self.base is None or self.meta == self.base.valor:
            return None
        razao = (self.valor_atual - self.base.valor) / (self.meta - self.base.valor)
        return max(0, min(100, round(razao * 100)))

    @computed_field  # type: ignore[prop-decorator]
    @property
    def distancia_meta(self) -> Optional[float]:
        """Quanto falta, em unidades do indicador (positivo = ainda não chegou)."""
        if self.meta is None:
            return None
        d = self.meta - self.valor_atual if self.direcao == "maior_melhor" else self.valor_atual - self.meta
        return round(max(0.0, d), 2)

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
