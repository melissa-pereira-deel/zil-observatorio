"""Extração de texto do inteiro teor — estágio plugável.

Medido em 2026-10-21 (RFC-006, C3; experimento S5 na Fase 1): o inteiro teor
da Câmara de 2010 em diante é PDF com camada de texto nativa, e **a
justificação do autor está lá** — "JUSTIFICAÇÃO" aparece na PNMCE, no PL
2583/2020 e no PL 9543/2018, seguida do texto de motivação. O PL 1847/2024
não tem a seção: o inteiro teor dele é o texto final, não a proposição
original. "Sem justificação" é estado válido, não falha.

OCR não entra no caminho principal. Fica um gancho explícito: se a extração
devolver menos de `MIN_CHARS_POR_PAGINA` por página, o resultado é marcado
`insuficiente` e o pipeline segue só com a ementa, declarando a lacuna. Isso é
o acervo pré-2008, fora da janela do projeto.

Refinamento do S5 (mesmo dia): ter ou não justificação depende da ORIGEM e do
ESTÁGIO, não do ano. Oito "PLs de 2025" listados pela API eram projetos de
origem no Senado — o inteiro teor na Câmara é o autógrafo, texto final
aprovado lá, sem justificação. `origem_senado` marca isso para que o leitor
da explicação saiba que a motivação do autor existe, só não está neste
documento.
"""

import io
import re
from dataclasses import dataclass
from typing import Literal, Optional

import httpx

# Abaixo disto por página, o PDF é imagem ou está vazio. Calibrado nos
# cinco PDFs do experimento S5 (1.139 a 2.623 chars/página em texto nativo).
MIN_CHARS_POR_PAGINA = 200

# Cabeçalho da seção de motivação. A forma observada nos PDFs da Câmara é
# "JUSTIFICAÇÃO" (S5: PNMCE, PL 2583/2020, PL 9543/2018). "JUSTIFICATIVA" e
# letras espaçadas ("J U S T I F I C A Ç Ã O") entram por precaução — não
# foram observadas, mas custam nada e um cabeçalho perdido é uma motivação
# que o leitor não vê.
_JUSTIFICACAO = re.compile(
    r"\bJ\s?U\s?S\s?T\s?I\s?F\s?I\s?C\s?A\s?(?:[ÇC]\s?[ÃA]\s?O|T\s?I\s?V\s?A)\b",
    re.IGNORECASE,
)
# Marca de autógrafo do Senado no fim do texto. Quando aparece, o documento é
# o texto final aprovado lá, e a ausência de justificação é esperada.
_AUTOGRAFO_SENADO = re.compile(r"Presidente do Senado Federal|Senado Federal, em", re.IGNORECASE)
# Fim do dispositivo / assinatura: "Sala das Sessões, em ..." costuma fechar
# a justificação; quando aparece antes dela, não é usado.
_SALA = re.compile(r"Sala das Sess[õo]es", re.IGNORECASE)

Metodo = Literal["pdf_nativo", "insuficiente", "nao_pdf", "indisponivel"]


class NaoEhPDF(ValueError):
    pass


@dataclass
class TextoExtraido:
    texto: str
    metodo: Metodo
    paginas: int = 0
    chars_por_pagina: float = 0.0
    # Partes separadas quando identificáveis. `None` = não encontrada, e o
    # pipeline diz isso ao leitor em vez de fingir.
    dispositivo: Optional[str] = None
    justificacao: Optional[str] = None
    # O documento é autógrafo vindo do Senado: texto final, sem justificação.
    origem_senado: bool = False
    erro: Optional[str] = None

    @property
    def utilizavel(self) -> bool:
        return self.metodo == "pdf_nativo" and bool(self.texto.strip())

    @property
    def motivo_sem_justificacao(self) -> Optional[str]:
        """Por que não há justificação — para o leitor, não para o log."""
        if self.justificacao:
            return None
        if self.metodo != "pdf_nativo":
            return f"texto integral não extraído ({self.metodo})"
        if self.origem_senado:
            return "o inteiro teor é o autógrafo do Senado: texto final aprovado lá, sem a justificação do autor"
        return "o inteiro teor não tem seção de justificação — provavelmente é o texto final após emendas, não a proposição original"


def separar_secoes(texto: str) -> tuple[Optional[str], Optional[str]]:
    """Divide o texto em (dispositivo, justificação) pelo cabeçalho padrão.

    Devolve `(texto, None)` quando não há justificação — que é o caso do texto
    final de uma proposição já emendada.
    """
    if not texto or not texto.strip():
        return None, None
    m = _JUSTIFICACAO.search(texto)
    if not m:
        return texto.strip(), None
    dispositivo = texto[: m.start()].strip() or None
    justificacao = texto[m.end():].strip() or None
    return dispositivo, justificacao


def extrair_texto_pdf(raw: bytes) -> TextoExtraido:
    """Extrai texto de um PDF em memória. Não faz OCR; sinaliza quando faria falta."""
    if not raw[:5] == b"%PDF-":
        raise NaoEhPDF(f"conteúdo não é PDF ({len(raw)} bytes; início {raw[:16]!r})")

    import pdfplumber  # import tardio: dependência pesada, só quem extrai paga

    paginas: list[str] = []
    with pdfplumber.open(io.BytesIO(raw)) as pdf:
        for p in pdf.pages:
            paginas.append(p.extract_text() or "")

    texto = "\n".join(paginas)
    n = len(paginas)
    chars = len(re.sub(r"\s+", " ", texto))
    por_pagina = chars / n if n else 0.0

    if por_pagina < MIN_CHARS_POR_PAGINA:
        return TextoExtraido(
            texto=texto, metodo="insuficiente", paginas=n, chars_por_pagina=por_pagina,
            erro=f"{por_pagina:.0f} chars/página — PDF de imagem ou vazio; OCR seria necessário",
        )

    dispositivo, justificacao = separar_secoes(texto)
    origem_senado = bool(_AUTOGRAFO_SENADO.search(texto[-1500:]))
    return TextoExtraido(
        texto=texto, metodo="pdf_nativo", paginas=n, chars_por_pagina=por_pagina,
        dispositivo=dispositivo, justificacao=justificacao, origem_senado=origem_senado,
    )


def baixar_e_extrair(url: str, client: Optional[httpx.Client] = None) -> TextoExtraido:
    """Baixa `urlInteiroTeor` e extrai. Nunca lança por falha de rede: devolve
    `indisponivel` com o erro, para o pipeline declarar a lacuna."""
    if not url:
        return TextoExtraido(texto="", metodo="indisponivel", erro="sem urlInteiroTeor")
    proprio = client is None
    client = client or httpx.Client(
        timeout=90, follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0 (compatible; ZIL-Observatorio/1.0; +https://zilobservatorio.com.br)"},
    )
    try:
        raw = client.get(url).content
    except Exception as e:  # noqa: BLE001
        return TextoExtraido(texto="", metodo="indisponivel", erro=f"download falhou: {type(e).__name__}")
    finally:
        if proprio:
            client.close()
    try:
        return extrair_texto_pdf(raw)
    except NaoEhPDF as e:
        return TextoExtraido(texto="", metodo="nao_pdf", erro=str(e))
