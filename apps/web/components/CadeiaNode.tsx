import Link from "next/link";
import { CadeiaRead } from "../lib/api";

interface CadeiaNodeProps {
  cadeia: CadeiaRead;
}

export default function CadeiaNode({ cadeia }: CadeiaNodeProps) {
  const nodes = [
    { label: "Anterior", fonteId: cadeia.anterior_fonte_id },
    { label: "Principal", fonteId: cadeia.principal_fonte_id },
    { label: "Posterior", fonteId: cadeia.posterior_fonte_id },
  ].filter((n) => n.fonteId);

  if (nodes.length === 0) return null;

  return (
    <div className="flex flex-col md:flex-row items-start md:items-center gap-2 text-sm">
      <span className="font-medium text-zil-fg">Cadeia:</span>
      <div className="flex flex-wrap items-center gap-1">
        {nodes.map((node, i) => (
          <span key={node.label} className="flex items-center gap-1">
            {i > 0 && <span className="text-zil-soft mx-1">&rarr;</span>}
            <span className="inline-flex items-center px-2 py-0.5 rounded bg-zil-card border border-zil-divider text-zil-fg text-xs">
              {node.label}: {node.fonteId}
            </span>
          </span>
        ))}
      </div>
    </div>
  );
}
