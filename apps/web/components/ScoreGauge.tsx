/**
 * ScoreGauge — visual indicator for the ZIL score (-10 to +10).
 * Green = aligned with sovereignty, gold border = neutral, red tones = against.
 */

interface ScoreGaugeProps {
  score: number | null;
  size?: "sm" | "md" | "lg";
}

export function ScoreGauge({ score, size = "md" }: ScoreGaugeProps) {
  const sizeClasses = {
    sm: "w-10 h-10 text-sm",
    md: "w-14 h-14 text-lg",
    lg: "w-20 h-20 text-2xl",
  };

  if (score === null || score === undefined) {
    return (
      <div
        className={`${sizeClasses[size]} rounded-full border-2 border-zil-divider flex items-center justify-center font-display text-zil-muted`}
      >
        —
      </div>
    );
  }

  const getColor = (s: number) => {
    if (s >= 5) return { bg: "bg-zil-green/10", border: "border-zil-green", text: "text-zil-green" };
    if (s >= 2) return { bg: "bg-zil-green/5", border: "border-zil-green/50", text: "text-zil-green" };
    if (s >= -2) return { bg: "bg-zil-gold/10", border: "border-zil-gold", text: "text-zil-gold-dark" };
    if (s >= -5) return { bg: "bg-orange-50", border: "border-orange-300", text: "text-orange-600" };
    return { bg: "bg-red-50", border: "border-red-300", text: "text-red-600" };
  };

  const colors = getColor(score);
  const display = score > 0 ? `+${score.toFixed(1)}` : score.toFixed(1);

  return (
    <div
      className={`${sizeClasses[size]} rounded-full border-2 ${colors.border} ${colors.bg} flex items-center justify-center font-display ${colors.text}`}
      title={`Score ZIL: ${display}`}
    >
      {display}
    </div>
  );
}
