import Link from "next/link";

import { Aviso, Button, Card, Chip, Chips, Lista, Linha, Painel, Selo } from "@/components/ui";
import { CATEGORIA_COR } from "@/lib/categorias";

/**
 * Metodologia: leitura longa (.zil-leitura), com os números do
 * score em Lista/Card tabulares e os avisos sobre validação em Aviso neutro.
 */

const CATEGORIAS = [
  {
    codigo: "ZIL-FER",
    nome: "Fertilizantes",
    descricao:
      "Proposições sobre produção nacional de insumos agrícolas, redução da dependência de ureia, fosfato e potássio importados, e política de estoques estratégicos.",
    exemplo: "PL que cria reservas estratégicas de fertilizantes nitrogenados",
  },
  {
    codigo: "ZIL-MIN",
    nome: "Minerais Estratégicos",
    descricao:
      "Regras para mineração, exportação e beneficiamento de nióbio, lítio, terras-raras e outros minerais críticos para cadeias tecnológicas.",
    exemplo: "PEC que exige processamento mínimo antes da exportação de nióbio",
  },
  {
    codigo: "ZIL-SEM",
    nome: "Semicondutores",
    descricao:
      "Política industrial para chips, eletrônica e equipamentos de telecomunicação. Inclui incentivos para fabricação local e compras governamentais.",
    exemplo: "MP que cria crédito tributário para fabricantes nacionais de chips",
  },
  {
    codigo: "ZIL-ENE",
    nome: "Energia",
    descricao:
      "Soberania energética: petróleo, gás, renováveis, redes de transmissão. Foco em capacidade nacional de produção e refino.",
    exemplo: "PL sobre obrigatoriedade de refino nacional do petróleo do pré-sal",
  },
  {
    codigo: "ZIL-DIG",
    nome: "Soberania Digital",
    descricao:
      "Infraestrutura de internet, data centers, software de base, cabos submarinos, computação em nuvem e proteção de dados estratégicos.",
    exemplo: "PDL sobre armazenamento obrigatório de dados governamentais em servidores nacionais",
  },
  {
    codigo: "ZIL-DEF",
    nome: "Defesa e Segurança",
    descricao:
      "Base industrial de defesa, compras governamentais com transferência tecnológica, satélites e sistemas de comunicação estratégicos.",
    exemplo: "PL que exige componentes nacionais em 60% dos equipamentos militares",
  },
  {
    codigo: "ZIL-EDU",
    nome: "Capital Humano",
    descricao:
      "Financiamento de C&T, formação de engenheiros e cientistas, programas de bolsas em áreas estratégicas, e retenção de talentos.",
    exemplo: "PEC que vincula 2% do PIB a investimentos em P&D",
  },
  {
    codigo: "ZIL-AGR",
    nome: "Agro-Indústria",
    descricao:
      "Industrialização da produção agrícola: processamento, embalagem, logística e exportação de valor agregado em vez de commodities brutas.",
    exemplo: "PL sobre incentivos para frigoríficos exportadores de cortes processados",
  },
  {
    codigo: "ZIL-COM",
    nome: "Comércio e Indústria",
    descricao:
      "Política industrial transversal: tarifas, compras governamentais, desindustrialização, reindustrialização e acordos comerciais com impacto produtivo.",
    exemplo: "PL que estabelece preferência nacional em licitações acima de R$50M",
  },
];

const PESOS = [
  ["Plenário — votação final", "3,0"],
  ["Comissão — votação final", "2,0"],
  ["Votação padrão", "1,0"],
  ["Votação processual", "0,5"],
];

const FAIXAS: { faixa: string; rotulo: string; tom: "alinhado" | "contra" | "neutro" }[] = [
  { faixa: "+5 a +10", rotulo: "Fortemente pró-soberania", tom: "alinhado" },
  { faixa: "+2 a +5", rotulo: "Majoritariamente favorável", tom: "alinhado" },
  { faixa: "−2 a +2", rotulo: "Neutro / misto", tom: "neutro" },
  { faixa: "−5 a −2", rotulo: "Majoritariamente contrário", tom: "contra" },
  { faixa: "−10 a −5", rotulo: "Fortemente contra", tom: "contra" },
];

const LIMITACOES = [
  "O score reflete apenas votações classificadas. Parlamentares com poucos votos em pautas ZIL têm scores menos representativos.",
  "A direção esperada de cada votação é uma decisão editorial — razoável pessoas podem discordar. Todas as decisões estão documentadas no repositório.",
  "O classificador automático de proposições usa palavras-chave, podendo incluir ou excluir proposições relevantes. A lista é revisada manualmente.",
  "Ausências e obstruções são contabilizadas como alinhamento 0 (neutro), não como voto contra.",
  "Dados do Senado Federal ainda não estão incluídos na v1.",
  "Todas as votações classificadas são matérias em que a posição pró-soberania é votar SIM. Não há, entre as votações com voto nominal de 2023–2026, uma matéria decidível em que ela seja votar NÃO — então o score mede alinhamento onde votar sim é o alinhamento, e nessa medida reflete também presença e disciplina partidária.",
];

