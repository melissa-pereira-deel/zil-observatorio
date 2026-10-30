/**
 * Histograma — quantos itens caem em cada faixa (ZIL Interface › Gráfico,
 * barras). Barras neutras; a faixa em `destaque` acende. A contagem de cada
 * barra vai no `title` e no rótulo de acessibilidade.
 */

export interface Faixa {
  rotulo: string;
  n: number;
  destaque?: boolean;
}

export function Histograma({
  faixas,
  eixo,
  rotulo,
  className = "",
}: {
  faixas: Faixa[];
  /** Rótulos sob o eixo: início, meio e fim. */
  eixo: [string, string, string];
  rotulo: string;
  className?: string;
}) {
  const maximo = Math.max(1, ...faixas.map((f) => f.n));
  const largura = 500;
  const altura = 140;
  const vao = 6;
  const barra = (largura - vao * (faixas.length - 1)) / faixas.length;
  return (
    <div className={`zil-grafico ${className}`}>
      <svg viewBox={`0 0 ${largura} ${altura}`} role="img" aria-label={`${rotulo}: ${faixas.map((f) => `${f.rotulo}, ${f.n}`).join("; ")}`}>
        {faixas.map((f, i) => {
          // Barra com valor > 0 nunca some: mínimo de 4 unidades de altura.
          const h = f.n === 0 ? 0 : Math.max(4, (f.n / maximo) * (altura - 4));
          return (
            <rect
              key={f.rotulo}
              className={`barra${f.destaque ? " is-aqui" : ""}`}
              x={i * (barra + vao)}
              y={altura - h}
              width={barra}
              height={h}
              rx={Math.min(5, barra / 2)}
            >
              <title>{`${f.rotulo}: ${f.n}`}</title>
            </rect>
          );
        })}
      </svg>
      <div className="flex justify-between mt-2 text-[13px] leading-[18px] font-medium text-zil-texto-2 zil-num" aria-hidden="true">
        <span>{eixo[0]}</span>
        <span>{eixo[1]}</span>
        <span>{eixo[2]}</span>
      </div>
    </div>
  );
}
