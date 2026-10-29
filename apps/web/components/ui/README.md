# ZIL Interface no site

Os componentes desta pasta implementam o design system **ZIL Interface**
(artefato `claude.ai/artifact/LwuwBsq8gRjEBTZCwrEvyr`) em React + Tailwind.
Os tokens vivem como variáveis CSS em `app/globals.css` e ganham nome
Tailwind em `tailwind.config.js` (`bg-zil-superficie-1`, `text-titulo-2`,
`rounded-l`, `duration-toque`, `ease-mola`). O escuro é o tema padrão;
`data-theme="claro"` no `<html>` troca.

## Os seis princípios, em código

| Princípio | O que fazer | O que não fazer |
| --- | --- | --- |
| Preenchimento, não contorno | `bg-zil-superficie-1` para cartão; `superficie-2` para controle dentro dele | `border`, `divide-y`, `ring` como separação |
| Tudo que se toca é pílula | `Button`, `Chip`, `Busca`, `Segmentado`, `Selo`, `Paginacao` | botão retangular, `rounded-sm` em controle |
| Vidro só no que flutua | `.zil-vidro` na nav, tab bar, legenda de foto, popover | vidro em cartão no fluxo da página |
| Movimento físico e curto | `duration-toque` (hover), `duration-padrao` + `ease-mola` (desliza), `Revelar` abaixo da dobra | animação que roda sozinha, `animate-pulse` |
| Um primário por área | um `variante="primario"` por tela ou cartão | dois primários lado a lado |
| Espaço no lugar de linha | `py-16 md:py-24` entre seções, `gap-4`/`gap-6` entre cartões | `<hr>`, `border-b` entre seções |

## Texto

Estilos pelo nome: `text-display-xl` … `text-display-m`, `text-titulo-1` …
`text-titulo-4`, `text-texto-l`, `text-texto` (18px, corpo), `text-texto-ui`
(16px, rótulos), `text-texto-s` (15px, metadados), `text-legenda` (13px),
`text-rotulo` (chapéu, com `uppercase`), `text-numero-xl`, `text-numero-l`.
Leitura longa: `.zil-leitura` (Newsreader 21px, medida de 68ch) ou
`font-serif text-leitura`. Números: `.zil-num` (tabulares). Cores de texto:
`text-zil-texto`, `text-zil-texto-2` (metadados), `text-zil-texto-3`
(placeholder, só sobre fundo e superfícies 1–2).

Nunca parágrafo abaixo de 18px. Datas em dd/mm/aaaa. Score com sinal e
vírgula (`formatarScore`). Botão diz o que acontece ("Ver 18 parlamentares").

## Componentes

| Precisa de | Use |
| --- | --- |
| Ação | `Button` (`primario` · `secundario` · `fantasma` · `vidro`; `tamanho` s/m/l), `BotaoIcone` |
| Filtro de uma lista | `Chip` + `Chips` (`rolagem` no celular), `BarraFiltros`, `Seletor` para listas longas (UF, partido) |
| Alternar um eixo | `Segmentado` (2–4 opções) |
| Buscar | `Busca` |
| Status | `Selo` (`alinhado` · `contra` · `neutro` · `forte`), `DirecaoBadge`, `ContextoBadge`, `CategoriaBadge` |
| Superfície | `Card` (com `href` vira link inteiro), `Estat` (número + rótulo + fonte), `Painel` (chamada final) |
| Lista de itens | `Lista` + `Linha` (ícone, título, sub, `fim`), ou `Placar*` para ranking |
| Score | `ScorePilula`, `ScoreGrande` + `Medidor`, `VotosBarra` + `VotosLegenda` |
| Pessoa | `Avatar` |
| Cronologia | `LinhaDoTempo` + `Marco`; `Etapas` para tramitação |
| Aviso | `Aviso` (`neutro` para dado não validado; `contra` para erro com o que fazer) |
| Carregando / nada | `Esqueleto`, `CardEsqueleto`, `PlacarLinhaEsqueleto`; `Vazio` com motivo e ação |
| Paginar | `Paginacao` |
| Título de seção | `TituloSecao` (chapéu + título + descrição) |
| Citação, foto | `Citacao`, `Foto` |
| Abaixo da dobra | `Revelar` (sequência por `ordem`), `Contador` (número que conta) |

## Layout de página

```tsx
<div className="zil-container">
  <header className="pt-10 md:pt-16 grid gap-4">
    <p className="text-rotulo uppercase text-zil-texto-2">CHAPÉU</p>
    <h1 className="text-titulo-1 md:text-display-m">Título</h1>
    <p className="text-texto-l text-zil-texto-2 max-w-[60ch]">Linha fina.</p>
  </header>
  <section className="zil-secao">…</section>
</div>
```

`zil-container` é `max-w-6xl` com margem lateral 16px no celular e 48px no
desktop. `zil-secao` é o respiro entre seções (64px / 96px).

## Regras do repositório que continuam valendo

- Sem `style={}` inline, exceto valor de dado (posição de marcador, largura
  de barra), sempre com comentário dizendo por quê.
- Novo token: primeiro em `globals.css` + `tailwind.config.js`, depois usar.
- Componente genérico fica aqui; componente de domínio (placar de uma
  proposição, cartão de parlamentar) fica em `components/`.
