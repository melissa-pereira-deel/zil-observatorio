"use client";

import { useState } from "react";
import { Badge, Card, Callout } from "@/components/ui";

const WEIGHTS = [
  { label: "Votação final em plenário", weight: 3.0, bar: "w-full" },
  { label: "Votação em comissão relevante", weight: 2.0, bar: "w-2/3" },
  { label: "Votação padrão", weight: 1.0, bar: "w-1/3" },
  { label: "Requerimento processual", weight: 0.5, bar: "w-1/6" },
];

const LIMITS = [
  "O score mede votação, não intenção.",
  "Ausências diluem o score, não punem.",
  "Trabalho de bastidor (negociações, articulações) não é capturado.",
  "É um subconjunto temático — não avalia o parlamentar inteiro.",
];

export function ScoreExplainer() {
  const [formulaOpen, setFormulaOpen] = useState(false);

  return (
    <div className="space-y-8 md:space-y-10">
      {/* Scale visual */}
      <div>
        <p className="text-sm md:text-base text-zil-soft leading-relaxed max-w-3xl mb-6">
          O Score mede como cada parlamentar vota nas pautas que determinam a
          soberania industrial do Brasil. Não é opinião — é matemática aplicada a
          dados públicos.
        </p>

        <div className="max-w-2xl">
          {/* Gradient bar */}
          <div className="relative h-3 md:h-4 rounded-full bg-gradient-to-r from-zil-red via-zil-gold to-zil-green overflow-hidden" />

          {/* Labels */}
          <div className="flex justify-between mt-2">
            <div className="text-left">
              <span className="font-display text-sm md:text-base text-zil-red">
                -10
              </span>
              <p className="text-2xs md:text-xs text-zil-muted mt-0.5">
                Contra a soberania
              </p>
            </div>
            <div className="text-center">
              <span className="font-display text-sm md:text-base text-zil-gold-dark">
                0
              </span>
              <p className="text-2xs md:text-xs text-zil-muted mt-0.5">
                Neutro
              </p>
            </div>
            <div className="text-right">
              <span className="font-display text-sm md:text-base text-zil-green">
                +10
              </span>
              <p className="text-2xs md:text-xs text-zil-muted mt-0.5">
                A favor da soberania
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Alignment cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 md:gap-4">
        <div className="flex items-start gap-3 p-4 border border-zil-green/20 bg-zil-green-light/50">
          <div className="w-3 h-3 rounded-full bg-zil-green mt-0.5 shrink-0" />
          <div>
            <div className="font-display text-sm text-zil-green">+1.0</div>
            <p className="text-xs text-zil-soft mt-1 leading-relaxed">
              Votou a favor da direção de soberania definida para a pauta.
            </p>
          </div>
        </div>

        <div className="flex items-start gap-3 p-4 border border-zil-red/20 bg-zil-orange-light/50">
          <div className="w-3 h-3 rounded-full bg-zil-red mt-0.5 shrink-0" />
          <div>
            <div className="font-display text-sm text-zil-red">-1.0</div>
            <p className="text-xs text-zil-soft mt-1 leading-relaxed">
              Votou contra a direção de soberania definida para a pauta.
            </p>
          </div>
        </div>

        <div className="flex items-start gap-3 p-4 border border-zil-gold/20 bg-zil-gold-light/50">
          <div className="w-3 h-3 rounded-full bg-zil-gold mt-0.5 shrink-0" />
          <div>
            <div className="font-display text-sm text-zil-gold-dark">0.0</div>
            <p className="text-xs text-zil-soft mt-1 leading-relaxed">
              Ausente ou abstenção. Não pontua, mas o peso entra no denominador.
            </p>
          </div>
        </div>
      </div>

      {/* Weights */}
      <div>
        <h3 className="font-semibold text-sm md:text-base mb-4">
          Nem todo voto tem o mesmo peso.
        </h3>
        <div className="space-y-3 max-w-xl">
          {WEIGHTS.map((w) => (
            <div key={w.label} className="flex items-center gap-4">
              <Badge variant="outline" className="shrink-0 min-w-[3rem] justify-center">
                {w.weight.toFixed(1)}
              </Badge>
              <div className="flex-1 min-w-0">
                <div className="text-xs md:text-sm text-zil-fg mb-1">
                  {w.label}
                </div>
                <div className="h-1.5 bg-zil-divider rounded-full overflow-hidden">
                  <div
                    className={`h-full bg-zil-green rounded-full ${w.bar}`}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Collapsible formula */}
      <div className="border border-zil-divider">
        <button
          onClick={() => setFormulaOpen(!formulaOpen)}
          className="w-full flex items-center justify-between p-4 text-left hover:bg-zil-card transition-colors"
        >
          <span className="font-mono text-xs tracking-wider text-zil-soft uppercase">
            Ver fórmula completa
          </span>
          <span
            className={`text-zil-muted transition-transform duration-200 ${
              formulaOpen ? "rotate-180" : ""
            }`}
          >
            &#9662;
          </span>
        </button>

        {formulaOpen && (
          <div className="px-4 pb-4 border-t border-zil-divider pt-4 space-y-4 animate-fade-in">
            <div className="bg-zil-card p-4 font-mono text-sm md:text-base text-center">
              Score = (&#931; alinhamento<sub>i</sub> &times; peso<sub>i</sub>)
              &divide; (&#931; |peso<sub>i</sub>|) &times; 10
            </div>

            <div>
              <p className="text-xs font-semibold text-zil-fg mb-2">
                Exemplo prático:
              </p>
              <div className="space-y-1.5 text-xs text-zil-soft">
                <p>
                  Um deputado votou em 3 pautas ZIL:
                </p>
                <ul className="space-y-1 ml-4">
                  <li className="flex gap-2">
                    <span className="text-zil-green">&#8226;</span>
                    <span>
                      Plenário (peso 3.0): votou <strong className="text-zil-green">A FAVOR</strong> = +1.0
                    </span>
                  </li>
                  <li className="flex gap-2">
                    <span className="text-zil-gold">&#8226;</span>
                    <span>
                      Comissão (peso 2.0): <strong className="text-zil-gold-dark">AUSENTE</strong> = 0.0
                    </span>
                  </li>
                  <li className="flex gap-2">
                    <span className="text-zil-red">&#8226;</span>
                    <span>
                      Padrão (peso 1.0): votou <strong className="text-zil-red">CONTRA</strong> = -1.0
                    </span>
                  </li>
                </ul>
                <div className="bg-zil-white p-3 font-mono text-center mt-3 border border-zil-divider">
                  ((+1&times;3) + (0&times;2) + (-1&times;1)) &divide; (3+2+1) &times; 10
                  = <strong className="text-zil-green">+3.3</strong>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Limitations */}
      <Card accent="gold" className="bg-zil-card">
        <p className="font-mono text-2xs tracking-wider text-zil-muted uppercase mb-3">
          Limitações
        </p>
        <ul className="space-y-2">
          {LIMITS.map((l) => (
            <li key={l} className="flex gap-2 text-xs md:text-sm text-zil-soft leading-relaxed">
              <span className="text-zil-gold mt-0.5 shrink-0">&#9670;</span>
              {l}
            </li>
          ))}
        </ul>
      </Card>

      {/* Transparency callout */}
      <Callout variant="dark">
        <p className="font-display text-sm md:text-base uppercase tracking-wide leading-snug">
          Todo dado, algoritmo e classificação é público.{" "}
          <span className="text-zil-gold">Código aberto.</span> Qualquer cidadão
          pode auditar.
        </p>
      </Callout>
    </div>
  );
}
