interface ContextoBadgeProps {
  status: string | null | undefined;
  confianca?: number | null;
  className?: string;
}

export function ContextoBadge({ status, confianca, className = "" }: ContextoBadgeProps) {
  if (!status || status === "pendente") {
    return (
      <span
        className={`inline-flex items-center gap-1 font-mono text-xs px-2 py-0.5 border border-zil-divider text-zil-muted ${className}`}
      >
        <span className="w-1.5 h-1.5 rounded-full bg-zil-muted inline-block" />
        Contexto pendente
      </span>
    );
  }

  if (status === "processando") {
    return (
      <span
        className={`inline-flex items-center gap-1 font-mono text-xs px-2 py-0.5 border border-zil-divider text-zil-soft ${className}`}
      >
        <span className="w-1.5 h-1.5 rounded-full bg-zil-soft inline-block animate-pulse" />
        Processando...
      </span>
    );
  }

  if (status === "falhou" || status === "llm_falhou") {
    return (
      <span
        className={`inline-flex items-center gap-1 font-mono text-xs px-2 py-0.5 border border-zil-red/40 text-zil-red ${className}`}
      >
        <span className="w-1.5 h-1.5 rounded-full bg-zil-red inline-block" />
        Contexto indisponível
      </span>
    );
  }

  if (status === "pronto") {
    const isPartial =
      confianca !== null && confianca !== undefined && confianca < 0.7;

    if (isPartial) {
      return (
        <span
          className={`inline-flex items-center gap-1 font-mono text-xs px-2 py-0.5 border border-zil-gold/50 text-zil-gold ${className}`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-zil-gold inline-block" />
          Contexto parcial
        </span>
      );
    }

    return (
      <span
        className={`inline-flex items-center gap-1 font-mono text-xs px-2 py-0.5 border border-zil-green/50 text-zil-green ${className}`}
      >
        <span className="w-1.5 h-1.5 rounded-full bg-zil-green inline-block" />
        Contexto verificado
      </span>
    );
  }

  return null;
}
