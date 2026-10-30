"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { CategoriaBadge } from "@/components/CategoriaBadge";
import { DirecaoBadge } from "@/components/DirecaoBadge";
import { BancadasVotacao, HemicicloVotacao } from "@/components/PlenarioVotacao";
import {
  Avatar,
  Aviso,
  BarraFiltros,
  Busca,
  Button,
  Card,
  CardEsqueleto,
  Chip,
  Chips,
  Esqueleto,
  Icone,
  Linha,
  Lista,
  PlacarLinhaEsqueleto,
  Selo,
  Vazio,
  type TomSelo,
} from "@/components/ui";
import {
  CADEIRAS,
  GRUPOS,
  ROTULO_GRUPO,
  ROTULO_VOTO,
  contarGrupos,
  grupoDoVoto,
  type GrupoVoto,
  type VotoIndividual,
} from "@/lib/votacao";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ProposicaoSnippet {
  id: string;
  tipo: string | null;
  numero: number | null;
  ano: number | null;
  ementa: string | null;
  resumo_simples: string | null;
}

interface VotacaoDetail {
  id: string;
  fonte: string;
  descricao: string | null;
  data: string | null;
  resultado: string | null;
  votos_sim: number | null;
  votos_nao: number | null;
  categorias_zil: string[] | null;
  direcao_esperada: string | null;
  peso: number | null;
  proposicao: ProposicaoSnippet | null;
}

/**
 * Tom do selo de voto: `alinhado` quando bate com a direção esperada pelo
 * ZIL, `contra` quando é sim/não na direção oposta, `padrao` para o resto
 * (abstenção, ausência, obstrução) e para votações ainda sem direção.
 */
function tomDoVoto(voto: string, direcao: string | null | undefined): TomSelo {
  if (!direcao || (voto !== "sim" && voto !== "nao")) return "padrao";
  return voto === direcao ? "alinhado" : "contra";
}

function tomDoResultado(texto: string): TomSelo {
  const t = texto.toLowerCase();
  if (t.includes("aprovad")) return "alinhado";
  if (t.includes("rejeitad")) return "contra";
  return "padrao";
}

