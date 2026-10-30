import { Icone, type NomeIcone } from "./Icone";

/**
 * Aviso — faixa com ícone, título, texto e uma ação opcional, em quatro tons
 * (ZIL Interface › Aviso). `neutro` é atenção (dado não validado), `contra`
 * é erro (diz o que aconteceu e o que fazer), `alinhado` é sucesso.
 */

type Tom = "padrao" | "neutro" | "contra" | "alinhado";

const TOM: Record<Tom, { fundo: string; icone: string; nome: NomeIcone; role: string }> = {
  padrao: { fundo: "bg-zil-superficie-1", icone: "bg-zil-superficie-3 text-zil-texto", nome: "info", role: "note" },
  neutro: { fundo: "bg-zil-neutro-fundo", icone: "bg-zil-neutro text-zil-inverso-texto", nome: "info", role: "note" },
  contra: { fundo: "bg-zil-contra-fundo", icone: "bg-zil-contra text-zil-inverso-texto", nome: "fechar", role: "alert" },
  alinhado: { fundo: "bg-zil-alinhado-fundo", icone: "bg-zil-alinhado text-zil-inverso-texto", nome: "check", role: "status" },
};

interface AvisoProps {
  tom?: Tom;
  titulo: React.ReactNode;
  children?: React.ReactNode;
  acao?: React.ReactNode;
  icone?: NomeIcone;
  className?: string;
}

export function Aviso({ tom = "padrao", titulo, children, acao, icone, className = "" }: AvisoProps) {
  const t = TOM[tom];
  return (
    // No celular a ação desce para baixo do texto; a partir de sm fica à direita.
    <div role={t.role} className={`grid grid-cols-[auto_minmax(0,1fr)] sm:grid-cols-[auto_minmax(0,1fr)_auto] gap-x-3.5 gap-y-3 items-start px-[18px] py-4 rounded-[18px] ${t.fundo} ${className}`}>
      <span className={`inline-grid place-items-center w-8 h-8 rounded-full ${t.icone}`}>
        <Icone nome={icone ?? t.nome} tamanho="s" />
      </span>
      <div className="min-w-0">
        <div className="text-[16px] leading-[22px] font-semibold">{titulo}</div>
        {children && <div className="mt-0.5 text-[15px] leading-[21px] text-zil-texto-2">{children}</div>}
      </div>
      {acao && <div className="col-start-2 sm:col-auto justify-self-start sm:justify-self-end">{acao}</div>}
    </div>
  );
}
