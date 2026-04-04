interface DirecaoBadgeProps {
  direcao: string | null | undefined;
}

export function DirecaoBadge({ direcao }: DirecaoBadgeProps) {
  if (!direcao) return null;

  if (direcao === "sim") {
    return (
      <span
        className="font-mono text-xs text-zil-green"
        title="Posição ZIL nesta votação: favorável · ver /metodologia"
      >
        ● FAVORÁVEL
      </span>
    );
  }

  if (direcao === "nao") {
    return (
      <span
        className="font-mono text-xs text-zil-orange"
        title="Posição ZIL nesta votação: contrária · ver /metodologia"
      >
        ● CONTRÁRIA
      </span>
    );
  }

  return null;
}
