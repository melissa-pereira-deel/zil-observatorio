import type { Assento, TomAssento } from "@/components/ui/Hemiciclo";
import type { ValorUF } from "@/components/ui/MapaUF";

/**
 * Uma votação vista como plenário: os votos individuais que a API devolve
 * viram cadeiras de um hemiciclo e bancadas de um mapa por UF.
 *
 * A Câmara só devolve quem registrou voto. Os demais (licença, missão,
 * quem não estava no plenário) não têm linha nenhuma — então "não votaram"
 * é o tamanho da Casa menos os votos registrados, e o rótulo diz isso em vez
 * de "ausentes".
 */

export interface VotoIndividual {
  parlamentar_id: string;
  parlamentar_nome: string;
  parlamentar_partido: string | null;
  parlamentar_uf: string | null;
  voto: string;
  orientacao_partido: string | null;
}

export const CADEIRAS: Record<string, number> = { camara: 513, senado: 81 };

export type GrupoVoto = "sim" | "outros" | "nao_votou" | "nao";

/** Ordem no hemiciclo, da esquerda para a direita. */
export const GRUPOS: GrupoVoto[] = ["sim", "outros", "nao_votou", "nao"];

export const ROTULO_GRUPO: Record<GrupoVoto, string> = {
  sim: "Sim",
  nao: "Não",
  outros: "Abstenção ou obstrução",
  nao_votou: "Não votaram",
};

export function grupoDoVoto(voto: string): GrupoVoto {
  if (voto === "sim" || voto === "nao") return voto;
  if (voto === "abstencao" || voto === "obstrucao") return "outros";
  // ausente e artigo_17 (o presidente da sessão, que não vota)
  return "nao_votou";
}

/**
 * Cor de cada grupo. Com direção esperada, sim e não viram alinhado e
 * contra — e a legenda precisa dizer isso. Sem direção, sim e não ficam
 * neutros: a cor não pode sugerir um lado que o ZIL não declarou.
 */
export function tomDoGrupo(grupo: GrupoVoto, direcao: string | null | undefined): TomAssento {
  if (grupo === "outros") return "neutro";
  if (grupo === "nao_votou") return "vazio";
  if (!direcao) return grupo;
  return grupo === direcao ? "alinhado" : "contra";
}

export const COR_DO_TOM: Record<TomAssento, string> = {
  alinhado: "bg-zil-alinhado",
  contra: "bg-zil-contra",
  neutro: "bg-zil-neutro",
  sim: "bg-zil-texto",
  nao: "bg-zil-texto-3",
  vazio: "bg-zil-superficie-4",
};

export function contarGrupos(votos: VotoIndividual[], cadeiras: number): Record<GrupoVoto, number> {
  const n: Record<GrupoVoto, number> = { sim: 0, nao: 0, outros: 0, nao_votou: 0 };
  for (const v of votos) n[grupoDoVoto(v.voto)]++;
  n.nao_votou += Math.max(0, cadeiras - votos.length);
  return n;
}

/**
 * Cadeiras do hemiciclo, na ordem dos grupos; dentro de cada grupo, por
 * partido, para as bancadas ficarem juntas. Quem não registrou voto vira
 * cadeira sem nome no fim do grupo "não votaram".
 */
export function assentosDaVotacao(
  votos: VotoIndividual[],
  cadeiras: number,
  direcao: string | null | undefined,
  marcado: (v: VotoIndividual | null, grupo: GrupoVoto) => boolean,
): Assento[] {
  const porGrupo: Record<GrupoVoto, VotoIndividual[]> = { sim: [], nao: [], outros: [], nao_votou: [] };
  for (const v of votos) porGrupo[grupoDoVoto(v.voto)].push(v);
  const semRegistro = Math.max(0, cadeiras - votos.length);

  const assentos: Assento[] = [];
  for (const g of GRUPOS) {
    const tom = tomDoGrupo(g, direcao);
    porGrupo[g]
      .sort((a, b) => (a.parlamentar_partido ?? "").localeCompare(b.parlamentar_partido ?? "") || a.parlamentar_nome.localeCompare(b.parlamentar_nome))
      .forEach((v) =>
        assentos.push({
          id: v.parlamentar_id,
          tom,
          titulo: `${v.parlamentar_nome} · ${v.parlamentar_partido ?? "—"} · ${v.parlamentar_uf ?? "—"} — ${ROTULO_VOTO[v.voto] ?? v.voto}`,
          marcado: marcado(v, g),
        }),
      );
    if (g === "nao_votou") {
      for (let i = 0; i < semRegistro; i++) {
        assentos.push({ id: `sem-registro-${i}`, tom, titulo: "Não registrou voto", marcado: marcado(null, g) });
      }
    }
  }
  return assentos;
}

export const ROTULO_VOTO: Record<string, string> = {
  sim: "Sim",
  nao: "Não",
  abstencao: "Abstenção",
  ausente: "Ausente",
  obstrucao: "Obstrução",
  artigo_17: "Art. 17 (presidente)",
};

function pct(n: number): string {
  return `${Math.round(n * 100)}%`;
}

/**
 * Como cada bancada estadual votou: a parcela de Sim entre quem votou sim
 * ou não. Com direção esperada, a cor diz se a maioria da bancada foi na
 * direção (≥ 55%), contra (≤ 45%) ou dividida; sem direção, cinza.
 */
export function bancadasDaVotacao(votos: VotoIndividual[], direcao: string | null | undefined): Record<string, ValorUF> {
  const porUF: Record<string, { sim: number; nao: number }> = {};
  for (const v of votos) {
    if (!v.parlamentar_uf || (v.voto !== "sim" && v.voto !== "nao")) continue;
    const u = (porUF[v.parlamentar_uf] ??= { sim: 0, nao: 0 });
    u[v.voto]++;
  }
  const valores: Record<string, ValorUF> = {};
  for (const [uf, { sim, nao }] of Object.entries(porUF)) {
    const total = sim + nao;
    const fracSim = sim / total;
    const naDirecao = direcao === "nao" ? 1 - fracSim : fracSim;
    valores[uf] = {
      valor: pct(fracSim),
      tom: !direcao ? "padrao" : naDirecao >= 0.55 ? "alinhado" : naDirecao <= 0.45 ? "contra" : "neutro",
      titulo: `${uf}: ${sim} sim e ${nao} não (${pct(fracSim)} sim)`,
    };
  }
  return valores;
}
