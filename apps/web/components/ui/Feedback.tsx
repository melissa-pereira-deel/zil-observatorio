import { Icone, type NomeIcone } from "./Icone";

/**
 * Feedback (ZIL Interface › Feedback): estado vazio e esqueleto.
 *
 * O vazio explica o motivo e oferece uma ação que resolve ("Limpar filtros").
 * O esqueleto copia a forma do conteúdo real.
 */

export function Vazio({
  icone = "busca",
  titulo,
  children,
  acao,
  className = "",
}: {
  icone?: NomeIcone;
  titulo: React.ReactNode;
  children?: React.ReactNode;
  acao?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`grid justify-items-center gap-2.5 text-center px-6 py-12 rounded-l bg-zil-superficie-1 ${className}`}>
      <span className="inline-grid place-items-center w-14 h-14 rounded-full bg-zil-superficie-2 text-zil-texto-2">
        <Icone nome={icone} />
      </span>
      <span className="text-titulo-4">{titulo}</span>
      {children && <span className="text-texto-s text-zil-texto-2 max-w-[36ch]">{children}</span>}
      {acao && <div className="mt-1.5">{acao}</div>}
    </div>
  );
}

/** Bloco de esqueleto; combine larguras e alturas com classes. */
export function Esqueleto({ className = "" }: { className?: string }) {
  return <span aria-hidden="true" className={`zil-esqueleto ${className}`} />;
}

/** Esqueleto de um cartão de texto: título e duas linhas. */
export function CardEsqueleto({ className = "" }: { className?: string }) {
  return (
    <div aria-hidden="true" className={`grid gap-3 p-6 rounded-l bg-zil-superficie-1 ${className}`}>
      <Esqueleto className="h-5 w-[55%]" />
      <Esqueleto className="h-3.5 w-full" />
      <Esqueleto className="h-3.5 w-[80%]" />
    </div>
  );
}
