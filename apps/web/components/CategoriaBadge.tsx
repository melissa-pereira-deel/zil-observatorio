import { CATEGORIA_LABELS } from "@/lib/categorias";

interface CategoriaBadgeProps {
  codigo: string;
}

export function CategoriaBadge({ codigo }: CategoriaBadgeProps) {
  const label = CATEGORIA_LABELS[codigo] || codigo;

  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-mono tracking-wider bg-zil-green/8 text-zil-green border border-zil-green/20 rounded-sm">
      {label}
    </span>
  );
}
