"use client";

import { Icone } from "./Icone";

/**
 * Paginação — páginas numa cápsula `superficie-2`, página atual invertida
 * e resumo do intervalo (ZIL Interface › Paginação). Mostra primeira,
 * última e vizinhas da atual; o resto vira "…".
 */

interface PaginacaoProps {
  atual: number;
  total: number;
  onMudar: (pagina: number) => void;
  /** "Mostrando 1–20 de 513" */
  resumo?: string;
  className?: string;
}

function paginas(atual: number, total: number): (number | "…")[] {
  const s = new Set<number>([1, total]);
  for (let i = Math.max(1, atual - 1); i <= Math.min(total, atual + 1); i++) s.add(i);
  const ordenadas = Array.from(s).sort((a, b) => a - b);
  const out: (number | "…")[] = [];
  let anterior = 0;
  for (const n of ordenadas) {
    if (n - anterior > 1) out.push("…");
    out.push(n);
    anterior = n;
  }
  return out;
}

export function Paginacao({ atual, total, onMudar, resumo, className = "" }: PaginacaoProps) {
  if (total <= 1) return resumo ? <p className={`text-texto-s text-zil-texto-2 zil-num ${className}`}>{resumo}</p> : null;
  const botao =
    "inline-grid place-items-center min-w-9 h-9 px-2.5 rounded-pilula text-[15px] font-medium leading-none zil-num transition-[background-color,color,transform] duration-toque hover:bg-zil-superficie-3 active:scale-[.94] disabled:text-zil-texto-3 disabled:pointer-events-none";
  return (
    <nav aria-label="Paginação" className={`flex flex-wrap items-center justify-between gap-3 ${className}`}>
      {resumo && <span className="text-texto-s text-zil-texto-2 zil-num">{resumo}</span>}
      <div className="flex items-center gap-0.5 p-[3px] rounded-pilula bg-zil-superficie-2">
        <button type="button" aria-label="Página anterior" disabled={atual <= 1} onClick={() => onMudar(atual - 1)} className={botao}>
          <Icone nome="chevron-esquerda" tamanho="s" />
        </button>
        {paginas(atual, total).map((p, i) =>
          p === "…" ? (
            <span key={`e${i}`} className="min-w-6 text-center text-zil-texto-3">
              …
            </span>
          ) : (
            <button
              key={p}
              type="button"
              aria-current={p === atual ? "page" : undefined}
              onClick={() => onMudar(p)}
              className={`${botao} ${p === atual ? "bg-zil-inverso text-zil-inverso-texto hover:bg-zil-inverso" : ""}`}
            >
              {p}
            </button>
          )
        )}
        <button type="button" aria-label="Próxima página" disabled={atual >= total} onClick={() => onMudar(atual + 1)} className={botao}>
          <Icone nome="chevron-direita" tamanho="s" />
        </button>
      </div>
    </nav>
  );
}
