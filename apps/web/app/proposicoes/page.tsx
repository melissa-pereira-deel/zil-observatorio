"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { CategoriaBadge } from "@/components/CategoriaBadge";
import { ContextoBadge } from "@/components/ContextoBadge";
import { CATEGORIA_LABELS } from "@/lib/categorias";
import type { Proposicao } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const CATEGORIAS = Object.entries(CATEGORIA_LABELS).map(([code, label]) => ({ code, label }));

const TIPOS = ["PL", "PEC", "PLP", "MPV", "PDL", "PRC"];

const ANO_ATUAL = new Date().getFullYear();
const ANOS = Array.from({ length: 10 }, (_, i) => ANO_ATUAL - i);

export default function ProposicoesPage() {
  const [proposicoes, setProposicoes] = useState<Proposicao[]>([]);
  const [loading, setLoading] = useState(true);
  const [categoria, setCategoria] = useState("");
  const [tipo, setTipo] = useState("");
  const [ano, setAno] = useState("");
  const [busca, setBusca] = useState("");

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const params = new URLSearchParams({ per_page: "100" });
        if (categoria) params.set("categoria", categoria);
        if (tipo) params.set("tipo", tipo);
        if (ano) params.set("ano", ano);
        const res = await fetch(`${API_BASE}/proposicoes?${params}`);
        setProposicoes(await res.json());
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [categoria, tipo, ano]);

  const filtered = busca
    ? proposicoes.filter((p) =>
        p.ementa?.toLowerCase().includes(busca.toLowerCase()) ||
        p.resumo_simples?.toLowerCase().includes(busca.toLowerCase())
      )
    : proposicoes;

  const hasFilters = !!(busca || categoria || tipo || ano);

  function clearFilters() {
    setBusca("");
    setCategoria("");
    setTipo("");
    setAno("");
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-12">
      {/* Header — UI-006: sem letra decorativa */}
      <h1 className="font-display text-2xl uppercase tracking-wide mb-2">
        Proposições
      </h1>
      <p className="text-sm text-zil-soft mb-8 max-w-lg">
        Projetos de lei, PECs e requerimentos classificados por pauta de
        soberania industrial.
      </p>

      {/* Category filter buttons */}
      <div className="flex flex-wrap gap-2 mb-4">
        <button
          onClick={() => setCategoria("")}
          className={`px-3 py-1.5 text-xs font-mono tracking-wider border transition-colors ${
            !categoria
              ? "bg-zil-green text-white border-zil-green"
              : "border-zil-divider text-zil-soft hover:border-zil-green"
          }`}
        >
          TODAS
        </button>
        {CATEGORIAS.map((c) => (
          <button
            key={c.code}
            onClick={() => setCategoria(categoria === c.code ? "" : c.code)}
            className={`px-3 py-1.5 text-xs font-mono tracking-wider border transition-colors ${
              categoria === c.code
                ? "bg-zil-green text-white border-zil-green"
                : "border-zil-divider text-zil-soft hover:border-zil-green"
            }`}
          >
            {c.label.toUpperCase()}
          </button>
        ))}
      </div>

      {/* Busca + Tipo + Ano — UI-005: numa linha */}
      <div className="flex flex-wrap gap-3 mb-8">
        <input
          type="text"
          placeholder="Buscar por ementa..."
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
          className="px-4 py-2 border border-zil-divider bg-transparent text-sm font-body focus:outline-none focus:border-zil-green w-64"
        />
        <select
          value={tipo}
          onChange={(e) => setTipo(e.target.value)}
          className="px-3 py-2 border border-zil-divider bg-zil-bg text-sm font-body focus:outline-none focus:border-zil-green"
        >
          <option value="">Todos os tipos</option>
          {TIPOS.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
        <select
          value={ano}
          onChange={(e) => setAno(e.target.value)}
          className="px-3 py-2 border border-zil-divider bg-zil-bg text-sm font-body focus:outline-none focus:border-zil-green"
        >
          <option value="">Todos os anos</option>
          {ANOS.map((a) => (
            <option key={a} value={String(a)}>{a}</option>
          ))}
        </select>
      </div>

      {/* Results */}
      {loading ? (
        <div className="py-20 text-center font-mono text-sm text-zil-muted">
          Carregando proposições...
        </div>
      ) : filtered.length === 0 ? (
        /* UI-004: empty state com Limpar filtros */
        <div className="py-16 text-center space-y-3">
          <p className="font-mono text-sm text-zil-muted">
            {hasFilters
              ? "Nenhum resultado para esses filtros."
              : "Nenhuma proposição encontrada."}
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
              {filtered.length}
              {busca && filtered.length !== proposicoes.length
                ? ` de ${proposicoes.length}`
                : ""}{" "}
              proposições
            </span>
          </div>

          <div className="border-t border-zil-divider">
            {filtered.map((p) => (
              <Link
                key={p.id}
                href={`/proposicoes/${p.id}`}
                className="block py-4 border-b border-zil-divider hover:bg-zil-card transition-colors px-4 -mx-4"
              >
                <div className="flex items-baseline gap-3 mb-1 flex-wrap">
                  <span className="font-display text-sm text-zil-fg">
                    {p.tipo} {p.numero}/{p.ano}
                  </span>
                  {p.situacao && (
                    <span className="font-mono text-xs text-zil-muted">
                      {p.situacao}
                    </span>
                  )}
                  <ContextoBadge status={p.contexto_status} confianca={p.confianca} />
                </div>
                {p.resumo_simples && (
                  <p className="text-sm text-zil-fg leading-relaxed mb-1 line-clamp-2">
                    {p.resumo_simples}
                  </p>
                )}
                <p className="text-xs text-zil-muted leading-relaxed mb-2 line-clamp-2">
                  {p.ementa}
                </p>
                <div className="flex flex-wrap items-center gap-2">
                  {p.categorias_zil?.map((c) => (
                    <CategoriaBadge key={c} codigo={c} />
                  ))}
                  {p.data_apresentacao && (
                    <span className="font-mono text-xs text-zil-muted">
                      {new Date(p.data_apresentacao).toLocaleDateString("pt-BR")}
                    </span>
                  )}
                </div>
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
