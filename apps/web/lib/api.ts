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

export interface ParlamentarSnippet {
  id: string;
  nome: string;
  partido: string | null;
  uf: string | null;
  foto_url: string | null;
}

export interface CadeiaRead {
  principal_fonte_id: string | null;
  anterior_fonte_id: string | null;
  posterior_fonte_id: string | null;
}

export interface TemaRead {
  cod: number;
  tema: string;
}

export interface AutorRead {
  id: string;
  nome: string;
  tipo: string;
  ordem: number;
  proponente: boolean;
  parlamentar: ParlamentarSnippet | null;
}

export interface RelacionadaRead {
  id: string;
  tipo_relacao: string;
  sigla_tipo: string | null;
  numero: number | null;
  ano: number | null;
  ementa: string | null;
  relacionada_fonte_id: string;
  proposicao_id_zil: string | null;
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
  url_inteiro_teor: string | null;
  // Enrichment fields (Feature 002)
  contexto_status: string | null;
  resumo_simples: string | null;
  confianca: number | null;
  // Detail fields (Feature 012)
  cod_situacao: number | null;
  regime: string | null;
  apreciacao: string | null;
  keywords_camara: string | null;
  urn_final: string | null;
  url_lei: string | null;
  situacao_grupo: string | null;
  temas_camara: TemaRead[] | null;
  autor_principal: ParlamentarSnippet | null;
  orgao_situacao: string | null;
  relator: ParlamentarSnippet | null;
  cadeia: CadeiaRead | null;
}

export interface LeiReferenciada {
  lei_id: string;
  numero_artigo: string;
  url_planalto: string | null;
  status: string;
  texto_snippet: string | null;
}

export interface ProposicaoContexto {
  proposicao_id: string;
  ementa_original: string | null;
  contexto_status: string | null;
  resumo_simples: string | null;
  glossario: Record<string, string> | null;
  impacto_zil: string | null;
  leis_referenciadas: LeiReferenciada[] | null;
  confianca: number | null;
  enriquecido_em: string | null;
  versao_pipeline: string;
  modelo_llm: string | null;
  fontes: string[];
}

export interface VotoHistorico {
  votacao_id: string;
  data: string | null;
  descricao: string | null;
  categorias_zil: string[] | null;
  voto: string;
  direcao_esperada: string | null;
  alinhado: boolean | null;
  proposicao_label: string | null;
  proposicao_id: string | null;
  resumo_simples: string | null;
  aprovacao: number | null;
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
    proposicoes: (id: string, params?: Record<string, string>) =>
      fetchApi<Proposicao[]>(`/parlamentares/${id}/proposicoes`, params),
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
    contexto: (id: string) =>
      fetchApi<ProposicaoContexto>(`/proposicoes/${id}/contexto`),
    autores: (id: string) =>
      fetchApi<AutorRead[]>(`/proposicoes/${id}/autores`),
    temas: (id: string) =>
      fetchApi<TemaRead[]>(`/proposicoes/${id}/temas`),
    relacionadas: (id: string, params?: Record<string, string>) =>
      fetchApi<RelacionadaRead[]>(`/proposicoes/${id}/relacionadas`, params),
  },
};
