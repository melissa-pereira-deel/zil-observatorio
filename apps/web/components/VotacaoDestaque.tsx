"use client";

import { useEffect, useState } from "react";

import { HemicicloVotacao } from "@/components/PlenarioVotacao";
import { Button, Card, Esqueleto, Selo, TituloSecao } from "@/components/ui";
import { VOTACAO_DESTAQUE } from "@/lib/destaque";
import { CADEIRAS, type GrupoVoto, type VotoIndividual } from "@/lib/votacao";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Votacao {
  id: string;
  fonte: string;
  data: string | null;
  resultado: string | null;
  direcao_esperada: string | null;
  proposicao: { tipo: string | null; numero: number | null; ano: number | null; ementa: string | null } | null;
}

/**
 * Seção 06 da home: uma votação acompanhada pelo ZIL, cadeira por cadeira.
 * A seção inteira — título incluído — some se a API não responder ou a
 * votação não estiver no banco: na home, um erro não explica nada.
 */
export function VotacaoDestaque() {
  const [votacao, setVotacao] = useState<Votacao | null>(null);
  const [votos, setVotos] = useState<VotoIndividual[]>([]);
  const [estado, setEstado] = useState<"carregando" | "pronto" | "falhou">("carregando");
  const [grupo, setGrupo] = useState<GrupoVoto | "">("");

  useEffect(() => {
    async function carregar() {
      try {
        const lista: Votacao[] = await fetch(`${API_BASE}/votacoes?fonte_id=${VOTACAO_DESTAQUE}`).then((r) => r.json());
        const v = lista[0];
        if (!v) throw new Error(`votação ${VOTACAO_DESTAQUE} não está no banco`);
        const res = await fetch(`${API_BASE}/votacoes/${v.id}/votos`);
        const vs: VotoIndividual[] = await res.json();
        if (!vs.length) throw new Error("votação sem voto individual");
        setVotacao(v);
        setVotos(vs);
        setEstado("pronto");
      } catch (err) {
        console.error("Votação em destaque:", err);
        setEstado("falhou");
      }
    }
    carregar();
  }, []);

  if (estado === "falhou") return null;

  const p = votacao?.proposicao;
  const rotulo = p ? `${p.tipo ?? ""} ${p.numero ?? ""}/${p.ano ?? ""}`.trim() : "";
  // A ementa oficial, e não o resumo gerado: a home não pode depender de
  // um resumo que ninguém revisou. Quando a Câmara reescreveu a ementa, vale
  // a nova.
  const ementa = p?.ementa?.split(/NOVA EMENTA:\s*/i).pop()?.trim();

  return (
    <section className="zil-secao">
      <TituloSecao
        chapeu="06"
        titulo="Onde o voto pela soberania está"
        descricao="Uma das votações que o ZIL acompanha, cadeira por cadeira. Toque num grupo para destacá-lo."
      />
      <div className="grid gap-4 md:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
        <Card className="grid gap-4 content-start">
          {estado === "carregando" || !votacao ? (
            <div aria-busy="true" aria-label="Carregando votação" className="grid gap-4">
              <Esqueleto className="aspect-[2/1] w-full rounded-[999px_999px_16px_16px]" />
              <Esqueleto className="h-[30px] w-64 justify-self-center rounded-pilula" />
            </div>
          ) : (
            <HemicicloVotacao
              votos={votos}
              cadeiras={CADEIRAS[votacao.fonte] ?? 513}
              direcao={votacao.direcao_esperada}
              grupo={grupo}
              aoMudarGrupo={setGrupo}
            />
          )}
        </Card>
        <Card className="grid gap-4 content-start">
          {estado === "carregando" || !votacao ? (
            <div className="grid gap-3">
              <Esqueleto className="h-4 w-24" />
              <Esqueleto className="h-8 w-40" />
              <Esqueleto className="h-20 w-full" />
            </div>
          ) : (
            <>
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-texto-s text-zil-texto-2 zil-num">
                  Câmara{votacao.data ? ` · ${new Date(votacao.data).toLocaleDateString("pt-BR")}` : ""}
                </span>
                {votacao.resultado && (
                  <Selo tom={votacao.resultado.toLowerCase().includes("aprovad") ? "alinhado" : "padrao"}>{votacao.resultado}</Selo>
                )}
              </div>
              {rotulo && <h3 className="text-titulo-2">{rotulo}</h3>}
              {ementa && <p className="text-texto text-zil-texto-2 line-clamp-6">{ementa}</p>}
              <p className="text-texto-s text-zil-texto-2">
                A direção esperada pelo ZIL nesta votação ainda não passou por validação editorial.
              </p>
              <div>
                <Button href={`/votacoes/${votacao.id}`} variante="secundario">
                  Ver como cada deputado votou
                </Button>
              </div>
            </>
          )}
        </Card>
      </div>
    </section>
  );
}
