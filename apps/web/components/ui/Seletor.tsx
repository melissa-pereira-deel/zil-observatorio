"use client";

import { type ComponentPropsWithoutRef } from "react";

import { Icone } from "./Icone";

/**
 * Seletor — `<select>` nativo vestido de pílula fantasma, para ordenação e
 * filtros com muitas opções (UF, partido). Substitui o menu em vidro do
 * sistema onde a lista é longa demais para chips.
 */

interface SeletorProps extends Omit<ComponentPropsWithoutRef<"select">, "onChange" | "value"> {
  valor: string;
  onMudar: (valor: string) => void;
  rotulo: string;
  opcoes: { valor: string; rotulo: string }[];
  /** Texto da opção vazia ("Todas as UFs"). */
  vazio?: string;
  variante?: "fantasma" | "superficie";
  className?: string;
}

export function Seletor({ valor, onMudar, rotulo, opcoes, vazio, variante = "superficie", className = "", ...props }: SeletorProps) {
  return (
    <label
      className={`relative inline-flex items-center h-9 rounded-pilula text-[15px] font-medium transition-colors duration-toque ${
        variante === "fantasma" ? "bg-transparent hover:bg-zil-superficie-2" : "bg-zil-superficie-2 hover:bg-zil-superficie-3"
      } ${valor ? "text-zil-texto" : "text-zil-texto-2"} ${className}`}
    >
      <select
        value={valor}
        onChange={(e) => onMudar(e.target.value)}
        aria-label={rotulo}
        className="appearance-none h-full pl-3.5 pr-8 bg-transparent border-0 outline-none text-inherit cursor-pointer"
        {...props}
      >
        {vazio !== undefined && <option value="">{vazio}</option>}
        {opcoes.map((o) => (
          <option key={o.valor} value={o.valor}>
            {o.rotulo}
          </option>
        ))}
      </select>
      <Icone nome="chevron-baixo" tamanho="s" className="pointer-events-none absolute right-2.5" />
    </label>
  );
}
