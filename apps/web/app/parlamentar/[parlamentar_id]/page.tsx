"use client";

import { useState, useEffect, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ScoreGauge } from "@/components/ScoreGauge";
import { CategoriaBadge } from "@/components/CategoriaBadge";
import { CATEGORIA_LABELS } from "@/lib/categorias";
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
  const router = useRouter();
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
    return Object.entries(map).sort((a, b) => b[1].total - a[1].total);
  }, [votos]);

  const votosFiltrados = filtroCategoria
    ? votos.filter((v) => v.categorias_zil?.includes(filtroCategoria))
    : votos;

  const alinhados = votos.filter((v) => v.alinhado === true).length;
  const contra = votos.filter((v) => v.alinhado === false).length;
  const semDirecao = votos.length - alinhados - contra;
  const pctAlinhado = votos.length > 0 ? Math.round((alinhados / votos.length) * 100) : 0;

  const scoreDisplay =
    parl?.score_zil !== null && parl?.score_zil !== undefined
      ? parl.score_zil > 0
        ? `+${parl.score_zil.toFixed(1)}`
        : parl.score_zil.toFixed(1)
      : null;

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
      <button
        onClick={() => router.back()}
        className="font-mono text-xs text-zil-muted hover:text-zil-green mb-8 inline-block"
      >
        ← Voltar
      </button>

      {/* Profile header */}
      <div className="flex items-start gap-6 flex-wrap mb-8">
        <div className="w-20 h-20 rounded-full bg-zil-divider overflow-hidden shrink-0">
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
      </div>

      {/* Hero Metric Block — UI-013 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-px bg-zil-divider border border-zil-divider mb-10">

        {/* Coluna esquerda: Score */}
        <div className="bg-zil-white px-6 py-5 flex items-center gap-5">
          <ScoreGauge score={parl.score_zil} size="lg" totalVotosZil={votos.length} />
          <div>
            <div className="font-mono text-2xs text-zil-muted uppercase tracking-wider mb-1">
              Score ZIL
            </div>
            <div className="font-display text-4xl text-zil-fg leading-none mb-1">
              {scoreDisplay ?? "—"}
            </div>
            <div className="font-mono text-2xs text-zil-muted">
              escala de −10 a +10
            </div>
            {parl.score_atualizado_em && (
              <div className="font-mono text-2xs text-zil-muted opacity-60 mt-1">
                atualizado {new Date(parl.score_atualizado_em).toLocaleDateString("pt-BR")}
              </div>
            )}
          </div>
        </div>

        {/* Coluna direita: Proporção de alinhamento */}
        <div className="bg-zil-white px-6 py-5">
          <div className="font-mono text-2xs text-zil-muted uppercase tracking-wider mb-3">
            Alinhamento ZIL
          </div>
          {votos.length > 0 ? (
            <>
              <div className="flex items-baseline gap-2 mb-2">
                <span className="font-display text-3xl text-zil-green leading-none">
                  {alinhados}
                </span>
                <span className="font-mono text-sm text-zil-muted">
                  de {votos.length} votos
                </span>
                <span className="font-mono text-sm text-zil-soft font-semibold">
                  ({pctAlinhado}%)
                </span>
              </div>
              <div className="h-2 bg-zil-divider rounded-full overflow-hidden mb-2">
                <div
                  className="h-full bg-zil-green rounded-full transition-all"
                  style={{ width: `${pctAlinhado}%` }}
                />
              </div>
              <div className="font-mono text-2xs text-zil-muted">
                {contra > 0 && <span>{contra} contra · </span>}
                {semDirecao > 0 && <span>{semDirecao} sem posição definida</span>}
              </div>
            </>
          ) : (
            <p className="font-mono text-xs text-zil-muted">
              Nenhuma votação ZIL registrada para este parlamentar.
              <br />
              <span className="opacity-70">
                A cobertura atual inclui votações da Câmara dos Deputados.
              </span>
            </p>
          )}
        </div>
      </div>

      {/* Category breakdown */}
      {breakdown.length > 0 && (
        <div className="mb-10">
          <h2 className="font-display text-base uppercase tracking-wide mb-1">
            Participação por pauta
          </h2>
          {/* UI-015: instrução de interatividade */}
          <p className="font-mono text-2xs text-zil-muted mb-4">
            Clique em uma pauta para filtrar o histórico abaixo
          </p>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {breakdown.map(([cat, stats]) => {
              const pct = stats.total > 0
                ? Math.round((stats.alinhados / stats.total) * 100)
                : 0;
              return (
                <button
                  key={cat}
                  onClick={() => setFiltroCategoria(filtroCategoria === cat ? "" : cat)}
                  title={`Filtrar histórico por ${CATEGORIA_LABELS[cat] ?? cat}`}
                  className={`text-left p-3 border transition-colors ${
                    filtroCategoria === cat
                      ? "border-zil-green bg-zil-green/5"
                      : "border-zil-divider hover:border-zil-green"
                  }`}
                >
                  <div className="font-mono text-xs text-zil-muted mb-1">{cat}</div>
                  <div className="font-display text-sm text-zil-fg">
                    {CATEGORIA_LABELS[cat] ?? cat}
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

          {/* UI-015: filtro ativo com badge */}
          {filtroCategoria && (
            <div className="mt-3 flex items-center gap-2">
              <span className="font-mono text-xs text-zil-soft border border-zil-green/40 px-2 py-0.5 bg-zil-green/5">
                Filtrando: {CATEGORIA_LABELS[filtroCategoria] ?? filtroCategoria}
              </span>
              <button
                onClick={() => setFiltroCategoria("")}
                className="font-mono text-xs text-zil-muted hover:text-zil-fg"
              >
                × Limpar
              </button>
            </div>
          )}
        </div>
      )}

      {/* Vote history — UI-017: título com contagem */}
      <div className="flex items-baseline justify-between mb-4">
        <h2 className="font-display text-base uppercase tracking-wide">
          Histórico de votos em pautas ZIL
          {filtroCategoria && (
            <span className="font-mono text-xs text-zil-muted normal-case tracking-normal ml-2">
              — {CATEGORIA_LABELS[filtroCategoria] ?? filtroCategoria}
            </span>
          )}
        </h2>
        <span className="font-mono text-xs text-zil-muted shrink-0">
          {filtroCategoria
            ? `${votosFiltrados.length} de ${votos.length}`
            : votos.length}{" "}
          votações
        </span>
      </div>

      {/* UI-014: Legenda do duplo encoding */}
      {votos.length > 0 && (
        <div className="flex flex-wrap gap-x-5 gap-y-1 mb-3 pb-3 border-b border-zil-divider">
          <span className="font-mono text-2xs text-zil-muted flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-zil-green inline-block shrink-0" />
            alinhado com ZIL
          </span>
          <span className="font-mono text-2xs text-zil-muted flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-zil-orange inline-block shrink-0" />
            contra a posição ZIL
          </span>
          <span className="font-mono text-2xs text-zil-muted flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-zil-divider inline-block shrink-0" />
            sem posição definida
          </span>
          <span className="font-mono text-2xs text-zil-muted opacity-70">
            · badge = voto registrado
          </span>
        </div>
      )}

      {votosFiltrados.length === 0 ? (
        <p className="text-sm text-zil-muted py-8">
          {filtroCategoria
            ? "Nenhuma votação nessa categoria."
            : "Nenhuma votação ZIL registrada para este parlamentar."}
        </p>
      ) : (
        <div>
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
