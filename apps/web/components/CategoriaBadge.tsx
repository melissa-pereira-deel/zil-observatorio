const LABELS: Record<string, string> = {
  "ZIL-FER": "Fertilizantes",
  "ZIL-MIN": "Minerais",
  "ZIL-SEM": "Semicondutores",
  "ZIL-ENE": "Energia",
  "ZIL-DIG": "Digital",
  "ZIL-DEF": "Defesa",
  "ZIL-EDU": "Educação",
  "ZIL-AGR": "Agro-Indústria",
  "ZIL-COM": "Comércio",
};

interface CategoriaBadgeProps {
  codigo: string;
}

export function CategoriaBadge({ codigo }: CategoriaBadgeProps) {
  const label = LABELS[codigo] || codigo;

  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-mono tracking-wider bg-zil-green/8 text-zil-green border border-zil-green/20 rounded-sm">
      {label}
    </span>
  );
}
