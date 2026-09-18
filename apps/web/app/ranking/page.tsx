"use client";

import { useState, useEffect } from "react";
import { ParlamentarCard } from "@/components/ParlamentarCard";
import type { Parlamentar } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const UFS = [
  "AC","AL","AM","AP","BA","CE","DF","ES","GO","MA","MG","MS","MT",
  "PA","PB","PE","PI","PR","RJ","RN","RO","RR","RS","SC","SE","SP","TO",
];

function SkeletonRow() {
  return (
    <div className="flex items-center gap-4 py-4 border-b border-zil-divider animate-pulse">
      <div className="w-8 h-4 bg-zil-card rounded" />
      <div className="w-10 h-10 rounded-full bg-zil-card shrink-0" />
      <div className="flex-1 space-y-2">
        <div className="h-4 bg-zil-card rounded w-48" />
        <div className="h-3 bg-zil-card rounded w-32" />
      </div>
      <div className="w-12 h-12 rounded-full bg-zil-card shrink-0" />
    </div>
  );
}

export default function RankingPage() {
  const [parlamentares, setParlamentares] = useState<Parlamentar[]>([]);
  const [partidos, setPartidos] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  const [fonte, setFonte] = useState("");
  const [uf, setUf] = useState("");
  const [partido, setPartido] = useState("");
  const [busca, setBusca] = useState("");
  const [ordem, setOrdem] = useState("score_desc");

  useEffect(() => {
    fetch(`${API_BASE}/parlamentares/partidos/ranking`)
      .then((r) => r.json())
      .then((data: { partido: string }[]) =>
        setPartidos(data.map((d) => d.partido).sort())
      )
      .catch(() => {});
  }, []);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const params = new URLSearchParams({ ordem, per_page: "600" });
        if (fonte) params.set("fonte", fonte);
        if (uf) params.set("uf", uf);
        if (partido) params.set("partido", partido);
        const res = await fetch(`${API_BASE}/parlamentares?${params}`);
        setParlamentares(await res.json());
      } catch (err) {
        console.error("Erro ao carregar ranking:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [fonte, uf, partido, ordem]);

  const filtered = busca
    ? parlamentares.filter((p) =>
        p.nome.toLowerCase().includes(busca.toLowerCase())
      )
    : parlamentares;

  const comScore = filtered.filter((p) => p.score_zil !== null);
  const semScore = filtered.filter((p) => p.score_zil === null);

  const hasFilters = !!(busca || fonte || uf || partido);

  function clearFilters() {
    setBusca("");
    setFonte("");
    setUf("");
    setPartido("");
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-12">
      {/* Header — UI-006: sem letra decorativa */}
      <h1 className="font-display text-2xl uppercase tracking-wide mb-2">
        Placar ZIL
      </h1>
      <p className="text-sm text-zil-soft mb-10 max-w-lg">
        Score de alinhamento com a soberania industrial do Brasil, de −10
        (contra) a +10 (a favor), calculado a partir dos votos nas votações
        selecionadas. Não é um índice de toda a atuação parlamentar — é um
        placar de pautas escolhidas, e o critério de escolha está na{" "}
        <a href="/metodologia" className="underline">metodologia</a>.
      </p>

      {/* Filters — UI-005: filtros numa linha, ordenação separada */}
      <div className="flex flex-wrap gap-3 mb-3">
        <input
          type="text"
          placeholder="Buscar por nome..."
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
          className="px-4 py-2 border border-zil-divider bg-transparent text-sm font-body focus:outline-none focus:border-zil-green w-56"
        />
        <select
          value={fonte}
          onChange={(e) => setFonte(e.target.value)}
          className="px-3 py-2 border border-zil-divider bg-zil-bg text-sm font-body focus:outline-none focus:border-zil-green"
        >
          <option value="">Câmara + Senado</option>
          <option value="camara">Deputados</option>
          <option value="senado">Senadores</option>
        </select>
        <select
          value={uf}
          onChange={(e) => setUf(e.target.value)}
          className="px-3 py-2 border border-zil-divider bg-zil-bg text-sm font-body focus:outline-none focus:border-zil-green"
        >
          <option value="">Todos os estados</option>
          {UFS.map((u) => (
            <option key={u} value={u}>{u}</option>
          ))}
        </select>
        <select
          value={partido}
          onChange={(e) => setPartido(e.target.value)}
          className="px-3 py-2 border border-zil-divider bg-zil-bg text-sm font-body focus:outline-none focus:border-zil-green"
        >
          <option value="">Todos os partidos</option>
          {partidos.map((p) => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
      </div>

      {/* Ordenação separada com label — UI-005 */}
      <div className="flex items-center gap-2 mb-8">
        <span className="font-mono text-2xs text-zil-muted uppercase tracking-wider">
          Ordenar por
        </span>
        <select
          value={ordem}
          onChange={(e) => setOrdem(e.target.value)}
          className="px-3 py-2 border border-zil-divider bg-zil-bg text-sm font-body focus:outline-none focus:border-zil-green"
        >
          <option value="score_desc">Maior score</option>
          <option value="score_asc">Menor score</option>
          <option value="nome">Nome A-Z</option>
        </select>
      </div>

      {/* Results */}
      {loading ? (
        <div className="border-t border-zil-divider">
          {Array.from({ length: 12 }).map((_, i) => (
            <SkeletonRow key={i} />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        /* UI-004: empty state com Limpar filtros */
        <div className="py-16 text-center space-y-3">
          <p className="font-mono text-sm text-zil-muted">
            {hasFilters
              ? "Nenhum resultado para esses filtros."
              : "Nenhum parlamentar encontrado."}
          </p>
          {hasFilters && (
            <button
              onClick={clearFilters}
              className="font-mono text-xs text-zil-green border border-zil-green/40 px-4 py-1.5 hover:bg-zil-green/5 transition-colors"
            >
              Limpar filtros
            </button>
          )}
        </div>
      ) : (
        <>
          {/* UI-003: contagem acima da lista */}
          <div className="flex justify-end mb-2">
            <span className="font-mono text-xs text-zil-muted">
              {comScore.length} com score
              {semScore.length > 0 && (
                <span className="opacity-60"> · {semScore.length} sem votos ZIL suficientes</span>
              )}
            </span>
          </div>

          <div className="border-t border-zil-divider">
            {comScore.map((p, i) => (
              <ParlamentarCard key={p.id} parlamentar={p} rank={i + 1} />
            ))}
          </div>

          {semScore.length > 0 && (
            <div className="mt-10">
              <p className="font-mono text-xs text-zil-muted uppercase tracking-wider mb-4">
                Sem votos ZIL suficientes para calcular score ({semScore.length})
              </p>
              <div className="border-t border-zil-divider opacity-50">
                {semScore.map((p) => (
                  <ParlamentarCard key={p.id} parlamentar={p} />
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
