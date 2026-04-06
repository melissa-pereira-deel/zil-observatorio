/**
 * Map situacao grupo to Tailwind color classes for badges.
 */
export function situacaoColor(grupo: string | null): string {
  switch (grupo) {
    case "tramitando": return "bg-yellow-100 text-yellow-800";
    case "aprovada": return "bg-green-100 text-green-800";
    case "arquivada": return "bg-orange-100 text-orange-800";
    case "outras": return "bg-gray-100 text-gray-700";
    default: return "bg-gray-100 text-gray-700";
  }
}

/**
 * Portuguese label for situacao grupo.
 */
export function situacaoLabel(grupo: string | null): string {
  switch (grupo) {
    case "tramitando": return "Em Tramitacao";
    case "aprovada": return "Aprovada";
    case "arquivada": return "Arquivada";
    case "outras": return "Outras";
    default: return "—";
  }
}

/**
 * Display label for regime.
 */
export function regimeLabel(regime: string | null): string {
  switch (regime?.toUpperCase()) {
    case "URGENCIA": return "Urgencia";
    case "ESPECIAL": return "Especial";
    case "ORDINARIO": return "Ordinario";
    default: return regime || "";
  }
}

/**
 * Tailwind classes for regime badge.
 */
export function regimeColor(regime: string | null): string {
  switch (regime?.toUpperCase()) {
    case "URGENCIA": return "bg-red-100 text-red-800";
    case "ESPECIAL": return "bg-amber-100 text-amber-800";
    default: return "bg-gray-100 text-gray-700";
  }
}

/**
 * Label for tipo_relacao in Portuguese.
 */
export function tipoRelacaoLabel(tipo: string): string {
  const map: Record<string, string> = {
    emenda: "Emendas",
    substitutivo: "Substitutivos",
    parecer: "Pareceres",
    redacao_final: "Redacao Final",
    destaque: "Destaques",
    requerimento: "Requerimentos",
    voto_separado: "Votos em Separado",
    apensada: "Apensadas",
    outro: "Outros",
  };
  return map[tipo] || tipo;
}
