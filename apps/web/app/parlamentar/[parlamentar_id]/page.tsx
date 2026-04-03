"use client";

import { useState, useEffect, useMemo } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ScoreGauge } from "@/components/ScoreGauge";
import { CategoriaBadge } from "@/components/CategoriaBadge";
import type { VotoHistorico } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ParlamentarDetail {
  id: string;
  nome: string;
  nome_civil: string | null;
  partido: string | null;
  uf: string | null;
  foto_url: string | null;
  email: string | null;
  fonte: string;
  score_zil: number | null;
  score_atualizado_em: string | null;
  frentes_parlamentares: string[] | null;
}

const LABEL: Record<string, string> = {
  "ZIL-FER": "Fertilizantes",
  "ZIL-MIN": "Minerais",
  "ZIL-SEM": "Semicondutores",
  "ZIL-ENE": "Energia",
  "ZIL-DIG": "Digital",
  "ZIL-DEF": "Defesa",
  "ZIL-EDU": "Educação",
  "ZIL-AGR": "Agro",
  "ZIL-COM": "Comércio",
};

const VOTO_LABEL: Record<string, string> = {
  sim: "SIM",
  nao: "NÃO",
  abstencao: "ABSTENÇÃO",
  ausente: "AUSENTE",
  obstrucao: "OBSTRUÇÃO",
  artigo_17: "ART.17",
};

