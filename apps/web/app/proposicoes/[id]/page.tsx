"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { CategoriaBadge } from "@/components/CategoriaBadge";
import type { Proposicao } from "@/lib/api";

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

export default function ProposicaoDetailPage() {
  const params = useParams();
  const id = params?.id as string;

  const [proposicao, setProposicao] = useState<Proposicao | null>(null);
  const [votacoes, setVotacoes] = useState<Votacao[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    async function load() {
      setLoading(true);
      try {
        const [pRes, vRes] = await Promise.all([
          fetch(`${API_BASE}/proposicoes/${id}`),
          fetch(`${API_BASE}/proposicoes/${id}/votacoes`),
        ]);
        setProposicao(await pRes.json());
        setVotacoes(await vRes.json());
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

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
        <div className="flex items-baseline gap-3 mb-3">
          <h1 className="font-display text-2xl uppercase tracking-wide">
            {proposicao.tipo} {proposicao.numero}/{proposicao.ano}
          </h1>
          {proposicao.situacao && (
            <span className="font-mono text-xs text-zil-muted border border-zil-divider px-2 py-1">
              {proposicao.situacao}
            </span>
          )}
        </div>

        <p className="text-base text-zil-soft leading-relaxed mb-4 max-w-3xl">
          {proposicao.ementa}
        </p>

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

      {/* Votações */}
      <h2 className="font-display text-base uppercase tracking-wide mb-4">
        Votações ({votacoes.length})
      </h2>

      {votacoes.length === 0 ? (
        <p className="text-sm text-zil-muted py-8 border-t border-zil-divider">
          Nenhuma votação registrada para esta proposição ainda.
        </p>
      ) : (
        <div className="border-t border-zil-divider">
          {votacoes.map((v) => (
            <div key={v.id} className="py-5 border-b border-zil-divider">
              <div className="flex items-start justify-between gap-4 flex-wrap">
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-zil-fg leading-relaxed mb-2">
                    {v.descricao || "Votação sem descrição"}
                  </p>
                  <div className="flex flex-wrap items-center gap-3 text-xs font-mono text-zil-muted">
                    {v.data && (
                      <span>
                        {new Date(v.data).toLocaleDateString("pt-BR")}
                      </span>
                    )}
                    {v.resultado && <span>{v.resultado}</span>}
                    {v.direcao_esperada && (
                      <span className={v.direcao_esperada === "sim" ? "text-zil-green" : "text-zil-orange"}>
                        Direção esperada: votar {v.direcao_esperada.toUpperCase()}
                      </span>
                    )}
                  </div>
                </div>

                {/* Placar */}
                {(v.votos_sim !== null || v.votos_nao !== null) && (
                  <div className="flex gap-4 shrink-0">
                    <div className="text-center">
                      <div className="font-display text-lg text-zil-green">{v.votos_sim ?? "—"}</div>
                      <div className="font-mono text-xs text-zil-muted">SIM</div>
                    </div>
                    <div className="text-center">
                      <div className="font-display text-lg text-zil-orange">{v.votos_nao ?? "—"}</div>
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
          ))}
        </div>
      )}
    </div>
  );
}
