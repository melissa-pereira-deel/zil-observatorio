import Link from "next/link";
import { type ComponentPropsWithoutRef } from "react";

/**
 * Cartão — superfície sem borda nem sombra, separada do fundo pelo degrau
 * de preenchimento (ZIL Interface › Cartão).
 *
 * Dentro de um cartão, controles usam `superficie-2`; não empilhe cartão
 * dentro de cartão. Entre cartões, gap de 16 a 24px, nunca linha.
 */

interface CardBase {
  compacto?: boolean;
  className?: string;
  children: React.ReactNode;
}
type CardEstatico = CardBase & Omit<ComponentPropsWithoutRef<"div">, keyof CardBase> & { href?: never };
/** O cartão inteiro é um link: hover `superficie-2`, pressionado escala 0,99. */
type CardInterativo = CardBase & Omit<ComponentPropsWithoutRef<typeof Link>, keyof CardBase> & { href: string };

export function Card({ compacto = false, className = "", children, ...props }: CardEstatico | CardInterativo) {
  const base = `min-w-0 rounded-l bg-zil-superficie-1 ${compacto ? "p-5" : "p-6"}`;
  if ("href" in props && props.href) {
    const { href, ...rest } = props as CardInterativo;
    return (
      <Link
        href={href}
        className={`block ${base} text-inherit no-underline cursor-pointer transition-[background-color,transform] duration-toque ease-padrao hover:bg-zil-superficie-2 active:scale-[.99] ${className}`}
        {...rest}
      >
        {children}
      </Link>
    );
  }
  return (
    <div className={`${base} ${className}`} {...(props as CardEstatico)}>
      {children}
    </div>
  );
}

/** Número em 44px tabular, rótulo e fonte. A fonte do dado é obrigatória. */
export function Estat({
  n,
  rotulo,
  fonte,
  className = "",
}: {
  n: React.ReactNode;
  rotulo: React.ReactNode;
  fonte?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`grid gap-1.5 p-6 rounded-l bg-zil-superficie-1 ${className}`}>
      {/* 36px no celular, onde dois cartões dividem 343px; 44px a partir de md. */}
      <span className="text-[36px] leading-10 font-semibold tracking-[-0.03em] md:text-numero-l zil-num whitespace-nowrap">{n}</span>
      <span className="text-texto-ui">{rotulo}</span>
      {fonte && <span className="text-[14px] leading-5 text-zil-texto-2">{fonte}</span>}
    </div>
  );
}

/** Painel de chamada centralizado (raio-xl, padding vertical 96px): o fecho de página. */
export function Painel({ className = "", children }: { className?: string; children: React.ReactNode }) {
  return (
    <section className={`grid justify-items-center gap-4 text-center px-6 py-16 md:px-10 md:py-24 rounded-xl bg-zil-superficie-1 ${className}`}>
      {children}
    </section>
  );
}
