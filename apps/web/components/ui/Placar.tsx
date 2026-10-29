import Link from "next/link";

import { Avatar } from "./Avatar";
import { Icone } from "./Icone";
import { ScorePilula, VotosBarra } from "./Score";

/**
 * Placar — a tabela de ranking em linhas arredondadas, sem grade nem zebra
 * (ZIL Interface › Placar). Colunas: # · Parlamentar · Score · Votos
 * alinhados · chevron.
 *
 * Duas variações, decididas pelo pai e não pelo viewport (uma coluna de
 * 440px no desktop precisa do mesmo layout que um celular):
 * - `compacto`: posição · pessoa · score, sempre. Para prévias e colunas.
 * - `colunaVotos={false}`: sem "Votos alinhados" quando a API não traz o dado.
 */

function grade(compacto: boolean, colunaVotos: boolean): string {
  if (compacto) return "grid grid-cols-[28px_minmax(0,1fr)_auto] items-center gap-3";
  const md = colunaVotos ? "md:grid-cols-[44px_minmax(0,1fr)_120px_160px_24px]" : "md:grid-cols-[44px_minmax(0,1fr)_120px_24px]";
  return `grid grid-cols-[28px_minmax(0,1fr)_auto] ${md} items-center gap-4`;
}

export function Placar({ rotulo = "Placar ZIL", children }: { rotulo?: string; children: React.ReactNode }) {
  return (
    <div role="table" aria-label={rotulo} className="grid gap-0.5">
      {children}
    </div>
  );
}

export function PlacarCabecalho({
  ordenarScore,
  ordenarNome,
  ordem,
  colunaVotos = true,
}: {
  ordenarScore?: () => void;
  ordenarNome?: () => void;
  /** Qual coluna está ordenada e em que direção. */
  ordem?: { coluna: "score" | "nome"; direcao: "ascending" | "descending" };
  colunaVotos?: boolean;
}) {
  const Ordem = ({ coluna, children, onClick }: { coluna: "score" | "nome"; children: React.ReactNode; onClick?: () => void }) => {
    const ativa = ordem?.coluna === coluna;
    return (
      <button
        type="button"
        onClick={onClick}
        className={`inline-flex items-center gap-1 h-[30px] px-2.5 -ml-2.5 rounded-pilula text-[14px] font-medium leading-none transition-colors duration-toque hover:bg-zil-superficie-2 hover:text-zil-texto ${
          ativa ? "text-zil-texto" : "text-zil-texto-2"
        }`}
      >
        {children}
        {ativa && (
          <Icone
            nome="seta-baixo"
            tamanho="s"
            className={`transition-transform duration-padrao ease-padrao ${ordem?.direcao === "ascending" ? "rotate-180" : ""}`}
          />
        )}
      </button>
    );
  };
  return (
    <div role="row" className={`hidden md:grid ${grade(false, colunaVotos)} h-10 px-3.5 text-[14px] font-medium leading-none text-zil-texto-2`}>
      <span role="columnheader">#</span>
      <span role="columnheader" aria-sort={ordem?.coluna === "nome" ? ordem.direcao : undefined}>
        <Ordem coluna="nome" onClick={ordenarNome}>
          Parlamentar
        </Ordem>
      </span>
      <span role="columnheader" aria-sort={ordem?.coluna === "score" ? ordem.direcao : undefined}>
        <Ordem coluna="score" onClick={ordenarScore}>
          Score
        </Ordem>
      </span>
      {colunaVotos && <span role="columnheader">Votos alinhados</span>}
      <span />
    </div>
  );
}

interface PlacarLinhaProps {
  /** Sem posição (lista de quem ainda não tem score), a coluna fica vazia. */
  posicao?: number;
  href: string;
  nome: string;
  fotoUrl?: string | null;
  meta: string;
  score: number | null;
  alinhados?: number;
  total?: number;
  scoreTitle?: string;
  compacto?: boolean;
  colunaVotos?: boolean;
}

export function PlacarLinha({
  posicao,
  href,
  nome,
  fotoUrl,
  meta,
  score,
  alinhados,
  total,
  scoreTitle,
  compacto = false,
  colunaVotos = true,
}: PlacarLinhaProps) {
  const temVotos = alinhados !== undefined && total !== undefined && total > 0;
  return (
    <Link
      href={href}
      role="row"
      className={`group ${grade(compacto, colunaVotos)} ${
        compacto ? "min-h-16 px-2.5 py-2 rounded-m" : "min-h-[72px] px-2.5 py-2 md:px-3.5 rounded-2xl"
      } text-zil-texto no-underline transition-[background-color,transform] duration-toque ease-padrao hover:bg-zil-superficie-1 active:scale-[.995]`}
    >
      <span className="text-[17px] font-semibold leading-none text-zil-texto-2 zil-num">{posicao ?? ""}</span>
      <span className="flex items-center gap-3 md:gap-3.5 min-w-0">
        <Avatar nome={nome} fotoUrl={fotoUrl} />
        <span className="grid min-w-0">
          <span className="text-[16px] md:text-[17px] leading-[22px] font-semibold truncate">{nome}</span>
          <span className="text-texto-s text-zil-texto-2 truncate">{meta}</span>
        </span>
      </span>
      <span className="justify-self-end md:justify-self-start">
        <ScorePilula valor={score} title={scoreTitle} />
      </span>
      {!compacto && colunaVotos && (
        <span className="hidden md:grid gap-1.5">
          {temVotos ? (
            <>
              <VotosBarra sim={alinhados} nao={total - alinhados} />
              <span className="text-texto-s text-zil-texto-2 zil-num">
                {alinhados} de {total}
              </span>
            </>
          ) : (
            <span className="text-texto-s text-zil-texto-3">—</span>
          )}
        </span>
      )}
      {!compacto && (
        <Icone
          nome="chevron-direita"
          className="hidden md:block text-zil-texto-3 transition-[transform,color] duration-padrao ease-padrao group-hover:translate-x-[3px] group-hover:text-zil-texto"
        />
      )}
    </Link>
  );
}

/** Esqueleto de uma linha do placar, com a forma do conteúdo real. */
export function PlacarLinhaEsqueleto({ compacto = false, colunaVotos = true }: { compacto?: boolean; colunaVotos?: boolean }) {
  return (
    <div aria-hidden="true" className={`${grade(compacto, colunaVotos)} ${compacto ? "min-h-16 px-2.5" : "min-h-[72px] px-3.5"}`}>
      <span className="zil-esqueleto h-4 w-5" />
      <span className="flex items-center gap-3.5">
        <span className="zil-esqueleto w-10 h-10 rounded-full" />
        <span className="flex-1 grid gap-2">
          <span className="zil-esqueleto h-3.5 w-[60%]" />
          <span className="zil-esqueleto h-3 w-[35%]" />
        </span>
      </span>
      <span className="zil-esqueleto w-16 h-[30px] rounded-pilula justify-self-end md:justify-self-start" />
      {!compacto && colunaVotos && <span className="hidden md:block zil-esqueleto h-2.5 w-full rounded-pilula" />}
      {!compacto && <span />}
    </div>
  );
}
