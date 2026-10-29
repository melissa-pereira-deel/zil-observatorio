import { Card } from "@/components/ui";
import { CATEGORIA_COR } from "@/lib/categorias";

/**
 * As nove áreas estratégicas, como cartões-link para a lista filtrada. O
 * ponto de cor é o mesmo do chip e do gráfico (CATEGORIA_COR); o código
 * interno fica no `title`, fora do texto público (UI-021).
 */

const CATEGORIAS = [
  { codigo: "ZIL-FER", nome: "Fertilizantes" },
  { codigo: "ZIL-MIN", nome: "Minerais" },
  { codigo: "ZIL-SEM", nome: "Semicondutores" },
  { codigo: "ZIL-ENE", nome: "Energia" },
  { codigo: "ZIL-DIG", nome: "Digital" },
  { codigo: "ZIL-DEF", nome: "Defesa" },
  { codigo: "ZIL-EDU", nome: "Capital Humano" },
  { codigo: "ZIL-AGR", nome: "Agro-Indústria" },
  { codigo: "ZIL-COM", nome: "Comércio" },
];

export function CategoryGrid() {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 md:gap-6">
      {CATEGORIAS.map((cat) => (
        <Card
          key={cat.codigo}
          href={`/proposicoes?categoria=${cat.codigo}`}
          compacto
          title={`Proposições em ${cat.nome} (${cat.codigo})`}
          className="flex items-center gap-3"
        >
          <span aria-hidden="true" className={`w-2.5 h-2.5 rounded-full shrink-0 ${CATEGORIA_COR[cat.codigo] ?? "bg-zil-texto-3"}`} />
          <span className="text-texto-ui">{cat.nome}</span>
        </Card>
      ))}
    </div>
  );
}
