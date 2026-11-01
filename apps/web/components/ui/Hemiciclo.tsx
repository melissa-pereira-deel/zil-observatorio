/**
 * Hemiciclo — um ponto por cadeira, agrupado por voto (ZIL Interface ›
 * Hemiciclo). SVG puro: a posição de cada ponto é calculada aqui, sem
 * biblioteca.
 *
 * Os assentos chegam já na ordem em que devem aparecer, da esquerda para a
 * direita: o pai decide os grupos (`lib/votacao.ts` faz isso para uma
 * votação). Com `filtrado`, só os assentos `marcado` ficam acesos.
 */

export type TomAssento = "alinhado" | "contra" | "neutro" | "sim" | "nao" | "vazio";

export interface Assento {
  id: string;
  tom: TomAssento;
  /** Nome · partido · UF, mostrado ao passar o mouse. */
  titulo?: string;
  marcado?: boolean;
}

interface Ponto {
  x: number;
  y: number;
}

/** Raio da fileira mais interna, em fração do raio externo: o vão guarda o total. */
const RAIO_INTERNO = 0.36;
const CENTRO = 300;
const ESCALA = 288;

const cache = new Map<number, { pontos: Ponto[]; raio: number }>();

/**
 * Distribui `n` cadeiras em fileiras concêntricas. Cada fileira recebe
 * cadeiras na proporção do seu comprimento, e os pontos são ordenados por
 * ângulo — assim cada grupo vira uma fatia do semicírculo, e não uma faixa.
 */
export function layoutHemiciclo(n: number): { pontos: Ponto[]; raio: number } {
  const salvo = cache.get(n);
  if (salvo) return salvo;

  let fileiras = 2;
  let raios: number[] = [];
  let capacidades: number[] = [];
  let passo = 0;
  for (; fileiras < 40; fileiras++) {
    passo = (1 - RAIO_INTERNO) / (fileiras - 1);
    raios = Array.from({ length: fileiras }, (_, i) => RAIO_INTERNO + i * passo);
    capacidades = raios.map((r) => Math.floor((Math.PI * r) / passo) + 1);
    if (capacidades.reduce((a, b) => a + b, 0) >= n) break;
  }

  // Maiores restos: cadeiras por fileira proporcionais à capacidade.
  const total = capacidades.reduce((a, b) => a + b, 0);
  const cotas = capacidades.map((c) => (c * n) / total);
  const porFileira = cotas.map(Math.floor);
  let faltam = n - porFileira.reduce((a, b) => a + b, 0);
  cotas
    .map((c, i) => ({ i, resto: c - Math.floor(c) }))
    .sort((a, b) => b.resto - a.resto)
    .forEach(({ i }) => {
      if (faltam > 0 && porFileira[i] < capacidades[i]) {
        porFileira[i]++;
        faltam--;
      }
    });

  const angulares: { x: number; y: number; angulo: number; r: number }[] = [];
  porFileira.forEach((m, i) => {
    const r = raios[i];
    for (let j = 0; j < m; j++) {
      const angulo = m === 1 ? Math.PI / 2 : Math.PI * (1 - j / (m - 1));
      angulares.push({
        x: CENTRO + ESCALA * r * Math.cos(angulo),
        y: CENTRO - ESCALA * r * Math.sin(angulo),
        angulo,
        r,
      });
    }
  });
  angulares.sort((a, b) => b.angulo - a.angulo || a.r - b.r);

  const resultado = {
    pontos: angulares.map(({ x, y }) => ({ x: Math.round(x * 10) / 10, y: Math.round(y * 10) / 10 })),
    raio: Math.round(ESCALA * passo * 0.42 * 10) / 10,
  };
  cache.set(n, resultado);
  return resultado;
}

export function Hemiciclo({
  assentos,
  filtrado = false,
  numero,
  legendaNumero,
  rotulo,
  className = "",
}: {
  assentos: Assento[];
  /** Apaga os assentos que não estão `marcado`. */
  filtrado?: boolean;
  /** O número grande no vão do semicírculo. */
  numero: string;
  legendaNumero: string;
  /** Descrição para leitor de tela, com as contagens. */
  rotulo: string;
  className?: string;
}) {
  const { pontos, raio } = layoutHemiciclo(assentos.length);
  return (
    <div className={`zil-hemiciclo ${filtrado ? "is-filtrado" : ""} ${className}`}>
      <svg viewBox={`0 0 600 ${CENTRO + raio + 2}`} role="img" aria-label={rotulo}>
        {assentos.map((a, i) => (
          <circle
            key={a.id}
            cx={pontos[i].x}
            cy={pontos[i].y}
            r={raio}
            className={`${a.tom}${a.marcado ? " is-marcado" : ""}`}
          >
            {a.titulo && <title>{a.titulo}</title>}
          </circle>
        ))}
      </svg>
      <div className="zil-hemiciclo__total" aria-hidden="true">
        <b>{numero}</b>
        <span>{legendaNumero}</span>
      </div>
    </div>
  );
}
