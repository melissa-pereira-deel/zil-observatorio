"use client";

import { useState, useEffect } from "react";
import { Aviso, Button, Placar, PlacarLinha, PlacarLinhaEsqueleto, Selo } from "@/components/ui";
import type { Parlamentar } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/** Partido, UF e casa, como no placar completo. */
function metaDe(p: Parlamentar): string {
  const partes = [p.partido, p.uf].filter(Boolean) as string[];
  if (p.fonte) partes.push(p.fonte === "camara" ? "Dep." : "Sen.");
  return partes.join(" · ");
}

/** Âncora de credibilidade do score (UI-001): em quantos votos ele se baseia. */
function tituloDoScore(p: Parlamentar): string {
  return `Baseado em ${p.total_votos_zil} ${p.total_votos_zil === 1 ? "voto" : "votos"} · ver metodologia`;
}

function Coluna({ titulo, lista, carregando }: { titulo: string; lista: Parlamentar[]; carregando: boolean }) {
  return (
    <div className="grid content-start gap-4">
      <h3 className="text-titulo-4">{titulo}</h3>
      <Placar rotulo={titulo}>
        {carregando
          ? Array.from({ length: 5 }).map((_, i) => <PlacarLinhaEsqueleto key={i} compacto />)
          : lista.map((p, i) => (
              <PlacarLinha
                key={p.id}
                posicao={i + 1}
                href={`/parlamentar/${p.id}`}
                nome={p.nome}
                fotoUrl={p.foto_url}
                meta={metaDe(p)}
                score={p.score_zil}
                scoreTitle={tituloDoScore(p)}
                compacto
              />
            ))}
      </Placar>
    </div>
  );
}

export function RankingPreview() {
  const [top, setTop] = useState<Parlamentar[]>([]);
  const [bottom, setBottom] = useState<Parlamentar[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const [topRes, bottomRes] = await Promise.all([
          fetch(`${API_BASE}/parlamentares?ordem=score_desc&per_page=5`),
          fetch(`${API_BASE}/parlamentares?ordem=score_asc&per_page=5`),
        ]);

        if (!topRes.ok || !bottomRes.ok) throw new Error("API error");

        const [topData, bottomData] = await Promise.all([topRes.json(), bottomRes.json()]);

        setTop(topData);
        setBottom(bottomData);
      } catch {
        setError(true);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (error) {
    return (
      <Aviso
        tom="contra"
        titulo="Não foi possível carregar a prévia do placar"
        acao={
          <Button href="/ranking" variante="secundario" tamanho="s">
            Ver o placar completo
          </Button>
        }
      >
        Os dados estão sendo carregados pela primeira vez ou a API ainda não está disponível. Tente de novo em instantes.
      </Aviso>
    );
  }

  return (
    <div className="grid gap-8">
      {/* Dados abertos */}
      <div className="flex flex-wrap items-center gap-3">
        <Selo tom="alinhado" ponto>
          Dados públicos
        </Selo>
        <span className="text-texto-s text-zil-texto-2">Acesso livre. Nenhuma conta necessária para consultar.</span>
      </div>

      {/* Duas colunas: mais e menos alinhados */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8">
        <Coluna titulo="Mais alinhados" lista={top} carregando={loading} />
        <Coluna titulo="Menos alinhados" lista={bottom} carregando={loading} />
      </div>

      {/* Ações */}
      <div className="flex flex-col sm:flex-row gap-3">
        <Button href="/ranking" variante="primario" className="flex-1">
          Ver o placar completo
        </Button>
        <Button href="/proposicoes" variante="secundario" className="flex-1">
          Ver proposições
        </Button>
      </div>
    </div>
  );
}
