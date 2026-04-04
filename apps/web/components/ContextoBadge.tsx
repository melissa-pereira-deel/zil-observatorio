import { Badge } from "@/components/ui/Badge";

interface ContextoBadgeProps {
  status: string | null | undefined;
  confianca?: number | null;
  className?: string;
}

export function ContextoBadge({ status, confianca, className = "" }: ContextoBadgeProps) {
  if (status !== "pronto") return null;

  const isPartial = confianca !== null && confianca !== undefined && confianca < 0.7;

  return (
    <Badge
      variant="status"
      color={isPartial ? "gold" : "green"}
      className={className}
    >
      {isPartial ? "Análise parcial" : "Análise disponível"}
    </Badge>
  );
}
