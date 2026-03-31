"use client";

import { useState, useEffect } from "react";
import { ParlamentarCard } from "@/components/ParlamentarCard";
import type { Parlamentar } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const UFS = [
  "AC","AL","AM","AP","BA","CE","DF","ES","GO","MA","MG","MS","MT",
  "PA","PB","PE","PI","PR","RJ","RN","RO","RR","RS","SC","SE","SP","TO",
];

export default function RankingPage() {
  const [parlamentares, setParlamentares] = useState<Parlamentar[]>([]);
  const [loading, setLoading] = useState(true);
  const [fonte, setFonte] = useState<string>("");
  const [uf, setUf] = useState<string>("");
  const [busca, setBusca] = useState<string>("");
  const [ordem, setOrdem] = useState<string>("score_desc");

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const params = new URLSearchParams({ ordem, per_page: "100" });
        if (fonte) params.set("fonte", fonte);
        if (uf) params.set("uf", uf);
        const res = await fetch(`${API_BASE}/parlamentares?${params}`);
        const data = await res.json();
        setParlamentares(data);
      } catch (err) {
        console.error("Erro ao carregar ranking:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [fonte, uf, ordem]);

  const filtered = busca
    ? parlamentares.filter((p) =>
        p.nome.toLowerCase().includes(busca.toLowerCase())
      )
    : parlamentares;

  return (
    <div className="max-w-5xl mx-auto px-6 py-12">
      {/* Header */}
      <div className="flex items-baseline gap-4 mb-2">
        <span className="font-display text-6xl text-zil-divider">R</span>
        <h1 className="font-display text-2xl uppercase tracking-wide">
          Ranking ZIL
        </h1>
      </div>
      <p className="text-sm text-zil-soft mb-10 max-w-lg">
        Score de alinhamento com a soberania industrial do Brasil, de -10
        (contra) a +10 (a favor), calculado a partir dos votos em pautas ZIL.
      </p>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-8">
        {/* Search */}
        <input
          type="text"
          placeholder="Buscar por nome..."
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
          className="px-4 py-2 border border-zil-divider bg-transparent text-sm font-body focus:outline-none focus:border-zil-green w-64"
        />

        {/* Fonte */}
        <select
          value={fonte}
          onChange={(e) => setFonte(e.target.value)}
          className="px-3 py-2 border border-zil-divider bg-transparent text-sm font-body focus:outline-none focus:border-zil-green"
        >
          <option value="">Todos</option>
          <option value="camara">Deputados</option>
          <option value="senado">Senadores</option>
        </select>

        {/* UF */}
        <select
          value={uf}
          onChange={(e) => setUf(e.target.value)}
          className="px-3 py-2 border border-zil-divider bg-transparent text-sm font-body focus:outline-none focus:border-zil-green"
        >
          <option value="">Todos os estados</option>
          {UFS.map((u) => (
            <option key={u} value={u}>
              {u}
            </option>
          ))}
        </select>

        {/* Ordem */}
        <select
          value={ordem}
          onChange={(e) => setOrdem(e.target.value)}
          className="px-3 py-2 border border-zil-divider bg-transparent text-sm font-body focus:outline-none focus:border-zil-green"
        >
          <option value="score_desc">Maior score</option>
          <option value="score_asc">Menor score</option>
          <option value="nome">Nome A-Z</option>
        </select>
      </div>

      {/* Results */}
      {loading ? (
        <div className="py-20 text-center text-zil-muted font-mono text-sm">
          Carregando parlamentares...
        </div>
      ) : filtered.length === 0 ? (
        <div className="py-20 text-center text-zil-muted font-mono text-sm">
          Nenhum parlamentar encontrado.
        </div>
      ) : (
        <div className="border-t border-zil-divider">
          {filtered.map((p, i) => (
            <ParlamentarCard key={p.id} parlamentar={p} rank={i + 1} />
          ))}
        </div>
      )}

      {/* Count */}
      <div className="mt-6 text-xs font-mono text-zil-muted">
        {filtered.length} parlamentares
      </div>
    </div>
  );
}
