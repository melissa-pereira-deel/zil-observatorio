import { Aviso, Card, Icone, Lista, Linha, Selo } from "@/components/ui";

/**
 * Explica o Score ZIL na home: a escala, o que cada voto vale, os pesos, a
 * fórmula (fechada por padrão, em <details> nativo) e as limitações.
 */

const PESOS = [
  { rotulo: "Votação final em plenário", peso: "3,0", barra: "w-full" },
  { rotulo: "Votação em comissão relevante", peso: "2,0", barra: "w-2/3" },
  { rotulo: "Votação padrão", peso: "1,0", barra: "w-1/3" },
  { rotulo: "Requerimento processual", peso: "0,5", barra: "w-1/6" },
];

const LIMITES = [
  "O score mede votação, não intenção.",
  "Ausências diluem o score, não punem.",
  "Trabalho de bastidor (negociações, articulações) não é capturado.",
  "É um subconjunto temático — não avalia o parlamentar inteiro.",
];

const ALINHAMENTOS: { valor: string; tom: "alinhado" | "contra" | "neutro"; desc: string }[] = [
  { valor: "+1,0", tom: "alinhado", desc: "Votou a favor da direção de soberania definida para a pauta." },
  { valor: "−1,0", tom: "contra", desc: "Votou contra a direção de soberania definida para a pauta." },
  { valor: "0,0", tom: "neutro", desc: "Ausente ou abstenção. Não pontua, mas o peso entra no denominador." },
];

/** Barra de peso: a largura é o valor do peso, já expressa em classe. */
function BarraPeso({ largura }: { largura: string }) {
  return (
    <span className="block mt-1.5 h-1.5 w-full max-w-[280px] rounded-pilula bg-zil-superficie-3 overflow-hidden">
      <span className={`block h-full rounded-pilula bg-zil-texto ${largura}`} />
    </span>
  );
}

export function ScoreExplainer() {
  return (
    <div className="grid gap-10 md:gap-12">
      {/* Escala */}
      <div className="grid gap-6">
        <p className="text-texto text-zil-texto-2 max-w-[60ch]">
          O Score mede como um parlamentar votou nas votações selecionadas como decisivas para a soberania industrial. A aritmética é
          pública e verificável; a escolha de quais votações entram, e de qual direção é pró-soberania, é um juízo editorial — assinado e
          auditável no repositório.
        </p>

        <div role="img" aria-label="Escala do score, de menos 10 contra a mais 10 a favor, com zero neutro no meio" className="max-w-2xl grid gap-2.5">
          <div className="grid grid-cols-[2fr_1fr_2fr] gap-[3px] h-2">
            <i className="rounded-pilula bg-zil-contra-fundo" />
            <i className="rounded-pilula bg-zil-neutro-fundo" />
            <i className="rounded-pilula bg-zil-alinhado-fundo" />
          </div>
          <div className="flex justify-between text-legenda text-zil-texto-2 zil-num">
            <span>
              <strong className="text-zil-contra">−10</strong> contra a soberania
            </span>
            <span>
              <strong className="text-zil-neutro">0</strong> neutro
            </span>
            <span>
              <strong className="text-zil-alinhado">+10</strong> a favor da soberania
            </span>
          </div>
        </div>
      </div>

      {/* O que cada voto vale */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6">
        {ALINHAMENTOS.map((a) => (
          <Card key={a.valor} compacto className="grid content-start gap-3">
            <Selo tom={a.tom} className="zil-num">
              {a.valor}
            </Selo>
            <p className="text-texto text-zil-texto-2">{a.desc}</p>
          </Card>
        ))}
      </div>

      {/* Pesos */}
      <div className="grid gap-4">
        <h3 className="text-titulo-4">Nem todo voto tem o mesmo peso.</h3>
        <Lista className="max-w-xl">
          {PESOS.map((p) => (
            <Linha
              key={p.rotulo}
              titulo={p.rotulo}
              sub={<BarraPeso largura={p.barra} />}
              fim={<span className="text-texto-ui text-zil-texto zil-num">{p.peso}</span>}
            />
          ))}
        </Lista>
      </div>

      {/* Fórmula completa: fechada por padrão, em <details> nativo (UI-012). */}
      <details className="group rounded-l bg-zil-superficie-1">
        <summary className="flex items-center justify-between gap-4 px-6 py-5 cursor-pointer select-none list-none [&::-webkit-details-marker]:hidden text-texto-ui">
          Ver fórmula completa
          <Icone nome="chevron-baixo" className="text-zil-texto-2 transition-transform duration-padrao ease-padrao group-open:rotate-180" />
        </summary>
        <div className="grid gap-6 px-6 pb-6">
          <p className="px-5 py-4 rounded-m bg-zil-superficie-2 text-center text-texto font-medium zil-num">
            Score = (&#931; alinhamento<sub>i</sub> &times; peso<sub>i</sub>) &divide; (&#931; |peso<sub>i</sub>|) &times; 10
          </p>

          <div className="grid gap-3">
            <p className="text-texto-ui">Exemplo prático: um deputado votou em 3 pautas ZIL.</p>
            <ul className="grid gap-2 list-none m-0 p-0">
              <li className="flex flex-wrap items-center gap-2 text-texto-s text-zil-texto-2 zil-num">
                <Selo tom="alinhado">A favor</Selo>
                Plenário (peso 3,0) = +1,0
              </li>
              <li className="flex flex-wrap items-center gap-2 text-texto-s text-zil-texto-2 zil-num">
                <Selo tom="neutro">Ausente</Selo>
                Comissão (peso 2,0) = 0,0
              </li>
              <li className="flex flex-wrap items-center gap-2 text-texto-s text-zil-texto-2 zil-num">
                <Selo tom="contra">Contra</Selo>
                Padrão (peso 1,0) = −1,0
              </li>
            </ul>
            <p className="px-5 py-4 rounded-m bg-zil-superficie-2 text-center text-texto-s text-zil-texto-2 zil-num">
              ((+1 &times; 3) + (0 &times; 2) + (−1 &times; 1)) &divide; (3 + 2 + 1) &times; 10 ={" "}
              <strong className="font-semibold text-zil-alinhado">+3,3</strong>
            </p>
          </div>
        </div>
      </details>

      {/* Limitações */}
      <Aviso tom="neutro" titulo="Limitações">
        <ul className="grid gap-1.5 mt-1 list-disc pl-5">
          {LIMITES.map((l) => (
            <li key={l}>{l}</li>
          ))}
        </ul>
      </Aviso>

      {/* Transparência */}
      <p className="text-titulo-3 max-w-[40ch] text-balance">
        Todo dado, algoritmo e classificação é público. Código aberto. Qualquer cidadão pode auditar.
      </p>
    </div>
  );
}
