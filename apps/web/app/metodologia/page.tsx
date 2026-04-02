import Link from "next/link";

const CATEGORIAS = [
  {
    codigo: "ZIL-FER",
    nome: "Fertilizantes",
    emoji: "🌱",
    descricao:
      "Proposições sobre produção nacional de insumos agrícolas, redução da dependência de ureia, fosfato e potássio importados, e política de estoques estratégicos.",
    exemplo: "PL que cria reservas estratégicas de fertilizantes nitrogenados",
  },
  {
    codigo: "ZIL-MIN",
    nome: "Minerais Estratégicos",
    emoji: "⛏️",
    descricao:
      "Regras para mineração, exportação e beneficiamento de nióbio, lítio, terras-raras e outros minerais críticos para cadeias tecnológicas.",
    exemplo: "PEC que exige processamento mínimo antes da exportação de nióbio",
  },
  {
    codigo: "ZIL-SEM",
    nome: "Semicondutores",
    emoji: "💾",
    descricao:
      "Política industrial para chips, eletrônica e equipamentos de telecomunicação. Inclui incentivos para fabricação local e compras governamentais.",
    exemplo: "MP que cria crédito tributário para fabricantes nacionais de chips",
  },
  {
    codigo: "ZIL-ENE",
    nome: "Energia",
    emoji: "⚡",
    descricao:
      "Soberania energética: petróleo, gás, renováveis, redes de transmissão. Foco em capacidade nacional de produção e refino.",
    exemplo: "PL sobre obrigatoriedade de refino nacional do petróleo do pré-sal",
  },
  {
    codigo: "ZIL-DIG",
    nome: "Soberania Digital",
    emoji: "🔐",
    descricao:
      "Infraestrutura de internet, data centers, software de base, cabos submarinos, computação em nuvem e proteção de dados estratégicos.",
    exemplo: "PDL sobre armazenamento obrigatório de dados governamentais em servidores nacionais",
  },
  {
    codigo: "ZIL-DEF",
    nome: "Defesa e Segurança",
    emoji: "🛡️",
    descricao:
      "Base industrial de defesa, compras governamentais com transferência tecnológica, satélites e sistemas de comunicação estratégicos.",
    exemplo: "PL que exige componentes nacionais em 60% dos equipamentos militares",
  },
  {
    codigo: "ZIL-EDU",
    nome: "Capital Humano",
    emoji: "🎓",
    descricao:
      "Financiamento de C&T, formação de engenheiros e cientistas, programas de bolsas em áreas estratégicas, e retenção de talentos.",
    exemplo: "PEC que vincula 2% do PIB a investimentos em P&D",
  },
  {
    codigo: "ZIL-AGR",
    nome: "Agro-Indústria",
    emoji: "🌾",
    descricao:
      "Industrialização da produção agrícola: processamento, embalagem, logística e exportação de valor agregado em vez de commodities brutas.",
    exemplo: "PL sobre incentivos para frigoríficos exportadores de cortes processados",
  },
  {
    codigo: "ZIL-COM",
    nome: "Comércio e Indústria",
    emoji: "🏭",
    descricao:
      "Política industrial transversal: tarifas, compras governamentais, desindustrialização, reindustrialização e acordos comerciais com impacto produtivo.",
    exemplo: "PL que estabelece preferência nacional em licitações acima de R$50M",
  },
];

