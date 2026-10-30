import Link from "next/link";

import { Aviso, Button, Card, Chip, Chips, FAIXAS, Lista, Linha, Painel, Selo } from "@/components/ui";
import { CATEGORIA_COR } from "@/lib/categorias";
import { REPO_URL } from "@/lib/links";

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


// O critério que ordena as candidatas a classificação (`escore` em
// scripts/candidatas.py). O ADR-004 exige publicá-lo junto com o resultado.
const CRITERIO = [
  { termo: "Keyword forte da taxonomia", peso: "+8,0", mede: "A votação é sobre pauta ZIL de verdade" },
  { termo: "Só keyword fraca", peso: "−6,0", mede: "Sinal contrário: todo casamento fraco isolado que achamos era falso positivo" },
  { termo: "Direção indecidível", peso: "−12,0", mede: "Voto sobre emenda ou destaque: 'sim' aprova a emenda, e o texto dela não vem na API" },
  { termo: "Disputa", peso: "até +10,0", mede: "Quanto mais apertado o resultado, mais a votação separa parlamentares" },
  { termo: "Voto sobre o texto", peso: "+4,0", mede: "Substitutivo global ou o projeto inteiro" },
  { termo: "Pistas de plenário", peso: "+3,0", mede: "A API não distingue plenário de comissão; só o texto da descrição" },
  { termo: "Requerimento de urgência", peso: "−1,0", mede: "Nomeia o objeto, mas mede intenção de pautar, não posição sobre o mérito" },
  { termo: "Outro processual", peso: "−4,0", mede: "'Rejeitado o requerimento' não diz qual: sem saber o que se rejeitou, a direção é chute" },
];

const LIMITACOES = [
  "O score reflete apenas votações classificadas. Parlamentares com poucos votos em pautas ZIL têm scores menos representativos.",
  "A direção esperada de cada votação é uma decisão editorial — razoável pessoas podem discordar. Todas as decisões estão documentadas no repositório.",
  "O classificador de proposições usa palavras-chave fortes e fracas: só uma fraca não basta para incluir. Mesmo assim ele erra, e a lista é revisada manualmente.",
  "Ausências, abstenções, obstruções e o art. 17 contam alinhamento 0, mas o peso da votação entra no denominador: ausência dilui o score, não pune.",
  "Senadores e proposições do Senado estão no banco, mas nenhuma votação do Senado foi classificada. Por isso senadores não têm score.",
  "Todas as votações classificadas são matérias em que a posição pró-soberania é votar SIM. Não há, entre as votações com voto nominal de 2023–2026, uma matéria decidível em que ela seja votar NÃO — então o score mede alinhamento onde votar sim é o alinhamento, e nessa medida reflete também presença e disciplina partidária.",
];

const SECOES = [
  { id: "score", rotulo: "O Score ZIL" },
  { id: "selecao", rotulo: "Quais votações entram" },
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
          O placar mede alinhamento em votações escolhidas. Aqui está como escolhemos, como contamos e onde o método falha.
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
        <p className="text-texto-s text-zil-texto-2 zil-num">Hoje: 6 votações com peso 3,0 e 1 com peso 2,0.</p>
      </section>

      {/* ── Quais votações entram (ADR-004: o critério é publicado com o resultado) ── */}
      <section id="selecao" className="zil-secao scroll-mt-20 grid gap-8">
        <h2 className="text-titulo-2">Quais votações entram</h2>
        <div className="zil-leitura">
          <p>
            A v1 é um <strong>placar focado</strong>: como cada parlamentar votou nas cerca de dez votações que mais importaram para a
            soberania industrial, e não um índice de toda a atuação. Hoje são 7 classificadas, 4 delas com voto nominal.
          </p>
          <p>
            Num placar focado, a escolha das votações é a decisão editorial mais carregada do projeto. Por isso o critério que ordena as
            candidatas é público e está no código. Ele mede <strong>saliência, nunca mérito</strong>: diz onde vale gastar pesquisa, não
            qual é a direção.
          </p>
        </div>
        <Lista titulo="O que ordena as candidatas" className="max-w-3xl">
          {CRITERIO.map((c) => (
            <Linha key={c.termo} titulo={c.termo} sub={c.mede} fim={<span className="text-texto-ui text-zil-texto zil-num whitespace-nowrap">{c.peso}</span>} />
          ))}
        </Lista>
        <div className="zil-leitura">
          <p>
            A seleção final e a direção esperada são decisões humanas, com justificativa escrita em arquivo versionado. Votação simbólica
            não entra no score, com ou sem classificação: a Câmara proclama só o resultado e não registra quem votou o quê. Entre 2023 e 2026,
            86% das votações foram simbólicas.
          </p>
        </div>
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
            proposições reais em tramitação. As proposições de verdade estão em <Link href="/proposicoes">Proposições</Link>. Com o placar
            focado em cerca de dez votações, o papel das nove categorias no score está em revisão; mudar a taxonomia exige uma RFC.
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
          processo com duas aprovações que nunca foi praticado; isso está registrado e corrigido em <code className="zil-caminho">docs/GOVERNANCE.md</code> em vez de mantido
          como promessa.
        </Aviso>

        {/* Três colunas só a partir de lg: entre 768 e 1024px cada cartão ficava
            com ~200px, estreito demais para texto de 18px. */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 md:gap-6">
          <Card className="grid content-start gap-2">
            <h3 className="text-titulo-4">Classificação automática</h3>
            <p className="text-texto text-zil-texto-2">
              Keywords em <code className="zil-caminho">data/taxonomia/categorias.yml</code> determinam quais proposições são incluídas. As keywords são versionadas em git, então
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
              Quatro indicadores, em formação, em <code className="zil-caminho">data/bussula/marcos.yml</code>. Nenhum passou por revisão e nenhuma meta tem plano oficial
              como origem; a página mostra isso em cada cartão. Cada atualização entra por PR com link para a fonte, a cada trimestre
              ou quando sai dado novo.
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
            <Button href={REPO_URL} target="_blank" rel="noopener noreferrer" variante="secundario">
              Abrir o repositório no GitHub
            </Button>
          </div>
        </Painel>
      </section>
    </div>
  );
}
