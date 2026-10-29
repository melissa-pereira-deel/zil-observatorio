"use client";

import { useState, useEffect, useMemo } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

import { CategoriaBadge } from "@/components/CategoriaBadge";
import { DirecaoBadge } from "@/components/DirecaoBadge";
import { tituloDoScore } from "@/components/ParlamentarCard";
import {
  Avatar,
  Aviso,
  Button,
  Card,
  Chip,
  Chips,
  Esqueleto,
  Icone,
  Linha,
  Lista,
  Medidor,
  ScoreGrande,
  ScorePilula,
  Selo,
  Vazio,
  VotosBarra,
} from "@/components/ui";
import { CATEGORIA_COR, CATEGORIA_LABELS } from "@/lib/categorias";
import type { VotoHistorico } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ParlamentarDetail {
  id: string;
  nome: string;
  nome_civil: string | null;
  partido: string | null;
  uf: string | null;
  foto_url: string | null;
  email: string | null;
  fonte: string;
  score_zil: number | null;
  score_atualizado_em: string | null;
  frentes_parlamentares: string[] | null;
}

const VOTO_LABEL: Record<string, string> = {
  sim: "Sim",
  nao: "Não",
  abstencao: "Abstenção",
  ausente: "Ausente",
  obstrucao: "Obstrução",
  artigo_17: "Art. 17",
};

/** Ponto de alinhamento com a posição ZIL: o primeiro encoding (UI-014). */
function PontoAlinhamento({ alinhado }: { alinhado: boolean | null }) {
  const cor = alinhado === true ? "bg-zil-alinhado" : alinhado === false ? "bg-zil-contra" : "bg-zil-superficie-4";
  return <span aria-hidden="true" className={`w-2.5 h-2.5 rounded-full ${cor}`} />;
}

