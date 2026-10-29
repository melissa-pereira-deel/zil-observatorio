"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Aviso, Button, Card, CardEsqueleto, Icone, Revelar, Selo, Vazio, type NomeIcone, type TomSelo } from "@/components/ui";
import { CATEGORIA_COR, CATEGORIA_LABELS } from "@/lib/categorias";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/** Espelha `apps/api/schemas/bussula.py`, inclusive os campos calculados no servidor. */
interface Marco {
  codigo: string;
  nome: string;
  categoria: string;
  descricao: string;
  valor_atual: number;
  unidade: string;
  direcao: "maior_melhor" | "menor_melhor";
  tendencia: "avancando" | "retrocedendo" | "estavel";
  meta: number | null;
  prazo: number | null;
  meta_origem: { nome: string; url?: string | null } | null;
  fonte: string;
  natureza_fonte: "estatal" | "autarquia" | "associacao_setorial" | "academia" | "imprensa";
  fonte_url: string;
  fonte_dataset: string | null;
  ultima_atualizacao: string;
  validacao: "nao-validado" | "revisado";
  governo_referencia: string | null;
  progresso_pct: number | null;
  meta_atingida: boolean;
  meta_provisoria: boolean;
}

/**
 * A tendência diz se o indicador melhora para a soberania, não se o número
 * sobe (como o delta do KPI do ZIL Interface). Hoje ela é declarada no
 * arquivo pelo maintainer, não calculada: não há histórico ainda.
 */
const TENDENCIA: Record<Marco["tendencia"], { label: string; tom: TomSelo; icone: NomeIcone }> = {
  avancando: { label: "Avançando", tom: "alinhado", icone: "seta-cima" },
  retrocedendo: { label: "Retrocedendo", tom: "contra", icone: "seta-baixo" },
  estavel: { label: "Estável", tom: "neutro", icone: "seta-direita" },
};

const NATUREZA: Record<Marco["natureza_fonte"], string> = {
  estatal: "órgão estatal",
  autarquia: "autarquia",
  associacao_setorial: "associação setorial",
  academia: "academia",
  imprensa: "imprensa",
};

/** "2024-12" → "12/2024". */
function mesAno(iso: string): string {
  const [ano, mes] = iso.split("-");
  return mes && ano ? `${mes}/${ano}` : iso;
}

function TendenciaSelo({ tendencia }: { tendencia: Marco["tendencia"] }) {
  const t = TENDENCIA[tendencia] ?? TENDENCIA.estavel;
  return (
    <Selo tom={t.tom} icone={<Icone nome={t.icone} tamanho="s" />} className="shrink-0" title={`${t.label} — tendência declarada no arquivo de dados, ainda não calculada a partir de histórico`}>
      {t.label}
    </Selo>
  );
}

