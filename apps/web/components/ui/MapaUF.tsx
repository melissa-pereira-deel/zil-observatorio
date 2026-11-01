import { GRADE_UF, UFS, type UF } from "@/lib/ufs";

/**
 * Mapa por UF — as 27 unidades numa grade que lembra o Brasil (ZIL
 * Interface › Mapa por UF). Cada estado é um botão: tocar filtra o que está
 * ao lado, tocar de novo tira o filtro. A cor nunca é a única pista: o
 * valor aparece escrito sob a sigla.
 */

export type TomUF = "alinhado" | "forte" | "contra" | "neutro" | "padrao" | "vazio";

export interface ValorUF {
  /** O que aparece sob a sigla: "+6,2", "94%". */
  valor: string;
  tom: TomUF;
  /** Frase completa, para o mouse e o leitor de tela. */
  titulo: string;
}

const TOM: Record<TomUF, string> = {
  alinhado: "bg-zil-alinhado-fundo text-zil-alinhado",
  forte: "bg-zil-alinhado text-zil-inverso-texto",
  contra: "bg-zil-contra-fundo text-zil-contra",
  neutro: "bg-zil-neutro-fundo text-zil-neutro",
  padrao: "bg-zil-superficie-3 text-zil-texto",
  vazio: "bg-zil-superficie-2 text-zil-texto-3",
};

export function MapaUF({
  valores,
  selecionada,
  aoSelecionar,
  rotulo,
  className = "",
}: {
  valores: Partial<Record<UF, ValorUF>>;
  selecionada?: string;
  /** Recebe a UF tocada, ou "" quando a selecionada é tocada de novo. */
  aoSelecionar?: (uf: string) => void;
  rotulo: string;
  className?: string;
}) {
  return (
    <div role="group" aria-label={rotulo} className={`grid grid-cols-7 gap-1.5 w-full max-w-[400px] justify-self-center ${className}`}>
      {UFS.map((uf) => {
        const v = valores[uf] ?? { valor: "—", tom: "vazio" as const, titulo: `${uf} · sem dados` };
        const ativa = selecionada === uf;
        const [coluna, linha] = GRADE_UF[uf];
        return (
          <button
            key={uf}
            type="button"
            aria-pressed={ativa}
            title={v.titulo}
            aria-label={v.titulo}
            onClick={() => aoSelecionar?.(ativa ? "" : uf)}
            // Posição na grade: é o mapa, não estilo.
            style={{ gridColumn: coluna, gridRow: linha }}
            className={[
              "relative aspect-square grid place-content-center gap-0.5 rounded-m text-center cursor-pointer select-none",
              "transition-[transform,box-shadow] duration-toque ease-padrao hover:scale-[1.08] hover:z-[2] hover:shadow-elevada active:scale-toque",
              ativa ? "shadow-[0_0_0_2px_var(--fundo),0_0_0_4px_var(--texto)] z-[1]" : "",
              TOM[v.tom],
            ].join(" ")}
          >
            <span className="text-[13px] leading-none font-semibold">{uf}</span>
            <small className="text-[11px] leading-none font-medium opacity-80 zil-num">{v.valor}</small>
          </button>
        );
      })}
    </div>
  );
}

/** Legenda de pontos coloridos (ZIL Interface › Legenda). */
export function Legenda({ itens, className = "" }: { itens: { cor: string; rotulo: string }[]; className?: string }) {
  return (
    <div className={`flex flex-wrap gap-x-4 gap-y-1.5 text-[14px] leading-5 font-medium text-zil-texto-2 ${className}`}>
      {itens.map((i) => (
        <span key={i.rotulo} className="inline-flex items-center gap-1.5">
          <i aria-hidden="true" className={`w-2 h-2 rounded-full ${i.cor}`} />
          {i.rotulo}
        </span>
      ))}
    </div>
  );
}
