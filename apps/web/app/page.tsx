import { Button, Card, Citacao, Contador, Estat, Icone, Lista, Linha, Painel, Revelar, Selo, TituloSecao } from "@/components/ui";
import { ScoreExplainer } from "@/components/ScoreExplainer";
import { RankingPreview } from "@/components/RankingPreview";
import { rankingPublico } from "@/lib/flags";
import { CategoryGrid } from "@/components/CategoryGrid";
import { Newsletter } from "@/components/Newsletter";

/* ── Dados estáticos do manifesto ── */

// Cada número leva a fonte ao lado (ZIL Interface: "números têm fonte").
// Dois pares, que respondem às duas frases do título: o que já provamos e
// o que ainda falta convergir.
const PROVAS = [
  { ate: 177, sufixo: " mi", rotulo: "brasileiros usam o Pix", fonte: "Banco Central" },
  { ate: 83, sufixo: "%", rotulo: "da eletricidade vem de fontes renováveis", fonte: "EPE, Balanço Energético" },
];
const FALTAS = [
  { ate: 87, sufixo: "%", rotulo: "dos fertilizantes são importados", fonte: "ANDA / MAPA" },
  { ate: 94, sufixo: "%", rotulo: "das reservas de nióbio são nossas — e sai quase tudo bruto", fonte: "USGS" },
];

const CONQUISTAS = [
  { ano: "1906", titulo: "Santos Dumont voa", desc: "Disseram que era impossível." },
  { ano: "1969", titulo: "Embraer", desc: "A terceira maior fabricante de aviões do mundo." },
  { ano: "1972", titulo: "Embrapa", desc: "Cerrado vira celeiro de 1 bilhão de pessoas." },
  { ano: "1975", titulo: "Proálcool", desc: "Crise do petróleo? Inventamos alternativa." },
  { ano: "1994", titulo: "Plano Real", desc: "2.477% de inflação/ano. Resolvido." },
  { ano: "1996", titulo: "Urna eletrônica", desc: "150 milhões de votos. Resultado em horas." },
  { ano: "2006", titulo: "Pré-sal", desc: "Tecnologia que nenhum outro país dominava." },
  { ano: "2020", titulo: "PIX", desc: "US$4 mi para criar. US$5,7 bi economizados. O mundo copia." },
];

const PRINCIPIOS = [
  ["Consenso, não polarização", "Redes sociais amplificam divisão porque engajamento raivoso gera cliques. O ZIL faz o oposto: parte do que já é consenso — o país não pode depender de fora no que é estratégico — e mede quem age de acordo."],
  ["Sinal, não ruído", "O debate público está afogado em ruído. O ZIL é o lugar onde há clareza: dados verificáveis, metas mensuráveis, progresso rastreável."],
  ["Projeto de Estado, não de governo", "Nenhum programa estratégico pode morrer com um mandato. A Bússola mede marcos que não mudam com o governo, e o placar mostra quem vota pela continuidade."],
  ["Apartidário por design", "O ZIL não lança candidatos, não apoia partidos. Tem método. O agricultor conservador e o sindicalista progressista concordam que importar 87% dos fertilizantes é absurdo."],
  ["Aberto e auditável", "Todo dado, algoritmo, classificação e decisão é pública. Código aberto. Processo rastreável. Legitimidade vem de transparência."],
];

// O que está no ar (v1). Cada cartão leva à página correspondente.
const O_QUE_EXISTE = [
  { titulo: "Score de alinhamento", href: "/metodologia", desc: "Calculado por fórmula publicada sobre votações selecionadas, cada uma com direção esperada justificada. Fórmula, dados e classificações estão no repositório." },
  { titulo: "Proposições classificadas", href: "/proposicoes", desc: "Projetos, PECs e MPs do Congresso classificados nas nove pautas de soberania industrial, com resumo em linguagem simples quando há." },
  { titulo: "A Bússola", href: "/bussula", desc: "Marcos com métrica, fonte oficial e prazo, em arquivo versionado. Quando um governo muda, os marcos não mudam." },
  { titulo: "Dados abertos", href: "/proposicoes", desc: "API pública, código AGPL e histórico de cada decisão editorial no git. Sem login, sem paywall, sem tracking." },
];

