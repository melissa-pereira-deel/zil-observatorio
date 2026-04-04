/**
 * ScoreGauge — visual indicator for the ZIL score (-10 to +10).
 * Green = aligned with sovereignty, gold = neutral, orange/red = against.
 */

interface ScoreGaugeProps {
  score: number | null;
  size?: "sm" | "md" | "lg";
  totalVotosZil?: number;
}

export function ScoreGauge({ score, size = "md", totalVotosZil }: ScoreGaugeProps) {
  const sizeClasses = {
    sm: "w-10 h-10 text-sm",
    md: "w-14 h-14 text-lg",
    lg: "w-20 h-20 text-2xl",
  };

  const title =
    totalVotosZil != null && totalVotosZil > 0
      ? `Score calculado a partir de ${totalVotosZil} votos em pautas ZIL · Saiba mais em /metodologia`
      : undefined;

  if (score === null || score === undefined) {
    return (
      <div className="inline-flex flex-col items-center gap-1">
        <div
          className={`${sizeClasses[size]} rounded-full border-2 border-zil-divider flex items-center justify-center font-display text-zil-muted`}
          title={title}
        >
          —
        </div>
      </div>
    );
  }

  const getColor = (s: number) => {
    if (s >= 5) return { bg: "bg-zil-green/10", border: "border-zil-green", text: "text-zil-green" };
    if (s >= 2) return { bg: "bg-zil-green/5", border: "border-zil-green/50", text: "text-zil-green" };
    if (s >= -2) return { bg: "bg-zil-gold/10", border: "border-zil-gold", text: "text-zil-gold-dark" };
    if (s >= -5) return { bg: "bg-zil-orange-light", border: "border-zil-orange", text: "text-zil-orange" };
    return { bg: "bg-zil-red/10", border: "border-zil-red", text: "text-zil-red" };
  };

  const colors = getColor(score);
  const display = score > 0 ? `+${score.toFixed(1)}` : score.toFixed(1);

  return (
    <div className="inline-flex flex-col items-center gap-1">
      <div
        className={`${sizeClasses[size]} rounded-full border-2 ${colors.border} ${colors.bg} flex items-center justify-center font-display ${colors.text}`}
        title={title ?? `Score ZIL: ${display}`}
      >
        {display}
      </div>
      {size !== "sm" && totalVotosZil != null && totalVotosZil > 0 && (
        <span className="font-mono text-2xs text-zil-muted text-center">
          com base em {totalVotosZil} votos
        </span>
      )}
    </div>
  );
}