export default function ParlamentarPage() {
  const params = useParams();
  const id = params?.parlamentar_id as string;

  const [parl, setParl] = useState<ParlamentarDetail | null>(null);
  const [votos, setVotos] = useState<VotoHistorico[]>([]);
  const [loading, setLoading] = useState(true);
  const [filtroCategoria, setFiltroCategoria] = useState("");

  useEffect(() => {
    if (!id) return;
    async function load() {
      setLoading(true);
      try {
        const [pRes, vRes] = await Promise.all([
          fetch(`${API_BASE}/parlamentares/${id}`),
          fetch(`${API_BASE}/parlamentares/${id}/votos-zil`),
        ]);
        setParl(await pRes.json());
        setVotos(await vRes.json());
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  // Category breakdown computed from vote history
  const breakdown = useMemo(() => {
    const map: Record<string, { alinhados: number; contra: number; total: number }> = {};
    for (const v of votos) {
      for (const cat of v.categorias_zil ?? []) {
        if (!map[cat]) map[cat] = { alinhados: 0, contra: 0, total: 0 };
        map[cat].total++;
        if (v.alinhado === true) map[cat].alinhados++;
        if (v.alinhado === false) map[cat].contra++;
      }
    }
    return Object.entries(map)
      .sort((a, b) => b[1].total - a[1].total);
  }, [votos]);

  const votosFiltrados = filtroCategoria
    ? votos.filter((v) => v.categorias_zil?.includes(filtroCategoria))
    : votos;

  const alinhados = votos.filter((v) => v.alinhado === true).length;
  const contra = votos.filter((v) => v.alinhado === false).length;

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-20 text-center font-mono text-sm text-zil-muted">
        Carregando...
      </div>
    );
  }

  if (!parl) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-20 text-center font-mono text-sm text-zil-muted">
        Parlamentar não encontrado.
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-12">
      {/* Back */}
      <Link
        href="/ranking"
        className="font-mono text-xs text-zil-muted hover:text-zil-green mb-8 inline-block"
      >
        ← Voltar ao ranking
      </Link>

      {/* Profile header */}
      <div className="flex items-start gap-6 flex-wrap mb-10">
        <div className="w-24 h-24 rounded-full bg-zil-divider overflow-hidden shrink-0">
          {parl.foto_url && (
            <img
              src={parl.foto_url}
              alt={parl.nome}
              className="w-full h-full object-cover"
            />
          )}
        </div>

        <div className="flex-1 min-w-0">
          <h1 className="font-display text-2xl uppercase tracking-wide">
            {parl.nome}
          </h1>
          {parl.nome_civil && parl.nome_civil !== parl.nome && (
            <p className="text-sm text-zil-muted mt-1">{parl.nome_civil}</p>
          )}
          <div className="flex items-center gap-3 mt-2 text-sm text-zil-soft">
            {parl.partido && <span className="font-semibold">{parl.partido}</span>}
            {parl.uf && <span>· {parl.uf}</span>}
            <span className="font-mono text-xs opacity-50">
              {parl.fonte === "camara" ? "Deputado(a) Federal" : "Senador(a)"}
            </span>
          </div>
          {parl.email && (
            <a
              href={`mailto:${parl.email}`}
              className="text-sm text-zil-green hover:underline mt-2 inline-block"
            >
              {parl.email}
            </a>
          )}
        </div>

        <div className="text-center">
          <ScoreGauge score={parl.score_zil} size="lg" />
          <p className="font-mono text-xs text-zil-muted mt-2">Score ZIL</p>
          {parl.score_atualizado_em && (
            <p className="font-mono text-xs text-zil-muted opacity-50 mt-1">
              atualizado {new Date(parl.score_atualizado_em).toLocaleDateString("pt-BR")}
            </p>
          )}
        </div>
      </div>

      {/* Stats bar */}
      <div className="flex gap-8 py-4 border-y border-zil-divider mb-10">
        <div>
          <div className="font-display text-xl text-zil-green">{alinhados}</div>
          <div className="font-mono text-xs text-zil-muted">votos alinhados</div>
        </div>
        <div>
          <div className="font-display text-xl text-zil-orange">{contra}</div>
          <div className="font-mono text-xs text-zil-muted">votos contra</div>
        </div>
        <div>
          <div className="font-display text-xl text-zil-soft">{votos.length}</div>
          <div className="font-mono text-xs text-zil-muted">total pautas ZIL</div>
        </div>
      </div>

      {/* Category breakdown */}
      {breakdown.length > 0 && (
        <div className="mb-10">
          <h2 className="font-display text-base uppercase tracking-wide mb-4">
            Participação por pauta
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {breakdown.map(([cat, stats]) => {
              const pct = stats.total > 0
                ? Math.round((stats.alinhados / stats.total) * 100)
                : 0;
              return (
                <button
                  key={cat}
                  onClick={() => setFiltroCategoria(filtroCategoria === cat ? "" : cat)}
                  className={`text-left p-3 border transition-colors ${
                    filtroCategoria === cat
                      ? "border-zil-green bg-zil-green/5"
                      : "border-zil-divider hover:border-zil-green"
                  }`}
                >
                  <div className="font-mono text-xs text-zil-muted mb-1">{cat}</div>
                  <div className="font-display text-sm text-zil-fg">
                    {LABEL[cat] ?? cat}
                  </div>
                  <div className="flex items-center gap-2 mt-2">
                    <div className="flex-1 h-1 bg-zil-divider rounded-full overflow-hidden">
                      <div
                        className="h-full bg-zil-green rounded-full"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <span className="font-mono text-xs text-zil-muted whitespace-nowrap">
                      {stats.alinhados}/{stats.total}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
          {filtroCategoria && (
            <button
              onClick={() => setFiltroCategoria("")}
              className="mt-3 font-mono text-xs text-zil-muted hover:text-zil-fg"
            >
              × Limpar filtro
            </button>
          )}
        </div>
      )}

      {/* Vote history */}
      <h2 className="font-display text-base uppercase tracking-wide mb-4">
        Histórico de votos em pautas ZIL
        {filtroCategoria && (
          <span className="font-mono text-xs text-zil-muted normal-case tracking-normal ml-2">
            — {LABEL[filtroCategoria] ?? filtroCategoria}
          </span>
        )}
      </h2>

      {votosFiltrados.length === 0 ? (
        <p className="text-sm text-zil-muted py-8">
          Nenhuma votação registrada{filtroCategoria ? " nessa categoria" : ""}.
        </p>
      ) : (
        <div className="border-t border-zil-divider">
          {votosFiltrados.map((v) => (
            <div
              key={v.votacao_id}
              className="py-4 border-b border-zil-divider flex items-start gap-4"
            >
              <div
                className={`w-2 h-2 rounded-full mt-2 shrink-0 ${
                  v.alinhado === true
                    ? "bg-zil-green"
                    : v.alinhado === false
                    ? "bg-zil-orange"
                    : "bg-zil-divider"
                }`}
              />

              <div className="flex-1 min-w-0">
                {/* Proposição como identificador principal */}
                {v.proposicao_label && (
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-display text-sm text-zil-fg">
                      {v.proposicao_label}
                    </span>
                    {v.proposicao_id && (
                      <Link
                        href={`/proposicoes/${v.proposicao_id}`}
                        className="font-mono text-xs text-zil-muted hover:text-zil-green"
                        onClick={(e) => e.stopPropagation()}
                      >
                        ver proposição ↗
                      </Link>
                    )}
                  </div>
                )}
                {/* Descrição processual como secundária */}
                <p className={`leading-relaxed ${v.proposicao_label ? "text-xs text-zil-muted" : "text-sm text-zil-fg"}`}>
                  {v.descricao || "Votação sem descrição"}
                </p>
                <div className="flex flex-wrap items-center gap-2 mt-2">
                  {v.categorias_zil?.map((c) => (
                    <CategoriaBadge key={c} codigo={c} />
                  ))}
                  {v.data && (
                    <span className="font-mono text-xs text-zil-muted">
                      {new Date(v.data).toLocaleDateString("pt-BR")}
                    </span>
                  )}
                  <Link
                    href={`/votacoes/${v.votacao_id}`}
                    className="font-mono text-xs text-zil-green hover:underline"
                    onClick={(e) => e.stopPropagation()}
                  >
                    ver votação →
                  </Link>
                </div>
              </div>

              <span
                className={`shrink-0 font-mono text-xs px-3 py-1 rounded-sm ${
                  v.voto === "sim"
                    ? "bg-zil-green/10 text-zil-green"
                    : v.voto === "nao"
                    ? "bg-zil-orange-light text-zil-orange"
                    : "bg-zil-card text-zil-muted"
                }`}
              >
                {VOTO_LABEL[v.voto] ?? v.voto.toUpperCase()}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