// v2 e v3 do roadmap (docs/ROADMAP.md). Fora da v1 por decisão explícita:
// aparecem como visão, sem mecânica, para a home não prometer o que não há.
const VISAO = [
  { titulo: "Deliberação por consenso", desc: "Decisões estratégicas discutidas por declarações, ao estilo vTaiwan." },
  { titulo: "Compromissos públicos", desc: "Parlamentares registram posições verificáveis; a plataforma cruza promessa com voto." },
  { titulo: "Índice de continuidade", desc: "Quanto cada governo manteve, expandiu ou desmontou dos programas estratégicos." },
];
const ROADMAP_URL = "https://github.com/zil-observatorio/zil-observatorio/blob/main/docs/ROADMAP.md";

const O_QUE_E = ["Observatório de votos e proposições", "Bússola de longo prazo", "Dados verificáveis", "Apartidário por design", "Código aberto", "Método publicado"];

const O_QUE_NAO_E = ["Partido ou movimento", "Veículo de candidaturas", "Órgão de denúncia", "Rede social de opinião", "Ferramenta de um lado", "Mais ruído"];

const PERGUNTAS_BUSSOLA = [
  "O Brasil processa os recursos que extrai ou exporta matéria-prima barata?",
  "Nossos fertilizantes, chips e combustíveis dependem de importação?",
  "Os compromissos dos nossos representantes estão sendo cumpridos?",
  "Os programas estratégicos estão sendo mantidos entre governos?",
  "O país está mais ou menos soberano do que há um ano?",
];

const PARA_QUEM = [
  "A quem quer sinal no meio do ruído",
  "A quem discorda sobre política mas concorda sobre soberania",
  "A quem cansou de promessa sem medição",
  "A quem sabe que o Brasil pode mais — e quer a prova",
  "Ao político que quer ser cobrado por resultados",
  "A quem acredita que tecnologia pode servir à democracia",
];

const EXPLORAR = [
  "Placar das votações monitoradas",
  "Histórico de votações por pauta",
  "Proposições classificadas por categoria",
  "API aberta para jornalistas e pesquisadores",
];

const PARTICIPAR = [
  "Propor classificações de votações (via Pull Request)",
  "Revisar as classificações já existentes",
  "Planejado: contas, alertas e deliberação por consenso",
];

/* ── Página ── */

