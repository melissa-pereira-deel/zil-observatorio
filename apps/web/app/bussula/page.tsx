"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Aviso, Button, Card, CardEsqueleto, Icone, Revelar, Selo, Vazio, type TomSelo } from "@/components/ui";
import { CATEGORIA_COR } from "@/lib/categorias";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Marco {
  codigo: string;
  nome: string;
  categoria: string;
  descricao: string;
  valor_atual: number;
  unidade: string;
  tendencia: "avancando" | "retrocedendo" | "estavel";
  meta?: number;
  prazo?: number;
  fonte: string;
  fonte_url: string;
  ultima_atualizacao: string;
  governo_referencia: string;
}

/**
 * A tendência diz se o indicador melhora para a soberania, não se o número
 * sobe (como o delta do KPI do ZIL Interface): `alinhado` avança rumo à
 * meta, `contra` retrocede, `neutro` está parado.
 */
const TENDENCIA: Record<Marco["tendencia"], { label: string; title: string; tom: TomSelo }> = {
  avancando: { label: "Avançando", title: "Avançando em direção à meta", tom: "alinhado" },
  retrocedendo: { label: "Retrocedendo", title: "Retrocedendo em relação à meta", tom: "contra" },
  estavel: { label: "Estável", title: "Estável", tom: "neutro" },
};

const CAT_LABEL: Record<string, string> = {
  "ZIL-FER": "Fertilizantes",
  "ZIL-MIN": "Minerais",
  "ZIL-SEM": "Semicondutores",
  "ZIL-ENE": "Energia",
  "ZIL-DIG": "Digital",
  "ZIL-DEF": "Defesa",
  "ZIL-EDU": "Capital Humano",
  "ZIL-AGR": "Agro",
  "ZIL-COM": "Comércio",
};

/** Seta para a direita, no padrão do `Icone` (não existe no kit). */
function SetaDireita() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="w-4 h-4 shrink-0 fill-none stroke-current" strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 12h14M13 6l6 6-6 6" />
    </svg>
  );
}

function TendenciaSelo({ tendencia }: { tendencia: Marco["tendencia"] }) {
  const t = TENDENCIA[tendencia] ?? TENDENCIA.estavel;
  return (
    <Selo tom={t.tom} title={t.title}>
      {tendencia === "avancando" ? <Icone nome="seta-cima" tamanho="s" /> : tendencia === "retrocedendo" ? <Icone nome="seta-baixo" tamanho="s" /> : <SetaDireita />}
      {t.label}
    </Selo>
  );
}

function MarcoCard({ marco }: { marco: Marco }) {
  const progresso =
    marco.meta !== undefined
      ? Math.min(100, Math.round((marco.valor_atual / marco.meta) * 100))
      : null;

  return (
    <Card className="h-full grid content-start gap-3">
      {/* Rótulo e tendência */}
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-texto-ui text-zil-texto-2">{marco.nome}</h3>
        <TendenciaSelo tendencia={marco.tendencia} />
      </div>

      {/* Valor */}
      <div className="grid gap-1">
        <span className="text-numero-l zil-num">{marco.valor_atual}</span>
        <span className="text-texto-s text-zil-texto-2">{marco.unidade}</span>
      </div>

      {/* Progresso rumo à meta */}
      {marco.meta !== undefined && progresso !== null && (
        <div className="grid gap-2">
          <div className="flex justify-between gap-3 text-texto-s text-zil-texto-2 zil-num">
            <span>
              Meta: {marco.meta} {marco.unidade.split(" ")[0]}
            </span>
            {marco.prazo && <span>até {marco.prazo}</span>}
          </div>
          <div
            role="progressbar"
            aria-valuenow={progresso}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`${progresso}% da meta`}
            className="h-2 rounded-pilula bg-zil-superficie-3 overflow-hidden"
          >
            <div
              className="h-full rounded-pilula bg-zil-inverso transition-[width] duration-lenta ease-padrao"
              // Largura é o dado (percentual da meta), não estilo decorativo.
              style={{ width: `${progresso}%` }}
            />
          </div>
        </div>
      )}

      {/* Fonte oficial e data do dado */}
      <div className="flex items-center justify-between gap-3 text-texto-s text-zil-texto-2">
        <a
          href={marco.fonte_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 min-w-0 text-zil-texto-2 hover:text-zil-texto transition-colors duration-toque"
        >
          <span className="truncate">{marco.fonte}</span>
          <Icone nome="externo" tamanho="s" />
        </a>
        <span className="shrink-0 zil-num">{marco.ultima_atualizacao}</span>
      </div>
    </Card>
  );
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
      .then((r) => r.json())
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
          Estado atual da soberania industrial brasileira, por categoria estratégica. Indicadores verificáveis a partir de fontes oficiais.
        </p>
        <p className="text-texto-s text-zil-texto-2 max-w-[60ch]">
          Atualização trimestral via PR. Fontes linkadas diretamente em cada indicador.{" "}
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
            {/* Os marcos ainda estão em formação (ver o cabeçalho de data/bussula/marcos.yml) */}
            <Aviso tom="neutro" titulo="Indicadores em formação">
              {marcos.length} {marcos.length === 1 ? "indicador publicado" : "indicadores publicados"} até agora. Cada um entra por PR, com link para a fonte oficial.
            </Aviso>

            {Object.entries(porCategoria).map(([cat, items], gi) => (
              <div key={cat} className="grid gap-4">
                {/* UI-021: o código interno fica no title, não no texto */}
                <h2 className="flex items-center gap-2.5 text-titulo-3" title={cat}>
                  {CATEGORIA_COR[cat] && <span aria-hidden="true" className={`w-2.5 h-2.5 rounded-full shrink-0 ${CATEGORIA_COR[cat]}`} />}
                  {CAT_LABEL[cat] ?? cat}
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
