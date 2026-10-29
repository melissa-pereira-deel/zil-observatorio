/**
 * Os números do ZIL (ZIL Interface › Score): pílula de score, score grande,
 * medidor de −10 a +10 e barra de votos.
 *
 * Score sempre com sinal e vírgula: +6,4, −3,3. Classes: ≥ +3 alinhado,
 * ≤ −3 contra, entre os dois neutro. O marcador e a cor nunca são a única
 * pista: o número e a frase sempre aparecem.
 */

export type TomScore = "alinhado" | "contra" | "neutro";

export function tomDoScore(v: number): TomScore {
  return v >= 3 ? "alinhado" : v <= -3 ? "contra" : "neutro";
}

export function formatarScore(v: number): string {
  const sinal = v > 0 ? "+" : v < 0 ? "−" : "";
  return sinal + Math.abs(v).toFixed(1).replace(".", ",");
}

export function fraseDoScore(v: number): string {
  return { alinhado: "Majoritariamente alinhado", contra: "Majoritariamente contra", neutro: "Dividido" }[tomDoScore(v)];
}

const PILULA: Record<TomScore, string> = {
  alinhado: "bg-zil-alinhado-fundo text-zil-alinhado",
  contra: "bg-zil-contra-fundo text-zil-contra",
  neutro: "bg-zil-neutro-fundo text-zil-neutro",
};

const GRANDE: Record<TomScore, string> = {
  alinhado: "text-zil-alinhado",
  contra: "text-zil-contra",
  neutro: "text-zil-neutro",
};

/** Pílula de 30px para listas. `null` vira "sem dado". */
export function ScorePilula({ valor, title, className = "" }: { valor: number | null | undefined; title?: string; className?: string }) {
  const base = "inline-flex items-center justify-center min-w-16 h-[30px] px-3 rounded-pilula text-[15px] font-semibold leading-none tracking-[-0.01em] zil-num";
  if (valor === null || valor === undefined) {
    return (
      <span className={`${base} bg-zil-superficie-2 text-zil-texto-2 ${className}`} title={title}>
        sem dado
      </span>
    );
  }
  return (
    <span className={`${base} ${PILULA[tomDoScore(valor)]} ${className}`} title={title}>
      {formatarScore(valor)}
    </span>
  );
}

/** 80px tabular, com a frase abaixo. */
export function ScoreGrande({ valor, frase, className = "" }: { valor: number; frase?: string; className?: string }) {
  return (
    <div className={`grid gap-2 ${className}`}>
      <span className={`text-numero-xl zil-num ${GRANDE[tomDoScore(valor)]}`}>{formatarScore(valor)}</span>
      <span className="text-[18px] leading-6 font-semibold">{frase ?? fraseDoScore(valor)}</span>
    </div>
  );
}

/** Três zonas em fundos semânticos e um marcador invertido que desliza com mola até a posição. Sem `valor`, é só a escala (explicações da metodologia). */
export function Medidor({ valor, className = "" }: { valor?: number; className?: string }) {
  const pos = valor === undefined ? null : Math.min(100, Math.max(0, ((valor + 10) / 20) * 100));
  return (
    <div
      role="img"
      aria-label={valor === undefined ? "Escala de menos 10 a mais 10" : `Score ${formatarScore(valor)} numa escala de menos 10 a mais 10`}
      className={`relative pt-2.5 ${className}`}
    >
      <div className="grid grid-cols-[2fr_1fr_2fr] gap-[3px] h-2">
        <i className="rounded-pilula bg-zil-contra-fundo" />
        <i className="rounded-pilula bg-zil-neutro-fundo" />
        <i className="rounded-pilula bg-zil-alinhado-fundo" />
      </div>
      {pos !== null && (
        <span
          aria-hidden="true"
          className="absolute top-1.5 w-4 h-4 -ml-2 rounded-full bg-zil-inverso shadow-[0_0_0_4px_var(--fundo)] transition-[left] duration-lenta ease-mola"
          // Posição do marcador: valor de dado, não estilo decorativo.
          style={{ left: `${pos}%` }}
        />
      )}
      <div className="flex justify-between mt-2.5 text-[13px] leading-[18px] font-medium text-zil-texto-2 zil-num">
        <span>−10 contra</span>
        <span>0</span>
        <span>+10 a favor</span>
      </div>
    </div>
  );
}

/** Barra empilhada de sim, não e ausentes, com 3px de vão. Partes com zero somem. */
export function VotosBarra({
  sim,
  nao,
  ausentes = 0,
  rotulo,
  className = "",
}: {
  sim: number;
  nao: number;
  ausentes?: number;
  rotulo?: string;
  className?: string;
}) {
  const partes = [
    { n: sim, cls: "bg-zil-alinhado" },
    { n: nao, cls: "bg-zil-contra" },
    { n: ausentes, cls: "bg-zil-superficie-4" },
  ].filter((p) => p.n > 0);
  return (
    <div
      role="img"
      aria-label={rotulo ?? `${sim} sim, ${nao} não${ausentes ? `, ${ausentes} ausentes` : ""}`}
      className={`flex gap-[3px] h-2.5 ${className}`}
    >
      {partes.map((p, i) => (
        // flex-grow proporcional ao número de votos: é dado, não estilo.
        <i key={i} className={`rounded-pilula min-w-1.5 transition-[flex-grow] duration-lenta ease-padrao ${p.cls}`} style={{ flexGrow: p.n }} />
      ))}
    </div>
  );
}

/** Legenda da barra de votos. Os rótulos mudam com o dado: "sim/não" numa votação, "alinhados/contra" num perfil. */
export function VotosLegenda({
  sim,
  nao,
  ausentes,
  rotulos = { sim: "sim", nao: "não", ausentes: "ausentes" },
}: {
  sim: number;
  nao: number;
  ausentes?: number;
  rotulos?: { sim: string; nao: string; ausentes?: string };
}) {
  const Item = ({ cor, children }: { cor: string; children: React.ReactNode }) => (
    <span className="inline-flex items-center gap-1.5">
      <i className={`w-2 h-2 rounded-full ${cor}`} />
      {children}
    </span>
  );
  return (
    <div className="flex flex-wrap gap-x-4 gap-y-1.5 text-[14px] leading-5 font-medium text-zil-texto-2 zil-num">
      <Item cor="bg-zil-alinhado">
        {sim} {rotulos.sim}
      </Item>
      <Item cor="bg-zil-contra">
        {nao} {rotulos.nao}
      </Item>
      {ausentes !== undefined && ausentes > 0 && (
        <Item cor="bg-zil-superficie-4">
          {ausentes} {rotulos.ausentes ?? "ausentes"}
        </Item>
      )}
    </div>
  );
}
