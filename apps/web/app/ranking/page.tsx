"use client";

import { useState, useEffect } from "react";

import { ParlamentarCard } from "@/components/ParlamentarCard";
import {
  Aviso,
  BarraFiltros,
  Busca,
  Button,
  Placar,
  PlacarCabecalho,
  PlacarLinhaEsqueleto,
  Segmentado,
  Seletor,
  Vazio,
} from "@/components/ui";
import type { Parlamentar } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const UFS = [
  "AC","AL","AM","AP","BA","CE","DF","ES","GO","MA","MG","MS","MT",
  "PA","PB","PE","PI","PR","RJ","RN","RO","RR","RS","SC","SE","SP","TO",
];

type Fonte = "" | "camara" | "senado";
type Ordem = "score_desc" | "score_asc" | "nome";

const FONTES: { valor: Fonte; rotulo: string }[] = [
  { valor: "", rotulo: "Todas" },
  { valor: "camara", rotulo: "Câmara" },
  { valor: "senado", rotulo: "Senado" },
];

const ORDENS: { valor: Ordem; rotulo: string }[] = [
  { valor: "score_desc", rotulo: "Maior score" },
  { valor: "score_asc", rotulo: "Menor score" },
  { valor: "nome", rotulo: "Nome A–Z" },
];

/** A coluna e a direção que o cabeçalho do placar mostra para cada ordenação da API. */
const ORDEM_NO_CABECALHO: Record<Ordem, { coluna: "score" | "nome"; direcao: "ascending" | "descending" }> = {
  score_desc: { coluna: "score", direcao: "descending" },
  score_asc: { coluna: "score", direcao: "ascending" },
  nome: { coluna: "nome", direcao: "ascending" },
};