export default function MetodologiaPage() {
  return (
    <div className="max-w-5xl mx-auto px-6 py-12">
      {/* Header */}
      <div className="flex items-baseline gap-4 mb-2">
        <span className="font-display text-6xl text-zil-divider">M</span>
        <h1 className="font-display text-2xl uppercase tracking-wide">
          Metodologia
        </h1>
      </div>
      <p className="text-sm text-zil-soft mb-12 max-w-xl">
        Como o Score ZIL é calculado, o que as categorias representam e como as
        classificações são definidas.
      </p>

      {/* Score ZIL */}
      <section className="mb-14">
        <h2 className="font-display text-lg uppercase tracking-wide mb-4">
          O Score ZIL
        </h2>
        <div className="max-w-3xl space-y-4 text-sm text-zil-soft leading-relaxed">
          <p>
            O Score ZIL mede o alinhamento de cada parlamentar com a agenda de
            soberania industrial do Brasil, em uma escala de{" "}
            <strong className="text-zil-fg">-10 (contra) a +10 (a favor)</strong>.
          </p>
          <p>
            Ele é calculado a partir dos votos do parlamentar em votações que o
            comitê editorial classificou como relevantes para a soberania industrial.
            Cada votação tem um <em>peso</em> e uma <em>direção esperada</em> (sim ou
            não), definidos editorialmente.
          </p>
        </div>

        {/* Formula */}
        <div className="mt-6 bg-zil-card border border-zil-divider p-6 max-w-2xl">
          <p className="font-mono text-xs text-zil-muted mb-3">FÓRMULA</p>
          <p className="font-mono text-sm text-zil-fg">
            score = (Σ alinhamento_i × peso_i) / (Σ |peso_i|) × 10
          </p>
          <p className="font-mono text-xs text-zil-muted mt-4">
            alinhamento_i = +1 se votou na direção esperada, −1 se votou contra,
            0 se ausente
          </p>
        </div>

        {/* Weights */}
        <div className="mt-6 max-w-lg">
          <p className="font-mono text-xs text-zil-muted mb-3 uppercase tracking-wider">
            Pesos por tipo de votação
          </p>
          <table className="w-full text-sm border-collapse">
            <tbody>
              {[
                ["Plenário — votação final", "3.0"],
                ["Comissão — votação final", "2.0"],
                ["Votação padrão", "1.0"],
                ["Votação processual", "0.5"],
              ].map(([tipo, peso]) => (
                <tr key={tipo} className="border-b border-zil-divider">
                  <td className="py-2 text-zil-soft">{tipo}</td>
                  <td className="py-2 font-mono text-zil-fg text-right">{peso}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Scale */}
      <section className="mb-14">
        <h2 className="font-display text-lg uppercase tracking-wide mb-4">
          Escala do Score
        </h2>
        <div className="max-w-2xl">
          <div className="h-3 rounded-full bg-gradient-to-r from-zil-red via-zil-gold to-zil-green mb-3" />
          <div className="flex justify-between font-mono text-xs text-zil-muted">
            <span>-10 (contra)</span>
            <span>0 (neutro)</span>
            <span>+10 (a favor)</span>
          </div>
          <div className="mt-4 space-y-2 text-sm">
            {[
              { range: "+5 a +10", label: "Fortemente pró-soberania", color: "text-zil-green" },
              { range: "+2 a +5", label: "Majoritariamente favorável", color: "text-zil-green" },
              { range: "-2 a +2", label: "Neutro / misto", color: "text-zil-gold" },
              { range: "-5 a -2", label: "Majoritariamente contrário", color: "text-zil-orange" },
              { range: "-10 a -5", label: "Fortemente contra", color: "text-zil-red" },
            ].map((r) => (
              <div key={r.range} className="flex items-center gap-3">
                <span className={`font-mono text-xs w-20 ${r.color}`}>{r.range}</span>
                <span className="text-zil-soft">{r.label}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Limitations */}
      <section className="mb-14">
        <h2 className="font-display text-lg uppercase tracking-wide mb-4">
          Limitações
        </h2>
        <ul className="max-w-2xl space-y-3 text-sm text-zil-soft leading-relaxed list-none">
          {[
            "O score reflete apenas votações classificadas. Parlamentares com poucos votos em pautas ZIL têm scores menos representativos.",
            "A direção esperada de cada votação é uma decisão editorial — razoável pessoas podem discordar. Todas as decisões estão documentadas no repositório.",
            "O classificador automático de proposições usa palavras-chave, podendo incluir ou excluir proposições relevantes. A lista é revisada manualmente.",
            "Ausências e obstruções são contabilizadas como alinhamento 0 (neutro), não como voto contra.",
            "Dados do Senado Federal ainda não estão incluídos na v1.",
          ].map((item) => (
            <li key={item} className="flex gap-3">
              <span className="text-zil-divider mt-0.5">—</span>
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </section>

      {/* Categories */}
      <section className="mb-14">
        <h2 className="font-display text-lg uppercase tracking-wide mb-4">
          As 9 Categorias ZIL
        </h2>
        <div className="space-y-6">
          {CATEGORIAS.map((cat) => (
            <div
              key={cat.codigo}
              className="border-l-2 border-zil-divider pl-5"
            >
              <div className="flex items-center gap-2 mb-1">
                <span>{cat.emoji}</span>
                <span className="font-display text-sm uppercase tracking-wide">
                  {cat.nome}
                </span>
                <span className="font-mono text-xs text-zil-muted">{cat.codigo}</span>
              </div>
              <p className="text-sm text-zil-soft leading-relaxed mb-1">
                {cat.descricao}
              </p>
              <p className="text-xs font-mono text-zil-muted">
                Ex: {cat.exemplo}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Editorial process */}
      <section className="mb-14">
        <h2 className="font-display text-lg uppercase tracking-wide mb-4">
          Processo Editorial
        </h2>
        <div className="max-w-2xl space-y-4 text-sm text-zil-soft leading-relaxed">
          <p>
            As classificações são gerenciadas por um comitê editorial de
            voluntários via código aberto. Não há interface admin — todas as
            mudanças passam por Pull Request no GitHub.
          </p>
          <div className="space-y-3">
            {[
              {
                titulo: "Classificação automática",
                desc: "Keywords em data/taxonomia/categorias.yml determinam quais proposições são incluídas. Qualquer pessoa pode propor novas keywords via PR.",
              },
              {
                titulo: "Direção esperada",
                desc: "Para cada votação relevante, o comitê define se votar SIM ou NÃO é pró-soberania industrial. Requer 2 aprovações de maintainers + discussão no Discord.",
              },
              {
                titulo: "Bússola ZIL",
                desc: "Indicadores estratégicos em data/bussula/marcos.yml, atualizados trimestralmente com link para a fonte oficial.",
              },
            ].map((item) => (
              <div key={item.titulo} className="border border-zil-divider p-4">
                <p className="font-display text-sm uppercase tracking-wide mb-1">
                  {item.titulo}
                </p>
                <p>{item.desc}</p>
              </div>
            ))}
          </div>
          <p>
            <strong className="text-zil-fg">Princípio:</strong> na dúvida sobre
            a direção esperada de uma votação, não classificar.
          </p>
        </div>
      </section>

      {/* CTA */}
      <div className="border border-zil-divider p-6 max-w-2xl">
        <p className="font-display text-sm uppercase tracking-wide mb-2">
          Contribua com a metodologia
        </p>
        <p className="text-sm text-zil-soft mb-4">
          Encontrou uma proposição relevante que não está classificada? Discorde
          de uma direção esperada? Contribuições são bem-vindas.
        </p>
        <div className="flex gap-4">
          <Link
            href="https://github.com/melissa-pereira-deel/manifesto-zil"
            target="_blank"
            rel="noopener noreferrer"
            className="font-mono text-xs text-zil-green hover:underline"
          >
            GitHub ↗
          </Link>
          <Link
            href="/proposicoes"
            className="font-mono text-xs text-zil-green hover:underline"
          >
            Ver proposições classificadas →
          </Link>
        </div>
      </div>
    </div>
  );
}
