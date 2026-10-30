"use client";

import { useEffect, useLayoutEffect, useRef, useState } from "react";

/**
 * Segmentado — 2 a 4 opções exclusivas com um polegar que desliza com mola
 * (ZIL Interface › Segmentado). Para filtrar a mesma lista por um eixo.
 * Para trocar de conteúdo, use abas.
 *
 * Sem JavaScript o item ativo recebe o preenchimento direto; o polegar
 * animado só entra depois de montar.
 */

interface Opcao<T extends string> {
  valor: T;
  rotulo: string;
}

interface SegmentadoProps<T extends string> {
  opcoes: Opcao<T>[];
  valor: T;
  onMudar: (valor: T) => void;
  rotulo: string;
  bloco?: boolean;
  className?: string;
}

const useIsomorphicLayoutEffect = typeof window === "undefined" ? useEffect : useLayoutEffect;

export function Segmentado<T extends string>({ opcoes, valor, onMudar, rotulo, bloco = false, className = "" }: SegmentadoProps<T>) {
  const trilho = useRef<HTMLDivElement>(null);
  const [polegar, setPolegar] = useState<{ x: number; w: number } | null>(null);

  useIsomorphicLayoutEffect(() => {
    const raiz = trilho.current;
    if (!raiz) return;
    const medir = () => {
      const ativo = raiz.querySelector<HTMLButtonElement>('[aria-pressed="true"]');
      if (!ativo) return;
      setPolegar({ x: ativo.offsetLeft - 3, w: ativo.offsetWidth });
    };
    medir();
    const ro = new ResizeObserver(medir);
    ro.observe(raiz);
    return () => ro.disconnect();
  }, [valor, opcoes.length]);

  return (
    <div
      ref={trilho}
      role="group"
      aria-label={rotulo}
      className={`relative isolate inline-grid grid-flow-col auto-cols-fr p-[3px] rounded-pilula bg-zil-superficie-2 ${bloco ? "w-full" : ""} ${className}`}
    >
      {polegar && (
        <span
          aria-hidden="true"
          className="absolute -z-10 top-[3px] bottom-[3px] left-[3px] rounded-pilula bg-zil-polegar shadow-polegar transition-[transform,width] duration-padrao ease-mola"
          // Posição medida do item ativo: é estado, não estilo.
          style={{ transform: `translateX(${polegar.x}px)`, width: polegar.w }}
        />
      )}
      {opcoes.map((o) => {
        const ativo = o.valor === valor;
        return (
          <button
            key={o.valor}
            type="button"
            aria-pressed={ativo}
            onClick={() => onMudar(o.valor)}
            className={`h-[34px] px-4 rounded-pilula text-[15px] font-medium leading-none whitespace-nowrap transition-colors duration-toque ${
              ativo ? "text-zil-texto" : "text-zil-texto-2 hover:text-zil-texto"
            } ${ativo && !polegar ? "bg-zil-polegar shadow-polegar" : ""}`}
          >
            {o.rotulo}
          </button>
        );
      })}
    </div>
  );
}
