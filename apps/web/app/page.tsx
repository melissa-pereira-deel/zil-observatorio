import Link from "next/link";
import { SectionHeader, Button, Card, Callout } from "@/components/ui";
import { ScoreExplainer } from "@/components/ScoreExplainer";
import { RankingPreview } from "@/components/RankingPreview";
import { rankingPublico } from "@/lib/flags";
import { CategoryGrid } from "@/components/CategoryGrid";
import { ManifestoSignature } from "@/components/ManifestoSignature";

/* ── Static data ── */

const STATS = [
  { value: "94%", label: "nióbio mundial", color: "text-zil-green" },
  { value: "87%", label: "fertilizantes importados", color: "text-zil-gold" },
  { value: "83%", label: "eletricidade renovável", color: "text-zil-green" },
  { value: "177mi", label: "brasileiros no PIX", color: "text-zil-gold" },
];

const CONQUISTAS = [
  { year: "1906", title: "Santos Dumont voa", desc: "Disseram que era impossível." },
  { year: "1969", title: "Embraer", desc: "A terceira maior fabricante de aviões do mundo." },
  { year: "1972", title: "Embrapa", desc: "Cerrado vira celeiro de 1 bilhão de pessoas." },
  { year: "1975", title: "Proálcool", desc: "Crise do petróleo? Inventamos alternativa." },
  { year: "1994", title: "Plano Real", desc: "2.477% de inflação/ano. Resolvido." },
  { year: "1996", title: "Urna eletrônica", desc: "150 milhões de votos. Resultado em horas." },
  { year: "2006", title: "Pré-sal", desc: "Tecnologia que nenhum outro país dominava." },
  { year: "2020", title: "PIX", desc: "US$4 mi para criar. US$5,7 bi economizados. O mundo copia." },
];

const PRINCIPLES = [
  ["Consenso, não polarização", "Redes sociais amplificam divisão porque engajamento raivoso gera cliques. O ZIL faz o oposto: usa tecnologia que identifica e amplifica os pontos onde grupos opostos concordam."],
  ["Sinal, não ruído", "O debate público está afogado em ruído. O ZIL é o lugar onde há clareza: dados verificáveis, metas mensuráveis, progresso rastreável."],
  ["Projeto de Estado, não de governo", "Nenhum programa estratégico pode morrer com um mandato. Criamos tecnologia que mede continuidade, registra compromissos e torna a descontinuidade visível."],
  ["Apartidário por design", "O ZIL não lança candidatos, não apoia partidos. Tem método. O agricultor conservador e o sindicalista progressista concordam que importar 87% dos fertilizantes é absurdo."],
  ["Aberto e auditável", "Todo dado, algoritmo, classificação e decisão é pública. Código aberto. Processo rastreável. Legitimidade vem de transparência."],
  ["Compromisso tem registro", "Todo parlamentar que assumir compromisso terá esse compromisso registrado publicamente. A plataforma cruza promessa com voto real."],
];

const MECHANISMS = [
  ["Deliberação por consenso", "Inspirado no Polis/vTaiwan — que gerou legislação real para 23 milhões de taiwaneses. Ninguém responde a ninguém: apenas propõe, concorda ou discorda. O algoritmo identifica declarações-ponte entre grupos opostos."],
  ["A bússola", "Marcos estratégicos definidos pela comunidade, com métricas verificáveis. Monitorados trimestralmente, independente de quem governa. Quando um governo muda, os marcos não mudam."],
  ["Compromisso rastreável", "Parlamentares registram metas específicas. O sistema cruza cada compromisso com dados reais de votação e execução orçamentária."],
  ["Score de alinhamento", "Cada parlamentar tem score calculado por fórmula transparente. Qualquer cidadão pode ver, auditar e contestar."],
  ["Continuidade mensurável", "Índice público que mostra quanto cada governo manteve, expandiu ou desmontou dos programas estratégicos anteriores."],
];

