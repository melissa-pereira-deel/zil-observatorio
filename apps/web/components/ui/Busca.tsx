"use client";

import { type ComponentPropsWithoutRef } from "react";

import { Icone } from "./Icone";

/**
 * Busca — campo em pílula com ícone, botão de limpar que surge com mola e
 * halo de foco (ZIL Interface › Busca).
 *
 * O placeholder diz o que dá para buscar: "Buscar parlamentar, partido ou UF".
 */

interface BuscaProps extends Omit<ComponentPropsWithoutRef<"input">, "onChange" | "value" | "type"> {
  valor: string;
  onMudar: (valor: string) => void;
  rotulo: string;
  className?: string;
}

export function Busca({ valor, onMudar, rotulo, placeholder, className = "", ...props }: BuscaProps) {
  return (
    <label
      className={`group relative flex items-center gap-2.5 h-11 pl-4 pr-2 rounded-pilula bg-zil-superficie-2 text-zil-texto-2 transition-[background-color,box-shadow] duration-padrao ease-padrao hover:bg-zil-superficie-3 focus-within:bg-zil-superficie-1 focus-within:shadow-halo focus-within:text-zil-texto ${className}`}
    >
      <Icone nome="busca" />
      <input
        type="search"
        value={valor}
        onChange={(e) => onMudar(e.target.value)}
        placeholder={placeholder}
        aria-label={rotulo}
        autoComplete="off"
        className="peer flex-1 min-w-0 h-full bg-transparent border-0 outline-none text-zil-texto text-[16px] placeholder:text-zil-texto-3"
        {...props}
      />
      <button
        type="button"
        aria-label="Limpar busca"
        onClick={() => onMudar("")}
        className="grid place-items-center w-7 h-7 rounded-full bg-zil-superficie-4 text-zil-texto opacity-0 scale-[.6] pointer-events-none transition-[opacity,transform] duration-padrao ease-mola peer-[:not(:placeholder-shown)]:opacity-100 peer-[:not(:placeholder-shown)]:scale-100 peer-[:not(:placeholder-shown)]:pointer-events-auto"
      >
        <Icone nome="fechar" className="!w-3.5 !h-3.5" />
      </button>
    </label>
  );
}
