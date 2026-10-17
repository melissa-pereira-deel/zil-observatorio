"use client";

import { useState, useEffect, useMemo } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { CategoriaBadge } from "@/components/CategoriaBadge";
import { ContextoBadge } from "@/components/ContextoBadge";
import { DirecaoBadge } from "@/components/DirecaoBadge";
import { Badge } from "@/components/ui/Badge";
import type { Proposicao, ProposicaoContexto } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Votacao {
  id: string;
  fonte_id: string;
  data: string | null;
  descricao: string | null;
  resultado: string | null;
  votos_sim: number | null;
  votos_nao: number | null;
  categorias_zil: string[] | null;
  direcao_esperada: string | null;
  peso: number | null;
}

function resultadoColor(texto: string): "green" | "orange" | "muted" {
  const t = texto.toLowerCase();
  if (t.includes("aprovad")) return "green";
  if (t.includes("rejeitad")) return "orange";
  return "muted";
}

export default function ProposicaoDetailPage() {
  const params = useParams();
  const id = params?.id as string;

  const [proposicao, setProposicao] = useState<Proposicao | null>(null);
  const [votacoes, setVotacoes] = useState<Votacao[]>([]);
  const [contexto, setContexto] = useState<ProposicaoContexto | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    async function load() {
      setLoading(true);
      try {
        const [pRes, vRes, cRes] = await Promise.all([
          fetch(`${API_BASE}/proposicoes/${id}`),
          fetch(`${API_BASE}/proposicoes/${id}/votacoes`),
          fetch(`${API_BASE}/proposicoes/${id}/contexto`),
        ]);
        setProposicao(await pRes.json());
        const vData = await vRes.json();
        setVotacoes(Array.isArray(vData) ? vData : []);
        if (cRes.ok) setContexto(await cRes.json());
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  // UI-010: Síntese da posição ZIL
  const posicaoZil = useMemo(() => {
    const comDirecao = votacoes.filter((v) => v.direcao_esperada !== null);
    if (comDirecao.length === 0) return null;
    const favoraveis = comDirecao.filter((v) => v.direcao_esperada === "sim").length;
    const contrarias = comDirecao.filter((v) => v.direcao_esperada === "nao").length;
    return {
      label:
        favoraveis > 0 && contrarias === 0
          ? "FAVORÁVEL"
          : contrarias > 0 && favoraveis === 0
          ? "CONTRÁRIA"
          : "POSIÇÃO MISTA",
      color:
        favoraveis > 0 && contrarias === 0
          ? ("green" as const)
          : contrarias > 0 && favoraveis === 0
          ? ("orange" as const)
          : ("gold" as const),
      total: comDirecao.length,
    };
  }, [votacoes]);

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-20 text-center font-mono text-sm text-zil-muted">
        Carregando...
      </div>
    );
  }

  if (!proposicao) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-20 text-center font-mono text-sm text-zil-muted">
        Proposição não encontrada.
      </div>
    );
  }

  const hasContexto = contexto?.contexto_status === "pronto" && contexto.resumo_simples;

  return (
    <div className="max-w-5xl mx-auto px-6 py-12">
      {/* Back */}
      <Link
        href="/proposicoes"
        className="font-mono text-xs text-zil-muted hover:text-zil-green mb-8 inline-block"
      >
        ← Voltar às proposições
      </Link>

      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-3 flex-wrap">
          <h1 className="font-display text-2xl uppercase tracking-wide">
            {proposicao.tipo} {proposicao.numero}/{proposicao.ano}
          </h1>
          {proposicao.situacao && (
            <span className="font-mono text-xs text-zil-muted border border-zil-divider px-2 py-1">
              {proposicao.situacao}
            </span>
          )}
          <ContextoBadge
            status={proposicao.contexto_status}
            confianca={proposicao.confianca}
          />
        </div>

        {/* Resumo em linguagem simples */}
        {hasContexto && (
          <p className="text-base text-zil-fg leading-relaxed mb-3 max-w-3xl">
            {contexto!.resumo_simples}
          </p>
        )}

        {/* UI-008: placeholder quando sem análise LLM */}
        {!hasContexto && (
          <p className="text-sm text-zil-muted italic mb-3 max-w-3xl">
            Esta proposição ainda não foi analisada pela plataforma.
            A ementa técnica original está disponível abaixo.
          </p>
        )}

        {/* UI-008: ementa sempre colapsada por padrão */}
        <details className="mb-4">
          <summary className="font-mono text-xs text-zil-muted cursor-pointer select-none hover:text-zil-soft">
            Ver ementa técnica ↓
          </summary>
          <p className="text-sm text-zil-soft leading-relaxed mt-2 max-w-3xl">
            {proposicao.ementa}
          </p>
        </details>

        {/* Impacto ZIL */}
        {contexto?.impacto_zil && (
          <div className="border-l-2 border-zil-green pl-4 mb-4 max-w-3xl">
            <p className="text-sm text-zil-soft leading-relaxed italic">
              {contexto.impacto_zil}
            </p>
          </div>
        )}

        <div className="flex flex-wrap items-center gap-3">
          {proposicao.categorias_zil?.map((c) => (
            <CategoriaBadge key={c} codigo={c} />
          ))}
          {proposicao.data_apresentacao && (
            <span className="font-mono text-xs text-zil-muted">
              Apresentada em{" "}
              {new Date(proposicao.data_apresentacao).toLocaleDateString("pt-BR")}
            </span>
          )}
          {proposicao.url_inteiro_teor && (
            <a
              href={proposicao.url_inteiro_teor}
              target="_blank"
              rel="noopener noreferrer"
              className="font-mono text-xs text-zil-green hover:underline"
            >
              Texto completo ↗
            </a>
          )}
        </div>
      </div>

      {/* UI-012: Context accordion — details/summary nativo (sem useState) */}
      {contexto && (contexto.glossario || contexto.leis_referenciadas?.length) && (
        <details className="mb-10 border border-zil-divider">
          <summary className="px-4 py-3 font-mono text-xs uppercase tracking-wider text-zil-soft cursor-pointer hover:bg-zil-card transition-colors list-none flex items-center justify-between">
            <span>Ver contexto completo</span>
            <span className="text-zil-muted">▼</span>
          </summary>

          <div className="px-4 pb-6 border-t border-zil-divider space-y-6 pt-4">
            {/* Glossário */}
            {contexto.glossario && Object.keys(contexto.glossario).length > 0 && (
              <div>
                <h3 className="font-mono text-xs uppercase tracking-wider text-zil-muted mb-3">
                  Glossário
                </h3>
                <dl className="space-y-2">
                  {Object.entries(contexto.glossario).map(([term, def]) => (
                    <div key={term}>
                      <dt className="font-display text-sm text-zil-fg inline">
                        {term}:{" "}
                      </dt>
                      <dd className="text-sm text-zil-soft inline">{def}</dd>
                    </div>
                  ))}
                </dl>
              </div>
            )}

            {/* Artigos referenciados */}
            {contexto.leis_referenciadas && contexto.leis_referenciadas.length > 0 && (
              <div>
                <h3 className="font-mono text-xs uppercase tracking-wider text-zil-muted mb-3">
                  Leis referenciadas
                </h3>
                <ul className="space-y-3">
                  {contexto.leis_referenciadas.map((lei) => (
                    <li
                      key={`${lei.lei_id}-${lei.numero_artigo}`}
                      className="border border-zil-divider p-3"
                    >
                      <div className="flex items-baseline gap-2 mb-1 flex-wrap">
                        <span className="font-mono text-xs font-semibold text-zil-fg">
                          {lei.lei_id} — Art. {lei.numero_artigo}
                        </span>
                        {lei.status !== "resolvido" && (
                          <span className="font-mono text-xs text-zil-orange">
                            ({lei.status.replace(/_/g, " ")})
                          </span>
                        )}
                        {lei.url_planalto && lei.status === "resolvido" && (
                          <a
                            href={lei.url_planalto}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-mono text-xs text-zil-green hover:underline"
                          >
                            Ver lei ↗
                          </a>
                        )}
                      </div>
                      {lei.texto_snippet && (
                        <p className="text-xs text-zil-muted leading-relaxed line-clamp-3">
                          {lei.texto_snippet}
                        </p>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Metadados */}
            <div className="font-mono text-xs text-zil-muted space-y-1 border-t border-zil-divider pt-4">
              {contexto.enriquecido_em && (
                <p>
                  Atualizado em{" "}
                  {new Date(contexto.enriquecido_em).toLocaleDateString("pt-BR")}
                </p>
              )}
              {contexto.confianca !== null && contexto.confianca !== undefined && (
                <p>Confiança: {Math.round(contexto.confianca * 100)}%</p>
              )}
              <p>
                Modelo: {contexto.modelo_llm} · Pipeline v{contexto.versao_pipeline}
              </p>
            </div>
          </div>
        </details>
      )}

      {/* Votações */}
      <h2 className="font-display text-base uppercase tracking-wide mb-4">
        Votações ({votacoes.length})
      </h2>

      {/* UI-010: Síntese da posição ZIL */}
      {posicaoZil && (
        <div className="flex items-baseline gap-3 mb-6 pb-4 border-b border-zil-divider flex-wrap">
          <span className="font-mono text-xs text-zil-muted">
            ZIL avalia esta proposição como
          </span>
          <span
            className={`font-display text-base ${
              posicaoZil.color === "green"
                ? "text-zil-green"
                : posicaoZil.color === "orange"
                ? "text-zil-orange"
                : "text-zil-gold"
            }`}
          >
            {posicaoZil.label}
          </span>
          <span className="font-mono text-xs text-zil-muted">
            · com base em {posicaoZil.total}{" "}
            {posicaoZil.total === 1 ? "votação monitorada" : "votações monitoradas"}{" "}
            <Link href="/metodologia" className="text-zil-green hover:underline">
              ver metodologia →
            </Link>
          </span>
        </div>
      )}

      {votacoes.length === 0 ? (
        <p className="text-sm text-zil-muted py-8 border-t border-zil-divider">
          Nenhuma votação plenária registrada para esta proposição.
        </p>
      ) : (
        <div className="border-t border-zil-divider">
          {votacoes.map((v) => {
            // UI-011: resultado inferido quando null — mas só quando existe
            // placar para inferir.
            //
            // Votação simbólica não tem voto nominal: a Câmara registra 0 e 0.
            // Com `0 > 0` falso, a regra anterior exibia "Rejeitado*" numa
            // votação aprovada. Três das sete votações curadas são simbólicas,
            // então isso estava no ar. Sem placar, não há o que inferir.
            const temPlacar =
              v.votos_sim !== null &&
              v.votos_nao !== null &&
              v.votos_sim + v.votos_nao > 0;
            const resultadoDisplay =
              v.resultado ??
              (temPlacar ? (v.votos_sim! > v.votos_nao! ? "Aprovado*" : "Rejeitado*") : null);
            const resultadoInferido = !v.resultado && resultadoDisplay !== null;

            return (
              <div key={v.id} className="py-5 border-b border-zil-divider">
                <div className="flex items-start justify-between gap-4 flex-wrap">
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-3 mb-2">
                      {/* UI-007: Badge variant="result" + UI-011: resultado inferido */}
                      {resultadoDisplay && (
                        <Badge
                          variant="result"
                          color={resultadoColor(resultadoDisplay)}
                          title={
                            resultadoInferido
                              ? "Resultado inferido dos votos registrados"
                              : undefined
                          }
                        >
                          {resultadoDisplay}
                        </Badge>
                      )}
                      {v.data && (
                        <span className="font-mono text-xs text-zil-muted">
                          {new Date(v.data).toLocaleDateString("pt-BR")}
                        </span>
                      )}
                      {/* UI-009: DirecaoBadge */}
                      <DirecaoBadge direcao={v.direcao_esperada} />
                    </div>

                    {v.descricao && (
                      <p className="text-xs text-zil-muted leading-relaxed">
                        {v.descricao}
                      </p>
                    )}
                  </div>

                  {/* Placar */}
                  {(v.votos_sim !== null || v.votos_nao !== null) && (
                    <div className="flex gap-4 shrink-0">
                      <div className="text-center">
                        <div className="font-display text-lg text-zil-green">
                          {v.votos_sim ?? "—"}
                        </div>
                        <div className="font-mono text-xs text-zil-muted">SIM</div>
                      </div>
                      <div className="text-center">
                        <div className="font-display text-lg text-zil-orange">
                          {v.votos_nao ?? "—"}
                        </div>
                        <div className="font-mono text-xs text-zil-muted">NÃO</div>
                      </div>
                    </div>
                  )}
                </div>

                <div className="mt-3 flex flex-wrap items-center gap-2">
                  {v.categorias_zil?.map((c) => (
                    <CategoriaBadge key={c} codigo={c} />
                  ))}
                  <Link
                    href={`/votacoes/${v.id}`}
                    className="font-mono text-xs text-zil-green hover:underline ml-auto"
                  >
                    Ver como cada parlamentar votou →
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
