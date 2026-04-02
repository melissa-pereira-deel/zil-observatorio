"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { ParlamentarCard } from "@/components/ParlamentarCard";
import { Button, Badge } from "@/components/ui";
import type { Parlamentar } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function SkeletonCard() {
  return (
    <div className="flex items-center gap-4 py-4 px-4 border-b border-zil-divider animate-pulse">
      <div className="w-8 h-4 bg-zil-divider rounded" />
      <div className="w-12 h-12 rounded-full bg-zil-divider" />
      <div className="flex-1 space-y-2">
        <div className="h-4 bg-zil-divider rounded w-3/4" />
        <div className="h-3 bg-zil-divider rounded w-1/2" />
      </div>
      <div className="w-10 h-10 rounded-full bg-zil-divider" />
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

        const [topData, bottomData] = await Promise.all([
          topRes.json(),
          bottomRes.json(),
        ]);

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
      <div className="text-center py-12 space-y-4">
        <p className="text-sm text-zil-muted">
          Os dados estão sendo carregados pela primeira vez ou a API ainda não
          está disponível.
        </p>
        <Button href="/ranking" variant="ghost" size="sm">
          Ir para o ranking completo
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Open data badge */}
      <div className="flex flex-wrap gap-3 items-center">
        <Badge variant="green">Dados públicos</Badge>
        <span className="text-xs text-zil-muted">
          Acesso livre. Nenhuma conta necessária para consultar.
        </span>
      </div>

      {/* Two-column ranking */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8">
        {/* Top aligned */}
        <div>
          <div className="flex items-center gap-2 mb-3 pb-2 border-b-2 border-zil-green">
            <div className="w-2 h-2 rounded-full bg-zil-green" />
            <h3 className="font-display text-sm uppercase tracking-wide text-zil-green">
              Mais alinhados
            </h3>
          </div>
          <div className="border-t border-zil-divider">
            {loading
              ? Array.from({ length: 5 }).map((_, i) => (
                  <SkeletonCard key={i} />
                ))
              : top.map((p, i) => (
                  <ParlamentarCard key={p.id} parlamentar={p} rank={i + 1} />
                ))}
          </div>
        </div>

        {/* Least aligned */}
        <div>
          <div className="flex items-center gap-2 mb-3 pb-2 border-b-2 border-zil-orange">
            <div className="w-2 h-2 rounded-full bg-zil-orange" />
            <h3 className="font-display text-sm uppercase tracking-wide text-zil-orange">
              Menos alinhados
            </h3>
          </div>
          <div className="border-t border-zil-divider">
            {loading
              ? Array.from({ length: 5 }).map((_, i) => (
                  <SkeletonCard key={i} />
                ))
              : bottom.map((p, i) => (
                  <ParlamentarCard key={p.id} parlamentar={p} rank={i + 1} />
                ))}
          </div>
        </div>
      </div>

      {/* CTAs */}
      <div className="flex flex-col sm:flex-row gap-3">
        <Button href="/ranking" variant="primary" className="flex-1">
          Ver ranking completo
        </Button>
        <Button href="/proposicoes" variant="secondary" className="flex-1">
          Ver proposições
        </Button>
      </div>
    </div>
  );
}
