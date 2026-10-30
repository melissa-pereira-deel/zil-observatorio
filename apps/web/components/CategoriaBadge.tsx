import { Selo } from "@/components/ui";
import { CATEGORIA_LABELS, CATEGORIA_COR } from "@/lib/categorias";

/** Selo de categoria ZIL, com o ponto na cor da pauta (a mesma dos gráficos). */
export function CategoriaBadge({ codigo }: { codigo: string }) {
  const label = CATEGORIA_LABELS[codigo] || codigo;
  const cor = CATEGORIA_COR[codigo];
  return (
    <Selo title={codigo}>
      {cor && <span aria-hidden="true" className={`w-1.5 h-1.5 rounded-full ${cor}`} />}
      {label}
    </Selo>
  );
}
