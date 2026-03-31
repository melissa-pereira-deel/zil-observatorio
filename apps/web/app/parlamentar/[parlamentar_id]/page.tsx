"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
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

export default function ParlamentarPage() {
  const params = useParams();
  const id = params?.parlamentar_id as string;

  const [parl, setParl] = useState<ParlamentarDetail | null>(null);
  const [votos, setVotos] = useState<VotoHistorico[]>([]);
  const [loading, setLoading] = useState(true);

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

  const alinhados = votos.filter((v) => v.alinhado === true).length;
  const contra = votos.filter((v) => v.alinhado === false).length;

  return (
    <div className="max-w-5xl mx-auto px-6 py-12">
      {/* Profile header */}
      <div className="flex items-start gap-6 flex-wrap mb-12">
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
        </div>
      </div>

      {/* Stats bar */}
      <div className="flex gap-8 py-4 border-y border-zil-divider mb-10">
        <div>
          <div className="font-display text-xl text-zil-green">{alinhados}</div>
          <div className="font-mono text-xs text-zil-muted">votos alinhados</div>
        </div>
        <div>
          <div className="font-display text-xl text-orange-500">{contra}</div>
          <div className="font-mono text-xs text-zil-muted">votos contra</div>
        </div>
        <div>
          <div className="font-display text-xl text-zil-soft">{votos.length}</div>
          <div className="font-mono text-xs text-zil-muted">total pautas ZIL</div>
        </div>
      </div>

      {/* Vote history */}
      <h2 className="font-display text-lg uppercase tracking-wide mb-6">
        Histórico de votos em pautas ZIL
      </h2>

      {votos.length === 0 ? (
        <p className="text-sm text-zil-muted py-8">
          Nenhuma votação em pauta ZIL registrada ainda.
        </p>
      ) : (
        <div className="space-y-0 border-t border-zil-divider">
          {votos.map((v) => (
            <div
              key={v.votacao_id}
              className="py-4 border-b border-zil-divider flex items-start gap-4"
            >
              {/* Alignment indicator */}
              <div
                className={`w-2 h-2 rounded-full mt-2 shrink-0 ${
                  v.alinhado === true
                    ? "bg-zil-green"
                    : v.alinhado === false
                    ? "bg-orange-400"
                    : "bg-zil-divider"
                }`}
              />

              <div className="flex-1 min-w-0">
                <p className="text-sm text-zil-fg leading-relaxed">
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
                </div>
              </div>

              {/* Vote chip */}
              <span
                className={`shrink-0 font-mono text-xs px-3 py-1 rounded-sm ${
                  v.voto === "sim"
                    ? "bg-zil-green/10 text-zil-green"
                    : v.voto === "nao"
                    ? "bg-orange-50 text-orange-600"
                    : "bg-zil-card text-zil-muted"
                }`}
              >
                {v.voto.toUpperCase()}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
