import { Selo } from "@/components/ui";

/** Só aparece quando a análise está pronta (UI-002); parcial quando a confiança é baixa. */
export function ContextoBadge({ status, confianca }: { status: string | null | undefined; confianca?: number | null }) {
  if (status !== "pronto") return null;
  const parcial = confianca !== null && confianca !== undefined && confianca < 0.7;
  return (
    <Selo tom={parcial ? "neutro" : "alinhado"} ponto>
      {parcial ? "Análise parcial" : "Análise disponível"}
    </Selo>
  );
}
