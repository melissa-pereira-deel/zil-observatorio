import { Selo } from "@/components/ui";

/** Direção esperada pelo ZIL numa votação: favorável ou contrária, com link para a metodologia no title. */
export function DirecaoBadge({ direcao }: { direcao: string | null | undefined }) {
  if (direcao === "sim") {
    return (
      <Selo tom="alinhado" ponto title="Posição ZIL nesta votação: favorável · ver /metodologia">
        Favorável
      </Selo>
    );
  }
  if (direcao === "nao") {
    return (
      <Selo tom="contra" ponto title="Posição ZIL nesta votação: contrária · ver /metodologia">
        Contrária
      </Selo>
    );
  }
  return null;
}
