"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Aviso, Button, Icone, Placar, PlacarLinha, PlacarLinhaEsqueleto, Selo } from "@/components/ui";
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

function Coluna({ titulo, href, lista, carregando }: { titulo: string; href: string; lista: Parlamentar[]; carregando: boolean }) {
  return (
    <div className="grid content-start gap-4">
      {/* O título leva ao placar já na ordem daquela coluna. */}
      <h3 className="text-titulo-4">
        <Link
          href={href}
          className="group inline-flex items-center gap-1 text-zil-texto no-underline transition-colors duration-toque hover:text-zil-texto-2"
        >
          {titulo}
          <Icone nome="chevron-direita" className="text-zil-texto-3 transition-transform duration-padrao ease-padrao group-hover:translate-x-[3px]" />
        </Link>
      </h3>
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
        <Coluna titulo="Mais alinhados" href="/ranking" lista={top} carregando={loading} />
        <Coluna titulo="Menos alinhados" href="/ranking?ordem=score_asc" lista={bottom} carregando={loading} />
      </div>

      {/* Um link de texto, não dois botões: a seção é uma prévia, e o primário
          da página está na abertura. */}
      <div>
        <Button href="/ranking" variante="fantasma" tamanho="s" className="-ml-3.5">
          Ver todos os parlamentares
          <Icone nome="chevron-direita" tamanho="s" />
        </Button>
      </div>
    </div>
  );
}
