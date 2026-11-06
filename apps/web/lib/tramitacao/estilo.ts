/**
 * Regras V-E1 a V-E10 do guia de redação (specs/013-tramitacao/backlog-interface.md
 * §2.4). `padrao` é o regex Python da spec, sem alteração, o mesmo que o
 * validador do YAML aplica; `regex` é a tradução para JS.
 */

export type IdRegraEstilo =
  | "V-E1" | "V-E2" | "V-E3" | "V-E4" | "V-E5"
  | "V-E6" | "V-E7" | "V-E8" | "V-E9" | "V-E10";

export interface RegraEstilo {
  id: IdRegraEstilo;
  padrao: string;
  regex: RegExp;
}

const LETRA = String.raw`[\p{L}\p{N}_]`;
const FRONTEIRA = `(?:(?<=${LETRA})(?!${LETRA})|(?<!${LETRA})(?=${LETRA}))`;

// Em JS, \b e \w só conhecem ASCII; em Python, acento é letra. Sem traduzir,
// "CÂMARA" casaria "MARA" em V-E10 aqui e não no validador do YAML.
function regra(id: IdRegraEstilo, padrao: string, flags: "iu" | "u" = "iu"): RegraEstilo {
  const js = padrao.split(String.raw`\b`).join(FRONTEIRA).split(String.raw`\w`).join(LETRA);
  return { id, padrao, regex: new RegExp(js, flags) };
}

export const REGRAS_ESTILO: readonly RegraEstilo[] = [
  regra("V-E1", String.raw`em breve|deve(rá)? ser votad|previs(ão|t[oa]) para|está prevista|até o fim do (ano|mês|semestre)`),
  regra("V-E2", String.raw`parad[oa] há|há \d+ (dias|meses|anos)|atrasad|engavetad|gaveta|travad|esquecid|emperrad|deveria|precisa ser votad`),
  regra("V-E3", String.raw`%|falta pouco|quase lá|reta final`),
  regra("V-E4", String.raw`não regulamentad|falta regulamentar|(governo|executivo) não (regulamentou|cumpriu)|descumpr`),
  regra("V-E5", String.raw`graças a|resultou em|importante|polêmic|vitória|derrota|felizmente|infelizmente|finalmente`),
  regra("V-E6", String.raw`\bPresidente\b(?! d[aoe] (Câmara|República|Senado|Congresso))`, "u"),
  regra("V-E7", String.raw`\b\d{1,2}/\d{1,2}(/\d{2,4})?\b`),
  regra("V-E8", String.raw`\b\d+ dias\b(?! (úteis|corridos))`),
  regra("V-E9", String.raw`\w\((a|as|o|os|à)\)`),
  regra("V-E10", String.raw`\b(?!(PL|PLP|PEC|MPV|PDL|PLV)\b)[A-Z]{3,}\b`, "u"),
];

/** IDs das regras com que o texto casa. */
export function violacoesDeEstilo(texto: string): IdRegraEstilo[] {
  return REGRAS_ESTILO.filter((r) => r.regex.test(texto)).map((r) => r.id);
}
