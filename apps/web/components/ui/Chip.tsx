import Link from "next/link";
import { type ComponentPropsWithoutRef } from "react";

import { Icone } from "./Icone";

/**
 * Chips — pílulas de filtro com contador, ponto de categoria e remoção
 * (ZIL Interface › Chips). Ativo é invertido; nada tem borda.
 *
 * Escolha única (todas as pautas ou uma): o pai controla `ativo` como rádio.
 * Sempre que souber, mostre em `n` quantos itens o filtro devolve.
 */

interface ChipBase {
  ativo?: boolean;
  /** Contagem à direita, em números tabulares. */
  n?: number | string;
  /** Cor da pauta, igual à do gráfico: uma classe `bg-zil-brasil-*`. */
  pontoClassName?: string;
  /** Chip removível na linha de filtros ativos. */
  removivel?: boolean;
  tamanho?: "s" | "m";
  className?: string;
  children: React.ReactNode;
}
type ChipComoBotao = ChipBase & Omit<ComponentPropsWithoutRef<"button">, keyof ChipBase> & { href?: never };
type ChipComoLink = ChipBase & Omit<ComponentPropsWithoutRef<typeof Link>, keyof ChipBase> & { href: string };

export function Chip({
  ativo = false,
  n,
  pontoClassName,
  removivel = false,
  tamanho = "m",
  className = "",
  children,
  ...props
}: ChipComoBotao | ChipComoLink) {
  const classes = [
    "inline-flex items-center gap-1.5 shrink-0 rounded-pilula font-medium leading-none whitespace-nowrap cursor-pointer select-none",
    "transition-[background-color,color,transform] duration-toque ease-padrao active:scale-toque",
    tamanho === "s" ? "h-[30px] px-3 text-[14px]" : "h-9 px-3.5 text-[15px]",
    ativo
      ? "bg-zil-inverso text-zil-inverso-texto hover:bg-zil-inverso-hover"
      : "bg-zil-superficie-2 text-zil-texto hover:bg-zil-superficie-3",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const conteudo = (
    <>
      {pontoClassName && <span aria-hidden="true" className={`w-2 h-2 rounded-full shrink-0 ${pontoClassName}`} />}
      {children}
      {n !== undefined && (
        <span className={`zil-num transition-colors duration-toque ${ativo ? "text-zil-inverso-texto opacity-[.64]" : "text-zil-texto-2"}`}>
          {n}
        </span>
      )}
      {removivel && (
        <span
          aria-hidden="true"
          className={`inline-grid place-items-center w-5 h-5 -mr-1.5 rounded-full ${
            ativo ? "bg-zil-inverso-hover text-zil-inverso-texto" : "bg-zil-superficie-4 text-zil-texto"
          }`}
        >
          <Icone nome="fechar" className="!w-3 !h-3" />
        </span>
      )}
    </>
  );

  if ("href" in props && props.href) {
    const { href, ...rest } = props as ChipComoLink;
    return (
      <Link href={href} className={classes} aria-current={ativo ? "true" : undefined} {...rest}>
        {conteudo}
      </Link>
    );
  }
  return (
    <button type="button" className={classes} aria-pressed={ativo} {...(props as ChipComoBotao)}>
      {conteudo}
    </button>
  );
}

/** Linha de chips. `rolagem` mantém uma linha só, com a borda direita esmaecida (UFs no celular). */
export function Chips({
  rolagem = false,
  className = "",
  children,
  ...props
}: { rolagem?: boolean } & ComponentPropsWithoutRef<"div">) {
  return (
    <div className={`${rolagem ? "zil-rolagem-x gap-2" : "flex flex-wrap gap-2"} ${className}`} {...props}>
      {children}
    </div>
  );
}

/** Junta o botão "Filtros", os chips e, em `fim`, a ordenação. */
export function BarraFiltros({
  fim,
  className = "",
  children,
}: {
  fim?: React.ReactNode;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <div className={`flex flex-wrap items-center gap-2 ${className}`}>
      {children}
      {fim && <div className="ml-auto flex items-center gap-2">{fim}</div>}
    </div>
  );
}

/** Contador de filtros ativos, dentro do botão "Filtros". */
export function Contador({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-grid place-items-center min-w-5 h-5 px-1.5 rounded-pilula bg-zil-inverso text-zil-inverso-texto text-[12px] font-semibold leading-none zil-num">
      {children}
    </span>
  );
}