export default function VotacaoDetailPage() {
  const params = useParams();
  const id = params?.id as string;

  const [votacao, setVotacao] = useState<VotacaoDetail | null>(null);
  const [votos, setVotos] = useState<VotoIndividual[]>([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState(false);
  // Um filtro só para o hemiciclo, o mapa e a lista: tocar "Não" no
  // plenário acende as cadeiras e filtra os nomes abaixo.
  const [filtroGrupo, setFiltroGrupo] = useState<GrupoVoto | "">("");
  const [filtroUF, setFiltroUF] = useState("");
  const [busca, setBusca] = useState("");
  // Incrementa para refazer a busca depois de um erro.
  const [tentativa, setTentativa] = useState(0);

  useEffect(() => {
    if (!id) return;
    async function load() {
      setLoading(true);
      setErro(false);
      try {
        const [vRes, votoRes] = await Promise.all([
          fetch(`${API_BASE}/votacoes/${id}`),
          fetch(`${API_BASE}/votacoes/${id}/votos`),
        ]);
        setVotacao(vRes.ok ? await vRes.json() : null);
        setVotos(await votoRes.json());
      } catch (err) {
        console.error(err);
        setErro(true);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id, tentativa]);

  const porVoto = votos.filter(
    (v) => (!filtroGrupo || grupoDoVoto(v.voto) === filtroGrupo) && (!filtroUF || v.parlamentar_uf === filtroUF),
  );

  const termo = busca.trim().toLowerCase();
  const filtered = termo
    ? porVoto.filter(
        (v) =>
          v.parlamentar_nome.toLowerCase().includes(termo) ||
          v.parlamentar_partido?.toLowerCase().includes(termo) ||
          v.parlamentar_uf?.toLowerCase().includes(termo)
      )
    : porVoto;

  const cadeiras = CADEIRAS[votacao?.fonte ?? "camara"] ?? 513;
  const grupos = contarGrupos(votos, cadeiras);
  const semRegistro = Math.max(0, cadeiras - votos.length);

  const prop = votacao?.proposicao;
  const propLabel = prop
    ? `${prop.tipo ?? ""} ${prop.numero ?? ""}/${prop.ano ?? ""}`.trim()
    : null;
  const propDescricao = prop?.resumo_simples || prop?.ementa;

  const voltar = prop ? { href: `/proposicoes/${prop.id}`, rotulo: "Voltar à proposição" } : { href: "/proposicoes", rotulo: "Todas as proposições" };

  if (loading) {
    return (
      <div className="zil-container" aria-busy="true" aria-label="Carregando votação">
        <header className="pt-10 md:pt-16 grid gap-4">
          <Esqueleto className="h-4 w-24" />
          <Esqueleto className="h-10 w-72" />
          <Esqueleto className="h-[26px] w-64 rounded-pilula" />
        </header>
        <section className="zil-secao grid gap-4">
          <CardEsqueleto />
          <div className="grid gap-0.5 p-1.5 rounded-l bg-zil-superficie-1">
            {Array.from({ length: 6 }, (_, i) => (
              <PlacarLinhaEsqueleto key={i} />
            ))}
          </div>
        </section>
      </div>
    );
  }

  if (erro) {
    return (
      <div className="zil-container zil-secao">
        <Aviso
          tom="contra"
          titulo="Não foi possível carregar a votação"
          acao={
            <Button variante="secundario" tamanho="s" onClick={() => setTentativa((t) => t + 1)}>
              Tentar de novo
            </Button>
          }
        >
          A API não respondeu. Confira a conexão e tente de novo em instantes.
        </Aviso>
      </div>
    );
  }

  if (!votacao && votos.length === 0) {
    return (
      <div className="zil-container zil-secao">
        <Vazio
          icone="placar"
          titulo="Votação não encontrada"
          acao={
            <Button variante="secundario" href="/proposicoes">
              Ver todas as proposições
            </Button>
          }
        >
          O endereço pode estar errado ou a votação saiu da cobertura.
        </Vazio>
      </div>
    );
  }

  return (
    <div className="zil-container">
      <div className="pt-6 md:pt-10">
        <Button variante="fantasma" tamanho="s" href={voltar.href} className="-ml-3.5">
          <Icone nome="chevron-esquerda" tamanho="s" />
          {voltar.rotulo}
        </Button>
      </div>

      {/* Cabeçalho — proposição como protagonista */}
      <header className="pt-6 md:pt-8 grid gap-4">
        <p className="text-rotulo uppercase text-zil-texto-2">Votação</p>
        {propLabel && prop && (
          <h1 className="text-titulo-1 md:text-display-m">
            <Link href={`/proposicoes/${prop.id}`} className="text-zil-texto no-underline hover:text-zil-texto-2 transition-colors duration-toque">
              {propLabel}
            </Link>
          </h1>
        )}
        {propDescricao && <p className="text-texto-l text-zil-texto-2 max-w-[60ch]">{propDescricao}</p>}

        {/* Metadados da votação */}
        <div className="flex flex-wrap items-center gap-2">
          {votacao?.data && <span className="text-texto-s text-zil-texto-2 zil-num mr-2">{new Date(votacao.data).toLocaleDateString("pt-BR")}</span>}
          {votacao?.resultado && <Selo tom={tomDoResultado(votacao.resultado)}>{votacao.resultado}</Selo>}
          <DirecaoBadge direcao={votacao?.direcao_esperada} />
          {votacao?.categorias_zil?.map((c) => (
            <CategoriaBadge key={c} codigo={c} />
          ))}
        </div>

        {prop && (
          <div>
            <Button variante="secundario" tamanho="s" href={`/proposicoes/${prop.id}`}>
              Ver proposição completa
            </Button>
          </div>
        )}
      </header>

      <section className="zil-secao grid gap-4">
        {/* Detalhes processuais colapsados — <details> nativo (UI-012) */}
        {votacao?.descricao && (
          <Lista>
            <details className="group">
              <summary className="flex items-center gap-3.5 min-h-14 px-3 py-2.5 rounded-m text-zil-texto cursor-pointer select-none list-none [&::-webkit-details-marker]:hidden transition-colors duration-toque hover:bg-zil-superficie-2 active:bg-zil-superficie-3">
                <span className="flex-1 min-w-0 grid gap-0.5">
                  <span className="text-[16px] leading-[22px] font-medium">Detalhes da sessão</span>
                  <span className="text-texto-s text-zil-texto-2">Descrição registrada pela Casa</span>
                </span>
                <Icone nome="chevron-baixo" className="text-zil-texto-3 transition-transform duration-padrao ease-padrao group-open:rotate-180" />
              </summary>
              <p className="px-3 pt-1 pb-3 text-texto text-zil-texto-2 max-w-[68ch]">{votacao.descricao}</p>
            </details>
          </Lista>
        )}

        {/* Plenário: hemiciclo e bancadas por UF */}
        {votos.length === 0 ? (
          <Aviso titulo="Votação sem voto individual">
            Esta votação não tem registro de voto por parlamentar — em geral é uma votação simbólica, em que o
            plenário decide sem painel (RICD art. 185). Por isso não há plenário para mostrar nem lista de nomes.
          </Aviso>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            <Card className="grid gap-4 content-start">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <h2 className="text-titulo-4">Plenário</h2>
                {votacao?.resultado && <Selo tom={tomDoResultado(votacao.resultado)}>{votacao.resultado}</Selo>}
              </div>
              <HemicicloVotacao
                votos={votos}
                cadeiras={cadeiras}
                direcao={votacao?.direcao_esperada}
                grupo={filtroGrupo}
                aoMudarGrupo={setFiltroGrupo}
                uf={filtroUF}
              />
            </Card>
            <Card className="grid gap-4 content-start">
              <div className="grid gap-1">
                <h2 className="text-titulo-4">Como cada estado votou</h2>
                <p className="text-texto-s text-zil-texto-2">
                  {filtroUF ? `Filtrando por ${filtroUF} · toque de novo para tirar` : "Parcela de sim em cada bancada. Toque num estado para filtrar."}
                </p>
              </div>
              <BancadasVotacao votos={votos} direcao={votacao?.direcao_esperada} uf={filtroUF} aoMudarUF={setFiltroUF} />
            </Card>
          </div>
        )}
      </section>

      {/* Votos por parlamentar — não existe em votação simbólica (ver o aviso acima). */}
      {votos.length > 0 && (
        <section className="pb-16 md:pb-24 grid gap-4">
          <h2 className="text-titulo-3">
            Como cada parlamentar votou <span className="text-zil-texto-2 zil-num">({votos.length})</span>
          </h2>

          <BarraFiltros>
            <Busca valor={busca} onMudar={setBusca} rotulo="Buscar parlamentar" placeholder="Buscar parlamentar, partido ou UF" className="w-full sm:w-72" />
            <Chips>
              <Chip ativo={!filtroGrupo} onClick={() => setFiltroGrupo("")}>
                Todos
              </Chip>
              {GRUPOS.filter((g) => grupos[g] > 0).map((g) => (
                <Chip key={g} ativo={filtroGrupo === g} n={grupos[g]} onClick={() => setFiltroGrupo(filtroGrupo === g ? "" : g)}>
                  {ROTULO_GRUPO[g]}
                </Chip>
              ))}
              {filtroUF && (
                <Chip ativo removivel onClick={() => setFiltroUF("")} aria-label={`Tirar o filtro ${filtroUF}`}>
                  {filtroUF}
                </Chip>
              )}
            </Chips>
          </BarraFiltros>

          <p className="text-texto-s text-zil-texto-2 zil-num">
            {filtered.length} {filtered.length === 1 ? "voto registrado" : "votos registrados"}
            {filtroGrupo ? ` — ${ROTULO_GRUPO[filtroGrupo]}` : ""}
            {filtroUF ? ` · ${filtroUF}` : ""}
            {filtroGrupo === "nao_votou" && semRegistro > 0 &&
              `. Outros ${semRegistro} não registraram voto e não aparecem na lista da Câmara.`}
          </p>

          {filtered.length === 0 ? (
            <Vazio
              titulo="Nenhum parlamentar com esse filtro"
              acao={
                <Button
                  variante="secundario"
                  onClick={() => {
                    setBusca("");
                    setFiltroGrupo("");
                    setFiltroUF("");
                  }}
                >
                  Limpar filtros
                </Button>
              }
            >
              Tente outro nome, partido ou UF, ou volte a ver todos os votos.
            </Vazio>
          ) : (
            <Lista separada>
              {filtered.map((v) => (
                <Linha
                  key={v.parlamentar_id}
                  href={`/parlamentar/${v.parlamentar_id}`}
                  icone={<Avatar nome={v.parlamentar_nome} tamanho="s" />}
                  titulo={v.parlamentar_nome}
                  sub={`${v.parlamentar_partido ?? "—"} · ${v.parlamentar_uf ?? "—"}`}
                  fim={<Selo tom={tomDoVoto(v.voto, votacao?.direcao_esperada)}>{ROTULO_VOTO[v.voto] ?? v.voto.toUpperCase()}</Selo>}
                />
              ))}
            </Lista>
          )}
        </section>
      )}
    </div>
  );
}
