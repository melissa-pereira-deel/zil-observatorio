import Link from "next/link";
import { ParlamentarSnippet } from "../lib/api";

interface AutoresLineProps {
  autorPrincipal: ParlamentarSnippet | null;
  totalAutores?: number;
}

export default function AutoresLine({ autorPrincipal, totalAutores }: AutoresLineProps) {
  if (!autorPrincipal) {
    return null;
  }

  const label = `${autorPrincipal.nome}${autorPrincipal.partido ? ` (${autorPrincipal.partido}/${autorPrincipal.uf || "?"})` : ""}`;

  return (
    <p className="text-sm text-zil-muted">
      <span className="font-medium text-zil-fg">Autor: </span>
      <Link
        href={`/parlamentar/${autorPrincipal.id}`}
        className="text-zil-accent hover:underline"
      >
        {label}
      </Link>
      {totalAutores && totalAutores > 1 && (
        <span className="text-zil-soft"> e mais {totalAutores - 1}</span>
      )}
    </p>
  );
}