function MarcoCard({ marco }: { marco: Marco }) {
  const unidadeCurta = marco.unidade.split(" ")[0];
  const sentido = marco.direcao === "menor_melhor" ? "quanto menor, melhor" : "quanto maior, melhor";

  return (
    <Card className="h-full grid content-start gap-3">
      {/* Rótulo e tendência */}
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-texto-ui text-zil-texto-2">{marco.nome}</h3>
        <TendenciaSelo tendencia={marco.tendencia} />
      </div>

      {/* Valor */}
      <div className="grid gap-1">
        <span className="text-numero-l zil-num">{marco.valor_atual.toLocaleString("pt-BR")}</span>
        <span className="text-texto-s text-zil-texto-2">
          {marco.unidade} · {sentido}
        </span>
      </div>

      {/* Progresso rumo à meta — calculado no servidor, com a direção do indicador */}
      {marco.meta !== null && marco.progresso_pct !== null && (
        <div className="grid gap-2">
          <div className="flex flex-wrap justify-between gap-x-3 gap-y-1 text-texto-s text-zil-texto-2 zil-num">
            <span>
              Meta: {marco.meta.toLocaleString("pt-BR")} {unidadeCurta}
              {marco.prazo && <> até {marco.prazo}</>}
            </span>
            {marco.meta_atingida ? (
              <Selo tom="alinhado">Meta atingida</Selo>
            ) : (
              <span>{marco.progresso_pct}% do caminho</span>
            )}
          </div>
          <div
            role="progressbar"
            aria-valuenow={marco.progresso_pct}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`${marco.progresso_pct}% do caminho até a meta`}
            className="h-2 rounded-pilula bg-zil-superficie-3 overflow-hidden"
          >
            <div
              className="h-full rounded-pilula bg-zil-inverso transition-[width] duration-lenta ease-padrao"
              // Largura é o dado (percentual do caminho), não estilo decorativo.
              style={{ width: `${marco.progresso_pct}%` }}
            />
          </div>
          {marco.meta_provisoria ? (
            <p className="text-legenda text-zil-texto-2">Meta provisória, escolhida pelo projeto: nenhum plano oficial foi citado como origem.</p>
          ) : (
            marco.meta_origem && (
              <p className="text-legenda text-zil-texto-2">
                Meta de{" "}
                {marco.meta_origem.url ? (
                  <a href={marco.meta_origem.url} target="_blank" rel="noopener noreferrer" className="underline underline-offset-2 hover:text-zil-texto">
                    {marco.meta_origem.nome}
                  </a>
                ) : (
                  marco.meta_origem.nome
                )}
              </p>
            )
          )}
        </div>
      )}

      {/* Proveniência: fonte, natureza, dado, validação */}
      <div className="grid gap-1.5 text-texto-s text-zil-texto-2">
        <div className="flex items-center justify-between gap-3">
          <a
            href={marco.fonte_dataset ?? marco.fonte_url}
            target="_blank"
            rel="noopener noreferrer"
            title={marco.fonte_dataset ? "Abre o dado na fonte" : "Abre a página da instituição; o link direto do dado ainda não foi indicado"}
            className="inline-flex items-center gap-1 min-w-0 text-zil-texto-2 hover:text-zil-texto transition-colors duration-toque"
          >
            <span className="truncate">{marco.fonte}</span>
            <Icone nome="externo" tamanho="s" />
          </a>
          <span className="shrink-0 zil-num">dado de {mesAno(marco.ultima_atualizacao)}</span>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Selo>{NATUREZA[marco.natureza_fonte] ?? marco.natureza_fonte}</Selo>
          {!marco.fonte_dataset && <Selo title="O link aponta para a página inicial da instituição, não para a tabela ou série de onde o número saiu">sem link do dado</Selo>}
          {marco.validacao === "nao-validado" ? (
            <Selo tom="neutro" ponto title="Ainda não passou por revisão editorial independente">
              Não validado
            </Selo>
          ) : (
            <Selo tom="alinhado" ponto>
              Revisado
            </Selo>
          )}
        </div>
      </div>
    </Card>
  );
}

/** "4 indicadores · nenhum validado · nenhuma meta com fonte · dado mais recente 12/2024". */
function resumo(marcos: Marco[]): string {
  const validados = marcos.filter((m) => m.validacao === "revisado").length;
  const comOrigem = marcos.filter((m) => m.meta !== null && !m.meta_provisoria).length;
  const maisRecente = marcos.map((m) => m.ultima_atualizacao).sort().at(-1);
  const partes = [
    `${marcos.length} ${marcos.length === 1 ? "indicador" : "indicadores"}`,
    validados === 0 ? "nenhum validado" : `${validados} ${validados === 1 ? "validado" : "validados"}`,
    comOrigem === 0 ? "nenhuma meta com fonte declarada" : `${comOrigem} ${comOrigem === 1 ? "meta com fonte" : "metas com fonte"}`,
  ];
  if (maisRecente) partes.push(`dado mais recente de ${mesAno(maisRecente)}`);
  return partes.join(" · ");
}

