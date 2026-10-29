"use client";

import { useState } from "react";

/**
 * Avatar — iniciais em `superficie-3` ou foto, redondo
 * (ZIL Interface › Controles). 28/40/56/96px.
 */

type Tamanho = "s" | "m" | "l" | "xl";

const TAMANHO: Record<Tamanho, string> = {
  s: "w-7 h-7 text-[11px]",
  m: "w-10 h-10 text-[15px]",
  l: "w-14 h-14 text-[21px]",
  xl: "w-24 h-24 text-[36px]",
};

export function iniciais(nome: string): string {
  return nome
    .split(" ")
    .filter((p) => p.length > 2)
    .map((p) => p[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

interface AvatarProps {
  nome: string;
  fotoUrl?: string | null;
  tamanho?: Tamanho;
  className?: string;
}

export function Avatar({ nome, fotoUrl, tamanho = "m", className = "" }: AvatarProps) {
  const [erro, setErro] = useState(false);
  const mostraFoto = !!fotoUrl && !erro;
  return (
    <span
      className={`inline-grid place-items-center shrink-0 overflow-hidden rounded-full bg-zil-superficie-3 text-zil-texto font-semibold leading-none tracking-[-0.01em] select-none ${TAMANHO[tamanho]} ${className}`}
    >
      {mostraFoto ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={fotoUrl}
          alt={nome}
          loading="lazy"
          className="w-full h-full object-cover"
          onError={() => setErro(true)}
        />
      ) : (
        <span aria-hidden="true">{iniciais(nome)}</span>
      )}
    </span>
  );
}