export default function HomePage() {
  return (
    <div className="zil-container">
      {/* ═══════ ABERTURA ═══════ */}
      {/* Ordem: quem fala (chapéu) → a tese (título e linha fina) → o convite
          (botões) → a prova (números). A foto acompanha o texto no desktop. */}
      <header className="pt-10 md:pt-16 grid gap-10 md:gap-14">
        <div className="grid gap-10 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)] lg:gap-14 lg:items-center">
          <div className="grid gap-6">
            <p className="text-rotulo uppercase text-zil-texto-2">Manifesto pela soberania industrial</p>
            <h1 className="text-titulo-1 md:text-display-m lg:text-display-l max-w-[16ch]">
              O Brasil já provou que pode.
              <br />
              Falta convergir.
            </h1>
            <p className="text-texto-l text-zil-texto-2 max-w-[62ch]">
              Vencemos a hiperinflação, inventamos o Pix, transformamos o cerrado no celeiro do mundo e construímos a Embraer. Nenhuma
              dessas conquistas foi de um governo só, nem de um lado só: nasceu de décadas de continuidade. O ZIL Observatório existe
              para mostrar, voto a voto, quem no Congresso trabalha pela próxima — e quem a desmonta.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 pt-1">
              <Button href={rankingPublico ? "/ranking" : "/proposicoes"} variante="primario" tamanho="l">
                {rankingPublico ? "Ver o placar" : "Ver proposições monitoradas"}
              </Button>
              <Button href="#score" variante="secundario" tamanho="l">
                Como funciona o score
              </Button>
            </div>
          </div>

          {/* Foto de abertura (fotografia.md): pessoas construindo o país, ao
              lado do texto no desktop. Ainda não há foto licenciada no
              repositório. Candidatas: trabalhadores da construção de Brasília
              (1957, Arquivo Nacional, domínio público) ou o primeiro voo do
              Bandeirante (1968). Ao escolher, trocar o bloco abaixo por:
              <Foto src="/fotos/..." alt="descrição da cena" titulo="…" credito="Autor · Acervo Arquivo Nacional" />
              e baixar o original no acervo antes de publicar. */}
          <div aria-hidden="true" className="aspect-[16/9] lg:aspect-[4/5] w-full rounded-xl bg-zil-superficie-1" />
        </div>

        {/* Os dois pares só ficam lado a lado a partir de lg: em 768px, quatro
            cartões numa linha espremem "177 mi" em duas linhas. */}
        <Revelar className="grid gap-6 lg:grid-cols-2">
          <div className="grid gap-3 content-start">
            <p className="text-rotulo uppercase text-zil-texto-2">Já provou que pode</p>
            <div className="grid grid-cols-2 gap-4 md:gap-6">
              {PROVAS.map((n) => (
                <Estat key={n.rotulo} n={<Contador ate={n.ate} sufixo={n.sufixo} />} rotulo={n.rotulo} fonte={n.fonte} />
              ))}
            </div>
          </div>
          <div className="grid gap-3 content-start">
            <p className="text-rotulo uppercase text-zil-texto-2">Falta convergir</p>
            <div className="grid grid-cols-2 gap-4 md:gap-6">
              {FALTAS.map((n) => (
                <Estat key={n.rotulo} n={<Contador ate={n.ate} sufixo={n.sufixo} />} rotulo={n.rotulo} fonte={n.fonte} />
              ))}
            </div>
          </div>
        </Revelar>
      </header>

      {/* ═══════ 01 — CONQUISTAS ═══════ */}
      <section className="zil-secao">
        <TituloSecao chapeu="01" titulo="Oito vezes em que provamos." descricao="Toda vez que disseram que não conseguiríamos, provamos o contrário." />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6">
          {CONQUISTAS.map((c, i) => (
            <Revelar key={c.ano} ordem={i}>
              <Card compacto className="h-full grid content-start gap-2">
                <span className="text-legenda text-zil-texto-2 zil-num">{c.ano}</span>
                <h3 className="text-titulo-4">{c.titulo}</h3>
                <p className="text-texto-s text-zil-texto-2">{c.desc}</p>
              </Card>
            </Revelar>
          ))}
        </div>
      </section>

      {/* ═══════ 02 — POR QUE PARAMOS ═══════ */}
      <section className="zil-secao">
        <TituloSecao chapeu="02" titulo="Por que paramos?" />
        <div className="zil-leitura">
          <p>
            O mesmo país que criou o PIX — US$4,6 trilhões processados em 2024 — importa 87% dos fertilizantes. Exporta petróleo e importa
            gasolina.
          </p>
          <p>
            Em três décadas, desmontamos capacidade que levou gerações para construir. A Petrobras fechou fábricas de fertilizantes. A Vale foi
            privatizada por fração do valor. A estatal de chips, liquidada.
          </p>
          <p>
            <strong>O problema não é capacidade. É outro.</strong>
          </p>
        </div>
      </section>

      {/* ═══════ 03 — COORDENAÇÃO ═══════ */}
      <section className="zil-secao">
        <TituloSecao chapeu="03" titulo="Não conseguimos convergir." />
        <div className="zil-leitura">
          <p>O Brasil não tem déficit de planos. Tem déficit de continuidade. Cada governo desfaz o que o anterior construiu. E o que alimenta esse ciclo?</p>
          <p>
            Redes sociais maximizam engajamento. Engajamento é maximizado por indignação. Indignação gera polarização. Polarização impede
            convergência. Sem convergência, não existe projeto de longo prazo.
          </p>
          <p>
            <strong>A saída é uma infraestrutura diferente — desenhada para convergência, não para polarização.</strong>
          </p>
        </div>
      </section>

      {/* ═══════ 04 — O QUE É ═══════ */}
      <section className="zil-secao">
        <TituloSecao chapeu="04" titulo="O ZIL é um observatório." />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
          <Lista titulo="O que é">
            {O_QUE_E.map((t) => (
              <Linha key={t} icone={<Icone nome="check" tamanho="s" />} titulo={t} />
            ))}
          </Lista>
          <Lista titulo="O que não é">
            {O_QUE_NAO_E.map((t) => (
              <Linha key={t} icone={<Icone nome="fechar" tamanho="s" />} titulo={<span className="text-zil-texto-2">{t}</span>} />
            ))}
          </Lista>
        </div>
      </section>

      {/* ═══════ 05 — SCORE ZIL ═══════ */}
      <section id="score" className="zil-secao scroll-mt-20">
        <TituloSecao chapeu="05" titulo="Como funciona o Score ZIL" />
        <ScoreExplainer />
      </section>

      {/* ═══════ 06 — PRÉVIA DO RANKING ═══════ */}
      {/* A seção inteira sai enquanto o ranking não for público: manter só o
          cabeçalho anunciaria um conteúdo que não está lá. */}
      {rankingPublico && (
        <section className="zil-secao">
          <TituloSecao
            chapeu="06"
            titulo="Como votaram nas pautas que mais importam"
            descricao="Score de alinhamento calculado a partir de votos reais em pautas de soberania industrial."
          />
          <RankingPreview />
        </section>
      )}

      {/* ═══════ 07 — CATEGORIAS ═══════ */}
      <section className="zil-secao">
        <TituloSecao
          chapeu="07"
          titulo="9 áreas estratégicas"
          descricao="O ZIL acompanha proposições e votações do Congresso nos eixos da soberania industrial brasileira."
        />
        <CategoryGrid />
      </section>

      {/* ═══════ 08 — PRINCÍPIOS, O QUE EXISTE E VISÃO ═══════ */}
      <section className="zil-secao">
        <TituloSecao chapeu="08" titulo="Princípios de design" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
          {PRINCIPIOS.map(([titulo, desc], i) => (
            <Revelar key={titulo} ordem={i}>
              <Card className="h-full grid content-start gap-2">
                <h3 className="text-titulo-4">{titulo}</h3>
                <p className="text-texto text-zil-texto-2">{desc}</p>
              </Card>
            </Revelar>
          ))}
        </div>

        <h3 className="text-titulo-3 mt-16 md:mt-20 mb-6 md:mb-8">Como funciona hoje</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
          {O_QUE_EXISTE.map((m, i) => (
            <Revelar key={m.titulo} ordem={i}>
              <Card href={m.href} className="h-full grid grid-cols-[minmax(0,1fr)_auto] gap-x-4 gap-y-2 content-start">
                <h4 className="text-titulo-4">{m.titulo}</h4>
                <Icone nome="chevron-direita" className="text-zil-texto-3 mt-0.5" />
                <p className="text-texto text-zil-texto-2 col-span-2">{m.desc}</p>
              </Card>
            </Revelar>
          ))}
        </div>

        {/* Visão de longo prazo: v2 e v3 do roadmap, fora da v1 por decisão
            explícita (CLAUDE.md, ROADMAP). Fica separado e rotulado para a
            home não prometer o que não existe. */}
        <div className="mt-16 md:mt-20 grid gap-6">
          <div className="flex flex-wrap items-center gap-3">
            <h3 className="text-titulo-3">Para onde vamos</h3>
            <Selo tom="neutro" ponto>
              Visão de longo prazo · v2 e v3
            </Selo>
          </div>
          <p className="text-texto text-zil-texto-2 max-w-[60ch]">
            Nada disto existe hoje. Está no roadmap público, nesta ordem, e só entra quando o placar estiver sustentado pela curadoria.
          </p>
          <Lista>
            {VISAO.map((v) => (
              <Linha key={v.titulo} titulo={v.titulo} sub={v.desc} />
            ))}
          </Lista>
          <div>
            <Button href={ROADMAP_URL} variante="fantasma" tamanho="s" target="_blank" rel="noopener noreferrer">
              Ver o roadmap
              <Icone nome="externo" tamanho="s" />
            </Button>
          </div>
        </div>
      </section>

      {/* ═══════ 09 — ACESSO LIVRE ═══════ */}
      <section className="zil-secao">
        <TituloSecao chapeu="09" titulo="Acesso livre por design" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-12">
          {/* Dados públicos */}
          <div className="grid content-start gap-5">
            <h3 className="text-titulo-3">Explorar dados</h3>
            <p className="text-texto text-zil-texto-2">
              O ranking, os scores, as proposições e todos os votos são dados públicos. Sem paywall, sem login obrigatório.
            </p>
            <Lista>
              {EXPLORAR.map((item) => (
                <Linha key={item} icone={<Icone nome="check" tamanho="s" />} titulo={item} />
              ))}
            </Lista>
            <div className="flex flex-wrap gap-2">
              {rankingPublico ? (
                <>
                  <Button href="/ranking" variante="primario" tamanho="s">
                    Ver o placar
                  </Button>
                  <Button href="/proposicoes" variante="secundario" tamanho="s">
                    Ver proposições
                  </Button>
                </>
              ) : (
                <Button href="/proposicoes" variante="primario" tamanho="s">
                  Ver proposições
                </Button>
              )}
            </div>
          </div>

          {/* Participação */}
          <div className="grid content-start gap-5">
            <h3 className="text-titulo-3">Participar</h3>
            <p className="text-texto text-zil-texto-2">
              Não há contas de usuário nem deliberação na plataforma — isto é visão de longo prazo, não o que existe hoje. Quem quiser
              participar agora contribui pelo repositório: a curadoria das classificações é o trabalho de maior impacto no momento.
            </p>
            <Lista>
              {PARTICIPAR.map((item) => (
                <Linha key={item} icone={<Icone nome="documento" tamanho="s" />} titulo={item} />
              ))}
            </Lista>
            <div className="flex flex-wrap gap-2">
              {["Apartidário", "Código aberto", "Sem ads ou tracking"].map((t) => (
                <Selo key={t} ponto>
                  {t}
                </Selo>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ═══════ 10 — BÚSSOLA + PARA QUEM ═══════ */}
      <section className="zil-secao">
        <TituloSecao
          chapeu="10"
          titulo="A bússola"
          descricao="Perguntas estratégicas com métricas verificáveis. A bússola não muda com o ciclo de notícias."
        />
        <Lista>
          {PERGUNTAS_BUSSOLA.map((q) => (
            <Linha key={q} icone={<Icone nome="bussola" tamanho="s" />} titulo={q} />
          ))}
        </Lista>
        <p className="mt-8 md:mt-10 text-texto-l max-w-[60ch]">
          <strong className="font-semibold">Clareza onde antes havia só ruído.</strong>{" "}
          <span className="text-zil-texto-2">Marcos com métricas, fontes oficiais e prazos. Quando um governo muda, os marcos permanecem.</span>
        </p>

        <h3 className="text-titulo-3 mt-16 md:mt-20 mb-6 md:mb-8">Para quem é o ZIL</h3>
        <Lista className="md:grid-cols-2">
          {PARA_QUEM.map((a) => (
            <Linha key={a} titulo={a} />
          ))}
        </Lista>

        <Revelar className="mt-16 md:mt-24">
          <Citacao autor="Manifesto ZIL">
            O Brasil não precisa de mais opinião. Precisa de mais convergência. O ZIL é a infraestrutura para isso.
          </Citacao>
        </Revelar>
      </section>

      {/* ═══════ 11 — NEWSLETTER ═══════ */}
      {/* A nav aponta para /#newsletter. */}
      <section id="newsletter" className="zil-secao scroll-mt-20">
        <Painel>
          <p className="text-rotulo uppercase text-zil-texto-2">11</p>
          <h2 className="text-titulo-1 md:text-display-m">Acompanhe o ZIL</h2>
          <Newsletter />
        </Painel>
      </section>
    </div>
  );
}
