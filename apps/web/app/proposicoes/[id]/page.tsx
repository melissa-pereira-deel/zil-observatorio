"use client";

import { useState, useEffect, useMemo } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { CategoriaBadge } from "@/components/CategoriaBadge";
import { ContextoBadge } from "@/components/ContextoBadge";
import { DirecaoBadge } from "@/components/DirecaoBadge";
import { Button, Card, CardEsqueleto, Esqueleto, Icone, Linha, Lista, Selo, Vazio, type TomSelo } from "@/components/ui";
import type { Proposicao, ProposicaoContexto } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Votacao {
  id: string;
  fonte_id: string;
  data: string | null;
  descricao: string | null;
  resultado: string | null;
  votos_sim: number | null;
  votos_nao: number | null;
  categorias_zil: string[] | null;
  direcao_esperada: string | null;
  peso: number | null;
}

function tomDoResultado(texto: string): TomSelo {
  const t = texto.toLowerCase();
  if (t.includes("aprovad")) return "alinhado";
  if (t.includes("rejeitad")) return "contra";
  return "padrao";
}

/**
 * Cabeçalho de um `<details>` nativo (UI-012) com a cara de uma `Linha`:
 * título, subtítulo e um chevron que gira quando aberto. O marcador padrão
 * do navegador some; o `<details>` continua funcionando sem JavaScript.
 */
function SumarioLinha({ titulo, sub, className = "" }: { titulo: string; sub?: string; className?: string }) {
  return (
    <summary
      className={`flex items-center gap-3.5 min-h-14 px-3 py-2.5 rounded-m text-zil-texto cursor-pointer select-none list-none [&::-webkit-details-marker]:hidden transition-colors duration-toque hover:bg-zil-superficie-2 active:bg-zil-superficie-3 ${className}`}
    >
      <span className="flex-1 min-w-0 grid gap-0.5">
        <span className="text-[16px] leading-[22px] font-medium">{titulo}</span>
        {sub && <span className="text-texto-s text-zil-texto-2">{sub}</span>}
      </span>
      <Icone nome="chevron-baixo" className="text-zil-texto-3 transition-transform duration-padrao ease-padrao group-open:rotate-180" />
    </summary>
  );
}

