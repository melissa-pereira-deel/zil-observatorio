"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Marco {
  codigo: string;
  nome: string;
  categoria: string;
  descricao: string;
  valor_atual: number;
  unidade: string;
  tendencia: "avancando" | "retrocedendo" | "estavel";
  meta?: number;
  prazo?: number;
  fonte: string;
  fonte_url: string;
  ultima_atualizacao: string;
  governo_referencia: string;
}

const TENDENCIA = {
  avancando: { symbol: "▲", label: "Avançando", color: "text-zil-green" },
  retrocedendo: { symbol: "▼", label: "Retrocedendo", color: "text-zil-orange" },
  estavel: { symbol: "→", label: "Estável", color: "text-zil-gold" },
};

const CAT_LABEL: Record<string, string> = {
  "ZIL-FER": "Fertilizantes",
  "ZIL-MIN": "Minerais",
  "ZIL-SEM": "Semicondutores",
  "ZIL-ENE": "Energia",
  "ZIL-DIG": "Digital",
  "ZIL-DEF": "Defesa",
  "ZIL-EDU": "Capital Humano",
  "ZIL-AGR": "Agro",
  "ZIL-COM": "Comércio",
};

function MarcoCard({ marco }: { marco: Marco }) {
  const tend = TENDENCIA[marco.tendencia] ?? TENDENCIA.estavel;
  const progresso =
    marco.meta !== undefined
      ? Math.min(100, Math.round((marco.valor_atual / marco.meta) * 100))
      : null;

  return (
    <div className="border border-zil-divider p-5 bg-zil-white hover:border-zil-green transition-colors">
      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-3">
        <div>
          <span className="font-mono text-xs text-zil-muted">{marco.categoria}</span>
          <h3 className="font-display text-sm uppercase tracking-wide mt-0.5">
            {marco.nome}
          </h3>
        </div>
        <span className={`font-mono text-sm font-bold ${tend.color}`} title={tend.label}>
          {tend.symbol}
        </span>
      </div>

      {/* Value */}
      <div className="mb-3">
        <span className="font-display text-3xl text-zil-fg">{marco.valor_atual}</span>
        <span className="font-mono text-xs text-zil-muted ml-2">{marco.unidade}</span>
      </div>

      {/* Progress bar toward goal */}
      {marco.meta !== undefined && progresso !== null && (
        <div className="mb-3">
          <div className="flex justify-between font-mono text-xs text-zil-muted mb-1">
            <span>Meta: {marco.meta} {marco.unidade.split(" ")[0]}</span>
            {marco.prazo && <span>até {marco.prazo}</span>}
          </div>
          <div className="h-1.5 bg-zil-divider rounded-full overflow-hidden">
            <div
              className="h-full bg-zil-gold rounded-full"
              style={{ width: `${progresso}%` }}
            />
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between gap-2 mt-4 pt-3 border-t border-zil-divider">
        <a
          href={marco.fonte_url}
          target="_blank"
          rel="noopener noreferrer"
          className="font-mono text-xs text-zil-muted hover:text-zil-green truncate"
        >
          {marco.fonte}
        </a>
        <span className="font-mono text-xs text-zil-muted shrink-0">
          {marco.ultima_atualizacao}
        </span>
      </div>
    </div>
  );
}

export default function BussulaPage() {
  const [marcos, setMarcos] = useState<Marco[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/bussula`)
      .then((r) => r.json())
      .then(setMarcos)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const porCategoria = marcos.reduce<Record<string, Marco[]>>((acc, m) => {
    if (!acc[m.categoria]) acc[m.categoria] = [];
    acc[m.categoria].push(m);
    return acc;
  }, {});

  return (
    <div className="max-w-5xl mx-auto px-6 py-12">
      {/* Header */}
      <div className="flex items-baseline gap-4 mb-2">
        <span className="font-display text-6xl text-zil-divider">B</span>
        <h1 className="font-display text-2xl uppercase tracking-wide">
          Bússola ZIL
        </h1>
      </div>
      <p className="text-sm text-zil-soft mb-2 max-w-xl">
        Estado atual da soberania industrial brasileira, por categoria estratégica.
        Indicadores verificáveis a partir de fontes oficiais.
      </p>
      <p className="text-xs font-mono text-zil-muted mb-10 max-w-xl">
        Atualização trimestral via PR. Fontes linkadas diretamente em cada indicador.{" "}
        <Link href="/metodologia" className="text-zil-green hover:underline">
          Como isso é calculado?
        </Link>
      </p>

      {loading ? (
        <div className="py-20 text-center font-mono text-sm text-zil-muted">
          Carregando indicadores...
        </div>
      ) : marcos.length === 0 ? (
        <div className="py-20 text-center font-mono text-sm text-zil-muted max-w-md mx-auto">
          <p className="mb-2">Nenhum indicador publicado ainda.</p>
          <p>
            Os indicadores da Bússola são gerenciados via{" "}
            <code className="bg-zil-card px-1">data/bussula/marcos.yml</code> no repositório.
          </p>
        </div>
      ) : (
        <div className="space-y-10">
          {Object.entries(porCategoria).map(([cat, items]) => (
            <div key={cat}>
              <h2 className="font-mono text-xs uppercase tracking-widest text-zil-muted mb-4">
                {CAT_LABEL[cat] ?? cat} · {cat}
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {items.map((m) => (
                  <MarcoCard key={m.codigo} marco={m} />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Legend */}
      <div className="mt-12 pt-6 border-t border-zil-divider flex flex-wrap gap-6 font-mono text-xs text-zil-muted">
        <span className="text-zil-green">▲ Avançando em direção à meta</span>
        <span className="text-zil-gold">→ Estável</span>
        <span className="text-zil-orange">▼ Retrocedendo</span>
      </div>
    </div>
  );
}
