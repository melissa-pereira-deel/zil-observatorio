"use client";

import { useState, useEffect } from "react";
import { CategoriaBadge } from "@/components/CategoriaBadge";
import { ContextoBadge } from "@/components/ContextoBadge";
import {
  Aviso,
  BarraFiltros,
  Busca,
  Button,
  Card,
  CardEsqueleto,
  Chip,
  Chips,
  Revelar,
  Segmentado,
  Seletor,
  Selo,
  Vazio,
} from "@/components/ui";
import { CATEGORIA_COR, CATEGORIA_LABELS } from "@/lib/categorias";
import type { Proposicao } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const CATEGORIAS = Object.entries(CATEGORIA_LABELS).map(([code, label]) => ({ code, label }));

const TIPOS = ["PL", "PEC", "PLP", "MPV", "PDL", "PRC"];

const ANO_ATUAL = new Date().getFullYear();
const ANOS = Array.from({ length: 10 }, (_, i) => ANO_ATUAL - i);

// "Analisada" = enriquecimento pronto (resumo em linguagem simples). A API
// filtra e, sem filtro, já devolve as analisadas primeiro.
type Analise = "" | "analisada" | "pendente";
const ANALISES: { valor: Analise; rotulo: string }[] = [
  { valor: "", rotulo: "Todas" },
  { valor: "analisada", rotulo: "Analisadas" },
  { valor: "pendente", rotulo: "Sem análise" },
];

// Ordenação é separada dos filtros (UI-005). Sem escolha, vale a ordem da API.
const ORDENS = [
  { valor: "recentes", rotulo: "Mais recentes" },
  { valor: "antigas", rotulo: "Mais antigas" },
];

