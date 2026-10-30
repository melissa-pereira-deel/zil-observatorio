import Link from "next/link";
import { type ComponentPropsWithoutRef } from "react";

import { Icone } from "./Icone";

/**
 * Lista agrupada — lista em cartão no estilo de Ajustes do iPhone
 * (ZIL Interface › Lista agrupada): ícone em squircle, título, subtítulo e
 * acessório. Sem linha por padrão; `separada` só em listas longas e densas.
 */

export function Lista({
  titulo,
  separada = false,
  className = "",
  children,
  ...props
}: { titulo?: string; separada?: boolean } & ComponentPropsWithoutRef<"div">) {
  return (
    <div className={`grid gap-0.5 p-1.5 rounded-l bg-zil-superficie-1 ${separada ? "[&>a+a]:relative [&>a+a]:before:absolute [&>a+a]:before:-top-px [&>a+a]:before:left-[58px] [&>a+a]:before:right-3 [&>a+a]:before:h-px [&>a+a]:before:bg-zil-separador [&>div+div]:relative [&>div+div]:before:absolute [&>div+div]:before:-top-px [&>div+div]:before:left-[58px] [&>div+div]:before:right-3 [&>div+div]:before:h-px [&>div+div]:before:bg-zil-separador" : ""} ${className}`} {...props}>
      {titulo && <div className="px-3.5 pt-3.5 pb-1.5 text-[15px] leading-5 font-semibold text-zil-texto-2">{titulo}</div>}
      {children}
    </div>
  );
}

/** Esqueleto de uma linha, com a forma do conteúdo real. */
export function LinhaEsqueleto({ icone = true }: { icone?: boolean }) {
  return (
    <div aria-hidden="true" className="flex items-center gap-3.5 min-h-14 px-3 py-2.5">
      {icone && <span className="zil-esqueleto w-8 h-8 rounded-[10px]" />}
      <span className="flex-1 grid gap-2">
        <span className="zil-esqueleto h-3.5 w-[55%]" />
        <span className="zil-esqueleto h-3 w-[35%]" />
      </span>
      <span className="zil-esqueleto w-16 h-[26px] rounded-pilula" />
    </div>
  );
}

interface LinhaBase {
  icone?: React.ReactNode;
  titulo: React.ReactNode;
  sub?: React.ReactNode;
  /** Acessório à direita: valor, selo, chevron. */
  fim?: React.ReactNode;
  /** Mostra o chevron de navegação ao lado de `fim`. */
  chevron?: boolean;
  className?: string;
}
type LinhaEstatica = LinhaBase & Omit<ComponentPropsWithoutRef<"div">, keyof LinhaBase> & { href?: never };
type LinhaLink = LinhaBase & Omit<ComponentPropsWithoutRef<typeof Link>, keyof LinhaBase> & { href: string };

export function Linha({ icone, titulo, sub, fim, chevron, className = "", ...props }: LinhaEstatica | LinhaLink) {
  const ehLink = "href" in props && !!props.href;
  const classes = [
    "flex items-center gap-3.5 min-h-14 px-3 py-2.5 rounded-m text-zil-texto no-underline",
    ehLink ? "cursor-pointer transition-colors duration-toque hover:bg-zil-superficie-2 active:bg-zil-superficie-3" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");
  const conteudo = (
    <>
      {icone && <span className="inline-grid place-items-center w-8 h-8 rounded-[10px] bg-zil-superficie-3 text-zil-texto shrink-0">{icone}</span>}
      <span className="flex-1 min-w-0 grid gap-0.5">
        <span className="text-[16px] leading-[22px] font-medium">{titulo}</span>
        {sub && <span className="text-texto-s text-zil-texto-2">{sub}</span>}
      </span>
      {(fim || chevron || ehLink) && (
        <span className="flex items-center gap-2 text-zil-texto-2 text-[15px] shrink-0">
          {fim}
          {(chevron ?? ehLink) && <Icone nome="chevron-direita" className="text-zil-texto-3" />}
        </span>
      )}
    </>
  );
  if (ehLink) {
    const { href, ...rest } = props as LinhaLink;
    return (
      <Link href={href} className={classes} {...rest}>
        {conteudo}
      </Link>
    );
  }
  return (
    <div className={classes} {...(props as LinhaEstatica)}>
      {conteudo}
    </div>
  );
}