export default function BussulaPage() {
  const [marcos, setMarcos] = useState<Marco[]>([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState(false);
  // Incrementa para refazer a busca depois de um erro.
  const [tentativa, setTentativa] = useState(0);

  useEffect(() => {
    setLoading(true);
    setErro(false);
    fetch(`${API_BASE}/bussula`)
      .then((r) => {
        if (!r.ok) throw new Error(String(r.status));
        return r.json();
      })
      .then(setMarcos)
      .catch(() => setErro(true))
      .finally(() => setLoading(false));
  }, [tentativa]);

  const porCategoria = marcos.reduce<Record<string, Marco[]>>((acc, m) => {
    if (!acc[m.categoria]) acc[m.categoria] = [];
    acc[m.categoria].push(m);
    return acc;
  }, {});

  return (
    <div className="zil-container">
      {/* Cabeçalho — UI-006: sem letra decorativa */}
      <header className="pt-10 md:pt-16 grid gap-4">
        <p className="text-rotulo uppercase text-zil-texto-2">Bússola</p>
        <h1 className="text-titulo-1 md:text-display-m">Bússola ZIL</h1>
        <p className="text-texto-l text-zil-texto-2 max-w-[60ch]">
          Onde o Brasil está em cada eixo da soberania industrial, com meta e prazo. Cada indicador diz de onde veio o número e o que
          ainda não foi conferido.
        </p>
        <p className="text-texto-s text-zil-texto-2 max-w-[60ch]">
          Os indicadores entram e mudam por PR no repositório, com link para a fonte.{" "}
          <Link href="/metodologia" className="text-zil-texto underline underline-offset-4 decoration-1">
            Como isso é calculado?
          </Link>
        </p>
      </header>

      <section className="zil-secao grid gap-10 md:gap-12">
        {erro ? (
          <Aviso
            tom="contra"
            titulo="Não foi possível carregar os indicadores"
            acao={
              <Button variante="secundario" tamanho="s" onClick={() => setTentativa((t) => t + 1)}>
                Tentar de novo
              </Button>
            }
          >
            A API não respondeu. Confira a conexão e tente de novo em instantes.
          </Aviso>
        ) : loading ? (
          <div className="grid gap-4 md:grid-cols-2" aria-busy="true" aria-label="Carregando indicadores">
            {Array.from({ length: 4 }, (_, i) => (
              <CardEsqueleto key={i} />
            ))}
          </div>
        ) : marcos.length === 0 ? (
          <Vazio icone="bussola" titulo="Nenhum indicador publicado ainda">
            Os indicadores da Bússola são gerenciados via <code className="px-1 rounded-xs bg-zil-superficie-2 text-zil-texto">data/bussula/marcos.yml</code> no repositório.
          </Vazio>
        ) : (
          <>
            {/* O estado vem do dado (validacao, meta_origem, ultima_atualizacao), não de texto fixo. */}
            <Aviso tom="neutro" titulo="Indicadores em formação">
              {resumo(marcos)}. As metas sem fonte são escolhas provisórias do projeto, e a tendência é declarada por quem edita o
              arquivo, não medida: ainda não há histórico.
            </Aviso>

            {Object.entries(porCategoria).map(([cat, items], gi) => (
              <div key={cat} className="grid gap-4">
                {/* UI-021: o código interno fica no title, não no texto */}
                <h2 className="flex items-center gap-2.5 text-titulo-3" title={cat}>
                  {CATEGORIA_COR[cat] && <span aria-hidden="true" className={`w-2.5 h-2.5 rounded-full shrink-0 ${CATEGORIA_COR[cat]}`} />}
                  {CATEGORIA_LABELS[cat] ?? cat}
                </h2>
                <ul className="grid gap-4 md:grid-cols-2 list-none m-0 p-0">
                  {items.map((m, i) => (
                    <Revelar key={m.codigo} as="li" ordem={(gi + i) % 4}>
                      <MarcoCard marco={m} />
                    </Revelar>
                  ))}
                </ul>
              </div>
            ))}
          </>
        )}
      </section>
    </div>
  );
}
