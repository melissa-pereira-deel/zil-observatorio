"use client";

import { useState, useEffect } from "react";
import { CategoriaBadge } from "@/components/CategoriaBadge";
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

export default function ProposicoesPage() {
  const [proposicoes, setProposicoes] = useState<Proposicao[]>([]);
  const [loading, setLoading] = useState(true);
  const [categoria, setCategoria] = useState<string>("");

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const params = new URLSearchParams({ per_page: "50" });
        if (categoria) params.set("categoria", categoria);
        const res = await fetch(`${API_BASE}/proposicoes?${params}`);
        setProposicoes(await res.json());
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [categoria]);

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
      <div className="flex flex-wrap gap-2 mb-8">
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
            onClick={() => setCategoria(c.code)}
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
            <div
              key={p.id}
              className="py-4 border-b border-zil-divider hover:bg-zil-card transition-colors px-4"
            >
              <div className="flex items-baseline gap-3 mb-2">
                <span className="font-display text-sm text-zil-fg">
                  {p.tipo} {p.numero}/{p.ano}
                </span>
                {p.situacao && (
                  <span className="font-mono text-xs text-zil-muted">
                    {p.situacao}
                  </span>
                )}
              </div>
              <p className="text-sm text-zil-soft leading-relaxed mb-2">
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
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
