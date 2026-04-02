"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { CategoriaBadge } from "@/components/CategoriaBadge";
import { ContextoBadge } from "@/components/ContextoBadge";
import type { Proposicao } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const CATEGORIAS = [
  { code: "ZIL-FER", label: "Fertilizantes" },
  { code: "ZIL-MIN", label: "Minerais" },
  { code: "ZIL-SEM", label: "Semicondutores" },
  { code: "ZIL-ENE", label: "Energia" },
  { code: "ZIL-DIG", label: "Digital" },
  { code: "ZIL-DEF", label: "Defesa" },
  { code: "ZIL-EDU", label: "Educação" },
  { code: "ZIL-AGR", label: "Agro" },
  { code: "ZIL-COM", label: "Comércio" },
];

const TIPOS = ["PL", "PEC", "PLP", "MPV", "PDL", "PRC"];

const ANO_ATUAL = new Date().getFullYear();
const ANOS = Array.from({ length: 10 }, (_, i) => ANO_ATUAL - i);

export default function ProposicoesPage() {
  const [proposicoes, setProposicoes] = useState<Proposicao[]>([]);
  const [loading, setLoading] = useState(true);
  const [categoria, setCategoria] = useState("");
  const [tipo, setTipo] = useState("");
  const [ano, setAno] = useState("");

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

  return (
    <div className="max-w-5xl mx-auto px-6 py-12">
      <div className="flex items-baseline gap-4 mb-2">
        <span className="font-display text-6xl text-zil-divider">P</span>
        <h1 className="font-display text-2xl uppercase tracking-wide">
          Proposições
        </h1>
      </div>
      <p className="text-sm text-zil-soft mb-10 max-w-lg">
        Projetos de lei, PECs e requerimentos classificados por pauta de
        soberania industrial.
      </p>

      {/* Category filter */}
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

      {/* Tipo + Ano filters */}
      <div className="flex flex-wrap gap-3 mb-8">
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
      ) : proposicoes.length === 0 ? (
        <div className="py-20 text-center font-mono text-sm text-zil-muted">
          Nenhuma proposição encontrada.
        </div>
      ) : (
        <div className="border-t border-zil-divider">
          {proposicoes.map((p) => (
            <Link
              key={p.id}
              href={`/proposicoes/${p.id}`}
              className="block py-4 border-b border-zil-divider hover:bg-zil-card transition-colors px-4 -mx-4"
            >
              <div className="flex items-baseline gap-3 mb-1">
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
              {p.resumo_simples ? (
                <p className="text-sm text-zil-fg leading-relaxed mb-1 line-clamp-2">
                  {p.resumo_simples}
                </p>
              ) : null}
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
      )}

      {!loading && (
        <div className="mt-6 text-xs font-mono text-zil-muted">
          {proposicoes.length} proposições
        </div>
      )}
    </div>
  );
}
