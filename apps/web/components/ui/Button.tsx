import Link from "next/link";
import { type ComponentPropsWithoutRef } from "react";

import { Icone, type NomeIcone } from "./Icone";

/**
 * Botão — pílula sem borda para toda ação (ZIL Interface › Botão).
 *
 * `primario` é o único bloco invertido da área: um por tela ou por cartão.
 * `secundario` (padrão) fica ao lado dele; `fantasma` é terciário; `vidro`
 * vai sobre fotos. O rótulo diz o que acontece: "Ver 18 parlamentares".
 */

type Variante = "primario" | "secundario" | "fantasma" | "vidro";
type Tamanho = "s" | "m" | "l";

interface Base {
  variante?: Variante;
  tamanho?: Tamanho;
  bloco?: boolean;
  carregando?: boolean;
  className?: string;
}

type ComoBotao = Base & Omit<ComponentPropsWithoutRef<"button">, keyof Base> & { href?: never };
type ComoLink = Base & Omit<ComponentPropsWithoutRef<typeof Link>, keyof Base> & { href: string };

export type ButtonProps = ComoBotao | ComoLink;

const VARIANTE: Record<Variante, string> = {
  primario: "bg-zil-inverso text-zil-inverso-texto hover:bg-zil-inverso-hover",
  secundario: "bg-zil-superficie-3 text-zil-texto hover:bg-zil-superficie-4",
  fantasma: "bg-transparent text-zil-texto hover:bg-zil-superficie-2",
  vidro: "zil-vidro text-zil-texto hover:bg-zil-vidro-forte",
};

const TAMANHO: Record<Tamanho, string> = {
  s: "h-9 px-3.5 text-[15px]",
  m: "h-11 px-5 text-[16px]",
  l: "h-[52px] px-[26px] text-[17px]",
};

export function Button({
  variante = "secundario",
  tamanho = "m",
  bloco = false,
  carregando = false,
  className = "",
  children,
  ...props
}: ButtonProps) {
  const classes = [
    "relative inline-flex items-center justify-center gap-2 rounded-pilula font-medium leading-none tracking-[-0.005em] whitespace-nowrap select-none cursor-pointer",
    "transition-[background-color,transform,opacity] duration-toque ease-padrao active:scale-toque",
    "disabled:opacity-40 disabled:pointer-events-none aria-disabled:opacity-40 aria-disabled:pointer-events-none",
    VARIANTE[variante],
    TAMANHO[tamanho],
    bloco ? "flex w-full" : "",
    carregando ? "text-transparent pointer-events-none" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const conteudo = (
    <>
      {children}
      {carregando && (
        <span
          aria-hidden="true"
          className={`absolute inset-0 m-auto h-[18px] w-[18px] rounded-full border-2 border-zil-texto-3 animate-zil-gira ${
            variante === "primario" ? "border-t-zil-inverso-texto" : "border-t-zil-texto"
          }`}
        />
      )}
    </>
  );

  if ("href" in props && props.href) {
    const { href, ...rest } = props as ComoLink;
    return (
      <Link href={href} className={classes} {...rest}>
        {conteudo}
      </Link>
    );
  }

  return (
    <button className={classes} aria-busy={carregando || undefined} {...(props as ComoBotao)}>
      {conteudo}
    </button>
  );
}

/** Ação só com ícone: 44×44, cantos `raio-m` (squircle). `redondo` para fechar e compartilhar. */
interface BotaoIconeBase {
  icone: NomeIcone;
  /** Obrigatório: o ícone sozinho não diz o que faz. */
  rotulo: string;
  variante?: "padrao" | "fantasma" | "vidro";
  redondo?: boolean;
  tamanho?: "s" | "m";
  className?: string;
}
type BotaoIconeComoBotao = BotaoIconeBase & Omit<ComponentPropsWithoutRef<"button">, keyof BotaoIconeBase | "children"> & { href?: never };
type BotaoIconeComoLink = BotaoIconeBase & Omit<ComponentPropsWithoutRef<typeof Link>, keyof BotaoIconeBase | "children"> & { href: string };

const VARIANTE_ICONE = {
  padrao: "bg-zil-superficie-2 hover:bg-zil-superficie-3",
  fantasma: "bg-transparent hover:bg-zil-superficie-2",
  vidro: "zil-vidro hover:bg-zil-vidro-forte",
} as const;

export function BotaoIcone({
  icone,
  rotulo,
  variante = "padrao",
  redondo = false,
  tamanho = "m",
  className = "",
  ...props
}: BotaoIconeComoBotao | BotaoIconeComoLink) {
  const classes = [
    "inline-grid place-items-center shrink-0 text-zil-texto cursor-pointer",
    "transition-[background-color,transform] duration-toque ease-padrao active:scale-[.94]",
    tamanho === "s" ? "w-9 h-9 rounded-s" : "w-11 h-11 rounded-m",
    redondo ? "rounded-pilula" : "",
    VARIANTE_ICONE[variante],
    className,
  ]
    .filter(Boolean)
    .join(" ");

  if ("href" in props && props.href) {
    const { href, ...rest } = props as BotaoIconeComoLink;
    return (
      <Link href={href} className={classes} aria-label={rotulo} title={rotulo} {...rest}>
        <Icone nome={icone} />
      </Link>
    );
  }
  return (
    <button type="button" className={classes} aria-label={rotulo} title={rotulo} {...(props as BotaoIconeComoBotao)}>
      <Icone nome={icone} />
    </button>
  );
}
