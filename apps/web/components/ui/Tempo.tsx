/**
 * Linha do tempo e etapas (ZIL Interface › Linha do tempo, Etapas).
 */

type TomMarco = "padrao" | "alinhado" | "contra";

const MARCO: Record<TomMarco, string> = {
  padrao: "bg-zil-texto-2",
  alinhado: "bg-zil-alinhado",
  contra: "bg-zil-contra",
};

export function LinhaDoTempo({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <ol className={`grid gap-1 list-none m-0 p-0 ${className}`}>{children}</ol>;
}

/** Um marco: quando, título e detalhes. A cor do marco segue o voto. */
export function Marco({
  quando,
  titulo,
  tom = "padrao",
  ultimo = false,
  children,
}: {
  quando: React.ReactNode;
  titulo: React.ReactNode;
  tom?: TomMarco;
  ultimo?: boolean;
  children?: React.ReactNode;
}) {
  return (
    <li className="relative grid grid-cols-[24px_1fr] gap-3.5 py-3 pl-2 pr-3 rounded-2xl transition-colors duration-toque hover:bg-zil-superficie-1">
      {!ultimo && <span aria-hidden="true" className="absolute left-[19px] top-[34px] -bottom-3.5 w-0.5 rounded-sm bg-zil-separador" />}
      <span className="inline-grid place-items-center w-6 h-6 mt-px rounded-full bg-zil-superficie-3">
        <i className={`w-2.5 h-2.5 rounded-full ${MARCO[tom]}`} />
      </span>
      <div>
        <div className="text-legenda text-zil-texto-2">{quando}</div>
        <div className="mt-0.5 text-[17px] leading-6 font-semibold">{titulo}</div>
        {children && <div className="mt-1.5 flex flex-wrap items-center gap-2 text-texto-s text-zil-texto-2">{children}</div>}
      </div>
    </li>
  );
}

/** Etapas da tramitação em barras: feitas em `texto`, a atual em `neutro` pulsando, as próximas apagadas. */
export function Etapas({
  etapas,
  className = "",
}: {
  etapas: { nome: string; quando?: string; estado: "feita" | "atual" | "futura" }[];
  className?: string;
}) {
  return (
    // No celular as etapas rolam para o lado (mínimo de 120px cada); do md em diante dividem a largura.
    <ol className={`grid grid-flow-col auto-cols-[minmax(120px,1fr)] md:auto-cols-fr gap-1.5 list-none m-0 p-0 overflow-x-auto pb-1 ${className}`}>
      {etapas.map((e) => (
        <li key={e.nome} className="grid gap-2.5 content-start min-w-0" aria-current={e.estado === "atual" ? "step" : undefined}>
          <span className="h-1.5 rounded-pilula bg-zil-superficie-3 overflow-hidden">
            <span
              className={`block h-full rounded-[inherit] transition-[width] duration-lenta ease-padrao ${
                e.estado === "feita" ? "w-full bg-zil-texto" : e.estado === "atual" ? "w-1/2 bg-zil-neutro animate-zil-respira" : "w-0"
              }`}
            />
          </span>
          <span className={`text-[15px] leading-5 font-semibold ${e.estado === "futura" ? "text-zil-texto-2" : ""}`}>{e.nome}</span>
          <span className="text-[14px] leading-[18px] text-zil-texto-2">{e.quando ?? "—"}</span>
        </li>
      ))}
    </ol>
  );
}
