/**
 * Selo — pílula de 26px para status (ZIL Interface › Controles).
 *
 * `alinhado`, `contra` e `neutro` usam o par cor/fundo semântico; `forte` é
 * invertido, para "Novo". Com `ponto` para status.
 */

export type TomSelo = "padrao" | "alinhado" | "contra" | "neutro" | "forte";

const TOM: Record<TomSelo, string> = {
  padrao: "bg-zil-superficie-2 text-zil-texto-2",
  alinhado: "bg-zil-alinhado-fundo text-zil-alinhado",
  contra: "bg-zil-contra-fundo text-zil-contra",
  neutro: "bg-zil-neutro-fundo text-zil-neutro",
  forte: "bg-zil-inverso text-zil-inverso-texto",
};

interface SeloProps {
  tom?: TomSelo;
  ponto?: boolean;
  /** Ícone antes do texto. Vai fora do span truncado: svg é `display:block` no preflight e quebraria a linha. */
  icone?: React.ReactNode;
  title?: string;
  className?: string;
  children: React.ReactNode;
}

export function Selo({ tom = "padrao", ponto = false, icone, title, className = "", children }: SeloProps) {
  // Texto longo (situação da Câmara) trunca em vez de alargar o cartão; o
  // inteiro vai para o title quando o texto é uma string.
  const inteiro = title ?? (typeof children === "string" ? children : undefined);
  return (
    <span
      title={inteiro}
      className={`inline-flex items-center gap-1.5 max-w-full min-w-0 h-[26px] px-2.5 rounded-pilula text-[13px] font-semibold leading-none ${TOM[tom]} ${className}`}
    >
      {ponto && <span aria-hidden="true" className="w-1.5 h-1.5 rounded-full bg-current shrink-0" />}
      {icone && <span aria-hidden="true" className="inline-flex shrink-0">{icone}</span>}
      <span className="truncate">{children}</span>
    </span>
  );
}