export default function ParlamentarPage() {
  const params = useParams();
  const id = params?.parlamentar_id as string;

  const [parl, setParl] = useState<ParlamentarDetail | null>(null);
  const [votos, setVotos] = useState<VotoHistorico[]>([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState(false);
  // Incrementar refaz o fetch: é o que "Tentar de novo" faz.
  const [tentativa, setTentativa] = useState(0);
  const [filtroCategoria, setFiltroCategoria] = useState("");

  useEffect(() => {
    if (!id) return;
    async function load() {
      setLoading(true);
      setErro(false);
      try {
        const [pRes, vRes] = await Promise.all([
          fetch(`${API_BASE}/parlamentares/${id}`),
          fetch(`${API_BASE}/parlamentares/${id}/votos-zil`),
        ]);
        // 404 é "não encontrado", não erro de rede: cai no estado vazio.
        if (pRes.status === 404) {
          setParl(null);
          setVotos([]);
          return;
        }
        if (!pRes.ok || !vRes.ok) throw new Error(`API error: ${pRes.status}/${vRes.status}`);
        setParl(await pRes.json());
        setVotos(await vRes.json());
      } catch (err) {
        console.error(err);
        setErro(true);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id, tentativa]);

  const breakdown = useMemo(() => {
    const map: Record<string, { alinhados: number; contra: number; total: number }> = {};
    for (const v of votos) {
      for (const cat of v.categorias_zil ?? []) {
        if (!map[cat]) map[cat] = { alinhados: 0, contra: 0, total: 0 };
        map[cat].total++;
        if (v.alinhado === true) map[cat].alinhados++;
        if (v.alinhado === false) map[cat].contra++;
      }
    }
    return Object.entries(map).sort((a, b) => b[1].total - a[1].total);
  }, [votos]);

  const votosFiltrados = filtroCategoria
    ? votos.filter((v) => v.categorias_zil?.includes(filtroCategoria))
    : votos;

  const alinhados = votos.filter((v) => v.alinhado === true).length;
  const contra = votos.filter((v) => v.alinhado === false).length;
  const semDirecao = votos.length - alinhados - contra;

  function getScoreLabel(score: number | null): string {
    if (score === null) return "Sem dados suficientes";
    if (score >= 8) return "Alinhamento total";
    if (score >= 4) return "Majoritariamente alinhado";
    if (score >= 1) return "Parcialmente alinhado";
    if (score >= -1) return "Posição neutra";
    if (score >= -4) return "Parcialmente contrário";
    if (score >= -8) return "Majoritariamente contrário";
    return "Posição contrária";
  }

  // UI-022: a frase conta só os votos com direção esperada. Quem votou em 9
  // pautas e só 4 tinham direção não "votou contra" nas outras 5 — elas não
  // entram no score, e a frase diz isso.
  function getSynthesis(): string | null {
    const comDirecao = alinhados + contra;
    if (comDirecao === 0) return votos.length ? `Nenhuma das ${votos.length} votações registradas tem direção esperada definida.` : null;
    const pct = Math.round((alinhados / comDirecao) * 100);
    const resto = semDirecao ? ` Outras ${semDirecao} ainda não têm direção definida.` : "";
    if (pct === 100) return `Votou a favor da soberania industrial em todas as ${comDirecao} pautas com direção definida.${resto}`;
    if (pct >= 50) return `Votou a favor da soberania industrial em ${alinhados} de ${comDirecao} pautas com direção definida.${resto}`;
    if (pct > 0) return `Votou contra a posição de soberania industrial em ${contra} de ${comDirecao} pautas com direção definida.${resto}`;
    return `Votou contra a posição de soberania industrial em todas as ${comDirecao} pautas com direção definida.${resto}`;
  }

  const synthesis = getSynthesis();
  const rotuloFiltro = filtroCategoria ? CATEGORIA_LABELS[filtroCategoria] ?? filtroCategoria : "";

  const voltar = (
    <Button href="/ranking" variante="fantasma" tamanho="s" className="-ml-3.5">
      <Icone nome="chevron-esquerda" />
      Voltar ao placar
    </Button>
  );

  if (loading) {
    return (
      <div className="zil-container pt-10 md:pt-16 grid gap-8">
        {voltar}
        {/* Esqueleto com a forma do hero: avatar, nome, meta e o bloco do score. */}
        <Card className="grid gap-8 md:grid-cols-2 md:p-10" aria-busy="true">
          <div className="flex items-start gap-6">
            <Esqueleto className="w-24 h-24 rounded-full shrink-0" />
            <div className="flex-1 grid gap-3 pt-2">
              <Esqueleto className="h-8 w-[70%]" />
              <Esqueleto className="h-4 w-[45%]" />
            </div>
          </div>
          <div className="grid gap-4">
            <Esqueleto className="h-16 w-40" />
            <Esqueleto className="h-5 w-[60%]" />
            <Esqueleto className="h-2.5 w-full rounded-pilula" />
          </div>
        </Card>
        <Lista aria-hidden="true">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3.5 min-h-14 px-3 py-2.5">
              <Esqueleto className="w-8 h-8 rounded-[10px]" />
              <div className="flex-1 grid gap-2">
                <Esqueleto className="h-3.5 w-[55%]" />
                <Esqueleto className="h-3 w-[35%]" />
              </div>
              <Esqueleto className="h-[26px] w-14 rounded-pilula" />
            </div>
          ))}
        </Lista>
      </div>
    );
  }

  if (erro) {
    return (
      <div className="zil-container pt-10 md:pt-16 grid gap-8">
        {voltar}
        <Aviso
          tom="contra"
          titulo="Não foi possível carregar este parlamentar"
          acao={
            <Button variante="secundario" tamanho="s" onClick={() => setTentativa((t) => t + 1)}>
              Tentar de novo
            </Button>
          }
        >
          A API não respondeu. Confira a conexão e tente de novo; se persistir, o serviço pode estar fora do ar.
        </Aviso>
      </div>
    );
  }

  if (!parl) {
    return (
      <div className="zil-container pt-10 md:pt-16 grid gap-8">
        {voltar}
        <Vazio
          icone="busca"
          titulo="Parlamentar não encontrado"
          acao={
            <Button href="/ranking" variante="secundario">
              Ver o placar
            </Button>
          }
        >
          Não há ninguém com esse identificador na base. O link pode estar desatualizado.
        </Vazio>
      </div>
    );
  }

  const cargo = parl.fonte === "camara" ? "Deputado(a) Federal" : "Senador(a)";
  const meta = [parl.partido, parl.uf, cargo].filter(Boolean).join(" · ");

  return (
    <div className="zil-container pt-10 md:pt-16">
      {voltar}

      {/* Hero — UI-013: score e síntese como protagonistas, ao lado da pessoa */}
      <Card className="mt-6 grid gap-8 md:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)] md:gap-12 md:p-10">
        <div className="flex items-start gap-5 md:gap-6">
          <Avatar nome={parl.nome} fotoUrl={parl.foto_url} tamanho="xl" />
          <div className="min-w-0 grid gap-2">
            <h1 className="text-titulo-2 md:text-titulo-1">{parl.nome}</h1>
            {parl.nome_civil && parl.nome_civil !== parl.nome && (
              <p className="text-texto-s text-zil-texto-2">{parl.nome_civil}</p>
            )}
            <p className="text-texto-ui text-zil-texto-2">{meta}</p>
            {parl.email && (
              <a
                href={`mailto:${parl.email}`}
                className="text-texto-s text-zil-texto-2 underline underline-offset-4 decoration-1 transition-colors duration-toque hover:text-zil-texto break-all"
              >
                {parl.email}
              </a>
            )}
          </div>
        </div>

        <div className="grid gap-5 content-start">
          <span className="text-texto-ui text-zil-texto-2">
            Score ZIL · escala de −10 a +10
            {parl.score_atualizado_em && (
              <> · atualizado {new Date(parl.score_atualizado_em).toLocaleDateString("pt-BR")}</>
            )}
          </span>

          {/* UI-001: o número leva no title em quantos votos se apoia. */}
          {parl.score_zil !== null ? (
            <div title={tituloDoScore(votos.length)} className="grid gap-5">
              <ScoreGrande valor={parl.score_zil} frase={getScoreLabel(parl.score_zil)} />
              <Medidor valor={parl.score_zil} />
            </div>
          ) : (
            <div title={tituloDoScore(votos.length)} className="grid gap-2 justify-items-start">
              <ScorePilula valor={null} />
              <span className="text-[18px] leading-6 font-semibold">{getScoreLabel(null)}</span>
            </div>
          )}

          {/* UI-022 e UI-019: a frase de síntese é o único lugar da contagem de votos. */}
          {votos.length > 0 ? (
            <div className="grid gap-3">
              <p className="text-texto" title={tituloDoScore(votos.length)}>
                {synthesis}
              </p>
              <VotosBarra
                sim={alinhados}
                nao={contra}
                ausentes={semDirecao}
                rotulo={`${alinhados} alinhados, ${contra} contra${semDirecao ? `, ${semDirecao} sem posição definida` : ""}`}
              />
              {/* Legenda com os rótulos deste dado (alinhamento, não sim/não). */}
              <div className="flex flex-wrap gap-x-4 gap-y-1.5 text-[14px] leading-5 font-medium text-zil-texto-2 zil-num">
                <span className="inline-flex items-center gap-1.5">
                  <i className="w-2 h-2 rounded-full bg-zil-alinhado" />
                  {alinhados} alinhados
                </span>
                <span className="inline-flex items-center gap-1.5">
                  <i className="w-2 h-2 rounded-full bg-zil-contra" />
                  {contra} contra
                </span>
                {semDirecao > 0 && (
                  <span className="inline-flex items-center gap-1.5">
                    <i className="w-2 h-2 rounded-full bg-zil-superficie-4" />
                    {semDirecao} sem posição definida
                  </span>
                )}
              </div>
            </div>
          ) : (
            /* UI-004: ausência de dado explicada pela cobertura, não pelo parlamentar */
            <p className="text-texto-s text-zil-texto-2">
              Nenhuma votação ZIL registrada para este parlamentar. A cobertura atual inclui
              votações da Câmara dos Deputados.
            </p>
          )}
        </div>
      </Card>

      {/* Participação por pauta — UI-015: os chips são o filtro do histórico */}
      {breakdown.length > 0 && (
        <section className="zil-secao grid gap-5">
          <div className="grid gap-2">
            <h2 className="text-titulo-3">Participação por pauta</h2>
            <p className="text-texto-s text-zil-texto-2">
              Escolha uma pauta para filtrar o histórico abaixo. O número é quantos votos foram
              alinhados do total naquela pauta.
            </p>
          </div>
          <Chips>
            <Chip ativo={!filtroCategoria} n={votos.length} onClick={() => setFiltroCategoria("")}>
              Todas as pautas
            </Chip>
            {breakdown.map(([cat, stats]) => (
              <Chip
                key={cat}
                ativo={filtroCategoria === cat}
                pontoClassName={CATEGORIA_COR[cat]}
                n={`${stats.alinhados}/${stats.total}`}
                // UI-021: o código interno fica no title, fora do texto público.
                title={`${cat} — Filtrar histórico por ${CATEGORIA_LABELS[cat] ?? cat}`}
                onClick={() => setFiltroCategoria(filtroCategoria === cat ? "" : cat)}
              >
                {CATEGORIA_LABELS[cat] ?? cat}
              </Chip>
            ))}
          </Chips>
        </section>
      )}

      {/* Histórico — UI-017: contagem sempre no título */}
      <section className={`grid gap-5 ${breakdown.length > 0 ? "pb-16 md:pb-24" : "zil-secao"}`}>
        <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-2">
          <h2 className="text-titulo-3">
            Histórico de votos em pautas ZIL
            {filtroCategoria && <span className="text-zil-texto-2"> — {rotuloFiltro}</span>}
          </h2>
          <span className="text-texto-s text-zil-texto-2 zil-num shrink-0">
            {filtroCategoria ? `${votosFiltrados.length} de ${votos.length}` : votos.length} votações
          </span>
        </div>

        {/* UI-014 e UI-020: legenda do duplo encoding, com um selo real de exemplo */}
        {votos.length > 0 && (
          <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-texto-s text-zil-texto-2">
            <span className="inline-flex items-center gap-2">
              <PontoAlinhamento alinhado={true} />
              alinhado com a posição ZIL
            </span>
            <span className="inline-flex items-center gap-2">
              <PontoAlinhamento alinhado={false} />
              contra a posição ZIL
            </span>
            <span className="inline-flex items-center gap-2">
              <PontoAlinhamento alinhado={null} />
              sem posição definida
            </span>
            <span className="inline-flex items-center gap-2">
              <Selo>Sim</Selo>
              voto registrado
            </span>
          </div>
        )}

        {votosFiltrados.length === 0 ? (
          <Vazio
            icone="documento"
            titulo={filtroCategoria ? "Nenhuma votação nessa pauta" : "Nenhuma votação ZIL registrada"}
            acao={
              filtroCategoria ? (
                <Button variante="secundario" onClick={() => setFiltroCategoria("")}>
                  Ver todas as pautas
                </Button>
              ) : undefined
            }
          >
            {filtroCategoria
              ? `Este parlamentar não votou em nenhuma votação monitorada de ${rotuloFiltro}.`
              : "A cobertura atual inclui votações da Câmara dos Deputados; pode não haver votação monitorada com voto deste parlamentar."}
          </Vazio>
        ) : (
          <Lista>
            {votosFiltrados.map((v) => {
              const data = v.data ? new Date(v.data).toLocaleDateString("pt-BR") : null;
              const descricao = v.resumo_simples
                ? v.resumo_simples.length > 200
                  ? v.resumo_simples.slice(0, 200).trimEnd() + "..."
                  : v.resumo_simples
                : v.descricao || "Votação sem descrição";
              return (
                <Linha
                  key={v.votacao_id}
                  icone={<PontoAlinhamento alinhado={v.alinhado} />}
                  titulo={v.proposicao_label ?? descricao}
                  sub={
                    <span className="grid gap-1.5">
                      {v.proposicao_label && <span>{descricao}</span>}
                      <span className="flex flex-wrap items-center gap-x-3 gap-y-1">
                        {data && <span className="zil-num">{data}</span>}
                        {v.categorias_zil?.map((c) => (
                          <CategoriaBadge key={c} codigo={c} />
                        ))}
                        <Link
                          href={`/votacoes/${v.votacao_id}`}
                          className="text-zil-texto underline underline-offset-4 decoration-1 transition-colors duration-toque hover:text-zil-texto-2"
                        >
                          Ver votação
                        </Link>
                        {v.proposicao_id && (
                          <Link
                            href={`/proposicoes/${v.proposicao_id}`}
                            className="text-zil-texto underline underline-offset-4 decoration-1 transition-colors duration-toque hover:text-zil-texto-2"
                          >
                            Ver proposição
                          </Link>
                        )}
                      </span>
                    </span>
                  }
                  fim={
                    <span className="flex flex-wrap items-center justify-end gap-1.5">
                      <Selo>{VOTO_LABEL[v.voto] ?? v.voto}</Selo>
                      <DirecaoBadge direcao={v.direcao_esperada} />
                    </span>
                  }
                  className="items-start"
                />
              );
            })}
          </Lista>
        )}
      </section>
    </div>
  );
}
