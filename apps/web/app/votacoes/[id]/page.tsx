"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { CategoriaBadge } from "@/components/CategoriaBadge";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ProposicaoSnippet {
  id: string;
  tipo: string | null;
  numero: number | null;
  ano: number | null;
  ementa: string | null;
  resumo_simples: string | null;
}

interface VotoIndividual {
  parlamentar_id: string;
  parlamentar_nome: string;
  parlamentar_partido: string | null;
  parlamentar_uf: string | null;
  voto: string;
  orientacao_partido: string | null;
}

interface VotacaoDetail {
  id: string;
  descricao: string | null;
  data: string | null;
  resultado: string | null;
  votos_sim: number | null;
  votos_nao: number | null;
  categorias_zil: string[] | null;
  direcao_esperada: string | null;
  peso: number | null;
  proposicao: ProposicaoSnippet | null;
}

const VOTO_LABEL: Record<string, string> = {
  sim: "SIM",
  nao: "NÃO",
  abstencao: "ABSTENÇÃO",
  ausente: "AUSENTE",
  obstrucao: "OBSTRUÇÃO",
  artigo_17: "ART.17",
};

const VOTO_STYLE: Record<string, string> = {
  sim: "bg-zil-green/10 text-zil-green",
  nao: "bg-zil-orange-light text-zil-orange",
  abstencao: "bg-zil-card text-zil-muted",
  ausente: "bg-zil-card text-zil-muted opacity-50",
  obstrucao: "bg-yellow-50 text-yellow-700",
  artigo_17: "bg-zil-card text-zil-muted",
};

