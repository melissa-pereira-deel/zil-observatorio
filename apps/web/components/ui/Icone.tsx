/**
 * Ícones do sistema: traço de 1,75px, pontas arredondadas, grade de 24px.
 * Desenhos inline no mesmo padrão dos previews do ZIL Interface. Ícone
 * acompanha texto; sozinho, só em botão de ícone com `aria-label`.
 */

export type NomeIcone =
  | "busca"
  | "fechar"
  | "chevron-direita"
  | "chevron-esquerda"
  | "chevron-baixo"
  | "mais"
  | "externo"
  | "filtros"
  | "inicio"
  | "placar"
  | "documento"
  | "bussola"
  | "check"
  | "info"
  | "alerta"
  | "download"
  | "seta-baixo"
  | "seta-cima"
  | "seta-direita"
  | "compartilhar"
  | "pausa"
  | "play"
  | "menu";

const CAMINHOS: Record<NomeIcone, React.ReactNode> = {
  busca: (
    <>
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.5-3.5" />
    </>
  ),
  fechar: <path d="M6 6l12 12M18 6 6 18" />,
  "chevron-direita": <path d="m9 6 6 6-6 6" />,
  "chevron-esquerda": <path d="m15 6-6 6 6 6" />,
  "chevron-baixo": <path d="m6 9 6 6 6-6" />,
  mais: <path d="M12 5v14M5 12h14" />,
  externo: <path d="M7 17 17 7M9 7h8v8" />,
  filtros: (
    <>
      <path d="M4 7h10M18 7h2M4 17h4M12 17h8" />
      <circle cx="16" cy="7" r="2" />
      <circle cx="10" cy="17" r="2" />
    </>
  ),
  inicio: <path d="M4 11 12 4l8 7v8a1 1 0 0 1-1 1h-4v-6H9v6H5a1 1 0 0 1-1-1z" />,
  placar: <path d="M5 20V10M12 20V4M19 20v-7" />,
  documento: (
    <>
      <path d="M7 3h7l5 5v12a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z" />
      <path d="M14 3v5h5" />
    </>
  ),
  bussola: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="m15.5 8.5-2 5-5 2 2-5z" />
    </>
  ),
  check: <path d="m5 12 5 5 9-10" />,
  info: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 11v5M12 8h.01" />
    </>
  ),
  alerta: <path d="M12 9v4M12 17h.01M10.3 3.9 2.6 17.2a2 2 0 0 0 1.7 3h15.4a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" />,
  download: <path d="M12 3v12M8 11l4 4 4-4M5 19h14" />,
  "seta-baixo": <path d="M12 5v14M6 13l6 6 6-6" />,
  "seta-cima": <path d="M12 19V5M6 11l6-6 6 6" />,
  "seta-direita": <path d="M5 12h14M13 6l6 6-6 6" />,
  compartilhar: <path d="M12 3v12M8 7l4-4 4 4M5 13v5a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-5" />,
  pausa: <path d="M9 5v14M15 5v14" />,
  play: <path d="M7 5v14l12-7z" />,
  menu: <path d="M4 7h16M4 12h16M4 17h16" />,
};

interface IconeProps {
  nome: NomeIcone;
  /** 20px é o padrão; `s` é 16px. */
  tamanho?: "s" | "m" | "l";
  className?: string;
}

const TAMANHO = { s: "w-4 h-4", m: "w-5 h-5", l: "w-6 h-6" } as const;

export function Icone({ nome, tamanho = "m", className = "" }: IconeProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      aria-hidden="true"
      className={`${TAMANHO[tamanho]} shrink-0 fill-none stroke-current ${className}`}
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {CAMINHOS[nome]}
    </svg>
  );
}