const SECOES = [
  { id: "score", rotulo: "O Score ZIL" },
  { id: "escala", rotulo: "Escala" },
  { id: "limitacoes", rotulo: "Limitações" },
  { id: "categorias", rotulo: "Categorias" },
  { id: "processo", rotulo: "Processo editorial" },
];

export default function MetodologiaPage() {
  return (
    <div className="zil-container">
      <header className="pt-10 md:pt-16 grid gap-4">
        <p className="text-rotulo uppercase text-zil-texto-2">Metodologia</p>
        <h1 className="text-titulo-1 md:text-display-m">Como o Score ZIL é calculado</h1>
        <p className="text-texto-l text-zil-texto-2 max-w-[60ch]">
          Como o Score ZIL é calculado, o que as categorias representam e como as classificações são definidas.
        </p>
        <Chips rolagem className="mt-4">
          {SECOES.map((s) => (
            <Chip key={s.id} href={`#${s.id}`} tamanho="s">
              {s.rotulo}
            </Chip>
          ))}
        </Chips>
      </header>

      {/* ── O Score ZIL ── */}
      <section id="score" className="zil-secao scroll-mt-20 grid gap-8">
        <h2 className="text-titulo-2">O Score ZIL</h2>
        <div className="zil-leitura">
          <p>
            O Score ZIL mede como um parlamentar votou num <strong>conjunto selecionado de votações</strong> decisivas para a soberania
            industrial, numa escala de <strong>−10 (contra) a +10 (a favor)</strong>.
          </p>
          <p>
            <strong>Não é um índice de toda a atuação parlamentar.</strong> É um placar de pautas escolhidas — o que significa que a escolha
            das pautas importa tanto quanto a aritmética. Cada votação tem um <em>peso</em> e uma <em>direção esperada</em> (sim ou não),
            definidos editorialmente e registrados em arquivo versionado.
          </p>
        </div>

        <Card className="max-w-2xl grid gap-3">
          <span className="text-rotulo uppercase text-zil-texto-2">Fórmula</span>
          <p className="text-texto font-medium zil-num">score = (Σ alinhamento_i × peso_i) / (Σ |peso_i|) × 10</p>
          <p className="text-texto-s text-zil-texto-2 zil-num">alinhamento_i = +1 se votou na direção esperada, −1 se votou contra, 0 se ausente</p>
        </Card>

        <Lista titulo="Pesos por tipo de votação" className="max-w-lg">
          {PESOS.map(([tipo, peso]) => (
            <Linha key={tipo} titulo={tipo} fim={<span className="text-texto-ui text-zil-texto zil-num">{peso}</span>} />
          ))}
        </Lista>
      </section>

      {/* ── Escala ── */}
      <section id="escala" className="zil-secao scroll-mt-20 grid gap-8">
        <h2 className="text-titulo-2">Escala do Score</h2>
        <div role="img" aria-label="Escala do score, de menos 10 contra a mais 10 a favor, com zero neutro no meio" className="max-w-2xl grid gap-2.5">
          <div className="grid grid-cols-[2fr_1fr_2fr] gap-[3px] h-2">
            <i className="rounded-pilula bg-zil-contra-fundo" />
            <i className="rounded-pilula bg-zil-neutro-fundo" />
            <i className="rounded-pilula bg-zil-alinhado-fundo" />
          </div>
          <div className="flex justify-between text-legenda text-zil-texto-2 zil-num">
            <span>−10 (contra)</span>
            <span>0 (neutro)</span>
            <span>+10 (a favor)</span>
          </div>
        </div>
        <Lista className="max-w-2xl">
          {FAIXAS.map((f) => (
            <Linha
              key={f.faixa}
              icone={<span aria-hidden="true" className={`w-2.5 h-2.5 rounded-full ${f.tom === "alinhado" ? "bg-zil-alinhado" : f.tom === "contra" ? "bg-zil-contra" : "bg-zil-neutro"}`} />}
              titulo={f.rotulo}
              fim={
                <Selo tom={f.tom} className="zil-num">
                  {f.faixa}
                </Selo>
              }
            />
          ))}
        </Lista>
      </section>

      {/* ── Limitações ── */}
      <section id="limitacoes" className="zil-secao scroll-mt-20 grid gap-8">
        <h2 className="text-titulo-2">Limitações</h2>
        <ul className="zil-leitura grid gap-4 list-disc pl-6">
          {LIMITACOES.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      {/* ── Categorias ── */}
      <section id="categorias" className="zil-secao scroll-mt-20 grid gap-8">
        <h2 className="text-titulo-2">As 9 Categorias ZIL</h2>
        <div className="zil-leitura">
          <p>
            Os exemplos abaixo são <strong>hipotéticos</strong>, escritos para ilustrar o tipo de matéria que cada categoria abrange — não são
            proposições reais em tramitação. As proposições de verdade estão em <Link href="/proposicoes">Proposições</Link>.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
          {CATEGORIAS.map((cat) => (
            <Card key={cat.codigo} className="grid content-start gap-3">
              <div className="flex items-center gap-2.5">
                <span aria-hidden="true" className={`w-2.5 h-2.5 rounded-full shrink-0 ${CATEGORIA_COR[cat.codigo] ?? "bg-zil-texto-3"}`} />
                <h3 className="text-titulo-4">{cat.nome}</h3>
                {/* O código é o nome da categoria em data/taxonomia/categorias.yml. */}
                <span className="ml-auto text-legenda text-zil-texto-2 zil-num">{cat.codigo}</span>
              </div>
              <p className="text-texto text-zil-texto-2">{cat.descricao}</p>
              <p className="text-texto-s text-zil-texto-2">Exemplo hipotético: {cat.exemplo}</p>
            </Card>
          ))}
        </div>
      </section>

      {/* ── Processo editorial ── */}
      <section id="processo" className="zil-secao scroll-mt-20 grid gap-8">
        <h2 className="text-titulo-2">Processo Editorial</h2>
        <div className="zil-leitura">
          <p>
            As classificações são gerenciadas via código, sem interface admin — toda mudança passa por Pull Request e fica registrada no
            histórico do repositório.
          </p>
        </div>

        <Aviso tom="neutro" titulo="Quantas pessoas revisam: uma" className="max-w-leitura">
          O projeto tem hoje um único maintainer, e não há revisão editorial independente. Nossos documentos de governança descrevem um
          processo com duas aprovações que nunca foi praticado; isso está registrado e corrigido em docs/GOVERNANCE.md em vez de mantido
          como promessa.
        </Aviso>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6">
          <Card className="grid content-start gap-2">
            <h3 className="text-titulo-4">Classificação automática</h3>
            <p className="text-texto text-zil-texto-2">
              Keywords em data/taxonomia/categorias.yml determinam quais proposições são incluídas. As keywords são versionadas em git, então
              toda inclusão e exclusão é rastreável.
            </p>
          </Card>
          <Card className="grid content-start gap-2">
            <h3 className="text-titulo-4">Direção esperada</h3>
            <p className="text-texto text-zil-texto-2">
              Para cada votação relevante, define-se se votar SIM ou NÃO é pró-soberania industrial, com justificativa escrita.
            </p>
          </Card>
          <Card className="grid content-start gap-2">
            <h3 className="text-titulo-4">Bússola ZIL</h3>
            <p className="text-texto text-zil-texto-2">
              Indicadores estratégicos em data/bussula/marcos.yml, atualizados trimestralmente com link para a fonte oficial.
            </p>
          </Card>
        </div>

        <Aviso tom="neutro" titulo="As 7 classificações existentes ainda não foram validadas" className="max-w-leitura">
          Estão marcadas como não validadas nos próprios arquivos: foram criadas num único dia, por uma pessoa, e ainda não passaram por
          revisão. Dessas 7, só 4 alimentam o score — as outras três foram decididas por votação simbólica, em que a Câmara proclama apenas o
          resultado e não registra o voto individual de cada deputado.
        </Aviso>

        <div className="zil-leitura">
          <p>
            <strong>Princípio:</strong> na dúvida sobre a direção esperada de uma votação, não classificar.
          </p>
        </div>
      </section>

      {/* ── Contribuir ── */}
      <section className="zil-secao pt-0">
        <Painel>
          <h2 className="text-titulo-2">Contribua com a metodologia</h2>
          <p className="text-texto text-zil-texto-2 max-w-[52ch]">
            Encontrou uma proposição relevante que não está classificada? Discorde de uma direção esperada? Contribuições são bem-vindas.
          </p>
          <div className="flex flex-wrap justify-center gap-3 mt-2">
            <Button href="/proposicoes" variante="primario">
              Ver proposições classificadas
            </Button>
            <Button href="https://github.com/melissa-pereira-deel/zil-observatorio" target="_blank" rel="noopener noreferrer" variante="secundario">
              Abrir o repositório no GitHub
            </Button>
          </div>
        </Painel>
      </section>
    </div>
  );
}
