import Link from "next/link";
import { ScoreGauge } from "./ScoreGauge";
import type { Parlamentar } from "@/lib/api";

interface ParlamentarCardProps {
  parlamentar: Parlamentar;
  rank?: number;
}

export function ParlamentarCard({ parlamentar: p, rank }: ParlamentarCardProps) {
  return (
    <Link
      href={`/parlamentar/${p.id}`}
      className="flex items-center gap-4 py-4 px-4 border-b border-zil-divider hover:bg-zil-card transition-colors group"
    >
      {/* Rank number */}
      {rank !== undefined && (
        <span className="font-display text-zil-divider text-lg w-8 text-right shrink-0">
          {rank}
        </span>
      )}

      {/* Photo */}
      <div className="w-12 h-12 rounded-full bg-zil-divider overflow-hidden shrink-0">
        {p.foto_url && (
          <img
            src={p.foto_url}
            alt={p.nome}
            className="w-full h-full object-cover"
            loading="lazy"
          />
        )}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="font-semibold text-zil-fg truncate group-hover:text-zil-green transition-colors">
          {p.nome}
        </div>
        <div className="text-sm text-zil-muted">
          {p.partido && <span>{p.partido}</span>}
          {p.partido && p.uf && <span> · </span>}
          {p.uf && <span>{p.uf}</span>}
          {p.fonte && (
            <span className="ml-2 text-xs font-mono opacity-50">
              {p.fonte === "camara" ? "Dep." : "Sen."}
            </span>
          )}
        </div>
      </div>

      {/* Score */}
      <ScoreGauge score={p.score_zil} size="sm" />
    </Link>
  );
}
