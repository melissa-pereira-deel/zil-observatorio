import { PlacarLinha } from "@/components/ui";
import type { Parlamentar } from "@/lib/api";

/**
 * Linha de um parlamentar no placar: envelope fino de `PlacarLinha` que monta
 * a meta ("PARTIDO · UF · N votos") e o `title` de credibilidade do score
 * (UI-001) a partir do tipo `Parlamentar` da API.
 *
 * A API ainda não expõe quantos votos foram alinhados, só o total; por isso
 * a coluna "Votos alinhados" fica vazia até o campo existir.
 */

interface ParlamentarCardProps {
  parlamentar: Parlamentar;
  /** Posição na lista. Quem não tem score continua a numeração, com a pílula "sem dado". */
  rank: number;
}

/** UI-001: o número nunca aparece sem dizer em quantos votos se apoia. */
export function tituloDoScore(totalVotos: number): string {
  const votos = totalVotos === 1 ? "1 voto" : `${totalVotos} votos`;
  return `Score ZIL baseado em ${votos} em pautas monitoradas · ver /metodologia`;
}

export function ParlamentarCard({ parlamentar: p, rank }: ParlamentarCardProps) {
  const votos = p.total_votos_zil === 1 ? "1 voto" : `${p.total_votos_zil} votos`;
  const meta = [p.partido, p.uf, votos].filter(Boolean).join(" · ");
  return (
    <PlacarLinha
      posicao={rank}
      href={`/parlamentar/${p.id}`}
      nome={p.nome}
      fotoUrl={p.foto_url}
      meta={meta}
      score={p.score_zil}
      scoreTitle={tituloDoScore(p.total_votos_zil)}
      colunaVotos={false}
    />
  );
}