export default function ProposicoesPage() {
  const [proposicoes, setProposicoes] = useState<Proposicao[]>([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState(false);
  const [categoria, setCategoria] = useState("");
  const [tipo, setTipo] = useState("");
  const [ano, setAno] = useState("");
  const [analise, setAnalise] = useState<Analise>("");
  const [busca, setBusca] = useState("");
  const [ordem, setOrdem] = useState("");
  // Incrementa para refazer a busca depois de um erro.
  const [tentativa, setTentativa] = useState(0);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setErro(false);
      try {
        const params = new URLSearchParams({ per_page: "100" });
        if (categoria) params.set("categoria", categoria);
        if (tipo) params.set("tipo", tipo);
        if (ano) params.set("ano", ano);
        if (analise) params.set("analise", analise);
        const res = await fetch(`${API_BASE}/proposicoes?${params}`);
        setProposicoes(await res.json());
      } catch (err) {
        console.error(err);
        setErro(true);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [categoria, tipo, ano, analise, tentativa]);

  const filtered = busca
    ? proposicoes.filter((p) =>
        p.ementa?.toLowerCase().includes(busca.toLowerCase()) ||
        p.resumo_simples?.toLowerCase().includes(busca.toLowerCase())
      )
    : proposicoes;

  const ordenadas = ordem
    ? [...filtered].sort((a, b) => {
        const da = a.data_apresentacao ?? "";
        const db = b.data_apresentacao ?? "";
        return ordem === "recentes" ? db.localeCompare(da) : da.localeCompare(db);
      })
    : filtered;

  const hasFilters = !!(busca || categoria || tipo || ano || analise);

  function clearFilters() {
    setBusca("");
    setCategoria("");
    setTipo("");
    setAno("");
    setAnalise("");
  }

  return (
    <div className="zil-container">
      {/* Cabeçalho — UI-006: sem letra decorativa */}
      <header className="pt-10 md:pt-16 grid gap-4">
        <p className="text-rotulo uppercase text-zil-texto-2">Proposições</p>
        <h1 className="text-titulo-1 md:text-display-m">Proposições</h1>
        <p className="text-texto-l text-zil-texto-2 max-w-[60ch]">
          Projetos de lei, PECs e requerimentos classificados por pauta de soberania industrial.
        </p>
      </header>

      <section className="zil-secao grid gap-6">
        {/* Busca, pauta, tipo e ano numa linha; ordenação no fim (UI-005) */}
        <BarraFiltros
          fim={
            <Seletor
              variante="fantasma"
              valor={ordem}
              onMudar={setOrdem}
              rotulo="Ordenar proposições"
              vazio="Ordenar"
              opcoes={ORDENS}
            />
          }
        >
          <Busca
            valor={busca}
            onMudar={setBusca}
            rotulo="Buscar proposições"
            placeholder="Buscar por ementa ou resumo"
            className="w-full sm:w-72"
          />
          <Seletor valor={tipo} onMudar={setTipo} rotulo="Tipo de proposição" vazio="Todos os tipos" opcoes={TIPOS.map((t) => ({ valor: t, rotulo: t }))} />
          <Seletor valor={ano} onMudar={setAno} rotulo="Ano de apresentação" vazio="Todos os anos" opcoes={ANOS.map((a) => ({ valor: String(a), rotulo: String(a) }))} />
          <Segmentado opcoes={ANALISES} valor={analise} onMudar={setAnalise} rotulo="Análise" />
        </BarraFiltros>

        {/* Pauta: escolha única, como rádio; "Todas" é o padrão */}
        <Chips>
          <Chip ativo={!categoria} onClick={() => setCategoria("")}>
            Todas
          </Chip>
          {CATEGORIAS.map((c) => (
            <Chip
              key={c.code}
              ativo={categoria === c.code}
              pontoClassName={CATEGORIA_COR[c.code]}
              onClick={() => setCategoria(categoria === c.code ? "" : c.code)}
            >
              {c.label}
            </Chip>
          ))}
        </Chips>

        {erro ? (
          <Aviso
            tom="contra"
            titulo="Não foi possível carregar as proposições"
            acao={
              <Button variante="secundario" tamanho="s" onClick={() => setTentativa((t) => t + 1)}>
                Tentar de novo
              </Button>
            }
          >
            A API não respondeu. Confira a conexão e tente de novo em instantes.
          </Aviso>
        ) : loading ? (
          <div className="grid gap-4 md:grid-cols-2" aria-busy="true" aria-label="Carregando proposições">
            {Array.from({ length: 6 }, (_, i) => (
              <CardEsqueleto key={i} />
            ))}
          </div>
        ) : ordenadas.length === 0 ? (
          /* UI-004: vazio diz o motivo — cobertura ou filtro — e oferece a saída */
          <Vazio
            icone="documento"
            titulo={hasFilters ? "Nenhuma proposição com esses filtros" : "Nenhuma proposição classificada ainda"}
            acao={
              hasFilters ? (
                <Button variante="secundario" onClick={clearFilters}>
                  Limpar filtros
                </Button>
              ) : undefined
            }
          >
            {analise === "analisada"
              ? "Nenhuma proposição analisada com esses filtros. A análise em linguagem simples é feita pelo pipeline de enriquecimento."
              : hasFilters
              ? "Tente outra pauta, tipo ou ano, ou busque por outro termo."
              : "A cobertura ainda está em formação: as proposições entram conforme a curadoria classifica cada pauta."}
          </Vazio>
        ) : (
          <>
            {/* UI-003: contagem acima da lista */}
            <p className="text-texto-s text-zil-texto-2 zil-num">
              {ordenadas.length}
              {busca && ordenadas.length !== proposicoes.length ? ` de ${proposicoes.length}` : ""}{" "}
              {ordenadas.length === 1 ? "proposição" : "proposições"}
              {analise === "analisada" ? (ordenadas.length === 1 ? " analisada" : " analisadas") : ""}
              {analise === "pendente" ? " sem análise" : ""}
            </p>

            <ul className="grid gap-4 md:grid-cols-2 list-none m-0 p-0">
              {ordenadas.map((p, i) => (
                <Revelar key={p.id} as="li" ordem={i % 6}>
                  <Card href={`/proposicoes/${p.id}`} className="h-full grid content-start gap-3">
                    <div className="flex flex-wrap items-center gap-2">
                      {p.situacao && <Selo>{p.situacao}</Selo>}
                      {p.categorias_zil?.map((c) => (
                        <CategoriaBadge key={c} codigo={c} />
                      ))}
                      <ContextoBadge status={p.contexto_status} confianca={p.confianca} />
                    </div>
                    <h2 className="text-titulo-4">
                      {p.tipo} {p.numero}/{p.ano}
                    </h2>
                    {/* Resumo em linguagem simples quando a análise está pronta; senão, a ementa.
                        A API já omite o resumo fora de `pronto` — o teste aqui é a mesma regra da página da proposição. */}
                    <p className="text-texto-s text-zil-texto-2 line-clamp-3">
                      {(p.contexto_status === "pronto" && p.resumo_simples) || p.ementa}
                    </p>
                    {p.data_apresentacao && (
                      <p className="text-texto-s text-zil-texto-2 zil-num">
                        Apresentada em {new Date(p.data_apresentacao).toLocaleDateString("pt-BR")}
                      </p>
                    )}
                  </Card>
                </Revelar>
              ))}
            </ul>
          </>
        )}
      </section>
    </div>
  );
}
