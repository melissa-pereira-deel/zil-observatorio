/** Classes que usam as cores de alinhamento ou de atenção. Fase e status não podem usá-las. */
export function classesDeAlinhamento(raiz: Element): string[] {
  const re = /\b(?:bg|text|fill|stroke|shadow|outline|ring|decoration|border)-zil-(?:alinhado|contra|neutro)(?:-fundo)?\b/;
  return [raiz, ...Array.from(raiz.querySelectorAll("[class]"))]
    .map((e) => e.getAttribute("class") ?? "")
    .filter((c) => re.test(c));
}