export default function RankingPage() {
  const [parlamentares, setParlamentares] = useState<Parlamentar[]>([]);
  const [partidos, setPartidos] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState(false);
  // Incrementar refaz o fetch: é o que "Tentar de novo" faz.
  const [tentativa, setTentativa] = useState(0);

  const [fonte, setFonte] = useState<Fonte>("");
  const [uf, setUf] = useState("");
  const [partido, setPartido] = useState("");
  const [busca, setBusca] = useState("");
  const [ordem, setOrdem] = useState<Ordem>("score_desc");

  useEffect(() => {
    fetch(`${API_BASE}/parlamentares/partidos/ranking`)
      .then((r) => r.json())
      .then((data: { partido: string }[]) =>
        setPartidos(data.map((d) => d.partido).sort())
      )
      .catch(() => {});
  }, []);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setErro(false);
      try {
        const params = new URLSearchParams({ ordem, per_page: "600" });
        if (fonte) params.set("fonte", fonte);
        if (uf) params.set("uf", uf);
        if (partido) params.set("partido", partido);
        const res = await fetch(`${API_BASE}/parlamentares?${params}`);
        if (!res.ok) throw new Error(`API error: ${res.status}`);
        setParlamentares(await res.json());
      } catch (err) {
        console.error("Erro ao carregar ranking:", err);
        setErro(true);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [fonte, uf, partido, ordem, tentativa]);

  const filtered = busca
    ? parlamentares.filter((p) =>
        p.nome.toLowerCase().includes(busca.toLowerCase())
      )
    : parlamentares;

  const comScore = filtered.filter((p) => p.score_zil !== null);
  const semScore = filtered.filter((p) => p.score_zil === null);

  const hasFilters = !!(busca || fonte || uf || partido);

  function clearFilters() {
    setBusca("");
    setFonte("");
    setUf("");
    setPartido("");
  }

  // Clicar em "Score" inverte a direção; clicar em "Parlamentar" ordena por
  // nome (a API só ordena nome em ordem crescente).
  function ordenarPorScore() {
    setOrdem(ordem === "score_desc" ? "score_asc" : "score_desc");
  }
  function ordenarPorNome() {
    setOrdem("nome");
  }

  return (
    <div className="zil-container">
      {/* Cabeçalho — UI-006: sem letra decorativa */}
      <header className="pt-10 md:pt-16 grid gap-4">
        <p className="text-rotulo uppercase text-zil-texto-2">Placar</p>
        <h1 className="text-titulo-1 md:text-display-m">Placar ZIL</h1>
        <p className="text-texto-l text-zil-texto-2 max-w-[60ch]">
          Score de alinhamento com a soberania industrial do Brasil, de −10
          (contra) a +10 (a favor), calculado a partir dos votos nas votações
          selecionadas. Não é um índice de toda a atuação parlamentar — é um
          placar de pautas escolhidas, e o critério de escolha está na{" "}
          <a href="/metodologia" className="text-zil-texto underline underline-offset-4 decoration-1">
            metodologia
          </a>
          .
        </p>
      </header>

      {/* O placar só está no ar atrás da flag rankingPublico (lib/flags.ts);
          mesmo assim, quem chega aqui precisa saber o que o número sustenta. */}
      <Aviso
        tom="neutro"
        titulo="As votações deste placar ainda não foram validadas"
        className="mt-8"
        acao={
          <Button href="/metodologia" variante="fantasma" tamanho="s">
            Ver metodologia
          </Button>
        }
      >
        As classificações que alimentam o Score ZIL estão marcadas como não
        validadas nos arquivos do projeto, e poucas têm voto nominal registrado.
        Leia o número como um protótipo, não como um veredito.
      </Aviso>

      <section className="zil-secao grid gap-6">
        {/* Filtros — UI-005: busca na mesma linha dos filtros; ordenação separada, no fim */}
        <BarraFiltros
          fim={
            <Seletor
              variante="fantasma"
              rotulo="Ordenar por"
              valor={ordem}
              onMudar={(v) => setOrdem(v as Ordem)}
              opcoes={ORDENS}
            />
          }
        >
          <Busca
            valor={busca}
            onMudar={setBusca}
            rotulo="Buscar parlamentar"
            placeholder="Buscar parlamentar, partido ou UF"
            className="w-full sm:w-72"
          />
          <Segmentado opcoes={FONTES} valor={fonte} onMudar={setFonte} rotulo="Casa legislativa" />
          <Seletor
            rotulo="Estado"
            valor={uf}
            onMudar={setUf}
            vazio="Todas as UFs"
            opcoes={UFS.map((u) => ({ valor: u, rotulo: u }))}
          />
          <Seletor
            rotulo="Partido"
            valor={partido}
            onMudar={setPartido}
            vazio="Todos os partidos"
            opcoes={partidos.map((p) => ({ valor: p, rotulo: p }))}
          />
        </BarraFiltros>

        {erro ? (
          <Aviso
            tom="contra"
            titulo="Não foi possível carregar o placar"
            acao={
              <Button variante="secundario" tamanho="s" onClick={() => setTentativa((t) => t + 1)}>
                Tentar de novo
              </Button>
            }
          >
            A API não respondeu. Confira a conexão e tente de novo; se persistir, o serviço pode estar fora do ar.
          </Aviso>
        ) : loading ? (
          <Placar>
            <PlacarCabecalho ordem={ORDEM_NO_CABECALHO[ordem]} colunaVotos={false} />
            {Array.from({ length: 8 }).map((_, i) => (
              <PlacarLinhaEsqueleto key={i} colunaVotos={false} />
            ))}
          </Placar>
        ) : filtered.length === 0 ? (
          /* UI-004: vazio com motivo e ação que resolve */
          <Vazio
            icone="placar"
            titulo={hasFilters ? "Nenhum parlamentar com esses filtros" : "Nenhum parlamentar encontrado"}
            acao={
              hasFilters ? (
                <Button variante="secundario" onClick={clearFilters}>
                  Limpar filtros
                </Button>
              ) : undefined
            }
          >
            {hasFilters
              ? "A combinação de busca, casa, UF e partido não devolveu ninguém."
              : "A base ainda não tem parlamentares carregados."}
          </Vazio>
        ) : (
          <>
            {/* UI-003: contagem acima da lista, antes de rolar */}
            <p className="text-texto-s text-zil-texto-2 zil-num">
              {comScore.length} com score
              {semScore.length > 0 && <> · {semScore.length} sem votos ZIL suficientes</>}
            </p>

            <Placar>
              {/* Sem a coluna de votos alinhados: a API só traz o total (ver ParlamentarCard). */}
              <PlacarCabecalho
                ordem={ORDEM_NO_CABECALHO[ordem]}
                ordenarScore={ordenarPorScore}
                ordenarNome={ordenarPorNome}
                colunaVotos={false}
              />
              {comScore.map((p, i) => (
                <ParlamentarCard key={p.id} parlamentar={p} rank={i + 1} />
              ))}
            </Placar>

            {semScore.length > 0 && (
              <div className="grid gap-4 mt-10">
                <h2 className="text-titulo-4">
                  Sem votos ZIL suficientes para calcular score{" "}
                  <span className="text-zil-texto-2 zil-num">({semScore.length})</span>
                </h2>
                <Placar rotulo="Parlamentares sem score">
                  {semScore.map((p, i) => (
                    <ParlamentarCard key={p.id} parlamentar={p} rank={comScore.length + i + 1} />
                  ))}
                </Placar>
              </div>
            )}
          </>
        )}
      </section>
    </div>
  );
}
