const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Parlamentar {
  id: string;
  nome: string;
  partido: string | null;
  uf: string | null;
  foto_url: string | null;
  fonte: string;
  score_zil: number | null;
  total_votos_zil: number;
}

export interface Proposicao {
  id: string;
  fonte_id: string;
  fonte: string;
  tipo: string | null;
  numero: number | null;
  ano: number | null;
  ementa: string | null;
  situacao: string | null;
  data_apresentacao: string | null;
  categorias_zil: string[] | null;
  relevancia_zil: number | null;
}

export interface VotoHistorico {
  votacao_id: string;
  data: string | null;
  descricao: string | null;
  categorias_zil: string[] | null;
  voto: string;
  direcao_esperada: string | null;
  alinhado: boolean | null;
}

export interface Stats {
  total_parlamentares: number;
  total_deputados: number;
  total_senadores: number;
  total_proposicoes_zil: number;
  total_votacoes_zil: number;
  score_medio: number | null;
}

async function fetchApi<T>(path: string, params?: Record<string, string>): Promise<T> {
  const url = new URL(`${API_BASE}${path}`);
  if (params) {
    Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  }
  const res = await fetch(url.toString(), { next: { revalidate: 300 } });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export const api = {
  stats: () => fetchApi<Stats>("/stats"),

  parlamentares: {
    listar: (params?: Record<string, string>) =>
      fetchApi<Parlamentar[]>("/parlamentares", params),
    obter: (id: string) => fetchApi<Parlamentar>(`/parlamentares/${id}`),
    votosZil: (id: string) =>
      fetchApi<VotoHistorico[]>(`/parlamentares/${id}/votos-zil`),
    rankingPartidos: (params?: Record<string, string>) =>
      fetchApi<{ partido: string; score_medio: number; membros: number }[]>(
        "/parlamentares/partidos/ranking",
        params
      ),
  },

  proposicoes: {
    listar: (params?: Record<string, string>) =>
      fetchApi<Proposicao[]>("/proposicoes", params),
    obter: (id: string) => fetchApi<Proposicao>(`/proposicoes/${id}`),
  },
};
