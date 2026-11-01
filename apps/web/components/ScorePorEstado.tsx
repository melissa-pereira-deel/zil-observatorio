"use client";

import { Card, Histograma, Legenda, MapaUF, formatarScore, tomDoScore, type Faixa, type ValorUF } from "@/components/ui";
import type { Parlamentar } from "@/lib/api";

/**
 * O placar por estado e por faixa (ZIL Interface › Placar, "No plenário e
 * nos estados"). Só existe dentro do /ranking, que fica fechado enquanto
 * `rankingPublico` estiver desligado: é o Score ZIL agregado, e herda as
 * mesmas ressalvas do número individual.
 *
 * As cores seguem `tomDoScore` (±3), as mesmas da pílula de score — um
 * número tem uma cor só no site inteiro.
 */

const FAIXAS: [number, number][] = Array.from({ length: 10 }, (_, i) => [-10 + i * 2, -8 + i * 2]);

function rotuloFaixa([de, ate]: [number, number]): string {
  return `${formatarScore(de)} a ${formatarScore(ate)}`;
}

export function ScorePorEstado({
  parlamentares,
  uf,
  aoMudarUF,
}: {
  /** Todos os parlamentares da casa escolhida, sem filtro de UF ou partido. */
  parlamentares: Parlamentar[];
  uf: string;
  aoMudarUF: (uf: string) => void;
}) {
  const comScore = parlamentares.filter((p): p is Parlamentar & { score_zil: number } => p.score_zil !== null);

  const porUF: Record<string, { soma: number; n: number }> = {};
  for (const p of comScore) {
    if (!p.uf) continue;
    const u = (porUF[p.uf] ??= { soma: 0, n: 0 });
    u.soma += p.score_zil;
    u.n++;
  }
  const valores: Record<string, ValorUF> = {};
  for (const [sigla, { soma, n }] of Object.entries(porUF)) {
    const media = Math.round((soma / n) * 10) / 10;
    valores[sigla] = {
      valor: formatarScore(media),
      tom: tomDoScore(media),
      titulo: `${sigla}: score médio ${formatarScore(media)}, ${n} ${n === 1 ? "parlamentar" : "parlamentares"}`,
    };
  }

  const base = uf ? comScore.filter((p) => p.uf === uf) : comScore;
  const faixas: Faixa[] = FAIXAS.map((f, i) => ({
    rotulo: rotuloFaixa(f),
    // A última faixa fecha em +10; as outras são [de, ate).
    n: base.filter((p) => p.score_zil >= f[0] && (i === FAIXAS.length - 1 ? p.score_zil <= f[1] : p.score_zil < f[1])).length,
    destaque: !!uf,
  }));

  return (
    <section className="grid gap-4" aria-labelledby="estados-titulo">
      <div className="grid gap-1">
        <h2 id="estados-titulo" className="text-titulo-3">
          Nos estados e entre os parlamentares
        </h2>
        <p className="text-texto-s text-zil-texto-2">Toque num estado para filtrar o placar abaixo.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Card className="grid gap-4 content-start">
          <div className="grid gap-1">
            <h3 className="text-titulo-4">Score médio por estado</h3>
            <p className="text-texto-s text-zil-texto-2">
              {uf ? `Placar filtrado por ${uf} · toque de novo para tirar` : "Média dos parlamentares com score em cada estado"}
            </p>
          </div>
          <MapaUF valores={valores} selecionada={uf} aoSelecionar={aoMudarUF} rotulo="Score médio por estado" />
          <Legenda
            className="justify-center"
            itens={[
              { cor: "bg-zil-contra", rotulo: "−3 ou menos" },
              { cor: "bg-zil-neutro", rotulo: "entre −3 e +3" },
              { cor: "bg-zil-alinhado", rotulo: "+3 ou mais" },
              { cor: "bg-zil-superficie-2", rotulo: "sem dados" },
            ]}
          />
        </Card>
        <Card className="grid gap-4 content-start">
          <div className="grid gap-1">
            <h3 className="text-titulo-4">{uf ? `Em ${uf}` : "Entre os parlamentares"}</h3>
            <p className="text-texto-s text-zil-texto-2 zil-num">
              Quantos estão em cada faixa de score · {base.length} com score
            </p>
          </div>
          <Histograma faixas={faixas} eixo={["−10", "0", "+10"]} rotulo="Parlamentares por faixa de score" />
        </Card>
      </div>
    </section>
  );
}