export default function VotacaoDetailPage() {
  const params = useParams();
  const id = params?.id as string;

  const [votacao, setVotacao] = useState<VotacaoDetail | null>(null);
  const [votos, setVotos] = useState<VotoIndividual[]>([]);
  const [loading, setLoading] = useState(true);
  const [filtroVoto, setFiltroVoto] = useState("");

  useEffect(() => {
    if (!id) return;
    async function load() {
      setLoading(true);
      try {
        const [vRes, votoRes] = await Promise.all([
          fetch(`${API_BASE}/votacoes/${id}`),
          fetch(`${API_BASE}/votacoes/${id}/votos`),
        ]);
        setVotacao(vRes.ok ? await vRes.json() : null);
        setVotos(await votoRes.json());
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  const filtered = filtroVoto
    ? votos.filter((v) => v.voto === filtroVoto)
    : votos;

  const contagem = votos.reduce<Record<string, number>>((acc, v) => {
    acc[v.voto] = (acc[v.voto] ?? 0) + 1;
    return acc;
  }, {});

  const prop = votacao?.proposicao;
  const propLabel = prop
    ? `${prop.tipo ?? ""} ${prop.numero ?? ""}/${prop.ano ?? ""}`.trim()
    : null;
  const propDescricao = prop?.resumo_simples || prop?.ementa;

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-20 text-center font-mono text-sm text-zil-muted">
        Carregando...
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-12">
      {/* Back */}
      {prop ? (
        <Link
          href={`/proposicoes/${prop.id}`}
          className="font-mono text-xs text-zil-muted hover:text-zil-green mb-8 inline-block"
        >
          ← Voltar à proposição
        </Link>
      ) : (
        <Link
          href="/proposicoes"
          className="font-mono text-xs text-zil-muted hover:text-zil-green mb-8 inline-block"
        >
          ← Voltar às proposições
        </Link>
      )}

      {/* Header — proposição como protagonista */}
      <div className="mb-8">
        {propLabel && (
          <div className="flex items-center gap-3 mb-2 flex-wrap">
            <h1 className="font-display text-2xl uppercase tracking-wide">
              {propLabel}
            </h1>
            {prop && (
              <Link
                href={`/proposicoes/${prop.id}`}
                className="font-mono text-xs text-zil-green hover:underline"
              >
                Ver proposição completa ↗
              </Link>
            )}
          </div>
        )}

        {/* Descrição da proposição (resumo ou ementa) */}
        {propDescricao && (
          <p className="text-base text-zil-fg leading-relaxed mb-3 max-w-3xl">
            {propDescricao}
          </p>
        )}

        {/* Metadados da votação */}
        <div className="flex flex-wrap items-center gap-3 text-xs font-mono text-zil-muted mb-3">
          {votacao?.data && (
            <span>{new Date(votacao.data).toLocaleDateString("pt-BR")}</span>
          )}
          {votacao?.resultado && (
            <span
              className={
                votacao.resultado.toLowerCase().includes("aprovad")
                  ? "text-zil-green"
                  : votacao.resultado.toLowerCase().includes("rejeitad")
                  ? "text-zil-orange"
                  : ""
              }
            >
              {votacao.resultado}
            </span>
          )}
          {votacao?.direcao_esperada && (
            <span
              className={
                votacao.direcao_esperada === "sim"
                  ? "text-zil-green"
                  : "text-zil-orange"
              }
            >
              Direção esperada: votar {votacao.direcao_esperada.toUpperCase()}
            </span>
          )}
        </div>

        <div className="flex flex-wrap gap-2 mb-3">
          {votacao?.categorias_zil?.map((c) => (
            <CategoriaBadge key={c} codigo={c} />
          ))}
        </div>

        {/* Detalhes processuais colapsados */}
        {votacao?.descricao && (
          <details className="mt-2">
            <summary className="font-mono text-xs text-zil-muted cursor-pointer select-none hover:text-zil-soft">
              Ver detalhes da sessão ↓
            </summary>
            <p className="text-sm text-zil-muted leading-relaxed mt-2 max-w-3xl pl-2 border-l border-zil-divider">
              {votacao.descricao}
            </p>
          </details>
        )}
      </div>

      {/* Placar */}
      <div className="flex flex-wrap gap-6 py-4 border-y border-zil-divider mb-8">
        {Object.entries(contagem)
          .sort((a, b) => b[1] - a[1])
          .map(([voto, count]) => (
            <button
              key={voto}
              onClick={() => setFiltroVoto(filtroVoto === voto ? "" : voto)}
              className={`text-left transition-opacity ${
                filtroVoto && filtroVoto !== voto ? "opacity-30" : ""
              }`}
            >
              <div
                className={`font-display text-xl ${
                  voto === "sim"
                    ? "text-zil-green"
                    : voto === "nao"
                    ? "text-zil-orange"
                    : "text-zil-soft"
                }`}
              >
                {count}
              </div>
              <div className="font-mono text-xs text-zil-muted uppercase">
                {VOTO_LABEL[voto] ?? voto}
              </div>
            </button>
          ))}
        {filtroVoto && (
          <button
            onClick={() => setFiltroVoto("")}
            className="font-mono text-xs text-zil-muted hover:text-zil-fg self-center"
          >
            × todos
          </button>
        )}
      </div>

      {/* Lista de votos individuais */}
      <div className="border-t border-zil-divider">
        {filtered.map((v) => (
          <Link
            key={v.parlamentar_id}
            href={`/parlamentar/${v.parlamentar_id}`}
            className="flex items-center gap-4 py-3 border-b border-zil-divider hover:bg-zil-card transition-colors"
          >
            <div className="flex-1 min-w-0">
              <span className="text-sm text-zil-fg font-semibold">
                {v.parlamentar_nome}
              </span>
              <span className="text-xs text-zil-muted font-mono ml-2">
                {v.parlamentar_partido} · {v.parlamentar_uf}
              </span>
            </div>
            <span
              className={`font-mono text-xs px-3 py-1 rounded-sm shrink-0 ${
                VOTO_STYLE[v.voto] ?? "bg-zil-card text-zil-muted"
              }`}
            >
              {VOTO_LABEL[v.voto] ?? v.voto.toUpperCase()}
            </span>
          </Link>
        ))}
      </div>

      <div className="mt-4 text-xs font-mono text-zil-muted">
        {filtered.length} votos
        {filtroVoto ? ` — ${VOTO_LABEL[filtroVoto] ?? filtroVoto}` : ""}
      </div>
    </div>
  );
}