export default function ProposicaoDetailPage() {
  const params = useParams();
  const id = params?.id as string;

  const [proposicao, setProposicao] = useState<Proposicao | null>(null);
  const [votacoes, setVotacoes] = useState<Votacao[]>([]);
  const [contexto, setContexto] = useState<ProposicaoContexto | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    async function load() {
      setLoading(true);
      try {
        const [pRes, vRes, cRes] = await Promise.all([
          fetch(`${API_BASE}/proposicoes/${id}`),
          fetch(`${API_BASE}/proposicoes/${id}/votacoes`),
          fetch(`${API_BASE}/proposicoes/${id}/contexto`),
        ]);
        setProposicao(await pRes.json());
        const vData = await vRes.json();
        setVotacoes(Array.isArray(vData) ? vData : []);
        if (cRes.ok) setContexto(await cRes.json());
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  // UI-010: Síntese da posição ZIL
  const posicaoZil = useMemo(() => {
    const comDirecao = votacoes.filter((v) => v.direcao_esperada !== null);
    if (comDirecao.length === 0) return null;
    const favoraveis = comDirecao.filter((v) => v.direcao_esperada === "sim").length;
    const contrarias = comDirecao.filter((v) => v.direcao_esperada === "nao").length;
    const direcao = favoraveis > 0 && contrarias === 0 ? "sim" : contrarias > 0 && favoraveis === 0 ? "nao" : null;
    return {
      direcao,
      label: direcao === "sim" ? "Favorável" : direcao === "nao" ? "Contrária" : "Posição mista",
      total: comDirecao.length,
    };
  }, [votacoes]);

  if (loading) {
    return (
      <div className="zil-container" aria-busy="true" aria-label="Carregando proposição">
        <header className="pt-10 md:pt-16 grid gap-4">
          <Esqueleto className="h-[26px] w-40 rounded-pilula" />
          <Esqueleto className="h-10 w-72" />
          <Esqueleto className="h-4 w-56" />
        </header>
        <section className="zil-secao grid gap-4">
          <CardEsqueleto />
          <CardEsqueleto />
        </section>
      </div>
    );
  }

  if (!proposicao) {
    return (
      <div className="zil-container zil-secao">
        <Vazio
          icone="documento"
          titulo="Proposição não encontrada"
          acao={
            <Button variante="secundario" href="/proposicoes">
              Ver todas as proposições
            </Button>
          }
        >
          O endereço pode estar errado ou a proposição saiu da cobertura.
        </Vazio>
      </div>
    );
  }

  const hasContexto = contexto?.contexto_status === "pronto" && contexto.resumo_simples;
  const temContextoCompleto = !!contexto && !!(contexto.glossario || contexto.leis_referenciadas?.length);

  return (
    <div className="zil-container">
      <div className="pt-6 md:pt-10">
        <Button variante="fantasma" tamanho="s" href="/proposicoes" className="-ml-3.5">
          <Icone nome="chevron-esquerda" tamanho="s" />
          Todas as proposições
        </Button>
      </div>

      {/* Cabeçalho */}
      <header className="pt-6 md:pt-8 grid gap-4">
        <div className="flex flex-wrap items-center gap-2">
          {proposicao.situacao && <Selo>{proposicao.situacao}</Selo>}
          {proposicao.categorias_zil?.map((c) => (
            <CategoriaBadge key={c} codigo={c} />
          ))}
          <ContextoBadge status={proposicao.contexto_status} confianca={proposicao.confianca} />
        </div>
        <h1 className="text-titulo-1 md:text-display-m">
          {proposicao.tipo} {proposicao.numero}/{proposicao.ano}
        </h1>
        <p className="flex flex-wrap items-center gap-x-4 gap-y-1 text-texto-s text-zil-texto-2 zil-num">
          {proposicao.data_apresentacao && <span>Apresentada em {new Date(proposicao.data_apresentacao).toLocaleDateString("pt-BR")}</span>}
          {proposicao.url_inteiro_teor && (
            <a
              href={proposicao.url_inteiro_teor}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-zil-texto-2 hover:text-zil-texto transition-colors duration-toque"
            >
              Texto completo
              <Icone nome="externo" tamanho="s" />
            </a>
          )}
        </p>
      </header>

      <section className="zil-secao grid gap-4">
        {/* Resumo em linguagem simples */}
        {hasContexto ? (
          <Card>
            <p className="text-rotulo uppercase text-zil-texto-2 mb-3">Em linguagem simples</p>
            <p className="text-texto max-w-[68ch]">{contexto!.resumo_simples}</p>
          </Card>
        ) : (
          /* UI-008: sem análise, a pessoa fica sabendo e a ementa abre logo abaixo */
          <Card>
            <p className="text-texto text-zil-texto-2 max-w-[68ch]">
              Esta proposição ainda não foi analisada pela plataforma. A ementa técnica original está disponível abaixo.
            </p>
          </Card>
        )}

        {/* UI-008: ementa colapsada por padrão quando há resumo simples; UI-012: <details> nativo */}
        <Lista>
          <details className="group" open={!hasContexto}>
            <SumarioLinha titulo="Ementa técnica" sub="Texto original, como registrado na Casa" />
            <p className="px-3 pt-1 pb-3 text-texto text-zil-texto-2 max-w-[68ch]">{proposicao.ementa}</p>
          </details>
        </Lista>

        {/* Impacto ZIL */}
        {contexto?.impacto_zil && (
          <Card>
            <h2 className="text-titulo-4 mb-3">Impacto para a soberania industrial</h2>
            <p className="text-texto text-zil-texto-2 max-w-[68ch]">{contexto.impacto_zil}</p>
          </Card>
        )}

        {/* UI-012: contexto completo em <details>/<summary> nativo (sem useState) */}
        {temContextoCompleto && contexto && (
          <details className="group grid gap-4">
            <SumarioLinha
              titulo="Contexto completo"
              sub="Glossário, leis referenciadas e metadados da análise"
              className="rounded-l bg-zil-superficie-1 px-6 min-h-16 hover:bg-zil-superficie-2"
            />

            {/* Glossário */}
            {contexto.glossario && Object.keys(contexto.glossario).length > 0 && (
              <Card>
                <h2 className="text-titulo-4 mb-4">Glossário</h2>
                <dl className="grid gap-3 max-w-[68ch]">
                  {Object.entries(contexto.glossario).map(([term, def]) => (
                    <div key={term} className="text-texto">
                      <dt className="inline font-semibold">{term}: </dt>
                      <dd className="inline text-zil-texto-2">{def}</dd>
                    </div>
                  ))}
                </dl>
              </Card>
            )}

            {/* Leis referenciadas */}
            {contexto.leis_referenciadas && contexto.leis_referenciadas.length > 0 && (
              <Lista titulo="Leis referenciadas">
                {contexto.leis_referenciadas.map((lei) => {
                  const titulo = `${lei.lei_id} — Art. ${lei.numero_artigo}`;
                  const sub = lei.texto_snippet ? <span className="line-clamp-2">{lei.texto_snippet}</span> : undefined;
                  const resolvida = lei.status === "resolvido" && !!lei.url_planalto;
                  return resolvida ? (
                    <Linha
                      key={`${lei.lei_id}-${lei.numero_artigo}`}
                      href={lei.url_planalto!}
                      target="_blank"
                      rel="noopener noreferrer"
                      titulo={titulo}
                      sub={sub}
                      fim={<Icone nome="externo" />}
                      chevron={false}
                    />
                  ) : (
                    <Linha
                      key={`${lei.lei_id}-${lei.numero_artigo}`}
                      titulo={titulo}
                      sub={sub}
                      fim={<Selo tom="neutro">{lei.status.replace(/_/g, " ")}</Selo>}
                    />
                  );
                })}
              </Lista>
            )}

            {/* Metadados da análise */}
            <Card compacto>
              <p className="flex flex-wrap gap-x-4 gap-y-1 text-texto-s text-zil-texto-2 zil-num">
                {contexto.enriquecido_em && <span>Atualizado em {new Date(contexto.enriquecido_em).toLocaleDateString("pt-BR")}</span>}
                {contexto.confianca !== null && contexto.confianca !== undefined && <span>Confiança: {Math.round(contexto.confianca * 100)}%</span>}
                <span>
                  Modelo: {contexto.modelo_llm} · Pipeline v{contexto.versao_pipeline}
                </span>
              </p>
            </Card>
          </details>
        )}
      </section>

      {/* Votações */}
      <section className="pb-16 md:pb-24 grid gap-4">
        <h2 className="text-titulo-3">
          Votações <span className="text-zil-texto-2 zil-num">({votacoes.length})</span>
        </h2>

        {/* UI-010: Síntese da posição ZIL */}
        {posicaoZil && (
          <Card className="grid gap-3">
            <p className="text-rotulo uppercase text-zil-texto-2">ZIL avalia esta proposição como</p>
            <div className="flex flex-wrap items-center gap-3">
              {posicaoZil.direcao ? <DirecaoBadge direcao={posicaoZil.direcao} /> : <Selo tom="neutro" ponto>Posição mista</Selo>}
              <span className="text-titulo-3">{posicaoZil.label}</span>
            </div>
            <p className="text-texto-s text-zil-texto-2 zil-num">
              Com base em {posicaoZil.total} {posicaoZil.total === 1 ? "votação monitorada" : "votações monitoradas"} ·{" "}
              <Link href="/metodologia" className="text-zil-texto underline underline-offset-4 decoration-1">
                ver metodologia
              </Link>
            </p>
          </Card>
        )}

        {votacoes.length === 0 ? (
          <Vazio icone="placar" titulo="Nenhuma votação registrada">
            Nenhuma votação plenária registrada para esta proposição.
          </Vazio>
        ) : (
          <Lista>
            {votacoes.map((v) => {
              // UI-011: resultado inferido quando null — mas só quando existe
              // placar para inferir.
              //
              // Votação simbólica não tem voto nominal: a Câmara registra 0 e 0.
              // Com `0 > 0` falso, a regra anterior exibia "Rejeitado*" numa
              // votação aprovada. Três das sete votações curadas são simbólicas,
              // então isso estava no ar. Sem placar, não há o que inferir.
              const temPlacar =
                v.votos_sim !== null &&
                v.votos_nao !== null &&
                v.votos_sim + v.votos_nao > 0;
              const resultadoDisplay =
                v.resultado ??
                (temPlacar ? (v.votos_sim! > v.votos_nao! ? "Aprovado*" : "Rejeitado*") : null);
              const resultadoInferido = !v.resultado && resultadoDisplay !== null;

              return (
                <Linha
                  key={v.id}
                  href={`/votacoes/${v.id}`}
                  title="Ver como cada parlamentar votou"
                  titulo={v.descricao ?? `Votação ${v.fonte_id}`}
                  sub={
                    <span className="flex flex-wrap items-center gap-x-2 gap-y-1 zil-num">
                      {v.data && <span>{new Date(v.data).toLocaleDateString("pt-BR")}</span>}
                      {(v.votos_sim !== null || v.votos_nao !== null) && (
                        <span>
                          · {v.votos_sim ?? "—"} sim · {v.votos_nao ?? "—"} não
                        </span>
                      )}
                      {v.categorias_zil?.map((c) => (
                        <CategoriaBadge key={c} codigo={c} />
                      ))}
                    </span>
                  }
                  fim={
                    <span className="flex flex-wrap items-center justify-end gap-2">
                      {/* UI-011: resultado inferido leva * e title explicativo */}
                      {resultadoDisplay && (
                        <Selo tom={tomDoResultado(resultadoDisplay)} title={resultadoInferido ? "Resultado inferido dos votos registrados" : undefined}>
                          {resultadoDisplay}
                        </Selo>
                      )}
                      {/* UI-009: DirecaoBadge */}
                      <DirecaoBadge direcao={v.direcao_esperada} />
                    </span>
                  }
                />
              );
            })}
          </Lista>
        )}
      </section>
    </div>
  );
}