const COMPASS_QUESTIONS = [
  "O Brasil processa os recursos que extrai ou exporta matéria-prima barata?",
  "Nossos fertilizantes, chips e combustíveis dependem de importação?",
  "Os compromissos dos nossos representantes estão sendo cumpridos?",
  "Os programas estratégicos estão sendo mantidos entre governos?",
  "O país está mais ou menos soberano do que há um ano?",
];

const AUDIENCE = [
  "A quem quer sinal no meio do ruído",
  "A quem discorda sobre política mas concorda sobre soberania",
  "A quem cansou de promessa sem medição",
  "A quem sabe que o Brasil pode mais — e quer a prova",
  "Ao político que quer ser cobrado por resultados",
  "A quem acredita que tecnologia pode servir à democracia",
];

/* ── Page ── */

export default function HomePage() {
  return (
    <div className="animate-fade-in">
      {/* ═══════ HERO ═══════ */}
      <section className="zil-container zil-section relative overflow-hidden">
        {/* Decorative circle */}
        <div className="absolute -top-32 -right-20 w-80 h-80 rounded-full border border-zil-divider opacity-30 pointer-events-none hidden md:block" />

        <div className="font-mono text-2xs md:text-xs tracking-[0.25em] text-zil-muted uppercase mb-8 md:mb-10">
          Manifesto pela soberania industrial
        </div>

        <div className="relative mb-1">
          <h1 className="font-display text-7xl md:text-8xl lg:text-9xl leading-none tracking-tighter">
            ZIL
          </h1>
          <div className="absolute bottom-1 md:bottom-2 left-[5.5rem] md:left-[7.5rem] lg:left-[8.5rem] flex gap-1">
            <div className="w-14 md:w-16 h-1 bg-zil-gold skew-x-[-12deg]" />
            <div className="w-6 md:w-7 h-1 bg-zil-green skew-x-[-12deg]" />
          </div>
        </div>

        <p className="font-semibold text-xs md:text-sm tracking-[0.25em] text-zil-soft uppercase mt-5">
          Zero Dependência — Indústria Nacional — Liderança Soberana
        </p>

        <p className="text-base md:text-lg leading-relaxed text-zil-soft mt-8 max-w-xl border-l-[3px] border-zil-green pl-4 md:pl-5">
          Um país que venceu a hiperinflação, inventou o PIX, transformou
          cerrado em celeiro do mundo e construiu a Embraer pode fazer qualquer
          coisa — se conseguir convergir.
        </p>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 md:gap-8 mt-10 md:mt-12">
          {STATS.map((s) => (
            <div key={s.label}>
              <div className={`font-display text-2xl md:text-3xl ${s.color}`}>
                {s.value}
              </div>
              <div className="font-mono text-2xs md:text-xs text-zil-muted tracking-wider mt-1">
                {s.label}
              </div>
            </div>
          ))}
        </div>

        {/* CTA */}
        <div className="flex flex-col sm:flex-row gap-3 mt-10">
          <Button href={rankingPublico ? "/ranking" : "/proposicoes"} variant="primary">
            {rankingPublico ? "Ver ranking de parlamentares" : "Ver proposições monitoradas"}
          </Button>
          <Button href="#score" variant="secondary">
            Como funciona o score
          </Button>
        </div>
      </section>

      <div className="zil-container"><div className="zil-divider-line" /></div>

      {/* ═══════ 01 — CONQUISTAS ═══════ */}
      <section className="zil-container zil-section">
        <SectionHeader
          number="01"
          title="Já fizemos antes."
          description="Toda vez que disseram que não conseguiríamos, provamos o contrário. Cada conquista nasceu da recusa coletiva de aceitar dependência."
        />

        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          {CONQUISTAS.map((c) => (
            <div
              key={c.year}
              className="p-3 md:p-4 border-l-2 border-zil-divider hover:bg-zil-card transition-colors"
            >
              <div className="font-display text-xs text-zil-gold tracking-widest">
                {c.year}
              </div>
              <div className="font-semibold text-xs md:text-sm mt-1">
                {c.title}
              </div>
              <p className="text-xs text-zil-muted mt-1 leading-relaxed">
                {c.desc}
              </p>
            </div>
          ))}
        </div>

        <Callout variant="light" className="mt-6">
          <p className="text-xs md:text-sm text-zil-soft leading-relaxed">
            <strong className="text-zil-fg">
              Nenhuma dessas conquistas nasceu de um lado só do espectro
              político.
            </strong>{" "}
            Nasceu de convergência.
          </p>
        </Callout>
      </section>

      <div className="zil-container"><div className="zil-divider-line" /></div>

      {/* ═══════ 02 — POR QUE PARAMOS ═══════ */}
      <section className="zil-container zil-section">
        <SectionHeader number="02" title="Por que paramos?" />
        <div className="zil-prose space-y-3">
          <p className="text-sm md:text-base text-zil-soft leading-relaxed">
            O mesmo país que criou o PIX — US$4,6 trilhões processados em 2024
            — importa 87% dos fertilizantes. Exporta petróleo e importa
            gasolina.
          </p>
          <p className="text-sm md:text-base text-zil-soft leading-relaxed">
            Em três décadas, desmontamos capacidade que levou gerações para
            construir. A Petrobras fechou fábricas de fertilizantes. A Vale foi
            privatizada por fração do valor. A estatal de chips, liquidada.
          </p>
          <p className="text-sm md:text-base text-zil-green font-semibold">
            O problema não é capacidade. É outro.
          </p>
        </div>
      </section>

      <div className="zil-container"><div className="zil-divider-line" /></div>

      {/* ═══════ 03 — COORDENAÇÃO ═══════ */}
      <section className="zil-container zil-section">
        <SectionHeader number="03" title="Não conseguimos convergir." />
        <div className="zil-prose space-y-3">
          <p className="text-sm md:text-base text-zil-soft leading-relaxed">
            O Brasil não tem déficit de planos. Tem déficit de continuidade. Cada
            governo desfaz o que o anterior construiu. E o que alimenta esse
            ciclo?
          </p>
          <p className="text-sm md:text-base text-zil-soft leading-relaxed">
            Redes sociais maximizam engajamento. Engajamento é maximizado por
            indignação. Indignação gera polarização. Polarização impede
            convergência. Sem convergência, não existe projeto de longo prazo.
          </p>
          <p className="text-sm md:text-base text-zil-green font-semibold">
            A saída é uma infraestrutura diferente — desenhada para convergência,
            não para polarização.
          </p>
        </div>
      </section>

      <div className="zil-container"><div className="zil-divider-line" /></div>

      {/* ═══════ 04 — O QUE É ═══════ */}
      <section className="zil-container zil-section">
        <SectionHeader number="04" title="O ZIL é tecnologia para consenso." />

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-8 md:gap-12 mt-4">
          <div>
            <div className="font-semibold text-xs tracking-widest text-zil-green uppercase mb-3">
              O que é
            </div>
            {[
              "Tecnologia para consenso",
              "Bússola de longo prazo",
              "Dados verificáveis",
              "Apartidário por design",
              "Código aberto",
              "Espaço de clareza",
            ].map((t) => (
              <div
                key={t}
                className="flex gap-2 items-baseline text-xs md:text-sm text-zil-soft mb-1.5"
              >
                <span className="text-zil-green text-[5px]">&#9679;</span>
                {t}
              </div>
            ))}
          </div>

          <div>
            <div className="font-semibold text-xs tracking-widest text-zil-muted uppercase mb-3">
              O que não é
            </div>
            {[
              "Partido ou movimento",
              "Veículo de candidaturas",
              "Órgão de denúncia",
              "Rede social de opinião",
              "Ferramenta de um lado",
              "Mais ruído",
            ].map((t) => (
              <div
                key={t}
                className="flex gap-2 items-baseline text-xs md:text-sm text-zil-muted mb-1.5"
              >
                <span className="text-[5px]">&#9675;</span>
                {t}
              </div>
            ))}
          </div>
        </div>
      </section>

      <div className="zil-container"><div className="zil-divider-line" /></div>

      {/* ═══════ 05 — SCORE ZIL (NEW) ═══════ */}
      <section id="score" className="zil-container zil-section scroll-mt-20">
        <SectionHeader
          number="05"
          title="Como funciona o Score ZIL"
        />
        <ScoreExplainer />
      </section>

      <div className="zil-container"><div className="zil-divider-line" /></div>

      {/* ═══════ 06 — RANKING PREVIEW (NEW) ═══════ */}
      {/* A seção inteira sai enquanto o ranking não for público: manter só o
          cabeçalho anunciaria um conteúdo que não está lá. */}
      {rankingPublico && (
        <>
          <section className="zil-container zil-section">
            <SectionHeader
              number="06"
              title="Como votam os parlamentares do Brasil"
              description="Score de alinhamento calculado a partir de votos reais em pautas de soberania industrial."
            />
            <RankingPreview />
          </section>

          <div className="zil-container"><div className="zil-divider-line" /></div>
        </>
      )}

      {/* ═══════ 07 — CATEGORIAS (NEW) ═══════ */}
      <section className="zil-container zil-section">
        <SectionHeader
          number="07"
          title="9 áreas estratégicas"
          description="O ZIL monitora votações, proposições e posicionamentos em nove eixos da soberania industrial brasileira."
        />
        <CategoryGrid />
      </section>

      <div className="zil-container"><div className="zil-divider-line" /></div>

      {/* ═══════ 08 — PRINCÍPIOS + MECANISMOS ═══════ */}
      <section className="zil-container zil-section">
        <SectionHeader number="08" title="Princípios de design" />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-5 mb-10 md:mb-12">
          {PRINCIPLES.map(([title, desc]) => (
            <div
              key={title}
              className="pl-4 border-l-2 border-zil-green hover:pl-5 transition-all"
            >
              <div className="font-semibold text-xs tracking-widest text-zil-green-dark uppercase mb-1">
                {title}
              </div>
              <p className="text-xs md:text-sm text-zil-soft leading-relaxed">
                {desc}
              </p>
            </div>
          ))}
        </div>

        <h3 className="font-display text-base md:text-lg uppercase tracking-wide mb-5">
          Como funciona
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {MECHANISMS.map(([title, desc]) => (
            <div
              key={title}
              className="p-4 border-l-2 border-zil-divider hover:border-l-zil-green hover:bg-zil-card transition-all"
            >
              <div className="font-semibold text-sm mb-1">{title}</div>
              <p className="text-xs md:text-sm text-zil-soft leading-relaxed">
                {desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      <div className="zil-container"><div className="zil-divider-line" /></div>

      {/* ═══════ 09 — ACESSO LIVRE (NEW) ═══════ */}
      <section className="zil-container zil-section">
        <SectionHeader number="09" title="Acesso livre por design" />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-12">
          {/* Public data */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <div className="w-2 h-2 rounded-full bg-zil-green" />
              <h3 className="font-display text-sm uppercase tracking-wide">
                Explorar dados
              </h3>
            </div>
            <p className="text-sm text-zil-soft leading-relaxed mb-4">
              O ranking, os scores, as proposições e todos os votos são dados
              públicos. Sem paywall, sem login obrigatório.
            </p>
            <ul className="space-y-2 mb-5">
              {[
                "Ranking completo de parlamentares",
                "Histórico de votações por pauta",
                "Proposições classificadas por categoria",
                "API aberta para jornalistas e pesquisadores",
              ].map((item) => (
                <li
                  key={item}
                  className="flex gap-2 text-xs md:text-sm text-zil-soft"
                >
                  <span className="text-zil-green mt-0.5">&#10003;</span>
                  {item}
                </li>
              ))}
            </ul>
            <div className="flex flex-wrap gap-2">
              {rankingPublico && (
                <Button href="/ranking" variant="primary" size="sm">
                  Ranking
                </Button>
              )}
              <Button href="/proposicoes" variant="ghost" size="sm">
                Proposições
              </Button>
            </div>
          </div>

          {/* Account for participation */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <div className="w-2 h-2 rounded-full bg-zil-gold" />
              <h3 className="font-display text-sm uppercase tracking-wide">
                Participar
              </h3>
            </div>
            <p className="text-sm text-zil-soft leading-relaxed mb-4">
              Para votar em deliberações, cobrar parlamentares e receber
              alertas, crie uma conta gratuita.
            </p>
            <ul className="space-y-2 mb-5">
              {[
                "Votar em deliberações por consenso",
                "Cobrar parlamentares diretamente",
                "Alertas sobre votações e mudanças de score",
                "Propor e contestar classificações",
              ].map((item) => (
                <li
                  key={item}
                  className="flex gap-2 text-xs md:text-sm text-zil-soft"
                >
                  <span className="text-zil-gold mt-0.5">&#9670;</span>
                  {item}
                </li>
              ))}
            </ul>
            <div className="flex flex-wrap gap-3 text-xs font-mono text-zil-muted">
              {[
                "Apartidário",
                "Código aberto",
                "Sem ads ou tracking",
              ].map((t) => (
                <span key={t} className="flex items-center gap-1.5">
                  <span className="text-zil-green text-[9px]">&#10003;</span>
                  {t}
                </span>
              ))}
            </div>
          </div>
        </div>
      </section>

      <div className="zil-container"><div className="zil-divider-line" /></div>

      {/* ═══════ 10 — BÚSSOLA + PARA QUEM ═══════ */}
      <section className="zil-container zil-section">
        <SectionHeader
          number="10"
          title="A bússola"
          description="Perguntas estratégicas com métricas verificáveis. A bússola não muda com o ciclo de notícias."
        />

        <div className="mb-8">
          {COMPASS_QUESTIONS.map((q, i) => (
            <div
              key={i}
              className="py-3 pl-4 border-l-2 border-zil-gold border-b border-b-zil-divider last:border-b-0"
            >
              <p className="text-xs md:text-sm font-medium">{q}</p>
            </div>
          ))}
        </div>

        <Callout variant="light">
          <p className="text-xs md:text-sm text-zil-soft leading-relaxed">
            <strong className="text-zil-fg">
              Clareza onde antes havia só ruído.
            </strong>{" "}
            Marcos com métricas, fontes oficiais e prazos. Quando um governo
            muda, os marcos permanecem.
          </p>
        </Callout>

        {/* Audience */}
        <div className="mt-10">
          <h3 className="font-display text-base md:text-lg uppercase tracking-wide mb-5">
            Para quem é o ZIL
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-2">
            {AUDIENCE.map((a) => (
              <div
                key={a}
                className="flex gap-2 items-baseline text-sm text-zil-soft hover:text-zil-green hover:pl-1 transition-all"
              >
                <span className="text-zil-gold text-[7px] shrink-0 mt-1">
                  &#9670;
                </span>
                {a}
              </div>
            ))}
          </div>
        </div>

        <Callout variant="dark" className="mt-8">
          <p className="font-display text-sm md:text-base uppercase tracking-wide leading-snug">
            O Brasil não precisa de mais opinião. Precisa de mais convergência.
            O ZIL é a infraestrutura para isso.
          </p>
        </Callout>
      </section>

      <div className="zil-container"><div className="zil-divider-line" /></div>

      {/* ═══════ 11 — ASSINAR ═══════ */}
      <section className="zil-container zil-section">
        <SectionHeader number="11" title="Assinar o manifesto" />
        <ManifestoSignature />
      </section>
    </div>
  );
}
