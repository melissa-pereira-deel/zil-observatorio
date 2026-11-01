"use client";

import { Chip, Chips, Hemiciclo, Legenda, MapaUF } from "@/components/ui";
import {
  COR_DO_TOM,
  GRUPOS,
  ROTULO_GRUPO,
  assentosDaVotacao,
  bancadasDaVotacao,
  contarGrupos,
  tomDoGrupo,
  type GrupoVoto,
  type VotoIndividual,
} from "@/lib/votacao";

/**
 * Hemiciclo de uma votação com os chips de grupo. O filtro é do pai
 * (`grupo`, `uf`): na página da votação ele também filtra a lista de votos;
 * na home, só acende as cadeiras.
 */
export function HemicicloVotacao({
  votos,
  cadeiras,
  direcao,
  grupo,
  aoMudarGrupo,
  uf = "",
}: {
  votos: VotoIndividual[];
  cadeiras: number;
  direcao: string | null | undefined;
  grupo: GrupoVoto | "";
  aoMudarGrupo: (g: GrupoVoto | "") => void;
  uf?: string;
}) {
  const n = contarGrupos(votos, cadeiras);
  const filtrado = !!grupo || !!uf;
  const assentos = assentosDaVotacao(votos, cadeiras, direcao, (v, g) =>
    (!grupo || g === grupo) && (!uf || (v !== null && v.parlamentar_uf === uf)),
  );
  const acesos = filtrado ? assentos.filter((a) => a.marcado).length : cadeiras;
  const casa = cadeiras === 81 ? "senadores" : "deputados";

  let legenda = casa;
  if (grupo && uf) legenda = `${ROTULO_GRUPO[grupo].toLowerCase()} · ${uf}`;
  else if (grupo) legenda = `${ROTULO_GRUPO[grupo].toLowerCase()} de ${cadeiras} ${casa}`;
  else if (uf) legenda = `${casa} de ${uf} que votaram`;

  return (
    <div className="grid gap-4">
      <Hemiciclo
        assentos={assentos}
        filtrado={filtrado}
        numero={String(acesos)}
        legendaNumero={legenda}
        rotulo={`Hemiciclo: ${GRUPOS.map((g) => `${n[g]} ${ROTULO_GRUPO[g].toLowerCase()}`).join(", ")}, de ${cadeiras} ${casa}`}
      />
      <Chips className="justify-center">
        {GRUPOS.filter((g) => n[g] > 0).map((g) => (
          <Chip
            key={g}
            tamanho="s"
            ativo={grupo === g}
            n={n[g]}
            pontoClassName={COR_DO_TOM[tomDoGrupo(g, direcao)]}
            onClick={() => aoMudarGrupo(grupo === g ? "" : g)}
          >
            {ROTULO_GRUPO[g]}
          </Chip>
        ))}
      </Chips>
      <p className="text-texto-s text-zil-texto-2 text-center max-w-[52ch] justify-self-center">
        {direcao
          ? `Verde é o voto na direção que o ZIL espera nesta votação (${direcao === "sim" ? "sim" : "não"}); vermelho, o voto contrário.`
          : "O ZIL não declarou direção para esta votação: sim e não aparecem sem cor de lado."}{" "}
        {n.nao_votou > 0 && "“Não votaram” inclui quem não registrou voto e o presidente da sessão, que não vota."}
      </p>
    </div>
  );
}

/** Mapa das bancadas estaduais numa votação: % de sim entre quem votou sim ou não. */
export function BancadasVotacao({
  votos,
  direcao,
  uf,
  aoMudarUF,
}: {
  votos: VotoIndividual[];
  direcao: string | null | undefined;
  uf: string;
  aoMudarUF: (uf: string) => void;
}) {
  const valores = bancadasDaVotacao(votos, direcao);
  return (
    <div className="grid gap-4">
      <MapaUF valores={valores} selecionada={uf} aoSelecionar={aoMudarUF} rotulo="Como cada bancada estadual votou" />
      <Legenda
        className="justify-center"
        itens={
          direcao
            ? [
                { cor: "bg-zil-alinhado", rotulo: "maioria na direção ZIL" },
                { cor: "bg-zil-neutro", rotulo: "dividida (45–55%)" },
                { cor: "bg-zil-contra", rotulo: "maioria contra" },
              ]
            : [{ cor: "bg-zil-superficie-4", rotulo: "% de sim entre quem votou sim ou não" }]
        }
      />
    </div>
  );
}
